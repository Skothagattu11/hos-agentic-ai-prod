"""
Sahha Data Service - Integrates direct Sahha fetch with existing flow
MVP-style: Simple wrapper, non-breaking integration
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

from services.sahha import get_sahha_client
from services.background import get_job_queue
from shared_libs.data_models.health_models import UserHealthContext, create_health_context_from_raw_data

logger = logging.getLogger(__name__)


class SahhaDataService:
    """
    Wraps Sahha client for seamless integration with existing analysis flow

    Features:
    - Fetches directly from Sahha (with watermark for incremental)
    - Converts to UserHealthContext format
    - Submits background archival job
    - Fallback to Supabase on error
    """

    def __init__(self):
        self.sahha_client = get_sahha_client()

    async def fetch_health_data_for_analysis(
        self,
        user_id: str,
        archetype: str,
        analysis_type: str,
        watermark: Optional[datetime] = None,
        days: int = 7
    ) -> UserHealthContext:
        """
        Fetch health data for analysis (main method)

        Args:
            user_id: User identifier
            archetype: Archetype name
            analysis_type: "behavior_analysis" or "circadian_analysis"
            watermark: Last analysis timestamp (None = initial fetch)
            days: Days to fetch if no watermark

        Returns:
            UserHealthContext with fresh Sahha data
        """

        logger.info(f"[SAHHA_DATA] Fetching for {user_id[:8]}... ({archetype}, {analysis_type})")

        try:
            # Fetch from Sahha (incremental if watermark exists)
            sahha_data = await self.sahha_client.fetch_health_data(
                external_id=user_id,
                since_timestamp=watermark,
                days=days
            )

            # Check if we got data
            if not sahha_data.get("biomarkers") and not sahha_data.get("scores"):
                logger.warning(f"[SAHHA_DATA] No data returned from Sahha for {user_id[:8]}...")
                # Return empty context (will trigger fallback in caller)
                return self._create_empty_context(user_id, days)

            # Convert to UserHealthContext format
            context = self._convert_to_health_context(user_id, sahha_data, days)

            logger.info(
                f"[SAHHA_DATA] Fetched {len(sahha_data['biomarkers'])} biomarkers + "
                f"{len(sahha_data['scores'])} scores"
            )

            # Submit background archival job (fire-and-forget - truly non-blocking)
            asyncio.create_task(self._submit_archival_job(
                user_id=user_id,
                archetype=archetype,
                analysis_type=analysis_type,
                sahha_data=sahha_data
            ))

            return context

        except Exception as e:
            logger.error(f"[SAHHA_DATA] Fetch failed for {user_id[:8]}...: {e}")
            # Return empty context (caller will fallback to Supabase)
            return self._create_empty_context(user_id, days)

    def _convert_to_health_context(
        self,
        user_id: str,
        sahha_data: Dict[str, Any],
        days: int
    ) -> UserHealthContext:
        """
        Convert Sahha data format to UserHealthContext

        Sahha format: {"biomarkers": [...], "scores": [...]}
        UserHealthContext format: Pydantic model with nested structure
        """

        try:
            # Convert biomarkers to expected format
            raw_biomarkers = []
            for bio in sahha_data.get("biomarkers", []):
                raw_biomarkers.append({
                    "id": bio.get("id", f"sahha_{bio.get('type')}_{bio.get('startDateTime')}"),
                    "profile_id": user_id,
                    "category": self._map_biomarker_category(bio.get("type")),
                    "type": bio.get("type"),
                    "data": {
                        "value": bio.get("value"),
                        "unit": bio.get("unit")
                    },
                    "start_date_time": bio.get("startDateTime"),
                    "end_date_time": bio.get("endDateTime"),
                    "created_at": bio.get("createdAt", datetime.utcnow().isoformat()),
                    "updated_at": datetime.utcnow().isoformat()
                })

            # Convert scores to expected format
            raw_scores = []
            for score in sahha_data.get("scores", []):
                raw_scores.append({
                    "id": score.get("id", f"sahha_{score.get('type')}_{score.get('scoreDateTime')}"),
                    "profile_id": user_id,
                    "type": score.get("type"),
                    "score": score.get("score"),
                    "data": {},  # Sahha doesn't provide extra data field
                    "score_date_time": score.get("scoreDateTime"),
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })

            # Create UserHealthContext using existing function
            context = create_health_context_from_raw_data(
                user_id=user_id,
                raw_scores=raw_scores,
                raw_biomarkers=raw_biomarkers,
                raw_archetypes=[],  # Archetypes not needed for analysis
                days=days
            )

            return context

        except Exception as e:
            logger.error(f"[SAHHA_DATA] Conversion failed: {e}")
            return self._create_empty_context(user_id, days)

    def _map_biomarker_category(self, biomarker_type: str) -> str:
        """Map Sahha biomarker types to categories"""
        # Simple mapping (extend as needed)
        if "sleep" in biomarker_type.lower():
            return "sleep"
        elif "steps" in biomarker_type.lower() or "active" in biomarker_type.lower():
            return "activity"
        elif "heart" in biomarker_type.lower() or "hrv" in biomarker_type.lower():
            return "vitals"
        else:
            return "other"

    def _create_empty_context(self, user_id: str, days: int) -> UserHealthContext:
        """Create empty UserHealthContext for fallback"""
        return create_health_context_from_raw_data(
            user_id=user_id,
            raw_scores=[],
            raw_biomarkers=[],
            raw_archetypes=[],
            days=days
        )

    async def _submit_archival_job(
        self,
        user_id: str,
        archetype: str,
        analysis_type: str,
        sahha_data: Dict[str, Any]
    ):
        """Submit background archival job (non-blocking)"""
        try:
            job_queue = get_job_queue()
            await job_queue.submit_job(
                job_type="SYNC_SAHHA_DATA",
                payload={
                    "user_id": user_id,
                    "archetype": archetype,
                    "analysis_type": analysis_type,
                    "sahha_data": sahha_data
                }
            )
            logger.debug(f"[SAHHA_DATA] Archival job submitted for {user_id[:8]}...")
        except Exception as e:
            # Non-critical - just log
            logger.warning(f"[SAHHA_DATA] Failed to submit archival job: {e}")


# Singleton instance
_sahha_data_service = None


def get_sahha_data_service() -> SahhaDataService:
    """Get or create singleton Sahha data service"""
    global _sahha_data_service

    if _sahha_data_service is None:
        _sahha_data_service = SahhaDataService()

    return _sahha_data_service
