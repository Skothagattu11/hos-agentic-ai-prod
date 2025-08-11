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
        """Reuse existing connection pattern"""
        if not self.db_adapter:
            try:
                self.db_adapter = SupabaseAsyncPGAdapter()
                await self.db_adapter.connect()
                logger.info("[MEMORY_SERVICE] Connected to Supabase successfully")
            except Exception as e:
                logger.error(f"[MEMORY_SERVICE_ERROR] Connection failed: {e}")
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
            
            await db.execute(
                query, user_id, session_id, agent_id, memory_type, content,
                priority, datetime.now(timezone.utc), expires_at, True
            )
            
            logger.info(f"[WORKING_MEMORY] Stored {memory_type} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"[WORKING_MEMORY_ERROR] Failed to store for {user_id}: {e}")
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
            
            logger.info(f"[WORKING_MEMORY] Retrieved {len(working_memory)} items for {user_id}")
            return working_memory
            
        except Exception as e:
            logger.error(f"[WORKING_MEMORY_ERROR] Failed to retrieve for {user_id}: {e}")
            return []
    
    # ========== SHORT-TERM MEMORY (Recent patterns) ==========
    
    async def store_shortterm_memory(self, user_id: str, category: str, content: Dict[str, Any],
                                   confidence_score: float = 0.8, expires_days: int = 30) -> bool:
        """Store data in holistic_shortterm_memory table"""
        try:
            db = await self._ensure_db_connection()
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
            
            query = """
                INSERT INTO holistic_shortterm_memory (
                    user_id, category, content, confidence_score, 
                    created_at, expires_at, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            
            await db.execute(
                query, user_id, category, content, confidence_score,
                datetime.now(timezone.utc), expires_at, True
            )
            
            logger.info(f"[SHORTTERM_MEMORY] Stored {category} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"[SHORTTERM_MEMORY_ERROR] Failed to store for {user_id}: {e}")
            return False
    
    async def get_recent_patterns(self, user_id: str, category: str = None, 
                                days: int = 7) -> List[Dict[str, Any]]:
        """Get recent patterns from holistic_shortterm_memory table"""
        try:
            db = await self._ensure_db_connection()
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Build dynamic query
            conditions = ["user_id = $1", "is_active = true", "expires_at > NOW()", "created_at >= $2"]
            params = [user_id, since_date]
            param_count = 2
            
            if category:
                param_count += 1
                conditions.append(f"category = ${param_count}")
                params.append(category)
            
            query = f"""
                SELECT user_id, category, content, confidence_score, created_at, expires_at
                FROM holistic_shortterm_memory 
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC, confidence_score DESC
            """
            
            rows = await db.fetch(query, *params)
            
            patterns = []
            for row in rows:
                patterns.append({
                    'user_id': row['user_id'],
                    'category': row['category'],
                    'content': row['content'],
                    'confidence_score': row['confidence_score'],
                    'created_at': row['created_at'],
                    'expires_at': row['expires_at']
                })
            
            logger.info(f"[SHORTTERM_MEMORY] Retrieved {len(patterns)} patterns for {user_id}")
            return patterns
            
        except Exception as e:
            logger.error(f"[SHORTTERM_MEMORY_ERROR] Failed to retrieve for {user_id}: {e}")
            return []
    
    # ========== LONG-TERM MEMORY (Stable patterns) ==========
    
    async def get_user_longterm_memory(self, user_id: str) -> Optional[UserMemoryProfile]:
        """Get user's long-term memory profile"""
        try:
            db = await self._ensure_db_connection()
            
            query = """
                SELECT user_id, category, content, confidence_score, created_at, updated_at
                FROM holistic_longterm_memory 
                WHERE user_id = $1 AND is_active = true
                ORDER BY confidence_score DESC, updated_at DESC
            """
            
            rows = await db.fetch(query, user_id)
            
            if not rows:
                logger.info(f"[LONGTERM_MEMORY] No long-term memory found for {user_id}")
                return None
            
            # Aggregate all categories into a single profile
            behavioral_patterns = {}
            health_goals = {}
            preference_patterns = {}
            success_predictors = {}
            max_confidence = 0.0
            latest_created = None
            
            for row in rows:
                category = row['category']
                content = row['content']
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
            
            logger.info(f"[LONGTERM_MEMORY] Retrieved profile for {user_id} with {len(rows)} memory items")
            return profile
            
        except Exception as e:
            logger.error(f"[LONGTERM_MEMORY_ERROR] Failed to retrieve profile for {user_id}: {e}")
            return None
    
    async def update_longterm_memory(self, user_id: str, category: str, 
                                   memory_data: Dict[str, Any], confidence_score: float = 0.9) -> bool:
        """Update or create long-term memory entry"""
        try:
            db = await self._ensure_db_connection()
            
            # Check if entry exists
            check_query = """
                SELECT id FROM holistic_longterm_memory 
                WHERE user_id = $1 AND category = $2 AND is_active = true
            """
            existing = await db.fetch(check_query, user_id, category)
            
            if existing:
                # Update existing entry
                update_query = """
                    UPDATE holistic_longterm_memory 
                    SET content = $3, confidence_score = $4, updated_at = $5
                    WHERE user_id = $1 AND category = $2 AND is_active = true
                """
                await db.execute(update_query, user_id, category, memory_data, 
                               confidence_score, datetime.now(timezone.utc))
                logger.info(f"[LONGTERM_MEMORY] Updated {category} for user {user_id}")
            else:
                # Create new entry
                insert_query = """
                    INSERT INTO holistic_longterm_memory (
                        user_id, category, content, confidence_score, 
                        created_at, updated_at, is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                now = datetime.now(timezone.utc)
                await db.execute(insert_query, user_id, category, memory_data, 
                               confidence_score, now, now, True)
                logger.info(f"[LONGTERM_MEMORY] Created {category} for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"[LONGTERM_MEMORY_ERROR] Failed to update {category} for {user_id}: {e}")
            return False
    
    # ========== META-MEMORY (Learning patterns) ==========
    
    async def get_meta_memory(self, user_id: str) -> Dict[str, Any]:
        """Get user's meta-learning patterns"""
        try:
            db = await self._ensure_db_connection()
            
            query = """
                SELECT category, content, confidence_score, created_at, updated_at
                FROM holistic_meta_memory 
                WHERE user_id = $1 AND is_active = true
                ORDER BY confidence_score DESC, updated_at DESC
            """
            
            rows = await db.fetch(query, user_id)
            
            meta_memory = {}
            for row in rows:
                category = row['category']
                content = row['content']
                meta_memory[category] = {
                    'data': content,
                    'confidence_score': row['confidence_score'],
                    'updated_at': row['updated_at']
                }
            
            logger.info(f"[META_MEMORY] Retrieved {len(rows)} meta-memory items for {user_id}")
            return meta_memory
            
        except Exception as e:
            logger.error(f"[META_MEMORY_ERROR] Failed to retrieve for {user_id}: {e}")
            return {}
    
    async def update_meta_memory(self, user_id: str, adaptation_patterns: Dict[str, Any], 
                               learning_velocity: Dict[str, Any]) -> bool:
        """Update meta-memory with learning patterns"""
        try:
            db = await self._ensure_db_connection()
            now = datetime.now(timezone.utc)
            
            # Update adaptation patterns
            if adaptation_patterns:
                await self._upsert_meta_memory_category(
                    user_id, 'adaptation_patterns', adaptation_patterns, 0.8
                )
            
            # Update learning velocity
            if learning_velocity:
                await self._upsert_meta_memory_category(
                    user_id, 'learning_velocity', learning_velocity, 0.8
                )
            
            logger.info(f"[META_MEMORY] Updated meta-memory for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"[META_MEMORY_ERROR] Failed to update for {user_id}: {e}")
            return False
    
    async def _upsert_meta_memory_category(self, user_id: str, category: str, 
                                         content: Dict[str, Any], confidence: float):
        """Helper to upsert meta-memory category"""
        db = await self._ensure_db_connection()
        
        # Check if exists
        check_query = """
            SELECT id FROM holistic_meta_memory 
            WHERE user_id = $1 AND category = $2 AND is_active = true
        """
        existing = await db.fetch(check_query, user_id, category)
        
        now = datetime.now(timezone.utc)
        
        if existing:
            # Update existing
            update_query = """
                UPDATE holistic_meta_memory 
                SET content = $3, confidence_score = $4, updated_at = $5
                WHERE user_id = $1 AND category = $2 AND is_active = true
            """
            await db.execute(update_query, user_id, category, content, confidence, now)
        else:
            # Insert new
            insert_query = """
                INSERT INTO holistic_meta_memory (
                    user_id, category, content, confidence_score, 
                    created_at, updated_at, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            await db.execute(insert_query, user_id, category, content, confidence, now, now, True)
    
    # ========== ANALYSIS RESULTS (Historical analysis storage) ==========
    
    async def store_analysis_result(self, user_id: str, analysis_type: str, 
                                  analysis_result: Dict[str, Any], archetype_used: str = None) -> str:
        """Store complete analysis in holistic_analysis_results table"""
        try:
            db = await self._ensure_db_connection()
            
            query = """
                INSERT INTO holistic_analysis_results (
                    user_id, analysis_type, analysis_result, archetype_used,
                    created_at, updated_at, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """
            
            now = datetime.now(timezone.utc)
            result = await db.fetch(query, user_id, analysis_type, analysis_result, 
                                  archetype_used, now, now, True)
            
            analysis_id = str(result[0]['id'])
            logger.info(f"[ANALYSIS_RESULTS] Stored {analysis_type} analysis {analysis_id} for user {user_id}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"[ANALYSIS_RESULTS_ERROR] Failed to store for {user_id}: {e}")
            return ""
    
    async def get_analysis_history(self, user_id: str, analysis_type: str = None, 
                                 limit: int = 10) -> List[AnalysisHistory]:
        """Get analysis history from holistic_analysis_results table"""
        try:
            db = await self._ensure_db_connection()
            
            # Build dynamic query
            conditions = ["user_id = $1", "is_active = true"]
            params = [user_id]
            param_count = 1
            
            if analysis_type:
                param_count += 1
                conditions.append(f"analysis_type = ${param_count}")
                params.append(analysis_type)
            
            query = f"""
                SELECT id, user_id, analysis_type, analysis_result, archetype_used, created_at
                FROM holistic_analysis_results 
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC
                LIMIT ${param_count + 1}
            """
            params.append(limit)
            
            rows = await db.fetch(query, *params)
            
            history = []
            for row in rows:
                history.append(AnalysisHistory(
                    analysis_id=str(row['id']),
                    user_id=row['user_id'],
                    analysis_type=row['analysis_type'],
                    analysis_result=row['analysis_result'],
                    created_at=row['created_at'],
                    archetype_used=row['archetype_used']
                ))
            
            logger.info(f"[ANALYSIS_RESULTS] Retrieved {len(history)} analyses for {user_id}")
            return history
            
        except Exception as e:
            logger.error(f"[ANALYSIS_RESULTS_ERROR] Failed to retrieve for {user_id}: {e}")
            return []
    
    # ========== ANALYSIS TYPE DETECTION ==========
    
    async def determine_analysis_mode(self, user_id: str) -> Tuple[str, int]:
        """
        Determine analysis type based on existing analysis history
        Returns: (analysis_type, days_to_fetch)
        """
        try:
            # Get recent analysis history
            recent_analyses = await self.get_analysis_history(user_id, limit=5)
            
            if not recent_analyses:
                logger.info(f"[ANALYSIS_MODE] New user {user_id}: initial analysis")
                return ("initial", 7)  # New user: 7 days data
            
            last_analysis_date = recent_analyses[0].created_at
            days_since_last = (datetime.now(timezone.utc) - last_analysis_date).days
            
            if days_since_last >= 14:
                logger.info(f"[ANALYSIS_MODE] Long gap for {user_id}: initial analysis")
                return ("initial", 7)  # Long gap: treat as new
            elif days_since_last >= 1:
                logger.info(f"[ANALYSIS_MODE] Recent user {user_id}: follow-up analysis")
                return ("follow_up", 1)  # Recent: use 1 day + memory
            else:
                logger.info(f"[ANALYSIS_MODE] Same day for {user_id}: adaptation analysis")
                return ("adaptation", 1)  # Same day: adaptation only
                
        except Exception as e:
            logger.error(f"[ANALYSIS_MODE_ERROR] Failed for {user_id}: {e}")
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
                logger.info(f"[MEMORY_PROMPTS] Enhanced prompt for {user_id} with {len(memory_context_parts)} memory elements")
                return enhanced_prompt
            else:
                logger.info(f"[MEMORY_PROMPTS] No memory context found for {user_id}, using base prompt")
                return base_prompt
                
        except Exception as e:
            logger.error(f"[MEMORY_PROMPTS_ERROR] Failed to enhance prompt for {user_id}: {e}")
            return base_prompt
    
    # ========== CLEANUP ==========
    
    async def cleanup(self):
        """Clean shutdown"""
        if self.db_adapter:
            await self.db_adapter.close()
            logger.info("[MEMORY_SERVICE] Database connection closed")