import os
import uuid
import firebase_admin
from firebase_admin import credentials, auth, db
from google.cloud import aiplatform
from google.adk.tools import FunctionTool
import time
import json
import requests
from typing import Optional
from google.auth import default
import google.auth.transport.requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import base64
from google.cloud import storage
from datetime import datetime, timedelta

# Import staging access control
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from staging_access_control import staging_access
    print("✅ Staging access control loaded")
except ImportError as e:
    print(f"⚠️  Staging access control not available: {e}")
    # Create a dummy staging_access object if import fails
    class DummyStagingAccess:
        def enforce_staging_access(self, *args, **kwargs):
            pass
        def get_staging_info(self):
            return {"environment": "unknown", "access_control": "disabled"}
    staging_access = DummyStagingAccess()

# --- Firebase Initialization ---
try:
    cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    database_url = os.getenv("FIREBASE_DATABASE_URL", "https://taajirah-default-rtdb.europe-west1.firebasedatabase.app")
    
    if cred_path:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url,
            'projectId': project_id,
            'databaseAuthVariableOverride': {
                'uid': 'service-account',
                'token': {
                    'email': 'taajirah-agents@taajirah.iam.gserviceaccount.com'
                }
            }
        })
    else:
        firebase_admin.initialize_app(options={
            'databaseURL': database_url,
            'projectId': project_id,
            'databaseAuthVariableOverride': {
                'uid': 'service-account',
                'token': {
                    'email': 'taajirah-agents@taajirah.iam.gserviceaccount.com'
                }
            }
        })
    print("Firebase Admin SDK initialized successfully for custom tools.")
except Exception as e:
    # If the app is already initialized, it will raise an error.
    if "already exists" not in str(e):
        print(f"CRITICAL: Failed to initialize Firebase Admin SDK for custom tools: {e}")

# Direct function version for FastAPI
def check_user_access_direct(user_id: str) -> bool:
    """Checks if a user has video generation permission - Direct function version for FastAPI"""
    try:
        # For test user, always allow
        if user_id == "test_user":
            return True
            
        # Check staging access first
        try:
            staging_access.enforce_staging_access(user_id)
        except Exception as e:
            print(f"Staging access denied for {user_id}: {e}")
            return False
            
        # Check Firebase custom claims
        user = auth.get_user(user_id)
        claims = user.custom_claims or {}
        return claims.get("can_generate_video", False)
        
    except Exception as e:
        print(f"Error checking user access for {user_id}: {e}")
        return False

# Keep the FunctionTool decorated version for ADK
@FunctionTool
def check_user_access(user_id: str) -> dict:
    """Checks the custom claims of a user to see if they have video generation permission."""
    try:
        # For test user, always allow
        if user_id == "test_user":
            return {"can_generate_video": True}
            
        # Check staging access first
        try:
            staging_access.enforce_staging_access(user_id)
        except Exception as e:
            return {"can_generate_video": False, "reason": str(e)}
            
        # Check Firebase custom claims
        user = auth.get_user(user_id)
        claims = user.custom_claims or {}
        return {"can_generate_video": claims.get("can_generate_video", False)}
    except Exception as e:
        print(f"Error checking user access for {user_id}: {e}")
        return {"can_generate_video": False, "error": str(e)}

def get_vertex_ai_credentials():
    """Get fresh credentials for Vertex AI"""
    try:
        # Get credentials path
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            
        # Initialize Firebase Admin SDK if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://taajirah-default-rtdb.europe-west1.firebasedatabase.app'
            })
            print("Firebase Admin SDK initialized successfully for custom tools.")
            
        # Get Vertex AI credentials
        request = Request()
        credentials = service_account.Credentials.from_service_account_file(
            cred_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        credentials.refresh(request)
        
        return credentials
        
    except Exception as e:
        raise Exception(f"Failed to get Vertex AI credentials: {str(e)}")

# Direct function version for FastAPI
def submit_video_job(prompt: str, user_id: str = "test-user", aspect_ratio: str = "16:9", duration_seconds: int = 8, sample_count: int = 1, person_generation: str = "allow_adult", generate_audio: bool = True) -> str:
    """Submit a video generation job to VEO3 - Direct function version for FastAPI"""
    try:
        # Check quota first
        quota = get_quota_status()
        if "error" in quota:
            return f"Error checking quota: {quota['error']}"
            
        # Create job ID and data
        job_id = str(uuid.uuid4())
        job_data = {
            "status": "pending",
            "prompt": prompt,
            "createdAt": int(time.time()),
            "jobId": job_id,
            "userId": user_id,
            "model": "veo-3.0-generate-preview",
            "parameters": {
                "aspectRatio": aspect_ratio,
                "durationSeconds": duration_seconds,
                "sampleCount": sample_count,
                "personGeneration": person_generation,
                "generateAudio": generate_audio
            },
            "estimatedCost": calculate_veo_cost_direct(duration_seconds, sample_count, generate_audio)
        }
        
        # If quota available, process immediately
        if quota["daily"]["remaining"] > 0 and quota["monthly"]["remaining"] > 0:
            # Enforce 16:9 aspect ratio for VEO3
            if aspect_ratio != "16:9":
                return f"Error: VEO3 only supports 16:9 (landscape) aspect ratio. Provided: {aspect_ratio}"
            
            # Get fresh credentials
            credentials = get_vertex_ai_credentials()
            
            # Create job ID
            job_ref = db.reference(f"video_jobs/{job_id}")
            job_data = {
                "status": "pending",
                "prompt": prompt,
                "createdAt": int(time.time()),
                "jobId": job_id,
                "userId": user_id,
                "model": "veo-3.0-generate-preview",
                "parameters": {
                    "aspectRatio": aspect_ratio,
                    "durationSeconds": duration_seconds,
                    "sampleCount": sample_count,
                    "personGeneration": person_generation,
                    "generateAudio": generate_audio
                },
                "estimatedCost": calculate_veo_cost_direct(duration_seconds, sample_count, generate_audio),
                "userPaysDirectly": True
            }
            
            job_ref.set(job_data)
            print(f"✅ Created Firebase tracking document for job {job_id}")
            
            # Submit to Vertex AI with retry logic
            PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "taajirah")
            LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            MODEL_ID = "veo-3.0-generate-preview"
            
            # Use the correct Veo 3 endpoint for prediction
            api_endpoint = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:predict"
            
            # Get storage bucket for output
            bucket_name = os.getenv("GOOGLE_CLOUD_STAGING_BUCKET", "gs://taajirah-adk-staging").replace("gs://", "")
            output_uri = f"gs://{bucket_name}/veo3/{job_id}/"
            
            request_payload = {
                "instances": [{
                    "prompt": prompt
                }],
                "parameters": {
                    "aspectRatio": aspect_ratio,
                    "durationSeconds": duration_seconds,
                    "sampleCount": sample_count,
                    "personGeneration": person_generation,
                    "generateAudio": generate_audio,
                    "enhancePrompt": True,
                    "outputUri": output_uri  # Tell Veo 3 where to store the videos
                }
            }
            
            # Retry configuration
            max_retries = 5
            base_delay = 60  # Start with 1 minute delay
            max_delay = 600  # Maximum delay of 10 minutes
            current_retry = 0
            
            while current_retry <= max_retries:
                try:
                    headers = {
                        "Authorization": f"Bearer {credentials.token}",
                        "Content-Type": "application/json"
                    }
                    
                    print(f"✅ Job {job_id}: Submitting to Vertex AI with token: {credentials.token[:10]}...")
                    print(f"✅ Job {job_id}: Using output URI: {output_uri}")
                    
                    response = requests.post(
                        api_endpoint,
                        headers=headers,
                        json=request_payload,
                        timeout=30
                    )
                    
                    if response.status_code == 429:
                        if current_retry < max_retries:
                            # Calculate exponential backoff delay
                            delay = min(base_delay * (2 ** current_retry), max_delay)
                            print(f"⏳ Job {job_id}: Quota exceeded. Retrying in {delay} seconds (attempt {current_retry + 1}/{max_retries})")
                            
                            # Update Firebase with retry status
                            job_ref.update({
                                "status": "retrying",
                                "retryAttempt": current_retry + 1,
                                "nextRetryIn": delay,
                                "lastError": response.text
                            })
                            
                            time.sleep(delay)
                            current_retry += 1
                            continue
                        else:
                            error_msg = f"Vertex AI API quota exceeded after {max_retries} retries: {response.text}"
                            print(f"❌ Job {job_id}: {error_msg}")
                            print(f"❌ Job {job_id}: Response headers: {dict(response.headers)}")
                            
                            job_ref.update({
                                "status": "failed",
                                "error": error_msg,
                                "failedAt": int(time.time()),
                                "retryAttempts": current_retry
                            })
                            
                            return f"Error: {error_msg}"
                    
                    elif response.status_code != 200:
                        error_msg = f"Vertex AI API returned status {response.status_code}: {response.text}"
                        print(f"❌ Job {job_id}: {error_msg}")
                        print(f"❌ Job {job_id}: Response headers: {dict(response.headers)}")
                        
                        job_ref.update({
                            "status": "failed",
                            "error": error_msg,
                            "failedAt": int(time.time())
                        })
                        
                        return f"Error: {error_msg}"
                    
                    # Parse the successful response
                    response_data = response.json()
                    
                    # Success! Break out of retry loop
                    break
                    
                except Exception as request_error:
                    if current_retry < max_retries:
                        delay = min(base_delay * (2 ** current_retry), max_delay)
                        print(f"⚠️ Job {job_id}: Request failed. Retrying in {delay} seconds (attempt {current_retry + 1}/{max_retries})")
                        print(f"⚠️ Error details: {str(request_error)}")
                        
                        job_ref.update({
                            "status": "retrying",
                            "retryAttempt": current_retry + 1,
                            "nextRetryIn": delay,
                            "lastError": str(request_error)
                        })
                        
                        time.sleep(delay)
                        current_retry += 1
                        continue
                    else:
                        error_msg = f"Failed to submit video generation job after {max_retries} retries: {str(request_error)}"
                        print(f"❌ Job {job_id}: {error_msg}")
                        
                        job_ref.update({
                            "status": "failed",
                            "error": error_msg,
                            "failedAt": int(time.time()),
                            "retryAttempts": current_retry
                        })
                        
                        return f"Error: {error_msg}"
            
            # Check if we got an immediate response or need to poll
            if "predictions" in response_data:
                # Immediate response - extract video URLs or data
                predictions = response_data.get("predictions", [{}])[0]
                video_urls = predictions.get("videoUrls", [])
                audio_urls = predictions.get("audioUrls", [])
                
                # If we got base64 data, save it
                if not video_urls and "videoData" in predictions:
                    try:
                        video_data = base64.b64decode(predictions["videoData"])
                        
                        # Save to Google Cloud Storage
                        storage_client = storage.Client()
                        bucket = storage_client.bucket(bucket_name)
                        
                        # Generate video filename
                        video_filename = f"veo3/{job_id}/video_{int(time.time())}.mp4"
                        blob = bucket.blob(video_filename)
                        
                        # Upload video
                        blob.upload_from_string(video_data, content_type="video/mp4")
                        
                        # Generate signed URL that expires in 24 hours
                        video_urls = [blob.generate_signed_url(
                            version="v4",
                            expiration=datetime.timedelta(hours=24),
                            method="GET"
                        )]
                        
                        print(f"✅ Job {job_id}: Saved video to storage: {video_filename}")
                        
                    except Exception as storage_error:
                        print(f"❌ Job {job_id}: Failed to save video to storage: {storage_error}")
                        # Continue with base64 data as fallback
                        video_urls = [f"data:video/mp4;base64,{predictions['videoData']}"]
                
                # Update Firebase with immediate results
                job_ref.update({
                    "status": "completed",
                    "completedAt": int(time.time()),
                    "result": {
                        "videoUrls": video_urls,
                        "audioUrls": audio_urls,
                        "storagePrefix": f"veo3/{job_id}/"
                    }
                })
                
                return f"Success: Job {job_id} completed immediately. Videos available at: {', '.join(video_urls)}"
                
            else:
                # Long-running operation - store operation name and return
                vertex_operation_name = response_data.get("name", "")
                
                print(f"✅ Job {job_id}: Successfully submitted to Vertex AI")
                print(f"✅ Job {job_id}: Operation name: {vertex_operation_name}")
                print(f"✅ Job {job_id}: Full response: {json.dumps(response_data, indent=2)}")
                
                # Update status to processing and store operation name
                job_ref.update({
                    "status": "processing",
                    "vertexAiJobId": vertex_operation_name,
                    "startedAt": int(time.time())
                })
                
                return f"Success: Job {job_id} submitted. Operation name: {vertex_operation_name}"
            
        else:
            # Add to queue
            if queue_video_job(job_id, job_data):
                return f"Job {job_id} queued - quota exceeded"
            else:
                return f"Error queueing job {job_id}"
                
    except Exception as e:
        error_msg = f"Error submitting video generation job: {str(e)}"
        print(f"❌ Error: {error_msg}")
        
        if 'job_id' in locals() and 'job_ref' in locals():
            job_ref.update({
                "status": "failed",
                "error": error_msg,
                "failedAt": int(time.time())
            })
        
        return f"Error: {error_msg}"

# Keep the FunctionTool decorated version for ADK
@FunctionTool
def submit_veo_generation_job(prompt: str, user_id: str = "test-user", aspect_ratio: str = "16:9", duration_seconds: int = 8, sample_count: int = 1, person_generation: str = "allow_adult", generate_audio: bool = True) -> str:
    """Submit a video generation job to VEO3"""
    return submit_video_job(prompt, user_id, aspect_ratio, duration_seconds, sample_count, person_generation, generate_audio)

# Direct function version for FastAPI
def check_video_status(job_id: str, user_api_key: Optional[str] = None) -> dict:
    """Check video job status - Direct function version for FastAPI"""
    try:
        job_ref = db.reference(f"video_jobs/{job_id}")
        job_data = job_ref.get()
        
        print(f"✅ Job {job_id}: Firebase data: {json.dumps(job_data, indent=2)}")
        
        if not job_data:
            return {
                "status": "not_found",
                "message": f"Job {job_id} not found"
            }
        
        # Get current status and timestamps
        current_status = job_data.get("status", "unknown")
        started_at = job_data.get("startedAt")
        vertex_operation_name = job_data.get("vertexAiJobId")
        
        # Check for timeout (5 minutes)
        if started_at and current_status == "processing":
            elapsed_time = int(time.time()) - started_at
            if elapsed_time > 300:  # 5 minutes
                error_msg = "Video generation timed out after 5 minutes"
                job_ref.update({
                    "status": "failed",
                    "error": error_msg,
                    "failedAt": int(time.time())
                })
                return {
                    "status": "failed",
                    "error": error_msg,
                    "jobId": job_id,
                    "elapsed_seconds": elapsed_time
                }
        
        # If we have a Vertex AI operation name and status is processing, check operation status
        if vertex_operation_name and current_status == "processing":
            try:
                # Get fresh credentials
                credentials = get_vertex_ai_credentials()
                
                # Get operation status
                PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "taajirah")
                LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
                
                operation_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/{vertex_operation_name}"
                
                headers = {
                    "Authorization": f"Bearer {credentials.token}",
                    "Content-Type": "application/json"
                }
                
                response = requests.get(
                    operation_url,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    operation_data = response.json()
                    print(f"✅ Job {job_id}: Operation data: {json.dumps(operation_data, indent=2)}")
                    
                    # Check if operation is done
                    if operation_data.get("done", False):
                        # Check for errors
                        if "error" in operation_data:
                            error = operation_data["error"]
                            error_msg = f"Vertex AI operation failed: {error.get('message', 'Unknown error')}"
                            
                            job_ref.update({
                                "status": "failed",
                                "error": error_msg,
                                "failedAt": int(time.time())
                            })
                            
                            return {
                                "status": "failed",
                                "error": error_msg,
                                "jobId": job_id
                            }
                            
                        # Operation successful - extract video data
                        result = operation_data.get("response", {})
                        print(f"✅ Job {job_id}: Full result: {json.dumps(result, indent=2)}")
                        
                        # Handle both possible response formats
                        predictions = result.get("predictions", [{}])[0]
                        
                        # Try to get video URLs first
                        video_urls = predictions.get("videoUrls", [])
                        audio_urls = predictions.get("audioUrls", [])
                        
                        # If no URLs, check for base64 data
                        if not video_urls and "videoData" in predictions:
                            # We have base64 video data - save to storage
                            try:
                                video_data = base64.b64decode(predictions["videoData"])
                                
                                # Save to Google Cloud Storage
                                storage_client = storage.Client()
                                bucket_name = os.getenv("GOOGLE_CLOUD_STAGING_BUCKET").replace("gs://", "")
                                bucket = storage_client.bucket(bucket_name)
                                
                                # Generate video filename
                                video_filename = f"veo3/{job_id}/video_{int(time.time())}.mp4"
                                blob = bucket.blob(video_filename)
                                
                                # Upload video
                                blob.upload_from_string(video_data, content_type="video/mp4")
                                
                                # Generate signed URL that expires in 24 hours
                                video_urls = [blob.generate_signed_url(
                                    version="v4",
                                    expiration=datetime.timedelta(hours=24),
                                    method="GET"
                                )]
                                
                                print(f"✅ Job {job_id}: Saved video to storage: {video_filename}")
                                
                            except Exception as storage_error:
                                print(f"❌ Job {job_id}: Failed to save video to storage: {storage_error}")
                                # Continue with base64 data as fallback
                                video_urls = [f"data:video/mp4;base64,{predictions['videoData']}"]
                        
                        print(f"✅ Job {job_id}: Video URLs: {video_urls}")
                        print(f"✅ Job {job_id}: Audio URLs: {audio_urls}")
                        
                        # Store everything in Firebase
                        job_ref.update({
                            "status": "completed",
                            "completedAt": int(time.time()),
                            "result": {
                                "videoUrls": video_urls,
                                "audioUrls": audio_urls,
                                "storagePrefix": f"veo3/{job_id}/" if video_urls else None
                            }
                        })
                        
                        return {
                            "status": "completed",
                            "jobId": job_id,
                            "videoUrls": video_urls,
                            "audioUrls": audio_urls,
                            "storagePrefix": f"veo3/{job_id}/" if video_urls else None
                        }
                        
                    else:
                        # Still processing
                        progress = operation_data.get("metadata", {}).get("progress", 0)
                        return {
                            "status": "processing",
                            "progress": progress,
                            "jobId": job_id,
                            "message": f"Video generation in progress ({progress}% complete)"
                        }
                        
                else:
                    print(f"⚠️ Job {job_id}: Failed to get operation status: {response.status_code} - {response.text}")
                    # Don't update status, just return current data
                    
            except Exception as operation_error:
                print(f"⚠️ Job {job_id}: Error checking operation status: {operation_error}")
                # Don't update status, just return current data
        
        # Return current data from Firebase
        return {
            "status": current_status,
            "jobId": job_id,
            "data": job_data
        }
        
    except Exception as e:
        error_msg = f"Error checking video status: {str(e)}"
        print(f"❌ Error: {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "jobId": job_id
        }

# Keep the FunctionTool decorated version for ADK
@FunctionTool
def get_video_job_status(job_id: str, user_api_key: Optional[str] = None) -> dict:
    """Retrieves the status of a video generation job and polls Vertex AI for updates."""
    return check_video_status(job_id, user_api_key)

# Direct function version for FastAPI
def calculate_veo_cost_direct(duration_seconds: int, sample_count: int, generate_audio: bool) -> float:
    """Calculate the estimated cost of a VEO3 video generation - Direct function version for FastAPI"""
    try:
        # Base cost per second
        base_cost_per_second = 0.50  # $0.50 per second
        audio_cost_per_second = 0.25  # Additional $0.25 per second for audio
        
        # Calculate base video cost
        base_cost = duration_seconds * base_cost_per_second
        
        # Add audio cost if requested
        if generate_audio:
            audio_cost = duration_seconds * audio_cost_per_second
            total_cost = base_cost + audio_cost
        else:
            total_cost = base_cost
            
        # Multiply by number of samples
        total_cost = total_cost * sample_count
        
        return round(total_cost, 2)  # Round to 2 decimal places
        
    except Exception as e:
        print(f"Error calculating VEO3 cost: {e}")
        return 0.00  # Return 0 on error

# Keep the FunctionTool decorated version for ADK
@FunctionTool
def calculate_veo_cost(duration_seconds: int, sample_count: int, generate_audio: bool) -> float:
    """Calculate the estimated cost of a VEO3 video generation."""
    return calculate_veo_cost_direct(duration_seconds, sample_count, generate_audio)

@FunctionTool
def get_veo_pricing_info() -> dict:
    """
    Return official Google Cloud Veo pricing information for user transparency.
    Users pay Google directly - no subscription needed!
    
    Source: https://cloud.google.com/vertex-ai/generative-ai/pricing#veo
    """
    return {
        "payment_model": "You pay Google Cloud directly - no subscription or markup!",
        "official_rates": {
            "veo_3_video": 0.50,           # $0.50/second - Video generation
            "veo_3_video_audio": 0.75,     # $0.75/second - Video + Audio generation
            "veo_2_video": 0.50,           # $0.50/second - Video generation
        },
        "example_costs": {
            "8_second_video": 4.00,        # 8s × $0.50
            "8_second_with_audio": 6.00,   # 8s × $0.75
            "4_videos_batch": 24.00,       # 4 × 6.00 (no discounts in Google pricing)
        },
        "what_you_need": {
            "google_cloud_account": "Free to create at cloud.google.com",
            "vertex_ai_api": "Enable in Google Cloud Console",
            "billing_setup": "Required for Google Cloud usage",
            "api_key": "Generate in Google Cloud Console"
        },
        "benefits": {
            "transparent_pricing": "Pay Google's actual rates, no markup",
            "usage_control": "You control your own spending limits",
            "no_subscription": "Generate as many or few videos as you want",
            "enterprise_ready": "Use your own Google Cloud quotas and limits"
        },
        "cost_tips": {
            "shorter_videos": "5-second videos cost less than 8-second",
            "video_only": "Skip audio to save 33% ($0.50 vs $0.75/second)",
            "batch_wisely": "Generate multiple videos in one request when possible"
        },
        "source": "https://cloud.google.com/vertex-ai/generative-ai/pricing#veo",
        "last_updated": "December 2024"
    }

@FunctionTool
def track_user_analytics(user_id: str, action: str, metadata: dict = None) -> str:
    """
    Track user actions for business analytics and optimization.
    """
    try:
        analytics_ref = db.reference(f"analytics/{user_id}")
        timestamp = int(time.time())
        
        analytics_data = {
            "action": action,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        # Store the analytics event
        analytics_ref.child(str(timestamp)).set(analytics_data)
        
        # Update user usage stats
        user_stats_ref = db.reference(f"user_stats/{user_id}")
        current_stats = user_stats_ref.get() or {}
        
        # Track key metrics
        current_stats["total_actions"] = current_stats.get("total_actions", 0) + 1
        current_stats["last_activity"] = timestamp
        current_stats[f"{action}_count"] = current_stats.get(f"{action}_count", 0) + 1
        
        # Calculate engagement score
        if action == "video_generated":
            current_stats["videos_generated"] = current_stats.get("videos_generated", 0) + 1
        elif action == "upgrade_clicked":
            current_stats["upgrade_interest"] = current_stats.get("upgrade_interest", 0) + 1
            
        user_stats_ref.set(current_stats)
        
        return f"Analytics tracked: {action} for user {user_id}"
        
    except Exception as e:
        print(f"Error tracking analytics: {e}")
        return f"Analytics tracking failed: {str(e)}"

@FunctionTool
def get_user_usage_stats(user_id: str) -> dict:
    """
    Get user's video generation statistics (for analytics only - no limits with API key model).
    """
    try:
        # Get current usage stats
        user_stats_ref = db.reference(f"user_stats/{user_id}")
        stats = user_stats_ref.get() or {}
        
        current_month = time.strftime("%Y-%m")
        current_day = time.strftime("%Y-%m-%d")
        
        monthly_usage = stats.get(f"monthly_usage_{current_month}", 0)
        daily_usage = stats.get(f"daily_usage_{current_day}", 0)
        total_usage = stats.get("total_videos_generated", 0)
        
        return {
            "usage_stats": {
                "today": daily_usage,
                "this_month": monthly_usage,
                "all_time": total_usage
            },
            "payment_model": "api_key",
            "limits": "You control your own spending via Google Cloud billing",
            "last_activity": stats.get("last_activity"),
            "note": "With API keys, you pay Google directly - no artificial limits!"
        }
        
    except Exception as e:
        print(f"Error getting usage stats: {e}")
        return {"usage_stats": {"error": str(e)}}

@FunctionTool
def update_user_usage(user_id: str) -> str:
    """
    Update user usage counters after successful video generation.
    """
    try:
        user_stats_ref = db.reference(f"user_stats/{user_id}")
        stats = user_stats_ref.get() or {}
        
        current_month = time.strftime("%Y-%m")
        current_day = time.strftime("%Y-%m-%d")
        
        # Update counters
        stats[f"monthly_usage_{current_month}"] = stats.get(f"monthly_usage_{current_month}", 0) + 1
        stats[f"daily_usage_{current_day}"] = stats.get(f"daily_usage_{current_day}", 0) + 1
        stats["total_videos_generated"] = stats.get("total_videos_generated", 0) + 1
        
        user_stats_ref.set(stats)
        
        return "Usage updated successfully"
        
    except Exception as e:
        print(f"Error updating usage: {e}")
        return f"Usage update failed: {str(e)}"

@FunctionTool
def get_business_analytics() -> dict:
    """
    Get aggregated business analytics for revenue optimization.
    """
    try:
        analytics_ref = db.reference("analytics")
        user_stats_ref = db.reference("user_stats")
        
        # Get basic metrics
        all_users = user_stats_ref.get() or {}
        
        total_users = len(all_users)
        total_videos = sum(stats.get("total_videos_generated", 0) for stats in all_users.values())
        
        # Calculate tier distribution
        tier_distribution = {"basic": 0, "pro": 0, "enterprise": 0}
        active_users = 0
        week_ago = int(time.time()) - (7 * 24 * 60 * 60)
        
        for user_id, stats in all_users.items():
            if stats.get("last_activity", 0) > week_ago:
                active_users += 1
                
        # Calculate revenue potential
        avg_videos_per_user = total_videos / max(total_users, 1)
        
        return {
            "total_users": total_users,
            "active_users_7d": active_users,
            "total_videos_generated": total_videos,
            "avg_videos_per_user": round(avg_videos_per_user, 2),
            "tier_distribution": tier_distribution,
            "growth_opportunities": {
                "upgrade_candidates": sum(1 for stats in all_users.values() 
                                        if stats.get("videos_generated", 0) >= 3),
                "high_usage_users": sum(1 for stats in all_users.values() 
                                      if stats.get("total_videos_generated", 0) > 10)
            }
        }
        
    except Exception as e:
        print(f"Error getting business analytics: {e}")
        return {"error": str(e)}

@FunctionTool
def get_api_key_setup_guide(user_id: str = None) -> dict:
    """
    Provide step-by-step guide for users to set up their Google Cloud API key.
    """
    try:
        # Get user stats if available
        usage_info = {}
        if user_id:
            user_stats_ref = db.reference(f"user_stats/{user_id}")
            stats = user_stats_ref.get() or {}
            total_videos = stats.get("total_videos_generated", 0)
            usage_info = {"previous_videos": total_videos}
        
        return {
            "setup_steps": {
                "1_create_account": {
                    "title": "Create Google Cloud Account",
                    "description": "Sign up at cloud.google.com (free with $300 credit)",
                    "url": "https://cloud.google.com/",
                    "time": "2 minutes"
                },
                "2_enable_apis": {
                    "title": "Enable Vertex AI API",
                    "description": "Go to APIs & Services > Enable APIs > Search 'Vertex AI'",
                    "url": "https://console.cloud.google.com/apis/enableflow?apiid=aiplatform.googleapis.com",
                    "time": "1 minute"
                },
                "3_setup_billing": {
                    "title": "Set up Billing",
                    "description": "Add a payment method (required for Vertex AI)",
                    "url": "https://console.cloud.google.com/billing/",
                    "time": "2 minutes"
                },
                "4_create_api_key": {
                    "title": "Create API Key",
                    "description": "Go to APIs & Services > Credentials > Create API Key",
                    "url": "https://console.cloud.google.com/apis/credentials",
                    "time": "1 minute"
                },
                "5_secure_key": {
                    "title": "Secure Your Key",
                    "description": "Restrict API key to Vertex AI service only",
                    "note": "Important: Never share your API key publicly",
                    "time": "1 minute"
                }
            },
            "cost_transparency": {
                "google_charges": "You pay Google Cloud directly at their official rates",
                "no_markup": "82ndrop doesn't add any fees - we just provide the AI interface",
                "example_cost": "$6.00 for an 8-second video with audio"
            },
            "benefits": {
                "control": "You control your own spending limits in Google Cloud",
                "transparency": "See exactly what you're paying for in Google Cloud Console",
                "enterprise": "Use your company's existing Google Cloud billing and quotas",
                "no_subscription": "Pay only for what you generate"
            },
            "troubleshooting": {
                "api_errors": "Check that Vertex AI API is enabled and billing is set up",
                "permission_denied": "Ensure your API key has Vertex AI permissions",
                "quota_exceeded": "Increase quotas in Google Cloud Console"
            },
            "user_info": usage_info,
            "estimated_setup_time": "5-10 minutes total"
        }
        
    except Exception as e:
        print(f"Error generating setup guide: {e}")
        return {"error": str(e)}

@FunctionTool 
def get_staging_environment_info() -> dict:
    """Get information about the current staging environment and access controls"""
    try:
        info = staging_access.get_staging_info()
        info.update({
            "video_generation_costs": {
                "veo_3_video": "$0.50/second",
                "veo_3_video_audio": "$0.75/second", 
                "example_8_second_video": "$4.00",
                "example_8_second_with_audio": "$6.00"
            },
            "protection_reason": "Videos cost real money - staging environment is locked down",
            "current_environment": os.getenv("ENVIRONMENT", "unknown")
        })
        return info
    except Exception as e:
        return {"error": str(e), "environment": "unknown"}

@FunctionTool
def generate_video_complete(prompt: str, user_api_key: Optional[str] = None, user_id: str = "system", aspect_ratio: str = "16:9", 
                          duration_seconds: int = 8, sample_count: int = 1, 
                          person_generation: str = "allow_adult", negative_prompt: Optional[str] = None,
                          generate_audio: bool = True, user_project_id: Optional[str] = None) -> dict:
    """
    Generates a complete video using VEO3 and returns the actual MP4 video URLs.
    This function waits for completion (2-3 minutes) and returns the final video files.
    
    Args:
        prompt: The text prompt for video generation
        user_api_key: User's Google Cloud API key or service account JSON
        user_id: User ID for tracking (defaults to "system")
        aspect_ratio: "16:9" (landscape - VEO3 supported) or "9:16" (portrait - not supported by VEO3)
        duration_seconds: Video duration in seconds (Veo 3 uses 8 seconds)
        sample_count: Number of video variations to generate (1-4)
        person_generation: "dont_allow", "allow_adult", or "allow_all"
        negative_prompt: Optional negative prompt to discourage certain elements
        generate_audio: Whether to generate synchronized audio (Veo 3 feature)
        user_project_id: User's Google Cloud Project ID (if different from API key)
    
    Returns: Dictionary with video URLs and metadata, or error information
    """
    
    # Step 1: Submit the video generation job
    try:
        result = submit_video_job(
            prompt=prompt,
            user_id=user_id,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            sample_count=sample_count,
            person_generation=person_generation,
            generate_audio=generate_audio
        )
        
        # Extract job ID from the success message
        if "Success: Job" in result:
            job_id = result.split("Success: Job")[1].split(" ")[0].strip()
        else:
            # If submission failed, return the error
            return {
                "status": "failed",
                "error": result,
                "videos": []
            }
            
    except Exception as e:
        return {
            "status": "failed", 
            "error": f"Failed to submit video generation job: {str(e)}",
            "videos": []
        }
    
    # Step 2: Wait for completion and poll for results
    max_wait_time = 300  # 5 minutes maximum wait
    poll_interval = 15   # Check every 15 seconds
    elapsed_time = 0
    
    print(f"🎬 Waiting for VEO3 to generate video(s) for job {job_id}...")
    print(f"⏱️ This typically takes 2-3 minutes. Will check every {poll_interval} seconds.")
    
    while elapsed_time < max_wait_time:
        try:
            status_result = check_video_status(job_id, user_api_key)
            current_status = status_result.get("status", "unknown")
            
            if current_status == "completed":
                video_urls = status_result.get("data", {}).get("result", {}).get("videoUrls", [])
                
                if video_urls:
                    estimated_cost = status_result.get("data", {}).get("estimatedCost", 0)
                    audio_status = "with synchronized audio" if generate_audio else "video only"
                    
                    print(f"✅ Video generation completed! Generated {len(video_urls)} video(s)")
                    
                    return {
                        "status": "completed",
                        "videos": video_urls,
                        "job_id": job_id,
                        "prompt": prompt,
                        "parameters": {
                            "aspect_ratio": aspect_ratio,
                            "duration_seconds": duration_seconds,
                            "sample_count": sample_count,
                            "generate_audio": generate_audio
                        },
                        "estimated_cost": estimated_cost,
                        "generation_time_seconds": elapsed_time,
                        "message": f"🎉 Success! Generated {len(video_urls)} VEO3 video{'s' if len(video_urls) > 1 else ''} ({audio_status})"
                    }
                else:
                    return {
                        "status": "failed",
                        "error": "Video generation completed but no video URLs were returned",
                        "videos": [],
                        "job_id": job_id
                    }
                    
            elif current_status == "failed":
                error_msg = status_result.get("error", "Unknown error occurred")
                return {
                    "status": "failed",
                    "error": f"Video generation failed: {error_msg}",
                    "videos": [],
                    "job_id": job_id
                }
                
            elif current_status in ["pending", "processing"]:
                # Still processing, continue waiting
                print(f"⏳ Still generating... ({elapsed_time}s elapsed)")
                time.sleep(poll_interval)
                elapsed_time += poll_interval
                
            else:
                # Unknown status, continue waiting but log it
                print(f"🤔 Unknown status '{current_status}', continuing to wait...")
                time.sleep(poll_interval)
                elapsed_time += poll_interval
                
        except Exception as poll_error:
            print(f"⚠️ Error checking status: {poll_error}")
            time.sleep(poll_interval)
            elapsed_time += poll_interval
    
    # Timeout reached
    return {
        "status": "timeout",
        "error": f"Video generation timed out after {max_wait_time} seconds. The job may still be processing.",
        "videos": [],
        "job_id": job_id,
        "prompt": prompt
    }

def get_quota_status() -> dict:
    """Get current quota status and limits"""
    try:
        quota_ref = db.reference("quota_tracking")
        now = int(time.time())
        
        # Get or initialize daily quota
        daily_ref = quota_ref.child("daily")
        daily_data = daily_ref.get() or {
            "current_usage": 0,
            "limit": 1000,  # Default daily limit
            "reset_time": now + (24 * 60 * 60)  # Reset in 24 hours
        }
        
        # Get or initialize monthly quota
        monthly_ref = quota_ref.child("monthly")
        monthly_data = monthly_ref.get() or {
            "current_usage": 0,
            "limit": 10000,  # Default monthly limit
            "reset_time": now + (30 * 24 * 60 * 60)  # Reset in 30 days
        }
        
        # Check if quotas need reset
        if now > daily_data["reset_time"]:
            daily_data = {
                "current_usage": 0,
                "limit": daily_data["limit"],
                "reset_time": now + (24 * 60 * 60)
            }
            daily_ref.set(daily_data)
            
        if now > monthly_data["reset_time"]:
            monthly_data = {
                "current_usage": 0,
                "limit": monthly_data["limit"],
                "reset_time": now + (30 * 24 * 60 * 60)
            }
            monthly_ref.set(monthly_data)
            
        return {
            "daily": {
                "current_usage": daily_data["current_usage"],
                "remaining": daily_data["limit"] - daily_data["current_usage"],
                "limit": daily_data["limit"],
                "reset_in_seconds": daily_data["reset_time"] - now
            },
            "monthly": {
                "current_usage": monthly_data["current_usage"],
                "remaining": monthly_data["limit"] - monthly_data["current_usage"],
                "limit": monthly_data["limit"],
                "reset_in_seconds": monthly_data["reset_time"] - now
            }
        }
        
    except Exception as e:
        print(f"Error getting quota status: {e}")
        return {"error": str(e)}

def update_quota_usage(increment: int = 1) -> bool:
    """Update quota usage counters"""
    try:
        quota_ref = db.reference("quota_tracking")
        now = int(time.time())
        
        # Update daily quota
        daily_ref = quota_ref.child("daily")
        daily_data = daily_ref.get() or {
            "current_usage": 0,
            "limit": 1000,
            "reset_time": now + (24 * 60 * 60)
        }
        
        # Reset if needed
        if now > daily_data["reset_time"]:
            daily_data = {
                "current_usage": increment,
                "limit": daily_data["limit"],
                "reset_time": now + (24 * 60 * 60)
            }
        else:
            daily_data["current_usage"] += increment
            
        # Check if we'd exceed limit
        if daily_data["current_usage"] > daily_data["limit"]:
            return False
            
        # Update monthly quota
        monthly_ref = quota_ref.child("monthly")
        monthly_data = monthly_ref.get() or {
            "current_usage": 0,
            "limit": 10000,
            "reset_time": now + (30 * 24 * 60 * 60)
        }
        
        # Reset if needed
        if now > monthly_data["reset_time"]:
            monthly_data = {
                "current_usage": increment,
                "limit": monthly_data["limit"],
                "reset_time": now + (30 * 24 * 60 * 60)
            }
        else:
            monthly_data["current_usage"] += increment
            
        # Check if we'd exceed limit
        if monthly_data["current_usage"] > monthly_data["limit"]:
            return False
            
        # Update both quotas
        daily_ref.set(daily_data)
        monthly_ref.set(monthly_data)
        
        return True
        
    except Exception as e:
        print(f"Error updating quota usage: {e}")
        return False

def queue_video_job(job_id: str, job_data: dict) -> bool:
    """Add a job to the processing queue"""
    try:
        # Add to queue
        queue_ref = db.reference(f"video_jobs/queued/{job_id}")
        job_data["queuedAt"] = int(time.time())
        queue_ref.set(job_data)
        
        print(f"✅ Added job {job_id} to queue")
        return True
        
    except Exception as e:
        print(f"Error queueing job: {e}")
        return False

def process_queued_jobs() -> None:
    """Process queued jobs if quota allows"""
    try:
        # Get quota status
        quota = get_quota_status()
        if "error" in quota:
            print(f"Error checking quota: {quota['error']}")
            return
            
        # Check if we have quota available
        if quota["daily"]["remaining"] <= 0:
            print(f"⚠️ Daily quota exceeded. Next reset in {quota['daily']['reset_in_seconds']} seconds")
            return
            
        if quota["monthly"]["remaining"] <= 0:
            print(f"⚠️ Monthly quota exceeded. Next reset in {quota['monthly']['reset_in_seconds']} seconds")
            return
            
        # Get queued jobs
        queue_ref = db.reference("video_jobs/queued")
        queued_jobs = queue_ref.get() or {}
        
        if not queued_jobs:
            return
            
        # Sort by queue time
        sorted_jobs = sorted(
            [(job_id, data) for job_id, data in queued_jobs.items()],
            key=lambda x: x[1].get("queuedAt", 0)
        )
        
        # Process oldest job first
        job_id, job_data = sorted_jobs[0]
        
        # Move to processing
        processing_ref = db.reference(f"video_jobs/processing/{job_id}")
        processing_ref.set(job_data)
        
        # Remove from queue
        queue_ref.child(job_id).delete()
        
        print(f"✅ Processing queued job {job_id}")
        
        # Submit the job
        result = submit_video_job(
            prompt=job_data["prompt"],
            user_id=job_data["userId"],
            aspect_ratio=job_data["parameters"]["aspectRatio"],
            duration_seconds=job_data["parameters"]["durationSeconds"],
            sample_count=job_data["parameters"]["sampleCount"],
            person_generation=job_data["parameters"]["personGeneration"],
            generate_audio=job_data["parameters"]["generateAudio"]
        )
        
        if "Error" in result:
            # Move to failed
            failed_ref = db.reference(f"video_jobs/failed/{job_id}")
            job_data["error"] = result
            job_data["failedAt"] = int(time.time())
            failed_ref.set(job_data)
            
            # Remove from processing
            processing_ref.delete()
            
        # Update quota usage
        update_quota_usage()
        
    except Exception as e:
        print(f"Error processing queue: {e}")
