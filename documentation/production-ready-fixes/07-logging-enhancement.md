# P2: Logging Enhancement

## Why This Issue Exists

### Current Problem
- Basic logging without structured context
- No log aggregation or centralized viewing
- Difficult to trace requests across services
- No correlation between logs and metrics
- Limited debugging information in production

### Evidence from Current Code
```python
# Current basic logging throughout codebase
import logging
logger = logging.getLogger(__name__)
logger.info("User analysis completed")  # No context!
logger.error(f"Error: {e}")  # No request ID or trace
```

### Impact on Production Operations
- **Slow Debugging**: Manual log searching without correlation
- **Poor Visibility**: Can't trace user journeys across services
- **Reactive Response**: Issues discovered after user complaints
- **Limited Context**: Logs lack business and technical context

### Real-World Debugging Scenarios
```
Scenario 1: User reports routine generation failure
Current: Search through text logs manually
Enhanced: Filter by user_id, trace request through all services

Scenario 2: Performance degradation
Current: No correlation between logs and metrics
Enhanced: Logs include timing, memory usage, and correlation IDs

Scenario 3: Error investigation
Current: Basic error message without context
Enhanced: Full request context, user state, and error chain
```

## How to Fix

### Implementation Strategy

#### 1. Structured Logging with Context
```python
# shared_libs/logging/structured_logger.py
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
import asyncio

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')
service_name_var: ContextVar[str] = ContextVar('service_name', default='holisticos')

class StructuredLogger:
    """Enhanced logger with structured context"""
    
    def __init__(self, name: str, service_name: str = "holisticos"):
        self.logger = logging.getLogger(name)
        self.service_name = service_name
        
        # Configure JSON formatter
        self._configure_json_logging()
    
    def _configure_json_logging(self):
        """Configure JSON structured logging"""
        formatter = JsonFormatter()
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # File handler for production
        file_handler = logging.FileHandler('/tmp/holisticos.log')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)
    
    def _get_base_context(self) -> Dict[str, Any]:
        """Get base logging context"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "service": service_name_var.get(self.service_name),
            "request_id": request_id_var.get(''),
            "user_id": user_id_var.get(''),
            "environment": os.getenv("ENVIRONMENT", "production")
        }
    
    def info(self, message: str, **extra_context):
        """Log info with structured context"""
        context = {**self._get_base_context(), **extra_context}
        self.logger.info(message, extra={"context": context})
    
    def error(self, message: str, error: Exception = None, **extra_context):
        """Log error with full context"""
        context = {
            **self._get_base_context(),
            **extra_context
        }
        
        if error:
            context.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "error_traceback": traceback.format_exc()
            })
        
        self.logger.error(message, extra={"context": context})
    
    def warning(self, message: str, **extra_context):
        """Log warning with context"""
        context = {**self._get_base_context(), **extra_context}
        self.logger.warning(message, extra={"context": context})
    
    def debug(self, message: str, **extra_context):
        """Log debug with context"""
        context = {**self._get_base_context(), **extra_context}
        self.logger.debug(message, extra={"context": context})

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logs"""
    
    def format(self, record):
        log_entry = {
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add structured context if available
        if hasattr(record, 'context'):
            log_entry.update(record.context)
        
        return json.dumps(log_entry, default=str)

def get_logger(name: str) -> StructuredLogger:
    """Get structured logger instance"""
    return StructuredLogger(name)
```

#### 2. Request Correlation Middleware
```python
# shared_libs/middleware/correlation_middleware.py
import uuid
from fastapi import Request, Response
from typing import Callable
from shared_libs.logging.structured_logger import request_id_var, user_id_var, service_name_var

class CorrelationMiddleware:
    """Middleware to add correlation IDs to requests"""
    
    def __init__(self, service_name: str = "holisticos"):
        self.service_name = service_name
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        
        # Extract user ID from path or headers
        user_id = request.path_params.get("user_id", "")
        if not user_id:
            user_id = request.headers.get("x-user-id", "")
        
        # Set context variables
        request_id_var.set(correlation_id)
        user_id_var.set(user_id)
        service_name_var.set(self.service_name)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["x-correlation-id"] = correlation_id
        response.headers["x-service"] = self.service_name
        
        return response

# Add to FastAPI app
from shared_libs.middleware.correlation_middleware import CorrelationMiddleware
app.middleware("http")(CorrelationMiddleware())
```

#### 3. Business Context Logging
```python
# shared_libs/logging/business_logger.py
from shared_libs.logging.structured_logger import get_logger
from typing import Dict, Any

class BusinessLogger:
    """Logger for business events with domain context"""
    
    def __init__(self):
        self.logger = get_logger("business")
    
    def user_analysis_started(self, user_id: str, archetype: str, analysis_type: str):
        """Log when user analysis begins"""
        self.logger.info(
            "User analysis started",
            event_type="analysis_started",
            user_id=user_id,
            archetype=archetype,
            analysis_type=analysis_type
        )
    
    def user_analysis_completed(self, user_id: str, archetype: str, duration_ms: float, 
                              insights_count: int, cost_usd: float):
        """Log successful analysis completion"""
        self.logger.info(
            "User analysis completed successfully",
            event_type="analysis_completed",
            user_id=user_id,
            archetype=archetype,
            duration_ms=duration_ms,
            insights_count=insights_count,
            cost_usd=cost_usd
        )
    
    def user_analysis_failed(self, user_id: str, archetype: str, error: Exception, 
                           duration_ms: float):
        """Log analysis failure"""
        self.logger.error(
            "User analysis failed",
            error=error,
            event_type="analysis_failed",
            user_id=user_id,
            archetype=archetype,
            duration_ms=duration_ms
        )
    
    def routine_generated(self, user_id: str, routine_type: str, exercises_count: int):
        """Log routine generation"""
        self.logger.info(
            "Routine generated",
            event_type="routine_generated",
            user_id=user_id,
            routine_type=routine_type,
            exercises_count=exercises_count
        )
    
    def api_cost_tracked(self, user_id: str, endpoint: str, cost_usd: float, 
                        daily_total: float):
        """Log API cost tracking"""
        self.logger.info(
            "API cost tracked",
            event_type="cost_tracked",
            user_id=user_id,
            endpoint=endpoint,
            cost_usd=cost_usd,
            daily_total_usd=daily_total
        )

# Global business logger
business_logger = BusinessLogger()
```

#### 4. Performance Logging Decorator
```python
# shared_libs/logging/performance_logger.py
import functools
import time
import psutil
from shared_libs.logging.structured_logger import get_logger

logger = get_logger("performance")

def log_performance(operation_name: str, track_memory: bool = False):
    """Decorator to log performance metrics"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss if track_memory else 0
            
            try:
                result = await func(*args, **kwargs)
                
                # Calculate metrics
                duration_ms = (time.time() - start_time) * 1000
                memory_delta = 0
                
                if track_memory:
                    end_memory = psutil.Process().memory_info().rss
                    memory_delta = (end_memory - start_memory) / 1024 / 1024  # MB
                
                # Log success metrics
                logger.info(
                    f"{operation_name} completed",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    memory_delta_mb=round(memory_delta, 2) if track_memory else None,
                    status="success"
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Log failure metrics
                logger.error(
                    f"{operation_name} failed",
                    error=e,
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    status="failed"
                )
                raise
        
        return wrapper
    return decorator

# Usage examples
@log_performance("behavior_analysis", track_memory=True)
async def run_behavior_analysis(user_id: str):
    # Analysis logic
    pass

@log_performance("routine_generation")
async def generate_routine_plan(user_id: str, archetype: str):
    # Generation logic
    pass
```

#### 5. Update API Endpoints with Enhanced Logging
```python
# services/api_gateway/openai_main.py - ENHANCED LOGGING

from shared_libs.logging.structured_logger import get_logger
from shared_libs.logging.business_logger import business_logger
from shared_libs.logging.performance_logger import log_performance

# Replace basic logging
logger = get_logger("api_gateway")

@app.post("/api/user/{user_id}/routine/generate")
@log_performance("routine_generation_api", track_memory=True)
async def generate_fresh_routine_plan(user_id: str, request: PlanGenerationRequest):
    """Enhanced routine generation with comprehensive logging"""
    
    # Log request start
    logger.info(
        "Routine generation request received",
        user_id=user_id,
        archetype=request.archetype,
        endpoint="routine_generation"
    )
    
    business_logger.user_analysis_started(
        user_id=user_id,
        archetype=request.archetype,
        analysis_type="routine_generation"
    )
    
    try:
        start_time = time.time()
        
        # Original logic with enhanced logging
        behavior_analysis = await get_or_create_shared_behavior_analysis(
            user_id, request.archetype
        )
        
        logger.debug(
            "Behavior analysis retrieved",
            user_id=user_id,
            has_existing_analysis=bool(behavior_analysis.get("existing_analysis"))
        )
        
        routine_plan = await run_memory_enhanced_routine_generation(
            user_id=user_id,
            archetype=request.archetype,
            behavior_analysis=behavior_analysis
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log successful completion
        business_logger.routine_generated(
            user_id=user_id,
            routine_type=request.archetype,
            exercises_count=len(routine_plan.get("exercises", []))
        )
        
        logger.info(
            "Routine generation completed successfully",
            user_id=user_id,
            duration_ms=duration_ms,
            exercises_count=len(routine_plan.get("exercises", []))
        )
        
        return RoutinePlanResponse(
            status="success",
            user_id=user_id,
            routine_plan=routine_plan
        )
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        # Log failure with full context
        business_logger.user_analysis_failed(
            user_id=user_id,
            archetype=request.archetype,
            error=e,
            duration_ms=duration_ms
        )
        
        logger.error(
            "Routine generation failed",
            error=e,
            user_id=user_id,
            archetype=request.archetype,
            duration_ms=duration_ms
        )
        
        raise HTTPException(status_code=500, detail=str(e))
```

#### 6. Log Aggregation Setup
```python
# config/logging_config.py
import logging.config
import os

# Render.com compatible logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structured': {
            '()': 'shared_libs.logging.structured_logger.JsonFormatter',
        },
        'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'structured',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'structured',
            'filename': '/tmp/holisticos.log',
            'mode': 'a'
        }
    },
    'loggers': {
        'holisticos': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'business': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'performance': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}

def setup_logging():
    """Initialize logging configuration"""
    logging.config.dictConfig(LOGGING_CONFIG)
```

#### 7. Error Tracking Integration
```python
# shared_libs/monitoring/error_tracking.py
import traceback
from typing import Dict, Any, Optional
from shared_libs.logging.structured_logger import get_logger
from shared_libs.monitoring.alerting import alert_manager, AlertSeverity

logger = get_logger("error_tracking")

class ErrorTracker:
    """Enhanced error tracking with alerting"""
    
    def __init__(self):
        self.error_counts = {}
        self.alert_thresholds = {
            "error_rate": 10,  # 10 errors per hour triggers alert
            "critical_errors": 3   # 3 critical errors triggers immediate alert
        }
    
    async def track_error(self, error: Exception, context: Dict[str, Any], 
                         severity: str = "error"):
        """Track error with full context"""
        error_key = f"{type(error).__name__}:{context.get('operation', 'unknown')}"
        
        # Increment error count
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Enhanced error logging
        logger.error(
            "Error tracked",
            error=error,
            error_key=error_key,
            error_count=self.error_counts[error_key],
            context=context,
            severity=severity
        )
        
        # Check for alert conditions
        if severity == "critical" and self.error_counts[error_key] >= 3:
            await alert_manager.send_alert(
                AlertSeverity.CRITICAL,
                f"Critical Error Pattern: {error_key}",
                {
                    "Error Type": type(error).__name__,
                    "Error Count": self.error_counts[error_key],
                    "Context": str(context),
                    "Recent Message": str(error)
                }
            )
        elif self.error_counts[error_key] >= self.alert_thresholds["error_rate"]:
            await alert_manager.send_alert(
                AlertSeverity.WARNING,
                f"High Error Rate: {error_key}",
                {
                    "Error Type": type(error).__name__,
                    "Error Count": self.error_counts[error_key],
                    "Operation": context.get('operation', 'unknown')
                }
            )

# Global error tracker
error_tracker = ErrorTracker()
```

## What is the Expected Outcome

### Enhanced Debugging Capabilities
```python
debugging_improvements = {
    "request_tracing": "Follow user requests across all services",
    "structured_context": "Rich context in every log entry",
    "correlation_ids": "Link logs, metrics, and errors",
    "business_events": "Track user journey and business metrics",
    "performance_insights": "Detailed timing and resource usage"
}
```

### Operational Excellence
- **Faster Issue Resolution**: Find root cause in minutes, not hours
- **Proactive Monitoring**: Business events trigger alerts before user complaints
- **Better Insights**: Understand user behavior and system performance patterns
- **Cost Tracking**: Detailed OpenAI API cost attribution by user/operation

### Before vs After Debugging

**Before (Basic Logging)**:
```
User reports issue → Search text logs → Manual correlation → Slow resolution
```

**After (Structured Logging)**:
```
User reports issue → Filter by correlation ID → Full request trace → Fast resolution
```

### Log Entry Examples

**Enhanced Request Log**:
```json
{
  "level": "INFO",
  "message": "Routine generation completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "holisticos",
  "request_id": "req_abc123",
  "user_id": "user_456",
  "operation": "routine_generation",
  "duration_ms": 1250,
  "archetype": "Foundation Builder",
  "exercises_count": 8,
  "cost_usd": 0.02,
  "memory_delta_mb": 2.1
}
```

### Success Criteria
- [ ] All requests have correlation IDs
- [ ] Structured JSON logs for all services
- [ ] Business event tracking
- [ ] Performance metrics in logs
- [ ] Error tracking with alerting
- [ ] Request-to-response tracing capability

### Monitoring Integration
```python
log_monitoring = {
    "dashboards": [
        "Request volume by endpoint",
        "Error rates and patterns", 
        "Performance trends",
        "Business metrics (costs, user activity)",
        "System health correlation"
    ],
    "alerts": [
        "High error rates",
        "Slow response times",
        "Critical error patterns",
        "Cost anomalies"
    ]
}
```

### Dependencies
- Updated logging configuration
- Correlation middleware deployment
- Log aggregation service (can use Render's built-in logging)
- Dashboard configuration

### Risk Mitigation
- Gradual rollout of structured logging
- Configurable log levels to control verbosity
- Performance impact monitoring
- Fallback to basic logging if issues arise

---

**Estimated Effort**: 1 day  
**Risk Level**: Low (enhances observability)  
**MVP Impact**: Medium - Essential for production operations