const { initializeApp } = require("firebase-admin/app");
const { getAuth } = require("firebase-admin/auth");

// Initialize Firebase Admin with explicit project ID
initializeApp({
  projectId: "taajirah",
});

async function createTestUser(
  email,
  password = "testpassword123",
  accessLevel = "admin"
) {
  try {
    console.log(`Creating user with email: ${email}`);

    // Create the user
    const userRecord = await getAuth().createUser({
      email: email,
      password: password,
      displayName: "Test User",
      emailVerified: true,
    });

    console.log(`✅ User created: ${userRecord.uid}`);

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
    console.log(`Password: ${password}`);
    console.log(`Claims:`, JSON.stringify(customClaims, null, 2));

    return {
      success: true,
      uid: userRecord.uid,
      email: email,
      password: password,
      claims: customClaims,
    };
  } catch (error) {
    if (error.code === "auth/email-already-exists") {
      console.log(`📧 User ${email} already exists. Trying to grant access...`);

      try {
        // User exists, just grant access
        const userRecord = await getAuth().getUserByEmail(email);

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
        };

        await getAuth().setCustomUserClaims(userRecord.uid, customClaims);

        console.log(
          `✅ Agent access granted to existing user ${email} (${userRecord.uid})`
        );
        console.log(`Access level: ${accessLevel}`);

        return {
          success: true,
          uid: userRecord.uid,
          email: email,
          password: "existing user - password unchanged",
          claims: customClaims,
        };
      } catch (grantError) {
        console.error(
          "❌ Error granting access to existing user:",
          grantError.message
        );
        return {
          success: false,
          error: grantError.message,
        };
      }
    } else {
      console.error("❌ Error creating user:", error.message);
      return {
        success: false,
        error: error.message,
      };
    }
  }
}

// Command line usage
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log(`
Usage: 
  node create-test-user.js <email> [password] [access_level]

Examples:
  node create-test-user.js test@test.com
  node create-test-user.js test@test.com mypassword123 admin
  node create-test-user.js user@example.com password123 basic

Default password: testpassword123
Default access level: admin
    `);
    process.exit(1);
  }

  const email = args[0];
  const password = args[1] || "testpassword123";
  const accessLevel = args[2] || "admin";

  createTestUser(email, password, accessLevel)
    .then((result) => {
      if (result.success) {
        console.log("\n🎉 Test user setup completed successfully!");
        console.log("\n📝 Login Details:");
        console.log(`Email: ${result.email}`);
        console.log(`Password: ${result.password}`);
        console.log(`Access Level: ${accessLevel}`);
        console.log("\n🚀 You can now:");
        console.log("1. Sign in to the Angular app with these credentials");
        console.log("2. Navigate to /analytics to view the dashboard");
        console.log("3. Test all analytics features");
      } else {
        console.log("\n💥 Failed to create test user.");
        process.exit(1);
      }
    })
    .catch((error) => {
      console.error("💥 Unexpected error:", error);
      process.exit(1);
    });
}

module.exports = { createTestUser };
