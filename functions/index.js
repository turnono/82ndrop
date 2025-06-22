/**
 * 82ndrop Cloud Functions
 * User access management and authentication functions
 */

const { initializeApp } = require("firebase-admin/app");
const { setGlobalOptions } = require("firebase-functions");

// Initialize Firebase Admin
initializeApp();

// Set global options for cost control
setGlobalOptions({ maxInstances: 10 });

// Import and export our custom functions
const autoGrantAccess = require("./auto-grant-access");
const setUserClaims = require("./set-user-claims");
const grantUserAccess = require("./grant-user-access");

// Export auto-grant access functions
exports.autoGrantAccess = autoGrantAccess.autoGrantAccess;
exports.grantAccessManual = autoGrantAccess.grantAccessManual;
exports.checkAndGrantAccess = autoGrantAccess.checkAndGrantAccess;

// Export user claims management functions
exports.grantAgentAccess = setUserClaims.grantAgentAccess;
exports.revokeAgentAccess = setUserClaims.revokeAgentAccess;
exports.onUserCreate = setUserClaims.onUserCreate;

// Export manual user access functions
exports.grantUserAccess = grantUserAccess.grantUserAccess;
exports.createTestUser = grantUserAccess.createTestUser;
