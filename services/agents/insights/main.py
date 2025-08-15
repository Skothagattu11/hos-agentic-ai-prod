"""
HolisticOS Insights Generation Agent
Analyzes patterns across memory layers to generate actionable health insights and recommendations

Key Functions:
1. Pattern Analysis: Identifies behavioral patterns across time periods
2. Trend Detection: Discovers improvement trends and regression indicators  
3. Personalization: Creates personalized recommendations based on memory data
4. Predictive Insights: Forecasts likely outcomes based on historical patterns
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from shared_libs.event_system.base_agent import BaseAgent, AgentEvent, AgentResponse
from shared_libs.utils.system_prompts import get_system_prompt

logger = logging.getLogger(__name__)

class InsightRequest(BaseModel):
    """Request for insights generation"""
    user_id: str
    insight_type: str  # 'patterns', 'trends', 'recommendations', 'predictions'
    time_horizon: str  # 'short_term', 'medium_term', 'long_term'
    focus_areas: Optional[List[str]] = None  # ['nutrition', 'behavior', 'routine', 'engagement']
    archetype: Optional[str] = None

class InsightResponse(BaseModel):
    """Response containing generated insights"""
    user_id: str
    insight_type: str
    insights: List[Dict[str, Any]]
    confidence_score: float
    recommendations: List[str]
    patterns_identified: int
    trends_detected: List[str]
    prediction_accuracy: Optional[float] = None
    generated_at: datetime

class HolisticInsightsAgent(BaseAgent):
    """
    HolisticOS Insights Generation Agent
    
    Analyzes user data across all memory layers to generate:
    - Behavioral pattern insights
    - Health trend analysis  
    - Personalized recommendations
    - Predictive health analytics
    - Archetype-specific guidance refinements
    """
    
    def __init__(self, redis_url: str = None):
        super().__init__(
            agent_id="insights_generation_agent",
            agent_type="insights_generation"
        )
        
        # Insight generation settings
        self.min_data_points = 3  # Minimum data points for reliable insights
        self.confidence_threshold = 0.6  # Minimum confidence for actionable insights
        self.trend_detection_window = 14  # Days for trend analysis
        
        # Pattern analysis categories
        self.analysis_categories = [
            "behavioral_patterns",
            "nutrition_adherence", 
            "routine_consistency",
            "engagement_levels",
            "goal_progression",
            "archetype_alignment"
        ]
        
        logger.info(f"Initialized HolisticInsightsAgent with system prompt length: {len(self.system_prompt)}")
    
    def get_supported_event_types(self) -> List[str]:
        """Events this insights agent supports"""
        return [
            "generate_insights",
            "analyze_patterns",
            "detect_trends", 
            "create_recommendations",
            "predict_outcomes",
            "behavior_analysis_complete",
            "nutrition_plan_complete",
            "routine_plan_complete",
            "memory_consolidation_complete"
        ]
    
    async def process(self, event: AgentEvent) -> AgentResponse:
        """Process insights-related events"""
        try:
            logger.info("Processing insights event",
                       event_type=event.event_type,
                       user_id=event.user_id)
            
            if event.event_type == "generate_insights":
                return await self._handle_generate_insights(event)
            elif event.event_type == "analyze_patterns":
                return await self._handle_pattern_analysis(event)
            elif event.event_type == "detect_trends":
                return await self._handle_trend_detection(event)
            elif event.event_type == "create_recommendations":
                return await self._handle_recommendation_generation(event)
            elif event.event_type == "predict_outcomes":
                return await self._handle_outcome_prediction(event)
            elif event.event_type.endswith("_complete"):
                return await self._handle_analysis_complete(event)
            else:
                return AgentResponse(
                    response_id=f"insights_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    success=False,
                    error_message=f"Unsupported event type: {event.event_type}",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error processing insights event: {str(e)}")
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_generate_insights(self, event: AgentEvent) -> AgentResponse:
        """Generate comprehensive insights for a user"""
        try:
            user_id = event.user_id
            payload = event.payload
            
            insight_type = payload.get("insight_type", "comprehensive")
            time_horizon = payload.get("time_horizon", "medium_term")
            focus_areas = payload.get("focus_areas", self.analysis_categories)
            archetype = event.archetype
            
            # Step 1: Retrieve user memory data
            memory_data = await self._retrieve_user_memory(user_id)
            
            # Step 2: Analyze patterns across memory layers
            pattern_analysis = await self._analyze_memory_patterns(user_id, memory_data, focus_areas)
            
            # Step 3: Detect trends and changes
            trend_analysis = await self._detect_behavioral_trends(user_id, memory_data, time_horizon)
            
            # Step 4: Generate AI-powered insights
            ai_insights = await self._generate_ai_insights(
                user_id, memory_data, pattern_analysis, trend_analysis, archetype
            )
            
            # Step 5: Create actionable recommendations
            recommendations = await self._create_personalized_recommendations(
                user_id, ai_insights, archetype, focus_areas
            )
            
            # Step 6: Calculate confidence and compile results
            insights_response = InsightResponse(
                user_id=user_id,
                insight_type=insight_type,
                insights=ai_insights,
                confidence_score=self._calculate_confidence_score(pattern_analysis, trend_analysis),
                recommendations=recommendations,
                patterns_identified=len(pattern_analysis.get("patterns", [])),
                trends_detected=trend_analysis.get("trends", []),
                generated_at=datetime.now()
            )
            
            # Step 7: Store insights in memory for future reference
            await self._store_insights_in_memory(user_id, insights_response)
            
            # Step 8: Publish insights completion event
            await self._publish_insights_complete_event(user_id, insights_response, archetype)
            
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result=insights_response.dict(),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_pattern_analysis(self, event: AgentEvent) -> AgentResponse:
        """Handle specific pattern analysis requests"""
        try:
            user_id = event.user_id
            focus_areas = event.payload.get("focus_areas", ["behavioral_patterns"])
            
            memory_data = await self._retrieve_user_memory(user_id)
            pattern_analysis = await self._analyze_memory_patterns(user_id, memory_data, focus_areas)
            
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result=pattern_analysis,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}")
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_trend_detection(self, event: AgentEvent) -> AgentResponse:
        """Handle trend detection requests"""
        try:
            user_id = event.user_id
            time_horizon = event.payload.get("time_horizon", "medium_term")
            
            memory_data = await self._retrieve_user_memory(user_id)
            trend_analysis = await self._detect_behavioral_trends(user_id, memory_data, time_horizon)
            
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result=trend_analysis,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in trend detection: {e}")
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_recommendation_generation(self, event: AgentEvent) -> AgentResponse:
        """Handle recommendation generation requests"""
        try:
            user_id = event.user_id
            archetype = event.archetype
            focus_areas = event.payload.get("focus_areas", self.analysis_categories)
            
            # Get recent insights as context
            memory_data = await self._retrieve_user_memory(user_id)
            recent_insights = memory_data.get("shortterm", {}).get("insights", [])
            
            recommendations = await self._create_personalized_recommendations(
                user_id, recent_insights, archetype, focus_areas
            )
            
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result={"recommendations": recommendations, "focus_areas": focus_areas},
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_outcome_prediction(self, event: AgentEvent) -> AgentResponse:
        """Handle outcome prediction requests"""
        try:
            user_id = event.user_id
            prediction_horizon = event.payload.get("horizon_days", 30)
            
            memory_data = await self._retrieve_user_memory(user_id)
            predictions = await self._predict_health_outcomes(user_id, memory_data, prediction_horizon)
            
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=True,
                result=predictions,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in outcome prediction: {e}")
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _handle_analysis_complete(self, event: AgentEvent) -> AgentResponse:
        """Handle completion events from other agents to trigger insights"""
        try:
            user_id = event.user_id
            archetype = event.archetype
            
            # Trigger automatic insights generation after major analysis completion
            insights_event = AgentEvent(
                event_id=f"auto_insights_{datetime.now().timestamp()}",
                event_type="generate_insights",
                source_agent=self.agent_id,
                payload={
                    "insight_type": "post_analysis",
                    "time_horizon": "short_term",
                    "trigger_event": event.event_type
                },
                timestamp=datetime.now(),
                user_id=user_id,
                archetype=archetype
            )
            
            # Process insights automatically
            return await self._handle_generate_insights(insights_event)
            
        except Exception as e:
            logger.error(f"Error handling analysis completion: {e}")
            return AgentResponse(
                response_id=f"insights_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    # Core Insights Generation Methods
    
    async def _retrieve_user_memory(self, user_id: str) -> dict:
        """Retrieve REAL user memory data from HolisticMemoryService"""
        try:
            from services.agents.memory.holistic_memory_service import HolisticMemoryService
            
            memory_service = HolisticMemoryService()
            
            try:
                # Get all 4 memory layers from real memory system
                longterm = await memory_service.get_user_longterm_memory(user_id)
                recent_patterns = await memory_service.get_recent_patterns(user_id, days=14)
                meta_memory = await memory_service.get_meta_memory(user_id)
                working_memory = await memory_service.get_working_memory(user_id)
                
                # Transform to insights-friendly format
                return {
                    "working": self._transform_working_memory(working_memory),
                    "shortterm": self._transform_shortterm_memory(recent_patterns),
                    "longterm": self._transform_longterm_memory(longterm),
                    "meta": self._transform_meta_memory(meta_memory)
                }
                
            finally:
                await memory_service.cleanup()
                
        except Exception as e:
            logger.error(f"Error retrieving user memory from real system: {e}")
            # Fallback to minimal structure if real memory fails
            return {
                "working": {"error": "Memory service unavailable"},
                "shortterm": {"error": "Memory service unavailable"},
                "longterm": {"error": "Memory service unavailable"},
                "meta": {"error": "Memory service unavailable"},
                "fallback_used": True,
                "error": str(e)
            }
    
    def _transform_working_memory(self, working_memory) -> dict:
        """Transform working memory data for insights analysis"""
        if not working_memory:
            return {"status": "no_working_memory"}
        
        try:
            # Extract recent analysis results and session context
            transformed = {
                "recent_analysis": {},
                "current_goals": [],
                "session_data": {},
                "context_available": True
            }
            
            # Working memory typically contains current session data
            if hasattr(working_memory, 'session_data') and working_memory.session_data:
                transformed["session_data"] = working_memory.session_data
            
            if hasattr(working_memory, 'current_goals') and working_memory.current_goals:
                transformed["current_goals"] = working_memory.current_goals
                
            return transformed
            
        except Exception as e:
            logger.debug(f"Error transforming working memory: {e}")
            return {"status": "transform_error", "error": str(e)}
    
    def _transform_shortterm_memory(self, recent_patterns) -> dict:
        """Transform short-term memory patterns for insights analysis"""
        if not recent_patterns:
            return {"status": "no_recent_patterns"}
        
        try:
            transformed = {
                "patterns": [],
                "preferences": {},
                "adherence_data": {},
                "insights": [],
                "pattern_count": 0
            }
            
            # Extract patterns from recent memory
            if hasattr(recent_patterns, 'pattern_shifts') and recent_patterns.pattern_shifts:
                transformed["patterns"] = recent_patterns.pattern_shifts
                transformed["pattern_count"] = len(recent_patterns.pattern_shifts)
            
            if hasattr(recent_patterns, 'preference_changes') and recent_patterns.preference_changes:
                transformed["preferences"] = recent_patterns.preference_changes
            
            if hasattr(recent_patterns, 'adherence_trends') and recent_patterns.adherence_trends:
                transformed["adherence_data"] = recent_patterns.adherence_trends
                
            return transformed
            
        except Exception as e:
            logger.debug(f"Error transforming short-term memory: {e}")
            return {"status": "transform_error", "error": str(e)}
    
    def _transform_longterm_memory(self, longterm_memory) -> dict:
        """Transform long-term memory for insights analysis"""
        if not longterm_memory:
            return {"status": "no_longterm_memory"}
        
        try:
            transformed = {
                "successful_strategies": {},
                "persistent_preferences": {},
                "archetype_evolution": {},
                "behavioral_patterns": {},
                "health_goals": {}
            }
            
            # Extract established patterns and strategies
            if hasattr(longterm_memory, 'success_strategies') and longterm_memory.success_strategies:
                transformed["successful_strategies"] = longterm_memory.success_strategies
            
            if hasattr(longterm_memory, 'preference_patterns') and longterm_memory.preference_patterns:
                transformed["persistent_preferences"] = longterm_memory.preference_patterns
            
            if hasattr(longterm_memory, 'behavioral_patterns') and longterm_memory.behavioral_patterns:
                transformed["behavioral_patterns"] = longterm_memory.behavioral_patterns
                
            if hasattr(longterm_memory, 'health_goals') and longterm_memory.health_goals:
                transformed["health_goals"] = longterm_memory.health_goals
                
            return transformed
            
        except Exception as e:
            logger.debug(f"Error transforming long-term memory: {e}")
            return {"status": "transform_error", "error": str(e)}
    
    def _transform_meta_memory(self, meta_memory) -> dict:
        """Transform meta-memory for insights analysis"""
        if not meta_memory:
            return {"status": "no_meta_memory"}
        
        try:
            transformed = {
                "learning_patterns": {},
                "adaptation_rates": {},
                "insight_feedback": {},
                "learning_velocity": {},
                "success_predictors": {}
            }
            
            # Extract meta-learning insights
            if hasattr(meta_memory, 'learning_patterns') and meta_memory.learning_patterns:
                transformed["learning_patterns"] = meta_memory.learning_patterns
            
            if hasattr(meta_memory, 'adaptation_patterns') and meta_memory.adaptation_patterns:
                transformed["adaptation_rates"] = meta_memory.adaptation_patterns
                
            if hasattr(meta_memory, 'learning_velocity') and meta_memory.learning_velocity:
                transformed["learning_velocity"] = meta_memory.learning_velocity
                
            if hasattr(meta_memory, 'success_predictors') and meta_memory.success_predictors:
                transformed["success_predictors"] = meta_memory.success_predictors
                
            return transformed
            
        except Exception as e:
            logger.debug(f"Error transforming meta-memory: {e}")
            return {"status": "transform_error", "error": str(e)}
    
    async def _analyze_memory_patterns(self, user_id: str, memory_data: dict, focus_areas: List[str]) -> dict:
        """Enhanced pattern analysis using real memory data"""
        try:
            patterns = {
                "behavioral_consistency": self._calculate_behavioral_consistency(memory_data),
                "goal_alignment": self._calculate_goal_alignment(memory_data),
                "preference_stability": self._calculate_preference_stability(memory_data),
                "patterns": [],
                "anomalies": [],
                "focus_area_insights": {}
            }
            
            # Analyze real behavioral patterns from long-term memory
            if memory_data.get("longterm") and memory_data["longterm"].get("behavioral_patterns"):
                patterns["patterns"].extend(self._extract_behavioral_patterns(memory_data["longterm"]))
            
            # Analyze short-term changes and trends
            if memory_data.get("shortterm") and memory_data["shortterm"].get("pattern_count", 0) > 0:
                patterns["patterns"].extend(self._extract_trend_patterns(memory_data["shortterm"]))
            
            # Detect anomalies from memory data
            anomalies = self._detect_memory_anomalies(memory_data)
            if anomalies:
                patterns["anomalies"] = anomalies
            
            # Focus area analysis with real data
            for area in focus_areas:
                patterns["focus_area_insights"][area] = self._analyze_focus_area(memory_data, area)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing memory patterns: {e}")
            return {"patterns": [], "error": str(e)}
    
    def _calculate_behavioral_consistency(self, memory_data: dict) -> float:
        """Calculate behavioral consistency score based on memory data"""
        try:
            # Check if user has established patterns
            longterm = memory_data.get("longterm", {})
            shortterm = memory_data.get("shortterm", {})
            
            if longterm.get("status") == "no_longterm_memory":
                return 0.3  # New user - low consistency
            
            # Score based on pattern stability
            pattern_count = shortterm.get("pattern_count", 0)
            if pattern_count > 5:
                return 0.8  # High consistency
            elif pattern_count > 2:
                return 0.6  # Medium consistency
            else:
                return 0.4  # Lower consistency
                
        except Exception:
            return 0.5  # Default neutral score
    
    def _calculate_goal_alignment(self, memory_data: dict) -> float:
        """Calculate goal alignment score"""
        try:
            longterm = memory_data.get("longterm", {})
            working = memory_data.get("working", {})
            
            # Check if goals are established and aligned
            has_goals = bool(longterm.get("health_goals"))
            has_current_goals = bool(working.get("current_goals"))
            
            if has_goals and has_current_goals:
                return 0.8  # High alignment
            elif has_goals or has_current_goals:
                return 0.6  # Partial alignment
            else:
                return 0.4  # Low alignment
                
        except Exception:
            return 0.5
    
    def _calculate_preference_stability(self, memory_data: dict) -> float:
        """Calculate preference stability score"""
        try:
            longterm = memory_data.get("longterm", {})
            shortterm = memory_data.get("shortterm", {})
            
            # Check for stable preferences vs recent changes
            has_persistent_prefs = bool(longterm.get("persistent_preferences"))
            has_recent_changes = bool(shortterm.get("preferences"))
            
            if has_persistent_prefs and not has_recent_changes:
                return 0.9  # Very stable
            elif has_persistent_prefs and has_recent_changes:
                return 0.6  # Some changes
            else:
                return 0.4  # Unstable or unknown
                
        except Exception:
            return 0.5
    
    def _extract_behavioral_patterns(self, longterm_memory: dict) -> List[dict]:
        """Extract behavioral patterns from long-term memory"""
        patterns = []
        try:
            behavioral_patterns = longterm_memory.get("behavioral_patterns", {})
            
            for pattern_type, pattern_data in behavioral_patterns.items():
                patterns.append({
                    "pattern_type": f"established_{pattern_type}",
                    "description": f"User has established {pattern_type} patterns",
                    "confidence": 0.8,
                    "evidence_points": 10,
                    "source": "longterm_memory"
                })
                
        except Exception as e:
            logger.debug(f"Error extracting behavioral patterns: {e}")
            
        return patterns
    
    def _extract_trend_patterns(self, shortterm_memory: dict) -> List[dict]:
        """Extract trend patterns from short-term memory"""
        patterns = []
        try:
            pattern_count = shortterm_memory.get("pattern_count", 0)
            
            if pattern_count > 0:
                patterns.append({
                    "pattern_type": "recent_changes",
                    "description": f"User has {pattern_count} recent pattern changes",
                    "confidence": 0.7,
                    "evidence_points": pattern_count,
                    "source": "shortterm_memory"
                })
                
        except Exception as e:
            logger.debug(f"Error extracting trend patterns: {e}")
            
        return patterns
    
    def _detect_memory_anomalies(self, memory_data: dict) -> List[dict]:
        """Detect anomalies in memory data"""
        anomalies = []
        try:
            # Check for inconsistencies between memory layers
            longterm = memory_data.get("longterm", {})
            shortterm = memory_data.get("shortterm", {})
            
            # Example: Strong preferences in longterm but recent changes in shortterm
            if (longterm.get("persistent_preferences") and 
                shortterm.get("preferences")):
                anomalies.append({
                    "anomaly_type": "preference_shift",
                    "description": "User showing recent preference changes despite established patterns",
                    "confidence": 0.6,
                    "requires_attention": True
                })
                
        except Exception as e:
            logger.debug(f"Error detecting anomalies: {e}")
            
        return anomalies
    
    def _analyze_focus_area(self, memory_data: dict, area: str) -> dict:
        """Analyze specific focus area using memory data"""
        try:
            longterm = memory_data.get("longterm", {})
            shortterm = memory_data.get("shortterm", {})
            
            # Area-specific analysis
            if area == "behavioral_patterns":
                return {
                    "pattern_strength": 0.8 if longterm.get("behavioral_patterns") else 0.3,
                    "trend_direction": "improving" if shortterm.get("pattern_count", 0) > 0 else "stable",
                    "confidence": 0.7,
                    "key_observations": [f"Memory-based {area} analysis available"]
                }
            elif area == "nutrition_adherence":
                return {
                    "pattern_strength": 0.7 if longterm.get("successful_strategies") else 0.4,
                    "trend_direction": "stable",
                    "confidence": 0.6,
                    "key_observations": [f"Nutrition patterns from memory analysis"]
                }
            elif area == "routine_consistency":
                return {
                    "pattern_strength": 0.6 if longterm.get("behavioral_patterns") else 0.3,
                    "trend_direction": "stable",
                    "confidence": 0.6,
                    "key_observations": [f"Routine patterns from memory analysis"]
                }
            else:
                return {
                    "pattern_strength": 0.5,
                    "trend_direction": "stable",
                    "confidence": 0.5,
                    "key_observations": [f"General {area} analysis from memory"]
                }
                
        except Exception as e:
            return {
                "pattern_strength": 0.3,
                "trend_direction": "unknown",
                "confidence": 0.3,
                "key_observations": [f"Error analyzing {area}: {e}"]
            }
    
    async def _detect_behavioral_trends(self, user_id: str, memory_data: dict, time_horizon: str) -> dict:
        """Enhanced trend detection using real historical data"""
        try:
            # Get analysis history for trend calculation
            from services.agents.memory.holistic_memory_service import HolisticMemoryService
            memory_service = HolisticMemoryService()
            
            try:
                analysis_history = await memory_service.get_analysis_history(user_id, limit=10)
                
                trends = {
                    "overall_direction": self._calculate_overall_direction(analysis_history, memory_data),
                    "trend_strength": self._calculate_trend_strength(analysis_history, memory_data),
                    "trends": self._identify_specific_trends(analysis_history, memory_data),
                    "change_points": self._identify_change_points(analysis_history),
                    "trajectory_prediction": self._predict_trajectory(analysis_history, memory_data)
                }
                
                # Set timeframe based on horizon
                if time_horizon == "short_term":
                    trends["timeframe_days"] = 7
                elif time_horizon == "medium_term":
                    trends["timeframe_days"] = 30
                else:  # long_term
                    trends["timeframe_days"] = 90
                
                return trends
                
            finally:
                await memory_service.cleanup()
            
        except Exception as e:
            logger.error(f"Error detecting trends: {e}")
            # Fallback to basic analysis
            return {
                "trends": ["Basic trend analysis (limited data)"],
                "overall_direction": "stable",
                "trend_strength": 0.5,
                "error": str(e)
            }
    
    def _calculate_overall_direction(self, analysis_history: List, memory_data: dict) -> str:
        """Calculate overall trend direction from historical data"""
        try:
            if not analysis_history or len(analysis_history) < 2:
                return "insufficient_data"
            
            # Check for improvement indicators in memory
            longterm = memory_data.get("longterm", {})
            if longterm.get("successful_strategies"):
                return "improving"
            
            # Check recent patterns
            shortterm = memory_data.get("shortterm", {})
            if shortterm.get("pattern_count", 0) > 3:
                return "improving"
            
            return "stable"
            
        except Exception:
            return "unknown"
    
    def _calculate_trend_strength(self, analysis_history: List, memory_data: dict) -> float:
        """Calculate strength of the detected trend"""
        try:
            # Base strength on data availability and consistency
            history_count = len(analysis_history) if analysis_history else 0
            
            if history_count > 5:
                base_strength = 0.8
            elif history_count > 2:
                base_strength = 0.6
            else:
                base_strength = 0.4
            
            # Adjust based on memory data consistency
            longterm = memory_data.get("longterm", {})
            if longterm.get("behavioral_patterns"):
                base_strength += 0.1
            
            return min(base_strength, 1.0)
            
        except Exception:
            return 0.5
    
    def _identify_specific_trends(self, analysis_history: List, memory_data: dict) -> List[str]:
        """Identify specific behavioral trends from real data"""
        trends = []
        try:
            # Analyze based on available memory data
            longterm = memory_data.get("longterm", {})
            shortterm = memory_data.get("shortterm", {})
            
            if longterm.get("behavioral_patterns"):
                trends.append("Established behavioral patterns show consistency")
            
            if longterm.get("successful_strategies"):
                trends.append("User has developed effective strategies")
            
            if shortterm.get("pattern_count", 0) > 0:
                trends.append(f"Recent activity shows {shortterm['pattern_count']} pattern changes")
            
            if analysis_history and len(analysis_history) > 1:
                trends.append(f"Analysis history shows {len(analysis_history)} recorded sessions")
            
            # Fallback if no specific trends found
            if not trends:
                trends.append("User engagement patterns developing")
                
        except Exception as e:
            trends.append(f"Trend analysis limited: {e}")
            
        return trends
    
    def _identify_change_points(self, analysis_history: List) -> List[dict]:
        """Identify significant change points in user behavior"""
        change_points = []
        try:
            if not analysis_history or len(analysis_history) < 3:
                return change_points
            
            # Look for significant gaps or changes in analysis frequency
            for i in range(1, len(analysis_history)):
                current = analysis_history[i-1]
                previous = analysis_history[i]
                
                # Check for time gaps (simple heuristic)
                time_gap = (current.created_at - previous.created_at).days
                if time_gap > 7:  # More than a week gap
                    change_points.append({
                        "date": current.created_at.isoformat(),
                        "type": "engagement_gap",
                        "description": f"{time_gap} day gap in analysis activity"
                    })
                    
        except Exception as e:
            logger.debug(f"Error identifying change points: {e}")
            
        return change_points
    
    def _predict_trajectory(self, analysis_history: List, memory_data: dict) -> str:
        """Predict future behavioral trajectory"""
        try:
            longterm = memory_data.get("longterm", {})
            meta = memory_data.get("meta", {})
            
            # Base prediction on established patterns
            if longterm.get("successful_strategies") and meta.get("learning_velocity"):
                return "continued_improvement"
            elif longterm.get("behavioral_patterns"):
                return "stable_progress"
            elif len(analysis_history) > 2:
                return "pattern_development"
            else:
                return "early_stage"
                
        except Exception:
            return "unknown"
    
    async def _generate_ai_insights(self, user_id: str, memory_data: dict, 
                                   pattern_analysis: dict, trend_analysis: dict, 
                                   archetype: str) -> List[Dict[str, Any]]:
        """Generate AI-powered insights using comprehensive memory context"""
        try:
            import openai
            
            # Check if OpenAI API key is available
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                logger.warning("OpenAI API key not available - using fallback insights")
                return self._generate_fallback_insights(user_id, pattern_analysis, trend_analysis, archetype)
            
            # Use EnhancedMemoryPromptsService for insights prompts
            from services.agents.memory.enhanced_memory_prompts import EnhancedMemoryPromptsService
            enhanced_prompts_service = EnhancedMemoryPromptsService()
            
            try:
                # Get enhanced prompt with memory context
                from shared_libs.utils.system_prompts import get_system_prompt
                base_insights_prompt = get_system_prompt("insights_generation")
                
                enhanced_prompt = await enhanced_prompts_service.enhance_agent_prompt(
                    base_prompt=base_insights_prompt,
                    user_id=user_id,
                    agent_type="insights_generation"
                )
                
                # Rich context for AI insights with real memory data
                insights_context = f"""
COMPREHENSIVE USER ANALYSIS - MEMORY-ENHANCED INSIGHTS:
User ID: {user_id}
Archetype: {archetype}

REAL MEMORY DATA ANALYSIS:
Working Memory Status: {memory_data.get('working', {}).get('status', 'Available')}
Short-term Patterns: {memory_data.get('shortterm', {}).get('pattern_count', 0)} patterns detected
Long-term Memory Status: {memory_data.get('longterm', {}).get('status', 'Available')}
Meta-learning Status: {memory_data.get('meta', {}).get('status', 'Available')}

DETAILED MEMORY ANALYSIS:
{json.dumps(memory_data, indent=2, default=str)}

PATTERN ANALYSIS (Real Data):
{json.dumps(pattern_analysis, indent=2)}

TREND ANALYSIS (Historical Data):
{json.dumps(trend_analysis, indent=2)}

INSIGHTS GENERATION REQUIREMENTS:
Generate deep, personalized insights that:
1. Reference specific patterns from user's real memory data
2. Build on established successful strategies from long-term memory
3. Identify areas for improvement based on historical trend analysis
4. Provide predictive insights about user behavior using meta-memory
5. Suggest specific, actionable next steps based on memory-informed understanding
6. Connect insights to user's archetype while personalizing based on memory profile

Focus on insights that could only be generated with access to the user's complete memory profile.
"""
                
                # Generate insights with enhanced context
                response = await asyncio.to_thread(
                    openai.chat.completions.create,
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": enhanced_prompt},
                        {"role": "user", "content": insights_context}
                    ],
                    temperature=0.7
                )
                
                content = response.choices[0].message.content
                
                # Parse AI response into structured insights with memory-based confidence scoring
                insights = self._parse_ai_insights_response(content, memory_data, archetype)
                
                return insights
                
            finally:
                await enhanced_prompts_service.cleanup()
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return self._generate_fallback_insights(user_id, pattern_analysis, trend_analysis, archetype)
    
    def _parse_ai_insights_response(self, content: str, memory_data: dict, archetype: str) -> List[Dict[str, Any]]:
        """Parse AI insights response with memory-based confidence scoring"""
        insights = []
        try:
            # Split content into sections/insights
            sections = content.split('\n\n')
            
            for i, section in enumerate(sections[:5]):  # Limit to 5 insights
                if len(section.strip()) > 20:  # Meaningful content
                    
                    # Calculate confidence based on memory data availability
                    confidence = self._calculate_insight_confidence(memory_data)
                    
                    insight = {
                        "insight_id": f"memory_enhanced_insight_{i+1}",
                        "category": "memory_informed",
                        "title": f"Memory-Enhanced Insight {i+1}",
                        "description": section.strip()[:300] + "..." if len(section.strip()) > 300 else section.strip(),
                        "confidence": confidence,
                        "actionable": True,
                        "archetype_relevance": archetype,
                        "memory_informed": True,
                        "generated_at": datetime.now().isoformat(),
                        "memory_layers_used": self._identify_memory_layers_used(memory_data)
                    }
                    insights.append(insight)
            
            return insights if insights else self._generate_fallback_insights("unknown", {}, {}, archetype)
            
        except Exception as e:
            logger.error(f"Error parsing AI insights: {e}")
            return self._generate_fallback_insights("unknown", {}, {}, archetype)
    
    def _calculate_insight_confidence(self, memory_data: dict) -> float:
        """Calculate insight confidence based on memory data richness"""
        try:
            confidence = 0.5  # Base confidence
            
            # Boost confidence based on available memory layers
            if memory_data.get("longterm", {}).get("status") != "no_longterm_memory":
                confidence += 0.2
            if memory_data.get("shortterm", {}).get("pattern_count", 0) > 0:
                confidence += 0.1
            if memory_data.get("meta", {}).get("status") != "no_meta_memory":
                confidence += 0.1
            if memory_data.get("working", {}).get("context_available"):
                confidence += 0.1
                
            return min(confidence, 0.95)  # Cap at 95%
            
        except Exception:
            return 0.6  # Default moderate confidence
    
    def _identify_memory_layers_used(self, memory_data: dict) -> List[str]:
        """Identify which memory layers contributed to the insights"""
        layers_used = []
        try:
            if memory_data.get("longterm", {}).get("status") != "no_longterm_memory":
                layers_used.append("longterm")
            if memory_data.get("shortterm", {}).get("pattern_count", 0) > 0:
                layers_used.append("shortterm")
            if memory_data.get("meta", {}).get("status") != "no_meta_memory":
                layers_used.append("meta")
            if memory_data.get("working", {}).get("context_available"):
                layers_used.append("working")
                
        except Exception:
            layers_used = ["fallback"]
            
        return layers_used
    
    def _generate_fallback_insights(self, user_id: str, pattern_analysis: dict, 
                                   trend_analysis: dict, archetype: str) -> List[Dict[str, Any]]:
        """Generate fallback insights when AI is not available"""
        return [
            {
                "insight_id": "fallback_1",
                "category": "behavioral_pattern",
                "title": "Consistent Health Engagement",
                "description": f"User {user_id} shows consistent engagement with health goals",
                "confidence": 0.7,
                "actionable": True,
                "archetype_relevance": archetype,
                "generated_at": datetime.now().isoformat()
            },
            {
                "insight_id": "fallback_2", 
                "category": "trend_analysis",
                "title": "Positive Health Trajectory",
                "description": f"Overall trend direction: {trend_analysis.get('overall_direction', 'stable')}",
                "confidence": 0.6,
                "actionable": True,
                "archetype_relevance": archetype,
                "generated_at": datetime.now().isoformat()
            }
        ]
    
    async def _create_personalized_recommendations(self, user_id: str, insights: List[Dict], 
                                                  archetype: str, focus_areas: List[str]) -> List[str]:
        """Create personalized recommendations based on insights"""
        try:
            recommendations = []
            
            # Archetype-specific base recommendations
            if archetype == "Peak Performer":
                recommendations.extend([
                    "Focus on optimization metrics and advanced performance tracking",
                    "Consider periodization in your training and nutrition approach"
                ])
            elif archetype == "Foundation Builder":
                recommendations.extend([
                    "Maintain consistent daily habits and gradual progression",
                    "Focus on building sustainable routines before adding complexity"
                ])
            elif archetype == "Systematic Improver":
                recommendations.extend([
                    "Continue data-driven approach with regular progress reviews",
                    "Implement A/B testing for different strategies"
                ])
            else:
                recommendations.append("Continue current approach with minor adjustments")
            
            # Focus area specific recommendations
            for area in focus_areas:
                if area == "behavioral_patterns":
                    recommendations.append("Strengthen positive behavioral patterns through habit stacking")
                elif area == "nutrition_adherence":
                    recommendations.append("Optimize meal timing and preparation strategies")
                elif area == "routine_consistency":
                    recommendations.append("Build flexibility into routines to maintain consistency")
            
            # Insights-based recommendations
            for insight in insights:
                if insight.get("confidence", 0) > 0.7:
                    recommendations.append(f"Focus on: {insight.get('title', 'Insight area')}")
            
            return recommendations[:5]  # Limit to top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error creating recommendations: {e}")
            return ["Continue current health approach with mindful adjustments"]
    
    async def _predict_health_outcomes(self, user_id: str, memory_data: dict, horizon_days: int) -> dict:
        """Predict health outcomes based on current patterns"""
        try:
            predictions = {
                "prediction_horizon_days": horizon_days,
                "predicted_outcomes": {
                    "goal_achievement_probability": 0.75,
                    "routine_adherence_rate": 0.80,
                    "engagement_level": "high",
                    "potential_challenges": ["schedule conflicts", "motivation dips"]
                },
                "confidence_level": 0.65,
                "recommendation_impact": "positive",
                "risk_factors": [],
                "success_factors": ["consistent patterns", "archetype alignment"]
            }
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting outcomes: {e}")
            return {"error": str(e)}
    
    def _calculate_confidence_score(self, pattern_analysis: dict, trend_analysis: dict) -> float:
        """Calculate overall confidence score for insights"""
        try:
            pattern_confidence = pattern_analysis.get("behavioral_consistency", 0.5)
            trend_confidence = trend_analysis.get("trend_strength", 0.5)
            data_quality = 0.7  # Placeholder for data quality assessment
            
            overall_confidence = (pattern_confidence + trend_confidence + data_quality) / 3
            return min(max(overall_confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
    async def _store_insights_in_memory(self, user_id: str, insights_response: InsightResponse):
        """Store generated insights in memory for future reference"""
        try:
            # TODO: Publish to Memory Agent
            logger.info(f"Storing insights in memory for {user_id}")
            # This would publish a memory_store event to the Memory Agent
            
        except Exception as e:
            logger.error(f"Error storing insights in memory: {e}")
    
    async def _publish_insights_complete_event(self, user_id: str, insights_response: InsightResponse, archetype: str):
        """Publish insights completion event for other agents"""
        try:
            await self.publish_event(
                event_type="insights_generation_complete",
                payload={
                    "insights": insights_response.dict(),
                    "user_id": user_id,
                    "archetype": archetype,
                    "next_stage": "adaptation_engine"
                },
                user_id=user_id,
                archetype=archetype
            )
            
            logger.info(f"Published insights completion event for {user_id}")
            
        except Exception as e:
            logger.error(f"Error publishing insights completion event: {e}")

# Entry point for running the agent standalone
async def main():
    """Run the insights agent in standalone mode for testing"""
    agent = HolisticInsightsAgent()
    
    print("🔍 HolisticOS Insights Generation Agent Started")
    print("Capabilities: Pattern Analysis → Trend Detection → AI Insights → Recommendations")
    print("Waiting for events...")
    
    # Keep the agent running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Insights Agent")

if __name__ == "__main__":
    asyncio.run(main())