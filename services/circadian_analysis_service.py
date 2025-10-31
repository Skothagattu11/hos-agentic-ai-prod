"""
Circadian Analysis Service - AI-Powered Biomarker Analysis
Enhanced with Direct Sahha Integration (Phase 4 - MVP Style)

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

class CircadianAnalysisService:
    """
    AI-powered circadian rhythm analysis service using OpenAI models
    Enhanced with direct Sahha integration (MVP-style: simple, clean, pragmatic)
    """

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # UPDATED: Use gpt-4o for fast circadian analysis (213s with o3 was too slow)
        self.model = "gpt-4o"

        # NEW: Initialize Sahha integration (lazy load to avoid circular imports)
        self.sahha_service = None
        self.use_sahha_direct = os.getenv("USE_SAHHA_DIRECT", "true").lower() == "true"

        logger.debug(f"CircadianAnalysisService initialized (Model: {self.model}, Sahha direct: {self.use_sahha_direct})")

    async def analyze(
        self,
        enhanced_context: Dict[str, Any],
        user_id: Optional[str] = None,
        archetype: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        AI-powered circadian analysis - Enhanced with direct Sahha integration

        NEW: If user_id + archetype provided  uses direct Sahha fetch
        OLD: If only enhanced_context  uses Supabase (backward compatible)

        Args:
            enhanced_context: Context dict (memory, etc.)
            user_id: User identifier (NEW - enables Sahha direct fetch)
            archetype: Archetype name (NEW - for watermark tracking)
        """

        # NEW FLOW: Direct Sahha Integration
        if self.use_sahha_direct and user_id and archetype:
            logger.info(f"[CIRCADIAN_SAHHA] Using direct Sahha fetch for {user_id[:8]}...")
            try:
                return await self._analyze_with_sahha(enhanced_context, user_id, archetype)
            except Exception as e:
                logger.error(f"[CIRCADIAN_SAHHA] Failed: {e}, falling back to Supabase")
                # Fall through to old flow

        # OLD FLOW: Supabase-based (fallback or if Sahha disabled)
        logger.debug("[CIRCADIAN_SUPABASE] Using Supabase data (fallback or disabled)")
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
                user_id, archetype, "circadian_analysis"
            )
            logger.debug(f"[CIRCADIAN_SAHHA] Watermark: {watermark} (source: {source})")

            # Fetch from Sahha (incremental if watermark exists)
            health_context = await self.sahha_service.fetch_health_data_for_analysis(
                user_id=user_id,
                archetype=archetype,
                analysis_type="circadian_analysis",
                watermark=watermark,
                days=3 if not watermark else 2  # 3 days initial, 2 days follow-up (reduced to minimize tokens)
            )

            # Check if we got data
            if health_context.data_quality.quality_level == "insufficient":
                logger.warning(f"[CIRCADIAN_SAHHA] Insufficient data, falling back to Supabase")
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
                user_id, archetype, datetime.now(), "circadian_analysis"
            )

            logger.info(f"[CIRCADIAN_SAHHA] Analysis completed for {user_id[:8]}...")
            return result

        except Exception as e:
            logger.error(f"[CIRCADIAN_SAHHA] Error: {e}")
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
                temperature=0.7,  # Restored for gpt-4o
                max_tokens=8000,  # Increased for comprehensive analysis
                response_format={"type": "json_object"}
            )

            # Parse AI response
            ai_analysis = json.loads(response.choices[0].message.content)

            logger.debug("AI analysis completed successfully")

            # **NEW: Generate 96-slot energy timeline (FIX #1 - P0)**
            energy_timeline = self._generate_energy_timeline_from_analysis(ai_analysis)
            ai_analysis["energy_timeline"] = energy_timeline

            # **NEW: Add timeline summary and metadata (FIX #1 - P0)**
            ai_analysis["timeline_metadata"] = {
                "total_slots": 96,
                "slot_duration_minutes": 15,
                "interpolation_method": "linear",
                "zone_thresholds": {
                    "peak": 75,
                    "maintenance": 50,
                    "recovery": 50
                }
            }

            # **NEW: Generate human-readable summary**
            ai_analysis["summary"] = self._generate_timeline_summary(energy_timeline)

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

    def _format_biomarkers(self, health_context) -> Dict:
        """
        NEW: Format biomarkers from UserHealthContext for circadian analysis
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
        NEW: Format scores from UserHealthContext for circadian analysis
        """
        return [
            {
                "type": score.type,
                "score": score.score,
                "date": score.score_date_time.isoformat() if hasattr(score.score_date_time, 'isoformat') else str(score.score_date_time)
            }
            for score in health_context.scores
        ]

    def _generate_energy_timeline_from_analysis(self, ai_analysis: Dict[str, Any]) -> list:
        """
        **FIX #1 (P0): Generate 96-slot energy timeline with 15-minute granularity**

        Implements the documented specification from calendar-ui-energyzone-96.md
        Extracts energy windows from AI analysis and interpolates to create continuous timeline.

        Returns: List of 96 time slots with energy levels and zones
        """
        try:
            # Initialize 96 slots (00:00 to 23:45, 15-minute intervals)
            timeline = []
            for i in range(96):
                hour = (i * 15) // 60
                minute = (i * 15) % 60
                timeline.append({
                    "time": f"{hour:02d}:{minute:02d}",
                    "energy_level": 40,  # Default baseline energy
                    "slot_index": i,
                    "zone": "maintenance"
                })

            # Extract energy windows from AI response
            energy_zones = ai_analysis.get("energy_zone_analysis", {})

            # Parse each window type and assign energy levels
            windows_to_process = [
                ("peak_windows", 85, "peak"),
                ("productive_windows", 70, "maintenance"),
                ("maintenance_windows", 55, "maintenance"),
                ("recovery_windows", 30, "recovery")
            ]

            for window_key, energy_level, zone_name in windows_to_process:
                windows = energy_zones.get(window_key, [])
                for window in windows:
                    time_range = window.get("time_range", "")
                    self._apply_energy_window(timeline, time_range, energy_level, zone_name)

            # **FIX #2 (P0): Validate minimum peak energy zones**
            timeline = self._validate_and_fix_peak_zones(timeline)

            # Smooth transitions between zones (linear interpolation)
            timeline = self._smooth_energy_transitions(timeline)

            return timeline

        except Exception as e:
            logger.error(f"Error generating energy timeline: {e}")
            # Return default 24-hour pattern with reasonable energy curve
            return self._get_default_energy_timeline()

    def _apply_energy_window(self, timeline: list, time_range: str, energy_level: int, zone: str):
        """Apply energy level and zone to specified time range"""
        try:
            # Parse time range (e.g., "09:00-11:00" or "8:00 AM - 10:00 AM")
            if not time_range or "-" not in time_range:
                return

            # Clean and split
            time_range = time_range.replace(" AM", "").replace(" PM", "").strip()
            parts = time_range.split("-")
            if len(parts) != 2:
                return

            start_time, end_time = parts[0].strip(), parts[1].strip()

            # Convert to 24-hour format and get slot indices
            start_slot = self._time_to_slot_index(start_time)
            end_slot = self._time_to_slot_index(end_time)

            if start_slot is None or end_slot is None:
                return

            # Apply energy level and zone to all slots in range
            for i in range(start_slot, min(end_slot + 1, 96)):
                timeline[i]["energy_level"] = energy_level
                timeline[i]["zone"] = zone

        except Exception as e:
            logger.warning(f"Could not parse time range '{time_range}': {e}")

    def _time_to_slot_index(self, time_str: str) -> Optional[int]:
        """Convert time string (HH:MM) to slot index (0-95)"""
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return None

            hour = int(parts[0])
            minute = int(parts[1])

            # Calculate slot index (each slot is 15 minutes)
            slot = (hour * 60 + minute) // 15
            return min(max(slot, 0), 95)  # Clamp to valid range

        except Exception as e:
            logger.warning(f"Could not convert time '{time_str}' to slot: {e}")
            return None

    def _validate_and_fix_peak_zones(self, timeline: list) -> list:
        """
        **FIX #2 (P0): Ensure minimum peak energy zones are assigned**

        Analysis shows 0% peak zones - this fixes it by ensuring minimum coverage.
        """
        MIN_PEAK_SLOTS = 8  # Minimum 2 hours of peak energy (8 x 15min slots)

        # Count existing peak zones
        peak_count = sum(1 for slot in timeline if slot["zone"] == "peak")

        if peak_count >= MIN_PEAK_SLOTS:
            return timeline  # Already has enough peak zones

        logger.info(f"[CIRCADIAN_FIX] Only {peak_count} peak slots found, enforcing minimum {MIN_PEAK_SLOTS}")

        # Force assign peak zones during typical high-energy hours (9 AM - 12 PM)
        # Slot indices: 9 AM = 36, 12 PM = 48
        target_start = 36  # 9:00 AM
        slots_needed = MIN_PEAK_SLOTS - peak_count

        for i in range(target_start, min(target_start + slots_needed, 48)):
            if timeline[i]["zone"] != "peak":
                timeline[i]["zone"] = "peak"
                timeline[i]["energy_level"] = max(timeline[i]["energy_level"], 75)

        return timeline

    def _smooth_energy_transitions(self, timeline: list) -> list:
        """Apply linear interpolation to smooth energy transitions between zones"""
        for i in range(1, len(timeline) - 1):
            prev_energy = timeline[i-1]["energy_level"]
            curr_energy = timeline[i]["energy_level"]
            next_energy = timeline[i+1]["energy_level"]

            # If current slot is very different from neighbors, smooth it
            if abs(curr_energy - prev_energy) > 30 or abs(curr_energy - next_energy) > 30:
                # Average with neighbors for smooth transition
                timeline[i]["energy_level"] = int((prev_energy + curr_energy + next_energy) / 3)

        return timeline

    def _get_default_energy_timeline(self) -> list:
        """Return default energy pattern when analysis fails"""
        timeline = []
        for i in range(96):
            hour = (i * 15) // 60
            minute = (i * 15) % 60

            # Default energy pattern based on typical circadian rhythm
            if 0 <= hour < 6:  # Late night - recovery
                energy = 25
                zone = "recovery"
            elif 6 <= hour < 9:  # Morning - rising energy
                energy = 50 + (hour - 6) * 10
                zone = "maintenance"
            elif 9 <= hour < 12:  # Morning peak
                energy = 85
                zone = "peak"
            elif 12 <= hour < 14:  # Post-lunch dip
                energy = 55
                zone = "maintenance"
            elif 14 <= hour < 17:  # Afternoon productivity
                energy = 70
                zone = "maintenance"
            elif 17 <= hour < 20:  # Evening decline
                energy = 50
                zone = "maintenance"
            else:  # Night wind-down
                energy = 30
                zone = "recovery"

            timeline.append({
                "time": f"{hour:02d}:{minute:02d}",
                "energy_level": energy,
                "slot_index": i,
                "zone": zone
            })

        return timeline

    def _generate_timeline_summary(self, timeline: list) -> Dict[str, Any]:
        """Generate human-readable summary from energy timeline"""
        peak_minutes = sum(15 for slot in timeline if slot["zone"] == "peak")
        maintenance_minutes = sum(15 for slot in timeline if slot["zone"] == "maintenance")
        recovery_minutes = sum(15 for slot in timeline if slot["zone"] == "recovery")

        # Find peak periods (consecutive peak slots)
        peak_periods = self._extract_time_periods(timeline, "peak")
        maintenance_periods = self._extract_time_periods(timeline, "maintenance")
        recovery_periods = self._extract_time_periods(timeline, "recovery")

        return {
            "peak_energy_periods": peak_periods,
            "maintenance_periods": maintenance_periods,
            "low_energy_periods": recovery_periods,
            "total_peak_minutes": peak_minutes,
            "total_maintenance_minutes": maintenance_minutes,
            "total_recovery_minutes": recovery_minutes
        }

    def _extract_time_periods(self, timeline: list, target_zone: str) -> list:
        """Extract consecutive time periods for a given zone"""
        periods = []
        start_time = None

        for i, slot in enumerate(timeline):
            if slot["zone"] == target_zone:
                if start_time is None:
                    start_time = slot["time"]
            else:
                if start_time is not None:
                    # End of period
                    periods.append(f"{start_time}-{timeline[i-1]['time']}")
                    start_time = None

        # Handle period extending to end of day
        if start_time is not None:
            periods.append(f"{start_time}-23:45")

        return periods