"""
HealthDataClient - MVP Implementation for hos-fapi-hm-sahha-main Integration
CTO Design: Simple, Reliable, Easy to Debug, Production Ready
"""
import os
import asyncio
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    """Simple response wrapper for debugging"""
    success: bool
    data: List[Dict[str, Any]]
    status_code: int
    duration_ms: float
    error: Optional[str] = None

class HealthDataClient:
    """
    MVP API Client for hos-fapi-hm-sahha-main integration
    Focus: Reliability, Simplicity, Clear Error Handling
    """
    
    def __init__(self, base_url: str = None):
        """Initialize with sensible defaults - MVP pattern"""
        self.base_url = (base_url or os.getenv("HOS_FAPI_BASE_URL", "https://hos-fapi-hm-sahha.onrender.com")).rstrip('/')
        
        # Production-ready timeouts and retries
        self.timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
        # Simple request tracking for debugging
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        
        logger.debug(f"[API_CLIENT] Initialized for {self.base_url}")  # Reduced noise

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """
        Core request method - handles retries, timeouts, errors
        MVP: Simple but robust implementation
        """
        url = f"{self.base_url}{endpoint}"
        start_time = datetime.now()
        self.request_count += 1
        
        # logger.debug(f"[API_REQUEST] {endpoint} with params: {params}")  # Too noisy - commented out
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params)
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Handle different response scenarios
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Handle different response formats from hos-fapi
                        if isinstance(data, dict):
                            if 'data' in data:
                                actual_data = data['data']
                            elif 'items' in data:
                                actual_data = data['items']
                            elif 'results' in data:
                                actual_data = data['results']
                            else:
                                # Assume the whole response is data
                                actual_data = [data] if not isinstance(data, list) else data
                        else:
                            actual_data = data if isinstance(data, list) else [data]
                        
                        self.success_count += 1
                        logger.debug(f"[API_SUCCESS] {endpoint}: {len(actual_data)} records in {duration:.0f}ms")
                        
                        return APIResponse(
                            success=True,
                            data=actual_data,
                            status_code=response.status_code,
                            duration_ms=duration
                        )
                    
                    elif response.status_code == 404:
                        # Not found is OK - user might not have data
                        logger.debug(f"[API_NO_DATA] {endpoint}: No data found (404)")
                        return APIResponse(
                            success=True,
                            data=[],
                            status_code=response.status_code,
                            duration_ms=duration
                        )
                    
                    elif response.status_code == 429:
                        # Rate limited - exponential backoff
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(f"[API_RATE_LIMITED] {endpoint}: Retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        # Other HTTP errors
                        logger.warning(f"[API_HTTP_ERROR] {endpoint}: Status {response.status_code}, attempt {attempt + 1}")
                        if attempt == self.max_retries - 1:
                            self.error_count += 1
                            return APIResponse(
                                success=False,
                                data=[],
                                status_code=response.status_code,
                                duration_ms=duration,
                                error=f"HTTP {response.status_code}"
                            )
                        
                        await asyncio.sleep(self.retry_delay)
                        continue
                        
            except httpx.TimeoutException:
                logger.warning(f"[API_TIMEOUT] {endpoint}: Timeout on attempt {attempt + 1}")
                if attempt == self.max_retries - 1:
                    self.error_count += 1
                    return APIResponse(
                        success=False,
                        data=[],
                        status_code=0,
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                        error="Request timeout"
                    )
                await asyncio.sleep(self.retry_delay)
                
            except Exception as e:
                logger.error(f"[API_ERROR] {endpoint}: {str(e)} on attempt {attempt + 1}")
                if attempt == self.max_retries - 1:
                    self.error_count += 1
                    return APIResponse(
                        success=False,
                        data=[],
                        status_code=0,
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                        error=str(e)
                    )
                await asyncio.sleep(self.retry_delay)
        
        # Should never reach here, but safety net
        self.error_count += 1
        return APIResponse(
            success=False,
            data=[],
            status_code=0,
            duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
            error="Max retries exceeded"
        )

    async def get_user_scores(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Fetch user health scores from hos-fapi
        MVP: Simple, reliable implementation
        """
        params = {
            'user_id': user_id,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'limit': 1000  # Reasonable limit
        }
        
        response = await self._make_request('/api/v1/sahha/scores', params)
        
        if response.success:
            # Clean and validate data
            clean_data = []
            for item in response.data:
                try:
                    # Ensure required fields exist
                    if all(key in item for key in ['id', 'profile_id', 'type', 'score']):
                        clean_data.append(item)
                    else:
                        logger.warning(f"[API_DATA_WARNING] Skipping incomplete score record: {item.get('id', 'unknown')}")
                except Exception as e:
                    logger.warning(f"[API_DATA_ERROR] Error processing score record: {e}")
                    continue
            
            return clean_data
        else:
            logger.error(f"[API_SCORES_ERROR] Failed to fetch scores for {user_id}: {response.error}")
            return []

    async def get_user_biomarkers(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch user biomarkers from hos-fapi"""
        params = {
            'user_id': user_id,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'limit': 1000
        }
        
        response = await self._make_request('/api/v1/sahha/biomarkers', params)
        
        if response.success:
            clean_data = []
            for item in response.data:
                try:
                    if all(key in item for key in ['id', 'profile_id', 'category', 'type']):
                        clean_data.append(item)
                    else:
                        logger.warning(f"[API_DATA_WARNING] Skipping incomplete biomarker record: {item.get('id', 'unknown')}")
                except Exception as e:
                    logger.warning(f"[API_DATA_ERROR] Error processing biomarker record: {e}")
                    continue
            
            return clean_data
        else:
            logger.error(f"[API_BIOMARKERS_ERROR] Failed to fetch biomarkers for {user_id}: {response.error}")
            return []

    async def get_user_archetypes(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch user archetypes from hos-fapi"""
        params = {
            'user_id': user_id,
            'limit': 100  # Archetypes are typically fewer
        }
        
        response = await self._make_request('/api/v1/sahha/archetypes', params)
        
        if response.success:
            clean_data = []
            for item in response.data:
                try:
                    if all(key in item for key in ['id', 'profile_id', 'name']):
                        clean_data.append(item)
                    else:
                        logger.warning(f"[API_DATA_WARNING] Skipping incomplete archetype record: {item.get('id', 'unknown')}")
                except Exception as e:
                    logger.warning(f"[API_DATA_ERROR] Error processing archetype record: {e}")
                    continue
            
            return clean_data
        else:
            logger.error(f"[API_ARCHETYPES_ERROR] Failed to fetch archetypes for {user_id}: {response.error}")
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Simple health check - essential for monitoring"""
        try:
            # Simple health check endpoint
            response = await self._make_request('/health', {})
            
            return {
                'api_status': 'healthy' if response.success else 'unhealthy',
                'base_url': self.base_url,
                'request_stats': {
                    'total_requests': self.request_count,
                    'successful_requests': self.success_count,
                    'failed_requests': self.error_count,
                    'success_rate': self.success_count / max(self.request_count, 1) * 100
                },
                'last_response_time_ms': response.duration_ms,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'api_status': 'unhealthy',
                'error': str(e),
                'base_url': self.base_url,
                'timestamp': datetime.now().isoformat()
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics - useful for debugging"""
        return {
            'total_requests': self.request_count,
            'successful_requests': self.success_count,
            'failed_requests': self.error_count,
            'success_rate': self.success_count / max(self.request_count, 1) * 100,
            'base_url': self.base_url
        }

# Convenience functions for easy import
async def fetch_user_health_from_api(user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, List[Dict]]:
    """Simple function interface for getting all user health data from API"""
    client = HealthDataClient()
    
    try:
        # Fetch all data types concurrently
        tasks = [
            client.get_user_scores(user_id, start_date, end_date),
            client.get_user_biomarkers(user_id, start_date, end_date),
            client.get_user_archetypes(user_id)
        ]
        
        scores, biomarkers, archetypes = await asyncio.gather(*tasks)
        
        return {
            'scores': scores,
            'biomarkers': biomarkers,
            'archetypes': archetypes,
            'stats': client.get_stats()
        }
    except Exception as e:
        logger.error(f"[API_FETCH_ERROR] Failed to fetch health data for {user_id}: {e}")
        return {
            'scores': [],
            'biomarkers': [],
            'archetypes': [],
            'error': str(e)
        }

if __name__ == "__main__":
    # Simple test for development
    async def test():
        client = HealthDataClient()
        
        # Test health check
        health = await client.health_check()
        print(f"Health check: {health}")
        
        # Test with a real user if available
        # from datetime import timedelta
        # end_date = datetime.now()
        # start_date = end_date - timedelta(days=7)
        # data = await fetch_user_health_from_api("test_user", start_date, end_date)
        # print(f"API data: {len(data['scores'])} scores, {len(data['biomarkers'])} biomarkers")
    
    asyncio.run(test())