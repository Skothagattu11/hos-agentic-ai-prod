"""
Circuit breaker pattern implementation for HolisticOS MVP
Prevents cascading failures by temporarily blocking calls to failing services
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass
from shared_libs.exceptions.holisticos_exceptions import CircuitBreakerException

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Blocking calls due to failures
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5        # Failures before opening circuit
    recovery_timeout: int = 60        # Seconds before trying half-open
    success_threshold: int = 3        # Successes needed to close circuit
    timeout: int = 30                 # Request timeout in seconds

class CircuitBreaker:
    """Circuit breaker implementation for service protection"""
    
    def __init__(self, 
                 service_name: str, 
                 config: CircuitBreakerConfig = None):
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.next_attempt_time = None
        
        # Metrics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        
        logger.info(f"Circuit breaker initialized for service: {service_name}")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        self.total_requests += 1
        
        # Check if circuit should allow the call
        if not self._should_allow_request():
            raise CircuitBreakerException(
                service_name=self.service_name,
                retry_after=self._get_retry_after_seconds()
            )
        
        try:
            # Execute the function with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            # Record success
            self._record_success()
            return result
            
        except Exception as e:
            # Record failure
            self._record_failure()
            raise
    
    def _should_allow_request(self) -> bool:
        """Determine if request should be allowed based on circuit state"""
        now = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (self.last_failure_time and 
                now - self.last_failure_time >= self.config.recovery_timeout):
                self._transition_to_half_open()
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            # Allow limited requests to test service recovery
            return True
        
        return False
    
    def _record_success(self):
        """Record successful request"""
        self.total_successes += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _record_failure(self):
        """Record failed request"""
        self.total_failures += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            # If we fail in half-open, go back to open
            self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.next_attempt_time = time.time() + self.config.recovery_timeout
        
        logger.warning(
            f"Circuit breaker OPENED for service: {self.service_name}. "
            f"Failures: {self.failure_count}/{self.config.failure_threshold}"
        )
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        
        logger.info(
            f"Circuit breaker HALF_OPEN for service: {self.service_name}. "
            f"Testing service recovery..."
        )
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        
        logger.info(
            f"Circuit breaker CLOSED for service: {self.service_name}. "
            f"Service recovered successfully."
        )
    
    def _get_retry_after_seconds(self) -> int:
        """Get seconds until next retry attempt"""
        if self.next_attempt_time:
            return max(0, int(self.next_attempt_time - time.time()))
        return self.config.recovery_timeout
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "service_name": self.service_name,
            "state": self.state.value,
            "total_requests": self.total_requests,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_rate": (
                self.total_failures / self.total_requests 
                if self.total_requests > 0 else 0
            ),
            "next_attempt_time": self.next_attempt_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.next_attempt_time = None
        
        logger.info(f"Circuit breaker reset for service: {self.service_name}")

class CircuitBreakerRegistry:
    """Registry to manage multiple circuit breakers"""
    
    _instance = None
    _circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_circuit_breaker(self, 
                           service_name: str, 
                           config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self._circuit_breakers:
            self._circuit_breakers[service_name] = CircuitBreaker(
                service_name=service_name,
                config=config
            )
        return self._circuit_breakers[service_name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {
            name: cb.get_stats() 
            for name, cb in self._circuit_breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for cb in self._circuit_breakers.values():
            cb.reset()
        logger.info("All circuit breakers reset")

# Global registry instance
circuit_registry = CircuitBreakerRegistry()

# Convenience decorators
def with_circuit_breaker(service_name: str, config: CircuitBreakerConfig = None):
    """Decorator to add circuit breaker protection to async functions"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            cb = circuit_registry.get_circuit_breaker(service_name, config)
            return await cb.call(func, *args, **kwargs)
        return wrapper
    return decorator

# Pre-configured circuit breakers for common services
def openai_circuit_breaker():
    """Circuit breaker optimized for OpenAI API calls"""
    config = CircuitBreakerConfig(
        failure_threshold=3,  # More sensitive due to cost
        recovery_timeout=120, # Longer recovery time
        success_threshold=2,  # Fewer successes needed
        timeout=60           # Longer timeout for GPT calls
    )
    return with_circuit_breaker("openai", config)

def database_circuit_breaker():
    """Circuit breaker optimized for database operations"""
    config = CircuitBreakerConfig(
        failure_threshold=5,  # More tolerant of transient issues
        recovery_timeout=30,  # Quick recovery
        success_threshold=3,  # Standard successes needed
        timeout=30           # Standard timeout
    )
    return with_circuit_breaker("database", config)

def external_api_circuit_breaker():
    """Circuit breaker for external API calls"""
    config = CircuitBreakerConfig(
        failure_threshold=3,  # Standard threshold
        recovery_timeout=60,  # Standard recovery
        success_threshold=2,  # Quick recovery
        timeout=30           # Standard timeout
    )
    return with_circuit_breaker("external_api", config)