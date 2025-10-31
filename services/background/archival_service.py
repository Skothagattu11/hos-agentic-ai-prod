"""
Sahha Data Archival Service
MVP-style: UPSERT with simple error handling
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
from supabase import create_client

logger = logging.getLogger(__name__)


class ArchivalService:
    """
    Archives Sahha data to Supabase with deduplication

    Features:
    - UPSERT for biomarkers (prevents duplicates)
    - UPSERT for scores (prevents duplicates)
    - Updates sync status in archetype_analysis_tracking
    - Simple error handling with logging
    """

    def __init__(self):
        self.supabase = None

    def _get_supabase(self):
        """Get Supabase client"""
        if not self.supabase:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_KEY', '')

            if not supabase_url or not supabase_key:
                raise Exception("Missing SUPABASE_URL or SUPABASE_KEY")

            self.supabase = create_client(supabase_url, supabase_key)
            logger.debug("[ARCHIVAL] Connected to Supabase")

        return self.supabase

    async def archive_sahha_data(
        self,
        user_id: str,
        archetype: str,
        analysis_type: str,
        sahha_data: Dict[str, Any],
        tracking_record_id: Optional[int] = None
    ):
        """
        Archive Sahha data to Supabase (main method)

        Args:
            user_id: User identifier
            archetype: Archetype name
            analysis_type: "behavior_analysis" or "circadian_analysis"
            sahha_data: Dict with "biomarkers" and "scores" lists
            tracking_record_id: ID in archetype_analysis_tracking (optional)

        Raises:
            Exception: If archival fails (for retry logic)
        """

        logger.info(f"[ARCHIVAL] Starting for {user_id[:8]}... ({archetype}, {analysis_type})")

        try:
            supabase = self._get_supabase()

            biomarkers = sahha_data.get("biomarkers", [])
            scores = sahha_data.get("scores", [])

            # Store biomarkers with UPSERT (prevents duplicates)
            stored_biomarkers = await self._store_biomarkers(supabase, user_id, biomarkers)

            # Store scores with UPSERT
            stored_scores = await self._store_scores(supabase, user_id, scores)

            # Update sync status in tracking table
            await self._update_sync_status(
                supabase,
                user_id,
                archetype,
                analysis_type,
                success=True,
                biomarkers_count=stored_biomarkers,
                scores_count=stored_scores
            )

            logger.info(
                f"[ARCHIVAL] Completed: {stored_biomarkers} biomarkers + "
                f"{stored_scores} scores for {user_id[:8]}..."
            )

        except Exception as e:
            logger.error(f"[ARCHIVAL] Failed for {user_id[:8]}...: {e}")

            # Try to update sync status with error
            try:
                supabase = self._get_supabase()
                await self._update_sync_status(
                    supabase,
                    user_id,
                    archetype,
                    analysis_type,
                    success=False,
                    error_message=str(e)
                )
            except:
                pass  # Ignore secondary errors

            # Re-raise for retry logic
            raise

    async def _store_biomarkers(
        self,
        supabase,
        user_id: str,
        biomarkers: List[Dict[str, Any]]
    ) -> int:
        """
        Store biomarkers with UPSERT (prevents duplicates)

        Returns: Number of biomarkers stored
        """

        if not biomarkers:
            return 0

        stored_count = 0

        for bio in biomarkers:
            try:
                # Prepare biomarker data with ALL Sahha fields
                # Build data field with additional metadata
                data_field = {
                    "periodicity": bio.get("periodicity"),
                    "aggregation": bio.get("aggregation"),
                    "valueType": bio.get("valueType"),
                    "sahha_id": bio.get("id")
                }

                bio_data = {
                    "profile_id": user_id,
                    "category": bio.get("category"),  # CRITICAL: vitals, sleep, activity, etc.
                    "type": bio.get("type"),
                    "value": bio.get("value"),
                    "unit": bio.get("unit"),
                    "data": data_field,  # CRITICAL: Store additional metadata
                    "start_date_time": bio.get("startDateTime"),
                    "end_date_time": bio.get("endDateTime"),
                    "created_at": bio.get("createdAt", datetime.utcnow().isoformat()),
                    "updated_at": datetime.utcnow().isoformat()
                }

                # UPSERT using unique constraint (profile_id, type, start_date_time, end_date_time)
                # Supabase upsert() handles INSERT ON CONFLICT UPDATE automatically
                result = supabase.table("biomarkers").upsert(
                    bio_data,
                    on_conflict="profile_id,type,start_date_time,end_date_time"
                ).execute()

                if result.data:
                    stored_count += 1

            except Exception as e:
                # Log but continue with other biomarkers
                logger.debug(f"[ARCHIVAL] Biomarker insert/update failed: {e}")
                continue

        logger.debug(f"[ARCHIVAL] Stored {stored_count}/{len(biomarkers)} biomarkers")
        return stored_count

    async def _store_scores(
        self,
        supabase,
        user_id: str,
        scores: List[Dict[str, Any]]
    ) -> int:
        """
        Store scores with UPSERT (prevents duplicates)

        Returns: Number of scores stored
        """

        if not scores:
            return 0

        stored_count = 0

        for score in scores:
            try:
                # Prepare score data with ALL Sahha fields
                # Build data field with factors array (CRITICAL for analysis)
                data_field = {
                    "factors": score.get("factors", []),  # CRITICAL: Sleep factors, activity factors, etc.
                    "dataSources": score.get("dataSources", []),
                    "version": score.get("version"),
                    "sahha_id": score.get("id"),
                    "createdAtUtc": score.get("createdAtUtc")
                }

                score_data = {
                    "profile_id": user_id,
                    "type": score.get("type"),
                    "score": score.get("score"),
                    "score_date_time": score.get("scoreDateTime"),
                    "state": score.get("state"),
                    "data": data_field,  # CRITICAL: Store factors array for detailed analysis
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }

                # UPSERT using unique constraint (profile_id, type, score_date_time)
                result = supabase.table("scores").upsert(
                    score_data,
                    on_conflict="profile_id,type,score_date_time"
                ).execute()

                if result.data:
                    stored_count += 1

            except Exception as e:
                logger.debug(f"[ARCHIVAL] Score insert/update failed: {e}")
                continue

        logger.debug(f"[ARCHIVAL] Stored {stored_count}/{len(scores)} scores")
        return stored_count

    async def _update_sync_status(
        self,
        supabase,
        user_id: str,
        archetype: str,
        analysis_type: str,
        success: bool,
        biomarkers_count: int = 0,
        scores_count: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Update sync status in archetype_analysis_tracking

        Args:
            supabase: Supabase client
            user_id: User identifier
            archetype: Archetype name
            analysis_type: Analysis type
            success: Whether sync succeeded
            biomarkers_count: Number of biomarkers stored
            scores_count: Number of scores stored
            error_message: Error message if failed
        """

        try:
            update_data = {
                "sahha_data_synced": success,
                "biomarkers_synced": success and biomarkers_count > 0,
                "scores_synced": success and scores_count > 0,
                "sync_completed_at": datetime.utcnow().isoformat() if success else None,
                "sync_error": error_message if not success else None,
                "updated_at": datetime.utcnow().isoformat()
            }

            # Update the most recent analysis for this user + archetype + analysis_type
            # Note: Supabase Python client doesn't support .order() on update queries
            # We'll update all matching records (should only be one recent record anyway)
            result = supabase.table("archetype_analysis_tracking").update(update_data).eq(
                "user_id", user_id
            ).eq(
                "archetype", archetype
            ).eq(
                "analysis_type", analysis_type
            ).execute()

            if result.data:
                logger.debug(f"[ARCHIVAL] Updated sync status for {user_id[:8]}... ({archetype})")
            else:
                logger.warning(f"[ARCHIVAL] No tracking record found to update for {user_id[:8]}...")

        except Exception as e:
            logger.error(f"[ARCHIVAL] Failed to update sync status: {e}")
            # Don't raise - this is secondary


# Singleton instance
_archival_service = None


def get_archival_service() -> ArchivalService:
    """Get or create singleton archival service"""
    global _archival_service

    if _archival_service is None:
        _archival_service = ArchivalService()

    return _archival_service
