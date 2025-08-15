"""
Insights Extraction Service - Final Consolidated Version
Extracts and manages insights from health analysis results
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter

logger = logging.getLogger(__name__)


class InsightsExtractionService:
    """Consolidated insights service using proven memory service patterns"""
    
    def __init__(self):
        self.db_adapter = None
        
    async def _ensure_db_connection(self) -> SupabaseAsyncPGAdapter:
        """Same connection pattern as memory service"""
        if not self.db_adapter or not self.db_adapter.is_connected:
            try:
                print(f"[🔄 INSIGHTS_SERVICE] Creating new adapter and connecting...")
                self.db_adapter = SupabaseAsyncPGAdapter()
                await self.db_adapter.connect()
                print(f"[✅ INSIGHTS_SERVICE] Connected to Supabase successfully")
                logger.debug("[INSIGHTS_SERVICE] Connected to Supabase successfully")
            except Exception as e:
                print(f"[❌ INSIGHTS_SERVICE_ERROR] Connection failed: {e}")
                logger.error(f"[INSIGHTS_SERVICE_ERROR] Connection failed: {e}")
                raise e
        return self.db_adapter

    # Method 1: Simple insight storage (for MVP)
    async def store_simple_insight(
        self,
        user_id: str,
        title: str,
        content: str,
        insight_type: str = "general",
        archetype: str = "Foundation Builder"
    ) -> bool:
        """Store a simple insight using proven memory service pattern"""
        try:
            db = await self._ensure_db_connection()
            
            # Generate content hash for deduplication
            content_hash = hashlib.md5(content.encode()).hexdigest()
            expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
            
            # Use exact same insert pattern as memory service - step by step debugging
            query = """
                INSERT INTO holistic_insights (
                    user_id, insight_type, insight_title, insight_content,
                    archetype, priority, actionability_score, confidence_score,
                    content_hash, context_signature, is_active, expires_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
            """
            
            print(f"🔍 [DEBUG] About to insert insight with params:")
            print(f"   user_id: {user_id}")
            print(f"   insight_type: {insight_type}")  
            print(f"   title: {title[:50]}...")
            print(f"   content: {content[:100]}...")
            
            # Try the exact same pattern as memory service
            try:
                result = await db.fetchrow(
                    query,
                    user_id,
                    insight_type,
                    title,
                    content,
                    archetype,  # archetype (required field)
                    5,  # priority
                    0.7,  # actionability
                    0.8,  # confidence
                    content_hash,
                    content_hash,  # simple context signature
                    True,  # is_active
                    expires_at
                )
                print(f"🔍 [DEBUG] INSERT result: {result}")
            except Exception as insert_error:
                print(f"🔍 [DEBUG] INSERT error details: {insert_error}")
                print(f"🔍 [DEBUG] INSERT error type: {type(insert_error)}")
                raise insert_error
            
            if result:
                print(f"✨ [INSIGHTS] Stored insight: {title}")
                return True
            else:
                print(f"❌ [INSIGHTS] Failed to store insight - no result returned")
                return False
            
        except Exception as e:
            print(f"❌ [INSIGHTS_ERROR] Failed to store insight: {e}")
            logger.error(f"Failed to store insight: {str(e)}")
            return False

    # Method 2: Advanced insight extraction from analysis results
    async def extract_and_store_insights(
        self,
        analysis_result: Dict[str, Any],
        analysis_type: str,
        user_id: str,
        archetype: str,
        source_analysis_id: Optional[str] = None
    ) -> int:
        """Extract insights from analysis results and store them"""
        try:
            insights = []
            
            # Extract insights based on analysis type
            if analysis_type == 'behavior_analysis':
                # Extract from recommendations
                if 'recommendations' in analysis_result:
                    for i, rec in enumerate(analysis_result['recommendations'][:3], 1):
                        insights.append({
                            'title': f'Key Recommendation #{i}',
                            'content': rec,
                            'type': 'behavioral'
                        })
                
                # Extract from primary goal
                if 'primary_goal' in analysis_result:
                    goal = analysis_result['primary_goal']
                    goal_text = goal.get('goal', '') if isinstance(goal, dict) else str(goal)
                    if goal_text:
                        insights.append({
                            'title': 'Primary Health Goal',
                            'content': goal_text,
                            'type': 'behavioral'
                        })
            
            elif analysis_type in ['nutrition_plan', 'routine_plan']:
                # Extract key content from plans
                if 'content' in analysis_result:
                    content = analysis_result['content']
                    # Take first 400 chars as main insight
                    insights.append({
                        'title': f'{analysis_type.replace("_", " ").title()} Focus',
                        'content': content[:400] + '...' if len(content) > 400 else content,
                        'type': analysis_type.replace('_plan', '').replace('_analysis', '')
                    })
            
            else:
                # Generic extraction
                content = str(analysis_result)[:400]
                insights.append({
                    'title': f'{analysis_type.replace("_", " ").title()} Results',
                    'content': content,
                    'type': 'general'
                })
            
            # Store all extracted insights
            stored_count = 0
            for insight in insights:
                if await self.store_simple_insight(
                    user_id=user_id,
                    title=insight['title'],
                    content=insight['content'],
                    insight_type=insight['type'],
                    archetype=archetype
                ):
                    stored_count += 1
            
            logger.info(f"Extracted and stored {stored_count} insights from {analysis_type}")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error in extract_and_store_insights: {str(e)}")
            return 0

    # Method 3: Retrieve insights
    async def get_user_insights(
        self,
        user_id: str,
        limit: int = 10,
        insight_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get insights for a user"""
        try:
            db = await self._ensure_db_connection()
            
            # Build query based on filters
            if insight_type:
                query = """
                    SELECT * FROM holistic_insights 
                    WHERE user_id = $1 AND is_active = true AND insight_type = $2
                    LIMIT $3
                """
                rows = await db.fetch(query, user_id, insight_type, limit)
            else:
                query = """
                    SELECT * FROM holistic_insights 
                    WHERE user_id = $1 AND is_active = true 
                    LIMIT $2
                """
                rows = await db.fetch(query, user_id, limit)
            
            # Convert to list of dicts
            insights = []
            for row in rows:
                # Handle created_at - could be string or datetime object
                created_at_value = row['created_at']
                if created_at_value:
                    if hasattr(created_at_value, 'isoformat'):
                        created_at_str = created_at_value.isoformat()
                    else:
                        created_at_str = str(created_at_value)  # Already a string
                else:
                    created_at_str = None
                    
                insights.append({
                    'id': str(row['id']),
                    'insight_title': row['insight_title'],
                    'insight_content': row['insight_content'],
                    'insight_type': row['insight_type'],
                    'priority': row['priority'],
                    'actionability_score': float(row['actionability_score']) if row['actionability_score'] else 0.0,
                    'created_at': created_at_str
                })
            
            return insights
            
        except Exception as e:
            print(f"❌ [INSIGHTS_ERROR] Failed to get insights: {e}")
            logger.error(f"Failed to get insights: {str(e)}")
            return []

    # Method 4: Update insight status  
    async def acknowledge_insight(self, insight_id: str) -> bool:
        """Mark insight as acknowledged"""
        try:
            db = await self._ensure_db_connection()
            
            query = """
                UPDATE holistic_insights 
                SET user_acknowledged = true, last_surfaced_at = $1
                WHERE id = $2
            """
            
            await db.execute(query, datetime.utcnow().isoformat(), insight_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to acknowledge insight: {str(e)}")
            return False

    async def rate_insight(self, insight_id: str, rating: int, feedback: Optional[str] = None) -> bool:
        """Rate an insight"""
        try:
            db = await self._ensure_db_connection()
            
            if feedback:
                query = """
                    UPDATE holistic_insights 
                    SET user_rating = $1, user_feedback = $2
                    WHERE id = $3
                """
                await db.execute(query, rating, feedback, insight_id)
            else:
                query = """
                    UPDATE holistic_insights 
                    SET user_rating = $1
                    WHERE id = $2
                """
                await db.execute(query, rating, insight_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rate insight: {str(e)}")
            return False


# Create singleton instance
insights_service = InsightsExtractionService()