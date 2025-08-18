"""
HolisticOS Adaptation Engine Agent
Real-time adaptation of health strategies based on user feedback, progress patterns, and changing circumstances

Key Functions:
1. Strategy Effectiveness Monitoring: Track implementation outcomes and user engagement
2. Adaptive Optimization: Modify strategies based on real-world performance
3. Intervention Timing: Optimize when and how to deliver recommendations
4. Multi-Agent Coordination: Ensure consistent adaptation across all system components
5. User Engagement Management: Maintain motivation through responsive personalization
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel
from enum import Enum

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from shared_libs.event_system.base_agent import BaseAgent, AgentEvent, AgentResponse
from shared_libs.utils.system_prompts import get_system_prompt

logger = logging.getLogger(__name__)

class AdaptationTrigger(Enum):
    """Types of events that trigger adaptation"""
    USER_FEEDBACK = "user_feedback"
    POOR_ADHERENCE = "poor_adherence"  
    GOAL_CHANGE = "goal_change"
    LIFE_CONTEXT_CHANGE = "life_context_change"
    STRATEGY_INEFFECTIVE = "strategy_ineffective"
    ENGAGEMENT_DECLINE = "engagement_decline"
    PROGRESS_PLATEAU = "progress_plateau"
    SCHEDULE_CONFLICT = "schedule_conflict"

class AdaptationStrategy(Enum):
    """Types of adaptation strategies"""
    REDUCE_INTENSITY = "reduce_intensity"
    INCREASE_SUPPORT = "increase_support"
    CHANGE_TIMING = "change_timing"
    MODIFY_APPROACH = "modify_approach" 
    ADD_FLEXIBILITY = "add_flexibility"
    SIMPLIFY_PLAN = "simplify_plan"
    ENHANCE_MOTIVATION = "enhance_motivation"
    ADJUST_EXPECTATIONS = "adjust_expectations"

class AdaptationRequest(BaseModel):
    """Request for strategy adaptation"""
    user_id: str
    trigger: AdaptationTrigger
    context: Dict[str, Any]
    urgency: str = "medium"  # low, medium, high, critical
    affected_areas: List[str] = []  # nutrition, routine, behavior, engagement
    user_feedback: Optional[str] = None

class AdaptationResult(BaseModel):
    """Result of adaptation process"""
    user_id: str
    trigger: AdaptationTrigger
    adaptations_made: List[Dict[str, Any]]
    confidence: float
    expected_impact: str
    monitoring_plan: Dict[str, Any]
    rollback_available: bool
    adapted_at: datetime

class HolisticAdaptationEngine(BaseAgent):
    """
    HolisticOS Adaptation Engine Agent
    
    Provides real-time strategy adaptation based on:
    - User feedback and behavioral patterns
    - Strategy effectiveness monitoring
    - Life context changes and constraints
    - Engagement level fluctuations
    - Multi-agent coordination requirements
    """
    
    def __init__(self, redis_url: str = None):
        super().__init__(
            agent_id="adaptation_engine_agent",
            agent_type="adaptation_engine"
        )
        
        # Adaptation configuration
        self.adaptation_thresholds = {
            "poor_adherence": 0.4,  # Below 40% adherence triggers adaptation
            "engagement_decline": 0.3,  # 30% drop in engagement
            "strategy_ineffective": 0.5,  # Below 50% success rate
            "progress_plateau": 7  # Days without progress
        }
        
        # Strategy effectiveness tracking
        self.effectiveness_history = {}  # user_id -> strategy history
        self.adaptation_history = {}  # user_id -> adaptation history
        
        # Coordination settings
        self.coordination_agents = [
            "behavior_analysis_agent",
            "memory_management_agent", 
            "insights_generation_agent",
            "nutrition_plan_agent",
            "routine_plan_agent"
        ]
        
        logger.debug(f"Initialized HolisticAdaptationEngine with system prompt length: {len(self.system_prompt)}")
    
    def get_supported_event_types(self) -> List[str]:
        """Events this adaptation engine supports"""
        return [
            "adapt_strategy",
            "monitor_effectiveness",
            "user_feedback_received",
            "engagement_declined",
            "adherence_low",
            "progress_stalled",
            "context_changed",
            "strategy_failed",
            "coordination_request",
            # Completion events from other agents
            "behavior_analysis_complete",
            "insights_generation_complete",
            "memory_consolidation_complete",
            "nutrition_plan_complete",
            "routine_plan_complete"
        ]
    
    async def process(self, event: AgentEvent) -> AgentResponse:
        """Process adaptation-related events"""
        try:
            logger.debug("Processing adaptation event",
                       event_type=event.event_type,
                       user_id=event.user_id)
            
            if event.event_type == "adapt_strategy":
                return await self._handle_adapt_strategy(event)
            elif event.event_type == "monitor_effectiveness":
                return await self._handle_monitor_effectiveness(event)
            elif event.event_type == "user_feedback_received":
                return await self._handle_user_feedback(event)
            elif event.event_type in ["engagement_declined", "adherence_low", "progress_stalled"]:
                return await self._handle_performance_trigger(event)
            elif event.event_type in ["context_changed", "strategy_failed"]:
                return await self._handle_context_trigger(event)
            elif event.event_type == "coordination_request":
                return await self._handle_coordination_request(event)
            elif event.event_type.endswith("_complete"):
                return await self._handle_completion_event(event)
            else:
                return AgentResponse(
                    response_id=f"adaptation_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    success=False,
                    error_message=f"Unsupported event type: {event.event_type}",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error("Error processing adaptation event", error=str(e))
            return AgentResponse(
                response_id=f"adaptation_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_adapt_strategy(self, event: AgentEvent) -> AgentResponse:
        """Handle strategy adaptation requests"""
        try:
            user_id = event.user_id
            payload = event.payload
            archetype = event.archetype
            
            # Parse adaptation request
            adaptation_request = AdaptationRequest(
                user_id=user_id,
                trigger=AdaptationTrigger(payload.get("trigger", "strategy_ineffective")),
                context=payload.get("context", {}),
                urgency=payload.get("urgency", "medium"),
                affected_areas=payload.get("affected_areas", []),
                user_feedback=payload.get("user_feedback")
            )
            
            # Step 1: Analyze current situation and need for adaptation
            adaptation_analysis = await self._analyze_adaptation_need(adaptation_request, archetype)
            
            # Step 2: Get insights and memory context
            context_data = await self._gather_adaptation_context(user_id, adaptation_request)
            
            # Step 3: Generate adaptation strategies using AI
            adaptation_strategies = await self._generate_adaptation_strategies(
                adaptation_request, context_data, adaptation_analysis, archetype
            )
            
            # Step 4: Select and implement best adaptation
            selected_adaptation = await self._select_optimal_adaptation(
                user_id, adaptation_strategies, adaptation_analysis
            )
            
            # Step 5: Coordinate adaptation with other agents
            coordination_results = await self._coordinate_adaptation(user_id, selected_adaptation, archetype)
            
            # Step 6: Set up monitoring for adaptation effectiveness
            monitoring_plan = await self._create_adaptation_monitoring(user_id, selected_adaptation)
            
            # Create adaptation result
            adaptation_result = AdaptationResult(
                user_id=user_id,
                trigger=adaptation_request.trigger,
                adaptations_made=selected_adaptation.get("adaptations", []),
                confidence=selected_adaptation.get("confidence", 0.7),
                expected_impact=selected_adaptation.get("expected_impact", "positive"),
                monitoring_plan=monitoring_plan,
                rollback_available=True,
                adapted_at=datetime.now()
            )
            
            # Store adaptation in history for learning
            await self._store_adaptation_history(user_id, adaptation_result)
            
            # Publish adaptation complete event
            await self._publish_adaptation_complete(user_id, adaptation_result, archetype)
            
            return AgentResponse(
                response_id=f"adaptation_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result=adaptation_result.dict(),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in strategy adaptation: {e}")
            return AgentResponse(
                response_id=f"adaptation_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_monitor_effectiveness(self, event: AgentEvent) -> AgentResponse:
        """Monitor strategy effectiveness and trigger adaptations if needed"""
        try:
            user_id = event.user_id
            monitoring_data = event.payload.get("monitoring_data", {})
            
            # Analyze effectiveness metrics
            effectiveness_analysis = await self._analyze_strategy_effectiveness(user_id, monitoring_data)
            
            # Check if adaptation is needed
            adaptation_needed = await self._evaluate_adaptation_triggers(user_id, effectiveness_analysis)
            
            results = {
                "user_id": user_id,
                "effectiveness_analysis": effectiveness_analysis,
                "adaptation_needed": adaptation_needed,
                "recommendations": []
            }
            
            # If adaptation is needed, trigger it
            if adaptation_needed["needed"]:
                adaptation_event = AgentEvent(
                    event_id=f"auto_adaptation_{datetime.now().timestamp()}",
                    event_type="adapt_strategy",
                    source_agent=self.agent_id,
                    payload={
                        "trigger": adaptation_needed["trigger"],
                        "context": adaptation_needed["context"],
                        "urgency": adaptation_needed["urgency"],
                        "affected_areas": adaptation_needed["affected_areas"]
                    },
                    timestamp=datetime.now(),
                    user_id=user_id,
                    archetype=event.archetype
                )
                
                # Process the adaptation
                adaptation_response = await self._handle_adapt_strategy(adaptation_event)
                results["adaptation_triggered"] = adaptation_response.success
                results["adaptation_details"] = adaptation_response.result
            
            return AgentResponse(
                response_id=f"adaptation_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result=results,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error monitoring effectiveness: {e}")
            return AgentResponse(
                response_id=f"adaptation_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_user_feedback(self, event: AgentEvent) -> AgentResponse:
        """Handle user feedback and adapt strategies accordingly"""
        try:
            user_id = event.user_id
            feedback = event.payload.get("feedback", {})
            archetype = event.archetype
            
            # Analyze feedback sentiment and content
            feedback_analysis = await self._analyze_user_feedback(user_id, feedback, archetype)
            
            # Determine if adaptation is needed based on feedback
            if feedback_analysis.get("adaptation_needed", False):
                # Create adaptation request based on feedback
                adaptation_event = AgentEvent(
                    event_id=f"feedback_adaptation_{datetime.now().timestamp()}",
                    event_type="adapt_strategy",
                    source_agent=self.agent_id,
                    payload={
                        "trigger": "user_feedback",
                        "context": feedback_analysis,
                        "urgency": feedback_analysis.get("urgency", "medium"),
                        "user_feedback": feedback.get("text", ""),
                        "affected_areas": feedback_analysis.get("affected_areas", [])
                    },
                    timestamp=datetime.now(),
                    user_id=user_id,
                    archetype=archetype
                )
                
                # Process the adaptation
                return await self._handle_adapt_strategy(adaptation_event)
            else:
                # Store positive feedback for learning
                await self._store_positive_feedback(user_id, feedback_analysis)
                
                return AgentResponse(
                    response_id=f"adaptation_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    success=True,
                    result={"message": "Feedback processed, no adaptation needed", "analysis": feedback_analysis},
                    timestamp=datetime.now()
                )
            
        except Exception as e:
            logger.error(f"Error handling user feedback: {e}")
            return AgentResponse(
                response_id=f"adaptation_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_performance_trigger(self, event: AgentEvent) -> AgentResponse:
        """Handle performance-based adaptation triggers"""
        try:
            user_id = event.user_id
            trigger_type = event.event_type
            performance_data = event.payload
            
            # Map event type to adaptation trigger
            trigger_mapping = {
                "engagement_declined": AdaptationTrigger.ENGAGEMENT_DECLINE,
                "adherence_low": AdaptationTrigger.POOR_ADHERENCE,
                "progress_stalled": AdaptationTrigger.PROGRESS_PLATEAU
            }
            
            adaptation_trigger = trigger_mapping.get(trigger_type, AdaptationTrigger.STRATEGY_INEFFECTIVE)
            
            # Create adaptation request
            adaptation_event = AgentEvent(
                event_id=f"performance_adaptation_{datetime.now().timestamp()}",
                event_type="adapt_strategy",
                source_agent=self.agent_id,
                payload={
                    "trigger": adaptation_trigger.value,
                    "context": performance_data,
                    "urgency": "high" if trigger_type == "adherence_low" else "medium",
                    "affected_areas": performance_data.get("affected_areas", ["behavior", "engagement"])
                },
                timestamp=datetime.now(),
                user_id=user_id,
                archetype=event.archetype
            )
            
            return await self._handle_adapt_strategy(adaptation_event)
            
        except Exception as e:
            logger.error(f"Error handling performance trigger: {e}")
            return AgentResponse(
                response_id=f"adaptation_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_context_trigger(self, event: AgentEvent) -> AgentResponse:
        """Handle context change adaptation triggers"""
        try:
            user_id = event.user_id
            context_change = event.payload
            
            # Determine adaptation trigger
            trigger = (AdaptationTrigger.LIFE_CONTEXT_CHANGE 
                      if event.event_type == "context_changed" 
                      else AdaptationTrigger.STRATEGY_INEFFECTIVE)
            
            # Create adaptation request
            adaptation_event = AgentEvent(
                event_id=f"context_adaptation_{datetime.now().timestamp()}",
                event_type="adapt_strategy",
                source_agent=self.agent_id,
                payload={
                    "trigger": trigger.value,
                    "context": context_change,
                    "urgency": context_change.get("urgency", "medium"),
                    "affected_areas": context_change.get("affected_areas", ["routine", "nutrition"])
                },
                timestamp=datetime.now(),
                user_id=user_id,
                archetype=event.archetype
            )
            
            return await self._handle_adapt_strategy(adaptation_event)
            
        except Exception as e:
            logger.error(f"Error handling context trigger: {e}")
            return AgentResponse(
                response_id=f"adaptation_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_coordination_request(self, event: AgentEvent) -> AgentResponse:
        """Handle coordination requests from other agents"""
        try:
            request_type = event.payload.get("request_type", "sync_adaptation")
            requesting_agent = event.source_agent
            coordination_data = event.payload.get("data", {})
            
            if request_type == "sync_adaptation":
                # Coordinate adaptation across agents
                sync_result = await self._sync_adaptation_across_agents(event.user_id, coordination_data)
                
                return AgentResponse(
                    response_id=f"adaptation_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    success=True,
                    result={"sync_result": sync_result, "requesting_agent": requesting_agent},
                    timestamp=datetime.now()
                )
            else:
                return AgentResponse(
                    response_id=f"adaptation_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    success=False,
                    error_message=f"Unknown coordination request type: {request_type}",
                    timestamp=datetime.now()
                )
            
        except Exception as e:
            logger.error(f"Error handling coordination request: {e}")
            return AgentResponse(
                response_id=f"adaptation_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_completion_event(self, event: AgentEvent) -> AgentResponse:
        """Handle completion events from other agents"""
        try:
            user_id = event.user_id
            agent_type = event.source_agent
            completion_data = event.payload
            
            # Monitor the effectiveness of the completed action
            effectiveness_check = await self._evaluate_completion_effectiveness(
                user_id, agent_type, completion_data
            )
            
            # Store effectiveness data for future adaptations
            await self._store_effectiveness_data(user_id, agent_type, effectiveness_check)
            
            return AgentResponse(
                response_id=f"adaptation_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result={"effectiveness_check": effectiveness_check, "monitoring": "enabled"},
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error handling completion event: {e}")
            return AgentResponse(
                response_id=f"adaptation_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    # Core Adaptation Methods
    
    async def _analyze_adaptation_need(self, request: AdaptationRequest, archetype: str) -> Dict[str, Any]:
        """Analyze the need for adaptation based on trigger and context"""
        try:
            analysis = {
                "trigger_severity": "medium",
                "confidence": 0.7,
                "affected_components": [],
                "adaptation_priority": "normal",
                "risk_assessment": "low"
            }
            
            # Assess trigger severity
            if request.trigger in [AdaptationTrigger.POOR_ADHERENCE, AdaptationTrigger.ENGAGEMENT_DECLINE]:
                analysis["trigger_severity"] = "high"
                analysis["adaptation_priority"] = "high"
            elif request.trigger == AdaptationTrigger.STRATEGY_INEFFECTIVE:
                analysis["trigger_severity"] = "high"
                analysis["adaptation_priority"] = "urgent"
            
            # Archetype-specific analysis
            if archetype == "Peak Performer":
                analysis["confidence"] = 0.8
                analysis["affected_components"].extend(["optimization", "metrics"])
            elif archetype == "Foundation Builder":
                analysis["risk_assessment"] = "high"  # Be more careful with changes
                analysis["affected_components"].extend(["simplicity", "support"])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing adaptation need: {e}")
            return {"error": str(e)}
    
    async def _gather_adaptation_context(self, user_id: str, request: AdaptationRequest) -> Dict[str, Any]:
        """Gather context data from memory and insights for adaptation"""
        try:
            # In Phase 2 development, simulate context gathering
            # TODO: Integrate with actual Memory and Insights agents
            context = {
                "user_history": {
                    "previous_adaptations": [],
                    "successful_strategies": [],
                    "failed_strategies": [],
                    "preferences": {}
                },
                "current_state": {
                    "engagement_level": 0.7,
                    "adherence_rate": 0.6,
                    "progress_rate": 0.8,
                    "satisfaction": 0.7
                },
                "insights": {
                    "key_patterns": [],
                    "success_factors": [],
                    "challenge_areas": [],
                    "recommendations": []
                }
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error gathering adaptation context: {e}")
            return {}
    
    async def _generate_adaptation_strategies(self, request: AdaptationRequest, 
                                            context: Dict[str, Any], 
                                            analysis: Dict[str, Any], 
                                            archetype: str) -> List[Dict[str, Any]]:
        """Generate adaptation strategies using AI"""
        try:
            import openai
            
            # Check if OpenAI API key is available
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                logger.warning("OpenAI API key not available - using fallback adaptation strategies")
                return self._generate_fallback_adaptations(request, archetype)
            
            # Prepare context for AI analysis
            adaptation_context = f"""
STRATEGY ADAPTATION REQUEST:
User ID: {request.user_id}
Archetype: {archetype}
Trigger: {request.trigger.value}
Urgency: {request.urgency}
Affected Areas: {request.affected_areas}

CONTEXT DATA:
{json.dumps(context, indent=2)}

ANALYSIS:
{json.dumps(analysis, indent=2)}

USER FEEDBACK: {request.user_feedback or "None provided"}

Generate 3-5 adaptation strategies that:
1. Address the specific trigger and affected areas
2. Align with the user's archetype characteristics
3. Consider the user's history and preferences
4. Provide realistic implementation approaches
5. Include expected outcomes and success metrics

Format as JSON with strategy details, confidence scores, and implementation steps.
"""
            
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": adaptation_context}
                ],
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Parse AI response into structured strategies
            strategies = [
                {
                    "strategy_id": f"ai_adaptation_{i+1}",
                    "type": "ai_generated",
                    "description": f"AI Strategy {i+1}",
                    "details": content[:300] + "..." if len(content) > 300 else content,
                    "confidence": 0.8,
                    "expected_impact": "positive",
                    "implementation_complexity": "medium",
                    "archetype_alignment": archetype,
                    "adaptations": [
                        {"area": area, "change": f"AI-optimized change for {area}"}
                        for area in request.affected_areas
                    ]
                }
                for i in range(min(3, max(1, len(request.affected_areas))))
            ]
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error generating AI adaptation strategies: {e}")
            return self._generate_fallback_adaptations(request, archetype)
    
    def _generate_fallback_adaptations(self, request: AdaptationRequest, archetype: str) -> List[Dict[str, Any]]:
        """Generate fallback adaptation strategies when AI is not available"""
        strategies = []
        
        # Base strategy based on trigger
        if request.trigger == AdaptationTrigger.POOR_ADHERENCE:
            strategies.append({
                "strategy_id": "adherence_boost",
                "type": "adherence_improvement",
                "description": "Simplify and reduce complexity to improve adherence",
                "confidence": 0.7,
                "expected_impact": "positive",
                "adaptations": [
                    {"area": "routine", "change": "Reduce daily tasks by 25%"},
                    {"area": "nutrition", "change": "Focus on 2-3 key meals"},
                    {"area": "behavior", "change": "Add habit stacking"}
                ]
            })
        elif request.trigger == AdaptationTrigger.ENGAGEMENT_DECLINE:
            strategies.append({
                "strategy_id": "engagement_recovery",
                "type": "motivation_enhancement",
                "description": "Increase variety and reduce monotony",
                "confidence": 0.6,
                "expected_impact": "positive",
                "adaptations": [
                    {"area": "routine", "change": "Add 2 new activity options per week"},
                    {"area": "behavior", "change": "Introduce gamification elements"},
                    {"area": "engagement", "change": "Weekly progress celebrations"}
                ]
            })
        
        # Archetype-specific adaptations
        if archetype == "Peak Performer":
            strategies.append({
                "strategy_id": "performance_optimization",
                "type": "archetype_aligned",
                "description": "Add advanced tracking and optimization features",
                "confidence": 0.8,
                "adaptations": [
                    {"area": "behavior", "change": "Enhanced metrics tracking"},
                    {"area": "routine", "change": "Performance-based progression"}
                ]
            })
        elif archetype == "Foundation Builder":
            strategies.append({
                "strategy_id": "foundation_strengthen",
                "type": "archetype_aligned", 
                "description": "Reinforce basics with additional support",
                "confidence": 0.7,
                "adaptations": [
                    {"area": "behavior", "change": "Daily check-ins and encouragement"},
                    {"area": "routine", "change": "Simplified core habits focus"}
                ]
            })
        
        return strategies
    
    async def _select_optimal_adaptation(self, user_id: str, strategies: List[Dict], 
                                       analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Select the optimal adaptation strategy"""
        try:
            if not strategies:
                return {"error": "No strategies available"}
            
            # Score strategies based on multiple factors
            scored_strategies = []
            for strategy in strategies:
                score = 0
                
                # Confidence score (40% weight)
                score += strategy.get("confidence", 0.5) * 0.4
                
                # Expected impact (30% weight)  
                impact_score = 0.8 if strategy.get("expected_impact") == "positive" else 0.4
                score += impact_score * 0.3
                
                # Implementation complexity (20% weight) - simpler is better for some archetypes
                complexity = strategy.get("implementation_complexity", "medium")
                complexity_score = {"low": 0.9, "medium": 0.7, "high": 0.4}.get(complexity, 0.5)
                score += complexity_score * 0.2
                
                # Alignment with analysis (10% weight)
                alignment_score = 0.7  # Placeholder
                score += alignment_score * 0.1
                
                scored_strategies.append((strategy, score))
            
            # Select highest scoring strategy
            best_strategy = max(scored_strategies, key=lambda x: x[1])[0]
            best_strategy["selection_score"] = max(scored_strategies, key=lambda x: x[1])[1]
            
            return best_strategy
            
        except Exception as e:
            logger.error(f"Error selecting optimal adaptation: {e}")
            return {"error": str(e)}
    
    async def _coordinate_adaptation(self, user_id: str, adaptation: Dict[str, Any], archetype: str) -> Dict[str, Any]:
        """Coordinate adaptation with other agents"""
        try:
            coordination_results = {
                "coordinated_agents": [],
                "successful_coordinations": [],
                "failed_coordinations": []
            }
            
            # For Phase 2 development, simulate coordination
            # TODO: Integrate with actual agent coordination
            for agent in self.coordination_agents:
                try:
                    # Simulate coordination message
                    coordination_results["coordinated_agents"].append(agent)
                    coordination_results["successful_coordinations"].append(agent)
                    logger.debug(f"Coordinated adaptation with {agent} for {user_id}")
                except Exception as e:
                    coordination_results["failed_coordinations"].append({"agent": agent, "error": str(e)})
            
            return coordination_results
            
        except Exception as e:
            logger.error(f"Error coordinating adaptation: {e}")
            return {"error": str(e)}
    
    async def _create_adaptation_monitoring(self, user_id: str, adaptation: Dict[str, Any]) -> Dict[str, Any]:
        """Create monitoring plan for adaptation effectiveness"""
        try:
            monitoring_plan = {
                "user_id": user_id,
                "adaptation_id": adaptation.get("strategy_id", "unknown"),
                "monitoring_metrics": [
                    "adherence_rate",
                    "engagement_level", 
                    "user_satisfaction",
                    "goal_progress"
                ],
                "monitoring_frequency": "daily",
                "evaluation_period_days": 7,
                "success_criteria": {
                    "adherence_improvement": 0.1,  # 10% improvement
                    "engagement_maintained": 0.6,   # Above 60%
                    "user_satisfaction": 0.7       # Above 70%
                },
                "rollback_triggers": [
                    "adherence_decline_20_percent",
                    "user_dissatisfaction",
                    "goal_regression"
                ],
                "next_evaluation": (datetime.now() + timedelta(days=7)).isoformat()
            }
            
            return monitoring_plan
            
        except Exception as e:
            logger.error(f"Error creating monitoring plan: {e}")
            return {"error": str(e)}
    
    # Data Management Methods
    
    async def _store_adaptation_history(self, user_id: str, result: AdaptationResult):
        """Store adaptation history for learning"""
        try:
            # TODO: Integrate with actual memory storage
            if user_id not in self.adaptation_history:
                self.adaptation_history[user_id] = []
            
            self.adaptation_history[user_id].append({
                "timestamp": result.adapted_at.isoformat(),
                "trigger": result.trigger.value,
                "adaptations": result.adaptations_made,
                "confidence": result.confidence,
                "expected_impact": result.expected_impact
            })
            
            logger.debug(f"Stored adaptation history for {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing adaptation history: {e}")
    
    async def _analyze_strategy_effectiveness(self, user_id: str, monitoring_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze strategy effectiveness based on monitoring data"""
        try:
            effectiveness = {
                "overall_score": 0.7,
                "adherence_score": monitoring_data.get("adherence_rate", 0.7),
                "engagement_score": monitoring_data.get("engagement_level", 0.7),
                "progress_score": monitoring_data.get("progress_rate", 0.7),
                "user_satisfaction": monitoring_data.get("satisfaction", 0.7),
                "trend_direction": "stable",
                "effectiveness_category": "moderate"
            }
            
            # Calculate overall score
            overall = (effectiveness["adherence_score"] + 
                      effectiveness["engagement_score"] + 
                      effectiveness["progress_score"] + 
                      effectiveness["user_satisfaction"]) / 4
            
            effectiveness["overall_score"] = overall
            
            # Categorize effectiveness
            if overall >= 0.8:
                effectiveness["effectiveness_category"] = "excellent"
            elif overall >= 0.6:
                effectiveness["effectiveness_category"] = "good"
            elif overall >= 0.4:
                effectiveness["effectiveness_category"] = "moderate"
            else:
                effectiveness["effectiveness_category"] = "poor"
            
            return effectiveness
            
        except Exception as e:
            logger.error(f"Error analyzing effectiveness: {e}")
            return {"error": str(e)}
    
    async def _evaluate_adaptation_triggers(self, user_id: str, effectiveness: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if adaptation triggers are met"""
        try:
            adaptation_needed = {
                "needed": False,
                "trigger": None,
                "urgency": "low",
                "context": effectiveness,
                "affected_areas": []
            }
            
            overall_score = effectiveness.get("overall_score", 0.7)
            adherence = effectiveness.get("adherence_score", 0.7)
            engagement = effectiveness.get("engagement_score", 0.7)
            
            # Check thresholds
            if adherence < self.adaptation_thresholds["poor_adherence"]:
                adaptation_needed.update({
                    "needed": True,
                    "trigger": "poor_adherence",
                    "urgency": "high",
                    "affected_areas": ["routine", "behavior"]
                })
            elif engagement < (0.7 - self.adaptation_thresholds["engagement_decline"]):
                adaptation_needed.update({
                    "needed": True,
                    "trigger": "engagement_decline", 
                    "urgency": "medium",
                    "affected_areas": ["behavior", "engagement"]
                })
            elif overall_score < self.adaptation_thresholds["strategy_ineffective"]:
                adaptation_needed.update({
                    "needed": True,
                    "trigger": "strategy_ineffective",
                    "urgency": "high",
                    "affected_areas": ["routine", "nutrition", "behavior"]
                })
            
            return adaptation_needed
            
        except Exception as e:
            logger.error(f"Error evaluating adaptation triggers: {e}")
            return {"needed": False, "error": str(e)}
    
    async def _analyze_user_feedback(self, user_id: str, feedback: Dict[str, Any], archetype: str) -> Dict[str, Any]:
        """Analyze user feedback for adaptation needs"""
        try:
            analysis = {
                "sentiment": "neutral",
                "adaptation_needed": False,
                "urgency": "low",
                "affected_areas": [],
                "key_issues": [],
                "positive_aspects": []
            }
            
            feedback_text = feedback.get("text", "").lower()
            rating = feedback.get("rating", 5)  # Assume 1-10 scale
            
            # Simple sentiment analysis
            negative_keywords = ["difficult", "hard", "impossible", "hate", "frustrated", "tired", "boring"]
            positive_keywords = ["love", "great", "easy", "helpful", "motivated", "progress", "satisfied"]
            
            negative_count = sum(1 for word in negative_keywords if word in feedback_text)
            positive_count = sum(1 for word in positive_keywords if word in feedback_text)
            
            if rating <= 4 or negative_count > positive_count:
                analysis.update({
                    "sentiment": "negative",
                    "adaptation_needed": True,
                    "urgency": "high" if rating <= 3 else "medium"
                })
                
                # Identify affected areas based on keywords
                if any(word in feedback_text for word in ["routine", "exercise", "workout"]):
                    analysis["affected_areas"].append("routine")
                if any(word in feedback_text for word in ["food", "meal", "diet", "nutrition"]):
                    analysis["affected_areas"].append("nutrition")
                if any(word in feedback_text for word in ["time", "schedule", "busy"]):
                    analysis["affected_areas"].append("timing")
                    
            elif rating >= 7 or positive_count > negative_count:
                analysis.update({
                    "sentiment": "positive",
                    "positive_aspects": ["user_satisfaction", "strategy_effectiveness"]
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user feedback: {e}")
            return {"error": str(e)}
    
    async def _store_positive_feedback(self, user_id: str, feedback_analysis: Dict[str, Any]):
        """Store positive feedback for learning"""
        try:
            # TODO: Integrate with actual memory storage
            logger.debug(f"Stored positive feedback for {user_id}: {feedback_analysis.get('positive_aspects', [])}")
            
        except Exception as e:
            logger.error(f"Error storing positive feedback: {e}")
    
    async def _sync_adaptation_across_agents(self, user_id: str, coordination_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize adaptation across all coordinated agents"""
        try:
            sync_result = {
                "user_id": user_id,
                "sync_status": "completed",
                "synced_agents": self.coordination_agents,
                "sync_timestamp": datetime.now().isoformat(),
                "coordination_data": coordination_data
            }
            
            return sync_result
            
        except Exception as e:
            logger.error(f"Error syncing adaptation: {e}")
            return {"error": str(e)}
    
    async def _evaluate_completion_effectiveness(self, user_id: str, agent_type: str, completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate effectiveness of completed actions"""
        try:
            effectiveness_check = {
                "user_id": user_id,
                "agent_type": agent_type,
                "completion_timestamp": datetime.now().isoformat(),
                "effectiveness_prediction": 0.7,
                "monitoring_recommended": True,
                "next_check_in_hours": 24
            }
            
            return effectiveness_check
            
        except Exception as e:
            logger.error(f"Error evaluating completion effectiveness: {e}")
            return {"error": str(e)}
    
    async def _store_effectiveness_data(self, user_id: str, agent_type: str, effectiveness_data: Dict[str, Any]):
        """Store effectiveness data for future learning"""
        try:
            # TODO: Integrate with actual memory storage
            if user_id not in self.effectiveness_history:
                self.effectiveness_history[user_id] = {}
            
            if agent_type not in self.effectiveness_history[user_id]:
                self.effectiveness_history[user_id][agent_type] = []
            
            self.effectiveness_history[user_id][agent_type].append(effectiveness_data)
            logger.debug(f"Stored effectiveness data for {user_id} - {agent_type}")
            
        except Exception as e:
            logger.error(f"Error storing effectiveness data: {e}")
    
    async def _publish_adaptation_complete(self, user_id: str, result: AdaptationResult, archetype: str):
        """Publish adaptation completion event"""
        try:
            await self.publish_event(
                event_type="adaptation_complete",
                payload={
                    "adaptation_result": result.dict(),
                    "user_id": user_id,
                    "archetype": archetype,
                    "next_stage": "monitoring"
                },
                user_id=user_id,
                archetype=archetype
            )
            
            logger.debug(f"Published adaptation completion event for {user_id}")
            
        except Exception as e:
            logger.error(f"Error publishing adaptation completion: {e}")

# Entry point for running the agent standalone
async def main():
    """Run the adaptation engine in standalone mode for testing"""
    agent = HolisticAdaptationEngine()
    
    print("⚡ HolisticOS Adaptation Engine Agent Started")
    print("Capabilities: Strategy Monitoring → Effectiveness Analysis → Intelligent Adaptation → Multi-Agent Coordination")
    print("Waiting for events...")
    
    # Keep the agent running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Adaptation Engine")

if __name__ == "__main__":
    asyncio.run(main())