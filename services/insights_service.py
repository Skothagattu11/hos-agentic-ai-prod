"""
InsightsService - Key Insights Extraction
Purpose: Extract 4 actionable insights from behavior and circadian analysis for UI display

Features:
- Extracts strongest behavioral patterns (habits, friction points)
- Identifies optimal circadian windows (peak, recovery)
- Highlights personalization optimizations
- Formats as concise bullet points for user
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class InsightsService:
    """
    Extracts 4 key insights from analysis data for UI display.

    Priority order:
    1. Strongest behavioral pattern (established habit or top friction point)
    2. Primary circadian insight (peak energy or optimal sleep window)
    3. Personalization optimization (based on feedback or patterns)
    4. Actionable recommendation (next step for user)
    """

    def __init__(self):
        logger.info("[InsightsService] Initialized")

    def extract_key_insights(
        self,
        behavior_analysis: Optional[Dict[str, Any]] = None,
        circadian_analysis: Optional[Dict[str, Any]] = None,
        preselected_tasks: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Extract exactly 4 key insights for UI display.

        Args:
            behavior_analysis: Behavior analysis result (optional)
            circadian_analysis: Circadian analysis result (optional)
            preselected_tasks: TaskPreseeder result (optional)

        Returns:
            List of 4 concise insight strings
        """
        insights = []

        try:
            # Insight 1: Strongest behavioral pattern
            if behavior_analysis:
                behavioral_insight = self._extract_behavioral_insight(behavior_analysis)
                if behavioral_insight:
                    insights.append(behavioral_insight)

            # Insight 2: Primary circadian insight
            if circadian_analysis:
                circadian_insight = self._extract_circadian_insight(circadian_analysis)
                if circadian_insight:
                    insights.append(circadian_insight)

            # Insight 3: Feedback-based personalization (PRIORITY)
            if preselected_tasks and preselected_tasks.get('has_sufficient_feedback'):
                # First, try feedback-specific insights (excluded/boosted categories)
                feedback_insight = self._extract_feedback_insight(preselected_tasks)
                if feedback_insight:
                    insights.append(feedback_insight)
                else:
                    # Fallback to general personalization insight
                    personalization_insight = self._extract_personalization_insight(
                        behavior_analysis,
                        preselected_tasks
                    )
                    if personalization_insight:
                        insights.append(personalization_insight)

            # Insight 4: Actionable recommendation
            if behavior_analysis or circadian_analysis:
                recommendation = self._extract_recommendation(
                    behavior_analysis,
                    circadian_analysis
                )
                if recommendation:
                    insights.append(recommendation)

            # Fill with generic insights if needed
            while len(insights) < 4:
                insights.append(self._get_generic_insight(len(insights)))

            # Return exactly 4 insights
            return insights[:4]

        except Exception as e:
            logger.error(f"[InsightsService] Error extracting insights: {e}", exc_info=True)
            return self._get_fallback_insights()

    def _extract_behavioral_insight(self, behavior_analysis: Dict) -> Optional[str]:
        """Extract primary behavioral pattern insight."""
        try:
            habit_analysis = behavior_analysis.get('habit_analysis', {})

            # Check for established habits (positive)
            established_habits = habit_analysis.get('established_habits', [])
            if established_habits:
                strongest = max(established_habits, key=lambda x: x.get('strength', 0))
                strength = strongest.get('strength', 0)
                habit_name = strongest.get('habit', 'routine')

                return f"Strong {habit_name} - maintaining consistency (strength {strength:.1f})"

            # Check for friction points (areas to improve)
            friction_points = habit_analysis.get('friction_points', [])
            if friction_points:
                top_friction = friction_points[0]
                friction_name = top_friction.get('friction', 'challenge')

                return f"Focus area: {friction_name}"

            # Check behavioral signature
            signature = behavior_analysis.get('behavioral_signature', {})
            consistency_score = signature.get('consistency_score', 0)

            if consistency_score > 0.8:
                return f"High behavioral consistency ({int(consistency_score * 100)}%) - strong foundation"
            elif consistency_score < 0.6:
                return f"Building consistency ({int(consistency_score * 100)}%) - focus on routine stability"

            return None

        except Exception as e:
            logger.error(f"[InsightsService] Error extracting behavioral insight: {e}")
            return None

    def _extract_circadian_insight(self, circadian_analysis: Dict) -> Optional[str]:
        """Extract primary circadian insight."""
        try:
            # Check for peak energy windows
            energy_zone_analysis = circadian_analysis.get('energy_zone_analysis', {})
            peak_windows = energy_zone_analysis.get('peak_windows', [])

            if peak_windows:
                peak = peak_windows[0]
                time_range = peak.get('time_range', '')

                return f"Peak focus {time_range} - scheduled complex work here"

            # Check optimal windows from summary
            summary = circadian_analysis.get('summary', {})
            wake_window = summary.get('optimal_wake_window', '')
            sleep_window = summary.get('optimal_sleep_window', '')

            if wake_window and sleep_window:
                # Extract first time from wake window
                wake_time = wake_window.split('-')[0] if '-' in wake_window else wake_window

                return f"Optimal wake {wake_time}, wind-down {sleep_window[:5]}"

            # Check for recovery windows
            recovery_windows = energy_zone_analysis.get('recovery_windows', [])
            if recovery_windows:
                recovery = recovery_windows[0]
                time_range = recovery.get('time_range', '')

                return f"Recovery window {time_range} - light activities recommended"

            return None

        except Exception as e:
            logger.error(f"[InsightsService] Error extracting circadian insight: {e}")
            return None

    def _extract_personalization_insight(
        self,
        behavior_analysis: Optional[Dict],
        preselected_tasks: Dict
    ) -> Optional[str]:
        """Extract personalization optimization insight."""
        try:
            # Check if library tasks were selected
            task_count = len(preselected_tasks.get('preselected_tasks', []))

            if task_count > 0:
                selection_stats = preselected_tasks.get('selection_stats', {})
                feedback_count = selection_stats.get('feedback_available', 0)

                return f"Plan personalized with {task_count} proven tasks from {feedback_count} days of feedback"

            # Check for emerging patterns from behavior
            if behavior_analysis:
                habit_analysis = behavior_analysis.get('habit_analysis', {})
                emerging_patterns = habit_analysis.get('emerging_patterns', [])

                if emerging_patterns:
                    pattern = emerging_patterns[0]
                    pattern_name = pattern.get('pattern', 'behavior pattern')
                    direction = pattern.get('direction', 'developing')

                    return f"Detected {pattern_name} - {direction}, adjusting plan accordingly"

            return None

        except Exception as e:
            logger.error(f"[InsightsService] Error extracting personalization insight: {e}")
            return None

    def _extract_feedback_insight(self, preselected_tasks: Dict) -> Optional[str]:
        """Extract insight from friction analysis (NOT exclusion - we adapt, not remove)."""
        try:
            stats = preselected_tasks.get('selection_stats', {})

            # NEW: Friction-based insights (Atomic Habits approach)
            high_friction = stats.get('high_friction_categories', [])
            low_friction = stats.get('low_friction_categories', [])
            friction_analysis = stats.get('friction_analysis', {})
            feedback_count = stats.get('feedback_count', 0)

            # Priority 1: High friction detected (needs simplification)
            if high_friction:
                high_friction_str = ', '.join(high_friction)
                # Get specific friction score if available
                if friction_analysis and high_friction[0] in friction_analysis:
                    friction_score = friction_analysis[high_friction[0]].get('friction_score', 0)
                    if friction_score > 0.7:
                        return f"Simplified {high_friction_str} tasks to reduce friction - focus on micro-habits to build momentum"
                    else:
                        return f"Adjusting {high_friction_str} approach based on feedback - making it easier while keeping it essential"
                return f"Making {high_friction_str} easier with simplified tasks - small wins build lasting habits"

            # Priority 2: Low friction (success to leverage)
            if low_friction:
                low_friction_str = ', '.join(low_friction)
                return f"Leveraging your {low_friction_str} success - using habit stacking to strengthen other areas"

            # Priority 3: Balanced approach (medium friction)
            if feedback_count >= 3:
                return f"Plan optimized from {feedback_count} days of feedback - adapting difficulty, not content"

            return None

        except Exception as e:
            logger.error(f"[InsightsService] Error extracting feedback insight: {e}")
            return None

    def _extract_recommendation(
        self,
        behavior_analysis: Optional[Dict],
        circadian_analysis: Optional[Dict]
    ) -> Optional[str]:
        """Extract actionable recommendation."""
        try:
            # Check behavior recommendations
            if behavior_analysis:
                integration_recs = behavior_analysis.get('integration_recommendations', {})
                routine_recs = integration_recs.get('for_routine_agent', {})

                consistency_level = routine_recs.get('consistency_level_required', '')
                if consistency_level:
                    return f"Focus on {consistency_level} consistency in morning routines"

                # Check motivation tactics
                personalized_strategy = behavior_analysis.get('personalized_strategy', {})
                motivation_tactics = personalized_strategy.get('motivation_tactics', [])

                if motivation_tactics:
                    tactic = motivation_tactics[0]
                    tactic_name = tactic.get('tactic', 'tracking')
                    when = tactic.get('when_to_use', 'daily')

                    return f"Use {tactic_name} for {when} to boost engagement"

            # Check circadian recommendations
            if circadian_analysis:
                biomarker_insights = circadian_analysis.get('biomarker_insights', {})
                opportunities = biomarker_insights.get('improvement_opportunities', [])

                if opportunities:
                    opportunity = opportunities[0]
                    return opportunity  # Already formatted as string

            return None

        except Exception as e:
            logger.error(f"[InsightsService] Error extracting recommendation: {e}")
            return None

    def _get_generic_insight(self, index: int) -> str:
        """Get generic insight as fallback."""
        generic_insights = [
            "Building your personalized health routine",
            "Tracking patterns to optimize your plan",
            "Plan adapts based on your daily feedback",
            "Consistent completion strengthens recommendations"
        ]

        return generic_insights[index] if index < len(generic_insights) else generic_insights[0]

    def _get_fallback_insights(self) -> List[str]:
        """Return fallback insights when extraction fails."""
        return [
            "Building your personalized health routine",
            "Complete tasks to receive personalized insights",
            "Plan optimizes based on your preferences",
            "Track daily progress for better recommendations"
        ]

    def format_insights_for_ui(self, insights: List[str]) -> Dict[str, Any]:
        """
        Format insights for UI display with metadata.

        Args:
            insights: List of insight strings

        Returns:
            {
                'insights': List[str],
                'count': int,
                'generated_at': str,
                'has_personalization': bool
            }
        """
        return {
            'insights': insights,
            'count': len(insights),
            'generated_at': self._get_timestamp(),
            'has_personalization': any('personalized' in i.lower() for i in insights)
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'


# Singleton instance
_insights_service = None


def get_insights_service() -> InsightsService:
    """Get singleton InsightsService instance."""
    global _insights_service
    if _insights_service is None:
        _insights_service = InsightsService()
    return _insights_service
