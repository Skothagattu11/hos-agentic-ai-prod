"""
Circadian Analysis Service - AI-Powered Biomarker Analysis
Follows same pattern as BehaviorAnalysisAgent
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class CircadianAnalysisService:
    """AI-powered circadian rhythm analysis service using OpenAI models"""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # Use GPT-4o for advanced biomarker analysis
        logger.debug(f"CircadianAnalysisService initialized with model: {self.model}")

    async def analyze(self, enhanced_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered circadian analysis - matches BehaviorAnalysisAgent.analyze() signature
        """
        try:
            # Extract context data
            biomarker_data = enhanced_context.get("user_context", {})
            archetype = enhanced_context.get("archetype", "Foundation Builder")
            memory_context = enhanced_context.get("memory_context", {})

            logger.debug(f"Starting circadian analysis for archetype: {archetype}")

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
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            # Parse AI response
            ai_analysis = json.loads(response.choices[0].message.content)

            logger.debug("AI analysis completed successfully")

            # Add metadata (matches existing pattern)
            ai_analysis["analysis_metadata"] = {
                "model_used": self.model,
                "analysis_type": "ai_powered_circadian",
                "token_usage": response.usage.total_tokens if response.usage else 0,
                "analysis_timestamp": datetime.now().isoformat(),
                "data_quality": self._assess_data_quality(biomarker_data)
            }

            return ai_analysis

        except Exception as e:
            logger.error(f"Error in circadian analysis: {e}")
            # Return error structure matching existing pattern
            return {
                "chronotype_assessment": {
                    "primary_type": "unknown",
                    "confidence_score": 0.0,
                    "supporting_evidence": [f"Analysis failed: {str(e)}"]
                },
                "energy_zone_analysis": {
                    "peak_windows": [],
                    "productive_windows": [],
                    "maintenance_windows": [],
                    "recovery_windows": []
                },
                "schedule_recommendations": {
                    "optimal_daily_structure": {},
                    "weekly_optimization": {},
                    "archetype_customization": {"archetype": archetype}
                },
                "biomarker_insights": {
                    "sleep_pattern_analysis": {},
                    "hrv_trend_analysis": {},
                    "activity_rhythm_analysis": {},
                    "circadian_health_score": 0
                },
                "integration_recommendations": {
                    "for_routine_agent": {},
                    "for_behavior_agent": {}
                },
                "analysis_metadata": {
                    "analysis_type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }

    def _get_circadian_system_prompt(self, archetype: str) -> str:
        """Get specialized system prompt for circadian analysis"""
        return f"""You are a specialized Circadian Rhythm and Energy Optimization AI agent for the HolisticOS health system.

Your role is to analyze biomarker data (sleep patterns, HRV, activity rhythms, recovery metrics) and provide comprehensive circadian rhythm insights and energy zone recommendations.

## USER ARCHETYPE: {archetype}
Tailor your analysis and recommendations to this archetype's optimization style and preferences:

- Foundation Builder: Simple, sustainable basics - focus on consistent patterns
- Transformation Seeker: Ambitious lifestyle changes - provide detailed optimization
- Systematic Improver: Methodical, evidence-based - include data rationale
- Peak Performer: Elite-level optimization - advanced biohacking insights
- Resilience Rebuilder: Recovery focus - prioritize restoration
- Connected Explorer: Social/adventure oriented - flexible scheduling

## ANALYSIS REQUIREMENTS:

1. **Chronotype Assessment**: Determine user's natural chronotype based on sleep timing, activity patterns, and biomarker rhythms. Use categories: extreme_morning, moderate_morning, intermediate, moderate_evening, extreme_evening

2. **Energy Zone Mapping**: Identify specific time windows for:
   - Peak performance windows (highest cognitive and physical capacity)
   - Productive windows (sustained moderate-high performance)
   - Maintenance windows (routine tasks, social activities)
   - Recovery windows (rest, restoration, wind-down)

3. **Schedule Optimization**: Provide timing recommendations for work, exercise, meals, and sleep based on circadian patterns

4. **Biomarker Integration**: Analyze HRV trends, sleep quality patterns, recovery indicators, and activity rhythms

5. **Integration Guidelines**: Provide specific recommendations for routine and behavior agents to consume

## RESPONSE FORMAT:
Respond with valid JSON containing these exact sections:
- chronotype_assessment
- energy_zone_analysis
- schedule_recommendations
- biomarker_insights
- integration_recommendations

Focus on actionable, evidence-based recommendations derived from the biomarker patterns you observe. Include confidence scores (0.0-1.0) for all assessments."""

    def _prepare_analysis_prompt(self, biomarker_data: Dict, memory_context: Dict, archetype: str) -> str:
        """Prepare comprehensive prompt for AI analysis"""
        return f"""Analyze this biomarker data for comprehensive circadian rhythm and energy optimization insights:

## BIOMARKER DATA:
{json.dumps(biomarker_data, indent=2)}

## MEMORY CONTEXT (Previous Patterns):
{json.dumps(memory_context, indent=2)}

## USER PROFILE:
- Archetype: {archetype}
- Analysis Timestamp: {datetime.now().isoformat()}

## ANALYSIS REQUEST:

Please provide a comprehensive JSON analysis including:

1. **chronotype_assessment**: {{
   "primary_type": "moderate_morning|intermediate|etc",
   "confidence_score": 0.0-1.0,
   "supporting_evidence": ["evidence1", "evidence2"]
}}

2. **energy_zone_analysis**: {{
   "peak_windows": [{{
     "time_range": "09:00-11:00",
     "energy_level": 85,
     "confidence": 0.8,
     "optimal_activities": ["complex_cognitive_work", "strategic_planning"],
     "biomarker_support": "explanation"
   }}],
   "productive_windows": [...],
   "maintenance_windows": [...],
   "recovery_windows": [...]
}}

3. **schedule_recommendations**: {{
   "optimal_daily_structure": {{
     "wake_window": {{"ideal_time": "07:00", "acceptable_range": "06:30-07:30"}},
     "peak_performance_blocks": [...],
     "exercise_timing": {{...}},
     "meal_timing": {{...}},
     "evening_wind_down": {{...}}
   }},
   "weekly_optimization": {{...}},
   "archetype_customization": {{...}}
}}

4. **biomarker_insights**: {{
   "sleep_pattern_analysis": {{...}},
   "hrv_trend_analysis": {{...}},
   "activity_rhythm_analysis": {{...}},
   "circadian_health_score": 0-100,
   "improvement_opportunities": [...]
}}

5. **integration_recommendations**: {{
   "for_routine_agent": {{
     "exercise_timing_windows": [...],
     "activity_intensity_by_time": {{...}},
     "recovery_prioritization": {{...}}
   }},
   "for_behavior_agent": {{
     "habit_timing_optimization": [...],
     "energy_aware_goal_setting": {{...}}
   }}
}}

Base your analysis on the actual biomarker patterns you observe. If data is limited, indicate lower confidence scores and suggest improvements."""

    def _assess_data_quality(self, biomarker_data: Dict) -> str:
        """Assess quality of available biomarker data"""
        try:
            sahha_data = biomarker_data.get("sahha_biomarkers", {})
            sleep_count = len(sahha_data.get("sleep", []))
            activity_count = len(sahha_data.get("activity", []))
            body_metrics_count = len(sahha_data.get("body_metrics", []))

            total_data_points = sleep_count + activity_count + body_metrics_count

            if total_data_points >= 20 and sleep_count >= 7:
                return "excellent"
            elif total_data_points >= 10 and sleep_count >= 3:
                return "good"
            elif total_data_points >= 5:
                return "limited"
            else:
                return "insufficient"
        except Exception as e:
            logger.error(f"Error assessing data quality: {e}")
            return "unknown"

    def get_available_archetypes(self) -> list:
        """Get available archetypes for validation"""
        return [
            "Foundation Builder",
            "Transformation Seeker",
            "Systematic Improver",
            "Peak Performer",
            "Resilience Rebuilder",
            "Connected Explorer"
        ]