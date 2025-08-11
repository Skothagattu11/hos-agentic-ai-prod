"""
MVP Sync Tracking Service - Phase 4.0 Step 1
Uses existing holistic_working_memory table for sync state tracking
Simple, reliable, leverages existing infrastructure
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter

logger = logging.getLogger(__name__)

class SyncTracker:
    """
    MVP Sync tracking using existing holistic_working_memory table
    Simple, effective, scalable foundation for incremental sync
    """
    
    def __init__(self):
        self.db_adapter = None
    
    async def _ensure_db_connection(self) -> SupabaseAsyncPGAdapter:
        """Reuse existing connection pattern"""
        if not self.db_adapter:
            try:
                self.db_adapter = SupabaseAsyncPGAdapter()
                await self.db_adapter.connect()
                logger.info("[SYNC_TRACKER] Connected to Supabase successfully")
            except Exception as e:
                logger.error(f"[SYNC_TRACKER_ERROR] Connection failed: {e}")
                raise
        return self.db_adapter
    
    async def get_last_sync_time(self, user_id: str) -> Optional[datetime]:
        """
        Get user's last sync timestamp from holistic_working_memory
        Returns None if no previous sync found
        """
        try:
            db = await self._ensure_db_connection()
            
            query = """
                SELECT content
                FROM holistic_working_memory 
                WHERE user_id = $1 
                  AND memory_type = 'data_sync_state'
                  AND is_active = true
                  AND expires_at > NOW()
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            rows = await db.fetch(query, user_id)
            
            if not rows:
                logger.info(f"[SYNC_TRACKER] No previous sync found for {user_id}")
                return None
            
            sync_data = rows[0]['content']
            last_sync_str = sync_data.get('last_sync_timestamp')
            
            if last_sync_str:
                last_sync = datetime.fromisoformat(last_sync_str.replace('Z', '+00:00'))
                logger.info(f"[SYNC_TRACKER] Last sync for {user_id}: {last_sync.isoformat()}")
                return last_sync
            
            return None
            
        except Exception as e:
            logger.error(f"[SYNC_TRACKER_ERROR] Failed to get last sync for {user_id}: {e}")
            return None
    
    async def update_sync_time(self, user_id: str, sync_time: datetime = None) -> bool:
        """
        Update user's sync timestamp in holistic_working_memory
        Creates new record or updates existing one
        """
        try:
            db = await self._ensure_db_connection()
            sync_time = sync_time or datetime.now(timezone.utc)
            
            # Create session ID for sync tracking
            session_id = f"sync_{sync_time.strftime('%Y%m%d_%H%M%S')}"
            
            # Prepare sync state data
            sync_content = {
                'last_sync_timestamp': sync_time.isoformat(),
                'sync_strategy': 'full_sync',  # Will be enhanced in Phase 2
                'records_processed': {
                    'scores': 0,  # Will be populated by calling service
                    'biomarkers': 0
                }
            }
            
            # First, deactivate any existing sync records for this user
            deactivate_query = """
                UPDATE holistic_working_memory 
                SET is_active = false
                WHERE user_id = $1 AND memory_type = 'data_sync_state'
            """
            await db.execute(deactivate_query, user_id)
            
            # Insert new sync record
            insert_query = """
                INSERT INTO holistic_working_memory (
                    user_id, session_id, agent_id, memory_type, content, 
                    priority, created_at, expires_at, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            
            await db.execute(
                insert_query,
                user_id,
                session_id, 
                'user_data_service',  # agent_id
                'data_sync_state',    # memory_type
                sync_content,         # content (JSONB)
                5,                    # priority
                sync_time,           # created_at
                sync_time + timedelta(days=30),  # expires_at (30 days)
                True                 # is_active
            )
            
            logger.info(f"[SYNC_TRACKER] Updated sync time for {user_id}: {sync_time.isoformat()}")
            return True
            
        except Exception as e:
            logger.error(f"[SYNC_TRACKER_ERROR] Failed to update sync time for {user_id}: {e}")
            return False
    
    async def get_sync_strategy(self, user_id: str) -> str:
        """
        Determine sync strategy based on last sync time
        MVP implementation - will be enhanced in Phase 2
        """
        last_sync = await self.get_last_sync_time(user_id)
        
        if not last_sync:
            return "initial_full"  # New user
        
        hours_since_sync = (datetime.now(timezone.utc) - last_sync).total_seconds() / 3600
        
        if hours_since_sync <= 6:
            return "incremental_only"  # Recent sync
        elif hours_since_sync <= 48:
            return "incremental_plus_context"  # Regular sync
        else:
            return "refresh_full"  # Stale sync
    
    async def update_sync_stats(self, user_id: str, scores_count: int, biomarkers_count: int):
        """
        Update sync statistics in the latest sync record
        MVP helper method
        """
        try:
            db = await self._ensure_db_connection()
            
            # Get the latest sync record
            query = """
                UPDATE holistic_working_memory 
                SET content = jsonb_set(
                    jsonb_set(content, '{records_processed,scores}', $3::text::jsonb),
                    '{records_processed,biomarkers}', $4::text::jsonb
                )
                WHERE user_id = $1 
                  AND memory_type = 'data_sync_state'
                  AND is_active = true
                  AND expires_at > NOW()
            """
            
            await db.execute(query, user_id, user_id, scores_count, biomarkers_count)
            logger.info(f"[SYNC_TRACKER] Updated stats for {user_id}: {scores_count} scores, {biomarkers_count} biomarkers")
            
        except Exception as e:
            logger.error(f"[SYNC_TRACKER_ERROR] Failed to update stats for {user_id}: {e}")