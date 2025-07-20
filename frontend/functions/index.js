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

// Import functions from other files
const autoGrantAccess = require("./auto-grant-access");
const setUserClaims = require("./set-user-claims");
const grantUserAccess = require("./grant-user-access");

// Credit packages
const CREDIT_PACKAGES = {
  100: { credits: 100, amount: 10000 }, // R100 = 10000 cents
  450: { credits: 500, amount: 45000 }, // R450 = 45000 cents
  800: { credits: 1000, amount: 80000 }, // R800 = 80000 cents
};

// Export functions from auto-grant-access.js
exports.autoGrantAccess = autoGrantAccess.autoGrantAccess;
exports.grantAccessManual = autoGrantAccess.grantAccessManual;
exports.checkAndGrantAccess = autoGrantAccess.checkAndGrantAccess;

// Export functions from set-user-claims.js
exports.grantAgentAccess = setUserClaims.grantAgentAccess;
exports.revokeAgentAccess = setUserClaims.revokeAgentAccess;
exports.onUserCreate = setUserClaims.onUserCreate;

// Export functions from grant-user-access.js
exports.grantUserAccess = grantUserAccess.grantUserAccess;

const cors = require("cors")({
  origin: [
    "http://localhost:4200",
    "https://taajirah.web.app",
    "https://82ndrop.web.app",
    "https://82ndrop-staging.web.app",
  ],
});

// Function to get the environment from the request origin
const getEnvironmentFromOrigin = (origin) => {
  if (
    origin === "https://taajirah.web.app" ||
    origin === "https://82ndrop.web.app"
  ) {
    return "production";
  }
  // Default to staging for localhost or staging-specific URLs
  return "staging";
};

// Function to get the correct Paystack secret key based on the environment
const getPaystackSecretKey = (env) => {
  console.log("env: ", process.env);
  if (env === "production") {
    return process.env.PAYSTACK_LIVE_SECRET_KEY;
  }
  return process.env.PAYSTACK_SANDBOX_SECRET_KEY;
};

/**
 * Initialize Paystack payment
 */
exports.initializePayment = onRequest(
  {
    region: "us-central1",
    maxInstances: 10,
    secrets: ["PAYSTACK_LIVE_SECRET_KEY", "PAYSTACK_SANDBOX_SECRET_KEY"],
  },
  (request, response) => {
    cors(request, response, async () => {
      try {
        // Securely determine environment from request origin
        const environment = getEnvironmentFromOrigin(request.headers.origin);

        // Verify Firebase ID token
        const idToken = request.headers.authorization?.split("Bearer ")[1];
        if (!idToken) {
          response.status(401).send("Unauthorized");
          return;
        }
        const decodedToken = await getAuth().verifyIdToken(idToken);
        const uid = decodedToken.uid;

        const { email, amount } = request.body;

        if (!email || !amount) {
          response.status(400).send("Email and amount are required");
          return;
        }

        // Validate amount matches a credit package
        const creditPackage = CREDIT_PACKAGES[amount];
        if (!creditPackage) {
          response.status(400).send("Invalid credit package amount");
          return;
        }

        // Initialize payment with Paystack
        const paystackResponse = await fetch(
          "https://api.paystack.co/transaction/initialize",
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${getPaystackSecretKey(environment)}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              email,
              amount: creditPackage.amount, // Amount in cents
              callback_url: `${process.env.FRONTEND_URL}/dashboard`,
              metadata: {
                uid,
                credits: creditPackage.credits,
                environment, // Pass securely determined environment
                custom_fields: [
                  {
                    display_name: "Credits",
                    variable_name: "credits",
                    value: creditPackage.credits,
                  },
                ],
              },
            }),
          }
        );

        const data = await paystackResponse.json();
        if (!data.status) {
          throw new Error(data.message);
        }

        response.status(200).send(data);
      } catch (error) {
        console.error("Error initializing payment:", error);
        response.status(500).send(error.message);
      }
    });
  }
);

/**
 * Handle Paystack webhook
 */
exports.paystackWebhook = onRequest(
  {
    region: "us-central1",
    maxInstances: 10,
    secrets: ["PAYSTACK_LIVE_SECRET_KEY", "PAYSTACK_SANDBOX_SECRET_KEY"],
  },
  async (request, response) => {
    try {
      // Get environment from the transaction metadata
      const environment = request.body.data.metadata.environment;

      // Verify Paystack signature using the correct key
      const hash = crypto
        .createHmac("sha512", getPaystackSecretKey(environment))
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
