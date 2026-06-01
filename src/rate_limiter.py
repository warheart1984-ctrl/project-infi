"""Rate limiting and usage tracking"""

from datetime import datetime, timedelta
from src.logger import get_logger
import os

logger = get_logger(__name__)

class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self, requests_per_minute=60):
        """Initialize rate limiter"""
        self.requests_per_minute = requests_per_minute
        self.user_requests = {}
    
    def is_allowed(self, user_id: str, endpoint: str = None) -> bool:
        """Check if request is allowed"""
        try:
            now = datetime.utcnow()
            minute_ago = now - timedelta(minutes=1)
            
            if user_id not in self.user_requests:
                self.user_requests[user_id] = []
            
            self.user_requests[user_id] = [
                (ts, ep) for ts, ep in self.user_requests[user_id]
                if ts > minute_ago
            ]
            
            if len(self.user_requests[user_id]) >= self.requests_per_minute:
                logger.warning(f"Rate limit exceeded for {user_id}")
                return False
            
            self.user_requests[user_id].append((now, endpoint))
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            return True
    
    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests"""
        if user_id not in self.user_requests:
            return self.requests_per_minute
        
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        recent = [
            (ts, ep) for ts, ep in self.user_requests[user_id]
            if ts > minute_ago
        ]
        return max(0, self.requests_per_minute - len(recent))

rate_limiter = RateLimiter(requests_per_minute=int(os.getenv("RATE_LIMIT", "60")))
