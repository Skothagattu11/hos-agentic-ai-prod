# P0: Request Timeouts

## Why This Issue Exists

### Current Problem
- No timeouts configured for external API calls
- OpenAI API calls can hang indefinitely
- Supabase requests can block forever
- Users experience frozen applications
- Server resources get exhausted by hanging requests

### Evidence from Current Code
```python
# services/api_gateway/openai_main.py:2769
response = await client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    # NO TIMEOUT SPECIFIED - Can hang forever!
)

# services/user_data_service.py:424
async with session.get(url) as response:
    # NO TIMEOUT - Supabase calls can hang
```

### Impact on Render 0.5 CPU Instance
- **Resource Exhaustion**: Hanging requests consume worker threads
- **Poor UX**: Users wait indefinitely for responses
- **Cascade Failures**: One slow service affects entire system
- **Memory Leaks**: Hanging connections accumulate

### Real-World Scenarios
```
Scenario 1: OpenAI API Timeout
User Request → OpenAI API → Network Issue → Hangs Forever → User Abandons

Scenario 2: Database Timeout  
Analysis Request → Supabase Query → Slow Query → Blocks Thread → System Freezes

Scenario 3: Memory Exhaustion
50 Hanging Requests × 64MB each = 3.2GB Memory Usage (Crash on 0.5 CPU)
```

## How to Fix

### Implementation Strategy

#### 1. Create Timeout Configuration System
```python
# config/timeout_config.py
from dataclasses import dataclass
from typing import Dict, Any
import os

@dataclass
class TimeoutConfig:
    """Centralized timeout configuration"""
    
    # OpenAI API timeouts (in seconds)
    openai_request_timeout: int = 30
    openai_connect_timeout: int = 10
    openai_read_timeout: int = 60  # GPT-4 can be slow
    
    # Database timeouts
    database_query_timeout: int = 30
    database_connect_timeout: int = 10
    
    # HTTP client timeouts
    http_total_timeout: int = 30
    http_connect_timeout: int = 10
    http_read_timeout: int = 20
    
    # Internal service timeouts
    behavior_analysis_timeout: int = 120  # Complex analysis
    routine_generation_timeout: int = 60
    nutrition_generation_timeout: int = 60
    insights_generation_timeout: int = 45
    
    # Memory service timeouts
    memory_store_timeout: int = 15
    memory_retrieval_timeout: int = 10
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            openai_request_timeout=int(os.getenv("OPENAI_REQUEST_TIMEOUT", 30)),
            openai_connect_timeout=int(os.getenv("OPENAI_CONNECT_TIMEOUT", 10)),
            openai_read_timeout=int(os.getenv("OPENAI_READ_TIMEOUT", 60)),
            database_query_timeout=int(os.getenv("DATABASE_QUERY_TIMEOUT", 30)),
            # ... other timeouts
        )

# Global timeout configuration
TIMEOUTS = TimeoutConfig.from_env()
```

#### 2. Enhanced OpenAI Client with Timeouts
```python
# services/enhanced_openai_client.py
import openai
import asyncio
from config.timeout_config import TIMEOUTS
from shared_libs.exceptions.holisticos_exceptions import OpenAIException

class TimeoutOpenAIClient:
    """OpenAI client with comprehensive timeout handling"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(
            timeout=openai.Timeout(
                total=TIMEOUTS.openai_request_timeout,
                connect=TIMEOUTS.openai_connect_timeout,
                read=TIMEOUTS.openai_read_timeout,
                write=10.0
            )
        )
    
    async def chat_completion_with_timeout(self, **kwargs):
        """Chat completion with timeout and cancellation handling"""
        try:
            # Use asyncio.wait_for for additional timeout layer
            return await asyncio.wait_for(
                self.client.chat.completions.create(**kwargs),
                timeout=TIMEOUTS.openai_request_timeout
            )
        except asyncio.TimeoutError:
            raise OpenAIException(
                f"OpenAI request timed out after {TIMEOUTS.openai_request_timeout}s",
                error_code="timeout"
            )
        except openai.APITimeoutError as e:
            raise OpenAIException(
                f"OpenAI API timeout: {str(e)}",
                error_code="api_timeout"
            )
        except Exception as e:
            raise OpenAIException(f"OpenAI error: {str(e)}")
    
    async def with_fallback_timeout(self, primary_timeout: int, fallback_response: dict, **kwargs):
        """Try with timeout, return fallback if timeout occurs"""
        try:
            return await asyncio.wait_for(
                self.chat_completion_with_timeout(**kwargs),
                timeout=primary_timeout
            )
        except (asyncio.TimeoutError, OpenAIException) as e:
            logger.warning(f"OpenAI timeout, using fallback: {e}")
            return fallback_response
```

#### 3. HTTP Client with Timeouts
```python
# shared_libs/http/timeout_client.py
import aiohttp
import asyncio
from config.timeout_config import TIMEOUTS
import logging

logger = logging.getLogger(__name__)

class TimeoutHTTPClient:
    """HTTP client with comprehensive timeout configuration"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(
            total=TIMEOUTS.http_total_timeout,
            connect=TIMEOUTS.http_connect_timeout,
            sock_read=TIMEOUTS.http_read_timeout,
            sock_connect=TIMEOUTS.http_connect_timeout
        )
    
    async def get_with_timeout(self, url: str, **kwargs):
        """GET request with timeout handling"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, **kwargs) as response:
                    return await response.json()
        except asyncio.TimeoutError:
            logger.error(f"HTTP GET timeout: {url}")
            raise Exception(f"Request to {url} timed out after {TIMEOUTS.http_total_timeout}s")
        except aiohttp.ClientError as e:
            logger.error(f"HTTP GET error: {url} - {e}")
            raise Exception(f"HTTP request failed: {e}")
    
    async def post_with_timeout(self, url: str, **kwargs):
        """POST request with timeout handling"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, **kwargs) as response:
                    return await response.json()
        except asyncio.TimeoutError:
            logger.error(f"HTTP POST timeout: {url}")
            raise Exception(f"Request to {url} timed out after {TIMEOUTS.http_total_timeout}s")
        except aiohttp.ClientError as e:
            logger.error(f"HTTP POST error: {url} - {e}")
            raise Exception(f"HTTP request failed: {e}")
```

#### 4. Update Database Operations with Timeouts
```python
# shared_libs/database/connection_pool.py - UPDATED
import asyncpg
import asyncio
from config.timeout_config import TIMEOUTS

class DatabasePool:
    async def execute_query_with_timeout(self, query: str, *args, timeout: int = None):
        """Execute query with timeout protection"""
        timeout = timeout or TIMEOUTS.database_query_timeout
        
        try:
            async with self.get_connection() as conn:
                return await asyncio.wait_for(
                    conn.fetch(query, *args),
                    timeout=timeout
                )
        except asyncio.TimeoutError:
            logger.error(f"Database query timeout: {query[:100]}...")
            raise DatabaseException(f"Query timed out after {timeout}s")
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            raise DatabaseException(f"Database error: {e}")
    
    async def execute_one_with_timeout(self, query: str, *args, timeout: int = None):
        """Execute single-row query with timeout"""
        timeout = timeout or TIMEOUTS.database_query_timeout
        
        try:
            async with self.get_connection() as conn:
                return await asyncio.wait_for(
                    conn.fetchrow(query, *args),
                    timeout=timeout
                )
        except asyncio.TimeoutError:
            logger.error(f"Database fetchrow timeout: {query[:100]}...")
            raise DatabaseException(f"Query timed out after {timeout}s")
```

#### 5. Service-Level Timeout Decorators
```python
# shared_libs/utils/timeout_decorators.py
import asyncio
import functools
from config.timeout_config import TIMEOUTS
import logging

logger = logging.getLogger(__name__)

def with_timeout(timeout_seconds: int, fallback_response=None):
    """Decorator to add timeout to any async function"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.warning(f"{func.__name__} timed out after {timeout_seconds}s")
                if fallback_response is not None:
                    return fallback_response
                raise Exception(f"{func.__name__} timed out after {timeout_seconds}s")
        return wrapper
    return decorator

def behavior_analysis_timeout(func):
    """Specific timeout for behavior analysis"""
    return with_timeout(TIMEOUTS.behavior_analysis_timeout)(func)

def routine_generation_timeout(func):
    """Specific timeout for routine generation"""
    return with_timeout(TIMEOUTS.routine_generation_timeout)(func)

def memory_operation_timeout(func):
    """Specific timeout for memory operations"""
    return with_timeout(TIMEOUTS.memory_store_timeout)(func)
```

#### 6. Update API Endpoints with Timeouts
```python
# services/api_gateway/openai_main.py - KEY UPDATES

from shared_libs.utils.timeout_decorators import (
    behavior_analysis_timeout,
    routine_generation_timeout
)
from services.enhanced_openai_client import TimeoutOpenAIClient

# Replace OpenAI client
openai_client = TimeoutOpenAIClient()

@app.post("/api/user/{user_id}/routine/generate")
@routine_generation_timeout
async def generate_fresh_routine_plan(user_id: str, request: PlanGenerationRequest):
    """Routine generation with timeout protection"""
    try:
        # This entire function is now protected by timeout
        behavior_analysis = await get_or_create_shared_behavior_analysis(
            user_id, request.archetype
        )
        
        # OpenAI calls automatically have timeouts
        routine_plan = await run_memory_enhanced_routine_generation(
            user_id=user_id,
            archetype=request.archetype,
            behavior_analysis=behavior_analysis
        )
        
        return RoutinePlanResponse(
            status="success",
            user_id=user_id,
            routine_plan=routine_plan,
            # ... rest of response
        )
    except asyncio.TimeoutError:
        # Timeout occurred - return partial response
        return RoutinePlanResponse(
            status="timeout",
            user_id=user_id,
            routine_plan={"error": "Request timed out, please try again"},
            generation_metadata={
                "timeout_seconds": TIMEOUTS.routine_generation_timeout,
                "suggestion": "Try again in a few minutes"
            }
        )

@behavior_analysis_timeout
async def run_fresh_behavior_analysis_like_api_analyze(
    user_id: str, 
    archetype: str, 
    ondemand_metadata: dict = None
) -> dict:
    """Behavior analysis with timeout protection"""
    # Function body remains the same - decorator handles timeout
    # ...existing code...
```

### Configuration Management

```python
# Environment variables for Render deployment
RENDER_TIMEOUT_ENV_VARS = {
    "OPENAI_REQUEST_TIMEOUT": "30",
    "OPENAI_READ_TIMEOUT": "60",
    "DATABASE_QUERY_TIMEOUT": "30", 
    "HTTP_TOTAL_TIMEOUT": "30",
    "BEHAVIOR_ANALYSIS_TIMEOUT": "120",
    "ROUTINE_GENERATION_TIMEOUT": "60",
    "MEMORY_OPERATION_TIMEOUT": "15"
}
```

## What is the Expected Outcome

### Reliability Improvements
- **No Hanging Requests**: All requests complete within defined timeouts
- **Resource Protection**: Prevents worker thread exhaustion
- **Better UX**: Users get responses (even error responses) quickly
- **Graceful Degradation**: Fallback responses when services are slow

### Performance Metrics
```python
timeout_metrics = {
    "requests_completed_within_timeout": "99%+",
    "timeout_errors": "<1%",
    "average_response_time": "<5s",
    "hanging_requests": "0",
    "worker_thread_utilization": "<80%"
}
```

### Before vs After Behavior

**Before (No Timeouts)**:
```
User Request → OpenAI API (slow) → Hangs for 5 minutes → User Abandons
```

**After (With Timeouts)**:
```
User Request → OpenAI API (slow) → 30s timeout → Fallback Response → User Informed
```

### Timeout Strategy by Service

| Service | Timeout | Fallback Strategy |
|---------|---------|-------------------|
| OpenAI Chat | 30s | Cached response or error message |
| OpenAI Behavior Analysis | 120s | Simplified analysis |
| Database Query | 30s | Error with retry suggestion |
| Memory Operations | 15s | Skip memory enhancement |
| HTTP Requests | 30s | Error response |

### Success Criteria
- [ ] No requests hang longer than configured timeouts
- [ ] Fallback responses for timeout scenarios
- [ ] Timeout configuration via environment variables
- [ ] Monitoring of timeout occurrences
- [ ] Graceful cancellation of timed-out operations

### Monitoring Integration
```python
# Add to health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timeout_config": {
            "openai_timeout": TIMEOUTS.openai_request_timeout,
            "database_timeout": TIMEOUTS.database_query_timeout,
            "max_request_time": max(TIMEOUTS.behavior_analysis_timeout, 
                                  TIMEOUTS.routine_generation_timeout)
        },
        "active_timeouts": get_active_timeout_count()
    }
```

### Testing Plan
```python
# Timeout testing scenarios
async def test_timeout_scenarios():
    # Test 1: Simulate slow OpenAI API
    with mock_slow_openai(delay=45):  # Slower than 30s timeout
        response = await generate_routine()
        assert response.status == "timeout"
    
    # Test 2: Simulate slow database
    with mock_slow_database(delay=35):  # Slower than 30s timeout
        response = await get_user_data()
        assert "timed out" in response.error
    
    # Test 3: Normal operation under timeout
    response = await generate_routine()  # Should complete in <30s
    assert response.status == "success"
```

### Dependencies
- Update timeout configuration in environment
- Ensure all async operations use timeout wrappers
- Add fallback responses for each service

### Risk Mitigation
- Conservative timeout values (not too aggressive)
- Gradual rollout with monitoring
- Fallback responses maintain user experience
- Easy to adjust timeouts via environment variables

---

**Estimated Effort**: 1 day
**Risk Level**: Low (improves stability)
**MVP Impact**: Critical - Prevents system freezes