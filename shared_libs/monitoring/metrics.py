"""
Prometheus Metrics Collection System for HolisticOS
Tracks API performance, system resources, and business metrics
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import functools
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Define core metrics
REQUEST_COUNT = Counter(
    'holisticos_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'holisticos_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf'))
)

ACTIVE_CONNECTIONS = Gauge(
    'holisticos_active_database_connections',
    'Active database connections in pool'
)

IDLE_CONNECTIONS = Gauge(
    'holisticos_idle_database_connections', 
    'Idle database connections in pool'
)

OPENAI_API_CALLS = Counter(
    'holisticos_openai_calls_total',
    'OpenAI API calls',
    ['model', 'status', 'endpoint']
)

OPENAI_API_DURATION = Histogram(
    'holisticos_openai_duration_seconds',
    'OpenAI API call duration',
    ['model', 'endpoint'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, float('inf'))
)

OPENAI_API_COST = Counter(
    'holisticos_openai_cost_total',
    'OpenAI API costs in USD'
)

MEMORY_USAGE = Gauge(
    'holisticos_memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'holisticos_cpu_usage_percent',
    'CPU usage percentage'
)

ERROR_COUNT = Counter(
    'holisticos_errors_total',
    'Total errors',
    ['service', 'error_type', 'endpoint']
)

ANALYSIS_COUNT = Counter(
    'holisticos_analysis_total',
    'Total behavior analyses performed',
    ['user_archetype', 'analysis_type']
)

INSIGHTS_GENERATED = Counter(
    'holisticos_insights_generated_total',
    'Total insights generated',
    ['insight_type', 'user_archetype']
)

MEMORY_OPERATIONS = Counter(
    'holisticos_memory_operations_total',
    'Memory system operations',
    ['operation_type', 'memory_layer']
)

HEALTH_CHECK_STATUS = Gauge(
    'holisticos_health_check_status',
    'Health check status (1=healthy, 0=unhealthy)',
    ['service']
)

HEALTH_CHECK_DURATION = Histogram(
    'holisticos_health_check_duration_seconds',
    'Health check duration',
    ['service'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float('inf'))
)

class MetricsCollector:
    """Collect and expose metrics for monitoring"""
    
    def __init__(self):
        self.start_time = time.time()
        self.total_requests = 0
        self.total_errors = 0
    
    def track_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Track HTTP request metrics"""
        self.total_requests += 1
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        if status_code >= 400:
            self.total_errors += 1
    
    def track_openai_call(self, model: str, endpoint: str, status: str, duration: float = 0, cost: float = 0):
        """Track OpenAI API calls, duration, and costs"""
        OPENAI_API_CALLS.labels(model=model, status=status, endpoint=endpoint).inc()
        
        if duration > 0:
            OPENAI_API_DURATION.labels(model=model, endpoint=endpoint).observe(duration)
        
        if cost > 0:
            OPENAI_API_COST.inc(cost)
    
    def track_analysis(self, user_archetype: str, analysis_type: str):
        """Track behavior analysis operations"""
        ANALYSIS_COUNT.labels(user_archetype=user_archetype, analysis_type=analysis_type).inc()
    
    def track_insight_generation(self, insight_type: str, user_archetype: str):
        """Track insight generation"""
        INSIGHTS_GENERATED.labels(insight_type=insight_type, user_archetype=user_archetype).inc()
    
    def track_memory_operation(self, operation_type: str, memory_layer: str):
        """Track memory system operations"""
        MEMORY_OPERATIONS.labels(operation_type=operation_type, memory_layer=memory_layer).inc()
    
    def update_health_check_metrics(self, service: str, is_healthy: bool, duration: float):
        """Update health check metrics"""
        HEALTH_CHECK_STATUS.labels(service=service).set(1 if is_healthy else 0)
        HEALTH_CHECK_DURATION.labels(service=service).observe(duration)
    
    def update_system_metrics(self):
        """Update system-level metrics"""
        try:
            import psutil
            process = psutil.Process()
            
            # Update memory usage
            MEMORY_USAGE.set(process.memory_info().rss)
            
            # Update CPU usage (non-blocking)
            try:
                cpu_percent = process.cpu_percent()
                if cpu_percent is not None:
                    CPU_USAGE.set(cpu_percent)
            except:
                pass  # CPU measurement might fail occasionally
            
            # Update database connections (if pool available)
            try:
                from shared_libs.database.connection_pool import db_pool
                # Note: This is a sync function, so we can't await here
                # Database metrics will be updated separately by health checks
                logger.debug("Database metrics updated via health checks")
            except Exception as e:
                logger.debug(f"Could not update database metrics: {e}")
                
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def track_error(self, service: str, error_type: str, endpoint: str = "unknown"):
        """Track errors by service, type, and endpoint"""
        ERROR_COUNT.labels(service=service, error_type=error_type, endpoint=endpoint).inc()
        self.total_errors += 1
    
    async def update_database_metrics(self):
        """Update database metrics (async version for health checks)"""
        try:
            from shared_libs.database.connection_pool import db_pool
            pool_status = await db_pool.get_pool_status()
            
            if isinstance(pool_status, dict):
                current_size = pool_status.get("current_size", 0)
                idle_size = pool_status.get("idle_connections", 0)
                
                ACTIVE_CONNECTIONS.set(max(0, current_size - idle_size))
                IDLE_CONNECTIONS.set(idle_size)
        except Exception as e:
            logger.debug(f"Could not update database metrics: {e}")
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic runtime statistics"""
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": round(uptime, 2),
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": round(self.total_errors / max(self.total_requests, 1), 4),
            "requests_per_second": round(self.total_requests / max(uptime, 1), 2)
        }

def track_endpoint_metrics(endpoint_name: str):
    """Decorator to automatically track endpoint metrics"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            method = "POST"  # Most of our endpoints are POST
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                error_type = type(e).__name__
                
                # Track the error
                metrics.track_error("api", error_type, endpoint_name)
                
                # Log the error for debugging
                logger.error(f"Endpoint {endpoint_name} error: {error_type} - {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                metrics.track_request(method, endpoint_name, status_code, duration)
        
        return wrapper
    return decorator

def track_openai_metrics(model: str = "gpt-4o", endpoint: str = "unknown"):
    """Decorator to track OpenAI API calls"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error(f"OpenAI API error in {endpoint}: {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                # Estimate cost based on duration and model (rough estimate)
                estimated_cost = duration * 0.001 if model == "gpt-4o" else duration * 0.0005
                metrics.track_openai_call(model, endpoint, status, duration, estimated_cost)
        
        return wrapper
    return decorator

def track_memory_metrics(operation_type: str, memory_layer: str):
    """Decorator to track memory operations"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                metrics.track_memory_operation(operation_type, memory_layer)
                return result
            except Exception as e:
                metrics.track_error("memory", type(e).__name__, f"{operation_type}_{memory_layer}")
                raise
        
        return wrapper
    return decorator

# Global metrics collector instance
metrics = MetricsCollector()

# Utility functions for metrics export
def get_prometheus_metrics() -> str:
    """Get Prometheus-formatted metrics"""
    try:
        # Update system metrics before export
        metrics.update_system_metrics()
        return generate_latest()
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        return f"# Error generating metrics: {e}\n"

def get_metrics_content_type() -> str:
    """Get the correct content type for Prometheus metrics"""
    return CONTENT_TYPE_LATEST