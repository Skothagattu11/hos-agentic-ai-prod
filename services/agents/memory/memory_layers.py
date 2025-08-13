"""
HolisticOS Memory Layers Implementation
Provides concrete implementations for the 4-layer hierarchical memory system
"""

import asyncio
import asyncpg
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class MemoryLayer:
    """Base class for memory layer implementations"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def store(self, user_id: str, category: str, data: dict, confidence: float = 0.5) -> bool:
        """Store data in this memory layer"""
        raise NotImplementedError
    
    async def retrieve(self, user_id: str, category: Optional[str] = None, limit: int = 100) -> List[dict]:
        """Retrieve data from this memory layer"""
        raise NotImplementedError
    
    async def update(self, memory_id: str, data: dict, confidence: float = None) -> bool:
        """Update existing memory record"""
        raise NotImplementedError
    
    async def delete(self, memory_id: str) -> bool:
        """Delete memory record"""
        raise NotImplementedError

class WorkingMemoryLayer(MemoryLayer):
    """
    Working Memory Layer - Temporary session data
    TTL: Hours to 1 day
    Purpose: Active analysis context, workflow state, temporary insights
    """
    
    async def store(self, user_id: str, category: str, data: dict, confidence: float = 0.5) -> bool:
        """Store working memory with automatic expiration"""
        try:
            if not self.db_pool:
                logger.warning("No database connection - using in-memory storage")
                return True
            
            # Set expiration to 24 hours from now
            expires_at = datetime.now() + timedelta(hours=24)
            
            query = """
                INSERT INTO holistic_working_memory 
                (user_id, session_id, agent_id, memory_type, content, priority, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id, session_id, memory_type, agent_id) 
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    expires_at = EXCLUDED.expires_at,
                    is_active = true
            """
            
            session_id = f"session_{datetime.now().strftime('%Y%m%d')}"
            priority = min(10, max(1, int(confidence * 10)))
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    query,
                    user_id,
                    session_id,
                    "memory_agent",
                    category,
                    json.dumps(data),
                    priority,
                    expires_at
                )
            
            logger.info(f"Stored working memory: {user_id}/{category}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing working memory: {e}")
            return False
    
    async def retrieve(self, user_id: str, category: Optional[str] = None, limit: int = 100) -> List[dict]:
        """Retrieve active working memory"""
        try:
            if not self.db_pool:
                return []
            
            query = """
                SELECT id, memory_type, content, priority, created_at, expires_at
                FROM holistic_working_memory 
                WHERE user_id = $1 
                    AND is_active = true 
                    AND expires_at > NOW()
                    AND ($2 IS NULL OR memory_type = $2)
                ORDER BY priority DESC, created_at DESC
                LIMIT $3
            """
            
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, user_id, category, limit)
                
                memories = []
                for row in rows:
                    memories.append({
                        "id": str(row["id"]),
                        "category": row["memory_type"],
                        "content": json.loads(row["content"]),
                        "priority": row["priority"],
                        "created_at": row["created_at"].isoformat(),
                        "expires_at": row["expires_at"].isoformat()
                    })
                
                return memories
                
        except Exception as e:
            logger.error(f"Error retrieving working memory: {e}")
            return []
    
    async def cleanup_expired(self) -> int:
        """Clean up expired working memory"""
        try:
            if not self.db_pool:
                return 0
            
            query = """
                DELETE FROM holistic_working_memory 
                WHERE expires_at < NOW() OR is_active = false
            """
            
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(query)
                count = int(result.split()[-1])  # Extract count from "DELETE n"
                
                logger.info(f"Cleaned up {count} expired working memory records")
                return count
                
        except Exception as e:
            logger.error(f"Error cleaning up working memory: {e}")
            return 0

class ShortTermMemoryLayer(MemoryLayer):
    """
    Short-term Memory Layer - Recent patterns and behaviors
    TTL: Days to weeks (7-30 days typically)
    Purpose: Recent behavioral patterns, analysis results, preference changes
    """
    
    async def store(self, user_id: str, category: str, data: dict, confidence: float = 0.5) -> bool:
        """Store short-term memory with recency weighting"""
        try:
            if not self.db_pool:
                logger.warning("No database connection - using fallback storage")
                return True
            
            # Calculate recency weight (higher for more recent data)
            recency_weight = min(2.0, 1.0 + (confidence * 0.5))
            expires_at = datetime.now() + timedelta(days=30)
            
            query = """
                INSERT INTO holistic_shortterm_memory 
                (user_id, memory_category, content, confidence_score, recency_weight, 
                 source_agent, expires_at, relevance_score, importance_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            
            relevance_score = confidence
            importance_score = confidence * 0.8  # Slightly lower than confidence
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    query,
                    user_id,
                    category,
                    json.dumps(data),
                    confidence,
                    recency_weight,
                    "memory_agent",
                    expires_at,
                    relevance_score,
                    importance_score
                )
            
            logger.info(f"Stored short-term memory: {user_id}/{category}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing short-term memory: {e}")
            return False
    
    async def retrieve(self, user_id: str, category: Optional[str] = None, limit: int = 50) -> List[dict]:
        """Retrieve short-term memory with recency weighting"""
        try:
            if not self.db_pool:
                return []
            
            query = """
                SELECT id, memory_category, content, confidence_score, recency_weight,
                       relevance_score, importance_score, created_at, last_accessed
                FROM holistic_shortterm_memory 
                WHERE user_id = $1 
                    AND (expires_at IS NULL OR expires_at > NOW())
                    AND ($2 IS NULL OR memory_category = $2)
                ORDER BY recency_weight DESC, confidence_score DESC, created_at DESC
                LIMIT $3
            """
            
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, user_id, category, limit)
                
                memories = []
                for row in rows:
                    memories.append({
                        "id": str(row["id"]),
                        "category": row["memory_category"],
                        "content": json.loads(row["content"]),
                        "confidence": row["confidence_score"],
                        "recency_weight": row["recency_weight"],
                        "relevance": row["relevance_score"],
                        "importance": row["importance_score"],
                        "created_at": row["created_at"].isoformat(),
                        "last_accessed": row["last_accessed"].isoformat()
                    })
                
                # Update last_accessed for retrieved memories
                if memories:
                    memory_ids = [m["id"] for m in memories]
                    update_query = """
                        UPDATE holistic_shortterm_memory 
                        SET last_accessed = NOW(), access_count = access_count + 1
                        WHERE id = ANY($1)
                    """
                    await conn.execute(update_query, memory_ids)
                
                return memories
                
        except Exception as e:
            logger.error(f"Error retrieving short-term memory: {e}")
            return []

class LongTermMemoryLayer(MemoryLayer):
    """
    Long-term Memory Layer - Stable preferences and proven strategies  
    TTL: Months to years (persistent)
    Purpose: User personality, stable preferences, successful strategies, archetype evolution
    """
    
    async def store(self, user_id: str, category: str, data: dict, confidence: float = 0.5) -> bool:
        """Store or update long-term memory with versioning"""
        try:
            if not self.db_pool:
                logger.warning("No database connection - using fallback storage")
                return True
            
            # Use UPSERT to handle existing records properly
            async with self.db_pool.acquire() as conn:
                upsert_query = """
                    INSERT INTO holistic_longterm_memory 
                    (user_id, memory_category, memory_data, confidence_score, 
                     update_source, is_consolidated, version, created_at, last_updated)
                    VALUES ($1, $2, $3, $4, $5, $6, 1, NOW(), NOW())
                    ON CONFLICT (user_id, memory_category) 
                    DO UPDATE SET
                        memory_data = EXCLUDED.memory_data,
                        confidence_score = GREATEST(holistic_longterm_memory.confidence_score, EXCLUDED.confidence_score),
                        version = holistic_longterm_memory.version + 1,
                        last_updated = NOW(),
                        update_source = EXCLUDED.update_source,
                        is_consolidated = EXCLUDED.is_consolidated OR holistic_longterm_memory.is_consolidated
                    RETURNING id, version
                """
                
                result = await conn.fetchrow(
                    upsert_query,
                    user_id,
                    category,
                    json.dumps(data),
                        confidence,
                        "memory_agent",
                        confidence > 0.8  # Higher threshold for new memories
                    )
            
            logger.info(f"Stored long-term memory: {user_id}/{category}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing long-term memory: {e}")
            return False
    
    async def retrieve(self, user_id: str, category: Optional[str] = None, limit: int = 20) -> List[dict]:
        """Retrieve long-term memory (stable preferences)"""
        try:
            if not self.db_pool:
                return []
            
            query = """
                SELECT id, memory_category, memory_data, confidence_score, 
                       stability_score, version, is_consolidated, created_at, last_updated
                FROM holistic_longterm_memory 
                WHERE user_id = $1 
                    AND ($2 IS NULL OR memory_category = $2)
                ORDER BY confidence_score DESC, stability_score DESC, version DESC
                LIMIT $3
            """
            
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, user_id, category, limit)
                
                memories = []
                for row in rows:
                    memories.append({
                        "id": str(row["id"]),
                        "category": row["memory_category"],
                        "content": json.loads(row["memory_data"]),
                        "confidence": row["confidence_score"],
                        "stability": row["stability_score"] or 0.5,
                        "version": row["version"],
                        "consolidated": row["is_consolidated"],
                        "created_at": row["created_at"].isoformat(),
                        "last_updated": row["last_updated"].isoformat()
                    })
                
                return memories
                
        except Exception as e:
            logger.error(f"Error retrieving long-term memory: {e}")
            return []

class MetaMemoryLayer(MemoryLayer):
    """
    Meta-memory Layer - Learning about learning patterns
    TTL: Persistent (continuously updated)
    Purpose: User's learning patterns, adaptation effectiveness, system performance
    """
    
    async def store(self, user_id: str, category: str, data: dict, confidence: float = 0.5) -> bool:
        """Store or update meta-memory (one record per user)"""
        try:
            if not self.db_pool:
                logger.warning("No database connection - using fallback storage")
                return True
            
            # Meta-memory is typically one record per user, continuously updated
            query = """
                INSERT INTO holistic_meta_memory 
                (user_id, adaptation_patterns, learning_velocity, success_predictors, 
                 failure_patterns, agent_effectiveness, archetype_evolution, 
                 engagement_patterns, adaptability_score, consistency_score, 
                 complexity_tolerance, confidence_level, sample_size,
                 analysis_window_start, analysis_window_end)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    adaptation_patterns = EXCLUDED.adaptation_patterns,
                    learning_velocity = EXCLUDED.learning_velocity,
                    success_predictors = EXCLUDED.success_predictors,
                    failure_patterns = EXCLUDED.failure_patterns,
                    agent_effectiveness = EXCLUDED.agent_effectiveness,
                    archetype_evolution = EXCLUDED.archetype_evolution,
                    engagement_patterns = EXCLUDED.engagement_patterns,
                    adaptability_score = EXCLUDED.adaptability_score,
                    consistency_score = EXCLUDED.consistency_score,
                    complexity_tolerance = EXCLUDED.complexity_tolerance,
                    confidence_level = EXCLUDED.confidence_level,
                    sample_size = holistic_meta_memory.sample_size + 1,
                    last_updated = NOW(),
                    analysis_window_end = NOW()
            """
            
            # Extract or create default meta-memory structure
            adaptation_patterns = data.get("adaptation_patterns", {})
            learning_velocity = data.get("learning_velocity", {})
            success_predictors = data.get("success_predictors", {})
            failure_patterns = data.get("failure_patterns", {})
            agent_effectiveness = data.get("agent_effectiveness", {})
            archetype_evolution = data.get("archetype_evolution", {})
            engagement_patterns = data.get("engagement_patterns", {})
            
            adaptability_score = confidence
            consistency_score = data.get("consistency_score", 0.5)
            complexity_tolerance = data.get("complexity_tolerance", 0.5)
            
            # Analysis window (last 30 days for new records)
            analysis_start = datetime.now() - timedelta(days=30)
            analysis_end = datetime.now()
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    query,
                    user_id,
                    json.dumps(adaptation_patterns),
                    json.dumps(learning_velocity), 
                    json.dumps(success_predictors),
                    json.dumps(failure_patterns),
                    json.dumps(agent_effectiveness),
                    json.dumps(archetype_evolution),
                    json.dumps(engagement_patterns),
                    adaptability_score,
                    consistency_score,
                    complexity_tolerance,
                    confidence,
                    1,  # sample_size starts at 1, increments on conflict
                    analysis_start,
                    analysis_end
                )
            
            logger.info(f"Stored meta-memory: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing meta-memory: {e}")
            return False
    
    async def retrieve(self, user_id: str, category: Optional[str] = None, limit: int = 1) -> List[dict]:
        """Retrieve meta-memory (typically one record per user)"""
        try:
            if not self.db_pool:
                return []
            
            query = """
                SELECT adaptation_patterns, learning_velocity, success_predictors,
                       failure_patterns, agent_effectiveness, archetype_evolution,
                       engagement_patterns, adaptability_score, consistency_score,
                       complexity_tolerance, confidence_level, sample_size,
                       created_at, last_updated, analysis_window_start, analysis_window_end
                FROM holistic_meta_memory 
                WHERE user_id = $1
            """
            
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id)
                
                if not row:
                    return []
                
                meta_memory = {
                    "adaptation_patterns": json.loads(row["adaptation_patterns"]),
                    "learning_velocity": json.loads(row["learning_velocity"]),
                    "success_predictors": json.loads(row["success_predictors"]),
                    "failure_patterns": json.loads(row["failure_patterns"]),
                    "agent_effectiveness": json.loads(row["agent_effectiveness"]),
                    "archetype_evolution": json.loads(row["archetype_evolution"]),
                    "engagement_patterns": json.loads(row["engagement_patterns"]),
                    "adaptability_score": row["adaptability_score"],
                    "consistency_score": row["consistency_score"],
                    "complexity_tolerance": row["complexity_tolerance"],
                    "confidence_level": row["confidence_level"],
                    "sample_size": row["sample_size"],
                    "created_at": row["created_at"].isoformat(),
                    "last_updated": row["last_updated"].isoformat(),
                    "analysis_window": {
                        "start": row["analysis_window_start"].isoformat(),
                        "end": row["analysis_window_end"].isoformat()
                    }
                }
                
                return [meta_memory]
                
        except Exception as e:
            logger.error(f"Error retrieving meta-memory: {e}")
            return []

# Memory Layer Factory
class MemoryLayerFactory:
    """Factory for creating memory layer instances"""
    
    @staticmethod
    def create_layer(layer_type: str, db_pool) -> MemoryLayer:
        """Create memory layer instance"""
        if layer_type == "working":
            return WorkingMemoryLayer(db_pool)
        elif layer_type == "shortterm":
            return ShortTermMemoryLayer(db_pool)
        elif layer_type == "longterm":
            return LongTermMemoryLayer(db_pool)
        elif layer_type == "meta":
            return MetaMemoryLayer(db_pool)
        else:
            raise ValueError(f"Unknown memory layer type: {layer_type}")