"""
Simple Async Job Queue
MVP-style: In-memory queue with retry logic (no Redis needed)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class Job:
    """Simple job wrapper"""

    def __init__(self, job_type: str, payload: Dict[str, Any]):
        self.id = f"{job_type}_{datetime.utcnow().timestamp()}"
        self.job_type = job_type
        self.payload = payload
        self.status = JobStatus.PENDING
        self.attempts = 0
        self.max_attempts = 3
        self.error = None
        self.created_at = datetime.utcnow()


class SimpleJobQueue:
    """
    MVP-style async job queue

    Features:
    - In-memory queue (asyncio.Queue)
    - Automatic retry (3 attempts)
    - Worker loop running in background
    - No Redis dependency

    Limitations (acceptable for MVP):
    - Jobs lost on restart (okay - next analysis will refetch)
    - Single-server only (okay for MVP scale)
    """

    def __init__(self):
        self.queue = asyncio.Queue()
        self.running = False
        self.worker_task = None
        self.stats = {
            "queued": 0,
            "completed": 0,
            "failed": 0,
            "retries": 0
        }

    async def start(self):
        """Start background worker"""
        if self.running:
            logger.warning("[QUEUE] Worker already running")
            return

        self.running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        logger.info("[QUEUE] Background worker started")

    async def stop(self):
        """Stop background worker gracefully"""
        if not self.running:
            return

        self.running = False
        if self.worker_task:
            await self.worker_task
        logger.info("[QUEUE] Background worker stopped")

    async def submit_job(self, job_type: str, payload: Dict[str, Any]):
        """
        Submit job to queue (non-blocking)

        Args:
            job_type: Type of job (e.g., "SYNC_SAHHA_DATA")
            payload: Job data
        """
        job = Job(job_type, payload)
        await self.queue.put(job)
        self.stats["queued"] += 1
        logger.info(f"[QUEUE] Job {job.id} queued (type: {job_type})")

    async def _worker_loop(self):
        """Background worker loop - processes jobs from queue"""

        logger.info("[QUEUE] Worker loop starting")

        while self.running:
            try:
                # Get job from queue (wait up to 1 second)
                try:
                    job = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Process job
                await self._process_job(job)

            except Exception as e:
                logger.error(f"[QUEUE] Worker loop error: {e}")
                await asyncio.sleep(1)

        logger.info("[QUEUE] Worker loop stopped")

    async def _process_job(self, job: Job):
        """
        Process a single job with retry logic

        Args:
            job: Job to process
        """

        job.attempts += 1
        job.status = JobStatus.PROCESSING

        logger.info(f"[QUEUE] Processing job {job.id} (attempt {job.attempts}/{job.max_attempts})")

        try:
            # Import here to avoid circular dependency
            from .archival_service import get_archival_service

            archival_service = get_archival_service()

            # Process based on job type
            if job.job_type == "SYNC_SAHHA_DATA":
                await archival_service.archive_sahha_data(
                    user_id=job.payload["user_id"],
                    archetype=job.payload["archetype"],
                    analysis_type=job.payload["analysis_type"],
                    sahha_data=job.payload["sahha_data"],
                    tracking_record_id=job.payload.get("tracking_record_id")
                )

                job.status = JobStatus.COMPLETED
                self.stats["completed"] += 1
                logger.info(f"[QUEUE] Job {job.id} completed successfully")

            else:
                raise ValueError(f"Unknown job type: {job.job_type}")

        except Exception as e:
            job.error = str(e)
            logger.error(f"[QUEUE] Job {job.id} failed (attempt {job.attempts}): {e}")

            # Retry logic
            if job.attempts < job.max_attempts:
                job.status = JobStatus.RETRY
                self.stats["retries"] += 1

                # Re-queue with exponential backoff delay
                delay = 2 ** job.attempts  # 2s, 4s, 8s
                logger.info(f"[QUEUE] Retrying job {job.id} in {delay}s")
                await asyncio.sleep(delay)
                await self.queue.put(job)

            else:
                job.status = JobStatus.FAILED
                self.stats["failed"] += 1
                logger.error(f"[QUEUE] Job {job.id} permanently failed after {job.attempts} attempts")

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            **self.stats,
            "queue_size": self.queue.qsize(),
            "running": self.running
        }


# Singleton instance
_job_queue = None


def get_job_queue() -> SimpleJobQueue:
    """Get or create singleton job queue"""
    global _job_queue

    if _job_queue is None:
        _job_queue = SimpleJobQueue()

    return _job_queue
