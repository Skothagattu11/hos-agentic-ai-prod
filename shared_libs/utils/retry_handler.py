"""
Retry logic with exponential backoff for HolisticOS MVP
Provides decorators and utilities for handling temporary failures
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Type, Union, List
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

from shared_libs.exceptions.holisticos_exceptions import (
    RetryableException,
    OpenAIException,
    DatabaseException,
    NetworkException,
    PermanentException,
    CircuitBreakerException
)

logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuration for retry behavior"""
    
    # OpenAI API retries - more conservative due to cost
    OPENAI_RETRY_ATTEMPTS = 3
    OPENAI_WAIT_MIN = 1  # Start at 1 second
    OPENAI_WAIT_MAX = 60  # Max 60 seconds
    
    # Database retries - more aggressive for transient issues
    DATABASE_RETRY_ATTEMPTS = 5
    DATABASE_WAIT_MIN = 0.5
    DATABASE_WAIT_MAX = 30
    
    # Network retries - quick retries for connectivity
    NETWORK_RETRY_ATTEMPTS = 4
    NETWORK_WAIT_MIN = 0.1
    NETWORK_WAIT_MAX = 10
    
    # General service retries
    SERVICE_RETRY_ATTEMPTS = 3
    SERVICE_WAIT_MIN = 1
    SERVICE_WAIT_MAX = 30

def retry_openai_calls(max_attempts: int = None):
    """Decorator for OpenAI API calls with cost-conscious retry"""
    attempts = max_attempts or RetryConfig.OPENAI_RETRY_ATTEMPTS
    
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(
            multiplier=1,
            min=RetryConfig.OPENAI_WAIT_MIN,
            max=RetryConfig.OPENAI_WAIT_MAX
        ),
        retry=retry_if_exception_type((
            OpenAIException,
            NetworkException,
            ConnectionError,
            TimeoutError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )

def retry_database_operations(max_attempts: int = None):
    """Decorator for database operations with aggressive retry"""
    attempts = max_attempts or RetryConfig.DATABASE_RETRY_ATTEMPTS
    
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(
            multiplier=1,
            min=RetryConfig.DATABASE_WAIT_MIN,
            max=RetryConfig.DATABASE_WAIT_MAX
        ),
        retry=retry_if_exception_type((
            DatabaseException,
            NetworkException,
            ConnectionError,
            OSError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )

def retry_network_operations(max_attempts: int = None):
    """Decorator for network operations with quick retry"""
    attempts = max_attempts or RetryConfig.NETWORK_RETRY_ATTEMPTS
    
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(
            multiplier=1,
            min=RetryConfig.NETWORK_WAIT_MIN,
            max=RetryConfig.NETWORK_WAIT_MAX
        ),
        retry=retry_if_exception_type((
            NetworkException,
            ConnectionError,
            TimeoutError,
            OSError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )

def retry_service_operations(max_attempts: int = None, 
                           exception_types: List[Type[Exception]] = None):
    """Generic decorator for service operations"""
    attempts = max_attempts or RetryConfig.SERVICE_RETRY_ATTEMPTS
    
    # Default retryable exceptions
    if exception_types is None:
        exception_types = [RetryableException, NetworkException, ConnectionError]
    
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(
            multiplier=1,
            min=RetryConfig.SERVICE_WAIT_MIN,
            max=RetryConfig.SERVICE_WAIT_MAX
        ),
        retry=retry_if_exception_type(tuple(exception_types)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )

class AsyncRetryHandler:
    """Async retry handler with custom logic"""
    
    @staticmethod
    async def execute_with_retry(
        func: Callable,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        retryable_exceptions: tuple = None
    ) -> Any:
        """
        Execute function with custom retry logic
        
        Args:
            func: Async function to execute
            max_attempts: Maximum retry attempts
            base_delay: Initial delay between retries
            max_delay: Maximum delay between retries
            backoff_factor: Exponential backoff multiplier
            retryable_exceptions: Tuple of exception types to retry on
        """
        if retryable_exceptions is None:
            retryable_exceptions = (RetryableException, NetworkException, ConnectionError)
        
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return await func()
            except PermanentException:
                # Don't retry permanent exceptions
                raise
            except CircuitBreakerException:
                # Don't retry when circuit breaker is open
                raise
            except Exception as e:
                last_exception = e
                
                # Only retry if it's a retryable exception
                if not isinstance(e, retryable_exceptions):
                    raise
                
                # Don't sleep on the last attempt
                if attempt < max_attempts - 1:
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {max_attempts} attempts failed. Last error: {e}"
                    )
        
        # If we get here, all attempts failed
        raise last_exception

# Convenience functions for common patterns
async def retry_openai_call(func: Callable, *args, **kwargs) -> Any:
    """Retry OpenAI API call with appropriate settings"""
    return await AsyncRetryHandler.execute_with_retry(
        lambda: func(*args, **kwargs),
        max_attempts=RetryConfig.OPENAI_RETRY_ATTEMPTS,
        base_delay=RetryConfig.OPENAI_WAIT_MIN,
        max_delay=RetryConfig.OPENAI_WAIT_MAX,
        retryable_exceptions=(OpenAIException, NetworkException, ConnectionError, TimeoutError)
    )

async def retry_database_call(func: Callable, *args, **kwargs) -> Any:
    """Retry database call with appropriate settings"""
    return await AsyncRetryHandler.execute_with_retry(
        lambda: func(*args, **kwargs),
        max_attempts=RetryConfig.DATABASE_RETRY_ATTEMPTS,
        base_delay=RetryConfig.DATABASE_WAIT_MIN,
        max_delay=RetryConfig.DATABASE_WAIT_MAX,
        retryable_exceptions=(DatabaseException, NetworkException, ConnectionError, OSError)
    )