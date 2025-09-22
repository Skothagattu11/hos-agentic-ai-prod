"""
AI-Powered Energy Zones Service

Uses GPT-4o to analyze real health data and generate personalized energy zones.
Single comprehensive AI call replaces rule-based logic.
"""

import os
import json
import logging
from datetime import datetime, date, time, timedelta
from typing import List, Tuple, Any, Dict
from pathlib import Path
import openai

from services.user_data_service import UserDataService
from shared_libs.data_models.user_health_context import UserHealthContext
from shared_libs.data_models.energy_zones_models import (
    EnergyZonesResult, EnergyZone, SleepSchedule, BiomarkerSnapshot,
    IntensityLevel, ModeType, ChronotypeCategory
)

logger = logging.getLogger(__name__)


class AIEnergyZonesService:
    """
    AI-powered energy zones service using GPT-4o for comprehensive analysis.

    Single AI call analyzes health data and generates:
    1. Personalized sleep schedule
    2. Current energy mode
    3. Customized energy zones throughout the day
    """

    def __init__(self, user_data_service: UserDataService):
        self.user_data_service = user_data_service
        self.openai_client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

    async def calculate_energy_zones(self, user_id: str, force_recalculate: bool = False) -> EnergyZonesResult:
        """
        Main method: AI-powered energy zones calculation using single comprehensive analysis
        """
        try:
            # Get raw health data (same as behavior analysis)
            health_context, latest_timestamp = await self.user_data_service.get_analysis_data(user_id)

            if not health_context or not health_context.scores:
                return self._create_default_zones(user_id)

            # Single comprehensive AI analysis
            analysis_result = await self._ai_comprehensive_analysis(health_context)

            # Create final result
            result = EnergyZonesResult(
                user_id=user_id,
                calculation_date=date.today(),
                detected_mode=analysis_result["detected_mode"],
                sleep_schedule=analysis_result["sleep_schedule"],
                energy_zones=analysis_result["energy_zones"],
                confidence_score=analysis_result["confidence_score"],
                biomarker_snapshot=self._create_biomarker_snapshot(health_context),
                generated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24)
            )

            return result

        except Exception as e:
            logger.error(f"AI energy zones calculation failed: {e}")
            return self._create_default_zones(user_id)

    async def _ai_comprehensive_analysis(self, health_context: UserHealthContext) -> Dict[str, Any]:
        """
        Single comprehensive AI call to analyze health data and generate complete energy profile
        """
        try:
            # Prepare health data summary
            sleep_scores = [s for s in health_context.scores if 'sleep' in s.type.lower()]
            activity_scores = [s for s in health_context.scores if 'activity' in s.type.lower()]
            readiness_scores = [s for s in health_context.scores if 'readiness' in s.type.lower()]
            wellbeing_scores = [s for s in health_context.scores if 'wellbeing' in s.type.lower()]

            # Calculate recent averages
            recent_metrics = {
                "sleep": {
                    "scores": [s.score for s in sleep_scores[-3:]],
                    "average": sum([s.score for s in sleep_scores[-5:]]) / len(sleep_scores[-5:]) if sleep_scores else 0
                },
                "activity": {
                    "scores": [s.score for s in activity_scores[-3:]],
                    "average": sum([s.score for s in activity_scores[-5:]]) / len(activity_scores[-5:]) if activity_scores else 0
                },
                "readiness": {
                    "scores": [s.score for s in readiness_scores[-3:]],
                    "average": sum([s.score for s in readiness_scores[-5:]]) / len(readiness_scores[-5:]) if readiness_scores else 0
                },
                "wellbeing": {
                    "scores": [s.score for s in wellbeing_scores[-3:]],
                    "average": sum([s.score for s in wellbeing_scores[-5:]]) / len(wellbeing_scores[-5:]) if wellbeing_scores else 0
                }
            }

            prompt = f"""
            Analyze this user's health data to create a comprehensive personalized energy profile:

            Health Metrics Summary:
            {json.dumps(recent_metrics, indent=2)}

            Data Quality: {health_context.data_quality.completeness_score:.2f}
            Total Data Points: {len(health_context.scores)} scores, {len(health_context.biomarkers)} biomarkers

            Create a complete energy optimization profile including:

            1. **Sleep Schedule Analysis**:
               - Optimal wake time and bedtime based on sleep quality patterns
               - Chronotype identification (morning/neutral/evening person)
               - Sleep schedule confidence based on data consistency

            2. **Energy Mode Detection**:
               - Current energy state: RECOVERY (needs rest), PRODUCTIVE (balanced), or PERFORMANCE (high energy)
               - Based on readiness scores, sleep quality, and activity patterns

            3. **Personalized Energy Zones** (6-8 zones throughout the day):
               - Meaningful zone names (e.g., "Morning Peak", "Focus Flow", "Afternoon Recharge")
               - Precise timing based on circadian rhythms and personal patterns
               - Intensity levels: "low", "medium", or "high"
               - Optimal activities for each zone
               - Energy descriptions

            Consider:
            - Sleep scores indicate sleep quality patterns
            - Readiness scores show recovery and energy availability
            - Activity scores reveal movement and exercise patterns
            - Morning peak typically 1-3 hours after waking
            - Afternoon energy dip around 2-4 PM
            - Evening wind-down before sleep

            Respond with JSON in this exact format:
            {{
                "sleep_schedule": {{
                    "wake_time": "07:00:00",
                    "sleep_time": "23:00:00",
                    "chronotype": "morning|neutral|evening",
                    "confidence_score": 0.85
                }},
                "energy_mode": {{
                    "mode": "recovery|productive|performance",
                    "confidence": 0.85
                }},
                "energy_zones": [
                    {{
                        "name": "Morning Peak",
                        "start_time": "07:30:00",
                        "end_time": "10:00:00",
                        "intensity_level": "high",
                        "optimal_activities": "Complex tasks, important decisions, creative work",
                        "energy_description": "Peak mental clarity and focus"
                    }}
                ],
                "overall_confidence": 0.85
            }}
            """

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an energy optimization expert. Analyze health data and create personalized energy profiles. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            ai_response_text = response.choices[0].message.content

            # Clean up markdown code blocks if present
            if "```json" in ai_response_text:
                ai_response_text = ai_response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_response_text:
                ai_response_text = ai_response_text.split("```")[1].split("```")[0].strip()

            ai_response = json.loads(ai_response_text)

            # Convert AI response to objects
            sleep_data = ai_response["sleep_schedule"]
            sleep_schedule = SleepSchedule(
                estimated_wake_time=time.fromisoformat(sleep_data["wake_time"]),
                estimated_bedtime=time.fromisoformat(sleep_data["sleep_time"]),
                chronotype=self._map_chronotype(sleep_data["chronotype"]),
                confidence_score=sleep_data["confidence_score"],
                data_sources=["ai_analysis"],
                inference_date=date.today()
            )

            mode_data = ai_response["energy_mode"]
            detected_mode = self._map_mode(mode_data["mode"])

            # Convert energy zones
            energy_zones = []
            for zone_data in ai_response["energy_zones"]:
                try:
                    zone = EnergyZone(
                        name=zone_data["name"],
                        start_time=time.fromisoformat(zone_data["start_time"]),
                        end_time=time.fromisoformat(zone_data["end_time"]),
                        intensity_level=self._map_intensity(zone_data["intensity_level"]),
                        optimal_activities=zone_data.get("optimal_activities", ""),
                        energy_description=zone_data.get("energy_description", "")
                    )
                    energy_zones.append(zone)
                except Exception:
                    continue

            return {
                "sleep_schedule": sleep_schedule,
                "detected_mode": detected_mode,
                "energy_zones": energy_zones,
                "confidence_score": ai_response.get("overall_confidence", 0.8)
            }

        except Exception as e:
            logger.error(f"AI comprehensive analysis failed: {e}")
            return self._create_fallback_analysis()

    def _map_chronotype(self, chronotype_str: str) -> ChronotypeCategory:
        """Map string to chronotype enum"""
        mapping = {
            "morning": ChronotypeCategory.MORNING_LARK,
            "evening": ChronotypeCategory.EVENING_OWL,
            "neutral": ChronotypeCategory.NEUTRAL
        }
        return mapping.get(chronotype_str, ChronotypeCategory.NEUTRAL)

    def _map_mode(self, mode_str: str) -> ModeType:
        """Map string to mode enum"""
        mapping = {
            "recovery": ModeType.RECOVERY,
            "productive": ModeType.PRODUCTIVE,
            "performance": ModeType.PERFORMANCE
        }
        return mapping.get(mode_str, ModeType.PRODUCTIVE)

    def _map_intensity(self, intensity_str: str) -> IntensityLevel:
        """Map string to intensity enum"""
        mapping = {
            "low": IntensityLevel.LOW,
            "medium": IntensityLevel.MEDIUM,
            "high": IntensityLevel.HIGH
        }
        return mapping.get(intensity_str, IntensityLevel.MEDIUM)

    def _create_biomarker_snapshot(self, health_context: UserHealthContext) -> BiomarkerSnapshot:
        """Create biomarker snapshot from processed health data"""
        sleep_scores = [s.score for s in health_context.scores if 'sleep' in s.type.lower()]
        readiness_scores = [s.score for s in health_context.scores if 'readiness' in s.type.lower()]
        activity_scores = [s.score for s in health_context.scores if 'activity' in s.type.lower()]

        return BiomarkerSnapshot(
            sleep_score=sleep_scores[-1] if sleep_scores else 0.0,
            readiness_score=readiness_scores[-1] if readiness_scores else 0.0,
            activity_score=activity_scores[-1] if activity_scores else 0.0,
            timestamp=datetime.now()
        )

    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """Create fallback analysis when AI fails"""
        return {
            "sleep_schedule": SleepSchedule(
                estimated_wake_time=time(7, 0),
                estimated_bedtime=time(23, 0),
                chronotype=ChronotypeCategory.NEUTRAL,
                confidence_score=0.5,
                data_sources=["fallback"],
                inference_date=date.today()
            ),
            "detected_mode": ModeType.PRODUCTIVE,
            "energy_zones": self._create_default_energy_zones(),
            "confidence_score": 0.5
        }

    def _create_default_energy_zones(self) -> List[EnergyZone]:
        """Create default energy zones"""
        return [
            EnergyZone(
                name="Morning Start",
                start_time=time(7, 0),
                end_time=time(9, 0),
                intensity_level=IntensityLevel.MEDIUM,
                optimal_activities="Light tasks, planning",
                energy_description="Gentle energy building"
            ),
            EnergyZone(
                name="Mid-Morning Focus",
                start_time=time(9, 0),
                end_time=time(12, 0),
                intensity_level=IntensityLevel.HIGH,
                optimal_activities="Important work, complex tasks",
                energy_description="Peak cognitive performance"
            ),
            EnergyZone(
                name="Afternoon Maintenance",
                start_time=time(13, 0),
                end_time=time(17, 0),
                intensity_level=IntensityLevel.MEDIUM,
                optimal_activities="Routine tasks, meetings",
                energy_description="Steady productive work"
            ),
            EnergyZone(
                name="Evening Wind-down",
                start_time=time(19, 0),
                end_time=time(22, 0),
                intensity_level=IntensityLevel.LOW,
                optimal_activities="Relaxation, light activities",
                energy_description="Preparation for rest"
            )
        ]

    def _create_default_zones(self, user_id: str) -> EnergyZonesResult:
        """Create default zones result when no data available"""
        fallback = self._create_fallback_analysis()

        return EnergyZonesResult(
            user_id=user_id,
            calculation_date=date.today(),
            detected_mode=fallback["detected_mode"],
            sleep_schedule=fallback["sleep_schedule"],
            energy_zones=fallback["energy_zones"],
            confidence_score=fallback["confidence_score"],
            biomarker_snapshot=BiomarkerSnapshot(
                sleep_score=0.0,
                readiness_score=0.0,
                activity_score=0.0,
                timestamp=datetime.now()
            ),
            generated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24)
        )