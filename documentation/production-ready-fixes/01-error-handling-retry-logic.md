# P0: Error Handling & Retry Logic

## Why This Issue Exists

### Current Problem
- Generic `except Exception as e:` catches everywhere in the codebase
- No distinction between transient vs permanent failures
- OpenAI API calls fail permanently on temporary network issues
- Users see "500 Internal Server Error" for recoverable failures
- No systematic approach to handling external service failures

### Impact on MVP
- **User Experience**: Users abandon requests that could succeed on retry
- **Cost**: Wasted API calls when subsequent calls would succeed
- **Reliability**: System appears broken when it's just a temporary issue
- **Debugging**: Generic errors make troubleshooting impossible

### Evidence from Current Code
```python
# services/api_gateway/openai_main.py:2817
except Exception as e:
    print(f"Error in 4o nutrition planning: {e}")
    return {"error": str(e), "model_used": "gpt-4o - fallback"}
```

## How to Fix

### Implementation Strategy

#### 1. Create Custom Exception Hierarchy
```python
# shared_libs/exceptions/holisticos_exceptions.py
class HolisticOSException(Exception):
    """Base exception for HolisticOS"""
    pass

class RetryableException(HolisticOSException):
    """Exceptions that should be retried"""
    pass

class PermanentException(HolisticOSException):
    """Exceptions that should not be retried"""
    pass

class OpenAIException(RetryableException):
    """OpenAI API specific exceptions"""
    def __init__(self, message: str, error_code: str = None, retry_after: int = None):
        self.error_code = error_code
        self.retry_after = retry_after
        super().__init__(message)

class DatabaseException(RetryableException):
    """Database connection exceptions"""
    pass

class ValidationException(PermanentException):
    """Input validation exceptions - don't retry"""
    pass
```

#### 2. Implement Retry Decorator
```python
# shared_libs/utils/retry_handler.py
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)
import logging

logger = logging.getLogger(__name__)

def retry_openai_calls():
    """Retry configuration specifically for OpenAI API calls"""
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(OpenAIException),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )

def retry_database_calls():
    """Retry configuration for database operations"""
    return retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(DatabaseException),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
```

#### 3. Create Circuit Breaker Pattern
```python
# shared_libs/utils/circuit_breaker.py
import time
from enum import Enum
from typing import Callable, Any
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing - reject calls
    HALF_OPEN = "half_open" # Testing - allow one call

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time < self.recovery_timeout:
                raise Exception("Circuit breaker is OPEN")
            else:
                self.state = CircuitState.HALF_OPEN
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

#### 4. Enhanced OpenAI Client
```python
# services/enhanced_openai_client.py
import openai
from shared_libs.utils.retry_handler import retry_openai_calls
from shared_libs.exceptions.holisticos_exceptions import OpenAIException

class EnhancedOpenAIClient:
    def __init__(self):
        self.client = openai.AsyncOpenAI()
        self.circuit_breaker = CircuitBreaker(failure_threshold=3)
    
    @retry_openai_calls()
    async def chat_completion(self, **kwargs):
        try:
            return await self.circuit_breaker.call(
                self.client.chat.completions.create,
                **kwargs
            )
        except openai.RateLimitError as e:
            raise OpenAIException(
                "Rate limit exceeded", 
                error_code="rate_limit",
                retry_after=e.retry_after
            )
        except openai.APITimeoutError as e:
            raise OpenAIException("API timeout", error_code="timeout")
        except openai.APIConnectionError as e:
            raise OpenAIException("Connection error", error_code="connection")
        except openai.AuthenticationError as e:
            raise PermanentException("Invalid API key")
        except Exception as e:
            raise OpenAIException(f"Unexpected OpenAI error: {str(e)}")
```

### Files to Modify

1. **services/api_gateway/openai_main.py**
   - Replace all OpenAI calls with EnhancedOpenAIClient
   - Add specific exception handling for each endpoint
   - Return meaningful error messages to users

2. **services/user_data_service.py**
   - Add database retry logic
   - Handle connection pool exhaustion gracefully
   - Implement query timeout handling

3. **All agent files in services/agents/**
   - Replace generic exception handling
   - Add context to error messages
   - Implement fallback responses

### Configuration
```python
# config/retry_config.py
RETRY_CONFIG = {
    "openai": {
        "max_attempts": 3,
        "base_delay": 2,
        "max_delay": 10,
        "backoff_multiplier": 2
    },
    "database": {
        "max_attempts": 2,
        "base_delay": 1,
        "max_delay": 5,
        "backoff_multiplier": 1.5
    },
    "circuit_breaker": {
        "failure_threshold": 5,
        "recovery_timeout": 60
    }
}
```

## What is the Expected Outcome

### Immediate Benefits
- **Improved Success Rate**: 95% of transient failures now succeed on retry
- **Better User Experience**: Users see helpful error messages, not generic 500s
- **Reduced Support Load**: Self-healing system reduces manual intervention
- **Cost Optimization**: Fewer failed API calls that don't count toward quotas

### Metrics to Track
```python
# Add these metrics to monitoring
error_metrics = {
    "total_requests": counter,
    "successful_requests": counter,
    "retried_requests": counter,
    "permanent_failures": counter,
    "circuit_breaker_opens": counter,
    "openai_rate_limits": counter,
    "database_connection_errors": counter
}
```

### Before vs After

**Before**:
```
User Request → OpenAI API Call → Network Timeout → 500 Error → User Retry
```

**After**:
```
User Request → Enhanced OpenAI Call → Network Timeout → Auto Retry (2s) → Success → User Happy
```

### Success Criteria
- [ ] Zero 500 errors for transient failures
- [ ] <3% permanent failure rate
- [ ] Average retry success rate >90%
- [ ] Circuit breaker prevents cascade failures
- [ ] Meaningful error messages for all failure types

### Testing Plan
1. **Unit Tests**: Test retry logic with mocked failures
2. **Integration Tests**: Test with actual OpenAI API rate limits
3. **Chaos Testing**: Simulate network failures, database outages
4. **Load Testing**: Verify system stability under retry load

### Dependencies
- `pip install tenacity` - For retry logic
- Update requirements.txt
- Environment variables for retry configuration

### Rollback Plan
- Keep original exception handling as fallback
- Feature flag to disable retries if issues arise
- Monitoring to detect retry storms

---

**Estimated Effort**: 2 days
**Risk Level**: Low (isolated changes)
**MVP Impact**: Critical - Users need reliable responses