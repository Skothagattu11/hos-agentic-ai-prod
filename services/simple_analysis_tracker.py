"""
Simple Analysis Tracker - Direct Supabase Client Approach
Bypasses SQL adapter issues by using direct Supabase REST calls
"""
import logging
from datetime import datetime, timezone
from typing import Optional
import os

logger = logging.getLogger(__name__)

class SimpleAnalysisTracker:
    """
    Simple analysis tracking using direct Supabase client
    Avoids SQL parsing issues with complex adapter
    """
    
    def __init__(self):
        self.supabase_client = None
    
    def _get_supabase_client(self):
        """Get direct Supabase client"""
        if not self.supabase_client:
            try:
                from supabase import create_client
                
                # Get credentials from environment
                supabase_url = os.getenv('SUPABASE_URL') or os.getenv('DATABASE_URL', '').replace('postgresql://', 'https://').split('@')[1].split('/')[0] + '.supabase.co'
                supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY', '')
                
                if not supabase_url or not supabase_key:
                    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
                
                self.supabase_client = create_client(supabase_url, supabase_key)
                logger.info("[SIMPLE_TRACKER] Connected to Supabase directly")
                
            except Exception as e:
                logger.error(f"[SIMPLE_TRACKER_ERROR] Failed to connect: {e}")
                raise
                
        return self.supabase_client
    
    async def get_last_analysis_time(self, user_id: str) -> Optional[datetime]:
        """
        Get user's last analysis timestamp from profiles table
        Returns None if never analyzed before
        """
        try:
            supabase = self._get_supabase_client()
            
            # Direct query to profiles table
            response = supabase.table('profiles').select('last_analysis_at').eq('id', user_id).execute()
            
            if not response.data or not response.data[0].get('last_analysis_at'):
                logger.info(f"[SIMPLE_TRACKER] No previous analysis found for {user_id}")
                return None
            
            # Parse the timestamp
            timestamp_str = response.data[0]['last_analysis_at']
            last_analysis = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            logger.info(f"[SIMPLE_TRACKER] Last analysis for {user_id}: {last_analysis.isoformat()}")
            
            # Calculate time since last analysis for logging
            hours_since = (datetime.now(timezone.utc) - last_analysis).total_seconds() / 3600
            logger.info(f"[SIMPLE_TRACKER] Time since last analysis: {hours_since:.1f} hours")
            
            return last_analysis
            
        except Exception as e:
            logger.error(f"[SIMPLE_TRACKER_ERROR] Failed to get last analysis for {user_id}: {e}")
            return None
    
    async def update_analysis_time(self, user_id: str, analysis_time: datetime = None) -> bool:
        """
        Update user's last analysis timestamp in profiles table
        Uses direct Supabase client to avoid SQL parsing issues
        """
        try:
            supabase = self._get_supabase_client()
            analysis_time = analysis_time or datetime.now(timezone.utc)
            
            # Direct update using Supabase client
            response = supabase.table('profiles').update({
                'last_analysis_at': analysis_time.isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', user_id).execute()
            
            if response.data:
                logger.info(f"[SIMPLE_TRACKER] Updated analysis time for {user_id}: {analysis_time.isoformat()}")
                return True
            else:
                logger.error(f"[SIMPLE_TRACKER_ERROR] No rows updated for {user_id}")
                return False
            
        except Exception as e:
            logger.error(f"[SIMPLE_TRACKER_ERROR] Failed to update analysis time for {user_id}: {e}")
            return False
    
    async def get_analysis_stats(self, user_id: str) -> dict:
        """
        Get analysis statistics for a user
        Returns time since last analysis and metadata
        """
        try:
            supabase = self._get_supabase_client()
            
            # Get both timestamp and metadata
            response = supabase.table('profiles').select('last_analysis_at, analysis_metadata').eq('id', user_id).execute()
            
            if not response.data:
                return {
                    'user_id': user_id,
                    'last_analysis_at': None,
                    'hours_since_analysis': None,
                    'analysis_count': 0
                }
            
            row = response.data[0]
            last_analysis_str = row.get('last_analysis_at')
            metadata = row.get('analysis_metadata') or {}
            
            last_analysis = None
            hours_since = None
            
            if last_analysis_str:
                last_analysis = datetime.fromisoformat(last_analysis_str.replace('Z', '+00:00'))
                hours_since = (datetime.now(timezone.utc) - last_analysis).total_seconds() / 3600
            
            return {
                'user_id': user_id,
                'last_analysis_at': last_analysis.isoformat() if last_analysis else None,
                'hours_since_analysis': round(hours_since, 1) if hours_since else None,
                'analysis_count': metadata.get('analysis_count', 0),
                'last_data_volume': metadata.get('last_data_volume', {})
            }
            
        except Exception as e:
            logger.error(f"[SIMPLE_TRACKER_ERROR] Failed to get stats for {user_id}: {e}")
            return {}
    
    async def increment_analysis_count(self, user_id: str, scores_count: int, biomarkers_count: int) -> bool:
        """
        Track analysis count and data volume for monitoring
        """
        try:
            supabase = self._get_supabase_client()
            
            # First get current metadata
            response = supabase.table('profiles').select('analysis_metadata').eq('id', user_id).execute()
            
            current_metadata = {}
            if response.data and response.data[0].get('analysis_metadata'):
                current_metadata = response.data[0]['analysis_metadata']
            
            # Update metadata
            new_metadata = {
                **current_metadata,
                'analysis_count': current_metadata.get('analysis_count', 0) + 1,
                'last_data_volume': {
                    'scores': scores_count,
                    'biomarkers': biomarkers_count,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Update the metadata
            update_response = supabase.table('profiles').update({
                'analysis_metadata': new_metadata
            }).eq('id', user_id).execute()
            
            if update_response.data:
                logger.info(f"[SIMPLE_TRACKER] Incremented analysis count for {user_id}")
                return True
            else:
                logger.error(f"[SIMPLE_TRACKER_ERROR] Failed to update metadata for {user_id}")
                return False
            
        except Exception as e:
            logger.error(f"[SIMPLE_TRACKER_ERROR] Failed to increment count for {user_id}: {e}")
            return False
    
    async def cleanup(self):
        """Clean shutdown - no persistent connections to close"""
        logger.info("[SIMPLE_TRACKER] Cleanup completed")