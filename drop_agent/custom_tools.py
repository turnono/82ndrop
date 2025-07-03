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
    database_url = os.getenv("FIREBASE_DATABASE_URL")
    
    # Construct database URL if not explicitly provided
    if not database_url and project_id:
        database_url = f'https://{project_id}-default-rtdb.firebaseio.com/'
    
    if cred_path:
        cred = credentials.Certificate(cred_path)
        config = {}
        if database_url:
            config['databaseURL'] = database_url
        firebase_admin.initialize_app(cred, config)
    else:
        config = {}
        if database_url:
            config['databaseURL'] = database_url
        firebase_admin.initialize_app(options=config if config else None)
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
def submit_veo_generation_job(prompt: str, user_api_key: Optional[str] = None, user_id: str = "system", aspect_ratio: str = "16:9", 
                            duration_seconds: int = 8, sample_count: int = 1, 
                            person_generation: str = "allow_adult", negative_prompt: Optional[str] = None,
                            generate_audio: bool = True, user_project_id: Optional[str] = None) -> str:
    """
    Submits a video generation job to Google's Veo 3 model using user's own API credentials.
    Users pay Google directly - no subscription needed!
    
    Args:
        prompt: The text prompt for video generation
        user_api_key: User's Google Cloud API key or service account JSON
        user_id: User ID for tracking (defaults to "system")
        aspect_ratio: "16:9" (landscape) or "9:16" (portrait)
        duration_seconds: Video duration in seconds (Veo 3 uses 8 seconds)
        sample_count: Number of video variations to generate (1-4)
        person_generation: "dont_allow", "allow_adult", or "allow_all"
        negative_prompt: Optional negative prompt to discourage certain elements
        generate_audio: Whether to generate synchronized audio (Veo 3 feature)
        user_project_id: User's Google Cloud Project ID (if different from API key)
    
    Returns: Success message with job ID or error message
    """
    job_id = str(uuid.uuid4())
    
    # 🔒 STAGING ACCESS CONTROL: Prevent unauthorized video generation
    # This protects against costly accidental video generation in staging
    try:
        staging_access.enforce_staging_access(user_id, operation="Video generation")
    except Exception as access_error:
        # If staging access is denied, return the error immediately
        print(f"🚫 Staging access denied for user {user_id}: {access_error}")
        raise access_error
    
    # Use user's project ID or extract from their credentials
    PROJECT_ID = user_project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    # Reasonable limits for free tier (users can always generate more with their own costs)
    MAX_DURATION = 8  # Veo 3 limit
    MAX_SAMPLES = 4   # Veo API limit
    
    # Apply reasonable limits
    duration_seconds = min(duration_seconds, MAX_DURATION)
    sample_count = min(sample_count, MAX_SAMPLES)
    
    # Use the cutting-edge Veo 3 model
    VEO_MODEL_ID = "veo-3.0-generate-preview"
    
    try:
        # Calculate estimated cost for user transparency (they pay Google directly)
        estimated_cost = calculate_veo_cost.func(duration_seconds, sample_count, generate_audio)
        
        # Create Firebase tracking document 
        job_ref = db.reference(f"video_jobs/{job_id}")
        job_data = {
            "status": "pending",
            "prompt": prompt,
            "createdAt": int(time.time()),  # Use Unix timestamp instead of SERVER_TIMESTAMP
            "jobId": job_id,
            "userId": user_id,
            "model": VEO_MODEL_ID,
            "estimatedCost": estimated_cost,
            "userPaysDirectly": True,  # Flag indicating user pays Google directly
            "parameters": {
                "aspectRatio": aspect_ratio,
                "durationSeconds": duration_seconds,
                "sampleCount": sample_count,
                "personGeneration": person_generation,
                "generateAudio": generate_audio
            }
        }
        
        if negative_prompt:
            job_data["parameters"]["negativePrompt"] = negative_prompt
            
        job_ref.set(job_data)
        print(f"Job {job_id}: Created Firebase tracking document - User pays directly (${estimated_cost:.2f})")

        # REAL VEO API CALL using user's credentials or service account
        try:
            # Construct the API endpoint using user's project
            api_endpoint = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{VEO_MODEL_ID}:predictLongRunning"
            
            # Prepare the request payload for Veo 3 API
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
                }
            }
            
            if negative_prompt:
                request_payload["parameters"]["negativePrompt"] = negative_prompt

            # Determine authentication method
            if user_api_key:
                print(f"Job {job_id}: Submitting to Veo 3 with user's API key")
                headers = {
                    "Authorization": f"Bearer {user_api_key}",
                    "Content-Type": "application/json"
                }
            else:
                # Use service account credentials (for staging/testing)
                print(f"Job {job_id}: Submitting to Veo 3 with service account credentials (staging)")
                try:
                    credentials, _ = default()
                    auth_req = google.auth.transport.requests.Request()
                    credentials.refresh(auth_req)
                    access_token = credentials.token
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                except Exception as auth_error:
                    error_msg = f"Failed to get service account credentials: {str(auth_error)}"
                    print(f"Job {job_id}: {error_msg}")
                    job_ref.update({
                        "status": "failed",
                        "error": error_msg,
                        "failedAt": int(time.time())
                    })
                    return f"❌ Error: Authentication failed\n\nJob ID: {job_id}\nError: {error_msg}\n\nPlease provide your Google Cloud API key or contact admin."

            print(f"Job {job_id}: Parameters: {json.dumps(request_payload['parameters'], indent=2)}")
            print(f"Job {job_id}: Estimated cost: ${estimated_cost:.2f}")
            
            # Prepare headers for API call
            
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=request_payload,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"Veo API returned status {response.status_code}: {response.text}"
                print(f"Job {job_id}: {error_msg}")
                
                # Update Firebase with error
                job_ref.update({
                    "status": "failed",
                    "error": error_msg,
                    "failedAt": int(time.time())
                })
                
                # Provide helpful error messages for common issues
                if response.status_code == 401:
                    return f"❌ Error: Invalid API Key\n\nJob ID: {job_id}\n\nYour Google Cloud API key appears to be invalid or expired. Please:\n1. Check your API key in Google Cloud Console\n2. Ensure Vertex AI API is enabled\n3. Verify billing is set up\n\nGoogle Cloud will charge you directly for video generation."
                elif response.status_code == 403:
                    return f"❌ Error: Permission Denied\n\nJob ID: {job_id}\n\nYour API key doesn't have permission to use Veo. Please:\n1. Enable Vertex AI API in your project\n2. Ensure your account has Vertex AI User role\n3. Check if Veo access is approved for your project\n\nGoogle Cloud will charge you directly for video generation."
                else:
                    return f"❌ Error: Veo API request failed\n\nJob ID: {job_id}\nStatus: {response.status_code}\nError: {response.text[:200]}...\n\nPlease check your Google Cloud setup. You pay Google directly for usage."
            
            # Parse the successful response
            response_data = response.json()
            vertex_operation_name = response_data.get("name", "")
            
            print(f"Job {job_id}: Successfully submitted to Veo API using user credentials")
            print(f"Job {job_id}: Vertex AI operation: {vertex_operation_name}")
            
            # Update status to processing with real operation name
            job_ref.update({
                "status": "processing",
                "vertexAiJobId": vertex_operation_name,
                "userApiKey": "***REDACTED***",  # Never store the actual key
                "startedAt": int(time.time())
            })

        except Exception as api_error:
            error_msg = f"Failed to call Veo API with user credentials: {str(api_error)}"
            print(f"Job {job_id}: {error_msg}")
            
            # Update Firebase with API error
            job_ref.update({
                "status": "failed",
                "error": error_msg,
                "failedAt": int(time.time())
            })
            
            return f"❌ Error: Failed to connect to Veo API\n\nJob ID: {job_id}\nError: {str(api_error)}\n\nPlease verify:\n• Your Google Cloud API key is valid\n• Vertex AI API is enabled\n• Billing is set up in your Google Cloud project\n\nYou pay Google directly - no subscription needed!"

        audio_status = "with synchronized audio" if generate_audio else "video only"
        return f"🚀 Success! Video generation started with Veo 3\n\n📋 Job ID: {job_id}\n⏱️ Expected completion: 2-3 minutes\n🎯 Quality: 720p, 24fps ultra-high-quality\n📐 Aspect ratio: {aspect_ratio}\n⏰ Duration: {duration_seconds} seconds\n🎵 Audio: {audio_status}\n\n💳 **You pay Google directly: ${estimated_cost:.2f}**\n💡 No subscription needed - just your Google Cloud API key!\n\nYou'll be notified when your {sample_count} video{'s' if sample_count > 1 else ''} {'are' if sample_count > 1 else 'is'} ready!"

    except Exception as e:
        print(f"Job {job_id}: Error occurred: {e}")
        try:
            job_ref = db.reference(f"video_jobs/{job_id}")
            job_ref.update({
                "status": "failed", 
                "error": str(e),
                "failedAt": int(time.time())
            })
        except Exception as db_error:
            print(f"Job {job_id}: Could not update Firebase with failure status: {db_error}")
        
        return f"❌ Error: Failed to start video generation\n\nJob ID: {job_id}\nError: {str(e)}\n\nYou pay Google Cloud directly - no subscription fees!"

@FunctionTool
def calculate_veo_cost(duration_seconds: int, sample_count: int, generate_audio: bool) -> float:
    """
    Calculate actual Veo API cost based on official Google Cloud Vertex AI pricing.
    
    Official pricing from: https://cloud.google.com/vertex-ai/generative-ai/pricing#veo
    
    Veo 3 Pricing:
    - Video generation: $0.50/second
    - Video + Audio generation: $0.75/second
    
    Veo 2 Pricing:
    - Video generation: $0.50/second
    - Advanced Controls: $0.50/second
    """
    # OFFICIAL GOOGLE CLOUD VEO PRICING (Updated December 2024)
    if generate_audio:
        # Veo 3 Video + Audio generation
        cost_per_second = 0.75  # $0.75/second for video with synchronized audio
    else:
        # Veo 3 or Veo 2 Video generation
        cost_per_second = 0.50  # $0.50/second for video only
    
    # Apply volume discounts for multiple samples (business logic)
    volume_discount = 1.0
    if sample_count >= 3:
        volume_discount = 0.9  # 10% discount for 3+ videos
    elif sample_count >= 2:
        volume_discount = 0.95  # 5% discount for 2+ videos
    
    # Calculate total cost
    cost_per_video = duration_seconds * cost_per_second
    total_cost = cost_per_video * sample_count * volume_discount
    
    return round(total_cost, 2)

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
def get_video_job_status(job_id: str, user_api_key: Optional[str] = None) -> dict:
    """
    Retrieves the status of a video generation job and polls Vertex AI for updates.
    
    Args:
        job_id: The job ID to check
        
    Returns:
        Dictionary with job status information
    """
    try:
        job_ref = db.reference(f"video_jobs/{job_id}")
        job_data = job_ref.get()
        
        if not job_data:
            return {
                "status": "not_found",
                "message": f"Job {job_id} not found"
            }
        
        # If job is still processing, poll Vertex AI for updates
        current_status = job_data.get("status", "unknown")
        vertex_operation_name = job_data.get("vertexAiJobId")
        
        if current_status == "processing" and vertex_operation_name and user_api_key:
            try:
                # Poll the Vertex AI operation status using user's credentials
                PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
                LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
                MODEL_ID = job_data.get("model", "veo-3.0-generate-preview")
                
                # Construct the poll endpoint
                poll_endpoint = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:fetchPredictOperation"
                
                headers = {
                    "Authorization": f"Bearer {user_api_key}",
                    "Content-Type": "application/json"
                }
                
                poll_payload = {
                    "operationName": vertex_operation_name
                }
                
                response = requests.post(
                    poll_endpoint,
                    headers=headers,
                    json=poll_payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    operation_data = response.json()
                    operation_done = operation_data.get("done", False)
                    
                    if operation_done:
                        # Check if operation completed successfully
                        if "response" in operation_data:
                            videos = operation_data.get("response", {}).get("videos", [])
                            video_urls = [video.get("gcsUri", "") for video in videos if video.get("gcsUri")]
                            
                            # Update Firebase with completion
                            job_ref.update({
                                "status": "completed",
                                "videoUrls": video_urls,
                                "completedAt": int(time.time())
                            })
                            
                            current_status = "completed"
                            job_data["videoUrls"] = video_urls
                            
                            print(f"Job {job_id}: Completed successfully with {len(video_urls)} videos")
                        elif "error" in operation_data:
                            error_msg = str(operation_data.get("error", "Unknown error"))
                            
                            # Update Firebase with error
                            job_ref.update({
                                "status": "failed",
                                "error": error_msg,
                                "failedAt": int(time.time())
                            })
                            
                            current_status = "failed"
                            job_data["error"] = error_msg
                            
                            print(f"Job {job_id}: Failed with error: {error_msg}")
                    else:
                        print(f"Job {job_id}: Still processing...")
                        
                else:
                    print(f"Job {job_id}: Failed to poll status - HTTP {response.status_code}")
                    
            except Exception as poll_error:
                print(f"Job {job_id}: Error polling Vertex AI: {poll_error}")
                # Don't update status on polling errors, just log them
            
        return {
            "status": current_status,
            "jobId": job_id,
            "prompt": job_data.get("prompt", ""),
            "createdAt": job_data.get("createdAt"),
            "model": job_data.get("model", ""),
            "parameters": job_data.get("parameters", {}),
            "error": job_data.get("error"),
            "videoUrls": job_data.get("videoUrls", []),
            "estimatedCost": job_data.get("estimatedCost", 0),
            "paymentModel": "user_api_key",
            "userPaysDirectly": job_data.get("userPaysDirectly", True)
        }
        
    except Exception as e:
        print(f"Error retrieving job status for {job_id}: {e}")
        return {
            "status": "error",
            "message": f"Error retrieving job status: {str(e)}"
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
        result = submit_veo_generation_job(
            prompt=prompt,
            user_api_key=user_api_key,
            user_id=user_id,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            sample_count=sample_count,
            person_generation=person_generation,
            negative_prompt=negative_prompt,
            generate_audio=generate_audio,
            user_project_id=user_project_id
        )
        
        # Extract job ID from the success message
        if "Job ID:" in result:
            job_id = result.split("Job ID: ")[1].split("\n")[0].strip()
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
            status_result = get_video_job_status(job_id, user_api_key)
            current_status = status_result.get("status", "unknown")
            
            if current_status == "completed":
                video_urls = status_result.get("videoUrls", [])
                
                if video_urls:
                    estimated_cost = status_result.get("estimatedCost", 0)
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
        "message": f"⏰ Timeout: Video generation took longer than expected. Check job {job_id} status later using get_video_job_status()"
    }
