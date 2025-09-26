"""
HolisticOS Circadian-Energy Analysis Agent
Follows exact pattern as behavior and routine agents
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
from services.circadian_analysis_service import CircadianAnalysisService

class HolisticCircadianEnergyAgent(BaseAgent):
    """Circadian-Energy Analysis Agent following existing HolisticOS patterns"""

    def __init__(self, redis_url: str = None):
        super().__init__(
            agent_id="circadian_energy_agent",
            agent_type="circadian_energy_analysis",
            redis_url=redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        )

        # Initialize external analysis service (SAME PATTERN as behavior agent)
        self.analysis_agent = CircadianAnalysisService()

        # Initialize Supabase adapter (preserve existing data flow)
        self.supabase = SupabaseAsyncPGAdapter()

        self.logger.debug("HolisticOS Circadian-Energy Agent initialized")

    def get_supported_event_types(self) -> list[str]:
        """Events this agent responds to"""
        return [
            "analysis_request",
            "circadian_update",
            "energy_zone_feedback"
        ]

    async def process(self, event: AgentEvent) -> AgentResponse:
        """Process incoming events - EXACT SAME PATTERN as behavior agent"""
        try:
            self.logger.debug("Processing event",
                           event_type=event.event_type,
                           user_id=event.user_id)

            if event.event_type == "analysis_request":
                return await self._handle_analysis_request(event)
            elif event.event_type == "circadian_update":
                return await self._handle_circadian_update(event)
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
        """Handle circadian analysis requests - EXACT SAME PATTERN as behavior agent"""
        user_id = event.user_id
        archetype = event.archetype
        payload = event.payload

        # Step 1: Request memory context from Memory Agent (placeholder - SAME PATTERN)
        memory_context = await self._get_memory_context(user_id)

        # Step 2: Get user context (SAME PATTERN as behavior agent)
        try:
            await self.supabase.connect()
            user_context = await self._get_user_profile_context(user_id, days=14)  # More days for circadian

            # Get archetype-specific guidance (SAME PATTERN)
            archetype_guidance = self.get_archetype_guidance(archetype) if archetype else ""

            # Step 3: Enhance the analysis with HolisticOS prompt context + Memory (SAME PATTERN)
            enhanced_context = {
                "user_context": user_context,
                "archetype": archetype,
                "archetype_guidance": archetype_guidance,
                "system_prompt": self.system_prompt,
                "memory_context": memory_context,
                "analysis_timestamp": datetime.now().isoformat()
            }

            # Step 4: Use external analysis service (SAME PATTERN as behavior agent)
            analysis_result = await self.analysis_agent.analyze(enhanced_context)

            # Step 5: Store analysis results in memory for future personalization (SAME PATTERN)
            await self._store_analysis_in_memory(user_id, archetype, analysis_result)

            # Step 6: Publish completion event for other agents (SAME PATTERN)

            # Log input/output (preserve existing pattern)
            analysis_number = payload.get("analysis_number", 1)
            self.log_input_output(enhanced_context, analysis_result, analysis_number)

            # Publish results to next agents
            await self.publish_event(
                event_type="circadian_analysis_complete",
                payload={
                    "analysis_result": analysis_result,
                    "user_id": user_id,
                    "archetype": archetype,
                    "next_stage": "plan_generation"
                },
                user_id=user_id,
                archetype=archetype
            )

            self.logger.debug("Circadian analysis completed",
                           user_id=user_id,
                           archetype=archetype)

            return AgentResponse(
                response_id=f"resp_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result={
                    "analysis": analysis_result,
                    "user_id": user_id,
                    "archetype": archetype
                },
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error("Error in circadian analysis",
                            user_id=user_id,
                            error=str(e))
            raise

    async def _handle_circadian_update(self, event: AgentEvent) -> AgentResponse:
        """Handle circadian pattern updates"""
        # Future enhancement: Update circadian patterns based on new data
        return AgentResponse(
            response_id=f"resp_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={"message": "Circadian update acknowledged"},
            timestamp=datetime.now()
        )

    async def _get_user_profile_context(self, user_id: str, days: int = 14) -> Dict[str, Any]:
        """Get user biomarker context - MODIFIED from behavior agent for biomarkers"""
        try:
            # Use existing user data service for biomarkers (SAME PATTERN)
            from services.user_data_service import UserDataService
            user_data_service = UserDataService()

            # Get biomarker data instead of profile data
            biomarker_data = await user_data_service.get_user_health_data(user_id, analysis_number=1)

            return biomarker_data

        except Exception as e:
            self.logger.error("Error fetching biomarker context",
                            user_id=user_id,
                            error=str(e))
            raise

    # Memory Integration Methods (SAME PATTERN as behavior agent - placeholders)

    async def _get_memory_context(self, user_id: str) -> dict:
        """Retrieve circadian memory context - PLACEHOLDER"""
        try:
            # Publish memory retrieval request (SAME PATTERN as behavior agent)
            await self.publish_event(
                event_type="memory_retrieve",
                payload={
                    "memory_type": "circadian",
                    "query_context": "circadian_analysis_context"
                },
                target_agent="memory_management_agent",
                user_id=user_id
            )

            # TODO: Wait for memory response or implement direct memory access
            # For Phase 1 implementation, return empty context for now
            return {
                "energy_patterns": {},
                "schedule_effectiveness": {},
                "biomarker_trends": {},
                "timing_preferences": {},
                "retrieved_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error retrieving circadian memory context: {e}")
            return {}

    async def _store_analysis_in_memory(self, user_id: str, archetype: str, analysis_result) -> None:
        """Store circadian analysis results in memory for personalization - PLACEHOLDER"""
        try:
            # Extract key insights for memory storage (SAME PATTERN as behavior agent)
            analysis_data = analysis_result if isinstance(analysis_result, dict) else {}

            # Store circadian patterns in short-term memory
            circadian_patterns = {
                "chronotype_assessment": analysis_data.get("chronotype_assessment", {}),
                "energy_zone_analysis": analysis_data.get("energy_zone_analysis", {}),
                "schedule_recommendations": analysis_data.get("schedule_recommendations", {}),
                "biomarker_insights": analysis_data.get("biomarker_insights", {}),
                "archetype": archetype,
                "analysis_timestamp": datetime.now().isoformat()
            }

            await self.publish_event(
                event_type="memory_store",
                payload={
                    "memory_type": "shortterm",
                    "category": "circadian_patterns",
                    "data": circadian_patterns,
                    "confidence": analysis_data.get("chronotype_assessment", {}).get("confidence_score", 0.5)
                },
                target_agent="memory_management_agent",
                user_id=user_id
            )

            # Store high-confidence insights in long-term memory
            chronotype_confidence = analysis_data.get("chronotype_assessment", {}).get("confidence_score", 0.0)
            if chronotype_confidence > 0.7:
                circadian_insights = {
                    "chronotype": analysis_data.get("chronotype_assessment", {}),
                    "optimal_energy_zones": analysis_data.get("energy_zone_analysis", {}),
                    "integration_recommendations": analysis_data.get("integration_recommendations", {}),
                    "archetype": archetype,
                    "confidence": chronotype_confidence
                }

                await self.publish_event(
                    event_type="memory_store",
                    payload={
                        "memory_type": "longterm",
                        "category": "circadian_insights",
                        "data": circadian_insights,
                        "confidence": chronotype_confidence
                    },
                    target_agent="memory_management_agent",
                    user_id=user_id
                )

            self.logger.debug(f"Stored circadian analysis in memory for {user_id}")

        except Exception as e:
            self.logger.error(f"Error storing circadian analysis in memory: {e}")

async def main():
    """Main entry point for circadian-energy agent worker - SAME PATTERN as other agents"""
    agent = HolisticCircadianEnergyAgent()

    try:
        # print(f"Starting HolisticOS Circadian-Energy Analysis Agent...")  # Commented for error-only mode
        # print(f"Agent ID: {agent.agent_id}")  # Commented for error-only mode
        # print(f"System Prompt Length: {len(agent.system_prompt)} characters")  # Commented for error-only mode

        # Start listening for events
        await agent.start_listening()

    except KeyboardInterrupt:
        # print("Shutting down circadian-energy agent...")  # Commented for error-only mode
        pass
    except Exception as e:
        print(f"Error running circadian-energy agent: {e}")  # Keep error messages
        raise

if __name__ == "__main__":
    asyncio.run(main())