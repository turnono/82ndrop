const { getAuth } = require("firebase-admin/auth");

async function grantUserAccess(email, accessLevel = "basic") {
  try {
    console.log(`Looking up user with email: ${email}`);

    // Get user by email
    const userRecord = await getAuth().getUserByEmail(email);
    console.log(`Found user: ${userRecord.uid}`);

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

    await getAuth().setCustomUserClaims(userRecord.uid, customClaims);

    console.log(`✅ Agent access granted to user ${email} (${userRecord.uid})`);
    console.log(`Access level: ${accessLevel}`);
    console.log(`Claims:`, JSON.stringify(customClaims, null, 2));

    return {
      success: true,
      uid: userRecord.uid,
      email: email,
      claims: customClaims,
    };
  } catch (error) {
    console.error("❌ Error granting access:", error.message);
    return {
      success: false,
      error: error.message,
    };
  }
}

async function makeUserAdmin(email) {
  return await grantUserAccess(email, "admin");
}

async function grantVideoPower(email) {
  const result = await grantUserAccess(email, "admin");
  if (!result.success) {
    console.error(`Failed to grant base admin access to ${email}. Aborting video power grant.`);
    return result;
  }

  try {
    const userRecord = await getAuth().getUserByEmail(email);
    const existingClaims = userRecord.customClaims || {};
    const newClaims = {
      ...existingClaims,
      can_generate_video: true,
    };

    await getAuth().setCustomUserClaims(userRecord.uid, newClaims);
    console.log(`✅ Video generation power granted to ${email}`);
    return { success: true, claims: newClaims };
  } catch (error) {
    console.error(`❌ Error granting video power:`, error.message);
    return { success: false, error: error.message };
  }
}

// Command line usage
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log(`
Usage: 
  node grant-user-access.js <email> [access_level]
  node grant-user-access.js admin <email>
  node grant-user-access.js video <email>

Examples:
  node grant-user-access.js user@example.com basic
  node grant-user-access.js user@example.com premium  
  node grant-user-access.js admin user@example.com

Access levels: basic, premium, admin
    `);
    process.exit(1);
  }

  let email;
  let accessLevel;

  if (args[0] === "admin" && args[1]) {
    email = args[1];
    accessLevel = "admin";
    grantUserAccess(email, accessLevel)
  } else if (args[0] === "video" && args[1]) {
    email = args[1];
    grantVideoPower(email)
  } else {
    email = args[0];
    accessLevel = args[1] || "basic";
    grantUserAccess(email, accessLevel)
  }
    .then((result) => {
      if (result.success) {
        console.log("\n🎉 User access granted successfully!");
        console.log("The user can now access the 82ndrop analytics dashboard.");
      } else {
        console.log("\n💥 Failed to grant access.");
        process.exit(1);
      }
    })
    .catch((error) => {
      console.error("💥 Unexpected error:", error);
      process.exit(1);
    });
}

module.exports = { grantUserAccess, makeUserAdmin };
