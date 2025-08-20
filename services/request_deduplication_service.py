"""
Request Deduplication Service
Prevents duplicate API calls from creating multiple plans/analyses within short time windows
ENHANCED: Includes coordination logic to prevent race conditions
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class RequestDeduplicationService:
    """
    Service to prevent duplicate requests from creating multiple analyses/plans
    Uses in-memory tracking with configurable time windows
    ENHANCED: Includes coordination to wait for in-progress requests
    """
    
    def __init__(self):
        self.active_requests: Dict[str, datetime] = {}
        self.request_window_seconds = 60  # Block duplicates within 60 seconds
        
        # ENHANCED: Coordination for race condition prevention
        self.in_progress: Dict[str, asyncio.Event] = {}
        self.results_cache: Dict[str, Tuple[datetime, dict]] = {}  # (timestamp, result)
        self.request_cache_ttl = 600  # 10 minutes
        self.max_cache_entries = 100  # Memory management
        self.last_cleanup = datetime.now(timezone.utc)
        
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
    
    # ENHANCED: Coordination methods to prevent race conditions
    async def coordinate_request(self, user_id: str, archetype: str, 
                                request_type: str) -> Tuple[bool, Optional[dict]]:
        """
        Enhanced request coordination with wait-for-completion logic
        
        Returns:
            (should_process: bool, cached_result: Optional[dict])
        """
        key = self._generate_request_key(user_id, archetype, request_type)
        
        # Memory cleanup if needed
        await self._cleanup_if_needed()
        
        # Check if request already in progress
        if key in self.in_progress:
            print(f"⏳ [COORDINATION] Request in progress for {user_id[:8]}... + {archetype} - waiting...")
            try:
                # Wait for existing request with timeout
                await asyncio.wait_for(self.in_progress[key].wait(), timeout=30.0)
                print(f"✅ [COORDINATION] In-progress request completed for {user_id[:8]}... + {archetype}")
                # Return cached result
                if key in self.results_cache:
                    _, result = self.results_cache[key]
                    return False, result
            except asyncio.TimeoutError:
                print(f"⚠️ [COORDINATION] Request timeout for {user_id[:8]}... + {archetype} - proceeding")
                # Clean up stale in-progress marker
                self.in_progress.pop(key, None)
        
        # Check for recent cached results
        if key in self.results_cache:
            timestamp, result = self.results_cache[key]
            age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
            
            if age_seconds < self.request_cache_ttl:
                print(f"💾 [COORDINATION] Using cached result for {user_id[:8]}... + {archetype} ({age_seconds:.1f}s old)")
                return False, result
            else:
                # Remove stale cache entry
                del self.results_cache[key]
                print(f"🔄 [COORDINATION] Cache expired for {user_id[:8]}... + {archetype} - proceeding fresh")
        
        # New request - mark as in progress
        self.in_progress[key] = asyncio.Event()
        self.active_requests[key] = datetime.now(timezone.utc)
        print(f"🚀 [COORDINATION] Starting new request for {user_id[:8]}... + {archetype}")
        
        return True, None
    
    def complete_request(self, user_id: str, archetype: str, request_type: str, 
                        result: dict):
        """Mark request complete and cache result"""
        key = self._generate_request_key(user_id, archetype, request_type)
        
        # Cache the result with timestamp
        self.results_cache[key] = (datetime.now(timezone.utc), result)
        print(f"✅ [COORDINATION] Request completed and cached for {user_id[:8]}... + {archetype}")
        
        # Signal completion to waiting requests
        if key in self.in_progress:
            self.in_progress[key].set()
            del self.in_progress[key]
            print(f"🔔 [COORDINATION] Notified waiting requests for {user_id[:8]}... + {archetype}")
            
        # Also mark as complete for the original deduplication logic
        self.mark_request_complete(user_id, archetype, request_type)
    
    async def _cleanup_if_needed(self):
        """Perform memory cleanup based on usage and time"""
        now = datetime.now(timezone.utc)
        
        # Cleanup every 5 minutes or when memory threshold reached
        if ((now - self.last_cleanup).total_seconds() > 300 or 
            len(self.results_cache) > self.max_cache_entries):
            
            await self._perform_cleanup(now)
            self.last_cleanup = now
    
    async def _perform_cleanup(self, current_time: datetime):
        """Remove old entries to manage memory usage"""
        cutoff_time = current_time - timedelta(seconds=self.request_cache_ttl * 2)
        
        # Clean old active requests
        old_keys = [
            key for key, timestamp in self.active_requests.items()
            if timestamp < cutoff_time
        ]
        for key in old_keys:
            self.active_requests.pop(key, None)
        
        # Clean old cached results
        old_cache_keys = [
            key for key, (timestamp, _) in self.results_cache.items()
            if timestamp < cutoff_time
        ]
        for key in old_cache_keys:
            self.results_cache.pop(key, None)
        
        if old_keys or old_cache_keys:
            print(f"🧹 [COORDINATION] Cleaned up {len(old_keys)} active + {len(old_cache_keys)} cached entries")
        
        # If still over limit, remove oldest entries
        if len(self.results_cache) > self.max_cache_entries:
            sorted_cache = sorted(
                self.results_cache.items(), 
                key=lambda x: x[1][0]  # Sort by timestamp
            )
            
            to_remove = len(sorted_cache) - self.max_cache_entries + 10  # Remove extras
            for key, _ in sorted_cache[:to_remove]:
                self.results_cache.pop(key, None)
            
            print(f"🗑️ [COORDINATION] Removed {to_remove} oldest cache entries")
    
    def get_coordination_stats(self) -> Dict:
        """Get current coordination statistics"""
        return {
            'active_requests': len(self.active_requests),
            'in_progress': len(self.in_progress),
            'cached_results': len(self.results_cache),
            'last_cleanup': self.last_cleanup.isoformat()
        }

# Singleton instance for use across the application
request_deduplicator = RequestDeduplicationService()

# Alias for backward compatibility and consistency with naming
enhanced_deduplicator = request_deduplicator