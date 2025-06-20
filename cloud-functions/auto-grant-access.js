const { initializeApp } = require("firebase-admin/app");
const { getAuth } = require("firebase-admin/auth");
const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { onDocumentCreated } = require("firebase-functions/v2/firestore");

// Initialize Firebase Admin
initializeApp();

/**
 * Automatically grant basic agent access to new users
 * This can be triggered by user creation or called manually
 */
exports.autoGrantAccess = onCall(async (request) => {
  try {
    const { uid } = request.data;

    if (!uid) {
      throw new HttpsError("invalid-argument", "User UID is required");
    }

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

    return {
      success: true,
      message: `Basic agent access granted to user ${uid}`,
      claims: customClaims,
    };
  } catch (error) {
    console.error("Error auto-granting access:", error);
    throw new HttpsError(
      "internal",
      "Failed to grant agent access",
      error.message
    );
  }
});

/**
 * HTTP endpoint to manually grant access (for testing)
 */
exports.grantAccessManual = onCall(async (request) => {
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
});

/**
 * Check if user has access and grant if needed
 */
exports.checkAndGrantAccess = onCall(async (request) => {
  try {
    const { uid } = request.data;

    if (!uid) {
      throw new HttpsError("invalid-argument", "User UID is required");
    }

    // Get current user claims
    const user = await getAuth().getUser(uid);
    const currentClaims = user.customClaims || {};

    // If user doesn't have agent access, grant it
    if (!currentClaims.agent_access) {
      const customClaims = {
        agent_access: true,
        access_level: "basic",
        agent_permissions: {
          "82ndrop": true,
          video_prompts: true,
          search_agent: false,
          guide_agent: true,
          prompt_writer: true,
        },
        granted_at: new Date().toISOString(),
        auto_granted: true,
      };

      await getAuth().setCustomUserClaims(uid, customClaims);

      return {
        success: true,
        message: "Access granted",
        claims: customClaims,
        was_granted: true,
      };
    }

    return {
      success: true,
      message: "User already has access",
      claims: currentClaims,
      was_granted: false,
    };
  } catch (error) {
    console.error("Error checking/granting access:", error);
    throw new HttpsError("internal", "Failed to check access", error.message);
  }
});
