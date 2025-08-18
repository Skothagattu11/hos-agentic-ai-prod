"""
Rate Limiting Middleware for HolisticOS

Adds rate limit headers and integrates with the monitoring system.
"""

import time
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from .rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to add rate limit headers to responses and handle rate limit exceptions
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint in chain
        
    Returns:
        Response with rate limit headers added
    """
    start_time = time.time()
    
    try:
        # Call the next middleware/endpoint
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        await _add_rate_limit_headers(request, response)
        
        return response
        
    except Exception as e:
        # Handle rate limit exceptions with proper headers
        if "rate limit" in str(e).lower() or "429" in str(e):
            logger.warning(f"Rate limit exceeded: {e}")
            return _create_rate_limit_error_response(request, str(e))
        elif "cost limit" in str(e).lower() or "402" in str(e):
            logger.warning(f"Cost limit exceeded: {e}")
            return _create_cost_limit_error_response(request, str(e))
        else:
            # Re-raise other exceptions
            raise e
    
    finally:
        # Log request timing (for monitoring)
        duration = time.time() - start_time
        if duration > 5.0:  # Log slow requests
            logger.warning(f"Slow request: {request.method} {request.url.path} took {duration:.2f}s")


async def _add_rate_limit_headers(request: Request, response: Response) -> None:
    """Add rate limit headers to response"""
    try:
        # Extract user_id from request
        user_id = request.path_params.get("user_id")
        if not user_id:
            # Try to extract from request body for analyze endpoint
            if hasattr(request, '_body') and request._body:
                import json
                try:
                    body = json.loads(request._body.decode())
                    user_id = body.get('user_id')
                except:
                    pass
        
        if user_id:
            # Get user statistics
            stats = await rate_limiter.get_user_stats(user_id)
            
            if "error" not in stats:
                # Add standard rate limit headers
                tier_limits = stats.get("rate_limits", {})
                cost_info = stats.get("cost_info", {})
                
                # General API limit
                general_limit = tier_limits.get("general_api", "50/hour")
                limit_value = general_limit.split("/")[0]
                
                response.headers["X-RateLimit-Limit"] = limit_value
                response.headers["X-RateLimit-Remaining"] = str(max(0, int(limit_value) - 1))  # Approximate
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 3600)  # 1 hour from now
                
                # Cost tracking headers
                if cost_info.get("redis_available", False):
                    response.headers["X-Cost-Used-Today"] = f"{cost_info.get('daily_cost', 0):.4f}"
                    response.headers["X-Cost-Limit-Daily"] = f"{cost_info.get('daily_limit', 1.0):.2f}"
                    response.headers["X-Cost-Remaining-Today"] = f"{max(0, cost_info.get('daily_limit', 1.0) - cost_info.get('daily_cost', 0)):.4f}"
                
                # User tier information
                response.headers["X-User-Tier"] = stats.get("tier", "free")
                
    except Exception as e:
        # Don't let header addition break the response
        logger.error(f"Failed to add rate limit headers: {e}")


def _create_rate_limit_error_response(request: Request, error_message: str) -> JSONResponse:
    """Create a standardized rate limit error response"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please wait before trying again.",
            "details": error_message,
            "retry_after": 3600,  # 1 hour
            "suggestion": "Consider upgrading to premium for higher limits",
            "timestamp": time.time()
        },
        headers={
            "Retry-After": "3600",
            "X-RateLimit-Exceeded": "true",
            "X-Error-Type": "rate_limit"
        }
    )


def _create_cost_limit_error_response(request: Request, error_message: str) -> JSONResponse:
    """Create a standardized cost limit error response"""
    return JSONResponse(
        status_code=402,
        content={
            "error": "Cost limit exceeded",
            "message": "Daily spending limit reached. Please wait until tomorrow or upgrade.",
            "details": error_message,
            "suggestion": "Upgrade to premium for higher daily limits",
            "timestamp": time.time()
        },
        headers={
            "X-Cost-Limit-Exceeded": "true",
            "X-Error-Type": "cost_limit"
        }
    )


async def add_rate_limit_context_middleware(request: Request, call_next: Callable) -> Response:
    """
    Lightweight middleware to store request body for rate limiting context
    
    This middleware captures the request body so it can be used by rate limiting
    to extract user_id from POST requests without path parameters.
    """
    if request.method == "POST":
        try:
            body = await request.body()
            # Store body for later use by rate limiter
            request._body = body
        except Exception as e:
            logger.debug(f"Could not capture request body: {e}")
    
    response = await call_next(request)
    return response