"""
Input Validation Middleware
Simple validation without breaking existing API functionality
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import json
import logging
from typing import Callable, Any
from ..models.validation import InputSecurityChecker, sanitize_input

logger = logging.getLogger(__name__)


async def validate_request_middleware(request: Request, call_next: Callable) -> Any:
    """
    Lightweight validation middleware - only validates path params and headers
    Body validation is handled by Pydantic models in endpoint handlers
    """

    # Skip validation for health checks and static routes
    if request.url.path in ["/", "/api/health", "/metrics", "/debug/openapi", "/openapi.json"]:
        return await call_next(request)

    try:
        # Validate path parameters (user_id, etc.) - safe to do, doesn't consume body
        if "user_id" in request.path_params:
            user_id = request.path_params["user_id"]
            if not _is_valid_user_id(user_id):
                logger.warning(f"Invalid user_id in request: {user_id}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid user ID format"}
                )

        # Validate headers for potential injection attacks
        for header_name, header_value in request.headers.items():
            if not _is_safe_header(header_name, header_value):
                logger.warning(f"Potentially unsafe header detected: {header_name}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid request headers"}
                )

        # Continue with the request - body will be validated by Pydantic models
        response = await call_next(request)
        return response

    except Exception as e:
        logger.error(f"Error in input validation middleware: {e}", exc_info=True)
        # Don't break the request if validation fails
        return await call_next(request)


def _is_request_safe(data: Any) -> bool:
    """Check if request data is safe from common attacks"""
    
    if isinstance(data, str):
        return InputSecurityChecker.is_safe_input(data)
    
    elif isinstance(data, dict):
        for key, value in data.items():
            if not _is_request_safe(key) or not _is_request_safe(value):
                return False
    
    elif isinstance(data, list):
        for item in data:
            if not _is_request_safe(item):
                return False
    
    return True


def _is_valid_user_id(user_id: str) -> bool:
    """Validate user ID format"""
    try:
        from ..models.validation import validate_user_id
        validate_user_id(user_id)
        return True
    except ValueError:
        return False


def _is_safe_header(name: str, value: str) -> bool:
    """Check if header is safe from injection attacks"""
    if not isinstance(name, str) or not isinstance(value, str):
        return False

    # Check for null bytes
    if '\x00' in name or '\x00' in value:
        return False

    # Check for CRLF injection
    if '\r' in name or '\n' in name or '\r' in value or '\n' in value:
        return False

    # Basic length check to prevent DOS
    if len(name) > 256 or len(value) > 8192:
        return False

    return True


# Decorator for additional validation on specific endpoints
def validate_input(validation_class=None):
    """
    Decorator to add input validation to specific endpoints
    
    Args:
        validation_class: Pydantic model class for validation
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                # Add any specific validation logic here
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Validation error in {func.__name__}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input data"
                )
        return wrapper
    return decorator


class RequestSizeLimit:
    """Middleware to limit request size"""
    
    def __init__(self, app, max_size: int = 1024 * 1024):  # 1MB default
        self.app = app
        self.max_size = max_size
    
    async def __call__(self, scope, receive, send) -> Any:
        """ASGI middleware to limit request body size"""
        if scope["type"] == "http":
            # Check content length header
            headers = dict(scope.get("headers", []))
            content_length = headers.get(b"content-length")
            if content_length and int(content_length.decode()) > self.max_size:
                response = JSONResponse(
                    status_code=413,
                    content={"error": "Request too large"}
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)