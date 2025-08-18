"""
HolisticOS Memory Management Agent
Implements 4-layer hierarchical memory system for user personalization and learning

Memory Layers:
1. Working Memory: Current session data and active context
2. Short-term Memory: Recent patterns and behaviors (7-30 days)
3. Long-term Memory: Stable preferences and proven strategies (months/years)
4. Meta-memory: Learning about user's learning patterns and optimization
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

# Optional database import - not required for Phase 2 development
try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logging.warning("asyncpg not available - using in-memory storage for development")

from shared_libs.event_system.base_agent import BaseAgent, AgentEvent, AgentResponse
from shared_libs.utils.system_prompts import get_system_prompt

logger = logging.getLogger(__name__)

class MemoryRequest(BaseModel):
    """Request for memory operations"""
    operation: str  # 'store', 'retrieve', 'consolidate', 'analyze'
    user_id: str
    memory_type: str  # 'working', 'shortterm', 'longterm', 'meta'
    data: Optional[Dict[str, Any]] = None
    query_context: Optional[str] = None

class MemoryResponse(BaseModel):
    """Response for memory operations"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    insights: Optional[List[str]] = None
    confidence: Optional[float] = None
    message: Optional[str] = None

class HolisticMemoryAgent(BaseAgent):
    """
    HolisticOS Memory Management Agent
    
    Manages 4-layer hierarchical memory system:
    - Working Memory: Session-based temporary data
    - Short-term Memory: Recent behavioral patterns  
    - Long-term Memory: Stable user preferences and successful strategies
    - Meta-memory: Learning patterns about the user's learning and adaptation
    """
    
    def __init__(self, redis_url: str = None):
        super().__init__(
            agent_id="memory_management_agent",
            agent_type="memory_management"
        )
        
        # Database connection (using your existing memory tables)
        self.db_url = None
        self.db_pool = None
        
        # Memory consolidation settings
        self.working_memory_ttl = 3600 * 24  # 24 hours
        self.shortterm_memory_ttl = 3600 * 24 * 30  # 30 days
        self.consolidation_threshold = 0.7  # Confidence threshold for consolidation
        
        logger.debug(f"Initialized HolisticMemoryAgent with system prompt length: {len(self.system_prompt)}")
    
    def get_supported_event_types(self) -> List[str]:
        """Events this memory agent supports"""
        return [
            "memory_store",
            "memory_retrieve", 
            "memory_consolidate",
            "memory_analyze",
            "behavior_analysis_complete",
            "nutrition_plan_complete",
            "routine_plan_complete"
        ]
    
    async def process(self, event: AgentEvent) -> AgentResponse:
        """Process memory-related events"""
        try:
            logger.debug("Processing memory event", 
                       event_type=event.event_type,
                       user_id=event.user_id)
            
            if event.event_type == "memory_store":
                return await self._handle_memory_store(event)
            elif event.event_type == "memory_retrieve":
                return await self._handle_memory_retrieve(event)
            elif event.event_type == "memory_consolidate":
                return await self._handle_memory_consolidate(event)
            elif event.event_type == "memory_analyze":
                return await self._handle_memory_analyze(event)
            elif event.event_type.endswith("_complete"):
                return await self._handle_analysis_complete(event)
            else:
                return AgentResponse(
                    response_id=f"memory_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    success=False,
                    error_message=f"Unsupported event type: {event.event_type}",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error("Error processing memory event", error=str(e))
            return AgentResponse(
                response_id=f"memory_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_memory_store(self, event: AgentEvent) -> AgentResponse:
        """Handle memory storage requests"""
        try:
            user_id = event.user_id
            payload = event.payload
            
            memory_type = payload.get("memory_type", "working")
            data = payload.get("data", {})
            category = payload.get("category", "general")
            confidence = payload.get("confidence", 0.5)
            
            # Store in appropriate memory layer
            if memory_type == "working":
                success = await self._store_working_memory(user_id, category, data, confidence)
            elif memory_type == "shortterm":
                success = await self._store_shortterm_memory(user_id, category, data, confidence)
            elif memory_type == "longterm":
                success = await self._store_longterm_memory(user_id, category, data, confidence)
            elif memory_type == "meta":
                success = await self._store_meta_memory(user_id, data)
            else:
                raise ValueError(f"Invalid memory type: {memory_type}")
            
            if success:
                # Trigger consolidation if needed
                await self._check_consolidation_needs(user_id)
            
            return AgentResponse(
                response_id=f"memory_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=success,
                result={"stored": success, "memory_type": memory_type},
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return AgentResponse(
                response_id=f"memory_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_memory_retrieve(self, event: AgentEvent) -> AgentResponse:
        """Handle memory retrieval requests"""
        try:
            user_id = event.user_id
            payload = event.payload
            
            memory_type = payload.get("memory_type", "all")
            category = payload.get("category")
            query_context = payload.get("query_context", "")
            
            # Retrieve from memory layers
            memory_data = {}
            
            if memory_type in ["all", "working"]:
                memory_data["working"] = await self._retrieve_working_memory(user_id, category)
            
            if memory_type in ["all", "shortterm"]:
                memory_data["shortterm"] = await self._retrieve_shortterm_memory(user_id, category)
            
            if memory_type in ["all", "longterm"]:
                memory_data["longterm"] = await self._retrieve_longterm_memory(user_id, category)
            
            if memory_type in ["all", "meta"]:
                memory_data["meta"] = await self._retrieve_meta_memory(user_id)
            
            # Generate contextual insights using AI
            insights = await self._generate_memory_insights(user_id, memory_data, query_context)
            
            return AgentResponse(
                response_id=f"memory_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result={
                    "memory_data": memory_data,
                    "insights": insights,
                    "user_id": user_id,
                    "context": query_context
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error retrieving memory: {e}")
            return AgentResponse(
                response_id=f"memory_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_memory_consolidate(self, event: AgentEvent) -> AgentResponse:
        """Handle memory consolidation requests"""
        try:
            user_id = event.user_id
            
            # Perform memory consolidation
            consolidation_results = await self._consolidate_user_memory(user_id)
            
            return AgentResponse(
                response_id=f"memory_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result=consolidation_results,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error consolidating memory: {e}")
            return AgentResponse(
                response_id=f"memory_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_memory_analyze(self, event: AgentEvent) -> AgentResponse:
        """Handle memory analysis requests for insights and patterns"""
        try:
            user_id = event.user_id
            analysis_type = event.payload.get("analysis_type", "patterns")
            
            # Retrieve all memory layers for analysis
            memory_data = {
                "working": await self._retrieve_working_memory(user_id),
                "shortterm": await self._retrieve_shortterm_memory(user_id),
                "longterm": await self._retrieve_longterm_memory(user_id),
                "meta": await self._retrieve_meta_memory(user_id)
            }
            
            # Perform AI-powered memory analysis
            analysis_results = await self._analyze_memory_patterns(user_id, memory_data, analysis_type)
            
            return AgentResponse(
                response_id=f"memory_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result=analysis_results,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing memory: {e}")
            return AgentResponse(
                response_id=f"memory_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_analysis_complete(self, event: AgentEvent) -> AgentResponse:
        """Handle completion events from other agents to store results in memory"""
        try:
            user_id = event.user_id
            archetype = event.archetype
            analysis_data = event.payload
            
            # Determine memory storage strategy based on event type
            if "behavior" in event.event_type:
                await self._store_behavior_analysis_memory(user_id, archetype, analysis_data)
            elif "nutrition" in event.event_type:
                await self._store_nutrition_analysis_memory(user_id, archetype, analysis_data)
            elif "routine" in event.event_type:
                await self._store_routine_analysis_memory(user_id, archetype, analysis_data)
            
            # Store general analysis result
            await self._store_working_memory(
                user_id, 
                "analysis_results", 
                {
                    "event_type": event.event_type,
                    "archetype": archetype,
                    "timestamp": event.timestamp.isoformat(),
                    "data": analysis_data
                },
                confidence=0.8
            )
            
            return AgentResponse(
                response_id=f"memory_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result={"stored_analysis": event.event_type},
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error storing analysis memory: {e}")
            return AgentResponse(
                response_id=f"memory_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    # Database Operations (using your memory_system_tables.sql)
    
    async def _get_db_connection(self):
        """Get database connection (placeholder - implement with your DB config)"""
        if not ASYNCPG_AVAILABLE:
            logger.debug("Database not available - using in-memory storage for development")
            return None
        
        # TODO: Implement with your actual database connection
        # For now, return None and use fallback in-memory storage
        return None
    
    async def _store_working_memory(self, user_id: str, category: str, data: dict, confidence: float) -> bool:
        """Store data in working memory (temporary, session-based)"""
        try:
            # TODO: Implement with actual database
            # For Phase 2 development, use in-memory storage temporarily
            logger.debug(f"Storing working memory for {user_id}: {category}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing working memory: {e}")
            return False
    
    async def _store_shortterm_memory(self, user_id: str, category: str, data: dict, confidence: float) -> bool:
        """Store data in short-term memory (recent patterns)"""
        try:
            # TODO: Implement with holistic_shortterm_memory table
            logger.debug(f"Storing short-term memory for {user_id}: {category}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing short-term memory: {e}")
            return False
    
    async def _store_longterm_memory(self, user_id: str, category: str, data: dict, confidence: float) -> bool:
        """Store data in long-term memory (stable preferences)"""
        try:
            # TODO: Implement with holistic_longterm_memory table
            logger.debug(f"Storing long-term memory for {user_id}: {category}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing long-term memory: {e}")
            return False
    
    async def _store_meta_memory(self, user_id: str, data: dict) -> bool:
        """Store data in meta-memory (learning patterns)"""
        try:
            # TODO: Implement with holistic_meta_memory table
            logger.debug(f"Storing meta-memory for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing meta-memory: {e}")
            return False
    
    async def _retrieve_working_memory(self, user_id: str, category: Optional[str] = None) -> dict:
        """Retrieve working memory data"""
        try:
            # TODO: Implement with actual database
            return {}
        except Exception as e:
            logger.error(f"Error retrieving working memory: {e}")
            return {}
    
    async def _retrieve_shortterm_memory(self, user_id: str, category: Optional[str] = None) -> dict:
        """Retrieve short-term memory data"""
        try:
            # TODO: Implement with actual database
            return {}
        except Exception as e:
            logger.error(f"Error retrieving short-term memory: {e}")
            return {}
    
    async def _retrieve_longterm_memory(self, user_id: str, category: Optional[str] = None) -> dict:
        """Retrieve long-term memory data"""
        try:
            # TODO: Implement with actual database
            return {}
        except Exception as e:
            logger.error(f"Error retrieving long-term memory: {e}")
            return {}
    
    async def _retrieve_meta_memory(self, user_id: str) -> dict:
        """Retrieve meta-memory data"""
        try:
            # TODO: Implement with actual database
            return {}
        except Exception as e:
            logger.error(f"Error retrieving meta-memory: {e}")
            return {}
    
    # AI-Powered Memory Operations
    
    async def _generate_memory_insights(self, user_id: str, memory_data: dict, context: str) -> list:
        """Generate insights from memory data using AI"""
        try:
            import openai
            import os
            
            # Check if OpenAI API key is available
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                logger.warning("OpenAI API key not available - using fallback insights")
                return [
                    f"Memory system active for {user_id}",
                    f"Context: {context}",
                    f"Memory layers available: {', '.join(memory_data.keys())}",
                    "AI insights require OPENAI_API_KEY environment variable"
                ]
            
            # Create memory summary for AI analysis
            memory_summary = f"""
USER MEMORY ANALYSIS REQUEST:
User ID: {user_id}
Context: {context}

MEMORY DATA:
Working Memory: {json.dumps(memory_data.get('working', {}), indent=2)}
Short-term Memory: {json.dumps(memory_data.get('shortterm', {}), indent=2)}
Long-term Memory: {json.dumps(memory_data.get('longterm', {}), indent=2)}
Meta-memory: {json.dumps(memory_data.get('meta', {}), indent=2)}

Please analyze this user's memory data and provide:
1. Key patterns and preferences identified
2. Learning trends and adaptation insights
3. Recommendations for personalization
4. Areas where more data would be helpful

Respond with actionable insights in a structured format.
"""
            
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": memory_summary}
                ],
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Parse insights (simplified for now)
            insights = [
                f"Memory analysis for {user_id}",
                "Generated insights based on user patterns",
                content[:200] + "..." if len(content) > 200 else content
            ]
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating memory insights: {e}")
            return [
                f"Memory system active for {user_id}",
                f"Context: {context}",
                f"Memory layers: {', '.join(memory_data.keys())}",
                "Fallback insights - AI analysis temporarily unavailable"
            ]
    
    async def _analyze_memory_patterns(self, user_id: str, memory_data: dict, analysis_type: str) -> dict:
        """Analyze memory patterns using AI"""
        try:
            # Placeholder for pattern analysis
            return {
                "user_id": user_id,
                "analysis_type": analysis_type,
                "patterns_identified": 0,
                "recommendations": ["Memory pattern analysis in development"],
                "confidence": 0.5
            }
            
        except Exception as e:
            logger.error(f"Error analyzing memory patterns: {e}")
            return {"error": str(e)}
    
    # Memory Consolidation
    
    async def _check_consolidation_needs(self, user_id: str) -> None:
        """Check if memory consolidation is needed"""
        try:
            # TODO: Implement consolidation logic
            logger.debug(f"Checking consolidation needs for {user_id}")
            
        except Exception as e:
            logger.error(f"Error checking consolidation needs: {e}")
    
    async def _consolidate_user_memory(self, user_id: str) -> dict:
        """Consolidate user memory across layers"""
        try:
            # TODO: Implement memory consolidation
            return {
                "user_id": user_id,
                "consolidated_items": 0,
                "patterns_identified": 0,
                "preferences_updated": 0
            }
            
        except Exception as e:
            logger.error(f"Error consolidating memory: {e}")
            return {"error": str(e)}
    
    # Specialized Memory Storage
    
    async def _store_behavior_analysis_memory(self, user_id: str, archetype: str, analysis_data: dict):
        """Store behavior analysis results in appropriate memory layers"""
        try:
            # Store in short-term for pattern recognition
            await self._store_shortterm_memory(
                user_id,
                "behavioral_patterns",
                {
                    "archetype": archetype,
                    "sophistication_score": analysis_data.get("sophistication_assessment", {}).get("score"),
                    "readiness_level": analysis_data.get("readiness_level"),
                    "timestamp": datetime.now().isoformat()
                },
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error storing behavior analysis memory: {e}")
    
    async def _store_nutrition_analysis_memory(self, user_id: str, archetype: str, analysis_data: dict):
        """Store nutrition analysis results in memory"""
        try:
            # Store preferences and successful recommendations
            await self._store_shortterm_memory(
                user_id,
                "nutrition_preferences",
                {
                    "archetype": archetype,
                    "meal_preferences": analysis_data.get("preferred_meals", []),
                    "dietary_restrictions": analysis_data.get("restrictions", []),
                    "timestamp": datetime.now().isoformat()
                },
                confidence=0.7
            )
            
        except Exception as e:
            logger.error(f"Error storing nutrition analysis memory: {e}")
    
    async def _store_routine_analysis_memory(self, user_id: str, archetype: str, analysis_data: dict):
        """Store routine analysis results in memory"""
        try:
            # Store successful routines and user engagement patterns
            await self._store_shortterm_memory(
                user_id,
                "routine_preferences",
                {
                    "archetype": archetype,
                    "preferred_activities": analysis_data.get("activities", []),
                    "optimal_times": analysis_data.get("timing_preferences", {}),
                    "timestamp": datetime.now().isoformat()
                },
                confidence=0.7
            )
            
        except Exception as e:
            logger.error(f"Error storing routine analysis memory: {e}")


# Entry point for running the agent standalone
async def main():
    """Run the memory agent in standalone mode for testing"""
    agent = HolisticMemoryAgent()
    
    print("🧠 HolisticOS Memory Management Agent Started")
    print("Memory Layers: Working → Short-term → Long-term → Meta-memory")
    print("Waiting for events...")
    
    # Keep the agent running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Memory Agent")

if __name__ == "__main__":
    asyncio.run(main())