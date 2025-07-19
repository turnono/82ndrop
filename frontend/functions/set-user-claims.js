const { getAuth } = require("firebase-admin/auth");

/**
 * Cloud Function to set custom claims for 82ndrop access
 * This grants users permission to access the 82ndrop agent system
 */
exports.grantAgentAccess = async (req, res) => {
  try {
    const { uid, accessLevel = "basic" } = req.body;

    if (!uid) {
      return res.status(400).json({ error: "User UID is required" });
    }

    // Set custom claims for the user
    const customClaims = {
      agent_access: true,
      access_level: accessLevel, // 'basic', 'premium', 'admin'
      agent_permissions: {
        "82ndrop": true,
        video_prompts: true,
        search_agent: accessLevel !== "basic",
        guide_agent: true,
        prompt_writer: true,
      },
      granted_at: new Date().toISOString(),
    };

    await getAuth().setCustomUserClaims(uid, customClaims);

    res.json({
      success: true,
      message: `Agent access granted to user ${uid}`,
      claims: customClaims,
    });
  } catch (error) {
    console.error("Error setting custom claims:", error);
    res.status(500).json({
      error: "Failed to grant agent access",
      details: error.message,
    });
  }
};

/**
 * Cloud Function to revoke agent access
 */
exports.revokeAgentAccess = async (req, res) => {
  try {
    const { uid } = req.body;

    if (!uid) {
      return res.status(400).json({ error: "User UID is required" });
    }

    // Remove custom claims
    await getAuth().setCustomUserClaims(uid, {
      agent_access: false,
      access_level: null,
      agent_permissions: null,
      revoked_at: new Date().toISOString(),
    });

    res.json({
      success: true,
      message: `Agent access revoked for user ${uid}`,
    });
  } catch (error) {
    console.error("Error revoking custom claims:", error);
    res.status(500).json({
      error: "Failed to revoke agent access",
      details: error.message,
    });
  }
};

/**
 * Automatically grant access to new users (optional)
 */
exports.onUserCreate = async (user) => {
  try {
    // Automatically grant basic access and free credits to new users
    const customClaims = {
      agent_access: true,
      access_level: "basic",
      credits: 50, // Grant 50 free credits on sign-up
      agent_permissions: {
        "82ndrop": true,
        video_prompts: true,
        search_agent: true,
        guide_agent: true,
        prompt_writer: true,
      },
      granted_at: new Date().toISOString(),
    };

    await getAuth().setCustomUserClaims(user.uid, customClaims);
    console.log(
      `Auto-granted agent access and 50 credits to new user: ${user.uid}`
    );
  } catch (error) {
    console.error("Error auto-granting access:", error);
  }
};
