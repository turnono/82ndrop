# drop_agent/staging_access.py

import os
from typing import Dict, Any, List

# List of authorized users for staging environment
AUTHORIZED_USERS = [
    "test_user",  # Test user always allowed
    "taajirah-agents@taajirah.iam.gserviceaccount.com",  # Service account
    "admin@82ndrop.com"  # Admin user
]

class StagingAccessControl:
    """Controls access to staging environment features."""
    
    def __init__(self):
        """Initialize staging access control."""
        self.environment = os.getenv("ENV", "production").lower()
        self.is_active = self.environment == "staging"
        self.authorized_users = AUTHORIZED_USERS
        
        if self.is_active:
            print("🔒 Staging Access Control: ACTIVE")
            print(f"   Authorized users: {len(self.authorized_users)}")
            print("✅ Staging access control loaded")
    
    def enforce_staging_access(self, user_id: str) -> None:
        """Enforce staging access control for a user."""
        if not self.is_active:
            return  # No enforcement in production
            
        if user_id not in self.authorized_users:
            raise Exception(
                "Access denied: This feature is only available to authorized users in staging. "
                "Please contact support if you need access."
            )
    
    def get_staging_info(self) -> Dict[str, Any]:
        """Get information about the staging environment."""
        return {
            "is_active": self.is_active,
            "environment": self.environment,
            "authorized_users": len(self.authorized_users),
            "features": {
                "video_generation": True,
                "audio_generation": True,
                "quota_monitoring": True
            }
        }
    
    def get_authorized_users(self) -> List[str]:
        """Get list of authorized users."""
        return self.authorized_users

# Create singleton instance
staging_access = StagingAccessControl() 