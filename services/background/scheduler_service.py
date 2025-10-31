"""
Background Scheduler Service
Handles automated periodic tasks (Sahha data refresh, cleanup, etc.)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """
    Manages automated background tasks

    Features:
    - Periodic Sahha data refresh (every 30 minutes)
    - Old data cleanup (daily at 2 AM)
    - Health check pings (every 5 minutes)
    - Active user data sync (configurable)

    Uses APScheduler for reliable task scheduling
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.running = False

    async def start(self):
        """Start background scheduler"""
        if self.running:
            logger.warning("[SCHEDULER] Already running")
            return

        logger.info("[SCHEDULER] Starting background scheduler...")

        # Job 1: Refresh Sahha data for active users (every 30 minutes)
        self.scheduler.add_job(
            func=self._refresh_active_users_sahha_data,
            trigger=IntervalTrigger(minutes=30),
            id='sahha_refresh_active_users',
            name='Refresh Sahha data for active users',
            replace_existing=True
        )

        # Job 2: Cleanup old cache entries (daily at 2 AM)
        self.scheduler.add_job(
            func=self._cleanup_old_cache,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_old_cache',
            name='Cleanup old cached data',
            replace_existing=True
        )

        # Job 3: System health check (every 5 minutes)
        self.scheduler.add_job(
            func=self._system_health_check,
            trigger=IntervalTrigger(minutes=5),
            id='system_health_check',
            name='System health monitoring',
            replace_existing=True
        )

        # Job 4: Refresh stale Sahha data (every 10 minutes - checks for stale data)
        self.scheduler.add_job(
            func=self._refresh_stale_sahha_data,
            trigger=IntervalTrigger(minutes=10),
            id='sahha_refresh_stale',
            name='Refresh stale Sahha data',
            replace_existing=True
        )

        self.scheduler.start()
        self.running = True
        logger.info("[SCHEDULER] ✅ Background scheduler started with 4 jobs")

    async def stop(self):
        """Stop background scheduler gracefully"""
        if not self.running:
            return

        logger.info("[SCHEDULER] Stopping background scheduler...")
        self.scheduler.shutdown(wait=True)
        self.running = False
        logger.info("[SCHEDULER] Background scheduler stopped")

    # ============================================================================
    # SCHEDULED JOBS
    # ============================================================================

    async def _refresh_active_users_sahha_data(self):
        """
        Refresh Sahha data for users who have been active in last 24 hours
        Runs every 30 minutes
        """
        logger.info("[SCHEDULER] 🔄 Running: Refresh active users Sahha data")

        try:
            from shared_libs.supabase_client.adapter import get_db_adapter
            from services.sahha_data_service import get_sahha_data_service

            db = get_db_adapter()
            sahha_service = get_sahha_data_service()

            # Get users active in last 24 hours
            query = """
                SELECT DISTINCT profile_id
                FROM plan_items
                WHERE plan_date >= NOW() - INTERVAL '24 hours'
                LIMIT 50
            """

            result = await db.fetch(query)
            active_users = [row['profile_id'] for row in result]

            logger.info(f"[SCHEDULER] Found {len(active_users)} active users")

            # Refresh Sahha data for each user (background)
            for user_id in active_users:
                try:
                    # This will fetch fresh data and cache it
                    await sahha_service.get_sahha_data_with_cache(
                        user_id=user_id,
                        force_refresh=False  # Only refresh if stale
                    )
                except Exception as e:
                    logger.error(f"[SCHEDULER] Failed to refresh Sahha for {user_id[:8]}...: {e}")

            logger.info(f"[SCHEDULER] ✅ Refreshed Sahha data for {len(active_users)} users")

        except Exception as e:
            logger.error(f"[SCHEDULER] Job failed: refresh_active_users_sahha_data: {e}")

    async def _cleanup_old_cache(self):
        """
        Cleanup old cached Sahha data (older than 7 days)
        Runs daily at 2 AM
        """
        logger.info("[SCHEDULER] 🧹 Running: Cleanup old cache")

        try:
            from shared_libs.supabase_client.adapter import get_db_adapter

            db = get_db_adapter()

            # Delete biomarkers older than 7 days
            delete_biomarkers_query = """
                DELETE FROM biomarkers
                WHERE created_at < NOW() - INTERVAL '7 days'
            """

            # Delete scores older than 7 days
            delete_scores_query = """
                DELETE FROM scores
                WHERE created_at < NOW() - INTERVAL '7 days'
            """

            biomarkers_deleted = await db.execute(delete_biomarkers_query)
            scores_deleted = await db.execute(delete_scores_query)

            logger.info(
                f"[SCHEDULER] ✅ Cleanup complete: "
                f"{biomarkers_deleted} biomarkers, {scores_deleted} scores deleted"
            )

        except Exception as e:
            logger.error(f"[SCHEDULER] Job failed: cleanup_old_cache: {e}")

    async def _system_health_check(self):
        """
        Monitor system health (queue size, error rates, etc.)
        Runs every 5 minutes
        """
        logger.debug("[SCHEDULER] 💓 Running: System health check")

        try:
            from services.background.simple_queue import get_job_queue

            job_queue = get_job_queue()
            stats = job_queue.get_stats()

            # Check for issues
            if stats['queue_size'] > 100:
                logger.warning(f"[SCHEDULER] ⚠️  High queue size: {stats['queue_size']} jobs")

            if stats['failed'] > 10:
                logger.warning(f"[SCHEDULER] ⚠️  High failure rate: {stats['failed']} failed jobs")

            logger.debug(f"[SCHEDULER] Health: Queue={stats['queue_size']}, Failed={stats['failed']}")

        except Exception as e:
            logger.error(f"[SCHEDULER] Job failed: system_health_check: {e}")

    async def _refresh_stale_sahha_data(self):
        """
        Find and refresh stale Sahha data (older than 30 minutes)
        Runs every 10 minutes
        """
        logger.info("[SCHEDULER] 🔍 Running: Check for stale Sahha data")

        try:
            from shared_libs.supabase_client.adapter import get_db_adapter
            from services.sahha_data_service import get_sahha_data_service

            db = get_db_adapter()
            sahha_service = get_sahha_data_service()

            # Find users with stale data (last score > 30 min old)
            query = """
                SELECT DISTINCT s.profile_id, MAX(s.created_at) as last_sync
                FROM scores s
                WHERE s.created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY s.profile_id
                HAVING MAX(s.created_at) < NOW() - INTERVAL '30 minutes'
                LIMIT 20
            """

            result = await db.fetch(query)
            stale_users = [row['profile_id'] for row in result]

            if not stale_users:
                logger.debug("[SCHEDULER] No stale Sahha data found")
                return

            logger.info(f"[SCHEDULER] Found {len(stale_users)} users with stale data")

            # Refresh in background
            for user_id in stale_users:
                try:
                    await sahha_service.get_sahha_data_with_cache(
                        user_id=user_id,
                        force_refresh=True  # Force refresh
                    )
                except Exception as e:
                    logger.error(f"[SCHEDULER] Failed to refresh stale data for {user_id[:8]}...: {e}")

            logger.info(f"[SCHEDULER] ✅ Refreshed stale data for {len(stale_users)} users")

        except Exception as e:
            logger.error(f"[SCHEDULER] Job failed: refresh_stale_sahha_data: {e}")

    # ============================================================================
    # MANUAL TRIGGERS (can be called via API endpoints)
    # ============================================================================

    async def trigger_user_refresh(self, user_id: str, force: bool = False):
        """
        Manually trigger Sahha data refresh for a specific user

        Args:
            user_id: User to refresh
            force: Force refresh even if data is fresh
        """
        logger.info(f"[SCHEDULER] Manual trigger: Refresh Sahha for {user_id[:8]}...")

        try:
            from services.sahha_data_service import get_sahha_data_service

            sahha_service = get_sahha_data_service()
            await sahha_service.get_sahha_data_with_cache(
                user_id=user_id,
                force_refresh=force
            )

            logger.info(f"[SCHEDULER] ✅ Manual refresh complete for {user_id[:8]}...")

        except Exception as e:
            logger.error(f"[SCHEDULER] Manual trigger failed: {e}")
            raise

    async def trigger_bulk_refresh(self, user_ids: list[str]):
        """
        Manually trigger bulk Sahha data refresh

        Args:
            user_ids: List of user IDs to refresh
        """
        logger.info(f"[SCHEDULER] Bulk trigger: Refresh {len(user_ids)} users")

        for user_id in user_ids:
            try:
                await self.trigger_user_refresh(user_id, force=False)
            except Exception as e:
                logger.error(f"[SCHEDULER] Bulk refresh failed for {user_id[:8]}...: {e}")

        logger.info(f"[SCHEDULER] ✅ Bulk refresh complete")

    def get_job_status(self) -> dict:
        """Get status of all scheduled jobs"""
        jobs = self.scheduler.get_jobs()

        return {
            'running': self.running,
            'total_jobs': len(jobs),
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
                for job in jobs
            ]
        }


# Singleton instance
_scheduler = None


def get_scheduler() -> BackgroundScheduler:
    """Get or create singleton scheduler"""
    global _scheduler

    if _scheduler is None:
        _scheduler = BackgroundScheduler()

    return _scheduler
