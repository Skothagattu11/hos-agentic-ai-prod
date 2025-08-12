"""
Simplified Analysis Tracking Service - Single Field Approach
Replaces complex sync_tracker with simple last_analysis_at timestamp
True incremental: fetches ALL data from last analysis to now
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter

logger = logging.getLogger(__name__)

class AnalysisTracker:
    """
    Simple analysis tracking using profiles.last_analysis_at field
    No complex memory tables, just one timestamp per user
    """
    
    def __init__(self):
        self.db_adapter = None
    
    async def _ensure_db_connection(self) -> SupabaseAsyncPGAdapter:
        """Reuse existing connection pattern"""
        if not self.db_adapter:
            try:
                self.db_adapter = SupabaseAsyncPGAdapter()
                await self.db_adapter.connect()
                logger.info("[ANALYSIS_TRACKER] Connected to Supabase successfully")
            except Exception as e:
                logger.error(f"[ANALYSIS_TRACKER_ERROR] Connection failed: {e}")
                raise
        return self.db_adapter
    
    async def get_last_analysis_time(self, user_id: str) -> Optional[datetime]:
        """
        Get user's last analysis timestamp from profiles table
        Returns None if never analyzed before
        """
        try:
            db = await self._ensure_db_connection()
            
            # Simple, direct query - no complex JSON or conditions
            query = """
                SELECT last_analysis_at
                FROM profiles 
                WHERE id = $1
            """
            
            rows = await db.fetch(query, user_id)
            
            if not rows or not rows[0]['last_analysis_at']:
                logger.info(f"[ANALYSIS_TRACKER] No previous analysis found for {user_id}")
                return None
            
            last_analysis = rows[0]['last_analysis_at']
            logger.info(f"[ANALYSIS_TRACKER] Last analysis for {user_id}: {last_analysis.isoformat()}")
            
            # Calculate time since last analysis for logging
            hours_since = (datetime.now(timezone.utc) - last_analysis).total_seconds() / 3600
            logger.info(f"[ANALYSIS_TRACKER] Time since last analysis: {hours_since:.1f} hours")
            
            return last_analysis
            
        except Exception as e:
            logger.error(f"[ANALYSIS_TRACKER_ERROR] Failed to get last analysis for {user_id}: {e}")
            return None
    
    async def update_analysis_time(self, user_id: str, latest_data_timestamp: datetime = None) -> bool:
        """
        Update user's last analysis timestamp based on LATEST DATA found, not analysis execution time
        This ensures incremental sync works correctly even when no new data exists
        """
        try:
            db = await self._ensure_db_connection()
            
            # Use the timestamp of the latest data found, not current time
            if not latest_data_timestamp:
                # If no data provided, use current time as fallback
                latest_data_timestamp = datetime.now(timezone.utc)
                logger.warning(f"[ANALYSIS_TRACKER] No data timestamp provided for {user_id}, falling back to current time")
            
            # Update with latest data timestamp
            query = """
                UPDATE profiles 
                SET last_analysis_at = $2,
                    updated_at = NOW()
                WHERE id = $1
            """
            
            await db.execute(query, user_id, latest_data_timestamp)
            
            execution_time = datetime.now(timezone.utc)
            hours_difference = (execution_time - latest_data_timestamp).total_seconds() / 3600
            
            logger.info(f"[ANALYSIS_TRACKER] Updated analysis tracking for {user_id}")
            logger.info(f"[ANALYSIS_TRACKER] ✓ Analysis executed at: {execution_time.isoformat()}")
            logger.info(f"[ANALYSIS_TRACKER] ✓ Latest data found at: {latest_data_timestamp.isoformat()}")
            logger.info(f"[ANALYSIS_TRACKER] ✓ Data age: {hours_difference:.1f} hours old")
            logger.info(f"[ANALYSIS_TRACKER] → Next incremental sync will fetch data after: {latest_data_timestamp.isoformat()}")
            return True
            
        except Exception as e:
            logger.error(f"[ANALYSIS_TRACKER_ERROR] Failed to update analysis time for {user_id}: {e}")
            return False
    
    async def update_analysis_metadata(self, user_id: str, metadata: dict) -> bool:
        """
        Optional: Update analysis metadata (analysis count, data volume, etc)
        Uses JSONB column for flexibility
        """
        try:
            db = await self._ensure_db_connection()
            
            # Update metadata while preserving existing data
            query = """
                UPDATE profiles 
                SET analysis_metadata = analysis_metadata || $2,
                    updated_at = NOW()
                WHERE id = $1
            """
            
            await db.execute(query, user_id, metadata)
            
            logger.info(f"[ANALYSIS_TRACKER] Updated metadata for {user_id}: {metadata}")
            return True
            
        except Exception as e:
            logger.error(f"[ANALYSIS_TRACKER_ERROR] Failed to update metadata for {user_id}: {e}")
            return False
    
    async def get_analysis_stats(self, user_id: str) -> dict:
        """
        Get analysis statistics for a user
        Returns time since last analysis and metadata
        """
        try:
            db = await self._ensure_db_connection()
            
            query = """
                SELECT last_analysis_at, analysis_metadata
                FROM profiles 
                WHERE id = $1
            """
            
            rows = await db.fetch(query, user_id)
            
            if not rows:
                return {
                    'user_id': user_id,
                    'last_analysis_at': None,
                    'hours_since_analysis': None,
                    'analysis_count': 0
                }
            
            last_analysis = rows[0]['last_analysis_at']
            metadata = rows[0]['analysis_metadata'] or {}
            
            hours_since = None
            if last_analysis:
                hours_since = (datetime.now(timezone.utc) - last_analysis).total_seconds() / 3600
            
            return {
                'user_id': user_id,
                'last_analysis_at': last_analysis.isoformat() if last_analysis else None,
                'hours_since_analysis': round(hours_since, 1) if hours_since else None,
                'analysis_count': metadata.get('analysis_count', 0),
                'last_data_volume': metadata.get('last_data_volume', {})
            }
            
        except Exception as e:
            logger.error(f"[ANALYSIS_TRACKER_ERROR] Failed to get stats for {user_id}: {e}")
            return {}
    
    async def increment_analysis_count(self, user_id: str, scores_count: int, biomarkers_count: int) -> bool:
        """
        Track analysis count and data volume for monitoring
        """
        try:
            metadata = {
                'analysis_count': 1,  # Will be incremented in SQL
                'last_data_volume': {
                    'scores': scores_count,
                    'biomarkers': biomarkers_count,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            db = await self._ensure_db_connection()
            
            # Increment counter and update volume
            query = """
                UPDATE profiles 
                SET analysis_metadata = 
                    CASE 
                        WHEN analysis_metadata IS NULL THEN $2::jsonb
                        ELSE jsonb_set(
                            analysis_metadata,
                            '{analysis_count}',
                            to_jsonb(COALESCE((analysis_metadata->>'analysis_count')::int, 0) + 1)
                        ) || jsonb_build_object('last_data_volume', $2::jsonb->'last_data_volume')
                    END,
                    updated_at = NOW()
                WHERE id = $1
            """
            
            await db.execute(query, user_id, metadata)
            
            logger.info(f"[ANALYSIS_TRACKER] Incremented analysis count for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"[ANALYSIS_TRACKER_ERROR] Failed to increment count for {user_id}: {e}")
            return False
    
    async def cleanup(self):
        """Clean shutdown"""
        if self.db_adapter:
            await self.db_adapter.close()
            logger.info("[ANALYSIS_TRACKER] Database connection closed")