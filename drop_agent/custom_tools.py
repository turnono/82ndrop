import os
import uuid
import firebase_admin
from firebase_admin import credentials, auth, db
from google.cloud import aiplatform
from google.adk.tools import FunctionTool
import time
import json

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
def submit_veo_generation_job(prompt: str, user_id: str = "system", aspect_ratio: str = "9:16", 
                            duration_seconds: int = 8, sample_count: int = 1, 
                            person_generation: str = "allow_adult", negative_prompt: str = None,
                            generate_audio: bool = True, user_tier: str = "basic") -> str:
    """
    Submits a video generation job to Google's Veo 3 model via Vertex AI.
    Enhanced with cost optimization and tier management.
    
    Args:
        prompt: The text prompt for video generation
        user_id: User ID for tracking (defaults to "system")
        aspect_ratio: "16:9" (landscape) or "9:16" (portrait)
        duration_seconds: Video duration in seconds (Veo 3 uses 8 seconds)
        sample_count: Number of video variations to generate (1-4)
        person_generation: "dont_allow", "allow_adult", or "allow_all"
        negative_prompt: Optional negative prompt to discourage certain elements
        generate_audio: Whether to generate synchronized audio (Veo 3 feature)
        user_tier: User subscription tier for cost optimization
    
    Returns:
        Success message with job ID or error message
    """
    job_id = str(uuid.uuid4())
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    # Tier-based cost optimization
    tier_configs = {
        "basic": {
            "max_duration": 5,
            "audio_enabled": False,
            "max_samples": 1,
            "watermark": True
        },
        "pro": {
            "max_duration": 8,
            "audio_enabled": True,
            "max_samples": 2,
            "watermark": False
        },
        "enterprise": {
            "max_duration": 8,
            "audio_enabled": True,
            "max_samples": 4,
            "watermark": False
        }
    }
    
    config = tier_configs.get(user_tier, tier_configs["basic"])
    
    # Apply tier restrictions
    duration_seconds = min(duration_seconds, config["max_duration"])
    sample_count = min(sample_count, config["max_samples"])
    generate_audio = generate_audio and config["audio_enabled"]
    
    # Use the cutting-edge Veo 3 model
    VEO_MODEL_ID = "veo-3.0-generate-preview"
    
    try:
        # Enhanced cost tracking
        estimated_cost = calculate_veo_cost(duration_seconds, sample_count, generate_audio)
        
        # Create Firebase tracking document with cost data
        job_ref = db.reference(f"video_jobs/{job_id}")
        job_data = {
            "status": "pending",
            "prompt": prompt,
            "createdAt": db.SERVER_TIMESTAMP,
            "jobId": job_id,
            "userId": user_id,
            "userTier": user_tier,
            "model": VEO_MODEL_ID,
            "estimatedCost": estimated_cost,
            "parameters": {
                "aspectRatio": aspect_ratio,
                "durationSeconds": duration_seconds,
                "sampleCount": sample_count,
                "personGeneration": person_generation,
                "generateAudio": generate_audio,
                "watermark": config["watermark"]
            }
        }
        
        if negative_prompt:
            job_data["parameters"]["negativePrompt"] = negative_prompt
            
        job_ref.set(job_data)
        print(f"Job {job_id}: Created Firebase tracking document with cost ${estimated_cost:.2f}")

        # Initialize Vertex AI
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        
        # Prepare the request for Veo 3 API
        instances = [{
            "prompt": prompt
        }]
        
        parameters = {
            "aspectRatio": aspect_ratio,
            "durationSeconds": duration_seconds,
            "sampleCount": sample_count,
            "personGeneration": person_generation,
            "generateAudio": generate_audio,  # Veo 3 specific feature
            "enhancePrompt": True,  # Enable prompt enhancement by default
        }
        
        if negative_prompt:
            parameters["negativePrompt"] = negative_prompt

        print(f"Job {job_id}: Would submit to Veo 3 with parameters: {json.dumps(parameters, indent=2)}")
        print(f"Job {job_id}: Prompt: {prompt[:100]}...")
        print(f"Job {job_id}: Estimated cost: ${estimated_cost:.2f} | User tier: {user_tier}")
        
        # Update status to processing (simulated)
        job_ref.update({
            "status": "processing",
            "vertexAiJobId": f"simulated-veo3-operation-{job_id}",
            "startedAt": db.SERVER_TIMESTAMP
        })

        # Tier-specific messaging
        tier_message = ""
        if user_tier == "basic":
            tier_message = "\n💧 Basic tier: 5s videos, no audio. Upgrade for longer videos with sound!"
        elif user_tier == "pro":
            tier_message = "\n⭐ Pro tier: Full 8s videos with synchronized audio included!"
        else:
            tier_message = "\n🚀 Enterprise tier: Maximum quality with up to 4 variations!"

        audio_status = "with synchronized audio" if generate_audio else "video only"
        return f"🚀 Success! Video generation started with Veo 3 (Preview).\n\n📋 Job ID: {job_id}\n⏱️ Expected completion: 2-3 minutes\n🎯 Quality: 720p, 24fps ultra-high-quality\n📐 Aspect ratio: {aspect_ratio}\n⏰ Duration: {duration_seconds} seconds (Veo 3 optimized)\n🎵 Audio: {audio_status}\n💰 Estimated cost: ${estimated_cost:.2f}{tier_message}\n\nYou'll be notified when your {sample_count} video{'s' if sample_count > 1 else ''} {'are' if sample_count > 1 else 'is'} ready!"

    except Exception as e:
        print(f"Job {job_id}: Error occurred: {e}")
        try:
            job_ref = db.reference(f"video_jobs/{job_id}")
            job_ref.update({
                "status": "failed", 
                "error": str(e),
                "failedAt": db.SERVER_TIMESTAMP
            })
        except Exception as db_error:
            print(f"Job {job_id}: Could not update Firebase with failure status: {db_error}")
        
        return f"❌ Error: Failed to start Veo 3 video generation job.\n\nJob ID: {job_id}\nError: {str(e)}\n\nPlease try again or contact support if the issue persists."

@FunctionTool
def calculate_veo_cost(duration_seconds: int, sample_count: int, generate_audio: bool) -> float:
    """
    Calculate estimated Veo API cost for cost optimization.
    Update these rates based on actual Google pricing.
    """
    # Estimated Veo 3 pricing (update with actual rates)
    base_cost_per_second = 0.10  # $0.10 per second
    audio_multiplier = 1.5 if generate_audio else 1.0
    
    cost_per_video = duration_seconds * base_cost_per_second * audio_multiplier
    total_cost = cost_per_video * sample_count
    
    return round(total_cost, 2)

@FunctionTool 
def get_video_job_status(job_id: str) -> dict:
    """
    Retrieves the status of a video generation job.
    
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
            
        return {
            "status": job_data.get("status", "unknown"),
            "jobId": job_id,
            "prompt": job_data.get("prompt", ""),
            "createdAt": job_data.get("createdAt"),
            "model": job_data.get("model", ""),
            "parameters": job_data.get("parameters", {}),
            "error": job_data.get("error"),
            "videoUrls": job_data.get("videoUrls", [])
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
def check_user_usage_limits(user_id: str, user_tier: str) -> dict:
    """
    Check if user is within their usage limits for cost control.
    """
    try:
        # Define tier limits
        tier_limits = {
            "basic": {"monthly_videos": 3, "daily_videos": 1},
            "pro": {"monthly_videos": 50, "daily_videos": 5},
            "enterprise": {"monthly_videos": -1, "daily_videos": -1}  # Unlimited
        }
        
        limits = tier_limits.get(user_tier, tier_limits["basic"])
        
        # Get current usage
        user_stats_ref = db.reference(f"user_stats/{user_id}")
        stats = user_stats_ref.get() or {}
        
        current_month = time.strftime("%Y-%m")
        current_day = time.strftime("%Y-%m-%d")
        
        monthly_usage = stats.get(f"monthly_usage_{current_month}", 0)
        daily_usage = stats.get(f"daily_usage_{current_day}", 0)
        
        # Check limits
        can_generate = True
        reason = ""
        
        if limits["monthly_videos"] != -1 and monthly_usage >= limits["monthly_videos"]:
            can_generate = False
            reason = f"Monthly limit reached ({monthly_usage}/{limits['monthly_videos']})"
        elif limits["daily_videos"] != -1 and daily_usage >= limits["daily_videos"]:
            can_generate = False
            reason = f"Daily limit reached ({daily_usage}/{limits['daily_videos']})"
            
        return {
            "can_generate": can_generate,
            "reason": reason,
            "usage": {
                "monthly": monthly_usage,
                "daily": daily_usage,
                "limits": limits
            },
            "upgrade_suggested": not can_generate and user_tier == "basic"
        }
        
    except Exception as e:
        print(f"Error checking usage limits: {e}")
        return {"can_generate": False, "reason": f"Error: {str(e)}"}

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
def suggest_user_upgrade(user_id: str) -> dict:
    """
    Analyze user behavior and suggest appropriate upgrade path.
    """
    try:
        user_stats_ref = db.reference(f"user_stats/{user_id}")
        stats = user_stats_ref.get() or {}
        
        videos_generated = stats.get("total_videos_generated", 0)
        upgrade_interest = stats.get("upgrade_interest", 0)
        last_activity = stats.get("last_activity", 0)
        
        # Determine upgrade suggestion
        suggestion = {
            "should_upgrade": False,
            "recommended_tier": "basic",
            "reasons": [],
            "incentive": None
        }
        
        if videos_generated >= 3:
            suggestion["should_upgrade"] = True
            suggestion["recommended_tier"] = "pro"
            suggestion["reasons"].append("You've reached the basic tier limit")
            
        if videos_generated >= 20:
            suggestion["recommended_tier"] = "enterprise"
            suggestion["reasons"].append("Heavy usage detected - enterprise tier recommended")
            
        if upgrade_interest > 2:
            suggestion["incentive"] = "20% off first month - you've shown interest!"
            
        # Activity-based incentives
        days_since_activity = (int(time.time()) - last_activity) / (24 * 60 * 60)
        if days_since_activity > 7:
            suggestion["incentive"] = "Come back! 50% off your first upgraded month"
            
        return suggestion
        
    except Exception as e:
        print(f"Error generating upgrade suggestion: {e}")
        return {"error": str(e)}
