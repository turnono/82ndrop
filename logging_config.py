"""
Logging and Analytics Configuration for 82ndrop API
Tracks user behavior, API usage, and system performance
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import os

# Create logs directory
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

@dataclass
class UserAnalytics:
    """Data class for user analytics tracking"""
    user_id: str
    email: Optional[str]
    access_level: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    message_length: Optional[int] = None
    agent_response_length: Optional[int] = None
    session_id: Optional[str] = None
    timestamp: str = None
    error_message: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class APILogger:
    """Centralized logging system for API usage and analytics"""
    
    def __init__(self):
        # Configure main API logger
        self.api_logger = logging.getLogger("api_usage")
        self.api_logger.setLevel(logging.INFO)
        
        # Configure analytics logger
        self.analytics_logger = logging.getLogger("user_analytics")
        self.analytics_logger.setLevel(logging.INFO)
        
        # Configure error logger
        self.error_logger = logging.getLogger("api_errors")
        self.error_logger.setLevel(logging.ERROR)
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up file handlers for different log types"""
        
        # API Usage Handler (all API calls)
        api_handler = logging.FileHandler(logs_dir / "api_usage.log")
        api_handler.setLevel(logging.INFO)
        api_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        api_handler.setFormatter(api_formatter)
        self.api_logger.addHandler(api_handler)
        
        # Analytics Handler (structured JSON for analysis)
        analytics_handler = logging.FileHandler(logs_dir / "user_analytics.jsonl")
        analytics_handler.setLevel(logging.INFO)
        analytics_formatter = logging.Formatter('%(message)s')
        analytics_handler.setFormatter(analytics_formatter)
        self.analytics_logger.addHandler(analytics_handler)
        
        # Error Handler (errors and exceptions)
        error_handler = logging.FileHandler(logs_dir / "api_errors.log")
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
        )
        error_handler.setFormatter(error_formatter)
        self.error_logger.addHandler(error_handler)
        
        # Console handler for development
        if os.getenv("ENV", "development") == "development":
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.api_logger.addHandler(console_handler)
    
    def log_api_request(self, user_analytics: UserAnalytics):
        """Log API request with user analytics"""
        
        # Log structured analytics data (JSON)
        analytics_data = asdict(user_analytics)
        self.analytics_logger.info(json.dumps(analytics_data))
        
        # Log human-readable API usage
        self.api_logger.info(
            f"User {user_analytics.user_id} ({user_analytics.access_level}) "
            f"{user_analytics.method} {user_analytics.endpoint} - "
            f"Status: {user_analytics.status_code} - "
            f"Time: {user_analytics.response_time_ms:.2f}ms"
        )
    
    def log_chat_interaction(self, user_analytics: UserAnalytics, message: str, response: str):
        """Log chat interactions with the agent"""
        
        user_analytics.message_length = len(message)
        user_analytics.agent_response_length = len(response)
        
        # Log the interaction
        self.log_api_request(user_analytics)
        
        # Additional chat-specific logging
        self.api_logger.info(
            f"Chat - User {user_analytics.user_id}: "
            f"Message ({len(message)} chars) -> "
            f"Response ({len(response)} chars)"
        )
    
    def log_error(self, error: Exception, user_id: Optional[str] = None, context: Dict[str, Any] = None):
        """Log errors with context"""
        
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        self.error_logger.error(
            f"Error: {error_data['error_type']} - {error_data['error_message']} - "
            f"User: {user_id} - Context: {context}"
        )
        
        # Also log as JSON for analysis
        self.analytics_logger.info(json.dumps({"type": "error", **error_data}))
    
    def log_authentication(self, user_id: str, email: str, success: bool, reason: str = ""):
        """Log authentication attempts"""
        
        auth_data = {
            "type": "authentication",
            "user_id": user_id,
            "email": email,
            "success": success,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        self.analytics_logger.info(json.dumps(auth_data))
        
        if success:
            self.api_logger.info(f"Authentication successful - User: {user_id} ({email})")
        else:
            self.api_logger.warning(f"Authentication failed - User: {user_id} ({email}) - Reason: {reason}")

class AnalyticsTracker:
    """Track and aggregate user analytics"""
    
    def __init__(self):
        self.daily_stats = {}
        self.user_stats = {}
    
    def track_usage(self, user_analytics: UserAnalytics):
        """Track usage statistics"""
        
        today = datetime.now().strftime("%Y-%m-%d")
        user_id = user_analytics.user_id
        
        # Daily stats
        if today not in self.daily_stats:
            self.daily_stats[today] = {
                "total_requests": 0,
                "unique_users": set(),
                "total_response_time": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "chat_messages": 0,
                "access_levels": {}
            }
        
        daily = self.daily_stats[today]
        daily["total_requests"] += 1
        daily["unique_users"].add(user_id)
        daily["total_response_time"] += user_analytics.response_time_ms
        
        if user_analytics.status_code < 400:
            daily["successful_requests"] += 1
        else:
            daily["failed_requests"] += 1
        
        if user_analytics.endpoint == "/chat":
            daily["chat_messages"] += 1
        
        # Track access levels
        level = user_analytics.access_level
        daily["access_levels"][level] = daily["access_levels"].get(level, 0) + 1
        
        # User-specific stats
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                "total_requests": 0,
                "total_chat_messages": 0,
                "total_response_time": 0,
                "first_seen": user_analytics.timestamp,
                "last_seen": user_analytics.timestamp,
                "access_level": user_analytics.access_level,
                "email": user_analytics.email,
                "successful_requests": 0,
                "failed_requests": 0
            }
        
        user = self.user_stats[user_id]
        user["total_requests"] += 1
        user["total_response_time"] += user_analytics.response_time_ms
        user["last_seen"] = user_analytics.timestamp
        user["access_level"] = user_analytics.access_level  # Update in case it changed
        
        if user_analytics.status_code < 400:
            user["successful_requests"] += 1
        else:
            user["failed_requests"] += 1
        
        if user_analytics.endpoint == "/chat":
            user["total_chat_messages"] += 1
    
    def get_daily_summary(self, date: str = None) -> Dict[str, Any]:
        """Get daily usage summary"""
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if date not in self.daily_stats:
            # Return default stats for days with no data
            return {
                "total_requests": 0,
                "unique_users": 0,
                "avg_response_time": None,
                "successful_requests": 0,
                "failed_requests": 0,
                "chat_messages": 0,
                "access_levels": {}
            }
        
        stats = self.daily_stats[date].copy()
        stats["unique_users"] = len(stats["unique_users"])
        stats["avg_response_time"] = stats["total_response_time"] / stats["total_requests"] if stats["total_requests"] > 0 else None
        
        return stats
    
    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user-specific analytics"""
        
        if user_id not in self.user_stats:
            # Return default stats for new users
            return {
                "total_requests": 0,
                "total_chat_messages": 0,
                "avg_response_time": None,
                "success_rate": None,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "access_level": "basic",
                "email": None,
                "successful_requests": 0,
                "failed_requests": 0
            }
        
        stats = self.user_stats[user_id].copy()
        stats["avg_response_time"] = stats["total_response_time"] / stats["total_requests"] if stats["total_requests"] > 0 else None
        stats["success_rate"] = stats["successful_requests"] / stats["total_requests"] if stats["total_requests"] > 0 else None
        
        return stats
    
    def export_analytics(self, output_file: str = None):
        """Export analytics to JSON file"""
        
        if output_file is None:
            output_file = f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert sets to lists for JSON serialization
        export_data = {
            "daily_stats": {},
            "user_stats": self.user_stats,
            "export_timestamp": datetime.now().isoformat()
        }
        
        for date, stats in self.daily_stats.items():
            export_stats = stats.copy()
            export_stats["unique_users"] = list(export_stats["unique_users"])
            export_data["daily_stats"][date] = export_stats
        
        with open(logs_dir / output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return output_file

# Global instances
api_logger = APILogger()
analytics_tracker = AnalyticsTracker()