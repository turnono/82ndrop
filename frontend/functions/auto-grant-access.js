const { getAuth } = require("firebase-admin/auth");
const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { onRequest } = require("firebase-functions/v2/https");
const { defineString } = require("firebase-functions/params");
const cors = require("cors")({
  origin: [
    "http://localhost:4200",
    "https://taajirah.net",
    "https://82ndrop.web.app",
    "https://82ndrop-staging.web.app",
  ],
});

// Define region for better control
const REGION = defineString("REGION", { default: "us-central1" });

/**
 * Automatically grant basic agent access to new users
 * This can be triggered by user creation or called manually
 */
exports.autoGrantAccess = onRequest(
  {
    region: REGION,
    maxInstances: 10,
  },
  (request, response) => {
    cors(request, response, async () => {
      try {
        // Verify Firebase ID token
        const idToken = request.headers.authorization?.split("Bearer ")[1];
        if (!idToken) {
          response.status(401).send("Unauthorized");
          return;
        }
        const decodedToken = await getAuth().verifyIdToken(idToken);
        const uid = decodedToken.uid;

        // Set basic custom claims for new users
        const customClaims = {
          agent_access: true,
          access_level: "basic",
          agent_permissions: {
            "82ndrop": true,
            video_prompts: true,
            search_agent: false, // Premium feature
            guide_agent: true,
            prompt_writer: true,
          },
          granted_at: new Date().toISOString(),
          auto_granted: true,
        };

        await getAuth().setCustomUserClaims(uid, customClaims);

        console.log(`Auto-granted basic agent access to user: ${uid}`);

        response.status(200).send({
          success: true,
          message: `Basic agent access granted to user ${uid}`,
          claims: customClaims,
        });
      } catch (error) {
        console.error("Error auto-granting access:", error);
        response.status(500).send({
          success: false,
          message: "Failed to grant agent access",
          error: error.message,
        });
      }
    });
  }
);

/**
 * HTTP endpoint to manually grant access (for testing)
 */
exports.grantAccessManual = onCall(
  {
    region: REGION,
    maxInstances: 10,
  },
  async (request) => {
    try {
      const { uid, accessLevel = "basic" } = request.data;

      if (!uid) {
        throw new HttpsError("invalid-argument", "User UID is required");
      }

      const customClaims = {
        agent_access: true,
        access_level: accessLevel,
        agent_permissions: {
          "82ndrop": true,
          video_prompts: true,
          search_agent: accessLevel !== "basic",
          guide_agent: true,
          prompt_writer: true,
        },
        granted_at: new Date().toISOString(),
        manual_grant: true,
      };

      await getAuth().setCustomUserClaims(uid, customClaims);

      return {
        success: true,
        message: `Agent access granted to user ${uid}`,
        claims: customClaims,
      };
    } catch (error) {
      console.error("Error granting access:", error);
      throw new HttpsError(
        "internal",
        "Failed to grant agent access",
        error.message
      );
    }
  }
);

/**
 * Check if user has access and grant if needed
 */
exports.checkAndGrantAccess = onRequest(
  {
    region: REGION,
    maxInstances: 10,
  },
  (request, response) => {
    cors(request, response, async () => {
      try {
        // Verify Firebase ID token
        const idToken = request.headers.authorization?.split("Bearer ")[1];
        if (!idToken) {
          response.status(401).send("Unauthorized");
          return;
        }
        const decodedToken = await getAuth().verifyIdToken(idToken);
        const uid = decodedToken.uid;

        // Get current user claims
        const user = await getAuth().getUser(uid);
        const currentClaims = user.customClaims || {};

        // If user doesn't have agent access or credits, grant them.
        if (!currentClaims.agent_access || !currentClaims.credits) {
          const customClaims = {
            ...currentClaims,
            agent_access: true,
            access_level: "basic",
            credits: currentClaims.credits || 50, // Grant 50 credits if they don't have any
            agent_permissions: {
              "82ndrop": true,
              video_prompts: true,
              search_agent: true,
              guide_agent: true,
              prompt_writer: true,
            },
            granted_at: new Date().toISOString(),
            auto_granted: true,
          };

          await getAuth().setCustomUserClaims(uid, customClaims);

          response.status(200).send({
            success: true,
            message: "Access and credits granted",
            claims: customClaims,
            was_granted: true,
          });
        } else {
          response.status(200).send({
            success: true,
            message: "User already has access",
            claims: currentClaims,
            was_granted: false,
          });
        }
      } catch (error) {
        console.error("Error checking/granting access:", error);
        response.status(500).send({
          success: false,
          message: "Failed to check access",
          error: error.message,
        });
      }
    });
  }
);
