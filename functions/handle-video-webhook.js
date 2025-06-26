// functions/handle-video-webhook.js

const functions = require("firebase-functions");
const admin = require("firebase-admin");

// FE-Dev Note: We're not initializing the app here because it's assumed
// to be initialized in the main index.js of your functions directory.
// This is standard practice for Firebase Functions.

exports.handleVideoWebhook = functions.https.onRequest(async (req, res) => {
  // Log the request for debugging
  console.log("Received Veo webhook request:", req.body);

  // FE-Dev Note: When Veo calls this webhook, it will send a request body (payload)
  // containing the job_id and the final video_url. We need to extract these.
  const { jobId, videoUrl, status, error } = req.body;

  if (!jobId) {
    console.error("Error: Missing jobId in webhook payload.");
    return res.status(400).send("Bad Request: Missing jobId");
  }

  try {
    // FE-Dev Note: This is the core logic. We're getting a reference to the
    // specific job document in our 'video_jobs' collection in the database.
    const jobRef = admin.database().ref(`/video_jobs/${jobId}`);

    let updateData;
    if (status === "succeeded" && videoUrl) {
      // If the job was successful, we update the status to 'complete'
      // and, most importantly, we add the videoUrl. This is the trigger
      // that our frontend listener is waiting for.
      updateData = {
        status: "complete",
        videoUrl: videoUrl,
        completedAt: admin.database.ServerValue.TIMESTAMP,
      };
      console.log(`Updating job ${jobId} to 'complete'.`);
    } else {
      // If the job failed, we update the status and record the error.
      updateData = {
        status: "failed",
        error: error || "Unknown error from video generation service.",
        completedAt: admin.database.ServerValue.TIMESTAMP,
      };
      console.error(`Updating job ${jobId} to 'failed'. Error: ${error}`);
    }

    // Here we perform the actual update to the database.
    await jobRef.update(updateData);

    // Send a success response back to Veo to let it know we received the webhook.
    return res.status(200).send("Webhook processed successfully.");

  } catch (e) {
    console.error(`Error processing webhook for job ${jobId}:`, e);
    return res.status(500).send("Internal Server Error");
  }
});
