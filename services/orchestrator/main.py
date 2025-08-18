"""
HolisticOS Multi-Agent Orchestrator Service
Coordinates the complete workflow between all 5 agents:
Behavior Analysis → Memory Storage → Insights Generation → Strategy Adaptation → Continuous Learning
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from shared_libs.event_system.base_agent import BaseAgent, AgentEvent, AgentResponse
from shared_libs.utils.system_prompts import get_system_prompt

# Import all agent classes for direct method calls (Option A implementation)
from services.agents.memory.main import HolisticMemoryAgent
from services.agents.insights.main import HolisticInsightsAgent
from services.agents.adaptation.main import HolisticAdaptationEngine
# Note: Behavior, Nutrition, and Routine agents would need to be imported if they existed
# For now, we'll create placeholder responses for them

class WorkflowStage(Enum):
    """Stages of the complete analysis workflow"""
    STARTED = "started"
    BEHAVIOR_ANALYSIS = "behavior_analysis"
    MEMORY_STORAGE = "memory_storage" 
    PLAN_GENERATION = "plan_generation"
    INSIGHTS_GENERATION = "insights_generation"
    STRATEGY_ADAPTATION = "strategy_adaptation"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowState:
    """Track state of a complete analysis workflow"""
    def __init__(self, user_id: str, archetype: str, workflow_id: str):
        self.user_id = user_id
        self.archetype = archetype
        self.workflow_id = workflow_id
        self.current_stage = WorkflowStage.STARTED
        self.start_time = datetime.now()
        self.completed_stages = []
        self.results = {}
        self.errors = []

class HolisticOrchestrator(BaseAgent):
    """
    HolisticOS Multi-Agent Orchestrator
    
    Coordinates complete analysis workflows across all 5 agents:
    1. Behavior Analysis Agent - Analyzes user behavioral patterns
    2. Memory Management Agent - Stores and retrieves user context
    3. Plan Generation Agents - Creates nutrition and routine plans  
    4. Insights Generation Agent - Generates AI-powered insights
    5. Adaptation Engine Agent - Adapts strategies based on feedback
    """
    
    def __init__(self, redis_url: str = None):
        super().__init__(
            agent_id="holistic_orchestrator",
            agent_type="orchestrator",
            redis_url=redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        )
        
        # Track active workflow states
        self.workflow_states: Dict[str, WorkflowState] = {}
        
        # Configure agent coordination
        self.coordinated_agents = [
            "behavior_analysis_agent",
            "memory_management_agent", 
            "nutrition_plan_agent",
            "routine_plan_agent",
            "insights_generation_agent",
            "adaptation_engine_agent"
        ]
        
        # Workflow configuration
        self.workflow_timeout_minutes = 30
        self.parallel_plan_generation = True  # Run nutrition + routine in parallel
        self.auto_insights_generation = True  # Auto-trigger insights after plans
        self.auto_adaptation_monitoring = True  # Auto-monitor for adaptation needs
        
        # Initialize agents directly (Option A implementation)
        try:
            self.memory_agent = HolisticMemoryAgent()
            self.insights_agent = HolisticInsightsAgent()
            self.adaptation_agent = HolisticAdaptationEngine()
            
            # Placeholder agents for behavior, nutrition, and routine
            # These would be real agents if they existed in the system
            self.behavior_agent = None
            self.nutrition_agent = None
            self.routine_agent = None
            
            self.logger.debug("Direct agent instances created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent instances: {e}")
            # Continue without agent instances - will use placeholders
            self.memory_agent = None
            self.insights_agent = None
            self.adaptation_agent = None
            self.behavior_agent = None
            self.nutrition_agent = None
            self.routine_agent = None
        
        self.logger.debug(f"HolisticOS Multi-Agent Orchestrator initialized with {len(self.coordinated_agents)} agents")
    
    async def call_agent_directly(self, event_type: str, payload: Dict[str, Any], 
                                 target_agent: str, user_id: str, archetype: str = None) -> Optional[AgentResponse]:
        """
        Direct agent method calls (Option A implementation)
        Replaces Redis pub/sub with direct agent.process() calls
        """
        try:
            # Create event for the target agent
            agent_event = AgentEvent(
                event_id=f"direct_{datetime.now().timestamp()}",
                event_type=event_type,
                source_agent=self.agent_id,
                payload=payload,
                timestamp=datetime.now(),
                user_id=user_id,
                archetype=archetype
            )
            
            # Route to appropriate agent
            if target_agent == "memory_management_agent" and self.memory_agent:
                return await self.memory_agent.process(agent_event)
            elif target_agent == "insights_generation_agent" and self.insights_agent:
                return await self.insights_agent.process(agent_event)
            elif target_agent == "adaptation_engine_agent" and self.adaptation_agent:
                return await self.adaptation_agent.process(agent_event)
            elif target_agent == "behavior_analysis_agent":
                # Placeholder for behavior analysis agent
                return await self._placeholder_behavior_analysis(agent_event)
            elif target_agent == "nutrition_plan_agent":
                # Placeholder for nutrition plan agent
                return await self._placeholder_nutrition_plan(agent_event)
            elif target_agent == "routine_plan_agent":
                # Placeholder for routine plan agent
                return await self._placeholder_routine_plan(agent_event)
            else:
                self.logger.warning(f"Unknown target agent: {target_agent}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in direct agent call: {e}")
            return None
    
    def get_supported_event_types(self) -> List[str]:
        """Events this orchestrator responds to"""
        return [
            # Workflow initiation
            "start_analysis",
            "start_complete_workflow",
            
            # Agent completion events
            "behavior_analysis_complete",
            "memory_consolidation_complete",
            "nutrition_plan_complete",
            "routine_plan_complete", 
            "insights_generation_complete",
            "adaptation_complete",
            
            # Workflow coordination
            "workflow_status_request",
            "workflow_timeout",
            "workflow_error",
            
            # Legacy support
            "nutrition_plan_completed",
            "routine_plan_completed",
            "plan_generation_complete",
            "memory_update_complete"
        ]
    
    async def process(self, event: AgentEvent) -> AgentResponse:
        """Process multi-agent workflow coordination events"""
        try:
            self.logger.info("Orchestrating multi-agent event",
                           event_type=event.event_type,
                           user_id=event.user_id,
                           archetype=event.archetype)
            
            # Workflow initiation events
            if event.event_type in ["start_analysis", "start_complete_workflow"]:
                return await self._start_complete_workflow(event)
            
            # Agent completion events - handle the complete workflow progression
            elif event.event_type == "behavior_analysis_complete":
                return await self._handle_behavior_analysis_complete(event)
            elif event.event_type == "memory_consolidation_complete":
                return await self._handle_memory_consolidation_complete(event)
            elif event.event_type in ["nutrition_plan_complete", "nutrition_plan_completed"]:
                return await self._handle_nutrition_plan_complete(event)
            elif event.event_type in ["routine_plan_complete", "routine_plan_completed"]:
                return await self._handle_routine_plan_complete(event)
            elif event.event_type == "insights_generation_complete":
                return await self._handle_insights_generation_complete(event)
            elif event.event_type == "adaptation_complete":
                return await self._handle_adaptation_complete(event)
            
            # Workflow management events
            elif event.event_type == "workflow_status_request":
                return await self._handle_workflow_status_request(event)
            elif event.event_type == "workflow_timeout":
                return await self._handle_workflow_timeout(event)
            elif event.event_type == "workflow_error":
                return await self._handle_workflow_error(event)
            
            # Legacy support
            elif event.event_type == "plan_generation_complete":
                return await self._handle_legacy_plan_complete(event)
            
            # Acknowledgment for other events
            else:
                return AgentResponse(
                    response_id=f"orchestrator_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    success=True,
                    result={"message": f"Event {event.event_type} acknowledged by orchestrator"},
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self.logger.error("Multi-agent orchestration error", error=str(e))
            return AgentResponse(
                response_id=f"orchestrator_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    # =============================================================================
    # COMPLETE MULTI-AGENT WORKFLOW METHODS
    # =============================================================================
    
    async def _start_complete_workflow(self, event: AgentEvent) -> AgentResponse:
        """Start the complete multi-agent analysis workflow"""
        user_id = event.user_id
        archetype = event.archetype
        workflow_id = f"{user_id}_{datetime.now().timestamp()}"
        
        # Create workflow state tracking
        workflow_state = WorkflowState(user_id, archetype, workflow_id)
        self.workflow_states[workflow_id] = workflow_state
        
        self.logger.debug("Starting complete multi-agent workflow",
                        workflow_id=workflow_id,
                        user_id=user_id,
                        archetype=archetype,
                        coordinated_agents=len(self.coordinated_agents))
        
        # Stage 1: Start with Memory Context Retrieval
        workflow_state.current_stage = WorkflowStage.MEMORY_STORAGE
        await self.call_agent_directly(
            event_type="memory_retrieve",
            payload={
                "workflow_id": workflow_id,
                "memory_type": "all",
                "query_context": "analysis_preparation"
            },
            target_agent="memory_management_agent",
            user_id=user_id,
            archetype=archetype
        )
        
        # Stage 2: Simultaneously start Behavior Analysis with memory context
        workflow_state.current_stage = WorkflowStage.BEHAVIOR_ANALYSIS
        behavior_response = await self.call_agent_directly(
            event_type="analysis_request",
            payload={
                "workflow_id": workflow_id,
                "analysis_number": event.payload.get("analysis_number", 1),
                "include_memory_context": True
            },
            target_agent="behavior_analysis_agent",
            user_id=user_id,
            archetype=archetype
        )
        
        # Process behavior analysis result directly
        if behavior_response and behavior_response.success:
            behavior_complete_event = AgentEvent(
                event_id=f"auto_behavior_complete_{datetime.now().timestamp()}",
                event_type="behavior_analysis_complete",
                source_agent="behavior_analysis_agent",
                payload={
                    "workflow_id": workflow_id,
                    "analysis_result": behavior_response.result.get("analysis_result", {})
                },
                timestamp=datetime.now(),
                user_id=user_id,
                archetype=archetype
            )
            # Continue workflow automatically
            await self.process(behavior_complete_event)
        
        return AgentResponse(
            response_id=f"orchestrator_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={
                "workflow_id": workflow_id,
                "status": "started",
                "current_stage": workflow_state.current_stage.value,
                "coordinated_agents": self.coordinated_agents,
                "next_stages": ["memory_retrieval", "behavior_analysis"]
            },
            timestamp=datetime.now()
        )
    
    async def _handle_behavior_analysis_complete(self, event: AgentEvent) -> AgentResponse:
        """Handle behavior analysis completion and progress workflow"""
        user_id = event.user_id
        archetype = event.archetype
        analysis_result = event.payload.get("analysis_result", {})
        workflow_id = event.payload.get("workflow_id")
        
        # Find and update workflow state
        workflow_state = self._find_workflow_by_user(user_id) if not workflow_id else self.workflow_states.get(workflow_id)
        if workflow_state:
            workflow_state.current_stage = WorkflowStage.PLAN_GENERATION
            workflow_state.completed_stages.append(WorkflowStage.BEHAVIOR_ANALYSIS)
            workflow_state.results["behavior_analysis"] = analysis_result
        
        self.logger.info("Behavior analysis complete - progressing to plan generation",
                        user_id=user_id,
                        archetype=archetype,
                        workflow_id=workflow_id)
        
        # Store behavior analysis results in memory
        await self.call_agent_directly(
            event_type="memory_store",
            payload={
                "workflow_id": workflow_id,
                "memory_type": "shortterm",
                "category": "behavior_analysis_results",
                "data": analysis_result,
                "confidence": 0.8
            },
            target_agent="memory_management_agent",
            user_id=user_id,
            archetype=archetype
        )
        
        # Stage 3: Parallel plan generation (nutrition + routine)
        if self.parallel_plan_generation:
            # Launch both plan generations simultaneously
            nutrition_response, routine_response = await asyncio.gather(
                self.call_agent_directly(
                    event_type="nutrition_plan_request",
                    payload={
                        "workflow_id": workflow_id,
                        "behavior_analysis": analysis_result,
                        "memory_context": True
                    },
                    target_agent="nutrition_plan_agent",
                    user_id=user_id,
                    archetype=archetype
                ),
                self.call_agent_directly(
                    event_type="routine_plan_request", 
                    payload={
                        "workflow_id": workflow_id,
                        "behavior_analysis": analysis_result,
                        "memory_context": True
                    },
                    target_agent="routine_plan_agent",
                    user_id=user_id,
                    archetype=archetype
                )
            )
            
            # Process plan completion results directly
            if nutrition_response and nutrition_response.success:
                nutrition_complete_event = AgentEvent(
                    event_id=f"auto_nutrition_complete_{datetime.now().timestamp()}",
                    event_type="nutrition_plan_complete",
                    source_agent="nutrition_plan_agent",
                    payload={
                        "workflow_id": workflow_id,
                        "nutrition_plan": nutrition_response.result.get("nutrition_plan", {})
                    },
                    timestamp=datetime.now(),
                    user_id=user_id,
                    archetype=archetype
                )
                await self.process(nutrition_complete_event)
            
            if routine_response and routine_response.success:
                routine_complete_event = AgentEvent(
                    event_id=f"auto_routine_complete_{datetime.now().timestamp()}",
                    event_type="routine_plan_complete",
                    source_agent="routine_plan_agent",
                    payload={
                        "workflow_id": workflow_id,
                        "routine_plan": routine_response.result.get("routine_plan", {})
                    },
                    timestamp=datetime.now(),
                    user_id=user_id,
                    archetype=archetype
                )
                await self.process(routine_complete_event)
        
        return AgentResponse(
            response_id=f"orchestrator_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={
                "workflow_id": workflow_id,
                "status": "behavior_analysis_complete",
                "current_stage": WorkflowStage.PLAN_GENERATION.value,
                "next_stages": ["nutrition_planning", "routine_planning"],
                "parallel_execution": self.parallel_plan_generation
            },
            timestamp=datetime.now()
        )
    
    # Import all the new multi-agent workflow methods
    async def _handle_memory_consolidation_complete(self, event: AgentEvent) -> AgentResponse:
        """Handle memory consolidation completion"""
        user_id = event.user_id
        workflow_id = event.payload.get("workflow_id")
        consolidation_results = event.payload.get("consolidation_results", {})
        
        workflow_state = self._find_workflow_by_user(user_id)
        if workflow_state:
            workflow_state.results["memory_consolidation"] = consolidation_results
        
        self.logger.info("Memory consolidation complete",
                        user_id=user_id,
                        workflow_id=workflow_id)
        
        return AgentResponse(
            response_id=f"orchestrator_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={"status": "memory_consolidation_complete", "workflow_id": workflow_id},
            timestamp=datetime.now()
        )
    
    async def _handle_nutrition_plan_complete(self, event: AgentEvent) -> AgentResponse:
        """Handle nutrition plan completion and check for workflow progression"""
        user_id = event.user_id
        archetype = event.archetype
        nutrition_plan = event.payload.get("nutrition_plan", {})
        workflow_id = event.payload.get("workflow_id")
        
        workflow_state = self._find_workflow_by_user(user_id)
        if workflow_state:
            workflow_state.results["nutrition_plan"] = nutrition_plan
            
            # Check if both plans are complete to trigger insights
            if "routine_plan" in workflow_state.results and self.auto_insights_generation:
                return await self._trigger_insights_generation(workflow_state, archetype)
        
        self.logger.info("Nutrition plan complete",
                        user_id=user_id,
                        workflow_id=workflow_id)
        
        return AgentResponse(
            response_id=f"orchestrator_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={
                "status": "nutrition_plan_complete",
                "workflow_id": workflow_id,
                "awaiting_routine_plan": "routine_plan" not in workflow_state.results if workflow_state else True
            },
            timestamp=datetime.now()
        )
    
    async def _handle_routine_plan_complete(self, event: AgentEvent) -> AgentResponse:
        """Handle routine plan completion and check for workflow progression"""
        user_id = event.user_id
        archetype = event.archetype
        routine_plan = event.payload.get("routine_plan", {})
        workflow_id = event.payload.get("workflow_id")
        
        workflow_state = self._find_workflow_by_user(user_id)
        if workflow_state:
            workflow_state.results["routine_plan"] = routine_plan
            
            # Check if both plans are complete to trigger insights
            if "nutrition_plan" in workflow_state.results and self.auto_insights_generation:
                return await self._trigger_insights_generation(workflow_state, archetype)
        
        self.logger.info("Routine plan complete",
                        user_id=user_id,
                        workflow_id=workflow_id)
        
        return AgentResponse(
            response_id=f"orchestrator_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={
                "status": "routine_plan_complete", 
                "workflow_id": workflow_id,
                "awaiting_nutrition_plan": "nutrition_plan" not in workflow_state.results if workflow_state else True
            },
            timestamp=datetime.now()
        )
    
    async def _handle_insights_generation_complete(self, event: AgentEvent) -> AgentResponse:
        """Handle insights generation completion and trigger adaptation monitoring"""
        user_id = event.user_id
        archetype = event.archetype
        insights_result = event.payload.get("insights", {})
        workflow_id = event.payload.get("workflow_id")
        
        workflow_state = self._find_workflow_by_user(user_id)
        if workflow_state:
            workflow_state.current_stage = WorkflowStage.STRATEGY_ADAPTATION
            workflow_state.completed_stages.append(WorkflowStage.INSIGHTS_GENERATION)
            workflow_state.results["insights"] = insights_result
            
            # Trigger adaptation monitoring if enabled
            if self.auto_adaptation_monitoring:
                adaptation_response = await self.call_agent_directly(
                    event_type="monitor_effectiveness",
                    payload={
                        "workflow_id": workflow_id,
                        "monitoring_data": {
                            "behavior_analysis": workflow_state.results.get("behavior_analysis", {}),
                            "insights": insights_result,
                            "user_context": {"archetype": archetype}
                        }
                    },
                    target_agent="adaptation_engine_agent",
                    user_id=user_id,
                    archetype=archetype
                )
                
                # Process adaptation result directly
                if adaptation_response and adaptation_response.success:
                    adaptation_complete_event = AgentEvent(
                        event_id=f"auto_adaptation_complete_{datetime.now().timestamp()}",
                        event_type="adaptation_complete",
                        source_agent="adaptation_engine_agent",
                        payload={
                            "workflow_id": workflow_id,
                            "adaptation_result": adaptation_response.result.get("adaptation_result", {})
                        },
                        timestamp=datetime.now(),
                        user_id=user_id,
                        archetype=archetype
                    )
                    await self.process(adaptation_complete_event)
        
        self.logger.info("Insights generation complete - triggering adaptation monitoring",
                        user_id=user_id,
                        workflow_id=workflow_id)
        
        return AgentResponse(
            response_id=f"orchestrator_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={
                "status": "insights_generation_complete",
                "workflow_id": workflow_id,
                "current_stage": WorkflowStage.STRATEGY_ADAPTATION.value,
                "adaptation_monitoring_triggered": self.auto_adaptation_monitoring
            },
            timestamp=datetime.now()
        )
    
    async def _handle_adaptation_complete(self, event: AgentEvent) -> AgentResponse:
        """Handle adaptation completion and finalize workflow"""
        user_id = event.user_id
        adaptation_result = event.payload.get("adaptation_result", {})
        workflow_id = event.payload.get("workflow_id")
        
        workflow_state = self._find_workflow_by_user(user_id)
        if workflow_state:
            workflow_state.current_stage = WorkflowStage.COMPLETED
            workflow_state.completed_stages.append(WorkflowStage.STRATEGY_ADAPTATION)
            workflow_state.results["adaptation"] = adaptation_result
            
            # Store complete workflow results in memory
            await self.call_agent_directly(
                event_type="memory_store",
                payload={
                    "workflow_id": workflow_id,
                    "memory_type": "longterm",
                    "category": "complete_analysis_workflow",
                    "data": {
                        "workflow_results": workflow_state.results,
                        "completion_time": datetime.now().isoformat(),
                        "success": True
                    },
                    "confidence": 0.9
                },
                target_agent="memory_management_agent",
                user_id=user_id,
                archetype=event.archetype
            )
        
        self.logger.info("Complete workflow finished successfully",
                        user_id=user_id,
                        workflow_id=workflow_id,
                        stages_completed=len(workflow_state.completed_stages) if workflow_state else 0)
        
        return AgentResponse(
            response_id=f"orchestrator_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={
                "status": "complete_workflow_finished",
                "workflow_id": workflow_id,
                "stages_completed": workflow_state.completed_stages if workflow_state else [],
                "final_results": workflow_state.results if workflow_state else {}
            },
            timestamp=datetime.now()
        )
    
    # =============================================================================
    # PLACEHOLDER AGENT METHODS (for agents that don't exist yet)
    # =============================================================================
    
    async def _placeholder_behavior_analysis(self, event: AgentEvent) -> AgentResponse:
        """Placeholder for behavior analysis agent - simulates behavior analysis"""
        await asyncio.sleep(1)  # Simulate processing time
        
        return AgentResponse(
            response_id=f"behavior_placeholder_{datetime.now().timestamp()}",
            agent_id="behavior_analysis_agent",
            success=True,
            result={
                "analysis_result": {
                    "behavioral_signature": {
                        "primary_motivation": "performance_optimization",
                        "consistency_score": 0.82,
                        "signature": f"Generated analysis for {event.archetype} user"
                    },
                    "sophistication_assessment": {
                        "score": 78,
                        "category": "Advanced",
                        "level": "high_intermediate"
                    },
                    "readiness_level": "high",
                    "primary_goal": {
                        "category": "performance",
                        "specific_target": f"{event.archetype.lower()}_optimization"
                    },
                    "personalized_strategy": {
                        "motivation_drivers": ["achievement", "progress_tracking"],
                        "habit_integration": "structured_approach",
                        "barrier_mitigation": "systematic_problem_solving"
                    }
                },
                "workflow_id": event.payload.get("workflow_id"),
                "placeholder": True
            },
            timestamp=datetime.now()
        )
    
    async def _placeholder_nutrition_plan(self, event: AgentEvent) -> AgentResponse:
        """Placeholder for nutrition plan agent - simulates nutrition planning"""
        await asyncio.sleep(1.5)  # Simulate processing time
        
        return AgentResponse(
            response_id=f"nutrition_placeholder_{datetime.now().timestamp()}",
            agent_id="nutrition_plan_agent",
            success=True,
            result={
                "nutrition_plan": {
                    "daily_calories": 2400,
                    "macros": {"protein": "30%", "carbs": "40%", "fats": "30%"},
                    "meals": {
                        "breakfast": f"High protein breakfast for {event.archetype}",
                        "lunch": f"Balanced macro lunch for {event.archetype}",
                        "dinner": f"Recovery-focused dinner for {event.archetype}"
                    },
                    "supplements": ["whey_protein", "multivitamin", "omega_3"],
                    "archetype_specific": f"Optimized for {event.archetype} goals"
                },
                "workflow_id": event.payload.get("workflow_id"),
                "placeholder": True
            },
            timestamp=datetime.now()
        )
    
    async def _placeholder_routine_plan(self, event: AgentEvent) -> AgentResponse:
        """Placeholder for routine plan agent - simulates routine planning"""
        await asyncio.sleep(1.5)  # Simulate processing time
        
        return AgentResponse(
            response_id=f"routine_placeholder_{datetime.now().timestamp()}",
            agent_id="routine_plan_agent",
            success=True,
            result={
                "routine_plan": {
                    "workout_schedule": "6_days_per_week",
                    "focus_areas": ["strength", "endurance", "recovery"],
                    "daily_structure": {
                        "morning": f"Morning routine for {event.archetype}",
                        "afternoon": f"Afternoon activities for {event.archetype}",
                        "evening": f"Evening recovery for {event.archetype}"
                    },
                    "progression": "progressive_overload_weekly",
                    "archetype_specific": f"Designed for {event.archetype} approach"
                },
                "workflow_id": event.payload.get("workflow_id"),
                "placeholder": True
            },
            timestamp=datetime.now()
        )

    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    async def _trigger_insights_generation(self, workflow_state: WorkflowState, archetype: str) -> AgentResponse:
        """Trigger insights generation when both plans are complete"""
        workflow_state.current_stage = WorkflowStage.INSIGHTS_GENERATION
        workflow_state.completed_stages.append(WorkflowStage.PLAN_GENERATION)
        
        # Gather all data for insights
        insights_context = {
            "behavior_analysis": workflow_state.results.get("behavior_analysis", {}),
            "nutrition_plan": workflow_state.results.get("nutrition_plan", {}),
            "routine_plan": workflow_state.results.get("routine_plan", {}),
            "memory_context": workflow_state.results.get("memory_consolidation", {})
        }
        
        insights_response = await self.call_agent_directly(
            event_type="generate_insights",
            payload={
                "workflow_id": workflow_state.workflow_id,
                "insight_type": "comprehensive",
                "time_horizon": "medium_term",
                "context_data": insights_context
            },
            target_agent="insights_generation_agent",
            user_id=workflow_state.user_id,
            archetype=archetype
        )
        
        # Process insights generation result directly
        if insights_response and insights_response.success:
            insights_complete_event = AgentEvent(
                event_id=f"auto_insights_complete_{datetime.now().timestamp()}",
                event_type="insights_generation_complete",
                source_agent="insights_generation_agent",
                payload={
                    "workflow_id": workflow_state.workflow_id,
                    "insights": insights_response.result.get("insights", {})
                },
                timestamp=datetime.now(),
                user_id=workflow_state.user_id,
                archetype=archetype
            )
            await self.process(insights_complete_event)
        
        self.logger.info("Triggered insights generation after plan completion",
                        user_id=workflow_state.user_id,
                        workflow_id=workflow_state.workflow_id)
        
        return AgentResponse(
            response_id=f"orchestrator_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={
                "status": "plans_complete_insights_triggered",
                "workflow_id": workflow_state.workflow_id,
                "current_stage": WorkflowStage.INSIGHTS_GENERATION.value
            },
            timestamp=datetime.now()
        )
    
    def _find_workflow_by_user(self, user_id: str) -> Optional[WorkflowState]:
        """Find active workflow for user"""
        for workflow_state in self.workflow_states.values():
            if (workflow_state.user_id == user_id and 
                workflow_state.current_stage != WorkflowStage.COMPLETED):
                return workflow_state
        return None
    
    async def _handle_workflow_status_request(self, event: AgentEvent) -> AgentResponse:
        """Handle workflow status requests"""
        user_id = event.user_id
        workflow_id = event.payload.get("workflow_id")
        
        if workflow_id and workflow_id in self.workflow_states:
            workflow_state = self.workflow_states[workflow_id]
        else:
            workflow_state = self._find_workflow_by_user(user_id)
        
        if workflow_state:
            return AgentResponse(
                response_id=f"orchestrator_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result={
                    "workflow_id": workflow_state.workflow_id,
                    "user_id": workflow_state.user_id,
                    "current_stage": workflow_state.current_stage.value,
                    "completed_stages": [stage.value for stage in workflow_state.completed_stages],
                    "start_time": workflow_state.start_time.isoformat(),
                    "results_available": list(workflow_state.results.keys())
                },
                timestamp=datetime.now()
            )
        else:
            return AgentResponse(
                response_id=f"orchestrator_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=f"No active workflow found for user {user_id}",
                timestamp=datetime.now()
            )
    
    async def _handle_workflow_timeout(self, event: AgentEvent) -> AgentResponse:
        """Handle workflow timeout"""
        workflow_id = event.payload.get("workflow_id")
        workflow_state = self.workflow_states.get(workflow_id)
        
        if workflow_state:
            workflow_state.current_stage = WorkflowStage.FAILED
            workflow_state.errors.append("Workflow timeout exceeded")
        
        return AgentResponse(
            response_id=f"orchestrator_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={"status": "workflow_timeout", "workflow_id": workflow_id},
            timestamp=datetime.now()
        )
    
    async def _handle_workflow_error(self, event: AgentEvent) -> AgentResponse:
        """Handle workflow error"""
        workflow_id = event.payload.get("workflow_id")
        error_message = event.payload.get("error", "Unknown error")
        
        workflow_state = self.workflow_states.get(workflow_id)
        if workflow_state:
            workflow_state.current_stage = WorkflowStage.FAILED
            workflow_state.errors.append(error_message)
        
        return AgentResponse(
            response_id=f"orchestrator_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={"status": "workflow_error", "workflow_id": workflow_id, "error": error_message},
            timestamp=datetime.now()
        )
    
    async def _handle_legacy_plan_complete(self, event: AgentEvent) -> AgentResponse:
        """Handle legacy plan generation completion events"""
        return AgentResponse(
            response_id=f"orchestrator_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            success=True,
            result={"status": "legacy_plan_complete_acknowledged"},
            timestamp=datetime.now()
        )

async def main():
    """Main entry point for orchestrator service"""
    orchestrator = HolisticOrchestrator()
    
    try:
        print(f"Starting HolisticOS Orchestrator...")
        print(f"Agent ID: {orchestrator.agent_id}")
        
        # Start listening for coordination events
        await orchestrator.start_listening()
        
    except KeyboardInterrupt:
        print("Shutting down orchestrator...")
    except Exception as e:
        print(f"Error running orchestrator: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())