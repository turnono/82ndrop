#!/usr/bin/env python3
"""
Staging Access Control for 82ndrop
Prevents unauthorized video generation in staging environment
"""

import os
from typing import List, Optional
from fastapi import HTTPException

class StagingAccessControl:
    """Controls who can generate videos in staging environment"""
    
    def __init__(self):
        # Only these users can generate videos in staging
        self.authorized_users = [
            "turnono@gmail.com",  # Only authorized user for staging
            # All other users will be blocked from video generation
        ]
        
        # Environment check
        self.is_staging = os.getenv("ENVIRONMENT") == "staging"
        
        if self.is_staging:
            print("🔒 Staging Access Control: ACTIVE")
            print(f"   Authorized users: {len(self.authorized_users)}")
        
    def is_authorized_for_video_generation(self, user_id: str, user_email: str = None) -> bool:
        """Check if user can generate videos in staging"""
        
        # In production, everyone with valid auth can generate videos
        if not self.is_staging:
            return True
            
        # In staging, only authorized users
        authorized = (
            user_id in self.authorized_users or 
            user_email in self.authorized_users if user_email else False
        )
        
        if not authorized:
            print(f"🚫 Staging Access Denied: user_id={user_id}, email={user_email}")
        else:
            print(f"✅ Staging Access Granted: user_id={user_id}")
            
        return authorized
    
    def enforce_staging_access(self, user_id: str, user_email: str = None, operation: str = "video generation"):
        """Raise HTTPException if user not authorized in staging"""
        
        if not self.is_authorized_for_video_generation(user_id, user_email):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Staging Environment Access Restricted",
                    "message": f"This staging environment is restricted to authorized users only. {operation} is not available.",
                    "environment": "staging",
                    "user_id": user_id,
                    "authorized": False,
                    "contact": "Contact admin for staging access"
                }
            )
    
    def get_staging_info(self) -> dict:
        """Return staging environment info"""
        return {
            "environment": "staging" if self.is_staging else "production",
            "access_control": "enabled" if self.is_staging else "disabled",
            "video_generation_restricted": self.is_staging,
            "authorized_user_count": len(self.authorized_users) if self.is_staging else "unlimited",
            "cost_protection": "Videos cost real money - staging locked down",
            "estimated_cost_per_video": "$4-6 each (paid to Google Cloud)"
        }

# Global instance
staging_access = StagingAccessControl()

# Decorator for protecting video generation endpoints
def require_staging_authorization(func):
    """Decorator to protect video generation in staging"""
    def wrapper(*args, **kwargs):
        # Extract user info from function arguments
        user_id = kwargs.get('user_id') or (args[1] if len(args) > 1 else None)
        
        if staging_access.is_staging:
            staging_access.enforce_staging_access(user_id, operation="Video generation")
        
        return func(*args, **kwargs)
    
    return wrapper 