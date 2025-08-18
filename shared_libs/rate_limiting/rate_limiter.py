"""
HolisticOS Rate Limiter

Redis-based rate limiting with cost tracking and tier-based limits.
Integrates with existing error handling and timeout systems.
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
import logging

import redis.asyncio as redis
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import existing error handling
try:
    from shared_libs.exceptions.holisticos_exceptions import (
        HolisticOSException, RateLimitException, CostLimitException
    )
    from shared_libs.utils.retry_handler import exponential_backoff_retry
    EXCEPTIONS_AVAILABLE = True
except ImportError:
    # Fallback if exceptions module not available
    HolisticOSException = Exception
    RateLimitException = Exception
    CostLimitException = Exception
    EXCEPTIONS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RateLimitTier(Enum):
    """Different rate limit tiers for different users"""
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"


class HolisticRateLimiter:
    """
    Custom rate limiter for HolisticOS with cost tracking and tier-based limits.
    
    Features:
    - Redis-based storage with connection pooling
    - Tier-based rate limiting (free/premium/admin)
    - Cost tracking with daily/monthly limits
    - Integration with existing error handling
    - Graceful degradation when Redis unavailable
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self._redis_pool = None
        self._redis_available = bool(self.redis_url)  # Only available if URL is configured
        
        # In-memory rate limiting for development (when Redis not available)
        self._in_memory_limits = {}  # {user_id:endpoint_type: {"count": int, "reset_time": float}}
        
        # Rate limit configurations per tier
        self.tier_limits = {
            RateLimitTier.FREE: {
                "behavior_analysis": "5/hour",    # 5 behavior analyses per hour
                "routine_generation": "10/hour",  # 10 routine plans per hour
                "nutrition_generation": "10/hour", # 10 nutrition plans per hour
                "insights_generation": "20/hour", # 20 insights requests per hour
                "general_api": "50/hour"          # 50 general API calls per hour
            },
            RateLimitTier.PREMIUM: {
                "behavior_analysis": "20/hour",
                "routine_generation": "40/hour",
                "nutrition_generation": "40/hour",
                "insights_generation": "100/hour",
                "general_api": "200/hour"
            },
            RateLimitTier.ADMIN: {
                "behavior_analysis": "1000/hour", # Practically unlimited for admin
                "routine_generation": "1000/hour",
                "nutrition_generation": "1000/hour",
                "insights_generation": "1000/hour",
                "general_api": "1000/hour"
            }
        }
        
        # Cost limits per tier (in USD)
        self.cost_limits = {
            RateLimitTier.FREE: {"daily": 1.0, "monthly": 10.0},      # $1/day, $10/month
            RateLimitTier.PREMIUM: {"daily": 10.0, "monthly": 100.0}, # $10/day, $100/month
            RateLimitTier.ADMIN: {"daily": 1000.0, "monthly": 10000.0} # No real limits
        }
        
        # Cost estimates per endpoint (in USD)
        self.endpoint_costs = {
            "behavior_analysis": 0.03,     # Most expensive - full analysis
            "routine_generation": 0.02,    # Moderate cost
            "nutrition_generation": 0.02,  # Moderate cost
            "insights_generation": 0.01,   # Lower cost
            "general_api": 0.005          # Minimal cost
        }
        
        # Initialize slowapi limiter
        self.limiter = Limiter(
            key_func=self._get_user_identifier,
            storage_uri=self.redis_url
        )
    
    async def _get_redis_pool(self) -> Optional[redis.Redis]:
        """Get Redis connection pool with error handling"""
        if not self._redis_available:
            return None
            
        if self._redis_pool is None:
            try:
                self._redis_pool = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0
                )
                # Test connection
                await self._redis_pool.ping()
                logger.info("✅ Redis connection established for rate limiting")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                self._redis_available = False
                return None
        
        return self._redis_pool
    
    def _get_user_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Try to get user_id from path parameters
        user_id = request.path_params.get("user_id")
        if user_id:
            return f"user:{user_id}"
        
        # Try to get from request body for endpoints without user_id in path
        if hasattr(request, '_body') and request._body:
            try:
                body = json.loads(request._body.decode())
                if 'user_id' in body:
                    return f"user:{body['user_id']}"
            except:
                pass
        
        # Fallback to IP address
        return get_remote_address(request)
    
    def _get_user_tier(self, user_id: str) -> RateLimitTier:
        """Determine user's rate limit tier"""
        # For MVP, all users are FREE tier
        # TODO: Implement user tier lookup from database
        if user_id.startswith("admin_"):
            return RateLimitTier.ADMIN
        elif user_id.startswith("premium_"):
            return RateLimitTier.PREMIUM
        else:
            return RateLimitTier.FREE
    
    def get_limit_for_endpoint(self, endpoint_type: str, user_id: str) -> str:
        """Get rate limit for specific endpoint and user"""
        tier = self._get_user_tier(user_id)
        return self.tier_limits[tier].get(endpoint_type, "10/hour")
    
    async def check_cost_limits(self, user_id: str) -> Dict[str, Any]:
        """
        Check if user has exceeded cost limits
        
        Returns:
            Dict with cost information and whether user is within limits
        """
        redis_client = await self._get_redis_pool()
        if not redis_client:
            # If Redis unavailable, allow requests (expected in development)
            logger.debug("Redis unavailable for cost checking - allowing request")
            return {
                "daily_cost": 0.0,
                "monthly_cost": 0.0,
                "daily_limit": 1000.0,  # High fallback limit
                "monthly_limit": 10000.0,
                "within_limits": True,
                "redis_available": False
            }
        
        try:
            daily_cost_key = f"cost:daily:{user_id}"
            monthly_cost_key = f"cost:monthly:{user_id}"
            
            daily_cost = float(await redis_client.get(daily_cost_key) or 0)
            monthly_cost = float(await redis_client.get(monthly_cost_key) or 0)
            
            # Get cost limits for user tier
            tier = self._get_user_tier(user_id)
            tier_limits = self.cost_limits[tier]
            
            result = {
                "daily_cost": daily_cost,
                "monthly_cost": monthly_cost,
                "daily_limit": tier_limits["daily"],
                "monthly_limit": tier_limits["monthly"],
                "within_limits": daily_cost < tier_limits["daily"] and monthly_cost < tier_limits["monthly"],
                "redis_available": True
            }
            
            # Log cost tracking
            logger.info(f"Cost check: user={user_id}, daily=${daily_cost:.4f}/{tier_limits['daily']}, monthly=${monthly_cost:.4f}/{tier_limits['monthly']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Cost limit check failed for {user_id}: {e}")
            # Fallback to allow request
            return {
                "daily_cost": 0.0,
                "monthly_cost": 0.0,
                "daily_limit": 1000.0,
                "monthly_limit": 10000.0,
                "within_limits": True,
                "redis_available": False,
                "error": str(e)
            }
    
    async def track_api_cost(self, user_id: str, endpoint_type: str):
        """
        Track API costs for rate limiting
        
        Args:
            user_id: User identifier
            endpoint_type: Type of endpoint called
        """
        cost = self.endpoint_costs.get(endpoint_type, 0.005)
        
        redis_client = await self._get_redis_pool()
        if not redis_client:
            logger.warning(f"Redis unavailable - cannot track cost: user={user_id}, endpoint={endpoint_type}, cost=${cost:.4f}")
            return
        
        try:
            # Track costs with expiration
            daily_key = f"cost:daily:{user_id}"
            monthly_key = f"cost:monthly:{user_id}"
            
            # Increment costs atomically
            async with redis_client.pipeline() as pipe:
                await pipe.incrbyfloat(daily_key, cost)
                await pipe.expire(daily_key, 86400)  # 24 hours
                await pipe.incrbyfloat(monthly_key, cost)
                await pipe.expire(monthly_key, 2592000)  # 30 days
                await pipe.execute()
            
            # Log cost tracking (info level for production monitoring)
            logger.info(f"Cost tracked: user={user_id}, endpoint={endpoint_type}, cost=${cost:.4f}")
            
        except Exception as e:
            logger.error(f"Failed to track cost for {user_id}: {e}")
    
    async def apply_rate_limit(self, request: Request, endpoint_type: str) -> None:
        """
        Apply rate limiting to a request
        
        Args:
            request: FastAPI request object
            endpoint_type: Type of endpoint for rate limiting
            
        Raises:
            HTTPException: If rate limit or cost limit exceeded
        """
        # Extract user_id for limits
        identifier = self._get_user_identifier(request)
        user_id = identifier.replace("user:", "") if identifier.startswith("user:") else identifier
        
        # Get rate limit for this endpoint and user
        limit = self.get_limit_for_endpoint(endpoint_type, user_id)
        
        try:
            # Temporary fix: Skip SlowAPI integration and use basic in-memory rate limiting
            # Since we're not using Redis in development, just do basic checking
            
            # Use in-memory rate limiting for development
            await self._check_in_memory_rate_limit(user_id, endpoint_type, limit)
                
        except RateLimitExceeded as e:
            if EXCEPTIONS_AVAILABLE:
                raise RateLimitException(
                    message=f"Rate limit exceeded for {endpoint_type}",
                    details={
                        "limit": limit,
                        "endpoint_type": endpoint_type,
                        "suggestion": "Please wait before making another request",
                        "retry_after": 3600  # 1 hour
                    }
                )
            else:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit": limit,
                        "endpoint_type": endpoint_type,
                        "suggestion": "Please wait before making another request",
                        "retry_after": 3600
                    }
                )
        
        # Check cost limits
        cost_check = await self.check_cost_limits(user_id)
        if not cost_check["within_limits"]:
            if EXCEPTIONS_AVAILABLE:
                raise CostLimitException(
                    message="Daily cost limit exceeded",
                    details={
                        "daily_cost": cost_check["daily_cost"],
                        "daily_limit": cost_check["daily_limit"],
                        "monthly_cost": cost_check["monthly_cost"],
                        "monthly_limit": cost_check["monthly_limit"],
                        "suggestion": "Upgrade to premium or wait until tomorrow"
                    }
                )
            else:
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail={
                        "error": "Daily cost limit exceeded",
                        "daily_cost": cost_check["daily_cost"],
                        "daily_limit": cost_check["daily_limit"],
                        "suggestion": "Upgrade to premium or wait until tomorrow"
                    }
                )
    
    async def _check_in_memory_rate_limit(self, user_id: str, endpoint_type: str, limit: str) -> None:
        """Check rate limit using in-memory storage (for development without Redis)"""
        try:
            # Parse limit (e.g., "5/hour" -> 5 requests per hour)
            limit_parts = limit.split("/")
            if len(limit_parts) != 2:
                logger.warning(f"Invalid limit format: {limit}")
                return
            
            count_limit = int(limit_parts[0])
            time_window = limit_parts[1]
            
            # Convert time window to seconds
            window_seconds = {
                "minute": 60,
                "hour": 3600,
                "day": 86400
            }.get(time_window, 3600)  # Default to 1 hour
            
            # Key for this user and endpoint
            rate_key = f"{user_id}:{endpoint_type}"
            current_time = time.time()
            
            # Clean up expired entries first
            expired_keys = []
            for key, data in self._in_memory_limits.items():
                if current_time > data.get("reset_time", 0):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._in_memory_limits[key]
            
            # Check current limit
            if rate_key not in self._in_memory_limits:
                # First request in this window
                self._in_memory_limits[rate_key] = {
                    "count": 1,
                    "reset_time": current_time + window_seconds
                }
                logger.debug(f"Rate limit OK for {user_id}:{endpoint_type} (1/{count_limit})")
                return
            
            # Increment existing counter
            self._in_memory_limits[rate_key]["count"] += 1
            current_count = self._in_memory_limits[rate_key]["count"]
            
            # Check if limit exceeded
            if current_count > count_limit:
                logger.warning(f"Rate limit exceeded for {user_id}:{endpoint_type} ({current_count}/{count_limit})")
                raise RateLimitExceeded(detail=f"Rate limit exceeded: {current_count}/{count_limit}")
            
            logger.debug(f"Rate limit OK for {user_id}:{endpoint_type} ({current_count}/{count_limit})")
            
        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.error(f"In-memory rate limit check error: {e}")
            # Graceful degradation - don't block request if check fails
            return
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get current usage statistics for a user"""
        redis_client = await self._get_redis_pool()
        if not redis_client:
            return {"error": "Redis unavailable"}
        
        try:
            # Get cost information
            cost_info = await self.check_cost_limits(user_id)
            
            # Get rate limit information
            tier = self._get_user_tier(user_id)
            limits = self.tier_limits[tier]
            
            return {
                "user_id": user_id,
                "tier": tier.value,
                "cost_info": cost_info,
                "rate_limits": limits,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats for {user_id}: {e}")
            return {"error": str(e)}
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide rate limiting statistics"""
        redis_client = await self._get_redis_pool()
        if not redis_client:
            return {"error": "Redis unavailable"}
        
        try:
            # Get all user cost keys
            cost_keys = await redis_client.keys("cost:daily:*")
            
            total_cost_today = 0.0
            user_count = 0
            top_users = []
            
            for key in cost_keys:
                user_id = key.replace("cost:daily:", "")
                daily_cost = float(await redis_client.get(key) or 0)
                total_cost_today += daily_cost
                user_count += 1
                
                if daily_cost > 0:
                    top_users.append({
                        "user_id": user_id,
                        "daily_cost": daily_cost,
                        "tier": self._get_user_tier(user_id).value
                    })
            
            # Sort top users by cost
            top_users.sort(key=lambda x: x["daily_cost"], reverse=True)
            
            return {
                "total_users_with_usage": user_count,
                "total_cost_today": round(total_cost_today, 4),
                "top_users": top_users[:10],  # Top 10 users
                "redis_available": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {"error": str(e)}


# Global rate limiter instance
rate_limiter = HolisticRateLimiter()

# Make RateLimitTier accessible from rate_limiter
rate_limiter.RateLimitTier = RateLimitTier


def get_rate_limiter() -> HolisticRateLimiter:
    """Get the global rate limiter instance"""
    return rate_limiter