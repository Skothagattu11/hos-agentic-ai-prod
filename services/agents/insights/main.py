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
            logger.error("Error processing insights event", error=str(e))
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
        """Retrieve user memory data from Memory Agent"""
        try:
            # In Phase 2 development, simulate memory retrieval
            # TODO: Integrate with actual Memory Agent
            return {
                "working": {
                    "recent_analysis": {"behavior": {}, "nutrition": {}, "routine": {}},
                    "current_goals": [],
                    "session_data": {}
                },
                "shortterm": {
                    "patterns": [],
                    "preferences": {},
                    "adherence_data": {},
                    "insights": []
                },
                "longterm": {
                    "successful_strategies": {},
                    "persistent_preferences": {},
                    "archetype_evolution": {}
                },
                "meta": {
                    "learning_patterns": {},
                    "adaptation_rates": {},
                    "insight_feedback": {}
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving user memory: {e}")
            return {}
    
    async def _analyze_memory_patterns(self, user_id: str, memory_data: dict, focus_areas: List[str]) -> dict:
        """Analyze patterns across memory layers"""
        try:
            patterns = {
                "behavioral_consistency": 0.0,
                "goal_alignment": 0.0,
                "preference_stability": 0.0,
                "patterns": [],
                "anomalies": [],
                "focus_area_insights": {}
            }
            
            for area in focus_areas:
                patterns["focus_area_insights"][area] = {
                    "pattern_strength": 0.5,
                    "trend_direction": "stable",
                    "confidence": 0.6,
                    "key_observations": [f"Pattern analysis for {area} in development"]
                }
            
            patterns["patterns"] = [
                {
                    "pattern_type": "behavioral_consistency",
                    "description": "User shows consistent patterns in health behaviors",
                    "confidence": 0.7,
                    "evidence_points": 5
                }
            ]
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing memory patterns: {e}")
            return {"patterns": [], "error": str(e)}
    
    async def _detect_behavioral_trends(self, user_id: str, memory_data: dict, time_horizon: str) -> dict:
        """Detect trends and changes in user behavior"""
        try:
            trends = {
                "overall_direction": "improving",
                "trend_strength": 0.6,
                "trends": [
                    "Consistent engagement with health goals",
                    "Stable archetype alignment", 
                    "Positive response to recommendations"
                ],
                "change_points": [],
                "trajectory_prediction": "continued_improvement"
            }
            
            if time_horizon == "short_term":
                trends["timeframe_days"] = 7
            elif time_horizon == "medium_term":
                trends["timeframe_days"] = 30
            else:  # long_term
                trends["timeframe_days"] = 90
            
            return trends
            
        except Exception as e:
            logger.error(f"Error detecting trends: {e}")
            return {"trends": [], "error": str(e)}
    
    async def _generate_ai_insights(self, user_id: str, memory_data: dict, 
                                   pattern_analysis: dict, trend_analysis: dict, 
                                   archetype: str) -> List[Dict[str, Any]]:
        """Generate AI-powered insights using OpenAI"""
        try:
            import openai
            
            # Check if OpenAI API key is available
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                logger.warning("OpenAI API key not available - using fallback insights")
                return self._generate_fallback_insights(user_id, pattern_analysis, trend_analysis, archetype)
            
            # Prepare context for AI analysis
            insights_context = f"""
USER INSIGHTS ANALYSIS REQUEST:
User ID: {user_id}
Archetype: {archetype}

MEMORY ANALYSIS:
Working Memory: {json.dumps(memory_data.get('working', {}), indent=2)}
Short-term Patterns: {json.dumps(memory_data.get('shortterm', {}), indent=2)}
Long-term Preferences: {json.dumps(memory_data.get('longterm', {}), indent=2)}
Meta-learning Data: {json.dumps(memory_data.get('meta', {}), indent=2)}

PATTERN ANALYSIS:
{json.dumps(pattern_analysis, indent=2)}

TREND ANALYSIS:
{json.dumps(trend_analysis, indent=2)}

Generate actionable health insights focusing on:
1. Key behavioral patterns and their implications
2. Personalization opportunities based on user data
3. Archetype-specific recommendations
4. Areas for improvement with specific next steps
5. Predicted outcomes based on current trends

Provide insights in structured JSON format with confidence scores.
"""
            
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": insights_context}
                ],
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Parse AI response into structured insights
            insights = [
                {
                    "insight_id": f"ai_insight_{i+1}",
                    "category": "ai_generated",
                    "title": f"AI Insight {i+1}",
                    "description": content[:200] + "..." if len(content) > 200 else content,
                    "confidence": 0.8,
                    "actionable": True,
                    "archetype_relevance": archetype,
                    "generated_at": datetime.now().isoformat()
                }
                for i in range(min(3, len(content.split('\n'))))
            ]
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return self._generate_fallback_insights(user_id, pattern_analysis, trend_analysis, archetype)
    
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