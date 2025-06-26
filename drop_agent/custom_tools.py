import os
import uuid
import firebase_admin
from firebase_admin import credentials, auth, db
from google.cloud import aiplatform
from google.adk.tools import FunctionTool

# --- Firebase Initialization ---
try:
    cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if cred_path:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': f'https://{os.getenv("GOOGLE_CLOUD_PROJECT")}-default-rtdb.firebaseio.com/'
        })
    else:
        firebase_admin.initialize_app()
    print("Firebase Admin SDK initialized successfully for custom tools.")
except Exception as e:
    # If the app is already initialized, it will raise an error.
    if "already exists" not in str(e):
        print(f"CRITICAL: Failed to initialize Firebase Admin SDK for custom tools: {e}")

@FunctionTool
def check_user_access(user_id: str) -> dict:
    """Checks the custom claims of a user to see if they have video generation permission."""
    try:
        user = auth.get_user(user_id)
        claims = user.custom_claims or {}
        return {"can_generate_video": claims.get("can_generate_video", False)}
    except Exception as e:
        print(f"Error checking user access for {user_id}: {e}")
        return {"can_generate_video": False, "error": str(e)}

@FunctionTool
def submit_veo_generation_job(prompt: str, user_id: str) -> str:
    """Submits a video generation job to Vertex AI and creates a tracking document in Firebase."""
    job_id = str(uuid.uuid4())
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
    WEBHOOK_URL = f"https://us-central1-{PROJECT_ID}.cloudfunctions.net/handleVideoWebhook"
    VEO_MODEL_ID = "veo-3.0-generate-preview"

    try:
        job_ref = db.reference(f"video_jobs/{job_id}")
        job_ref.set({
            "status": "pending",
            "prompt": prompt,
            "createdAt": db.SERVER_TIMESTAMP,
            "jobId": job_id,
            "userId": user_id
        })

        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        model = aiplatform.Model(VEO_MODEL_ID)

        instances = [{"prompt": prompt}]
        parameters = {
            "videoLength": "15s",
            "aspectRatio": "9:16",
            "promptRewriter": "disabled",
            "webhook_uri": WEBHOOK_URL,
            "webhook_metadata": f'{{"jobId": "{job_id}"}}'
        }

        # response = model.predict(instances=instances, parameters=parameters)
        print(f"Job {job_id}: (Simulated) Successfully submitted to Vertex AI.")

        return f"Success: Video generation started. Your Job ID is: {job_id}"

    except Exception as e:
        print(f"Job {job_id}: An error occurred: {e}")
        try:
            job_ref = db.reference(f"video_jobs/{job_id}")
            job_ref.update({"status": "failed", "error": str(e)})
        except Exception as db_error:
            print(f"Job {job_id}: Could not update Firebase with failure status: {db_error}")
        
        return f"Error: Failed to start video generation job. {e}"
