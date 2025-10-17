"""
Baseline Calculation Service - Phase 1, Sprint 1.1

Responsible for:
- Calculating 30-day rolling baselines for each user
- Caching baselines in Redis (24-hour TTL)
- Providing baseline quality assessment
- Handling insufficient data gracefully

Baselines enable personalized insights by comparing current metrics
against each user's historical norms rather than population averages.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from .data_aggregation_service import UserBaselines


class BaselineCalculationService:
    """
    Calculates and caches user-specific baseline metrics

    Phase 1, Sprint 1.1 Implementation:
    - Calculate sleep baselines (duration, quality)
    - Calculate activity baselines (steps, active minutes)
    - Calculate energy baselines (energy score, readiness score)
    - Calculate behavioral baselines (completion rate, consistency)
    - Cache in Redis with 24-hour TTL
    - Quality assessment based on data points available
    """

    def __init__(
        self,
        supabase_adapter=None,
        redis_cache=None
    ):
        """
        Initialize with service dependencies

        Args:
            supabase_adapter: SupabaseAsyncPGAdapter for querying historical data
            redis_cache: Redis client for caching baselines
        """
        self.supabase = supabase_adapter
        self.redis = redis_cache
        self.baseline_period_days = 30
        self.cache_ttl_seconds = 86400  # 24 hours

    async def get_or_calculate_baselines(
        self,
        user_id: str
    ) -> UserBaselines:
        """
        Get baselines from cache or calculate fresh if needed

        Strategy:
        1. Check Redis cache first
        2. If cache miss, calculate from Supabase
        3. Store in cache with 24-hour TTL
        4. Return UserBaselines object

        Args:
            user_id: User identifier

        Returns:
            UserBaselines with calculated metrics
        """
        # Try cache first
        if self.redis:
            cached = await self._get_from_cache(user_id)
            if cached:
                return cached

        # Calculate fresh baselines
        baselines = await self.calculate_baselines(user_id)

        # Store in cache
        if self.redis:
            await self._store_in_cache(user_id, baselines)

        return baselines

    async def calculate_baselines(
        self,
        user_id: str
    ) -> UserBaselines:
        """
        Calculate 30-day rolling baselines from historical data

        Queries Supabase for:
        - biomarkers table: sleep_duration, steps, active_minutes
        - scores table: energy, readiness, sleep_quality
        - plan_items table: completion rates
        - user_check_ins table: consistency

        Args:
            user_id: User identifier

        Returns:
            UserBaselines with calculated averages
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.baseline_period_days)

        # TODO: Implement Supabase queries for 30-day data

        # Calculate baseline quality based on data points
        data_points_count = 0  # TODO: Count actual data points
        baseline_quality = self._assess_baseline_quality(data_points_count)

        baselines = UserBaselines(
            user_id=user_id,
            calculated_at=datetime.now(),
            baseline_period_days=self.baseline_period_days,
            data_points_count=data_points_count,
            baseline_quality=baseline_quality
        )

        return baselines

    async def calculate_sleep_baseline(
        self,
        user_id: str
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate sleep duration and quality baselines

        Queries biomarkers and scores tables for sleep metrics over 30 days.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (avg_duration_hours, avg_quality_score)
        """
        # TODO: Implement Supabase query
        # SELECT AVG(duration), AVG(quality_score)
        # FROM biomarkers
        # WHERE user_id = ? AND type = 'sleep'
        # AND date >= NOW() - INTERVAL '30 days'

        return (None, None)

    async def calculate_activity_baseline(
        self,
        user_id: str
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Calculate activity baselines (steps, active minutes)

        Queries biomarkers table for activity metrics over 30 days.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (avg_steps, avg_active_minutes)
        """
        # TODO: Implement Supabase query
        # SELECT AVG(steps), AVG(active_minutes)
        # FROM biomarkers
        # WHERE user_id = ? AND type IN ('steps', 'activity')
        # AND date >= NOW() - INTERVAL '30 days'

        return (None, None)

    async def calculate_energy_baseline(
        self,
        user_id: str
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate energy and readiness score baselines

        Queries scores table for Sahha-derived metrics over 30 days.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (avg_energy_score, avg_readiness_score)
        """
        # TODO: Implement Supabase query
        # SELECT AVG(score)
        # FROM scores
        # WHERE user_id = ? AND type IN ('energy', 'readiness')
        # AND date >= NOW() - INTERVAL '30 days'
        # GROUP BY type

        return (None, None)

    async def calculate_behavioral_baseline(
        self,
        user_id: str
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate behavioral baselines (completion rate, consistency)

        Queries plan_items table for task completion patterns over 30 days.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (avg_completion_rate, consistency_score)
        """
        # TODO: Implement Supabase query
        # SELECT
        #   COUNT(CASE WHEN completed THEN 1 END)::float / COUNT(*)::float as completion_rate,
        #   STDDEV(completion_rate) as consistency
        # FROM plan_items
        # WHERE user_id = ? AND plan_date >= NOW() - INTERVAL '30 days'
        # GROUP BY DATE(plan_date)

        return (None, None)

    def _assess_baseline_quality(self, data_points_count: int) -> str:
        """
        Assess baseline quality based on data availability

        Quality Thresholds:
        - Excellent: 25+ data points (83%+ of 30 days)
        - Good: 15-24 data points (50-83%)
        - Fair: 7-14 data points (23-50%)
        - Poor: <7 data points (<23%)

        Args:
            data_points_count: Number of days with data

        Returns:
            Quality rating string
        """
        if data_points_count >= 25:
            return "excellent"
        elif data_points_count >= 15:
            return "good"
        elif data_points_count >= 7:
            return "fair"
        else:
            return "poor"

    async def _get_from_cache(
        self,
        user_id: str
    ) -> Optional[UserBaselines]:
        """Get baselines from Redis cache"""
        # TODO: Implement Redis GET with JSON deserialization
        return None

    async def _store_in_cache(
        self,
        user_id: str,
        baselines: UserBaselines
    ) -> None:
        """Store baselines in Redis cache with 24-hour TTL"""
        # TODO: Implement Redis SET with JSON serialization and TTL
        pass


# Service singleton
_baseline_service: Optional[BaselineCalculationService] = None


async def get_baseline_service() -> BaselineCalculationService:
    """Get or create BaselineCalculationService singleton"""
    global _baseline_service

    if _baseline_service is None:
        # Initialize with Supabase
        try:
            from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter

            supabase = SupabaseAsyncPGAdapter()
            _baseline_service = BaselineCalculationService(
                supabase_adapter=supabase,
                redis_cache=None  # TODO: Add Redis later
            )
            print("[INSIGHTS_V2] Baseline Service initialized with Supabase")
        except Exception as e:
            print(f"[INSIGHTS_V2] Failed to initialize baseline service: {e}")
            _baseline_service = BaselineCalculationService()

    return _baseline_service
