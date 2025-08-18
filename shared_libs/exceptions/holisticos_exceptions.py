"""
Custom exception hierarchy for HolisticOS MVP
Provides specific exception types for better error handling and retry logic
"""

class HolisticOSException(Exception):
    """Base exception for all HolisticOS errors"""
    
    def __init__(self, message: str, error_code: str = None, retry_after: int = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.retry_after = retry_after  # Seconds to wait before retry
    
    def to_dict(self):
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "retry_after": self.retry_after
        }

# Retryable Exceptions (temporary failures)
class RetryableException(HolisticOSException):
    """Base class for exceptions that should be retried"""
    pass

class OpenAIException(RetryableException):
    """OpenAI API related errors"""
    pass

class DatabaseException(RetryableException):
    """Database connection and query errors"""
    pass

class NetworkException(RetryableException):
    """Network connectivity issues"""
    pass

class RateLimitException(RetryableException):
    """Rate limiting exceeded - should retry with backoff"""
    
    def __init__(self, message: str, retry_after: int = 3600):
        super().__init__(message, error_code="rate_limit_exceeded", retry_after=retry_after)

# Non-Retryable Exceptions (permanent failures)
class PermanentException(HolisticOSException):
    """Base class for exceptions that should NOT be retried"""
    pass

class ValidationException(PermanentException):
    """Invalid input data - don't retry"""
    pass

class AuthenticationException(PermanentException):
    """Invalid credentials - don't retry"""
    pass

class AuthorizationException(PermanentException):
    """Insufficient permissions - don't retry"""
    pass

class ConfigurationException(PermanentException):
    """System configuration errors - don't retry"""
    pass

# Service-Specific Exceptions
class BehaviorAnalysisException(HolisticOSException):
    """Behavior analysis service errors"""
    pass

class RoutineGenerationException(HolisticOSException):
    """Routine generation service errors"""
    pass

class NutritionGenerationException(HolisticOSException):
    """Nutrition generation service errors"""
    pass

class MemoryServiceException(HolisticOSException):
    """Memory management service errors"""
    pass

class InsightsGenerationException(HolisticOSException):
    """Insights generation service errors"""
    pass

# Circuit Breaker Exception
class CircuitBreakerException(HolisticOSException):
    """Service temporarily unavailable due to circuit breaker"""
    
    def __init__(self, service_name: str, retry_after: int = 300):
        message = f"Service {service_name} temporarily unavailable"
        super().__init__(message, error_code="circuit_breaker_open", retry_after=retry_after)
        self.service_name = service_name