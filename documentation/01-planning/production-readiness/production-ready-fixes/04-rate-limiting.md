# P1: Rate Limiting

## Why This Issue Exists

### Current Problem
- No protection against API abuse or excessive usage
- Users can make unlimited requests, causing cost overruns
- No mechanism to prevent DoS attacks
- OpenAI API costs can spiral out of control
- System can be overwhelmed by single aggressive user

### Evidence of Risk
```python
# Current: Any user can call this unlimited times
@app.post("/api/user/{user_id}/routine/generate")
async def generate_routine():
    # $0.03 OpenAI API call - no limits!
```

### Impact on MVP Business
- **Cost Risk**: OpenAI GPT-4 costs $0.03 per 1K tokens
- **Service Degradation**: Heavy users affect everyone
- **Resource Exhaustion**: 0.5 CPU can't handle unlimited load
- **Security Risk**: Potential for abuse/attacks

### Real-World Cost Scenario
```
Aggressive User: 1000 requests/hour × $0.03 = $30/hour = $720/day
Normal User: 10 requests/hour × $0.03 = $0.30/hour = $7.20/day

Without limits: Business unsustainable
With limits: Predictable costs
```

## How to Fix

### Implementation Strategy

#### 1. Install and Configure Rate Limiting
```python
# requirements.txt additions
slowapi==0.1.9
redis==4.5.4

# Rate limiting dependencies
pip install slowapi redis
```

#### 2. Create Rate Limiting Service
```python
# shared_libs/rate_limiting/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
import redis
import os
import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

class RateLimitTier(Enum):
    """Different rate limit tiers for different users"""
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"

class HolisticRateLimiter:
    """Custom rate limiter for HolisticOS"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        
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
                "behavior_analysis": "1000/hour", # Unlimited for admin
                "routine_generation": "1000/hour",
                "nutrition_generation": "1000/hour",
                "insights_generation": "1000/hour",
                "general_api": "1000/hour"
            }
        }
        
        # Initialize slowapi limiter
        self.limiter = Limiter(
            key_func=self._get_user_identifier,
            storage_uri=self.redis_url
        )
    
    def _get_user_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Try to get user_id from path parameters
        user_id = request.path_params.get("user_id")
        if user_id:
            return f"user:{user_id}"
        
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
        """Check if user has exceeded cost limits"""
        # Simple cost tracking (extend with database storage)
        redis_client = redis.Redis.from_url(self.redis_url)
        
        daily_cost_key = f"cost:daily:{user_id}"
        monthly_cost_key = f"cost:monthly:{user_id}"
        
        daily_cost = float(redis_client.get(daily_cost_key) or 0)
        monthly_cost = float(redis_client.get(monthly_cost_key) or 0)
        
        # Cost limits per tier
        tier = self._get_user_tier(user_id)
        limits = {
            RateLimitTier.FREE: {"daily": 1.0, "monthly": 10.0},      # $1/day, $10/month
            RateLimitTier.PREMIUM: {"daily": 10.0, "monthly": 100.0}, # $10/day, $100/month
            RateLimitTier.ADMIN: {"daily": 1000.0, "monthly": 10000.0} # No real limits
        }
        
        tier_limits = limits[tier]
        
        return {
            "daily_cost": daily_cost,
            "monthly_cost": monthly_cost,
            "daily_limit": tier_limits["daily"],
            "monthly_limit": tier_limits["monthly"],
            "within_limits": daily_cost < tier_limits["daily"] and monthly_cost < tier_limits["monthly"]
        }
    
    async def track_api_cost(self, user_id: str, cost: float, endpoint: str):
        """Track API costs for rate limiting"""
        redis_client = redis.Redis.from_url(self.redis_url)
        
        # Track costs with expiration
        daily_key = f"cost:daily:{user_id}"
        monthly_key = f"cost:monthly:{user_id}"
        
        # Increment costs
        redis_client.incrbyfloat(daily_key, cost)
        redis_client.incrbyfloat(monthly_key, cost)
        
        # Set expiration (24 hours for daily, 30 days for monthly)
        redis_client.expire(daily_key, 86400)  # 24 hours
        redis_client.expire(monthly_key, 2592000)  # 30 days
        
        # Log cost tracking
        logger.info(f"Cost tracked: user={user_id}, endpoint={endpoint}, cost=${cost:.4f}")

# Global rate limiter instance
rate_limiter = HolisticRateLimiter()
```

#### 3. Apply Rate Limits to API Endpoints
```python
# services/api_gateway/openai_main.py - ADD RATE LIMITING

from shared_libs.rate_limiting.rate_limiter import rate_limiter
from slowapi.errors import RateLimitExceeded
from fastapi import HTTPException

# Add rate limiter to app
app.state.limiter = rate_limiter.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/user/{user_id}/routine/generate", response_model=RoutinePlanResponse)
async def generate_fresh_routine_plan(
    user_id: str, 
    request: PlanGenerationRequest,
    http_request: Request  # Add Request parameter for rate limiting
):
    """Generate routine with rate limiting"""
    
    # Check rate limits first
    limit = rate_limiter.get_limit_for_endpoint("routine_generation", user_id)
    
    try:
        # Apply rate limit
        await rate_limiter.limiter.limit(limit)(http_request)
    except RateLimitExceeded:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": limit,
                "suggestion": "Please wait before making another request",
                "retry_after": 3600  # 1 hour
            }
        )
    
    # Check cost limits
    cost_check = await rate_limiter.check_cost_limits(user_id)
    if not cost_check["within_limits"]:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                "error": "Daily cost limit exceeded",
                "daily_cost": cost_check["daily_cost"],
                "daily_limit": cost_check["daily_limit"],
                "suggestion": "Upgrade to premium or wait until tomorrow"
            }
        )
    
    try:
        # Original routine generation logic
        behavior_analysis = await get_or_create_shared_behavior_analysis(
            user_id, request.archetype
        )
        
        routine_plan = await run_memory_enhanced_routine_generation(
            user_id=user_id,
            archetype=request.archetype,
            behavior_analysis=behavior_analysis
        )
        
        # Track API cost (estimate $0.02 per routine generation)
        await rate_limiter.track_api_cost(user_id, 0.02, "routine_generation")
        
        return RoutinePlanResponse(
            status="success",
            user_id=user_id,
            routine_plan=routine_plan,
            generation_metadata={
                "rate_limit_remaining": get_remaining_requests(user_id, "routine_generation"),
                "cost_used_today": cost_check["daily_cost"]
            }
        )
        
    except Exception as e:
        logger.error(f"Routine generation failed for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/{user_id}/nutrition/generate", response_model=NutritionPlanResponse)
async def generate_fresh_nutrition_plan(
    user_id: str, 
    request: PlanGenerationRequest,
    http_request: Request
):
    """Generate nutrition with rate limiting"""
    
    # Rate limiting logic (similar to routine)
    limit = rate_limiter.get_limit_for_endpoint("nutrition_generation", user_id)
    
    try:
        await rate_limiter.limiter.limit(limit)(http_request)
    except RateLimitExceeded:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": limit,
                "suggestion": "Please wait before making another request"
            }
        )
    
    # Cost check and original logic...
    # [Similar implementation to routine endpoint]

# High-cost endpoint - stricter limits
@app.post("/api/analyze")
async def complete_health_analysis(
    request: CompleteAnalysisRequest,
    http_request: Request
):
    """Complete analysis with strict rate limiting"""
    
    # Stricter limit for expensive operations
    limit = rate_limiter.get_limit_for_endpoint("behavior_analysis", request.user_id)
    
    try:
        await rate_limiter.limiter.limit(limit)(http_request)
    except RateLimitExceeded:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Analysis rate limit exceeded",
                "limit": limit,
                "cost_per_request": "$0.03",
                "suggestion": "This is an expensive operation. Please wait 1 hour between requests."
            }
        )
    
    # High cost tracking (behavior analysis is expensive)
    cost_check = await rate_limiter.check_cost_limits(request.user_id)
    if not cost_check["within_limits"]:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Daily cost limit exceeded",
                "daily_cost": cost_check["daily_cost"],
                "daily_limit": cost_check["daily_limit"]
            }
        )
    
    # Original analysis logic...
    result = await run_complete_health_analysis(request)
    
    # Track high cost for behavior analysis
    await rate_limiter.track_api_cost(request.user_id, 0.03, "behavior_analysis")
    
    return result
```

#### 4. Rate Limit Headers and Monitoring
```python
# shared_libs/rate_limiting/middleware.py
from fastapi import Request, Response
import time

async def add_rate_limit_headers(request: Request, response: Response):
    """Add rate limit headers to responses"""
    user_id = request.path_params.get("user_id")
    if user_id:
        # Get current usage from Redis
        remaining = get_remaining_requests(user_id, "general_api")
        reset_time = get_reset_time(user_id)
        
        response.headers["X-RateLimit-Limit"] = "50"
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        response.headers["X-Cost-Used-Today"] = str(get_daily_cost(user_id))

# Add middleware to app
app.middleware("http")(add_rate_limit_headers)
```

#### 5. Rate Limit Monitoring Dashboard
```python
# Add to health check endpoint
@app.get("/api/admin/rate-limits")
async def get_rate_limit_stats():
    """Admin endpoint to monitor rate limiting"""
    redis_client = redis.Redis.from_url(rate_limiter.redis_url)
    
    # Get top users by request count
    users_pattern = "slowapi:user:*"
    user_keys = redis_client.keys(users_pattern)
    
    user_stats = []
    for key in user_keys[:10]:  # Top 10 users
        user_id = key.decode().split(":")[-1]
        request_count = redis_client.get(key) or 0
        daily_cost = redis_client.get(f"cost:daily:{user_id}") or 0
        
        user_stats.append({
            "user_id": user_id,
            "requests_today": int(request_count),
            "cost_today": float(daily_cost)
        })
    
    return {
        "total_users": len(user_keys),
        "top_users": sorted(user_stats, key=lambda x: x["requests_today"], reverse=True),
        "total_cost_today": sum(stats["cost_today"] for stats in user_stats)
    }
```

### Configuration for Different Environments

```python
# config/rate_limits.py
ENVIRONMENT_CONFIGS = {
    "development": {
        "enabled": False,  # Disable in development
        "limits": {"general_api": "1000/hour"}
    },
    "staging": {
        "enabled": True,
        "limits": {"general_api": "100/hour"}  # More relaxed for testing
    },
    "production": {
        "enabled": True,
        "limits": {
            "behavior_analysis": "5/hour",
            "routine_generation": "10/hour",
            "nutrition_generation": "10/hour",
            "insights_generation": "20/hour",
            "general_api": "50/hour"
        }
    }
}
```

## What is the Expected Outcome

### Cost Control
- **Predictable Costs**: Max $10/day per user (free tier)
- **No Surprises**: Cost alerts before limits exceeded
- **Business Sustainability**: Revenue model protection

### System Protection
```python
protection_metrics = {
    "max_requests_per_user_per_hour": 50,
    "max_cost_per_user_per_day": "$1.00",
    "max_concurrent_expensive_operations": 5,
    "system_overload_prevention": "99%+"
}
```

### User Experience Improvements
- **Clear Error Messages**: Users understand why request was rejected
- **Rate Limit Headers**: Frontend can show remaining requests
- **Graceful Degradation**: System stays responsive for all users

### Before vs After

**Before (No Rate Limiting)**:
```
Aggressive User: 1000 requests → $30/hour → System Overwhelmed
Normal Users: Slow responses due to resource contention
Business: Unsustainable costs
```

**After (With Rate Limiting)**:
```
Aggressive User: 50 requests → Blocked after limit → Clear error message
Normal Users: Fast, reliable responses
Business: Predictable costs, sustainable operation
```

### Monitoring Dashboards
```python
rate_limit_dashboard = {
    "metrics": [
        "requests_per_hour_by_user",
        "rate_limit_violations",
        "cost_per_user_per_day",
        "endpoint_usage_patterns",
        "peak_usage_times"
    ],
    "alerts": [
        "daily_cost_exceeded",
        "unusual_traffic_patterns",
        "rate_limit_threshold_breached"
    ]
}
```

### Success Criteria
- [ ] No user exceeds cost limits
- [ ] Rate limit violations result in helpful error messages
- [ ] System remains responsive during high load
- [ ] Admin dashboard shows usage patterns
- [ ] Cost tracking is accurate
- [ ] Easy to adjust limits via configuration

### Implementation Phases

**Phase 1: Basic Rate Limiting (Day 1)**
- Install slowapi and Redis
- Add rate limits to high-cost endpoints
- Basic error responses

**Phase 2: Cost Tracking (Day 2)**
- Implement cost tracking in Redis
- Add cost limit enforcement
- Admin monitoring dashboard

**Phase 3: Enhanced Features (Future)**
- User tier system (free/premium)
- Dynamic rate limits based on system load
- Detailed analytics and reporting

### Dependencies
- Redis instance (available on Render)
- slowapi library
- Environment variables for configuration

### Risk Mitigation
- Start with generous limits to avoid blocking legitimate users
- Monitor usage patterns before tightening limits
- Provide clear upgrade paths for users who need higher limits
- Easy configuration changes without deployment

---

**Estimated Effort**: 1 day
**Risk Level**: Low (can be disabled if issues arise)
**MVP Impact**: High - Essential for cost control and system protection