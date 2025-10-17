"""
Data Aggregation Service - Phase 1, Sprint 1.1

Responsible for:
- Fetching health data from Sahha API (last 3 days)
- Fetching behavioral data from Supabase (plan completion, check-ins)
- Building comprehensive context for insights generation

Data Sources:
- Health Data: Sahha API (primary) → biomarkers, scores tables (backup)
- Behavioral Data: Supabase → plan_items, user_check_ins, holistic_analysis_results
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class HealthDataWindow:
    """Health metrics for 3-day insights window"""
    user_id: str
    start_date: datetime
    end_date: datetime

    # Sleep metrics
    sleep_duration_avg: Optional[float] = None  # hours
    sleep_quality_avg: Optional[float] = None  # 0-100 score
    sleep_consistency: Optional[float] = None  # variance measure

    # Activity metrics
    steps_avg: Optional[int] = None
    active_minutes_avg: Optional[int] = None
    calories_burned_avg: Optional[int] = None

    # Heart rate metrics
    resting_heart_rate_avg: Optional[int] = None
    heart_rate_variability_avg: Optional[float] = None

    # Energy/readiness scores (from Sahha)
    energy_score_avg: Optional[float] = None  # 0-100
    readiness_score_avg: Optional[float] = None  # 0-100

    # Raw data for detailed analysis
    daily_summaries: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BehaviorDataWindow:
    """Behavioral patterns for 3-day insights window"""
    user_id: str
    start_date: datetime
    end_date: datetime

    # Task completion metrics
    total_tasks: int = 0
    completed_tasks: int = 0
    completion_rate: float = 0.0

    # Task timing patterns
    morning_completion_rate: float = 0.0
    afternoon_completion_rate: float = 0.0
    evening_completion_rate: float = 0.0

    # Check-in data
    avg_energy_level: Optional[float] = None  # 1-10 scale
    avg_mood_level: Optional[float] = None  # 1-10 scale
    avg_stress_level: Optional[float] = None  # 1-10 scale

    # Consistency metrics
    daily_check_in_count: int = 0
    task_consistency_score: Optional[float] = None

    # Raw data for detailed analysis
    task_details: List[Dict[str, Any]] = field(default_factory=list)
    check_in_details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class UserBaselines:
    """30-day rolling baselines for personalization"""
    user_id: str
    calculated_at: datetime
    baseline_period_days: int = 30

    # Sleep baselines
    baseline_sleep_duration: Optional[float] = None
    baseline_sleep_quality: Optional[float] = None

    # Activity baselines
    baseline_steps: Optional[int] = None
    baseline_active_minutes: Optional[int] = None

    # Energy baselines
    baseline_energy_score: Optional[float] = None
    baseline_readiness_score: Optional[float] = None

    # Behavioral baselines
    baseline_completion_rate: Optional[float] = None
    baseline_consistency_score: Optional[float] = None

    # Metadata
    data_points_count: int = 0
    baseline_quality: str = "unknown"  # "excellent", "good", "fair", "poor"


@dataclass
class InsightContext:
    """
    Complete context package for AI insights generation

    This is the primary input to the insights generation engine.
    Contains all data needed to generate personalized, actionable insights.
    """
    user_id: str
    archetype: str  # Peak Performer, Transformation Seeker, Foundation Builder
    generated_at: datetime

    # Time windows
    health_data: HealthDataWindow
    behavior_data: BehaviorDataWindow
    baselines: UserBaselines

    # User profile context
    user_goals: Optional[Dict[str, Any]] = None
    current_phase: Optional[str] = None  # "onboarding", "building", "optimizing"

    # Analysis context from recent behavior analysis
    latest_analysis_summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "user_id": self.user_id,
            "archetype": self.archetype,
            "generated_at": self.generated_at.isoformat(),
            "health_data": self.health_data.__dict__,
            "behavior_data": self.behavior_data.__dict__,
            "baselines": self.baselines.__dict__,
            "user_goals": self.user_goals,
            "current_phase": self.current_phase,
            "latest_analysis_summary": self.latest_analysis_summary
        }


class DataAggregationService:
    """
    Aggregates data from multiple sources to build InsightContext

    Phase 1, Sprint 1.1 Implementation:
    - Fetch 3-day health data from Sahha API
    - Fetch 3-day behavioral data from Supabase
    - Calculate 30-day baselines (or fetch from cache)
    - Build complete InsightContext for AI generation
    """

    def __init__(
        self,
        sahha_data_service=None,
        supabase_adapter=None,
        baseline_service=None
    ):
        """
        Initialize with service dependencies

        Args:
            sahha_data_service: SahhaDataService instance for health data
            supabase_adapter: SupabaseAsyncPGAdapter for behavioral data
            baseline_service: BaselineCalculationService for baseline metrics
        """
        self.sahha_service = sahha_data_service
        self.supabase = supabase_adapter
        self.baseline_service = baseline_service

    async def fetch_health_data(
        self,
        user_id: str,
        days: int = 3
    ) -> HealthDataWindow:
        """
        Fetch health metrics from Sahha API - Same pattern as behavior analysis

        Strategy:
        1. Call fetch_health_data_for_analysis() (gets UserHealthContext)
        2. Extract metrics from UserHealthContext
        3. Calculate averages for insight window
        4. Background archival happens automatically in Sahha service

        Args:
            user_id: User identifier
            days: Number of days to fetch (default: 3 for daily insights)

        Returns:
            HealthDataWindow with aggregated health metrics
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Fetch from Sahha using same method as behavior analysis
        if self.sahha_service:
            try:
                # Fetch health data (returns UserHealthContext)
                health_context = await self.sahha_service.fetch_health_data_for_analysis(
                    user_id=user_id,
                    archetype="Foundation Builder",  # Will be overridden by actual archetype
                    analysis_type="insights_generation",
                    watermark=None,  # No watermark for insights (always fetch last N days)
                    days=days
                )

                # Extract metrics from UserHealthContext
                return self._extract_from_health_context(
                    user_id,
                    health_context,
                    start_date,
                    end_date
                )
            except Exception as e:
                print(f"[INSIGHTS_V2] Sahha fetch failed: {e}")

        # Return empty structure if failed
        return HealthDataWindow(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

    def _extract_from_health_context(
        self,
        user_id: str,
        health_context: Any,
        start_date: datetime,
        end_date: datetime
    ) -> HealthDataWindow:
        """
        Extract metrics from UserHealthContext

        UserHealthContext has:
        - biomarkers: List[BiomarkerData] with type field (sleep, steps, heart_rate, etc)
        - scores: List[HealthScore] with type field (energy, readiness, etc)
        """
        health_window = HealthDataWindow(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

        try:
            # Extract from biomarkers list
            if hasattr(health_context, 'biomarkers') and health_context.biomarkers:
                durations = []
                steps_list = []
                active_mins = []
                calories_list = []
                hr_list = []
                hrv_list = []

                for biomarker in health_context.biomarkers:
                    try:
                        biomarker_type = biomarker.type.lower()
                        data_dict = biomarker.data if hasattr(biomarker, 'data') else {}

                        # Sleep metrics
                        if 'sleep' in biomarker_type:
                            if 'duration' in data_dict:
                                duration_value = float(data_dict['duration'])
                                # Convert minutes to hours if needed
                                duration_hours = duration_value / 60 if duration_value > 24 else duration_value
                                durations.append(duration_hours)

                        # Activity metrics
                        elif 'step' in biomarker_type:
                            if 'value' in data_dict:
                                steps_list.append(int(float(data_dict['value'])))
                        elif 'activity' in biomarker_type or 'active' in biomarker_type:
                            if 'duration' in data_dict:
                                active_mins.append(int(float(data_dict['duration'])))
                            if 'value' in data_dict:
                                active_mins.append(int(float(data_dict['value'])))
                        elif 'calorie' in biomarker_type or 'energy' in biomarker_type:
                            if 'value' in data_dict:
                                calories_list.append(int(float(data_dict['value'])))

                        # Heart rate metrics
                        elif 'heart' in biomarker_type:
                            if 'resting' in biomarker_type.lower():
                                if 'value' in data_dict:
                                    hr_list.append(int(float(data_dict['value'])))
                            if 'hrv' in biomarker_type or 'variability' in biomarker_type:
                                if 'value' in data_dict:
                                    hrv_list.append(float(data_dict['value']))
                    except (ValueError, TypeError, KeyError) as e:
                        # Skip individual biomarkers that fail to parse
                        print(f"[INSIGHTS_V2] Skipping biomarker {biomarker_type}: {e}")
                        continue

                # Calculate averages
                health_window.sleep_duration_avg = sum(durations) / len(durations) if durations else None
                health_window.steps_avg = int(sum(steps_list) / len(steps_list)) if steps_list else None
                health_window.active_minutes_avg = int(sum(active_mins) / len(active_mins)) if active_mins else None
                health_window.calories_burned_avg = int(sum(calories_list) / len(calories_list)) if calories_list else None
                health_window.resting_heart_rate_avg = int(sum(hr_list) / len(hr_list)) if hr_list else None
                health_window.heart_rate_variability_avg = sum(hrv_list) / len(hrv_list) if hrv_list else None

            # Extract from scores list
            if hasattr(health_context, 'scores') and health_context.scores:
                energy_scores = []
                readiness_scores = []
                sleep_quality_scores = []

                for score_record in health_context.scores:
                    score_type = score_record.type.lower()
                    score_value = score_record.score

                    if 'energy' in score_type:
                        energy_scores.append(score_value)
                    elif 'readiness' in score_type or 'ready' in score_type:
                        readiness_scores.append(score_value)
                    elif 'sleep' in score_type and 'quality' in score_type:
                        sleep_quality_scores.append(score_value)

                health_window.energy_score_avg = sum(energy_scores) / len(energy_scores) if energy_scores else None
                health_window.readiness_score_avg = sum(readiness_scores) / len(readiness_scores) if readiness_scores else None
                health_window.sleep_quality_avg = sum(sleep_quality_scores) / len(sleep_quality_scores) if sleep_quality_scores else None

            print(f"[INSIGHTS_V2] Extracted health data: sleep={health_window.sleep_duration_avg}hr, steps={health_window.steps_avg}, energy={health_window.energy_score_avg}, biomarkers_count={len(health_context.biomarkers) if hasattr(health_context, 'biomarkers') else 0}, scores_count={len(health_context.scores) if hasattr(health_context, 'scores') else 0}")

        except Exception as e:
            print(f"[INSIGHTS_V2] Error extracting metrics: {e}")
            import traceback
            traceback.print_exc()

        return health_window

    async def fetch_behavioral_data(
        self,
        user_id: str,
        days: int = 3
    ) -> BehaviorDataWindow:
        """
        Fetch engagement data from Supabase for the last N days

        Data Sources:
        - plan_items: Task completion data (via engagement_context API)
        - daily_journals: Mood, energy, stress levels

        Args:
            user_id: User identifier
            days: Number of days to fetch (default: 3 for daily insights)

        Returns:
            BehaviorDataWindow with aggregated engagement metrics
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        behavior_window = BehaviorDataWindow(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

        if not self.supabase:
            print("[INSIGHTS_V2] No Supabase adapter available for behavioral data")
            return behavior_window

        try:
            # Ensure Supabase connection is established
            await self.supabase.connect()

            # Fetch engagement context (task completion data)
            engagement_data = await self._fetch_engagement_context(user_id, days)

            # Fetch daily journal data (self-reported metrics)
            journal_data = await self._fetch_journal_data(user_id, days)

            # Populate behavior window with engagement data
            if engagement_data:
                summary = engagement_data.get('engagement_summary', {})
                timing = engagement_data.get('timing_patterns', {})

                behavior_window.total_tasks = summary.get('total_planned', 0)
                behavior_window.completed_tasks = summary.get('completed', 0)
                behavior_window.completion_rate = summary.get('completion_rate', 0.0)

                behavior_window.morning_completion_rate = timing.get('morning_completion_rate', 0.0)
                behavior_window.afternoon_completion_rate = timing.get('afternoon_completion_rate', 0.0)
                behavior_window.evening_completion_rate = timing.get('evening_completion_rate', 0.0)

            # Populate behavior window with journal data
            if journal_data:
                behavior_window.daily_check_in_count = journal_data['check_in_count']
                behavior_window.avg_energy_level = journal_data['avg_energy']
                behavior_window.avg_mood_level = journal_data['avg_mood']
                behavior_window.avg_stress_level = journal_data['avg_stress']

            print(f"[INSIGHTS_V2] Extracted engagement data: {behavior_window.total_tasks} tasks, {behavior_window.completion_rate:.1%} completion, {behavior_window.daily_check_in_count} check-ins")

        except Exception as e:
            print(f"[INSIGHTS_V2] Error fetching behavioral data: {e}")
            import traceback
            traceback.print_exc()

        return behavior_window

    async def _fetch_engagement_context(self, user_id: str, days: int) -> Optional[Dict[str, Any]]:
        """
        Fetch engagement context from Supabase

        Uses the engagement-context endpoint pattern to get task completion data
        """
        try:
            # Query plan_items for task completion
            # For "last N days", we include today and go back (N-1) days
            # Example: days=3 means today + 2 days back = 3 total days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days - 1)

            print(f"[INSIGHTS_V2] Current datetime: {datetime.now()}")
            print(f"[INSIGHTS_V2] Date range for engagement data: {start_date} to {end_date} ({days} days)")
            print(f"[INSIGHTS_V2] Query parameters: user_id={user_id}, start={start_date.isoformat()}, end={end_date.isoformat()}")
            print(f"[INSIGHTS_V2] Expected data: plan_date should be between {start_date} and {end_date}")

            # Get plan items
            # Cast dates explicitly to handle type comparison
            plan_items_query = """
                SELECT id, title, task_type, time_block, plan_date, scheduled_time
                FROM plan_items
                WHERE profile_id = $1
                AND plan_date >= $2::date
                AND plan_date <= $3::date
                ORDER BY plan_date DESC
            """
            plan_items = await self.supabase.fetch(
                plan_items_query,
                user_id,
                start_date.isoformat(),
                end_date.isoformat()
            )

            print(f"[INSIGHTS_V2] Plan items query returned {len(plan_items)} results")
            if len(plan_items) > 0:
                print(f"[INSIGHTS_V2] Sample plan_item: {plan_items[0]}")
            else:
                # Debug: Try fetching without date filter to see what exists
                print(f"[INSIGHTS_V2] No results with date filter. Checking all records for user...")
                all_items_query = """
                    SELECT id, plan_date, scheduled_time
                    FROM plan_items
                    WHERE profile_id = $1
                    ORDER BY plan_date DESC
                    LIMIT 5
                """
                all_items = await self.supabase.fetch(all_items_query, user_id)
                print(f"[INSIGHTS_V2] Found {len(all_items)} total plan_items for this user")
                if len(all_items) > 0:
                    print(f"[INSIGHTS_V2] Sample dates in DB: {[item.get('plan_date') for item in all_items]}")

            # Get task check-ins
            # Cast dates explicitly to handle type comparison
            checkins_query = """
                SELECT completion_status, plan_item_id, planned_date
                FROM task_checkins
                WHERE profile_id = $1
                AND planned_date >= $2::date
                AND planned_date <= $3::date
            """
            checkins = await self.supabase.fetch(
                checkins_query,
                user_id,
                start_date.isoformat(),
                end_date.isoformat()
            )

            print(f"[INSIGHTS_V2] Check-ins query returned {len(checkins)} results")
            if len(checkins) > 0:
                print(f"[INSIGHTS_V2] Sample checkin: {checkins[0]}")

            # Build engagement summary
            total_planned = len(plan_items)
            completed = len([c for c in checkins if c.get('completion_status') == 'completed'])

            # Debug logging
            print(f"[INSIGHTS_V2] Engagement data debug: plan_items={len(plan_items)}, checkins={len(checkins)}, completed={completed}")
            if len(checkins) > 0 and len(plan_items) == 0:
                print(f"[INSIGHTS_V2] Warning: Found {len(checkins)} check-ins but no plan_items in date range")

            # Calculate time-of-day completion rates
            morning_tasks = [p for p in plan_items if 'block_1' in p.get('time_block', '')]
            afternoon_tasks = [p for p in plan_items if 'block_2' in p.get('time_block', '') or 'block_3' in p.get('time_block', '')]
            evening_tasks = [p for p in plan_items if 'block_4' in p.get('time_block', '')]

            # Build checkin lookup map
            checkin_map = {c['plan_item_id']: c for c in checkins if 'plan_item_id' in c}

            # Calculate completion by time block
            morning_completed = sum(1 for p in morning_tasks if p.get('id') in checkin_map and checkin_map[p['id']].get('completion_status') == 'completed')
            afternoon_completed = sum(1 for p in afternoon_tasks if p.get('id') in checkin_map and checkin_map[p['id']].get('completion_status') == 'completed')
            evening_completed = sum(1 for p in evening_tasks if p.get('id') in checkin_map and checkin_map[p['id']].get('completion_status') == 'completed')

            return {
                'engagement_summary': {
                    'total_planned': total_planned,
                    'completed': completed,
                    'completion_rate': completed / total_planned if total_planned > 0 else 0
                },
                'timing_patterns': {
                    'morning_completion_rate': morning_completed / len(morning_tasks) if morning_tasks else 0,
                    'afternoon_completion_rate': afternoon_completed / len(afternoon_tasks) if afternoon_tasks else 0,
                    'evening_completion_rate': evening_completed / len(evening_tasks) if evening_tasks else 0
                }
            }

        except Exception as e:
            print(f"[INSIGHTS_V2] Error fetching engagement context: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _fetch_journal_data(self, user_id: str, days: int) -> Optional[Dict[str, Any]]:
        """
        Fetch daily journal data (self-reported metrics)

        Returns aggregated energy, mood, stress levels from daily_journals table
        """
        try:
            # For "last N days", include today and go back (N-1) days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days - 1)

            # Query daily_journals table
            journal_query = """
                SELECT energy_level, mood_rating, stress_level, journal_date
                FROM daily_journals
                WHERE profile_id = $1 AND journal_date >= $2 AND journal_date <= $3
                ORDER BY journal_date DESC
            """
            journals = await self.supabase.fetch(
                journal_query,
                user_id,
                start_date.isoformat(),
                end_date.isoformat()
            )

            if not journals:
                return None

            # Calculate averages
            energy_levels = [j['energy_level'] for j in journals if j.get('energy_level') is not None]
            mood_ratings = [j['mood_rating'] for j in journals if j.get('mood_rating') is not None]
            stress_levels = [j['stress_level'] for j in journals if j.get('stress_level') is not None]

            return {
                'check_in_count': len(journals),
                'avg_energy': sum(energy_levels) / len(energy_levels) if energy_levels else None,
                'avg_mood': sum(mood_ratings) / len(mood_ratings) if mood_ratings else None,
                'avg_stress': sum(stress_levels) / len(stress_levels) if stress_levels else None
            }

        except Exception as e:
            print(f"[INSIGHTS_V2] Error fetching journal data: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _fetch_behavior_analysis(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch latest behavior analysis summary from holistic_analysis_results

        Returns summary of psychological patterns, barriers, and insights from JSONB analysis_result column
        """
        try:
            # Use Supabase REST API client to fetch analysis_result JSONB
            if not self.supabase.client:
                print("[INSIGHTS_V2] Supabase client not available")
                return None

            result = self.supabase.client.table("holistic_analysis_results")\
                .select("id, archetype, analysis_type, analysis_result, analysis_date, created_at")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            if not result.data or len(result.data) == 0:
                print(f"[INSIGHTS_V2] No behavior analysis found for user {user_id}")
                return None

            analysis_row = result.data[0]
            analysis_result = analysis_row.get('analysis_result', {})

            # Extract relevant summary information from JSONB structure
            # The structure varies by analysis_type, so we safely extract common fields
            return {
                'archetype': analysis_row.get('archetype'),
                'analysis_type': analysis_row.get('analysis_type'),
                'analysis_date': analysis_row.get('analysis_date'),
                'analysis_id': analysis_row.get('id'),
                # Extract from JSONB analysis_result
                'psychological_patterns': analysis_result.get('psychological_patterns'),
                'barriers_identified': analysis_result.get('barriers_identified'),
                'motivation_patterns': analysis_result.get('motivation_patterns'),
                'key_insights': analysis_result.get('key_insights'),
                'primary_goal': analysis_result.get('primary_goal'),
                'focus_areas': analysis_result.get('focus_areas', [])
            }

        except Exception as e:
            print(f"[INSIGHTS_V2] Error fetching behavior analysis: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def build_insight_context(
        self,
        user_id: str,
        archetype: str,
        days: int = 3
    ) -> InsightContext:
        """
        Build complete context for insights generation

        This is the main entry point for the data aggregation service.
        Orchestrates fetching from all data sources and combining into
        a comprehensive InsightContext object.

        Args:
            user_id: User identifier
            archetype: User's archetype (for archetype-specific insights)
            days: Number of days for insight window (default: 3)

        Returns:
            InsightContext ready for AI insights generation
        """
        # Fetch data in parallel
        health_data = await self.fetch_health_data(user_id, days)
        behavior_data = await self.fetch_behavioral_data(user_id, days)

        # Get or calculate baselines
        if self.baseline_service:
            baselines = await self.baseline_service.get_or_calculate_baselines(user_id)
        else:
            # Fallback: empty baselines
            baselines = UserBaselines(
                user_id=user_id,
                calculated_at=datetime.now()
            )

        # Fetch latest behavior analysis summary
        analysis_summary = await self._fetch_behavior_analysis(user_id)

        # Build complete context
        context = InsightContext(
            user_id=user_id,
            archetype=archetype,
            generated_at=datetime.now(),
            health_data=health_data,
            behavior_data=behavior_data,
            baselines=baselines,
            latest_analysis_summary=analysis_summary
        )

        print(f"[INSIGHTS_V2] Built complete context: health_data={health_data.steps_avg} steps, behavior_data={behavior_data.total_tasks} tasks, analysis_summary={'present' if analysis_summary else 'none'}")

        return context


# Service singleton
_data_aggregation_service: Optional[DataAggregationService] = None


async def get_data_aggregation_service() -> DataAggregationService:
    """Get or create DataAggregationService singleton"""
    global _data_aggregation_service

    if _data_aggregation_service is None:
        # Initialize with real services
        try:
            from services.sahha_data_service import SahhaDataService
            from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
            from .baseline_calculation_service import get_baseline_service

            sahha_service = SahhaDataService()
            supabase = SupabaseAsyncPGAdapter()
            baseline_service = await get_baseline_service()

            _data_aggregation_service = DataAggregationService(
                sahha_data_service=sahha_service,
                supabase_adapter=supabase,
                baseline_service=baseline_service
            )
            print("[INSIGHTS_V2] Data Aggregation Service initialized with Sahha + Supabase")
        except Exception as e:
            print(f"[INSIGHTS_V2] Failed to initialize real services: {e}, using empty service")
            _data_aggregation_service = DataAggregationService()

    return _data_aggregation_service
