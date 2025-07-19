/**
 * 82ndrop Cloud Functions
 * User access management and authentication functions
 */

const admin = require("firebase-admin");
const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { onRequest } = require("firebase-functions/v2/https");
const { getAuth } = require("firebase-admin/auth");
const crypto = require("crypto");

// Initialize Firebase Admin
if (!admin.apps.length) {
  admin.initializeApp();
}

// Credit packages
const CREDIT_PACKAGES = {
  100: { credits: 100, amount: 10000 }, // R100 = 10000 cents
  450: { credits: 500, amount: 45000 }, // R450 = 45000 cents
  800: { credits: 1000, amount: 80000 }, // R800 = 80000 cents
};

/**
 * Initialize Paystack payment
 */
exports.initializePayment = onCall(
  {
    region: "us-central1",
    maxInstances: 10,
  },
  async (request) => {
    try {
      const { email, amount } = request.data;
      const { uid } = request.auth;

      if (!email || !amount) {
        throw new HttpsError(
          "invalid-argument",
          "Email and amount are required"
        );
      }

      // Validate amount matches a credit package
      const package = CREDIT_PACKAGES[amount];
      if (!package) {
        throw new HttpsError(
          "invalid-argument",
          "Invalid credit package amount"
        );
      }

      // Initialize payment with Paystack
      const response = await fetch(
        "https://api.paystack.co/transaction/initialize",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${process.env.PAYSTACK_SECRET_KEY}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            amount: package.amount, // Amount in cents
            callback_url: `${process.env.FRONTEND_URL}/dashboard`,
            metadata: {
              uid,
              credits: package.credits,
              custom_fields: [
                {
                  display_name: "Credits",
                  variable_name: "credits",
                  value: package.credits,
                },
              ],
            },
          }),
        }
      );

      const data = await response.json();
      if (!data.status) {
        throw new Error(data.message);
      }

      return data;
    } catch (error) {
      console.error("Error initializing payment:", error);
      throw new HttpsError("internal", error.message);
    }
  }
);

/**
 * Handle Paystack webhook
 */
exports.paystackWebhook = onRequest(
  {
    region: "us-central1",
    maxInstances: 10,
  },
  async (request, response) => {
    try {
      // Verify Paystack signature
      const hash = crypto
        .createHmac("sha512", process.env.PAYSTACK_SECRET_KEY)
        .update(JSON.stringify(request.body))
        .digest("hex");

      if (hash !== request.headers["x-paystack-signature"]) {
        throw new Error("Invalid signature");
      }

      const event = request.body;

      // Handle successful charge
      if (event.event === "charge.success") {
        const { uid, credits } = event.data.metadata;

        // Get current user claims
        const user = await getAuth().getUser(uid);
        const currentClaims = user.customClaims || {};
        const currentCredits = currentClaims.credits || 0;

        // Update credits
        const newClaims = {
          ...currentClaims,
          credits: currentCredits + credits,
          last_purchase: new Date().toISOString(),
        };

        await getAuth().setCustomUserClaims(uid, newClaims);

        // Log the purchase
        await admin
          .firestore()
          .collection("credit_purchases")
          .add({
            uid,
            credits,
            amount: event.data.amount / 100, // Convert cents to Rand
            reference: event.data.reference,
            timestamp: admin.firestore.FieldValue.serverTimestamp(),
          });
      }

      response.status(200).send("Webhook processed");
    } catch (error) {
      console.error("Error processing webhook:", error);
      response.status(500).send(error.message);
    }
  }
);
