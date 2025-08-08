"""
HolisticOS Behavior Analysis Agent
Enhanced with system prompts and event-driven architecture
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from shared_libs.event_system.base_agent import BaseAgent, AgentEvent, AgentResponse
from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
from shared_libs.data_models.base_models import UserProfileContext
from shared_libs.utils.existing_behavior_agent import BehaviorAnalysisAgent

class HolisticBehaviorAgent(BaseAgent):
    """Enhanced Behavior Analysis Agent with HolisticOS capabilities"""
    
    def __init__(self, redis_url: str = None):
        super().__init__(
            agent_id="behavior_analysis_agent",
            agent_type="behavior_analysis", 
            redis_url=redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        )
        
        # Initialize existing behavior analysis logic
        self.analysis_agent = BehaviorAnalysisAgent()
        
        # Initialize Supabase adapter (preserve existing data flow)
        self.supabase = SupabaseAsyncPGAdapter()
        
        self.logger.info("HolisticOS Behavior Agent initialized")
    
    def get_supported_event_types(self) -> list[str]:
        """Events this agent responds to"""
        return [
            "analysis_request",
            "user_profile_updated", 
            "behavioral_feedback"
        ]
    
    async def process(self, event: AgentEvent) -> AgentResponse:
        """Process incoming events"""
        try:
            self.logger.info("Processing event", 
                           event_type=event.event_type,
                           user_id=event.user_id)
            
            if event.event_type == "analysis_request":
                return await self._handle_analysis_request(event)
            elif event.event_type == "user_profile_updated":
                return await self._handle_profile_update(event)
            else:
                return AgentResponse(
                    response_id=f"resp_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    success=False,
                    error_message=f"Unsupported event type: {event.event_type}",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self.logger.error("Error processing event", error=str(e))
            return AgentResponse(
                response_id=f"resp_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_analysis_request(self, event: AgentEvent) -> AgentResponse:
        """Handle behavioral analysis requests with memory integration"""
        user_id = event.user_id
        archetype = event.archetype
        payload = event.payload
        
        # Step 1: Request memory context from Memory Agent
        memory_context = await self._get_memory_context(user_id)
        
        # Get user context (preserve existing data fetching)
        try:
            await self.supabase.connect()
            user_context = await self._get_user_profile_context(user_id, days=7)
            
            # Get archetype-specific guidance
            archetype_guidance = self.get_archetype_guidance(archetype) if archetype else ""
            
            # Enhance the analysis with HolisticOS prompt context + Memory
            enhanced_context = {
                "user_context": user_context,
                "archetype": archetype,
                "archetype_guidance": archetype_guidance,
                "system_prompt": self.system_prompt,
                "memory_context": memory_context,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Use existing analysis logic with enhanced context
            analysis_result = await self.analysis_agent.analyze(enhanced_context)
            
            # Step 2: Store analysis results in memory for future personalization
            await self._store_analysis_in_memory(user_id, archetype, analysis_result)
            
            # Step 3: Publish completion event for other agents
            
            # Log input/output (preserve existing pattern)
            analysis_number = payload.get("analysis_number", 1)
            self.log_input_output(enhanced_context, analysis_result.dict(), analysis_number)
            
            # Publish results to next agents
            await self.publish_event(
                event_type="behavior_analysis_complete",
                payload={
                    "analysis_result": analysis_result.dict(),
                    "user_id": user_id,
                    "archetype": archetype,
                    "next_stage": "plan_generation"
                },
                user_id=user_id,
                archetype=archetype
            )
            
            self.logger.info("Behavioral analysis completed", 
                           user_id=user_id,
                           archetype=archetype)
            
            return AgentResponse(
                response_id=f"resp_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result={
                    "analysis": analysis_result.dict(),
                    "user_id": user_id,
                    "archetype": archetype
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error("Error in behavioral analysis", 
                            user_id=user_id, 
                            error=str(e))
            raise
    
    async def _handle_profile_update(self, event: AgentEvent) -> AgentResponse:
        """Handle user profile updates"""
        # Future enhancement: Update analysis based on profile changes
        return AgentResponse(
            response_id=f"resp_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={"message": "Profile update acknowledged"},
            timestamp=datetime.now()
        )
    
    async def _get_user_profile_context(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get user profile context (preserve existing logic)"""
        try:
            # This preserves your existing data fetching mechanism
            # The exact implementation depends on your current user_profile.py logic
            
            # Placeholder - you'll need to adapt this to your existing UserProfileContext
            user_data = {
                "user_id": user_id,
                "date_range": {"days": days},
                "timestamp": datetime.now().isoformat()
            }
            
            return user_data
            
        except Exception as e:
            self.logger.error("Error fetching user profile context", 
                            user_id=user_id, 
                            error=str(e))
            raise
    
    # Memory Integration Methods
    
    async def _get_memory_context(self, user_id: str) -> dict:
        """Retrieve user memory context from Memory Agent"""
        try:
            # Publish memory retrieval request
            await self.publish_event(
                event_type="memory_retrieve",
                payload={
                    "memory_type": "all",
                    "query_context": "behavioral_analysis_context"
                },
                target_agent="memory_management_agent",
                user_id=user_id
            )
            
            # TODO: Wait for memory response or implement direct memory access
            # For Phase 2 development, return empty context for now
            return {
                "working_memory": {},
                "shortterm_memory": {},
                "longterm_memory": {},
                "meta_memory": {},
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving memory context: {e}")
            return {}
    
    async def _store_analysis_in_memory(self, user_id: str, archetype: str, analysis_result) -> None:
        """Store behavioral analysis results in memory for personalization"""
        try:
            # Extract key insights for memory storage
            analysis_data = analysis_result.dict() if hasattr(analysis_result, 'dict') else analysis_result
            
            # Store behavioral patterns in short-term memory
            behavioral_patterns = {
                "behavioral_signature": analysis_data.get("behavioral_signature", {}),
                "sophistication_assessment": analysis_data.get("sophistication_assessment", {}),
                "primary_goal": analysis_data.get("primary_goal", {}),
                "readiness_level": analysis_data.get("readiness_level"),
                "archetype": archetype,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            await self.publish_event(
                event_type="memory_store",
                payload={
                    "memory_type": "shortterm",
                    "category": "behavioral_patterns",
                    "data": behavioral_patterns,
                    "confidence": 0.8
                },
                target_agent="memory_management_agent",
                user_id=user_id
            )
            
            # Store successful strategies in long-term memory if high confidence
            confidence_score = analysis_data.get("sophistication_assessment", {}).get("confidence", 0.0)
            if confidence_score > 0.7:
                successful_strategies = {
                    "personalized_strategy": analysis_data.get("personalized_strategy", {}),
                    "recommendations": analysis_data.get("recommendations", []),
                    "archetype": archetype,
                    "confidence": confidence_score
                }
                
                await self.publish_event(
                    event_type="memory_store",
                    payload={
                        "memory_type": "longterm",
                        "category": "successful_strategies",
                        "data": successful_strategies,
                        "confidence": confidence_score
                    },
                    target_agent="memory_management_agent",
                    user_id=user_id
                )
            
            self.logger.info(f"Stored behavioral analysis in memory for {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error storing analysis in memory: {e}")

async def main():
    """Main entry point for behavior agent worker"""
    agent = HolisticBehaviorAgent()
    
    try:
        print(f"Starting HolisticOS Behavior Analysis Agent...")
        print(f"Agent ID: {agent.agent_id}")
        print(f"System Prompt Length: {len(agent.system_prompt)} characters")
        
        # Start listening for events
        await agent.start_listening()
        
    except KeyboardInterrupt:
        print("Shutting down behavior agent...")
    except Exception as e:
        print(f"Error running behavior agent: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())