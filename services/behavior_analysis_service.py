"""
Behavior Analysis Service - AI-Powered Behavioral Pattern Analysis
Enhanced with Direct Sahha Integration (MVP Style)

Features:
- Direct Sahha API calls (with watermark for incremental sync)
- Automatic fallback to Supabase if Sahha fails
- Background archival (non-blocking)
- Backward compatible (existing analyze() method still works)
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class BehaviorAnalysisService:
    """
    AI-powered behavior analysis service using OpenAI models
    Enhanced with direct Sahha integration (MVP-style: simple, clean, pragmatic)
    """

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # UPDATED: Use gpt-4o for fast behavioral analysis (213s with o3 was too slow)
        self.model = "gpt-4o"

        # NEW: Initialize Sahha integration (lazy load to avoid circular imports)
        self.sahha_service = None
        self.use_sahha_direct = os.getenv("USE_SAHHA_DIRECT", "true").lower() == "true"

        logger.debug(f"BehaviorAnalysisService initialized (Model: {self.model}, Sahha direct: {self.use_sahha_direct})")

    async def analyze(
        self,
        enhanced_context: Dict[str, Any],
        user_id: Optional[str] = None,
        archetype: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        AI-powered behavior analysis - Enhanced with direct Sahha integration

        NEW: If user_id + archetype provided → uses direct Sahha fetch
        OLD: If only enhanced_context → uses Supabase (backward compatible)

        Args:
            enhanced_context: Context dict (memory, etc.)
            user_id: User identifier (NEW - enables Sahha direct fetch)
            archetype: Archetype name (NEW - for watermark tracking)
        """

        # NEW FLOW: Direct Sahha Integration
        if self.use_sahha_direct and user_id and archetype:
            logger.info(f"[BEHAVIOR_SAHHA] Using direct Sahha fetch for {user_id[:8]}...")
            try:
                return await self._analyze_with_sahha(enhanced_context, user_id, archetype)
            except Exception as e:
                logger.error(f"[BEHAVIOR_SAHHA] Failed: {e}, falling back to Supabase")
                # Fall through to old flow

        # OLD FLOW: Supabase-based (fallback or if Sahha disabled)
        logger.debug("[BEHAVIOR_SUPABASE] Using Supabase data (fallback or disabled)")
        return await self._analyze_legacy(enhanced_context)

    async def _analyze_with_sahha(
        self,
        enhanced_context: Dict[str, Any],
        user_id: str,
        archetype: str
    ) -> Dict[str, Any]:
        """
        NEW: Analyze with direct Sahha fetch (incremental sync with watermark)
        """
        try:
            # Lazy load services (avoid circular imports)
            if not self.sahha_service:
                from services.sahha_data_service import get_sahha_data_service
                from services.archetype_analysis_tracker import get_archetype_tracker
                self.sahha_service = get_sahha_data_service()
                self.archetype_tracker = await get_archetype_tracker()

            # Get watermark for incremental fetch
            watermark, source = await self.archetype_tracker.get_last_analysis_date_with_fallback(
                user_id, archetype, "behavior_analysis"
            )
            logger.debug(f"[BEHAVIOR_SAHHA] Watermark: {watermark} (source: {source})")

            # Fetch from Sahha (incremental if watermark exists)
            health_context = await self.sahha_service.fetch_health_data_for_analysis(
                user_id=user_id,
                archetype=archetype,
                analysis_type="behavior_analysis",
                watermark=watermark,
                days=3 if not watermark else 2  # 3 days initial, 2 days follow-up (reduced to minimize tokens)
            )

            # Check if we got data
            if health_context.data_quality.quality_level == "insufficient":
                logger.warning(f"[BEHAVIOR_SAHHA] Insufficient data, falling back to Supabase")
                return await self._analyze_legacy(enhanced_context)

            # Update enhanced_context with fresh Sahha data
            enhanced_context["user_context"] = {
                "sahha_biomarkers": self._format_biomarkers(health_context),
                "sahha_scores": self._format_scores(health_context)
            }

            # Run analysis with Sahha data
            result = await self._analyze_legacy(enhanced_context)

            # Update tracking timestamp
            await self.archetype_tracker.update_last_analysis_date(
                user_id, archetype, datetime.now(), "behavior_analysis"
            )

            logger.info(f"[BEHAVIOR_SAHHA] Analysis completed for {user_id[:8]}...")
            return result

        except Exception as e:
            logger.error(f"[BEHAVIOR_SAHHA] Error: {e}")
            raise  # Let caller handle fallback

    async def _analyze_legacy(self, enhanced_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        OLD: Original Supabase-based analysis (preserved for fallback)
        """
        try:
            # Extract context data
            biomarker_data = enhanced_context.get("user_context", {})
            archetype = enhanced_context.get("archetype", "Foundation Builder")
            memory_context = enhanced_context.get("memory_context", {})

            logger.debug(f"Starting behavior analysis for archetype: {archetype}")

            # Get specialized system prompt
            system_prompt = self._get_behavior_system_prompt(archetype)

            # Prepare AI analysis prompt
            user_prompt = self._prepare_analysis_prompt(biomarker_data, memory_context, archetype)

            # Call OpenAI for intelligent analysis
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Restored for gpt-4o
                max_tokens=8000,  # Increased for comprehensive analysis
                response_format={"type": "json_object"}
            )

            # Parse AI response
            ai_analysis = json.loads(response.choices[0].message.content)

            logger.debug("AI behavior analysis completed successfully")

            # Add metadata (matches existing pattern)
            ai_analysis["analysis_metadata"] = {
                "model_used": self.model,
                "analysis_type": "ai_powered_behavior",
                "token_usage": response.usage.total_tokens if response.usage else 0,
                "analysis_timestamp": datetime.now().isoformat(),
                "data_quality": self._assess_data_quality(biomarker_data)
            }

            return ai_analysis

        except Exception as e:
            logger.error(f"Error in behavior analysis: {e}")
            # Return error structure matching existing pattern
            return {
                "behavioral_signature": {
                    "primary_motivation": "unknown",
                    "consistency_score": 0.0,
                    "behavioral_patterns": []
                },
                "sophistication_assessment": {
                    "score": 0,
                    "category": "Unknown",
                    "readiness_indicators": []
                },
                "habit_analysis": {
                    "established_habits": [],
                    "emerging_patterns": [],
                    "friction_points": []
                },
                "motivation_profile": {
                    "primary_drivers": [],
                    "engagement_style": "unknown",
                    "barrier_patterns": []
                },
                "personalized_strategy": {
                    "recommended_approach": "Unable to analyze",
                    "habit_integration_method": "unknown",
                    "motivation_tactics": []
                },
                "integration_recommendations": {
                    "for_routine_agent": {},
                    "for_nutrition_agent": {}
                },
                "analysis_metadata": {
                    "analysis_type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }

    def _get_behavior_system_prompt(self, archetype: str) -> str:
        """Get specialized system prompt for behavior analysis"""
        return f"""You are a specialized Behavioral Pattern Analysis AI agent for the HolisticOS health system.

Your role is to analyze biomarker data (activity patterns, sleep consistency, heart rate variability, recovery metrics) and provide comprehensive behavioral insights and personalized strategy recommendations.

## USER ARCHETYPE: {archetype}
Tailor your analysis and recommendations to this archetype's behavioral profile and preferences:

- Foundation Builder: Simple, sustainable basics - focus on consistent patterns and achievable habits
- Transformation Seeker: Ambitious lifestyle changes - identify readiness and motivation drivers
- Systematic Improver: Methodical, evidence-based - provide data-driven behavioral insights
- Peak Performer: Elite-level optimization - analyze advanced behavioral patterns and performance psychology
- Resilience Rebuilder: Recovery focus - assess stress patterns and restoration behaviors
- Connected Explorer: Social/adventure oriented - evaluate social engagement and variety-seeking patterns

## ANALYSIS REQUIREMENTS:

1. **Behavioral Signature**: Identify user's primary behavioral patterns based on activity consistency, sleep regularity, and recovery patterns. Assess motivation type (intrinsic/extrinsic), consistency score (0.0-1.0), and behavioral stability.

2. **Sophistication Assessment**: Determine user's health sophistication level (0-100 score):
   - Novice (0-30): Inconsistent patterns, reactive approach
   - Intermediate (31-60): Building consistency, learning phase
   - Advanced (61-80): Strong patterns, proactive approach
   - Expert (81-100): Optimized behaviors, performance-focused

3. **Habit Analysis**: Evaluate established habits, emerging patterns, and friction points based on biomarker consistency

4. **Motivation Profile**: Identify primary motivation drivers, engagement style, and potential barriers

5. **Personalized Strategy**: Provide specific recommendations for habit formation, motivation tactics, and barrier mitigation tailored to archetype

6. **Integration Guidelines**: Provide specific recommendations for routine and nutrition agents to consume

## RESPONSE FORMAT:
Respond with valid JSON containing these exact sections:
- behavioral_signature
- sophistication_assessment
- habit_analysis
- motivation_profile
- personalized_strategy
- integration_recommendations

Focus on actionable, evidence-based recommendations derived from the behavioral patterns you observe in the biomarker data. Include confidence scores (0.0-1.0) for all assessments."""

    def _prepare_analysis_prompt(self, biomarker_data: Dict, memory_context: Dict, archetype: str) -> str:
        """Prepare comprehensive prompt for AI analysis"""
        return f"""Analyze this biomarker data for comprehensive behavioral pattern analysis and personalized strategy recommendations:

## BIOMARKER DATA:
{json.dumps(biomarker_data, indent=2)}

## MEMORY CONTEXT (Previous Patterns):
{json.dumps(memory_context, indent=2)}

## USER PROFILE:
- Archetype: {archetype}
- Analysis Timestamp: {datetime.now().isoformat()}

## ANALYSIS REQUEST:

Please provide a comprehensive JSON analysis including:

1. **behavioral_signature**: {{
   "primary_motivation": "intrinsic|extrinsic|mixed",
   "consistency_score": 0.0-1.0,
   "behavioral_patterns": [
     {{
       "pattern_type": "sleep|activity|recovery|nutrition",
       "consistency": 0.0-1.0,
       "trend": "improving|stable|declining",
       "evidence": "explanation based on biomarkers"
     }}
   ],
   "signature_summary": "overall behavioral profile description"
}}

2. **sophistication_assessment**: {{
   "score": 0-100,
   "category": "Novice|Intermediate|Advanced|Expert",
   "level": "beginner|intermediate|advanced|expert",
   "readiness_indicators": [
     {{
       "indicator": "consistency|awareness|proactivity|optimization",
       "present": true|false,
       "evidence": "biomarker-based evidence"
     }}
   ],
   "growth_potential": "assessment of potential for improvement"
}}

3. **habit_analysis**: {{
   "established_habits": [
     {{
       "habit": "description",
       "strength": 0.0-1.0,
       "frequency": "daily|weekly|occasional",
       "biomarker_support": "evidence from data"
     }}
   ],
   "emerging_patterns": [
     {{
       "pattern": "description",
       "maturity": 0.0-1.0,
       "direction": "strengthening|weakening",
       "recommendation": "how to reinforce or modify"
     }}
   ],
   "friction_points": [
     {{
       "friction": "description of barrier",
       "impact": "high|medium|low",
       "mitigation_strategy": "specific recommendation"
     }}
   ]
}}

4. **motivation_profile**: {{
   "primary_drivers": ["achievement", "health", "performance", "social", "appearance"],
   "engagement_style": "goal_oriented|process_oriented|socially_driven|data_driven",
   "response_to_setbacks": "resilient|adaptive|discouraged",
   "barrier_patterns": [
     {{
       "barrier": "description",
       "frequency": "common|occasional|rare",
       "override_strategy": "specific recommendation"
     }}
   ],
   "optimal_motivation_tactics": ["tactic1", "tactic2"]
}}

5. **personalized_strategy**: {{
   "recommended_approach": "detailed strategy description",
   "habit_integration_method": "stacking|replacement|addition|optimization",
   "motivation_tactics": [
     {{
       "tactic": "specific tactic",
       "when_to_use": "context for application",
       "expected_effectiveness": 0.0-1.0
     }}
   ],
   "barrier_mitigation": [
     {{
       "barrier": "identified barrier",
       "mitigation": "specific strategy",
       "implementation": "how to apply"
     }}
   ],
   "archetype_customization": {{
     "archetype_specific_recommendations": "tailored to {archetype}",
     "style_adaptations": "how to adapt general recommendations"
   }}
}}

6. **integration_recommendations**: {{
   "for_routine_agent": {{
     "habit_timing_preferences": ["morning|afternoon|evening routines"],
     "consistency_level_required": "high|medium|low",
     "progression_pace": "aggressive|moderate|gentle",
     "recovery_emphasis": 0.0-1.0
   }},
   "for_nutrition_agent": {{
     "behavioral_eating_patterns": ["pattern1", "pattern2"],
     "meal_timing_consistency": 0.0-1.0,
     "nutrition_sophistication": "basic|intermediate|advanced",
     "adherence_predictors": ["predictor1", "predictor2"]
   }}
}}

Base your analysis on the actual biomarker patterns you observe. Look for:
- Sleep consistency (regularity in sleep/wake times)
- Activity patterns (consistency, intensity, recovery balance)
- Heart rate variability trends (stress management, recovery capacity)
- Recovery patterns (rest days, active recovery, overtraining signs)

If data is limited, indicate lower confidence scores and suggest what additional data would improve accuracy."""

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

    def _format_biomarkers(self, health_context) -> Dict:
        """
        NEW: Format biomarkers from UserHealthContext for behavior analysis
        """
        sleep_bio = []
        activity_bio = []
        vitals_bio = []

        for bio in health_context.biomarkers:
            bio_dict = {
                "type": bio.type,
                "value": bio.data.get("value"),
                "unit": bio.data.get("unit"),
                "start_time": bio.start_date_time.isoformat() if hasattr(bio.start_date_time, 'isoformat') else str(bio.start_date_time),
                "end_time": bio.end_date_time.isoformat() if hasattr(bio.end_date_time, 'isoformat') else str(bio.end_date_time)
            }

            if bio.category == "sleep":
                sleep_bio.append(bio_dict)
            elif bio.category == "activity":
                activity_bio.append(bio_dict)
            elif bio.category == "vitals":
                vitals_bio.append(bio_dict)

        return {
            "sleep": sleep_bio,
            "activity": activity_bio,
            "body_metrics": vitals_bio
        }

    def _format_scores(self, health_context) -> list:
        """
        NEW: Format scores from UserHealthContext for behavior analysis
        """
        return [
            {
                "type": score.type,
                "score": score.score,
                "date": score.score_date_time.isoformat() if hasattr(score.score_date_time, 'isoformat') else str(score.score_date_time)
            }
            for score in health_context.scores
        ]


# Singleton pattern for easy access
_behavior_service_instance = None

def get_behavior_analysis_service() -> BehaviorAnalysisService:
    """Get or create the singleton behavior analysis service"""
    global _behavior_service_instance

    if _behavior_service_instance is None:
        _behavior_service_instance = BehaviorAnalysisService()

    return _behavior_service_instance
