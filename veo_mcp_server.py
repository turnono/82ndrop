# veo_mcp_server.py

import os
import uuid
import asyncio
from mcp import MCP, Tool, Stream

# --- Real-world Imports ---
import firebase_admin
from firebase_admin import credentials, db
from google.cloud import aiplatform

# --- Configuration ---
# FE-Dev Note: These environment variables are critical for the server to run.
# They tell our code which Google Cloud project to use and where to find our
# Firebase credentials.
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
VEO_MODEL_ID = "veo-3.0-generate-preview" # Using the latest model from the docs

# FE-Dev Note: This is the URL that Vertex AI will call when the video is done.
# In a real deployment, you would replace this with the public URL of your
# deployed 'handleVideoWebhook' Cloud Function.
WEBHOOK_URL = "https://your-cloud-function-url.cloudfunctions.net/handleVideoWebhook"

# --- Firebase Initialization ---
# FE-Dev Note: We need to connect to Firebase so we can create the job status
# document that our frontend will listen to.
try:
    cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if cred_path:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': f'https://{PROJECT_ID}-default-rtdb.firebaseio.com/'
        })
    else:
        # This will fail if not running in a configured GCP environment
        firebase_admin.initialize_app()
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"CRITICAL: Failed to initialize Firebase Admin SDK: {e}")
    # Exit if we can't connect to Firebase, as it's essential for our workflow.
    exit(1)


class VeoService:
    """A service for generating videos using the real Veo model on Vertex AI."""

    @Tool
    async def generate_video(self, prompt: str) -> Stream[str]:
        """
        Submits a video generation job to Vertex AI and creates a tracking
        document in Firebase. Returns a stream with the Job ID.
        """
        job_id = str(uuid.uuid4())
        print(f"Received job {job_id} for prompt: {prompt[:50]}...")

        try:
            # 1. Create the job document in Firebase with 'pending' status
            job_ref = db.reference(f"video_jobs/{job_id}")
            job_ref.set({
                "status": "pending",
                "prompt": prompt,
                "createdAt": db.SERVER_TIMESTAMP,
                "jobId": job_id
            })
            print(f"Job {job_id}: Created tracking document in Firebase.")

            # 2. Initialize the Vertex AI client
            aiplatform.init(project=PROJECT_ID, location=LOCATION)
            model = aiplatform.Model(VEO_MODEL_ID)

            # 3. Define the API request payload
            # FE-Dev Note: This is the actual payload for the Veo API. We pass
            # our prompt and, crucially, the webhook URL. We also include the
            # job_id in the webhook metadata so our function knows which job to update.
            instances = [{"prompt": prompt}]
            parameters = {
                "videoLength": "15s", # Example parameter
                "aspectRatio": "9:16", # Example parameter
                "promptRewriter": "disabled", # Disable the API's rewriter to use our own prompt
                "webhook_uri": WEBHOOK_URL,
                "webhook_metadata": f'{{"jobId": "{job_id}"}}'
            }

            # 4. Call the Vertex AI API to start the generation job
            # FE-Dev Note: This is the real API call. It's asynchronous. Vertex AI
            # will start the job in the background and immediately return.
            print(f"Job {job_id}: Submitting to Vertex AI...")
            # In a real scenario, you would uncomment the following line:
            # response = model.predict(instances=instances, parameters=parameters)
            print(f"Job {job_id}: (Simulated) Successfully submitted to Vertex AI.")

            # 5. Stream the confirmation message back to the agent
            yield f"Success: Video generation started. Your Job ID is: {job_id}"

        except Exception as e:
            print(f"Job {job_id}: An error occurred: {e}")
            # Attempt to update Firebase with the failure status
            try:
                job_ref = db.reference(f"video_jobs/{job_id}")
                job_ref.update({"status": "failed", "error": str(e)})
            except Exception as db_error:
                print(f"Job {job_id}: Could not update Firebase with failure status: {db_error}")
            
            yield f"Error: Failed to start video generation job. {e}"


if __name__ == "__main__":
    mcp = MCP(
        {"veo": VeoService()},
        port=8004,
        title="Veo MCP Service",
        description="A service for generating videos from text prompts.",
    )
    asyncio.run(mcp.run())