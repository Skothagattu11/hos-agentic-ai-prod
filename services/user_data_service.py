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
        
        # Phase 4.0 MVP: Simple sync tracking
        self.sync_cache = {}  # In-memory cache for last sync times (MVP approach)
        
        logger.debug("[USER_DATA_SERVICE] Initialized with API client and incremental sync support")

    async def _ensure_db_connection(self) -> SupabaseAsyncPGAdapter:
        """Lazy connection initialization - MVP pattern"""
        if not self.db_adapter:
            try:
                self.db_adapter = SupabaseAsyncPGAdapter()
                await self.db_adapter.connect()
                logger.debug("[DB] Connected to Supabase successfully")
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
            if (datetime.now(timezone.utc) - cache_data.fetch_timestamp).seconds < 300:  # 5 min cache
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
    
    # Simplified Incremental Sync - True incremental from last analysis to now
    async def fetch_data_since(self, user_id: str, since_timestamp: datetime) -> tuple[List[Dict], List[Dict], List[Dict], datetime]:
        """Fetch ALL data from timestamp to now - true incremental"""
        try:
            db = await self._ensure_db_connection()
            
            # Get ALL scores since last analysis
            scores_query = """
                SELECT id, profile_id, type, score, data, 
                       score_date_time, created_at, updated_at
                FROM scores 
                WHERE profile_id = $1 
                  AND created_at > $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            
            # Get ALL biomarkers since last analysis
            biomarkers_query = """
                SELECT id, profile_id, category, type, data,
                       start_date_time, end_date_time, created_at, updated_at
                FROM biomarkers 
                WHERE profile_id = $1 
                  AND created_at > $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            
            logger.info(f"[INCREMENTAL] Fetching data for {user_id} since {since_timestamp.isoformat()}")
            
            # Parallel fetch for efficiency
            scores_task = db.fetch(scores_query, user_id, since_timestamp, self.max_records)
            biomarkers_task = db.fetch(biomarkers_query, user_id, since_timestamp, self.max_records)
            archetypes_task = self.fetch_user_archetypes(user_id)
            
            scores_rows, biomarkers_rows, archetypes = await asyncio.gather(
                scores_task, biomarkers_task, archetypes_task
            )
            
            # Process scores
            scores = []
            for row in scores_rows:
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
                except Exception as e:
                    logger.warning(f"[SCORES_WARNING] Skipping bad row: {e}")
            
            # Process biomarkers
            biomarkers = []
            for row in biomarkers_rows:
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
                except Exception as e:
                    logger.warning(f"[BIOMARKERS_WARNING] Skipping bad row: {e}")
            
            # Calculate the latest data timestamp from all fetched data
            latest_data_timestamp = since_timestamp  # Default to input timestamp
            
            # Find latest timestamp from scores
            if scores:
                latest_score_timestamp = max(score['created_at'] for score in scores)
                latest_data_timestamp = max(latest_data_timestamp, latest_score_timestamp)
            
            # Find latest timestamp from biomarkers  
            if biomarkers:
                latest_biomarker_timestamp = max(biomarker['created_at'] for biomarker in biomarkers)
                latest_data_timestamp = max(latest_data_timestamp, latest_biomarker_timestamp)
            
            hours_since = (datetime.now(timezone.utc) - since_timestamp).total_seconds() / 3600
            print(f"📊 INCREMENTAL_RESULT: {len(scores)} scores, {len(biomarkers)} biomarkers")
            print(f"⏰ TIME_SPAN: {hours_since:.1f} hours of new data")
            print(f"📅 LATEST_DATA: {latest_data_timestamp.strftime('%m/%d %H:%M')}")
            
            return scores, biomarkers, archetypes, latest_data_timestamp
            
        except Exception as e:
            logger.error(f"[INCREMENTAL_ERROR] Failed fetching data since {since_timestamp}: {e}")
            return [], [], [], since_timestamp
    
    async def get_analysis_data(self, user_id: str) -> tuple[UserHealthContext, datetime]:
        """
        Get data for analysis based on last analysis time
        True incremental: fetches ALL data from last analysis to now
        """
        from .simple_analysis_tracker import SimpleAnalysisTracker as AnalysisTracker
        
        overall_start = datetime.now()
        tracker = AnalysisTracker()
        
        # Check when we last analyzed this user
        last_analysis = await tracker.get_last_analysis_time(user_id)
        
        if not last_analysis:
            # First analysis - get 7 days baseline
            logger.info(f"[ANALYSIS_DATA] First analysis for {user_id}, fetching 7 days baseline")
            print(f"📊 INCREMENTAL_SYNC: No previous analysis found - fetching 7 days baseline")
            result = await self.get_user_health_data(user_id, days=7)
            
            # For first analysis, calculate latest timestamp from the fetched data
            latest_data_timestamp = datetime.now(timezone.utc)
            if result.scores:
                latest_data_timestamp = max(score.created_at for score in result.scores)
            if result.biomarkers:
                biomarker_latest = max(biomarker.created_at for biomarker in result.biomarkers)
                latest_data_timestamp = max(latest_data_timestamp, biomarker_latest)
            
            # Track data volume for monitoring
            await tracker.increment_analysis_count(
                user_id, 
                result.data_quality.scores_count,
                result.data_quality.biomarkers_count
            )
            
            duration = (datetime.now() - overall_start).total_seconds()
            logger.info(f"[ANALYSIS_DATA] Initial analysis completed in {duration:.2f}s")
            logger.info(f"[ANALYSIS_DATA] Latest data found: {latest_data_timestamp.isoformat()}")
            return result, latest_data_timestamp
        
        # Calculate time span
        hours_since = (datetime.now(timezone.utc) - last_analysis).total_seconds() / 3600
        days_span = max(1, int(hours_since / 24) + 1)
        
        logger.info(f"[ANALYSIS_DATA] Incremental analysis for {user_id}")
        logger.info(f"[ANALYSIS_DATA] Last analysis: {hours_since:.1f} hours ago at {last_analysis.isoformat()}")
        logger.info(f"[ANALYSIS_DATA] Fetching incremental data from {last_analysis.isoformat()} to now")
        print(f"📊 INCREMENTAL_SYNC: Last analysis was {hours_since:.1f} hours ago")
        print(f"📊 INCREMENTAL_SYNC: Fetching new data since {last_analysis.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            # Get ALL data since last analysis (true incremental)
            scores, biomarkers, archetypes, latest_data_timestamp = await self.fetch_data_since(user_id, last_analysis)
            
            if not scores and not biomarkers:
                print(f"⚠️  ANALYSIS_DATA: No new data since last analysis - checking for stale timestamp")
                
                # Check if last_analysis is beyond all existing data (invalid timestamp scenario)
                db = await self._ensure_db_connection()
                
<<<<<<< HEAD
                # Get the actual latest data timestamp from database
                actual_latest_query = """
                    SELECT 
                        GREATEST(
                            COALESCE(MAX(scores.created_at), '1970-01-01'::timestamp),
                            COALESCE(MAX(biomarkers.created_at), '1970-01-01'::timestamp)
                        ) as actual_latest_timestamp
                    FROM profiles 
                    LEFT JOIN scores ON scores.profile_id = profiles.id
                    LEFT JOIN biomarkers ON biomarkers.profile_id = profiles.id
                    WHERE profiles.id = $1
                """
=======
                # Get the actual latest data timestamp from database - Fixed SQL parsing
                actual_latest_query = "SELECT GREATEST(COALESCE(MAX(scores.created_at), '1970-01-01'::timestamp), COALESCE(MAX(biomarkers.created_at), '1970-01-01'::timestamp)) as actual_latest_timestamp FROM profiles LEFT JOIN scores ON scores.profile_id = profiles.id LEFT JOIN biomarkers ON biomarkers.profile_id = profiles.id WHERE profiles.id = $1"
>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
                
                actual_latest_result = await db.fetch(actual_latest_query, user_id)
                actual_latest_timestamp = actual_latest_result[0]['actual_latest_timestamp'] if actual_latest_result else datetime(1970, 1, 1, tzinfo=timezone.utc)
                
                # If last_analysis is in the future relative to actual data, reset to initial analysis
                if last_analysis > actual_latest_timestamp:
                    print(f"🔄 RESET_TO_INITIAL: last_analysis ({last_analysis.isoformat()}) > actual_latest ({actual_latest_timestamp.isoformat()})")
                    print(f"📊 FALLBACK: Fetching 7 days of historical data for initial analysis")
                    
                    # Fetch 7 days of baseline data (initial analysis mode)
                    result = await self.get_user_health_data(user_id, days=7)
                    
                    # Calculate latest timestamp from the fetched data
                    latest_data_timestamp = datetime.now(timezone.utc)
                    if result.scores:
                        latest_data_timestamp = max(score.created_at for score in result.scores)
                    if result.biomarkers:
                        biomarker_latest = max(biomarker.created_at for biomarker in result.biomarkers)
                        latest_data_timestamp = max(latest_data_timestamp, biomarker_latest)
                        
                    print(f"✅ RECOVERY_SUCCESS: Found {result.data_quality.scores_count} scores, {result.data_quality.biomarkers_count} biomarkers")
                else:
                    print(f"✅ ANALYSIS_DATA: No new data since last analysis - up to date")
                    # Return empty context with last analysis timestamp (no newer data found)
                    result = create_health_context_from_raw_data(
                        user_id=user_id,
                        raw_scores=[],
                        raw_biomarkers=[],
                        raw_archetypes=[],
                        days=days_span
                    )
                    # Use the last analysis timestamp since no new data was found
                    latest_data_timestamp = last_analysis
            else:
                # Create context with incremental data
                result = create_health_context_from_raw_data(
                    user_id=user_id,
                    raw_scores=scores,
                    raw_biomarkers=biomarkers,
                    raw_archetypes=[
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
                        } for a in archetypes
                    ],
                    days=days_span
                )
            
            # Track analysis stats
            await tracker.increment_analysis_count(
                user_id,
                len(scores),
                len(biomarkers)
            )
            
            duration = (datetime.now() - overall_start).total_seconds()
            logger.info(f"[ANALYSIS_DATA] Incremental analysis completed in {duration:.2f}s")
            logger.info(f"[ANALYSIS_DATA] Fetched {len(scores)} scores, {len(biomarkers)} biomarkers")
            logger.info(f"[ANALYSIS_DATA] Latest data timestamp: {latest_data_timestamp.isoformat()}")
            
            return result, latest_data_timestamp
            
        except Exception as e:
            logger.error(f"[ANALYSIS_DATA_ERROR] Incremental failed for {user_id}: {e}")
            # Fallback to full sync on error
            logger.info(f"[ANALYSIS_DATA] Falling back to 7-day fetch")
            result = await self.get_user_health_data(user_id, days=7)
            
            # Calculate latest timestamp from fallback data
            fallback_latest_timestamp = datetime.now(timezone.utc)
            if result.scores:
                fallback_latest_timestamp = max(score.created_at for score in result.scores)
            if result.biomarkers:
                biomarker_latest = max(biomarker.created_at for biomarker in result.biomarkers)
                fallback_latest_timestamp = max(fallback_latest_timestamp, biomarker_latest)
            
            await tracker.increment_analysis_count(
                user_id,
                result.data_quality.scores_count,
                result.data_quality.biomarkers_count
            )
            
            return result, fallback_latest_timestamp

    # Backward compatibility wrapper
    async def get_incremental_health_data(self, user_id: str) -> UserHealthContext:
        """
        Backward compatibility - redirects to new simplified method
        """
        result, _ = await self.get_analysis_data(user_id)
        return result

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