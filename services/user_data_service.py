"""
UserDataService - MVP Implementation for Real User Data Fetching
CTO Design Principles: Simple, Reliable, Debuggable, Scalable Foundation
"""
import os
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import logging

# Import existing infrastructure
from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter

# Import new components
from .health_data_client import HealthDataClient
from shared_libs.data_models.health_models import UserHealthContext, create_health_context_from_raw_data

# Setup logging for easy troubleshooting
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserDataService:
    """
    MVP UserDataService - Inspired by health-agent-main patterns
    Focus: Reliability, Simplicity, Easy Debugging
    """
    
    def __init__(self):
        """Initialize with existing infrastructure - reuse what works"""
        self.db_adapter = None
        self.api_client = HealthDataClient()
        self.cache = {}  # Simple memory cache for MVP
        
        # Configuration
        self.default_days = 7
        self.max_records = 1000  # Prevent runaway queries
        self.use_api_first = True  # API-first approach like health-agent-main
        
        logger.info("[USER_DATA_SERVICE] Initialized with API client and database fallback")

    async def _ensure_db_connection(self) -> SupabaseAsyncPGAdapter:
        """Lazy connection initialization - MVP pattern"""
        if not self.db_adapter:
            try:
                self.db_adapter = SupabaseAsyncPGAdapter()
                await self.db_adapter.connect()
                logger.info("[DB] Connected to Supabase successfully")
            except Exception as e:
                logger.error(f"[DB_ERROR] Connection failed: {e}")
                raise
        return self.db_adapter
    
    def _get_date_range(self, days: int = None) -> tuple[datetime, datetime]:
        """Simple date range calculation - clean and debuggable"""
        days = days or self.default_days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"[DATE_RANGE] Fetching {days} days: {start_date.date()} to {end_date.date()}")
        return start_date, end_date

    async def fetch_user_scores(self, user_id: str, days: int = None) -> List[Dict[str, Any]]:
        """
        Fetch user health scores - MVP implementation
        Focus: Clean, reliable, easy to troubleshoot
        """
        start_time = datetime.now()
        start_date, end_date = self._get_date_range(days)
        
        try:
            db = await self._ensure_db_connection()
            
            # Simplified query to avoid SQL parsing issues - CTO fix
            query = """
                SELECT id, profile_id, type, score, data, 
                       score_date_time, created_at, updated_at
                FROM scores 
                WHERE profile_id = $1
                LIMIT $2
            """
            
            logger.info(f"[SCORES] Fetching for user {user_id} (simplified query)")
            rows = await db.fetch(query, user_id, self.max_records)
            
            # Simple data transformation - no over-engineering
            scores = []
            for row in rows:
                try:
                    score_data = {
                        'id': str(row['id']),
                        'profile_id': row['profile_id'],
                        'type': row['type'],
                        'score': float(row['score']),
                        'data': row['data'] if isinstance(row['data'], dict) else {},
                        'score_date_time': row['score_date_time'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                    scores.append(score_data)
                except Exception as row_error:
                    logger.warning(f"[SCORES_WARNING] Skipping bad row: {row_error}")
                    continue
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[SCORES] Retrieved {len(scores)} records in {duration:.2f}s")
            
            return scores
            
        except Exception as e:
            logger.error(f"[SCORES_ERROR] Failed for user {user_id}: {e}")
            return []  # Graceful failure - return empty list

    async def fetch_user_biomarkers(self, user_id: str, days: int = None) -> List[Dict[str, Any]]:
        """Fetch user biomarkers - clean MVP implementation"""
        start_time = datetime.now()
        start_date, end_date = self._get_date_range(days)
        
        try:
            db = await self._ensure_db_connection()
            
            # Simplified query to avoid SQL parsing issues - CTO fix
            query = """
                SELECT id, profile_id, category, type, data,
                       start_date_time, end_date_time, created_at, updated_at
                FROM biomarkers 
                WHERE profile_id = $1
                LIMIT $2
            """
            
            logger.info(f"[BIOMARKERS] Fetching for user {user_id} (simplified query)")
            rows = await db.fetch(query, user_id, self.max_records)
            
            biomarkers = []
            for row in rows:
                try:
                    biomarker_data = {
                        'id': str(row['id']),
                        'profile_id': row['profile_id'],
                        'category': row['category'],
                        'type': row['type'],
                        'data': row['data'] if isinstance(row['data'], dict) else {},
                        'start_date_time': row['start_date_time'],
                        'end_date_time': row['end_date_time'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                    biomarkers.append(biomarker_data)
                except Exception as row_error:
                    logger.warning(f"[BIOMARKERS_WARNING] Skipping bad row: {row_error}")
                    continue
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[BIOMARKERS] Retrieved {len(biomarkers)} records in {duration:.2f}s")
            
            return biomarkers
            
        except Exception as e:
            logger.error(f"[BIOMARKERS_ERROR] Failed for user {user_id}: {e}")
            return []

    async def fetch_user_archetypes(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Fetch user archetypes - get latest for each type
        MVP: Simple logic, easy to understand and debug
        """
        start_time = datetime.now()
        
        try:
            db = await self._ensure_db_connection()
            
            # Simplified query to avoid SQL parsing issues - CTO fix
            query = """
                SELECT id, profile_id, name, periodicity, value, data,
                       start_date_time, end_date_time, created_at, updated_at
                FROM archetypes 
                WHERE profile_id = $1
                LIMIT $2
            """
            
            logger.info(f"[ARCHETYPES] Fetching for user {user_id} (simplified query)")
            rows = await db.fetch(query, user_id, self.max_records)
            
            # Simple deduplication logic - easy to understand and debug
            archetypes_by_key = {}
            for row in rows:
                try:
                    key = f"{row['name']}_{row['periodicity']}"
                    
                    # Keep only the latest (rows are ordered by start_date_time DESC)
                    if key not in archetypes_by_key:
                        archetype_data = {
                            'id': str(row['id']),
                            'profile_id': row['profile_id'],
                            'name': row['name'],
                            'periodicity': row['periodicity'],
                            'value': row['value'],
                            'data': row['data'] if isinstance(row['data'], dict) else {},
                            'start_date_time': row['start_date_time'],
                            'end_date_time': row['end_date_time'],
                            'created_at': row['created_at'],
                            'updated_at': row['updated_at']
                        }
                        archetypes_by_key[key] = archetype_data
                        
                except Exception as row_error:
                    logger.warning(f"[ARCHETYPES_WARNING] Skipping bad row: {row_error}")
                    continue
            
            archetypes = list(archetypes_by_key.values())
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[ARCHETYPES] Retrieved {len(archetypes)} unique archetypes in {duration:.2f}s")
            
            return archetypes
            
        except Exception as e:
            logger.error(f"[ARCHETYPES_ERROR] Failed for user {user_id}: {e}")
            return []

    async def get_user_health_data(self, user_id: str, days: int = None) -> UserHealthContext:
        """
        Main entry point - fetch complete user health data using API-first approach
        MVP: Simple orchestration, comprehensive logging for debugging
        """
        overall_start = datetime.now()
        days = days or self.default_days
        
        logger.info(f"[USER_HEALTH_DATA] Starting fetch for user {user_id}, {days} days")
        
        # Use cache for MVP - simple but effective
        cache_key = f"{user_id}_{days}"
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            if (datetime.now() - cache_data.fetch_timestamp).seconds < 300:  # 5 min cache
                logger.info(f"[CACHE_HIT] Returning cached data for {user_id}")
                return cache_data
        
        start_date, end_date = self._get_date_range(days)
        
        try:
            # Try API first (health-agent-main pattern)
            if self.use_api_first:
                try:
                    logger.info(f"[API_FIRST] Attempting API fetch for {user_id}")
                    api_tasks = [
                        self.api_client.get_user_scores(user_id, start_date, end_date),
                        self.api_client.get_user_biomarkers(user_id, start_date, end_date),
                        self.api_client.get_user_archetypes(user_id)
                    ]
                    
                    api_scores, api_biomarkers, api_archetypes = await asyncio.gather(*api_tasks)
                    
                    # If API returns good data, use it
                    if api_scores or api_biomarkers:
                        logger.info(f"[API_SUCCESS] Using API data: {len(api_scores)} scores, {len(api_biomarkers)} biomarkers")
                        result = create_health_context_from_raw_data(
                            user_id=user_id,
                            raw_scores=api_scores,
                            raw_biomarkers=api_biomarkers,
                            raw_archetypes=api_archetypes,
                            days=days
                        )
                        
                        # Cache and return
                        self.cache[cache_key] = result
                        self._clean_cache()
                        
                        overall_duration = (datetime.now() - overall_start).total_seconds()
                        logger.info(f"[USER_HEALTH_DATA] API completed for {user_id} in {overall_duration:.2f}s")
                        
                        return result
                    
                    logger.info(f"[API_NO_DATA] No API data found, falling back to database")
                    
                except Exception as api_error:
                    logger.warning(f"[API_FALLBACK] API failed for {user_id}: {api_error}, trying database")
            
            # Fallback to database (existing logic)
            logger.info(f"[DB_FALLBACK] Using database for {user_id}")
            tasks = [
                self.fetch_user_scores(user_id, days),
                self.fetch_user_biomarkers(user_id, days),
                self.fetch_user_archetypes(user_id)
            ]
            
            db_scores, db_biomarkers, db_archetypes = await asyncio.gather(*tasks)
            
            # Convert to proper format for create_health_context_from_raw_data
            raw_scores = [
                {
                    'id': s['id'],
                    'profile_id': s['profile_id'],
                    'type': s['type'],
                    'score': s['score'],
                    'data': s['data'],
                    'score_date_time': s['score_date_time'],
                    'created_at': s['created_at'],
                    'updated_at': s['updated_at']
                } for s in db_scores
            ]
            
            raw_biomarkers = [
                {
                    'id': b['id'],
                    'profile_id': b['profile_id'],
                    'category': b['category'],
                    'type': b['type'],
                    'data': b['data'],
                    'start_date_time': b['start_date_time'],
                    'end_date_time': b['end_date_time'],
                    'created_at': b['created_at'],
                    'updated_at': b['updated_at']
                } for b in db_biomarkers
            ]
            
            raw_archetypes = [
                {
                    'id': a['id'],
                    'profile_id': a['profile_id'],
                    'name': a['name'],
                    'periodicity': a['periodicity'],
                    'value': a['value'],
                    'data': a['data'],
                    'start_date_time': a['start_date_time'],
                    'end_date_time': a['end_date_time'],
                    'created_at': a['created_at'],
                    'updated_at': a['updated_at']
                } for a in db_archetypes
            ]
            
            result = create_health_context_from_raw_data(
                user_id=user_id,
                raw_scores=raw_scores,
                raw_biomarkers=raw_biomarkers,
                raw_archetypes=raw_archetypes,
                days=days
            )
            
            # Cache result
            self.cache[cache_key] = result
            self._clean_cache()
            
            overall_duration = (datetime.now() - overall_start).total_seconds()
            logger.info(f"[USER_HEALTH_DATA] Database completed for {user_id} in {overall_duration:.2f}s")
            logger.info(f"[DATA_QUALITY] Scores: {result.data_quality.scores_count}, "
                       f"Biomarkers: {result.data_quality.biomarkers_count}, "
                       f"Quality: {result.data_quality.quality_level}")
            
            return result
            
        except Exception as e:
            logger.error(f"[USER_HEALTH_DATA_ERROR] Failed for user {user_id}: {e}")
            # Return empty result for graceful failure
            return create_health_context_from_raw_data(
                user_id=user_id,
                raw_scores=[],
                raw_biomarkers=[],
                raw_archetypes=[],
                days=days
            )
    
    def _clean_cache(self):
        """Clean old cache entries - prevent memory leaks"""
        if len(self.cache) > 100:  # Simple limit
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].fetch_timestamp)
            del self.cache[oldest_key]

    async def health_check(self) -> Dict[str, Any]:
        """Simple health check for monitoring - essential for production"""
        try:
            db = await self._ensure_db_connection()
            
            # Simple test query - check if profiles table exists
            result = await db.fetch("SELECT COUNT(*) as count FROM profiles LIMIT 1")
            
            return {
                'status': 'healthy',
                'database': 'connected',
                'cache_size': len(self.cache),
                'profiles_accessible': True,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def cleanup(self):
        """Clean shutdown - important for production"""
        if self.db_adapter:
            await self.db_adapter.close()
            logger.info("[USER_DATA_SERVICE] Database connection closed")

# Convenience function for easy import
async def get_user_health_data(user_id: str, days: int = 7) -> UserHealthContext:
    """Simple function interface for agents to use"""
    service = UserDataService()
    try:
        return await service.get_user_health_data(user_id, days)
    finally:
        await service.cleanup()

if __name__ == "__main__":
    # Simple test for development
    async def test():
        service = UserDataService()
        try:
            health = await service.health_check()
            print(f"Health check: {health}")
            
            # Test with a real user if available
            # data = await service.get_user_health_data("test_user", 7)
            # print(f"Data quality: {data.data_quality}")
        finally:
            await service.cleanup()
    
    asyncio.run(test())