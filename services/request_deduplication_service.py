"""
Request Deduplication Service
Prevents duplicate API calls from creating multiple plans/analyses within short time windows
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class RequestDeduplicationService:
    """
    Service to prevent duplicate requests from creating multiple analyses/plans
    Uses in-memory tracking with configurable time windows
    In production: consider using Redis for distributed deduplication
    """
    
    def __init__(self):
        self.active_requests: Dict[str, datetime] = {}
        self.request_window_seconds = 60  # Block duplicates within 60 seconds
        
    def is_duplicate_request(self, user_id: str, archetype: str, request_type: str) -> bool:
        """
        Check if this request is a duplicate within the time window
        
        Args:
            user_id: User identifier
            archetype: Archetype being used
            request_type: Type of request ('routine', 'nutrition', 'behavior')
            
        Returns:
            bool: True if this is a duplicate request that should be blocked
        """
        key = self._generate_request_key(user_id, archetype, request_type)
        now = datetime.now(timezone.utc)
        
        # Check if we have a recent request for this combination
        if key in self.active_requests:
            last_request_time = self.active_requests[key]
            time_diff = (now - last_request_time).total_seconds()
            
            if time_diff < self.request_window_seconds:
                logger.warning(
                    f"[DEDUP] Blocking duplicate {request_type} request for {user_id[:8]}... "
                    f"(last request {time_diff:.1f}s ago)"
                )
                return True
        
        # Record this request
        self.active_requests[key] = now
        logger.debug(f"[DEDUP] Allowing {request_type} request for {user_id[:8]}...")
        
        # Cleanup old entries (keep memory usage reasonable)
        self._cleanup_old_entries(now)
        
        return False
    
    def mark_request_complete(self, user_id: str, archetype: str, request_type: str):
        """
        Mark request as complete and remove from tracking
        Call this when request processing is finished (success or failure)
        """
        key = self._generate_request_key(user_id, archetype, request_type)
        if key in self.active_requests:
            del self.active_requests[key]
            logger.debug(f"[DEDUP] Marked {request_type} complete for {user_id[:8]}...")
    
    def get_active_requests_count(self) -> int:
        """Get number of currently tracked requests (for monitoring)"""
        return len(self.active_requests)
    
    def _generate_request_key(self, user_id: str, archetype: str, request_type: str) -> str:
        """Generate unique key for request combination"""
        return f"{user_id}_{archetype}_{request_type}"
    
    def _cleanup_old_entries(self, current_time: datetime):
        """Remove entries older than request window to prevent memory bloat"""
        cutoff_time = current_time.timestamp() - (self.request_window_seconds * 2)  # 2x window for safety
        
        old_keys = [
            key for key, timestamp in self.active_requests.items()
            if timestamp.timestamp() < cutoff_time
        ]
        
        for key in old_keys:
            del self.active_requests[key]
        
        if old_keys:
            logger.debug(f"[DEDUP] Cleaned up {len(old_keys)} old request entries")

# Singleton instance for use across the application
request_deduplicator = RequestDeduplicationService()