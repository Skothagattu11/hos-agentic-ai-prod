# Updated Circadian Agent Integration Plan
## AI-Powered Analysis Following Existing Agent Patterns

## Overview

This updated plan integrates the **unified circadian-energy analysis agent** using **OpenAI models for intelligent biomarker analysis** instead of manual if-then loops. The implementation follows the **exact same patterns** used by existing agents (behavior, routine, nutrition) for consistency and non-disruptive integration.

## Current Agent Pattern Analysis

### **Existing Agent Structure Pattern**
```python
# Pattern from services/agents/behavior/main.py & services/agents/routine/main.py

class HolisticBehaviorAgent(BaseAgent):
    def __init__(self, redis_url: str = None):
        super().__init__(
            agent_id="behavior_analysis_agent",
            agent_type="behavior_analysis",
            redis_url=redis_url
        )

        # Initialize external analysis service
        self.analysis_agent = BehaviorAnalysisAgent()  # External AI service

        # Initialize Supabase adapter (preserve existing data flow)
        self.supabase = SupabaseAsyncPGAdapter()

    async def _handle_analysis_request(self, event: AgentEvent):
        # Step 1: Get memory context (placeholder)
        memory_context = await self._get_memory_context(user_id)

        # Step 2: Get user data
        user_context = await self._get_user_profile_context(user_id, days=7)

        # Step 3: Build enhanced context
        enhanced_context = {
            "user_context": user_context,
            "archetype": archetype,
            "memory_context": memory_context,
            "system_prompt": self.system_prompt
        }

        # Step 4: Use external AI service for analysis
        analysis_result = await self.analysis_agent.analyze(enhanced_context)

        # Step 5: Store in memory, log, publish events
```

### **Key Pattern Elements**
1. **External AI Service**: Uses separate analysis service (not inline OpenAI calls)
2. **Supabase Integration**: Preserves existing data flow patterns
3. **Memory Placeholders**: Ready for future memory integration
4. **Event Publishing**: Publishes results to other agents
5. **MVP Logging**: Uses mvp_logger for input/output tracking

## Updated Implementation Plan

### **Phase 1: Create Circadian Analysis Service (Week 1, Days 1-2)**

Following the **exact same pattern** as `BehaviorAnalysisAgent`, create a separate AI service.

#### **Step 1.1: Create Circadian Analysis Service**
Create `services/circadian_analysis_service.py`:

```python
"""
Circadian Analysis Service - AI-Powered Biomarker Analysis
Follows same pattern as BehaviorAnalysisAgent
"""

import os
import json
from datetime import datetime
from typing import Dict, Any
from openai import AsyncOpenAI

class CircadianAnalysisService:
    """AI-powered circadian rhythm analysis service using OpenAI models"""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # Use GPT-4o for advanced biomarker analysis

    async def analyze(self, enhanced_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered circadian analysis - matches BehaviorAnalysisAgent.analyze() signature
        """
        try:
            # Extract context data
            biomarker_data = enhanced_context.get("user_context", {})
            archetype = enhanced_context.get("archetype", "Foundation Builder")
            memory_context = enhanced_context.get("memory_context", {})

            # Get specialized system prompt
            system_prompt = self._get_circadian_system_prompt(archetype)

            # Prepare AI analysis prompt
            user_prompt = self._prepare_analysis_prompt(biomarker_data, memory_context, archetype)

            # Call OpenAI for intelligent analysis
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            # Parse and structure AI response
            ai_analysis = json.loads(response.choices[0].message.content)

            # Add metadata (matches existing pattern)
            ai_analysis["analysis_metadata"] = {
                "model_used": self.model,
                "analysis_type": "ai_powered_circadian",
                "token_usage": response.usage.total_tokens if response.usage else 0,
                "analysis_timestamp": datetime.now().isoformat()
            }

            return ai_analysis

        except Exception as e:
            # Return error structure matching existing pattern
            return {
                "chronotype_assessment": {"primary_type": "unknown", "confidence_score": 0.0},
                "energy_zone_analysis": {"peak_windows": [], "productive_windows": [], "recovery_windows": []},
                "schedule_recommendations": {},
                "integration_recommendations": {},
                "error": str(e)
            }

    def _get_circadian_system_prompt(self, archetype: str) -> str:
        """Get specialized system prompt for circadian analysis"""
        return f"""
You are a specialized Circadian Rhythm and Energy Optimization AI agent for the HolisticOS health system.

Your role is to analyze biomarker data (sleep patterns, HRV, activity rhythms, recovery metrics) and provide comprehensive circadian rhythm insights and energy zone recommendations.

## USER ARCHETYPE: {archetype}
Tailor your analysis and recommendations to this archetype's optimization style and preferences.

## ANALYSIS REQUIREMENTS:

1. **Chronotype Assessment**: Determine user's natural chronotype based on sleep timing, activity patterns, and biomarker rhythms
2. **Energy Zone Mapping**: Identify specific time windows for peak, productive, maintenance, and recovery activities
3. **Schedule Optimization**: Provide timing recommendations for work, exercise, meals, and sleep
4. **Biomarker Integration**: Analyze HRV trends, sleep quality patterns, and recovery indicators
5. **Integration Guidelines**: Provide specific recommendations for routine and behavior agents

## RESPONSE FORMAT:
Respond with valid JSON containing chronotype_assessment, energy_zone_analysis, schedule_recommendations, and integration_recommendations sections.

Focus on actionable, evidence-based recommendations derived from the biomarker patterns you observe.
"""

    def _prepare_analysis_prompt(self, biomarker_data: Dict, memory_context: Dict, archetype: str) -> str:
        """Prepare comprehensive prompt for AI analysis"""
        return f"""
Analyze this biomarker data for circadian rhythm and energy optimization insights:

## BIOMARKER DATA:
{json.dumps(biomarker_data, indent=2)}

## MEMORY CONTEXT (Previous Patterns):
{json.dumps(memory_context, indent=2)}

## USER PROFILE:
- Archetype: {archetype}
- Analysis Timestamp: {datetime.now().isoformat()}

Provide comprehensive JSON analysis including chronotype assessment, energy zones, schedule recommendations, and integration guidelines for routine/behavior agents.
"""
```

#### **Step 1.2: Create Circadian Agent Following Exact Pattern**
Create `services/agents/circadian_energy/main.py`:

```python
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

        # Step 1: Get memory context (placeholder - SAME PATTERN)
        memory_context = await self._get_memory_context(user_id)

        # Step 2: Get user context (SAME PATTERN as behavior agent)
        try:
            await self.supabase.connect()
            user_context = await self._get_user_profile_context(user_id, days=14)  # More days for circadian

            # Step 3: Build enhanced context (SAME PATTERN)
            enhanced_context = {
                "user_context": user_context,
                "archetype": archetype,
                "archetype_guidance": self.get_archetype_guidance(archetype) if archetype else "",
                "system_prompt": self.system_prompt,
                "memory_context": memory_context,
                "analysis_timestamp": datetime.now().isoformat()
            }

            # Step 4: Use external analysis service (SAME PATTERN as behavior agent)
            analysis_result = await self.analysis_agent.analyze(enhanced_context)

            # Step 5: Store analysis results in memory (SAME PATTERN)
            await self._store_analysis_in_memory(user_id, archetype, analysis_result)

            # Step 6: Log input/output (SAME PATTERN)
            analysis_number = payload.get("analysis_number", 1)
            self.log_input_output(enhanced_context, analysis_result, analysis_number)

            # Step 7: Publish completion event (SAME PATTERN)
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

    # Memory Integration Methods (SAME PATTERN as behavior agent - placeholders)

    async def _get_memory_context(self, user_id: str) -> dict:
        """Retrieve circadian memory context - PLACEHOLDER"""
        try:
            # TODO: Same as behavior agent - placeholder for memory integration
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
        """Store circadian analysis results in memory - PLACEHOLDER"""
        try:
            # TODO: Implement actual memory storage - same pattern as behavior agent
            self.logger.debug(f"Stored circadian analysis in memory for {user_id}")

        except Exception as e:
            self.logger.error(f"Error storing analysis in memory: {e}")

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

async def main():
    """Main entry point - SAME PATTERN as other agents"""
    agent = HolisticCircadianEnergyAgent()

    try:
        await agent.start_listening()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error running circadian-energy agent: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

### **Phase 2: Standalone API Endpoint (Week 1, Days 3-4)**

#### **Step 2.1: Add API Endpoint Following Behavior Pattern**
Add to `services/api_gateway/openai_main.py` (EXACT SAME PATTERN as behavior endpoint):

```python
@app.post("/api/user/{user_id}/circadian/analyze", response_model=CircadianAnalysisResponse)
@track_endpoint_metrics("circadian_analysis") if MONITORING_AVAILABLE else lambda x: x
async def analyze_circadian_patterns(user_id: str, request: CircadianAnalysisRequest, http_request: Request):
    """
    Standalone circadian rhythm analysis endpoint
    FOLLOWS EXACT SAME PATTERN as /api/user/{user_id}/behavior/analyze
    """
    # EXACT SAME rate limiting pattern
    if RATE_LIMITING_AVAILABLE:
        try:
            await rate_limiter.apply_rate_limit(http_request, "circadian_analysis")
        except Exception as rate_limit_error:
            print(f"⚠️ [RATE_LIMIT] Rate limit exceeded for user {user_id}: {rate_limit_error}")
            raise rate_limit_error

    try:
        print(f"🌙 [CIRCADIAN_ANALYZE] Starting circadian analysis for user {user_id[:8]}...")

        # EXACT SAME service imports
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        from services.mvp_style_logger import mvp_logger

        # EXACT SAME service initialization
        ondemand_service = await get_ondemand_service()
        memory_service = HolisticMemoryService()

        # EXACT SAME MVP logging preparation
        analysis_number = mvp_logger.get_next_analysis_number()
        input_data = {
            "user_id": user_id,
            "archetype": request.archetype or "Foundation Builder",
            "endpoint": "/api/user/{user_id}/circadian/analyze",
            "request_timestamp": datetime.now().isoformat(),
            "analysis_number": analysis_number,
            "request_data": {
                "archetype": request.archetype,
                "force_refresh": request.force_refresh
            }
        }

        # EXACT SAME 50-item threshold check
        decision, metadata = await ondemand_service.should_run_analysis(user_id, request.force_refresh, request.archetype)

        circadian_analysis = None
        analysis_type = "unknown"

        if decision == AnalysisDecision.FRESH_ANALYSIS or decision == AnalysisDecision.STALE_FORCE_REFRESH:
            print(f"🚀 [CIRCADIAN_ANALYZE] Running fresh circadian analysis...")

            # EXACT SAME pattern for getting health data
            archetype = request.archetype or "Foundation Builder"

            from services.user_data_service import UserDataService
            user_data_service = UserDataService()
            health_data = await user_data_service.get_user_health_data(user_id, analysis_number)

            # EXACT SAME MVP logging
            mvp_logger.log_raw_health_data(user_id, health_data, analysis_number)

            # Use circadian agent (SAME PATTERN as behavior agent)
            circadian_agent = HolisticCircadianEnergyAgent()

            # Create analysis context (SAME PATTERN)
            analysis_context = {
                "user_context": health_data,
                "archetype": archetype,
                "memory_context": {},
                "analysis_number": analysis_number,
                "analysis_timestamp": datetime.now().isoformat()
            }

            # Run analysis using external service (SAME PATTERN)
            circadian_result = await circadian_agent.analysis_agent.analyze(analysis_context)

            # EXACT SAME MVP logging
            mvp_logger.log_ai_interaction(
                agent_name="circadian_energy_agent",
                input_data=analysis_context,
                output_data=circadian_result,
                analysis_number=analysis_number,
                model_used="gpt-4o"
            )

            # EXACT SAME database storage
            analysis_id = await memory_service.store_analysis_result(
                user_id=user_id,
                analysis_type="circadian_energy",
                analysis_result=circadian_result,
                archetype_used=archetype,
                analysis_trigger="api_request"
            )

            circadian_analysis = circadian_result
            analysis_type = "fresh"

        else:
            # EXACT SAME cached analysis pattern
            print(f"📋 [CIRCADIAN_ANALYZE] Using cached circadian analysis...")

            recent_analysis = await memory_service.get_analysis_history(
                user_id=user_id,
                analysis_type="circadian_energy",
                archetype=request.archetype,
                limit=1
            )

            if recent_analysis:
                circadian_analysis = recent_analysis[0].analysis_result
                analysis_type = "cached"
            else:
                # EXACT SAME fallback pattern
                circadian_analysis = {"error": "No cached analysis available"}
                analysis_type = "fallback"

        # EXACT SAME complete analysis logging
        mvp_logger.log_complete_analysis(
            user_id=user_id,
            analysis_type="circadian_energy",
            input_summary=input_data,
            output_summary=circadian_analysis,
            analysis_number=analysis_number,
            success=True
        )

        print(f"✅ [CIRCADIAN_ANALYZE] Circadian analysis completed for user {user_id[:8]}")

        return CircadianAnalysisResponse(
            user_id=user_id,
            analysis_type=analysis_type,
            circadian_analysis=circadian_analysis,
            analysis_metadata={
                "analysis_number": analysis_number,
                "decision": decision.value if hasattr(decision, 'value') else str(decision),
                "threshold_metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        print(f"❌ [CIRCADIAN_ANALYZE_ERROR] Failed: {e}")
        raise HTTPException(status_code=500, detail=f"Circadian analysis failed: {str(e)}")
```

### **Phase 3: Integration with Routine Agent (Week 1, Days 5-7)**

#### **Step 3.1: Enhance Routine Agent to Use Circadian Data**
Modify `services/agents/routine/main.py` to consume circadian analysis:

```python
# Add to routine agent's analysis request handler

async def _handle_analysis_request(self, event: AgentEvent):
    # EXISTING: Get behavior analysis
    behavior_context = await self._get_behavior_context(user_id, archetype)

    # NEW: Get circadian analysis if available
    circadian_context = await self._get_circadian_context(user_id, archetype)

    # ENHANCED: Build context with both behavior and circadian
    enhanced_context = {
        "behavior_analysis": behavior_context,
        "circadian_analysis": circadian_context,  # NEW
        "user_context": user_context,
        "archetype": archetype,
        "memory_context": memory_context
    }

    # Use enhanced context for routine generation
    routine_result = await self.routine_service.generate_routine(enhanced_context)

async def _get_circadian_context(self, user_id: str, archetype: str) -> Dict:
    """Get circadian analysis context for routine optimization"""
    try:
        # Get recent circadian analysis from memory
        memory_service = HolisticMemoryService()
        recent_analyses = await memory_service.get_analysis_history(
            user_id=user_id,
            analysis_type="circadian_energy",
            archetype=archetype,
            limit=1
        )

        if recent_analyses:
            return recent_analyses[0].analysis_result
        else:
            return {}

    except Exception as e:
        self.logger.error(f"Error getting circadian context: {e}")
        return {}
```

## Key Benefits of This Approach

### **1. AI-Powered Analysis**
- **GPT-4o** analyzes complex biomarker patterns intelligently
- **No manual if-then loops** - AI handles pattern recognition
- **Contextual recommendations** based on actual data patterns

### **2. Perfect Pattern Consistency**
- **Exact same structure** as behavior/routine agents
- **External analysis service** pattern maintained
- **Same memory placeholders** ready for integration
- **Same logging, error handling, event publishing**

### **3. Non-Disruptive Integration**
- **No changes to existing agents** initially
- **Standalone endpoint** for testing
- **Optional enhancement** to routine agent
- **Same database tables** and memory patterns

### **4. Future-Ready Architecture**
- **Memory integration points** already established
- **Event system** ready for agent-to-agent communication
- **Integration hooks** for behavior/routine agents
- **Logging system** captures all data flows

## Implementation Timeline

### **Week 1: Core Implementation**
- **Day 1-2**: Create `CircadianAnalysisService` and `HolisticCircadianEnergyAgent`
- **Day 3-4**: Add standalone API endpoint with full logging
- **Day 5-7**: Test, validate, and prepare routine agent integration

### **Week 2: Testing & Integration**
- **Day 1-3**: Comprehensive testing of AI analysis
- **Day 4-5**: Routine agent integration and end-to-end testing

This approach gives you **intelligent AI-powered circadian analysis** while following **exact existing patterns** for seamless integration.