"""
Sahha API Client with Incremental Sync Support
MVP-style: Simple code, full features (watermark-based incremental fetch)
"""

import aiohttp
import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class SahhaClient:
    """
    Direct Sahha API client with incremental fetch capability

    Features:
    - Token caching (23-hour expiry)
    - Incremental fetch with watermarks
    - Rate limiting & retry logic
    - Simple error handling
    """

    def __init__(self):
        # Load config from environment
        self.base_url = os.getenv("SAHHA_API_BASE_URL", "https://api.sahha.ai")
        self.client_id = os.getenv("SAHHA_CLIENT_ID")
        self.client_secret = os.getenv("SAHHA_CLIENT_SECRET")

        # Token cache
        self._token = None
        self._token_expires = None

        # Rate limiting config (MVP: simple delays)
        self.request_delay = float(os.getenv("SAHHA_RATE_LIMIT_DELAY", "0.5"))
        self.max_retries = int(os.getenv("SAHHA_MAX_RETRIES", "3"))
        self.timeout = int(os.getenv("SAHHA_REQUEST_TIMEOUT", "30"))

    async def get_token(self) -> Optional[str]:
        """Get account token with 23-hour caching"""

        # Return cached token if still valid
        now = datetime.utcnow()
        if self._token and self._token_expires and self._token_expires > now:
            return self._token

        # Fetch new token
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v1/oauth/account/token",
                    json={
                        "clientId": self.client_id,
                        "clientSecret": self.client_secret
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._token = data.get("accountToken")
                        self._token_expires = now + timedelta(hours=23)
                        logger.info("[SAHHA] Token refreshed successfully")
                        return self._token
                    else:
                        error = await response.text()
                        logger.error(f"[SAHHA] Token fetch failed: {response.status} {error}")
                        return None

        except Exception as e:
            logger.error(f"[SAHHA] Token fetch error: {e}")
            return None

    async def fetch_biomarkers(
        self,
        external_id: str,
        since_timestamp: Optional[datetime] = None,
        days: int = 7,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch biomarkers with incremental sync support

        Args:
            external_id: User's external ID (profile_id)
            since_timestamp: Watermark - fetch only data after this (incremental)
            days: If no watermark, fetch last N days (initial fetch)
            categories: List of categories to fetch (default: activity, sleep, vitals)

        Returns:
            List of biomarker dictionaries
        """

        try:
            token = await self.get_token()
            if not token:
                logger.error(f"[SAHHA] No token available for {external_id[:8]}...")
                return []

            headers = {
                "Authorization": f"account {token}",
                "Content-Type": "application/json"
            }

            # Calculate date range
            if since_timestamp:
                # Incremental fetch: from watermark to now
                start_date = since_timestamp
                end_date = datetime.utcnow()
                logger.info(f"[SAHHA] Incremental biomarker fetch for {external_id[:8]}... since {start_date.isoformat()}")
            else:
                # Initial fetch: last N days
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                logger.info(f"[SAHHA] Initial biomarker fetch for {external_id[:8]}... ({days} days)")

            # Default categories
            if not categories:
                categories = ["activity", "sleep", "vitals"]

            # Fetch biomarkers
            all_biomarkers = []
            for category in categories:
                params = {
                    "startDateTime": start_date.isoformat(),
                    "endDateTime": end_date.isoformat(),
                    "categories": [category]
                }

                # Rate limiting delay
                await asyncio.sleep(self.request_delay)

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/api/v1/profile/biomarker/{external_id}",
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data:
                                all_biomarkers.extend(data)
                                logger.debug(f"[SAHHA] Fetched {len(data)} {category} biomarkers")
                        elif response.status == 429:
                            # Rate limited - wait and skip
                            retry_after = int(response.headers.get('Retry-After', 2))
                            logger.warning(f"[SAHHA] Rate limited, waiting {retry_after}s")
                            await asyncio.sleep(retry_after)
                        else:
                            error = await response.text()
                            logger.error(f"[SAHHA] Biomarker fetch failed: {response.status} {error}")

            logger.info(f"[SAHHA] Fetched {len(all_biomarkers)} total biomarkers for {external_id[:8]}...")
            return all_biomarkers

        except Exception as e:
            logger.error(f"[SAHHA] Biomarker fetch error for {external_id}: {e}")
            return []

    async def fetch_scores(
        self,
        external_id: str,
        since_timestamp: Optional[datetime] = None,
        days: int = 7,
        types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch scores with incremental sync support

        Args:
            external_id: User's external ID
            since_timestamp: Watermark - fetch only data after this
            days: If no watermark, fetch last N days
            types: Score types to fetch (default: sleep, activity, wellbeing)

        Returns:
            List of score dictionaries
        """

        try:
            token = await self.get_token()
            if not token:
                logger.error(f"[SAHHA] No token available for {external_id[:8]}...")
                return []

            headers = {
                "Authorization": f"account {token}",
                "Content-Type": "application/json"
            }

            # Calculate date range
            if since_timestamp:
                start_date = since_timestamp
                end_date = datetime.utcnow()
                logger.info(f"[SAHHA] Incremental score fetch for {external_id[:8]}... since {start_date.isoformat()}")
            else:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                logger.info(f"[SAHHA] Initial score fetch for {external_id[:8]}... ({days} days)")

            # Default types
            if not types:
                types = ["sleep", "activity", "wellbeing"]

            params = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "types": types,
                "version": 1.0
            }

            # Rate limiting delay
            await asyncio.sleep(self.request_delay)

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v1/profile/score/{external_id}",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        scores = await response.json()
                        logger.info(f"[SAHHA] Fetched {len(scores)} scores for {external_id[:8]}...")
                        return scores if scores else []
                    elif response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 2))
                        logger.warning(f"[SAHHA] Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        return []
                    else:
                        error = await response.text()
                        logger.error(f"[SAHHA] Score fetch failed: {response.status} {error}")
                        return []

        except Exception as e:
            logger.error(f"[SAHHA] Score fetch error for {external_id}: {e}")
            return []

    async def fetch_health_data(
        self,
        external_id: str,
        since_timestamp: Optional[datetime] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Fetch complete health data (biomarkers + scores) with incremental sync

        This is the main method used by analysis agents

        Args:
            external_id: User's external ID
            since_timestamp: Watermark for incremental fetch (None = initial fetch)
            days: Days to fetch if no watermark (default: 7)

        Returns:
            {
                "biomarkers": [...],
                "scores": [...],
                "fetched_at": "...",
                "is_incremental": True/False,
                "watermark": "..." or None
            }
        """

        logger.info(f"[SAHHA] Fetching health data for {external_id[:8]}... (watermark: {since_timestamp})")

        # Fetch in parallel for speed
        biomarkers_task = self.fetch_biomarkers(external_id, since_timestamp, days)
        scores_task = self.fetch_scores(external_id, since_timestamp, days)

        biomarkers, scores = await asyncio.gather(biomarkers_task, scores_task)

        result = {
            "biomarkers": biomarkers,
            "scores": scores,
            "fetched_at": datetime.utcnow().isoformat(),
            "is_incremental": since_timestamp is not None,
            "watermark": since_timestamp.isoformat() if since_timestamp else None,
            "total_items": len(biomarkers) + len(scores)
        }

        logger.info(
            f"[SAHHA] Fetched {len(biomarkers)} biomarkers + {len(scores)} scores "
            f"({'incremental' if since_timestamp else 'initial'})"
        )

        return result


# Singleton instance
_sahha_client = None


def get_sahha_client() -> SahhaClient:
    """Get or create singleton Sahha client"""
    global _sahha_client

    if _sahha_client is None:
        _sahha_client = SahhaClient()

    return _sahha_client
