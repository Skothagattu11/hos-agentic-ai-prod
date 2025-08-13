"""
Behavior Analysis Scheduler - Background Service
Automatically triggers behavior analysis when sufficient new data is available
CTO Decision: 50+ data points threshold for optimal cost/performance balance
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

# Import existing services
from ..user_data_service import UserDataService
from ..simple_analysis_tracker import SimpleAnalysisTracker
from ..agents.memory.holistic_memory_service import HolisticMemoryService

logger = logging.getLogger(__name__)

class BehaviorAnalysisScheduler:
    """
    Background service that monitors data volume and triggers behavior analysis
    when sufficient new data (50+ points) is available for users
    """
    
    def __init__(self):
        self.user_service = None
        self.analysis_tracker = None
        self.memory_service = None
        self.is_running = False
        self.check_interval_minutes = 30  # Check every 30 minutes
        self.data_threshold = 50  # CTO decision: 50 data points
        self.active_users_cache = {}  # Cache active users list
        self.last_cache_refresh = None
        
    async def initialize(self):
        """Initialize required services"""
        try:
            self.user_service = UserDataService()
            self.analysis_tracker = SimpleAnalysisTracker()
            self.memory_service = HolisticMemoryService()
            logger.info(f"[SCHEDULER] Initialized with {self.data_threshold} data point threshold")
            return True
        except Exception as e:
            logger.error(f"[SCHEDULER_ERROR] Failed to initialize: {e}")
            return False
    
    async def get_active_users(self) -> List[str]:
        """
        Get list of users who have had recent activity (last 7 days)
        Cache results for 1 hour to avoid repeated queries
        """
        now = datetime.now(timezone.utc)
        
        # Use cache if fresh (< 1 hour old)
        if (self.last_cache_refresh and 
            (now - self.last_cache_refresh).total_seconds() < 3600 and
            self.active_users_cache):
            return list(self.active_users_cache.keys())
        
        try:
            # Use simpler approach compatible with Supabase adapter limitations
            # Get recent scores and biomarkers, then process in Python
            
            cutoff_date = now - timedelta(days=7)
            print(f"[SCHEDULER_DEBUG] Looking for users active since: {cutoff_date.isoformat()}")
            
            # Use the existing user service methods which work with the adapter
            all_users = {}
            
            # Instead of complex SQL queries, use a known user ID to test the system
            # In practice, you'd get user IDs from a simpler query or configuration
            test_user_id = "35pDPUIfAoRl2Y700bFkxPKYjjf2"  # Use your test user
            
            try:
                # Test if we can get data for the known user
                user_scores = await self.user_service.fetch_user_scores(test_user_id, days=7)
                user_biomarkers = await self.user_service.fetch_user_biomarkers(test_user_id, days=7)
                
                if user_scores or user_biomarkers:
                    # Calculate latest activity for this user
                    latest_activity = cutoff_date
                    
                    # Handle scores (could be dicts or objects)
                    for score in user_scores:
                        try:
                            created_at = None
                            if hasattr(score, 'created_at'):
                                created_at = score.created_at
                            elif isinstance(score, dict) and 'created_at' in score:
                                created_at = score['created_at']
                            
                            if created_at:
                                # Convert to datetime if it's a string
                                if isinstance(created_at, str):
                                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                elif not isinstance(created_at, datetime):
                                    continue
                                    
                                # Ensure timezone awareness
                                if created_at.tzinfo is None:
                                    created_at = created_at.replace(tzinfo=timezone.utc)
                                    
                                if created_at > latest_activity:
                                    latest_activity = created_at
                        except Exception as date_error:
                            print(f"[SCHEDULER_DEBUG] Date parsing error for score: {date_error}")
                            continue
                    
                    # Handle biomarkers (could be dicts or objects)
                    for biomarker in user_biomarkers:
                        try:
                            created_at = None
                            if hasattr(biomarker, 'created_at'):
                                created_at = biomarker.created_at
                            elif isinstance(biomarker, dict) and 'created_at' in biomarker:
                                created_at = biomarker['created_at']
                            
                            if created_at:
                                # Convert to datetime if it's a string
                                if isinstance(created_at, str):
                                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                elif not isinstance(created_at, datetime):
                                    continue
                                    
                                # Ensure timezone awareness
                                if created_at.tzinfo is None:
                                    created_at = created_at.replace(tzinfo=timezone.utc)
                                    
                                if created_at > latest_activity:
                                    latest_activity = created_at
                        except Exception as date_error:
                            print(f"[SCHEDULER_DEBUG] Date parsing error for biomarker: {date_error}")
                            continue
                    
                    if latest_activity > cutoff_date:
                        all_users[test_user_id] = latest_activity
                        print(f"[SCHEDULER_DEBUG] User {test_user_id[:8]} has recent activity: {latest_activity.isoformat()}")
                    
            except Exception as user_check_error:
                print(f"[SCHEDULER_DEBUG] Could not check user {test_user_id}: {user_check_error}")
            
            # For now, we'll work with known active users
            # TODO: Implement a proper user discovery mechanism or configuration
            if not all_users:
                print("[SCHEDULER_DEBUG] No users found via data query, using fallback to known test user")
                # Fallback: if we know there's a test user, include them for scheduler testing
                all_users[test_user_id] = now
            
            # Update cache
            self.active_users_cache = all_users
            self.last_cache_refresh = now
            
            print(f"[SCHEDULER] Found {len(self.active_users_cache)} active users: {list(all_users.keys())}")
            logger.info(f"[SCHEDULER] Found {len(self.active_users_cache)} active users")
            return list(self.active_users_cache.keys())
            
        except Exception as e:
            logger.error(f"[SCHEDULER_ERROR] Failed to get active users: {e}")
            return []
    
    async def count_new_data_points(self, user_id: str) -> Tuple[int, datetime]:
        """
        Count new data points since last behavior analysis
        Returns: (count, last_analysis_timestamp)
        """
        try:
            # Get last analysis timestamp
            last_analysis = await self.analysis_tracker.get_last_analysis_time(user_id)
            
            if not last_analysis:
                # New user - count all recent data (last 7 days)
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
            else:
                cutoff_time = last_analysis
            
            # Count new scores and biomarkers since cutoff using Supabase client
            db = await self.user_service._ensure_db_connection()
            
            try:
                # Count scores since cutoff
                scores_result = db.client.table("scores").select("id", count="exact").eq("profile_id", user_id).gt("created_at", cutoff_time.isoformat()).execute()
                scores_count = scores_result.count if hasattr(scores_result, 'count') else len(scores_result.data)
                
                # Count biomarkers since cutoff  
                biomarkers_result = db.client.table("biomarkers").select("id", count="exact").eq("profile_id", user_id).gt("created_at", cutoff_time.isoformat()).execute()
                biomarkers_count = biomarkers_result.count if hasattr(biomarkers_result, 'count') else len(biomarkers_result.data)
                
                count = scores_count + biomarkers_count
                
            except Exception as query_error:
                logger.error(f"[SCHEDULER_ERROR] Query error for {user_id}: {query_error}")
                # Fallback to simple count without date filter
                try:
                    scores_result = db.client.table("scores").select("id", count="exact").eq("profile_id", user_id).execute()
                    scores_count = scores_result.count if hasattr(scores_result, 'count') else len(scores_result.data)
                    count = max(scores_count - 20, 0)  # Rough estimate of "new" data
                except Exception:
                    count = 0
            
            hours_since = (datetime.now(timezone.utc) - cutoff_time).total_seconds() / 3600
            logger.debug(f"[SCHEDULER] User {user_id[:8]}... has {count} new data points ({hours_since:.1f}h)")
            
            return count, cutoff_time
            
        except Exception as e:
            logger.error(f"[SCHEDULER_ERROR] Failed to count data for {user_id}: {e}")
            return 0, datetime.now(timezone.utc)
    
    async def should_trigger_analysis(self, user_id: str) -> Tuple[bool, str]:
        """
        Determine if behavior analysis should be triggered for user
        Returns: (should_trigger, reason)
        """
        try:
            count, last_analysis = await self.count_new_data_points(user_id)
            
            # Primary trigger: Data volume threshold
            if count >= self.data_threshold:
                return True, f"{count} new data points (≥{self.data_threshold} threshold)"
            
            # Secondary trigger: Long time gap (5+ days) with some new data
            hours_since = (datetime.now(timezone.utc) - last_analysis).total_seconds() / 3600
            days_since = hours_since / 24
            
            if days_since >= 5 and count >= 10:
                return True, f"{days_since:.1f} days gap with {count} data points"
            
            # No trigger
            return False, f"Only {count} new data points ({days_since:.1f} days)"
            
        except Exception as e:
            logger.error(f"[SCHEDULER_ERROR] Failed to check trigger for {user_id}: {e}")
            return False, f"Error checking: {e}"
    
    async def trigger_behavior_analysis(self, user_id: str, reason: str):
        """
        Trigger behavior analysis for a specific user
        Uses existing analysis system to maintain consistency
        """
        try:
            print(f"🤖 [SCHEDULER] Triggering analysis for {user_id[:8]}... - {reason}")
            
            # Get user's current archetype (or default)
            archetype = await self.get_user_archetype(user_id)
            
            # Import at runtime to avoid circular import
            import sys
            import os
            
            # Add the api_gateway module to path if needed
            api_gateway_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_gateway')
            if api_gateway_path not in sys.path:
                sys.path.insert(0, api_gateway_path)
            
            # Import the analysis function at runtime
            from services.api_gateway.openai_main import run_complete_health_analysis
            
            # Run complete analysis using existing system
            # This preserves all existing functionality and memory integration
            analysis_result = await run_complete_health_analysis(user_id, archetype)
            
            if analysis_result and analysis_result.get('status') == 'success':
                print(f"✅ [SCHEDULER] Analysis completed for {user_id[:8]}...")
                
                # Log successful scheduled analysis
                await self.log_scheduled_analysis(user_id, reason, analysis_result)
            else:
                print(f"❌ [SCHEDULER] Analysis failed for {user_id[:8]}...")
                
        except Exception as e:
            logger.error(f"[SCHEDULER_ERROR] Failed to trigger analysis for {user_id}: {e}")
            print(f"❌ [SCHEDULER] Analysis error for {user_id[:8]}...: {e}")
    
    async def get_user_archetype(self, user_id: str) -> str:
        """Get user's preferred archetype or default to Foundation Builder"""
        try:
            # Try to get from memory system
            memory_profile = await self.memory_service.get_user_longterm_memory(user_id)
            if memory_profile and memory_profile.preference_patterns:
                archetype = memory_profile.preference_patterns.get('preferred_archetype')
                if archetype:
                    return archetype
            
            # Check analysis history for most recent archetype
            analysis_history = await self.memory_service.get_analysis_history(user_id, limit=1)
            if analysis_history and analysis_history[0].archetype_used:
                return analysis_history[0].archetype_used
                
        except Exception as e:
            logger.debug(f"[SCHEDULER] Could not get archetype for {user_id}: {e}")
        
        # Default fallback
        return "Foundation Builder"
    
    async def log_scheduled_analysis(self, user_id: str, reason: str, result: dict):
        """Log scheduled analysis for monitoring"""
        try:
            log_entry = {
                'user_id': user_id,
                'trigger_reason': reason,
                'analysis_result': result.get('status'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'type': 'scheduled_analysis'
            }
            
            # Store in memory system for tracking
            await self.memory_service.store_working_memory(
                user_id=user_id,
                session_id='scheduler',
                agent_id='scheduler',
                memory_type='workflow_state',  # Changed from 'analysis_log' to valid type
                content=log_entry,
                expires_hours=168  # Keep for 1 week
            )
            
        except Exception as e:
            logger.debug(f"[SCHEDULER] Could not log analysis: {e}")
    
    async def check_all_users(self):
        """Check all active users and trigger analysis if needed"""
        try:
            active_users = await self.get_active_users()
            
            if not active_users:
                logger.info("[SCHEDULER] No active users found")
                return
                
            print(f"🔍 [SCHEDULER] Checking {len(active_users)} active users...")
            
            triggers_found = 0
            
            for user_id in active_users:
                try:
                    should_trigger, reason = await self.should_trigger_analysis(user_id)
                    
                    if should_trigger:
                        triggers_found += 1
                        # Run analysis in background to avoid blocking
                        asyncio.create_task(self.trigger_behavior_analysis(user_id, reason))
                    
                except Exception as user_error:
                    logger.error(f"[SCHEDULER_ERROR] Error checking user {user_id}: {user_error}")
                    continue
            
            if triggers_found > 0:
                print(f"🚀 [SCHEDULER] Triggered {triggers_found} behavior analyses")
            else:
                print(f"✅ [SCHEDULER] All users up to date (no triggers needed)")
                
        except Exception as e:
            logger.error(f"[SCHEDULER_ERROR] Failed to check users: {e}")
    
    async def start_monitoring(self):
        """Start the background monitoring loop"""
        self.is_running = True
        logger.info(f"[SCHEDULER] Starting background monitoring (every {self.check_interval_minutes} minutes)")
        
        while self.is_running:
            try:
                await self.check_all_users()
                
                # Wait for next check interval
                await asyncio.sleep(self.check_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"[SCHEDULER_ERROR] Monitoring loop error: {e}")
                # Wait before retrying
                await asyncio.sleep(300)  # 5 minutes
    
    def stop_monitoring(self):
        """Stop the background monitoring"""
        self.is_running = False
        logger.info("[SCHEDULER] Stopping background monitoring")
    
    async def cleanup(self):
        """Clean shutdown"""
        self.stop_monitoring()
        if self.user_service:
            await self.user_service.cleanup()
        if self.analysis_tracker:
            await self.analysis_tracker.cleanup()
        if self.memory_service:
            await self.memory_service.cleanup()

# Global scheduler instance
scheduler_instance = None

async def start_behavior_analysis_scheduler():
    """Start the global behavior analysis scheduler"""
    global scheduler_instance
    
    if scheduler_instance and scheduler_instance.is_running:
        logger.warning("[SCHEDULER] Already running")
        return scheduler_instance
    
    scheduler_instance = BehaviorAnalysisScheduler()
    
    if await scheduler_instance.initialize():
        # Start monitoring in background task
        asyncio.create_task(scheduler_instance.start_monitoring())
        logger.info("[SCHEDULER] Background behavior analysis scheduler started")
        return scheduler_instance
    else:
        logger.error("[SCHEDULER] Failed to start scheduler")
        return None

async def stop_behavior_analysis_scheduler():
    """Stop the global behavior analysis scheduler"""
    global scheduler_instance
    
    if scheduler_instance:
        await scheduler_instance.cleanup()
        scheduler_instance = None
        logger.info("[SCHEDULER] Background scheduler stopped")

def get_scheduler_status() -> dict:
    """Get current scheduler status"""
    global scheduler_instance
    
    if not scheduler_instance:
        return {"status": "not_running", "active_users": 0}
    
    return {
        "status": "running" if scheduler_instance.is_running else "stopped",
        "active_users": len(scheduler_instance.active_users_cache),
        "data_threshold": scheduler_instance.data_threshold,
        "check_interval_minutes": scheduler_instance.check_interval_minutes,
        "last_cache_refresh": scheduler_instance.last_cache_refresh.isoformat() if scheduler_instance.last_cache_refresh else None
    }