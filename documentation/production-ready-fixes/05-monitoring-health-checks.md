# P1: Monitoring & Health Checks

## Why This Issue Exists

### Current Problem
- Basic health check only tests API availability
- No visibility into system performance and errors
- No alerting when issues occur
- Cannot diagnose problems without manual investigation
- No metrics for business decisions

### Evidence from Current Code
```python
# Current basic health check in openai_main.py
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}  # Too simple for production!
```

### Impact on Production Operations
- **Blind Operations**: Can't see what's happening in production
- **Slow Response**: Issues discovered by users, not monitoring
- **Poor Debugging**: No historical data when problems occur
- **Business Risk**: No insight into user behavior or system performance

### Real-World Scenarios
```
Scenario 1: Silent Failures
OpenAI API starts failing → Users see errors → No alerts → Manual discovery

Scenario 2: Performance Degradation  
Database becomes slow → Response times increase → Users abandon → No visibility

Scenario 3: Cost Overrun
Heavy user activity → API costs spike → Monthly bill shock → No prevention
```

## How to Fix

### Implementation Strategy

#### 1. Enhanced Health Check System
```python
# shared_libs/monitoring/health_checker.py
import asyncio
import psutil
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

@dataclass
class HealthCheckResult:
    service: str
    status: HealthStatus
    response_time_ms: float
    message: str
    details: Dict[str, Any] = None

class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self):
        self.check_timeout = 10  # 10 second timeout for health checks
        self.performance_thresholds = {
            "response_time_ms": 5000,     # 5 seconds max
            "memory_usage_percent": 80,   # 80% memory max
            "cpu_usage_percent": 90,      # 90% CPU max
            "error_rate_percent": 5,      # 5% error rate max
            "database_connections": 8     # Max pool size
        }
    
    async def check_database_health(self) -> HealthCheckResult:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            from shared_libs.database.connection_pool import db_pool
            
            # Test query
            result = await asyncio.wait_for(
                db_pool.execute_one("SELECT 1 as health_check, NOW() as timestamp"),
                timeout=self.check_timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            pool_status = await db_pool.get_pool_status()
            
            # Determine health based on response time and pool status
            if response_time > 3000:  # 3 seconds is too slow
                status = HealthStatus.DEGRADED
                message = f"Database slow: {response_time:.0f}ms"
            elif pool_status.get("idle_connections", 0) < 1:
                status = HealthStatus.DEGRADED
                message = "Database pool exhausted"
            else:
                status = HealthStatus.HEALTHY
                message = "Database operational"
            
            return HealthCheckResult(
                service="database",
                status=status,
                response_time_ms=response_time,
                message=message,
                details={
                    "pool_status": pool_status,
                    "query_result": bool(result),
                    "timestamp": result.get("timestamp") if result else None
                }
            )
            
        except asyncio.TimeoutError:
            return HealthCheckResult(
                service="database",
                status=HealthStatus.CRITICAL,
                response_time_ms=self.check_timeout * 1000,
                message=f"Database timeout after {self.check_timeout}s"
            )
        except Exception as e:
            return HealthCheckResult(
                service="database",
                status=HealthStatus.CRITICAL,
                response_time_ms=-1,
                message=f"Database error: {str(e)}"
            )
    
    async def check_openai_health(self) -> HealthCheckResult:
        """Check OpenAI API connectivity"""
        start_time = time.time()
        
        try:
            import openai
            client = openai.AsyncOpenAI()
            
            # Simple test call
            await asyncio.wait_for(
                client.models.list(),
                timeout=self.check_timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service="openai",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                message="OpenAI API accessible",
                details={"api_key_valid": True}
            )
            
        except asyncio.TimeoutError:
            return HealthCheckResult(
                service="openai",
                status=HealthStatus.DEGRADED,
                response_time_ms=self.check_timeout * 1000,
                message="OpenAI API timeout"
            )
        except Exception as e:
            status = HealthStatus.CRITICAL if "authentication" in str(e).lower() else HealthStatus.DEGRADED
            return HealthCheckResult(
                service="openai",
                status=status,
                response_time_ms=-1,
                message=f"OpenAI error: {str(e)}"
            )
    
    async def check_system_health(self) -> HealthCheckResult:
        """Check system resources (CPU, memory, disk)"""
        try:
            process = psutil.Process()
            
            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = process.memory_percent()
            
            # CPU usage (average over 1 second)
            cpu_percent = process.cpu_percent(interval=1)
            
            # System-wide stats
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=1)
            
            # Determine health status
            if memory_percent > self.performance_thresholds["memory_usage_percent"]:
                status = HealthStatus.DEGRADED
                message = f"High memory usage: {memory_percent:.1f}%"
            elif cpu_percent > self.performance_thresholds["cpu_usage_percent"]:
                status = HealthStatus.DEGRADED
                message = f"High CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources normal"
            
            return HealthCheckResult(
                service="system",
                status=status,
                response_time_ms=1000,  # 1 second check
                message=message,
                details={
                    "process_memory_mb": round(memory_mb, 2),
                    "process_memory_percent": round(memory_percent, 2),
                    "process_cpu_percent": round(cpu_percent, 2),
                    "system_memory_percent": round(system_memory.percent, 2),
                    "system_cpu_percent": round(system_cpu, 2),
                    "available_memory_mb": round(system_memory.available / 1024 / 1024, 2)
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="system",
                status=HealthStatus.DEGRADED,
                response_time_ms=-1,
                message=f"System check error: {str(e)}"
            )
    
    async def check_redis_health(self) -> HealthCheckResult:
        """Check Redis connectivity for rate limiting and caching"""
        start_time = time.time()
        
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            client = redis.Redis.from_url(redis_url, decode_responses=True)
            
            # Test Redis with ping
            result = client.ping()
            response_time = (time.time() - start_time) * 1000
            
            # Get Redis info
            info = client.info()
            
            return HealthCheckResult(
                service="redis",
                status=HealthStatus.HEALTHY if result else HealthStatus.DEGRADED,
                response_time_ms=response_time,
                message="Redis operational" if result else "Redis ping failed",
                details={
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses")
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="redis",
                status=HealthStatus.DEGRADED,
                response_time_ms=-1,
                message=f"Redis error: {str(e)}"
            )
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks in parallel"""
        checks = await asyncio.gather(
            self.check_database_health(),
            self.check_openai_health(),
            self.check_system_health(),
            self.check_redis_health(),
            return_exceptions=True
        )
        
        results = {}
        overall_status = HealthStatus.HEALTHY
        critical_issues = []
        warnings = []
        
        for check in checks:
            if isinstance(check, Exception):
                critical_issues.append(f"Health check failed: {str(check)}")
                overall_status = HealthStatus.CRITICAL
                continue
            
            results[check.service] = {
                "status": check.status.value,
                "response_time_ms": check.response_time_ms,
                "message": check.message,
                "details": check.details or {}
            }
            
            # Determine overall status
            if check.status == HealthStatus.CRITICAL:
                overall_status = HealthStatus.CRITICAL
                critical_issues.append(f"{check.service}: {check.message}")
            elif check.status == HealthStatus.DEGRADED and overall_status != HealthStatus.CRITICAL:
                overall_status = HealthStatus.DEGRADED
                warnings.append(f"{check.service}: {check.message}")
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "services": results,
            "summary": {
                "critical_issues": critical_issues,
                "warnings": warnings,
                "healthy_services": [
                    service for service, data in results.items() 
                    if data["status"] == "healthy"
                ]
            }
        }

# Global health checker instance
health_checker = HealthChecker()
```

#### 2. Prometheus Metrics System
```python
# shared_libs/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
import functools
from typing import Dict, Any

# Define metrics
REQUEST_COUNT = Counter(
    'holisticos_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'holisticos_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'holisticos_active_connections',
    'Active database connections'
)

OPENAI_API_CALLS = Counter(
    'holisticos_openai_calls_total',
    'OpenAI API calls',
    ['model', 'status']
)

OPENAI_API_COST = Counter(
    'holisticos_openai_cost_total',
    'OpenAI API costs in USD'
)

MEMORY_USAGE = Gauge(
    'holisticos_memory_usage_bytes',
    'Memory usage in bytes'
)

ERROR_COUNT = Counter(
    'holisticos_errors_total',
    'Total errors',
    ['service', 'error_type']
)

class MetricsCollector:
    """Collect and expose metrics for monitoring"""
    
    @staticmethod
    def track_request(method: str, endpoint: str, status_code: int, duration: float):
        """Track HTTP request metrics"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
    
    @staticmethod
    def track_openai_call(model: str, status: str, cost: float = 0):
        """Track OpenAI API calls and costs"""
        OPENAI_API_CALLS.labels(model=model, status=status).inc()
        if cost > 0:
            OPENAI_API_COST.inc(cost)
    
    @staticmethod
    def update_system_metrics():
        """Update system-level metrics"""
        import psutil
        process = psutil.Process()
        
        # Update memory usage
        MEMORY_USAGE.set(process.memory_info().rss)
        
        # Update database connections (if pool available)
        try:
            from shared_libs.database.connection_pool import db_pool
            pool_status = db_pool.get_pool_status()
            if isinstance(pool_status, dict):
                ACTIVE_CONNECTIONS.set(pool_status.get("size", 0))
        except:
            pass
    
    @staticmethod
    def track_error(service: str, error_type: str):
        """Track errors by service and type"""
        ERROR_COUNT.labels(service=service, error_type=error_type).inc()

def track_endpoint_metrics(endpoint_name: str):
    """Decorator to automatically track endpoint metrics"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                MetricsCollector.track_error("api", type(e).__name__)
                raise
            finally:
                duration = time.time() - start_time
                MetricsCollector.track_request("POST", endpoint_name, status_code, duration)
        
        return wrapper
    return decorator

# Global metrics collector
metrics = MetricsCollector()
```

#### 3. Enhanced API Endpoints with Monitoring
```python
# services/api_gateway/openai_main.py - ENHANCED HEALTH & METRICS

from shared_libs.monitoring.health_checker import health_checker
from shared_libs.monitoring.metrics import metrics, track_endpoint_metrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/api/health")
async def health_check():
    """Comprehensive health check endpoint"""
    return await health_checker.run_comprehensive_health_check()

@app.get("/api/health/simple")
async def simple_health_check():
    """Simple health check for load balancers"""
    try:
        # Quick database test
        from shared_libs.database.connection_pool import db_pool
        await db_pool.execute_one("SELECT 1")
        return {"status": "healthy"}
    except:
        return {"status": "unhealthy"}, 503

@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    # Update system metrics before returning
    metrics.update_system_metrics()
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/api/monitoring/stats")
async def get_monitoring_stats():
    """Get monitoring statistics"""
    from shared_libs.rate_limiting.rate_limiter import rate_limiter
    
    # Collect various stats
    health_status = await health_checker.run_comprehensive_health_check()
    
    return {
        "health": health_status,
        "metrics": {
            "uptime_seconds": time.time() - app.state.start_time,
            "total_requests": "See /metrics endpoint",
            "current_connections": "See /metrics endpoint"
        },
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "production")
    }

# Add metrics tracking to existing endpoints
@app.post("/api/user/{user_id}/routine/generate")
@track_endpoint_metrics("routine_generation")
async def generate_fresh_routine_plan(user_id: str, request: PlanGenerationRequest):
    """Routine generation with metrics tracking"""
    try:
        # Original logic here...
        result = await original_routine_generation_logic()
        
        # Track successful OpenAI call
        metrics.track_openai_call("gpt-4o", "success", 0.02)
        
        return result
    except Exception as e:
        # Track failed OpenAI call
        metrics.track_openai_call("gpt-4o", "error", 0)
        metrics.track_error("routine_generation", type(e).__name__)
        raise

# Add startup tracking
@app.on_event("startup")
async def startup_event():
    """Track application startup"""
    app.state.start_time = time.time()
    logger.info("🚀 HolisticOS started with monitoring enabled")
```

#### 4. Alerting System with Slack Integration
```python
# shared_libs/monitoring/alerting.py
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from enum import Enum
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.alert_cooldown = {}  # Prevent spam alerts
        self.cooldown_minutes = 15  # 15 minutes between same alerts
    
    def should_send_alert(self, alert_key: str) -> bool:
        """Check if alert should be sent (cooldown logic)"""
        now = datetime.now()
        last_sent = self.alert_cooldown.get(alert_key)
        
        if not last_sent:
            self.alert_cooldown[alert_key] = now
            return True
        
        minutes_since = (now - last_sent).total_seconds() / 60
        if minutes_since >= self.cooldown_minutes:
            self.alert_cooldown[alert_key] = now
            return True
        
        return False
    
    async def send_alert(self, severity: AlertSeverity, title: str, details: Dict[str, Any]):
        """Send alert to configured channels"""
        alert_key = f"{severity.value}:{title}"
        
        if not self.should_send_alert(alert_key):
            logger.debug(f"Alert cooldown active for: {alert_key}")
            return
        
        if self.webhook_url:
            await self._send_slack_alert(severity, title, details)
        else:
            logger.warning(f"No webhook configured. Alert: {title}")
    
    async def _send_slack_alert(self, severity: AlertSeverity, title: str, details: Dict[str, Any]):
        """Send alert to Slack"""
        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9900", 
            AlertSeverity.ERROR: "#ff0000",
            AlertSeverity.CRITICAL: "#990000"
        }
        
        payload = {
            "text": f"🚨 HolisticOS Alert",
            "attachments": [{
                "color": color_map[severity],
                "title": f"[{severity.value.upper()}] {title}",
                "fields": [
                    {"title": k, "value": str(v), "short": True}
                    for k, v in details.items()
                ],
                "footer": "HolisticOS Monitoring",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send Slack alert: {response.status}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")

# Global alert manager
alert_manager = AlertManager()

# Health check monitoring with alerts
async def monitor_health_continuously():
    """Background task to monitor health and send alerts"""
    while True:
        try:
            health_status = await health_checker.run_comprehensive_health_check()
            
            # Check for critical issues
            if health_status["overall_status"] == "critical":
                await alert_manager.send_alert(
                    AlertSeverity.CRITICAL,
                    "System Critical Issues Detected",
                    {
                        "Critical Issues": ", ".join(health_status["summary"]["critical_issues"]),
                        "Environment": os.getenv("ENVIRONMENT", "production"),
                        "Timestamp": health_status["timestamp"]
                    }
                )
            
            # Check for degraded performance
            elif health_status["overall_status"] == "degraded":
                await alert_manager.send_alert(
                    AlertSeverity.WARNING,
                    "System Performance Degraded",
                    {
                        "Warnings": ", ".join(health_status["summary"]["warnings"]),
                        "Healthy Services": ", ".join(health_status["summary"]["healthy_services"])
                    }
                )
            
            # Check specific service issues
            for service, data in health_status["services"].items():
                if data["status"] == "critical":
                    await alert_manager.send_alert(
                        AlertSeverity.ERROR,
                        f"{service.title()} Service Down",
                        {
                            "Service": service,
                            "Error": data["message"],
                            "Response Time": f"{data['response_time_ms']}ms"
                        }
                    )
        
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
        
        # Check every 2 minutes
        await asyncio.sleep(120)
```

## What is the Expected Outcome

### Operational Visibility
```python
monitoring_capabilities = {
    "real_time_health": "All services status visible",
    "performance_metrics": "Response times, error rates, resource usage",
    "business_metrics": "API costs, user activity, feature usage",
    "proactive_alerts": "Issues detected before users complain",
    "historical_data": "Trends and patterns for optimization"
}
```

### Alert Response Times
- **Critical Issues**: Immediate Slack notification
- **Performance Degradation**: Warning within 2 minutes
- **Service Recovery**: Automatic "all clear" notifications
- **Cost Anomalies**: Daily/weekly summary alerts

### Monitoring Dashboard URLs
```
Health Check: https://your-app.onrender.com/api/health
Simple Health: https://your-app.onrender.com/api/health/simple  
Metrics: https://your-app.onrender.com/metrics
Stats: https://your-app.onrender.com/api/monitoring/stats
```

### Before vs After

**Before (No Monitoring)**:
```
Issue Occurs → Users Notice → Manual Investigation → Slow Resolution
```

**After (With Monitoring)**:
```
Issue Occurs → Automatic Detection → Instant Alert → Fast Resolution
```

### Success Criteria
- [ ] Comprehensive health checks for all services
- [ ] Prometheus metrics collection
- [ ] Slack alerts for critical issues
- [ ] Performance monitoring and thresholds
- [ ] Historical data for trend analysis
- [ ] Alert cooldown to prevent spam

### Render Integration
```yaml
# Add to render.yaml
services:
  - type: web
    healthCheckPath: /api/health/simple
    envVars:
      - key: SLACK_WEBHOOK_URL
        sync: false
```

### Dependencies
- `pip install prometheus_client psutil`
- Slack webhook URL configuration
- Environment variables for thresholds

---

**Estimated Effort**: 2 days
**Risk Level**: Low (pure monitoring addition)
**MVP Impact**: Critical - Cannot operate production without visibility