"""
HolisticMemoryService - Phase 4.1 Implementation
Interfaces with existing 4-layer hierarchical memory system in Supabase
Leverages enterprise-grade memory infrastructure already deployed
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter

logger = logging.getLogger(__name__)

@dataclass
class UserMemoryProfile:
    """User's memory profile from long-term memory"""
    user_id: str
    behavioral_patterns: Dict[str, Any]
    health_goals: Dict[str, Any] 
    preference_patterns: Dict[str, Any]
    success_predictors: Dict[str, Any]
    created_at: datetime
    confidence_score: float

@dataclass
class AnalysisHistory:
    """Analysis history from analysis_results table"""
    analysis_id: str
    user_id: str
    analysis_type: str
    analysis_result: Dict[str, Any]
    created_at: datetime
    archetype_used: Optional[str] = None

class HolisticMemoryService:
    """
    Service to interface with existing 4-layer memory system
    - holistic_working_memory: Session-based temporary data
    - holistic_shortterm_memory: Recent patterns (7-30 days)
    - holistic_longterm_memory: Persistent user patterns
    - holistic_meta_memory: Learning about learning patterns
    - holistic_analysis_results: Historical analysis storage
    """
    
    def __init__(self):
        self.db_adapter = None
        
    async def _ensure_db_connection(self) -> SupabaseAsyncPGAdapter:
        """Reuse existing connection pattern - but check if actually connected"""
        # Check if adapter exists AND is connected
        if not self.db_adapter or not self.db_adapter.is_connected:
            try:
        # print(f"[🔄 MEMORY_SERVICE] Creating new adapter and connecting...")  # Commented to reduce noise
                self.db_adapter = SupabaseAsyncPGAdapter()
                await self.db_adapter.connect()
        # print(f"[✅ MEMORY_SERVICE] Connected to Supabase successfully")  # Commented to reduce noise
                logger.debug("[MEMORY_SERVICE] Connected to Supabase successfully")
            except Exception as e:
                print(f"[❌ MEMORY_SERVICE_ERROR] Connection failed: {e}")
                logger.error(f"[MEMORY_SERVICE_ERROR] Connection failed: {e}")
                # Set to None so next attempt creates fresh instance
                self.db_adapter = None
                raise
        return self.db_adapter
    
    # ========== WORKING MEMORY (Session-based) ==========
    
    async def store_working_memory(self, user_id: str, session_id: str, agent_id: str, 
                                 memory_type: str, content: Dict[str, Any], 
                                 priority: int = 5, expires_hours: int = 24) -> bool:
        """Store data in holistic_working_memory table"""
        try:
            db = await self._ensure_db_connection()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
            
            query = """
                INSERT INTO holistic_working_memory (
                    user_id, session_id, agent_id, memory_type, content, 
                    priority, created_at, expires_at, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            
            import json
            await db.execute(
                query, user_id, session_id, agent_id, memory_type, json.dumps(content),
                priority, datetime.now(timezone.utc), expires_at, True
            )
            
            logger.debug(f"[WORKING_MEMORY] Stored {memory_type} for user {user_id}")
            return True
            
        except Exception as e:
            logger.debug(f"[WORKING_MEMORY_ERROR] Failed to store for {user_id}: {e}")
            return False
    
    async def get_working_memory(self, user_id: str, session_id: str = None, 
                               memory_type: str = None) -> List[Dict[str, Any]]:
        """Get data from holistic_working_memory table"""
        try:
            db = await self._ensure_db_connection()
            
            # Build dynamic query based on parameters
            conditions = ["user_id = $1", "is_active = true", "expires_at > NOW()"]
            params = [user_id]
            param_count = 1
            
            if session_id:
                param_count += 1
                conditions.append(f"session_id = ${param_count}")
                params.append(session_id)
                
            if memory_type:
                param_count += 1
                conditions.append(f"memory_type = ${param_count}")
                params.append(memory_type)
            
            query = f"""
                SELECT user_id, session_id, agent_id, memory_type, content, 
                       priority, created_at, expires_at
                FROM holistic_working_memory 
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC
            """
            
            rows = await db.fetch(query, *params)
            
            working_memory = []
            for row in rows:
                working_memory.append({
                    'user_id': row['user_id'],
                    'session_id': row['session_id'],
                    'agent_id': row['agent_id'],
                    'memory_type': row['memory_type'],
                    'content': row['content'],
                    'priority': row['priority'],
                    'created_at': row['created_at'],
                    'expires_at': row['expires_at']
                })
            
            logger.debug(f"[WORKING_MEMORY] Retrieved {len(working_memory)} items for {user_id}")
            return working_memory
            
        except Exception as e:
            logger.debug(f"[WORKING_MEMORY_ERROR] Failed to retrieve for {user_id}: {e}")
            return []
    
    # ========== SHORT-TERM MEMORY (Recent patterns) ==========
    
    async def store_shortterm_memory(self, user_id: str, category: str, content: Dict[str, Any],
                                   confidence_score: float = 0.8, expires_days: int = 30) -> bool:
        """Store data in holistic_shortterm_memory table - using SQL like working memory"""
        try:
            db = await self._ensure_db_connection()
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
            
            # Use SQL execute method - same as working memory which works
            query = """
                INSERT INTO holistic_shortterm_memory (
                    user_id, memory_category, content, confidence_score,
                    source_agent, created_at, expires_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """
            
            import json
            result = await db.fetchrow(
                query, user_id, category, json.dumps(content), confidence_score,
                'memory_service', datetime.now(timezone.utc), expires_at
            )
            
            if result:
                logger.debug(f"[SHORTTERM_MEMORY] Stored {category} for user {user_id}")
                return True
            else:
                logger.debug(f"[SHORTTERM_MEMORY_ERROR] Failed to store {category} - no data returned")
                return False
            
        except Exception as e:
            logger.debug(f"[SHORTTERM_MEMORY_ERROR] Failed to store for {user_id}: {e}")
            return False
    
    async def get_recent_patterns(self, user_id: str, category: str = None, 
                                days: int = 7) -> List[Dict[str, Any]]:
        """Get recent patterns from holistic_shortterm_memory table"""
        try:
            db = await self._ensure_db_connection()
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Build dynamic query
            conditions = ["user_id = $1", "created_at >= $2"]
            params = [user_id, since_date]
            param_count = 2
            
            if category:
                param_count += 1
                conditions.append(f"memory_category = ${param_count}")
                params.append(category)
            
            query = f"""
                SELECT user_id, memory_category, content, confidence_score, created_at, expires_at
                FROM holistic_shortterm_memory 
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC, confidence_score DESC
            """
            
            rows = await db.fetch(query, *params)
            
            patterns = []
            for row in rows:
                patterns.append({
                    'user_id': row['user_id'],
                    'category': row['memory_category'],
                    'content': row['content'],
                    'confidence_score': row['confidence_score'],
                    'created_at': row['created_at'],
                    'expires_at': row['expires_at']
                })
            
            logger.debug(f"[SHORTTERM_MEMORY] Retrieved {len(patterns)} patterns for {user_id}")
            return patterns
            
        except Exception as e:
            logger.debug(f"[SHORTTERM_MEMORY_ERROR] Failed to retrieve for {user_id}: {e}")
            return []
    
    # ========== LONG-TERM MEMORY (Stable patterns) ==========
    
    async def get_user_longterm_memory(self, user_id: str) -> Optional[UserMemoryProfile]:
        """Get user's long-term memory profile"""
        try:
            db = await self._ensure_db_connection()
            
            query = """
                SELECT user_id, memory_category, memory_data, confidence_score, created_at, last_updated
                FROM holistic_longterm_memory 
                WHERE user_id = $1
                ORDER BY confidence_score DESC, last_updated DESC
            """
            
            rows = await db.fetch(query, user_id)
            
            if not rows:
                logger.debug(f"[LONGTERM_MEMORY] No long-term memory found for {user_id}")
                return None
            
            # Aggregate all categories into a single profile
            behavioral_patterns = {}
            health_goals = {}
            preference_patterns = {}
            success_predictors = {}
            max_confidence = 0.0
            latest_created = None
            
            for row in rows:
                category = row['memory_category']
                content = row['memory_data']
                confidence = row['confidence_score']
                created_at = row['created_at']
                
                # Track highest confidence and latest creation
                if confidence > max_confidence:
                    max_confidence = confidence
                if not latest_created or created_at > latest_created:
                    latest_created = created_at
                
                # Categorize content based on category
                if 'behavior' in category.lower():
                    behavioral_patterns[category] = content
                elif 'goal' in category.lower():
                    health_goals[category] = content
                elif 'preference' in category.lower():
                    preference_patterns[category] = content
                elif 'success' in category.lower() or 'pattern' in category.lower():
                    success_predictors[category] = content
                else:
                    # Default to behavioral patterns
                    behavioral_patterns[category] = content
            
            profile = UserMemoryProfile(
                user_id=user_id,
                behavioral_patterns=behavioral_patterns,
                health_goals=health_goals,
                preference_patterns=preference_patterns,
                success_predictors=success_predictors,
                created_at=latest_created or datetime.now(timezone.utc),
                confidence_score=max_confidence
            )
            
            logger.debug(f"[LONGTERM_MEMORY] Retrieved profile for {user_id} with {len(rows)} memory items")
            return profile
            
        except Exception as e:
            logger.debug(f"[LONGTERM_MEMORY_ERROR] Failed to retrieve profile for {user_id}: {e}")
            return None
    
    async def update_longterm_memory(self, user_id: str, category: str, 
                                   memory_data: Dict[str, Any], confidence_score: float = 0.9) -> bool:
        """Update or create long-term memory entry"""
        try:
            db = await self._ensure_db_connection()
            
            # Check if entry exists
            check_query = """
                SELECT id FROM holistic_longterm_memory 
                WHERE user_id = $1 AND memory_category = $2
            """
            existing = await db.fetch(check_query, user_id, category)
            
            if existing:
                # Update existing entry
                update_query = """
                    UPDATE holistic_longterm_memory 
                    SET memory_data = $3, confidence_score = $4, last_updated = $5
                    WHERE user_id = $1 AND memory_category = $2
                """
                import json
                await db.execute(update_query, user_id, category, json.dumps(memory_data), 
                               confidence_score, datetime.now(timezone.utc))
                logger.debug(f"[LONGTERM_MEMORY] Updated {category} for user {user_id}")
            else:
                # Create new entry
                insert_query = """
                    INSERT INTO holistic_longterm_memory (
                        user_id, memory_category, memory_data, confidence_score, 
                        created_at, last_updated, update_source
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                now = datetime.now(timezone.utc)
                import json
                await db.execute(insert_query, user_id, category, json.dumps(memory_data), 
                               confidence_score, now, now, 'memory_service')
                logger.debug(f"[LONGTERM_MEMORY] Created {category} for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.debug(f"[LONGTERM_MEMORY_ERROR] Failed to update {category} for {user_id}: {e}")
            return False
    
    # ========== META-MEMORY (Learning patterns) ==========
    
    async def get_meta_memory(self, user_id: str) -> Dict[str, Any]:
        """Get user's meta-learning patterns"""
        try:
            db = await self._ensure_db_connection()
            
            query = """
                SELECT adaptation_patterns, learning_velocity, success_predictors, 
                       failure_patterns, agent_effectiveness, confidence_level, last_updated
                FROM holistic_meta_memory 
                WHERE user_id = $1
                ORDER BY confidence_level DESC, last_updated DESC
            """
            
            rows = await db.fetch(query, user_id)
            
            meta_memory = {}
            for row in rows:
                meta_memory['adaptation_patterns'] = {
                    'data': row['adaptation_patterns'],
                    'confidence_score': row['confidence_level'],
                    'updated_at': row['last_updated']
                }
                meta_memory['learning_velocity'] = {
                    'data': row['learning_velocity'],
                    'confidence_score': row['confidence_level'],
                    'updated_at': row['last_updated']
                }
                meta_memory['success_predictors'] = {
                    'data': row['success_predictors'],
                    'confidence_score': row['confidence_level'],
                    'updated_at': row['last_updated']
                }
                meta_memory['failure_patterns'] = {
                    'data': row['failure_patterns'],
                    'confidence_score': row['confidence_level'],
                    'updated_at': row['last_updated']
                }
                meta_memory['agent_effectiveness'] = {
                    'data': row['agent_effectiveness'],
                    'confidence_score': row['confidence_level'],
                    'updated_at': row['last_updated']
                }
                break  # Only one row per user
            
            logger.debug(f"[META_MEMORY] Retrieved {len(rows)} meta-memory items for {user_id}")
            return meta_memory
            
        except Exception as e:
            logger.debug(f"[META_MEMORY_ERROR] Failed to retrieve for {user_id}: {e}")
            return {}
    
    async def update_meta_memory(self, user_id: str, adaptation_patterns: Dict[str, Any], 
                               learning_velocity: Dict[str, Any]) -> bool:
        """Update meta-memory with learning patterns"""
        try:
            db = await self._ensure_db_connection()
            now = datetime.now(timezone.utc)
            
            # Check if meta-memory exists for user
            check_query = "SELECT id FROM holistic_meta_memory WHERE user_id = $1"
            existing = await db.fetch(check_query, user_id)
            
            if existing:
                # Update existing meta-memory
                update_query = """
                    UPDATE holistic_meta_memory 
                    SET adaptation_patterns = $2, learning_velocity = $3, last_updated = $4
                    WHERE user_id = $1
                """
                import json
                await db.execute(update_query, user_id, json.dumps(adaptation_patterns or {}), 
                               json.dumps(learning_velocity or {}), now)
            else:
                # Create new meta-memory record using UPSERT for safety
                upsert_query = """
                    INSERT INTO holistic_meta_memory (
                        user_id, adaptation_patterns, learning_velocity, success_predictors,
                        failure_patterns, agent_effectiveness, archetype_evolution, engagement_patterns,
                        created_at, last_updated, analysis_window_start, analysis_window_end
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (user_id) DO UPDATE SET
                        adaptation_patterns = EXCLUDED.adaptation_patterns,
                        learning_velocity = EXCLUDED.learning_velocity,
                        last_updated = EXCLUDED.last_updated,
                        analysis_window_end = EXCLUDED.analysis_window_end
                """
                window_start = now - timedelta(days=30)
                import json
                await db.execute(upsert_query, user_id, json.dumps(adaptation_patterns or {}), 
                               json.dumps(learning_velocity or {}), json.dumps({}), json.dumps({}), json.dumps({}), json.dumps({}), json.dumps({}), 
                               now, now, window_start, now)
            
            logger.debug(f"[META_MEMORY] Updated meta-memory for user {user_id}")
            return True
            
        except Exception as e:
            logger.debug(f"[META_MEMORY_ERROR] Failed to update for {user_id}: {e}")
            return False
    
    # Removed _upsert_meta_memory_category - not needed with new schema
    
    # ========== ANALYSIS RESULTS (Historical analysis storage) ==========
    
    async def store_analysis_result(self, user_id: str, analysis_type: str, 
                                  analysis_result: Dict[str, Any], archetype_used: str = None) -> str:
        """Store complete analysis in holistic_analysis_results table"""
        try:
            db = await self._ensure_db_connection()
            input_summary = {"data_quality": "excellent", "source": "memory_service"}
            
            # Use UPSERT to handle duplicates gracefully
            insert_query = """
                INSERT INTO holistic_analysis_results (
                    user_id, analysis_type, archetype, analysis_result, 
                    input_summary, agent_id, analysis_date
                ) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_DATE)
                ON CONFLICT (user_id, analysis_type, analysis_date, archetype) 
                DO UPDATE SET
                    analysis_result = EXCLUDED.analysis_result,
                    input_summary = EXCLUDED.input_summary,
                    created_at = NOW()
                RETURNING id
            """
            
            import json
            result = await db.fetchrow(insert_query, user_id, analysis_type, archetype_used, 
                                     json.dumps(analysis_result), json.dumps(input_summary), 'memory_service')
            
            if result:
                analysis_id = str(result['id'])
                
                # Optional automatic insights extraction with error handling
                try:
                    from services.insights_extraction_service import insights_service
                    
                    if analysis_id:
                        insights_count = await insights_service.extract_and_store_insights(
                            analysis_result=analysis_result,
                            analysis_type=analysis_type,
                            user_id=user_id,
                            archetype=archetype_used or "Foundation Builder",
                            source_analysis_id=analysis_id
                        )
                        logger.debug(f"Auto-extracted {insights_count} insights from {analysis_type}")
                except Exception as e:
                    # Don't fail the analysis storage if insights extraction fails
                    logger.warning(f"Failed to auto-extract insights: {str(e)}")
                
                return analysis_id
            else:
                logger.error(f"Failed to store {analysis_type} analysis - no result returned")
                return None
                
        except Exception as e:
            logger.error(f"[ANALYSIS_RESULTS_ERROR] Failed to store for {user_id}: {e}")
            return ""
    
    async def get_analysis_history(self, user_id: str, analysis_type: str = None, 
                                 limit: int = 10) -> List[AnalysisHistory]:
        """Get analysis history from holistic_analysis_results table"""
        try:
            db = await self._ensure_db_connection()
            
            # Build dynamic query
            conditions = ["user_id = $1"]
            params = [user_id]
            param_count = 1
            
            if analysis_type:
                param_count += 1
                conditions.append(f"analysis_type = ${param_count}")
                params.append(analysis_type)
            
            query = f"""
                SELECT id, user_id, analysis_type, analysis_result, archetype, created_at
                FROM holistic_analysis_results 
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC
                LIMIT ${param_count + 1}
            """
            params.append(limit)
            
            rows = await db.fetch(query, *params)
            
            history = []
            for row in rows:
                # Parse JSON string to object if needed - CTO Fix for shared analysis
                analysis_result = row['analysis_result']
                if isinstance(analysis_result, str):
                    try:
                        import json
                        analysis_result = json.loads(analysis_result)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"[ANALYSIS_HISTORY] Failed to parse JSON analysis_result for {row['id']}")
                        # Keep as string if parsing fails
                        
                history.append(AnalysisHistory(
                    analysis_id=str(row['id']),
                    user_id=row['user_id'],
                    analysis_type=row['analysis_type'],
                    analysis_result=analysis_result,
                    created_at=row['created_at'],
                    archetype_used=row['archetype']
                ))
            
            logger.debug(f"[ANALYSIS_RESULTS] Retrieved {len(history)} analyses for {user_id}")
            return history
            
        except Exception as e:
            logger.debug(f"[ANALYSIS_RESULTS_ERROR] Failed to retrieve for {user_id}: {e}")
            return []
    
    # ========== ANALYSIS TYPE DETECTION ==========
    
    async def determine_analysis_mode(self, user_id: str) -> Tuple[str, int]:
        """
        Determine analysis type based on existing analysis history
        Returns: (analysis_type, days_to_fetch)
        """
        try:
            # Get recent analysis history from holistic_analysis_results table
            recent_analyses = await self.get_analysis_history(user_id, limit=5)
            
            # Also check profiles.last_analysis_at as a more reliable source
            last_analysis_from_profile = None
            try:
                # Import at runtime to avoid circular dependencies
                import sys
                import os
                # Add parent path to import from services
                parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                from services.simple_analysis_tracker import SimpleAnalysisTracker
                
                tracker = SimpleAnalysisTracker()
                last_analysis_from_profile = await tracker.get_last_analysis_time(user_id)
                if last_analysis_from_profile:
                    # print(f"📊 PROFILE_CHECK: Found last_analysis_at = {last_analysis_from_profile.isoformat()}")  # Commented to reduce noise
                    pass
            except Exception as profile_error:
                print(f"⚠️ PROFILE_CHECK: Could not check profiles table: {profile_error}")
            
            # Determine the most recent analysis timestamp from both sources
            last_analysis_date = None
            source = "none"
            
            if recent_analyses and last_analysis_from_profile:
                # Both sources have data - use the more recent one
                if recent_analyses[0].created_at > last_analysis_from_profile:
                    last_analysis_date = recent_analyses[0].created_at
                    source = "analysis_results"
                else:
                    last_analysis_date = last_analysis_from_profile
                    source = "profiles"
        # print(f"🔍 ANALYSIS_MODE: Using {source} table (more recent)")  # Commented to reduce noise
            elif recent_analyses:
                # Only analysis history available
                last_analysis_date = recent_analyses[0].created_at
                source = "analysis_results"
        # print(f"📋 ANALYSIS_MODE: Using analysis_results table (profiles empty)")  # Commented to reduce noise
            elif last_analysis_from_profile:
                # Only profile timestamp available - THIS IS THE KEY FIX
                last_analysis_date = last_analysis_from_profile
                source = "profiles"
        # print(f"✅ ANALYSIS_MODE: Using profiles table (analysis_results empty)")  # Commented to reduce noise
            
            if not last_analysis_date:
                print(f"🆕 ANALYSIS_MODE: New user - initial analysis (7 days data)")
                return ("initial", 7)  # New user: 7 days data
            
            # Calculate time since last analysis for logging
            time_since_last = datetime.now(timezone.utc) - last_analysis_date
            days_since_last = time_since_last.days
            hours_since_last = time_since_last.total_seconds() / 3600
            minutes_since_last = time_since_last.total_seconds() / 60
            
            # print(f"⏱️ ANALYSIS_MODE: Last analysis was {minutes_since_last:.1f} minutes ago ({hours_since_last:.1f} hours, {days_since_last} days) from {source}")  # Commented for error-only mode
            
            # Simple logic: If ANY previous analysis exists, next one is ALWAYS follow-up
            # Only exception: very long gaps (2+ weeks) treated as fresh start
            if days_since_last >= 14:
                print(f"⏰ ANALYSIS_MODE: Very long gap ({days_since_last} days) - treating as fresh initial analysis")
                return ("initial", 7)  # Only very long gaps get initial treatment
            else:
        # print(f"🔄 ANALYSIS_MODE: Previous analysis found - this is a FOLLOW-UP analysis (incremental data + memory)")  # Commented to reduce noise
                return ("follow_up", 1)  # ANY previous analysis = follow-up mode
                
        except Exception as e:
            logger.error(f"[ANALYSIS_MODE_ERROR] Failed for {user_id}: {e}")
            print(f"❌ ANALYSIS_MODE_ERROR: {e}")
            # Default to initial on error
            return ("initial", 7)
    
    # ========== MEMORY-ENHANCED PROMPTS ==========
    
    async def enhance_prompts_with_memory(self, base_prompt: str, user_id: str) -> str:
        """Add memory context to agent prompts"""
        try:
            # Get relevant memory layers
            longterm = await self.get_user_longterm_memory(user_id)
            recent_patterns = await self.get_recent_patterns(user_id)
            meta_memory = await self.get_meta_memory(user_id)
            
            # Build memory context
            memory_context_parts = []
            
            if longterm:
                memory_context_parts.append("USER LONG-TERM MEMORY:")
                if longterm.behavioral_patterns:
                    memory_context_parts.append(f"  Behavioral Patterns: {longterm.behavioral_patterns}")
                if longterm.health_goals:
                    memory_context_parts.append(f"  Health Goals: {longterm.health_goals}")
                if longterm.preference_patterns:
                    memory_context_parts.append(f"  Preferences: {longterm.preference_patterns}")
                if longterm.success_predictors:
                    memory_context_parts.append(f"  What Works: {longterm.success_predictors}")
            
            if recent_patterns:
                memory_context_parts.append("\nRECENT PATTERNS:")
                for pattern in recent_patterns[:3]:  # Limit to top 3 recent patterns
                    memory_context_parts.append(f"  {pattern['category']}: {pattern['content']}")
            
            if meta_memory:
                memory_context_parts.append("\nMETA-LEARNING:")
                for category, data in meta_memory.items():
                    if category in ['adaptation_patterns', 'learning_velocity']:
                        memory_context_parts.append(f"  {category}: {data['data']}")
            
            if memory_context_parts:
                memory_context = "\n".join(memory_context_parts)
                enhanced_prompt = f"{base_prompt}\n\n{memory_context}\n\nImportant: Use this memory context to personalize your analysis."
                # print(f"🧠 MEMORY_ENHANCED: Prompt enhanced with {len(memory_context_parts)} memory elements")  # Commented for error-only mode
                return enhanced_prompt
            else:
                print(f"💭 MEMORY_ENHANCED: No memory context - using base prompt")
                return base_prompt
                
        except Exception as e:
            logger.error(f"[MEMORY_PROMPTS_ERROR] Failed to enhance prompt for {user_id}: {e}")
            return base_prompt
    
    # ========== CLEANUP ==========
    
    async def cleanup(self):
        """Clean shutdown"""
        if self.db_adapter:
            await self.db_adapter.close()
            logger.debug("[MEMORY_SERVICE] Database connection closed")