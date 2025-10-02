"""
Archetype Analysis Tracker - MVP Implementation
Manages archetype-specific analysis timestamps for optimal data windows
"""

from typing import Optional, Dict
from datetime import datetime, timezone
import logging
import os
from supabase import create_client

logger = logging.getLogger(__name__)

class ArchetypeAnalysisTracker:
    """
    MVP Service for managing archetype-specific analysis timestamps
    Enables each archetype to maintain independent analysis windows
    
    Uses direct Supabase client to avoid adapter issues
    """
    
    def __init__(self):
        self.supabase_client = None
        
    def _get_supabase_client(self):
        """Get direct Supabase client"""
        if not self.supabase_client:
            try:
                # Get credentials from environment  
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY', '')
                
                if not supabase_url or not supabase_key:
                    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
                
                self.supabase_client = create_client(supabase_url, supabase_key)
                logger.debug("[ARCHETYPE_TRACKER] Connected to Supabase via direct client")
                
            except Exception as e:
                logger.error(f"[ARCHETYPE_TRACKER] Supabase connection failed: {e}")
                raise
                
        return self.supabase_client
        
    async def get_last_analysis_date(self, user_id: str, archetype: str, analysis_type: str = "behavior_analysis") -> Optional[datetime]:
        """
        Get the last analysis date for specific user + archetype + analysis_type combination

        Args:
            user_id: User identifier
            archetype: Archetype name (e.g., "Peak Performer")
            analysis_type: Type of analysis ("behavior_analysis" or "circadian_analysis")

        Returns:
            datetime: Last analysis date or None if never analyzed for this combination
        """
        try:
            supabase = self._get_supabase_client()

            # Direct Supabase query with analysis_type
            result = supabase.table('archetype_analysis_tracking') \
                .select('last_analysis_at') \
                .eq('user_id', user_id) \
                .eq('archetype', archetype) \
                .eq('analysis_type', analysis_type) \
                .execute()

            if result.data and len(result.data) > 0:
                timestamp_str = result.data[0]['last_analysis_at']
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                logger.debug(f"[ARCHETYPE_TRACKER] Found last {analysis_type} for {user_id} + {archetype}: {timestamp}")
                return timestamp
            else:
                logger.debug(f"[ARCHETYPE_TRACKER] No previous {analysis_type} found for {user_id} + {archetype}")
                return None

        except Exception as e:
            logger.error(f"[ARCHETYPE_TRACKER] Error getting last analysis date: {e}")
            return None
        
    async def update_last_analysis_date(self, user_id: str, archetype: str,
                                      analysis_date: datetime = None, analysis_type: str = "behavior_analysis") -> bool:
        """
        Update last analysis date for specific archetype + analysis_type (UPSERT - SIMPLIFIED VERSION)

        Args:
            user_id: User identifier
            archetype: Archetype name
            analysis_date: Analysis timestamp (defaults to now)
            analysis_type: Type of analysis ("behavior_analysis" or "circadian_analysis")

        Returns:
            bool: Success status
        """
        if analysis_date is None:
            analysis_date = datetime.now(timezone.utc)

        try:
            supabase = self._get_supabase_client()

            # Use direct Supabase UPSERT
            # This uses Supabase's native upsert which is more reliable than adapter UPSERT

            # Prepare data for upsert
            data = {
                'user_id': user_id,
                'archetype': archetype,
                'analysis_type': analysis_type,  # NEW: Track analysis type
                'last_analysis_at': analysis_date.isoformat(),
                'analysis_count': 1,  # Will be overridden if updating
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            # First try to get existing record to increment count
            existing = supabase.table('archetype_analysis_tracking') \
                .select('analysis_count') \
                .eq('user_id', user_id) \
                .eq('archetype', archetype) \
                .eq('analysis_type', analysis_type) \
                .execute()

            if existing.data and len(existing.data) > 0:
                # Update existing record
                data['analysis_count'] = existing.data[0]['analysis_count'] + 1

                result = supabase.table('archetype_analysis_tracking') \
                    .update(data) \
                    .eq('user_id', user_id) \
                    .eq('archetype', archetype) \
                    .eq('analysis_type', analysis_type) \
                    .execute()

                if result.data:
                    logger.info(f"[ARCHETYPE_TRACKER] Updated existing tracking for {user_id} + {archetype} + {analysis_type} (#{data['analysis_count']})")
                    return True
            else:
                # Insert new record
                data['created_at'] = datetime.now(timezone.utc).isoformat()

                result = supabase.table('archetype_analysis_tracking') \
                    .insert(data) \
                    .execute()

                if result.data:
                    logger.info(f"[ARCHETYPE_TRACKER] Created new tracking for {user_id} + {archetype} + {analysis_type}")
                    return True

            logger.error(f"[ARCHETYPE_TRACKER] Failed to update {user_id} + {archetype} + {analysis_type} - no data returned")
            return False

        except Exception as e:
            logger.error(f"[ARCHETYPE_TRACKER] Error updating last analysis date: {e}")
            return False
        
    async def get_archetype_history(self, user_id: str) -> Dict[str, datetime]:
        """
        Get analysis dates for all archetypes for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict mapping archetype names to last analysis dates
        """
        try:
            db = await self._ensure_db_connection()
            
            query = """
                SELECT archetype, last_analysis_at, analysis_count
                FROM archetype_analysis_tracking 
                WHERE user_id = $1
                ORDER BY last_analysis_at DESC
            """
            
            rows = await db.fetch(query, user_id)
            
            history = {}
            for row in rows:
                history[row['archetype']] = row['last_analysis_at']
            
            logger.debug(f"[ARCHETYPE_TRACKER] Retrieved history for {user_id}: {len(history)} archetypes")
            return history
            
        except Exception as e:
            logger.error(f"[ARCHETYPE_TRACKER] Error getting archetype history: {e}")
            return {}
    
    async def get_last_analysis_date_with_fallback(self, user_id: str, archetype: str, analysis_type: str = "behavior_analysis") -> tuple[Optional[datetime], str]:
        """
        Get archetype-specific timestamp with fallback to global timestamp
        Ensures system continues working even if archetype tracking fails

        Args:
            user_id: User identifier
            archetype: Archetype name
            analysis_type: Type of analysis ("behavior_analysis" or "circadian_analysis")

        Returns:
            (timestamp, source) where source is: 'archetype_specific', 'global_fallback', 'emergency_fallback'
        """
        try:
            # First try archetype-specific + analysis-type-specific timestamp
            archetype_timestamp = await self.get_last_analysis_date(user_id, archetype, analysis_type)
            if archetype_timestamp:
                return archetype_timestamp, "archetype_specific"

            # Fallback to global profiles.last_analysis_at using direct Supabase client
            supabase = self._get_supabase_client()
            result = supabase.table('profiles') \
                .select('last_analysis_at') \
                .eq('id', user_id) \
                .execute()

            if result.data and len(result.data) > 0 and result.data[0].get('last_analysis_at'):
                timestamp_str = result.data[0]['last_analysis_at']
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                logger.warning(f"[ARCHETYPE_TRACKER] Using global fallback for {user_id} + {analysis_type}")
                return timestamp, "global_fallback"

            # Emergency fallback - return None to trigger 7-day window
            logger.warning(f"[ARCHETYPE_TRACKER] No timestamps found - using emergency fallback for {analysis_type}")
            return None, "emergency_fallback"

        except Exception as e:
            logger.error(f"[ARCHETYPE_TRACKER] Fallback failed for {user_id} + {analysis_type}: {e}")
            # Emergency fallback to 7-day window
            return None, "emergency_fallback"

    async def cleanup(self):
        """Clean up resources - no cleanup needed for direct Supabase client"""
        logger.debug("[ARCHETYPE_TRACKER] Cleanup completed (direct Supabase client)")

# Singleton pattern for MVP
_tracker_instance = None

async def get_archetype_tracker() -> ArchetypeAnalysisTracker:
    """Get or create the singleton archetype tracker"""
    global _tracker_instance
    
    if _tracker_instance is None:
        _tracker_instance = ArchetypeAnalysisTracker()
    
    return _tracker_instance