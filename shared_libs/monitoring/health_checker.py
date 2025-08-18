"""
Comprehensive Health Check System for HolisticOS
Integrates with Agent 1's database infrastructure and monitors all critical services
"""

import asyncio
import psutil
import time
import logging
import os
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
    """Comprehensive health checking system integrated with Agent 1's infrastructure"""
    
    def __init__(self):
        self.check_timeout = 10  # 10 second timeout for health checks
        self.performance_thresholds = {
            "response_time_ms": 5000,     # 5 seconds max
            "memory_usage_percent": 80,   # 80% memory max
            "cpu_usage_percent": 90,      # 90% CPU max
            "error_rate_percent": 5,      # 5% error rate max
            "database_connections": 8     # Max pool size from Agent 1
        }
        # Check if Redis monitoring should be enabled
        self.redis_enabled = self._is_redis_enabled()
    
    def _is_redis_enabled(self) -> bool:
        """Check if Redis is intended to be used (not just localhost default)"""
        redis_url = os.getenv("REDIS_URL")
        # If Redis URL is not set, it's disabled
        if not redis_url:
            return False
        # If it's localhost in development, check if Redis is actually needed
        environment = os.getenv("ENVIRONMENT", "development")
        if redis_url == "redis://localhost:6379" and environment == "development":
            # Check if Redis is running by attempting a quick connection
            return self._test_redis_connection(redis_url)
        return True
    
    def _test_redis_connection(self, redis_url: str) -> bool:
        """Quick test to see if Redis is available"""
        try:
            import redis
            client = redis.Redis.from_url(redis_url, socket_connect_timeout=2)
            client.ping()
            return True
        except:
            return False
    
    async def check_database_health(self) -> HealthCheckResult:
        """Check database connectivity and performance using Agent 1's pool"""
        start_time = time.time()
        
        try:
            # Import Agent 1's database pool
            from shared_libs.database.connection_pool import db_pool
            
            # Test query with Agent 1's pool
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
            elif pool_status.get("status") != "healthy":
                status = HealthStatus.DEGRADED
                message = f"Database pool status: {pool_status.get('status', 'unknown')}"
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
                    "timestamp": result.get("timestamp").isoformat() if result and result.get("timestamp") else None,
                    "current_size": pool_status.get("current_size", 0),
                    "max_size": pool_status.get("max_size", 0),
                    "idle_connections": pool_status.get("idle_connections", 0)
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
            
            # Use the API key from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return HealthCheckResult(
                    service="openai",
                    status=HealthStatus.CRITICAL,
                    response_time_ms=0,
                    message="OpenAI API key not configured"
                )
            
            client = openai.AsyncOpenAI(api_key=api_key)
            
            # Simple test call - list models
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
                details={
                    "api_key_configured": True,
                    "response_time_threshold": response_time < 5000
                }
            )
            
        except asyncio.TimeoutError:
            return HealthCheckResult(
                service="openai",
                status=HealthStatus.DEGRADED,
                response_time_ms=self.check_timeout * 1000,
                message="OpenAI API timeout"
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "api key" in error_msg:
                status = HealthStatus.CRITICAL
                message = "OpenAI authentication error"
            elif "rate limit" in error_msg:
                status = HealthStatus.DEGRADED
                message = "OpenAI rate limit exceeded"
            else:
                status = HealthStatus.DEGRADED
                message = f"OpenAI error: {str(e)}"
            
            return HealthCheckResult(
                service="openai",
                status=status,
                response_time_ms=-1,
                message=message
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
            elif system_memory.percent > 90:  # System memory critical
                status = HealthStatus.DEGRADED
                message = f"System memory critical: {system_memory.percent:.1f}%"
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
                    "available_memory_mb": round(system_memory.available / 1024 / 1024, 2),
                    "disk_usage_percent": round(psutil.disk_usage('/').percent, 2)
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
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            
            # Try to import redis
            try:
                import redis.asyncio as redis
            except ImportError:
                # Fallback to sync redis for now
                import redis
                client = redis.Redis.from_url(redis_url, decode_responses=True)
                result = client.ping()
                response_time = (time.time() - start_time) * 1000
                
                return HealthCheckResult(
                    service="redis",
                    status=HealthStatus.HEALTHY if result else HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    message="Redis operational (sync)" if result else "Redis ping failed",
                    details={
                        "connection_type": "sync",
                        "ping_result": result
                    }
                )
            
            # Async redis implementation
            client = redis.Redis.from_url(redis_url, decode_responses=True)
            
            # Test Redis with ping
            result = await asyncio.wait_for(
                client.ping(),
                timeout=self.check_timeout
            )
            response_time = (time.time() - start_time) * 1000
            
            # Get Redis info
            try:
                info = await client.info()
            except:
                info = {}
            
            await client.aclose()
            
            return HealthCheckResult(
                service="redis",
                status=HealthStatus.HEALTHY if result else HealthStatus.DEGRADED,
                response_time_ms=response_time,
                message="Redis operational" if result else "Redis ping failed",
                details={
                    "connection_type": "async",
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2) if info.get("used_memory") else None,
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses")
                }
            )
            
        except asyncio.TimeoutError:
            return HealthCheckResult(
                service="redis",
                status=HealthStatus.DEGRADED,
                response_time_ms=self.check_timeout * 1000,
                message="Redis timeout"
            )
        except Exception as e:
            # Redis is optional for basic functionality - don't degrade system status
            error_msg = str(e).lower()
            if "connection" in error_msg or "connect" in error_msg:
                return HealthCheckResult(
                    service="redis",
                    status=HealthStatus.HEALTHY,  # Treat as healthy since it's optional
                    response_time_ms=-1,
                    message="Redis not available (optional service)"
                )
            else:
                return HealthCheckResult(
                    service="redis",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=-1,
                    message=f"Redis error: {str(e)}"
                )
    
    async def check_agent_health(self) -> HealthCheckResult:
        """Check health of core agents by testing imports and basic functionality"""
        start_time = time.time()
        
        try:
            agent_status = {}
            
            # Test core agent imports
            try:
                from services.orchestrator.main import HolisticOrchestrator
                agent_status["orchestrator"] = "importable"
            except Exception as e:
                agent_status["orchestrator"] = f"import_error: {str(e)}"
            
            try:
                from services.agents.memory.main import HolisticMemoryAgent
                agent_status["memory"] = "importable"
            except Exception as e:
                agent_status["memory"] = f"import_error: {str(e)}"
            
            try:
                from services.agents.insights.main import HolisticInsightsAgent
                agent_status["insights"] = "importable"
            except Exception as e:
                agent_status["insights"] = f"import_error: {str(e)}"
            
            try:
                from services.agents.adaptation.main import HolisticAdaptationEngine
                agent_status["adaptation"] = "importable"
            except Exception as e:
                agent_status["adaptation"] = f"import_error: {str(e)}"
            
            # Count import errors
            import_errors = sum(1 for status in agent_status.values() if "import_error" in status)
            
            response_time = (time.time() - start_time) * 1000
            
            if import_errors == 0:
                status = HealthStatus.HEALTHY
                message = "All agents importable"
            elif import_errors <= 2:
                status = HealthStatus.DEGRADED
                message = f"{import_errors} agents have import issues"
            else:
                status = HealthStatus.CRITICAL
                message = f"Multiple agent import failures: {import_errors}"
            
            return HealthCheckResult(
                service="agents",
                status=status,
                response_time_ms=response_time,
                message=message,
                details=agent_status
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="agents",
                status=HealthStatus.DEGRADED,
                response_time_ms=-1,
                message=f"Agent health check error: {str(e)}"
            )
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks in parallel"""
        # Build check list conditionally
        check_tasks = [
            self.check_database_health(),
            self.check_openai_health(),
            self.check_system_health(),
            self.check_agent_health()
        ]
        
        # Only include Redis if it's enabled
        if self.redis_enabled:
            check_tasks.append(self.check_redis_health())
        
        checks = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Update database metrics after health checks
        try:
            from .metrics import metrics
            await metrics.update_database_metrics()
        except Exception as e:
            logger.debug(f"Could not update database metrics after health check: {e}")
        
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
            },
            "system_info": {
                "environment": os.getenv("ENVIRONMENT", "production"),
                "version": "1.0.0",
                "uptime_check": True
            }
        }

# Global health checker instance
health_checker = HealthChecker()