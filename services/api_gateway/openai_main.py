"""
HolisticOS Enhanced API Gateway
Multi-Agent System with Memory, Insights, and Adaptation capabilities
Supports both Phase 1 (simple) and Phase 2 (complete multi-agent) workflows
"""

import asyncio
import logging
import os
import sys
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Environment-aware logging
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_DEVELOPMENT = ENVIRONMENT in ["development", "dev"]

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Global helper to convert all enums to strings for JSON serialization
def convert_enums_to_strings(obj):
    """
    Recursively convert all enum values to strings in nested dict/list structures.
    This prevents "Object of type X is not JSON serializable" errors.
    """
    if isinstance(obj, dict):
        return {k: convert_enums_to_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_enums_to_strings(item) for item in obj]
    elif hasattr(obj, 'value'):  # It's an Enum
        return obj.value
    else:
        return obj

from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Request, Header, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import openai
import time

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Setup logging
logger = logging.getLogger(__name__)

# Import monitoring system
try:
    from shared_libs.monitoring.health_checker import health_checker
    from shared_libs.monitoring.metrics import metrics, track_endpoint_metrics, get_prometheus_metrics, get_metrics_content_type
    from shared_libs.monitoring.alerting import alert_manager, monitor_health_continuously, AlertSeverity
    MONITORING_AVAILABLE = True
        # # Production: Verbose print removed  # Commented to reduce noise
except ImportError as e:
    pass  # Monitoring not available
    MONITORING_AVAILABLE = False

# Import rate limiting system
try:
    from shared_libs.rate_limiting.rate_limiter import rate_limiter
    from shared_libs.rate_limiting.middleware import rate_limit_middleware, add_rate_limit_context_middleware
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
        # # Production: Verbose print removed  # Commented to reduce noise
except ImportError as e:
    pass  # Rate limiting not available
    RATE_LIMITING_AVAILABLE = False

# Import error handling
try:
    from shared_libs.exceptions.holisticos_exceptions import (
        HolisticOSException, ValidationException, AuthenticationException,
        RetryableException, PermanentException
    )
    ERROR_HANDLING_AVAILABLE = True
except ImportError as e:
    pass  # Error handling not available
    ERROR_HANDLING_AVAILABLE = False

# Define API Key security scheme for Swagger UI
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

app = FastAPI(
    title="HolisticOS Enhanced API Gateway",
    version="2.0.0",
    description="Multi-Agent Health Optimization System with Memory, Insights, and Adaptation",
    # Configure security scheme for Swagger UI
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
    # Define security schemes in OpenAPI spec
    openapi_tags=[
        {
            "name": "Insights V2",
            "description": "Insights generation and management endpoints"
        }
    ]
)

# Customize OpenAPI schema to include security definitions
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add API Key security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "X-API-Key": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API Key for authentication. Use: `hosa_flutter_app_2024`"
        }
    }

    # Apply security to all /api/v2/insights endpoints
    if "paths" in openapi_schema:
        for path, path_item in openapi_schema["paths"].items():
            if "/api/v2/insights" in path:
                for method in path_item.values():
                    if isinstance(method, dict) and "operationId" in method:
                        method["security"] = [{"X-API-Key": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Production error handling middleware
async def production_error_handler(request: Request, call_next):
    """Production error handling middleware that prevents sensitive data exposure"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # Log the full error for debugging (server-side only)
        logger.error(f"Unhandled exception in {request.url.path}: {str(e)}", exc_info=True)
        
        # Return sanitized error response (no sensitive data)
        if ERROR_HANDLING_AVAILABLE and isinstance(e, HolisticOSException):
            # Use custom exception handling
            error_response = e.to_dict()
            # Remove any sensitive details for client
            if "database" in str(e).lower() or "connection" in str(e).lower():
                error_response["message"] = "Service temporarily unavailable"
            status_code = 429 if isinstance(e, RateLimitExceeded) else 500
        else:
            # Generic error response for unknown exceptions
            error_response = {
                "error": "InternalServerError",
                "message": "An unexpected error occurred. Please try again later.",
                "error_code": "internal_error"
            }
            status_code = 500
        
        return Response(
            content=json.dumps(error_response),
            status_code=status_code,
            headers={"Content-Type": "application/json"}
        )

# Configure CORS with secure settings
from shared_libs.config.security_settings import get_cors_config
from shared_libs.middleware.input_validator import validate_request_middleware, RequestSizeLimit
import re

# Custom origin validator to allow all localhost ports
def is_localhost_origin(origin: str) -> bool:
    """Check if origin is localhost with any port"""
    localhost_pattern = r'^https?://localhost(:\d+)?$'
    return bool(re.match(localhost_pattern, origin))

# Get base CORS config
cors_config = get_cors_config()

# Manual override to ensure X-API-Key header is allowed
cors_config['allow_headers'] = cors_config.get('allow_headers', []) + ['X-API-Key']

# Add custom origin validator for localhost
original_origins = cors_config.get('allow_origins', [])

def custom_allow_origins(origin: str) -> bool:
    """Allow configured origins + any localhost port"""
    return origin in original_origins or is_localhost_origin(origin)

# Use allow_origin_regex to match localhost with any port
cors_config['allow_origin_regex'] = r'https?://localhost(:\d+)?'

app.add_middleware(
    CORSMiddleware,
    **cors_config
)

# Add production error handling middleware (first in chain)
app.middleware("http")(production_error_handler)

# Add input validation middleware (lightweight, header/path validation only)
app.middleware("http")(validate_request_middleware)

# DISABLED: RequestSizeLimit middleware causes request body consumption issues
# TODO: Implement proper ASGI-level request size limiting
# app.add_middleware(RequestSizeLimit, max_size=2 * 1024 * 1024)  # 2MB limit

# Configure rate limiting - TEMPORARILY DISABLED DUE TO MIDDLEWARE ISSUES
# TODO: Fix rate limiting middleware to not block requests
# if RATE_LIMITING_AVAILABLE:
#     # Add rate limiter to app state
#     app.state.limiter = rate_limiter.limiter

#     # Add exception handler for rate limits
#     app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

#     # Add middleware for rate limit headers and context
#     app.middleware("http")(add_rate_limit_context_middleware)
#     app.middleware("http")(rate_limit_middleware)
    
        # # Production: Verbose print removed  # Commented to reduce noise

# Integrate Phase 2 Health Data Endpoints - CTO Integration
try:
    from .health_data_endpoints import router as health_data_router
    app.include_router(health_data_router)
        # # Production: Verbose print removed  # Commented to reduce noise
    # print("[ENDPOINTS] [ENDPOINTS] Real user data endpoints now available:")  # Commented for error-only mode
except ImportError as e:
    pass  # Health data endpoints not available
except Exception as e:
    print(f"[ERROR] Failed to integrate health data endpoints: {e}")

# Integrate Insights Endpoints
        # # Production: Verbose print removed  # Commented to reduce noise
try:
    from .insights_endpoints import router as insights_router
        # # Production: Verbose print removed  # Commented to reduce noise
    app.include_router(insights_router)
        # # Production: Verbose print removed  # Commented to reduce noise
except Exception as e:
    print(f"[ERROR] [ERROR] Failed to integrate insights endpoints: {e}")

# Integrate User Engagement Endpoints - TEMPORARILY DISABLED FOR OPENAPI FIX
try:
    from .engagement_endpoints import router as engagement_router
    app.include_router(engagement_router)
    pass
    print("  - POST /api/v1/engagement/task-checkin")
    print("  - GET /api/v1/engagement/tasks/{profile_id}")
    print("  - POST /api/v1/engagement/journal")
    print("  - POST /api/v1/engagement/extract-plan-items")
except ImportError as e:
    pass  # Engagement endpoints not available
except Exception as e:
    print(f"[ERROR] [ERROR] Failed to integrate engagement endpoints: {e}")

# Integrate Calendar Selection Endpoints
try:
    from .calendar_endpoints import router as calendar_router
    app.include_router(calendar_router)
    pass
    print("  - GET /api/calendar/available-items/{profile_id}")
except Exception as e:
    print(f"[ERROR] [ERROR] Failed to integrate calendar selection endpoints: {e}")

# Integrate Archetype Management Endpoints
try:
    from .archetype_router import router as archetype_router
    app.include_router(archetype_router, prefix="/api")
    pass
    print("  - GET /api/user/{user_id}/available-archetypes")
    print("  - GET /api/user/{user_id}/archetype/{analysis_id}/summary")
except Exception as e:
    print(f"[ERROR] [ERROR] Failed to integrate archetype management endpoints: {e}")

# Integrate Admin API Endpoints
try:
    from .admin_apis import register_admin_routes
    register_admin_routes(app)
    pass
    print("  - GET /api/admin/users")
    print("  - GET /api/admin/user/{user_id}/overview")
    print("  - GET /api/admin/user/{user_id}/analysis-data")
except ImportError as e:
    pass  # Admin API endpoints not available
except Exception as e:
    print(f"[ERROR] [ERROR] Failed to integrate admin API endpoints: {e}")
    print("Full traceback:")
    traceback.print_exc()

# Integrate Analysis Results Endpoints
try:
    from .analysis_results_endpoints import router as analysis_router
    app.include_router(analysis_router)
    pass
    print("  - GET /api/v1/analysis/user/{user_id}/results")
    print("  - GET /api/v1/analysis/user/{user_id}/latest-with-data")
    print("  - GET /api/v1/analysis/result/{analysis_id}/status")
    print("  - POST /api/v1/analysis/user/{user_id}/extract-latest")
except ImportError as e:
    pass  # Analysis results endpoints not available
except Exception as e:
    print(f"[ERROR] [ERROR] Failed to integrate analysis results endpoints: {e}")

# 🔥 ENERGY ZONES SERVICE INTEGRATION
try:
    # Import the energy zones router from the api directory
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../api'))
    from energy_zones_endpoints import router as energy_zones_router
    app.include_router(energy_zones_router)
    pass
    print("  - GET /api/v1/energy-zones/{user_id}")
    print("  - GET /api/v1/energy-zones/{user_id}/current")
    print("  - GET /api/v1/energy-zones/{user_id}/summary")
    print("  - GET /api/v1/energy-zones/{user_id}/for-planning")
    print("  - POST /api/v1/energy-zones/{user_id}/routine-with-zones")
    print("  - GET /api/v1/energy-zones/{user_id}/debug")
    print("  - GET /api/v1/energy-zones/health")
except ImportError as e:
    pass  # Energy Zones Service endpoints not available
except Exception as e:
    print(f"[ERROR] [ERROR] Failed to integrate Energy Zones Service endpoints: {e}")

# 🤖 HOLISTIC INTEGRATION ENDPOINTS (for holistic-ai conversational service)
try:
    from holistic_integration import router as holistic_integration_router
    app.include_router(holistic_integration_router)
    pass
    # Endpoints available for conversational AI service
except ImportError as e:
    pass  # Holistic Integration endpoints not available
except Exception as e:
    print(f"[ERROR] [ERROR] Failed to integrate Holistic Integration endpoints: {e}")

# [DATA] CONTEXT ENDPOINTS (comprehensive chatbot context)
try:
    from .context_endpoints import router as context_router
    app.include_router(context_router)
except ImportError as e:
    pass  # Context endpoints not available
except Exception as e:
    print(f"[ERROR] [ERROR] Failed to integrate context endpoints: {e}")

# [INFO] INSIGHTS V2 ENDPOINTS (standalone insights system - Phase 1)
try:
    from services.insights_v2.api_endpoints import router as insights_v2_router
    app.include_router(insights_v2_router)
    print("[SUCCESS] [INSIGHTS_V2] Endpoints registered successfully")
except ImportError as e:
    print(f"[WARNING] [INSIGHTS_V2] Module not available: {e}")
except Exception as e:
    print(f"[ERROR] [INSIGHTS_V2] Failed to register endpoints: {e}")

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Global variables for agent instances (initialized on startup)
orchestrator = None
memory_agent = None
insights_agent = None
adaptation_agent = None

# =====================================================================# REQUEST/RESPONSE MODELS
# =====================================================================
# Legacy Phase 1 Models
class AnalysisRequest(BaseModel):
    user_id: str
    archetype: str

class AnalysisResponse(BaseModel):
    status: str
    user_id: str
    archetype: str
    message: str
    analysis: Optional[Dict[str, Any]] = None

# Enhanced Phase 2 Models
class CompleteAnalysisRequest(BaseModel):
    user_id: str
    archetype: str
    analysis_number: Optional[int] = 1
    preferences: Optional[Dict[str, Any]] = None

class CompleteAnalysisResponse(BaseModel):
    status: str
    workflow_id: str
    user_id: str
    archetype: str
    message: str
    current_stage: str
    estimated_completion_minutes: int

class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    user_id: str
    current_stage: str
    completed_stages: List[str]
    progress_percentage: int
    start_time: str
    estimated_completion: Optional[str] = None
    results_available: List[str]

class InsightsRequest(BaseModel):
    user_id: str
    archetype: str
    insight_type: str = "comprehensive"  # comprehensive, patterns, trends
    time_horizon: str = "medium_term"    # short_term, medium_term, long_term
    focus_areas: Optional[List[str]] = None

class InsightsResponse(BaseModel):
    status: str
    user_id: str
    insights: List[Dict[str, Any]]
    confidence_score: float
    recommendations: List[str]
    patterns_identified: int

class AdaptationRequest(BaseModel):
    user_id: str
    archetype: str
    trigger: str  # poor_adherence, engagement_decline, user_feedback, etc.
    context: Dict[str, Any]
    urgency: str = "medium"  # low, medium, high, critical
    user_feedback: Optional[str] = None

class AdaptationResponse(BaseModel):
    status: str
    user_id: str
    adaptations_made: List[Dict[str, Any]]
    confidence: float
    expected_impact: str
    monitoring_plan: Dict[str, Any]

class MemoryRequest(BaseModel):
    user_id: str
    memory_type: str = "all"  # all, working, shortterm, longterm, meta
    category: Optional[str] = None
    query_context: Optional[str] = None

class MemoryResponse(BaseModel):
    status: str
    user_id: str
    memory_data: Dict[str, Any]
    insights: List[str]
    retrieved_at: str

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    version: str
    system: str
    agents_status: Optional[Dict[str, str]] = None
    database_status: Optional[Dict[str, Any]] = None

# On-Demand Plan Generation Models
class PlanGenerationRequest(BaseModel):
    archetype: Optional[str] = None  # Use stored archetype if not provided
    preferences: Optional[Dict[str, Any]] = None  # User preferences for customization
    timezone: Optional[str] = None  # User's IANA timezone (e.g., "America/New_York", "Asia/Kolkata")

class RoutinePlanResponse(BaseModel):
    status: str
    user_id: str
    routine_plan: Dict[str, Any]
    analysis_id: Optional[str] = None  # ID of the stored analysis in holistic_analysis_results
    behavior_analysis: Optional[Dict[str, Any]] = None  # Include behavior analysis in response
    circadian_analysis: Optional[Dict[str, Any]] = None  # Include circadian analysis in response
    generation_metadata: Dict[str, Any]
    cached: bool = False

class NutritionPlanResponse(BaseModel):
    status: str
    user_id: str
    nutrition_plan: Dict[str, Any]
    generation_metadata: Dict[str, Any]
    cached: bool = False

# Markdown Regeneration Models
class MarkdownRegenerationRequest(BaseModel):
    updated_plan_markdown: str
    source: str = "conversational_modification"

class MarkdownRegenerationResponse(BaseModel):
    success: bool
    analysis_id: Optional[str] = None
    extraction_triggered: bool = False
    message: str = ""
    error: Optional[str] = None

# New Behavior Analysis Models
class BehaviorAnalysisRequest(BaseModel):
    force_refresh: Optional[bool] = False
    archetype: Optional[str] = None

class BehaviorAnalysisResponse(BaseModel):
    status: str
    user_id: str
    analysis_type: str  # "fresh", "cached"
    behavior_analysis: Dict[str, Any]
    metadata: Dict[str, Any]

# Circadian Analysis Models
class CircadianAnalysisRequest(BaseModel):
    force_refresh: Optional[bool] = False
    archetype: Optional[str] = None

class CircadianAnalysisResponse(BaseModel):
    status: str
    user_id: str
    analysis_type: str  # "fresh", "cached"
    circadian_analysis: Dict[str, Any]
    metadata: Dict[str, Any]

# =====================================================================# AGENT INITIALIZATION
# =====================================================================
@app.on_event("startup")
async def initialize_agents():
    """Initialize all agents and database pool on startup"""
    global orchestrator, memory_agent, insights_agent, adaptation_agent
    
    try:
        # print("[STARTUP] Initializing HolisticOS Multi-Agent System...")  # Commented for error-only mode
        
        # Initialize database connection pool first
        try:
            from shared_libs.database.connection_pool import db_pool
            await db_pool.initialize()
        # # Production: Verbose print removed  # Commented to reduce noise
        except Exception as e:
            pass  # Database pool initialization failed
        
        # Initialize agents
        from services.orchestrator.main import HolisticOrchestrator
        from services.agents.memory.main import HolisticMemoryAgent
        from services.agents.insights.main import HolisticInsightsAgent
        from services.agents.adaptation.main import HolisticAdaptationEngine
        
        orchestrator = HolisticOrchestrator()
        memory_agent = HolisticMemoryAgent()
        insights_agent = HolisticInsightsAgent()
        adaptation_agent = HolisticAdaptationEngine()

        # NEW: Initialize background job queue worker for Sahha data archival
        try:
            from services.background import get_job_queue
            job_queue = get_job_queue()
            await job_queue.start()
            logger.info("[STARTUP] Background worker started successfully")
        except Exception as e:
            logger.error(f"[STARTUP] Failed to start background worker: {e}")
            # Non-critical - continue without background archival

        # NEW: Initialize background scheduler for automated Sahha data refresh
        try:
            from services.background.scheduler_service import get_scheduler
            scheduler = get_scheduler()
            await scheduler.start()
            logger.info("[STARTUP] Background scheduler started successfully")
        except Exception as e:
            logger.error(f"[STARTUP] Failed to start background scheduler: {e}")
            # Non-critical - system works without scheduler (just no proactive refresh)

        # REMOVED: Automatic background scheduler - now using on-demand analysis
        # Behavior analysis will be triggered only when routine/nutrition plans are requested
        # # Production: Verbose print removed  # Commented to reduce noise
        
        # Initialize monitoring system
        if MONITORING_AVAILABLE:
            try:
                # Set startup time for uptime tracking
                app.state.start_time = time.time()
                
                # Start background health monitoring
                asyncio.create_task(monitor_health_continuously())
        # # Production: Verbose print removed  # Commented to reduce noise
                
                # Send startup notification
                await alert_manager.send_alert(
                    AlertSeverity.INFO,
                    "HolisticOS System Started",
                    {
                        "version": "2.0.0",
                        "environment": os.getenv("ENVIRONMENT", "production"),
                        "agents_initialized": 4,
                        "monitoring_enabled": True
                    },
                    service="system"
                )
        # # Production: Verbose print removed  # Commented to reduce noise
            except Exception as e:
                pass  # Monitoring system initialization failed
        
        # # Production: Verbose print removed  # Commented to reduce noise
        
    except Exception as e:
        print(f"[ERROR] Error initializing agents: {e}")
        # Continue with limited functionality
        if MONITORING_AVAILABLE:
            try:
                await alert_manager.send_alert(
                    AlertSeverity.CRITICAL,
                    "HolisticOS Startup Failed",
                    {
                        "error": str(e),
                        "startup_phase": "agent_initialization"
                    },
                    service="system"
                )
            except:
                pass

@app.on_event("shutdown")
async def shutdown_agents():
    """Clean shutdown of all agents and services"""
    try:
        print("[SHUTDOWN] Shutting down HolisticOS Multi-Agent System...")

        # NEW: Stop background worker
        try:
            from services.background import get_job_queue
            job_queue = get_job_queue()
            await job_queue.stop()
            logger.info("[SHUTDOWN] Background worker stopped")
        except Exception as e:
            logger.error(f"[SHUTDOWN] Failed to stop background worker: {e}")

        # NEW: Stop background scheduler
        try:
            from services.background.scheduler_service import get_scheduler
            scheduler = get_scheduler()
            await scheduler.stop()
            logger.info("[SHUTDOWN] Background scheduler stopped")
        except Exception as e:
            logger.error(f"[SHUTDOWN] Failed to stop background scheduler: {e}")

        # Stop behavior analysis scheduler
        from services.scheduler.behavior_analysis_scheduler import stop_behavior_analysis_scheduler
        await stop_behavior_analysis_scheduler()

        # Close database connection pool
        try:
            from shared_libs.database.connection_pool import db_pool
            await db_pool.close()
        # # Production: Verbose print removed  # Commented to reduce noise
        except Exception as e:
            pass  # Database pool shutdown failed

        # # Production: Verbose print removed  # Commented to reduce noise

    except Exception as e:
        print(f"[ERROR] Error during shutdown: {e}")

# =====================================================================# HELPER FUNCTIONS
# =====================================================================
def get_score_actual_date(score) -> str:
    """
    Get actual data occurrence date from score_date_time, with fallback to created_at
    
    Args:
        score: HealthScore object with score_date_time and created_at fields
        
    Returns:
        str: Date in YYYY-MM-DD format representing when the data actually occurred
    """
    try:
        # Prefer score_date_time (actual data occurrence date)
        if hasattr(score, 'score_date_time') and score.score_date_time:
            if isinstance(score.score_date_time, str):
                # Handle string datetime formats
                return datetime.fromisoformat(score.score_date_time.replace('Z', '+00:00')).strftime("%Y-%m-%d")
            else:
                # Handle datetime objects
                return score.score_date_time.strftime("%Y-%m-%d")
    except (ValueError, AttributeError) as e:
        pass  # Handle score_date_time parsing errors
    
    # Fallback to created_at if score_date_time is unavailable/invalid
    if hasattr(score, 'created_at') and score.created_at:
        return score.created_at.strftime("%Y-%m-%d")
    
    # Last resort fallback
    return datetime.now().strftime("%Y-%m-%d")

# =====================================================================# API ENDPOINTS
# =====================================================================
@app.get("/")
async def root():
    """Root endpoint with system status"""
    agent_status = {}
    if orchestrator:
        agent_status["orchestrator"] = "ready"
    if memory_agent:
        agent_status["memory"] = "ready"
    if insights_agent:
        agent_status["insights"] = "ready"
    if adaptation_agent:
        agent_status["adaptation"] = "ready"
    
    return {
        "message": "HolisticOS Enhanced API Gateway", 
        "status": "running", 
        "version": "2.0.0",
        "mode": "Phase 2 - Complete Multi-Agent System",
        "agents": agent_status,
        "capabilities": [
            "Legacy Analysis (Phase 1)",
            "Complete Multi-Agent Workflows (Phase 2)",
            "Memory Management",
            "AI-Powered Insights", 
            "Strategy Adaptation",
            "Workflow Orchestration"
        ]
    }

@app.get("/debug/openapi")
async def debug_openapi_generation():
    """Debug endpoint to test OpenAPI schema generation"""
    try:
        schema = app.openapi()
        return {
            "status": "success",
            "message": "OpenAPI schema generated successfully",
            "path_count": len(schema.get("paths", {})),
            "component_count": len(schema.get("components", {}).get("schemas", {}))
        }
    except Exception as e:
        import traceback
        return {
            "status": "error", 
            "message": f"OpenAPI generation failed: {str(e)}",
            "traceback": traceback.format_exc()
        }

# Production health check with enhanced security
async def simple_health_check():
    """Simple health check when full monitoring is not available"""
    try:
        uptime = time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
        
        # Basic production health check
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": round(uptime, 2),
            "version": "2.0.0",
            "environment": os.getenv("ENVIRONMENT", "production"),
            "monitoring": "basic",
            "services": {
                "api_gateway": "operational",
                "rate_limiting": "enabled" if RATE_LIMITING_AVAILABLE else "disabled",
                "monitoring": "enabled" if MONITORING_AVAILABLE else "basic"
            }
        }
        
        # Quick connectivity tests (non-blocking)
        try:
            # Test database connectivity using Supabase adapter
            from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
            adapter = SupabaseAsyncPGAdapter()
            await asyncio.wait_for(adapter.connect(), timeout=2.0)
            await adapter.close()
            health_status["services"]["database"] = "operational"
        except asyncio.TimeoutError:
            health_status["services"]["database"] = "timeout"
        except Exception:
            health_status["services"]["database"] = "degraded"
        
        return health_status
        
    except Exception as e:
        # Never expose internal errors in health checks
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "api_gateway": "operational",
                "health_check": "limited"
            }
        }

@app.get("/api/health")
async def comprehensive_health_check(api_key: str = Security(api_key_header)):
    """Comprehensive health check endpoint with full system monitoring"""
    if MONITORING_AVAILABLE:
        try:
            health_result = await health_checker.run_comprehensive_health_check()
            # Sanitize health check results for production
            if "details" in health_result:
                # Remove sensitive database connection details
                for service in health_result.get("services", {}).values():
                    if isinstance(service, dict) and "connection_string" in str(service):
                        service["details"] = "[connection details hidden]"
            return health_result
        except Exception as e:
            # Fallback to simple health check if comprehensive fails
            logger.error(f"Comprehensive health check failed: {e}")
            return await simple_health_check()
    else:
        # Fallback to simple health check if monitoring not available
        return await simple_health_check()

@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint for monitoring and alerting"""
    if not MONITORING_AVAILABLE:
        return Response(
            content="# Monitoring system not available\n",
            media_type="text/plain"
        )
    
    # Update system metrics before returning
    metrics.update_system_metrics()
    
    return Response(
        content=get_prometheus_metrics(),
        media_type=get_metrics_content_type()
    )

@app.get("/api/monitoring/stats")
async def get_monitoring_stats():
    """Get comprehensive monitoring statistics and system info"""
    if not MONITORING_AVAILABLE:
        return {
            "error": "Monitoring system not available",
            "basic_stats": {
                "uptime_seconds": time.time() - getattr(app.state, 'start_time', time.time()),
                "version": "2.0.0",
                "environment": os.getenv("ENVIRONMENT", "production")
            }
        }
    
    # Collect comprehensive stats
    health_status = await health_checker.run_comprehensive_health_check()
    basic_stats = metrics.get_basic_stats()
    alert_summary = alert_manager.get_alert_summary()
    
    return {
        "health": health_status,
        "metrics": basic_stats,
        "alerts": alert_summary,
        "system_info": {
            "version": "2.0.0",
            "environment": os.getenv("ENVIRONMENT", "production"),
            "monitoring_enabled": True,
            "uptime_seconds": basic_stats.get("uptime_seconds", 0)
        }
    }

@app.get("/api/monitoring/alerts/history")
async def get_alert_history(hours: int = 24):
    """Get alert history for the specified time period"""
    if not MONITORING_AVAILABLE:
        return {"error": "Monitoring system not available"}
    
    try:
        history = alert_manager.get_alert_history(hours)
        return {
            "alerts": [
                {
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "service": alert.service,
                    "timestamp": alert.timestamp.isoformat(),
                    "details": alert.details
                }
                for alert in history
            ],
            "total_count": len(history),
            "period_hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        return {"error": f"Failed to get alert history: {str(e)}"}

@app.get("/api/admin/rate-limits")
async def get_rate_limit_stats():
    """
    Admin endpoint to monitor rate limiting usage and costs
    """
    if not RATE_LIMITING_AVAILABLE:
        return {"error": "Rate limiting system not available"}
    
    try:
        # Get system-wide rate limiting statistics
        stats = await rate_limiter.get_system_stats()
        
        return {
            "status": "success",
            "rate_limiting": {
                "enabled": True,
                "redis_available": stats.get("redis_available", False),
                "system_stats": stats
            },
            "cost_tracking": {
                "total_cost_today": stats.get("total_cost_today", 0),
                "total_users_with_usage": stats.get("total_users_with_usage", 0),
                "top_users": stats.get("top_users", [])
            },
            "tier_configuration": {
                "free": rate_limiter.tier_limits[rate_limiter.RateLimitTier.FREE],
                "premium": rate_limiter.tier_limits[rate_limiter.RateLimitTier.PREMIUM],
                "admin": rate_limiter.tier_limits[rate_limiter.RateLimitTier.ADMIN]
            },
            "endpoint_costs": rate_limiter.endpoint_costs,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        return {"error": f"Failed to get rate limit stats: {str(e)}"}

@app.get("/api/admin/rate-limits/user/{user_id}")
async def get_user_rate_limit_stats(user_id: str):
    """
    Admin endpoint to get rate limiting stats for a specific user
    """
    if not RATE_LIMITING_AVAILABLE:
        return {"error": "Rate limiting system not available"}
    
    try:
        # Get user-specific statistics
        user_stats = await rate_limiter.get_user_stats(user_id)
        
        return {
            "status": "success",
            "user_stats": user_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting user rate limit stats: {e}")
        return {"error": f"Failed to get user rate limit stats: {str(e)}"}

# =====================================================================# ON-DEMAND PLAN GENERATION ENDPOINTS
# =====================================================================
@app.get("/api/user/{user_id}/routine/latest", response_model=RoutinePlanResponse)
async def get_latest_routine_plan(user_id: str):
    """
    Get the most recent routine plan based on latest behavior analysis
    Fast endpoint - uses cached analysis results
    """
    try:
        # # Production: Verbose print removed  # Commented to reduce noise

        # TODO: Replace with AI Context Integration Service query
        # Analysis history is now handled by AI Context Integration Service
        # For now, return not_found and prompt user to run fresh analysis
        return RoutinePlanResponse(
            status="not_found",
            user_id=user_id,
            routine_plan={},
            generation_metadata={
                "error": "Cached routine plans not yet available. Please run a behavior analysis first.",
                "suggestion": "Use POST /api/analyze to generate initial analysis"
            },
            cached=False
        )

    except Exception as e:
        print(f"[ERROR] [ROUTINE_API_ERROR] Failed to get routine for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve routine plan: {str(e)}")

# =====================================================================
# SIMPLE CONSOLIDATED ENDPOINT
# =====================================================================

@app.get("/api/user/{user_id}/plans/{date}")
async def get_user_plans_for_date(user_id: str, date: str):
    """Simple endpoint: Get routine plan and extract time blocks for calendar"""
    try:
        from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
        from services.plan_extraction_service import PlanExtractionService
        from datetime import datetime
        
        # Validate date
        datetime.strptime(date, '%Y-%m-%d')
        
        adapter = SupabaseAsyncPGAdapter()
        extraction_service = PlanExtractionService()
        
        try:
            # Get routine plan from existing analysis
            query = """
                SELECT id, user_id, archetype, routine_plan, extracted_at, analysis_result
                FROM holistic_analysis_results 
                WHERE user_id = %s 
                AND DATE(extracted_at) = %s
                AND routine_plan IS NOT NULL
                ORDER BY extracted_at DESC
                LIMIT 1
            """
            
            analysis_result = await adapter.fetch_one(query, (user_id, date))
            
            if not analysis_result:
                raise HTTPException(status_code=404, detail=f"No routine plan found for user {user_id} on {date}")
            
            # Extract time blocks from routine plan
            plan_content = extraction_service._parse_plan_content(analysis_result)
            if not plan_content:
                raise HTTPException(status_code=422, detail="Unable to parse routine plan")
            
            extracted_plan = extraction_service.extract_plan_with_time_blocks(plan_content, analysis_result)
            
            # Return simple response
            return {
                "user_id": user_id,
                "date": date,
                "archetype": extracted_plan.archetype,
                "time_blocks": [
                    {
                        "title": block.title,
                        "time_range": block.time_range,
                        "why_it_matters": block.why_it_matters,
                        "connection_to_insights": block.connection_to_insights,
                        "tasks": [
                            {
                                "title": task.title,
                                "description": task.description,
                                "scheduled_time": task.scheduled_time.strftime("%H:%M") if task.scheduled_time else None,
                                "duration_minutes": task.estimated_duration_minutes,
                                "task_type": task.task_type
                            }
                            for task in extracted_plan.tasks if task.time_block_id == block.block_id
                        ]
                    }
                    for block in extracted_plan.time_blocks
                ]
            }
            
        finally:
            await adapter.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/user/{user_id}/routine/{date}", response_model=RoutinePlanResponse)
async def get_routine_plan_by_date(user_id: str, date: str):
    """
    LEGACY ENDPOINT: Get routine plan for a specific date (YYYY-MM-DD format)
    Use /api/user/{user_id}/plans/{date} for new time-block-centric approach
    """
    try:
        from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
        from datetime import datetime

        # Validate date format
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Date must be in YYYY-MM-DD format")

        # Initialize adapter
        adapter = SupabaseAsyncPGAdapter()
        
        try:
            # Query holistic_analysis_results for routine plans on the specified date
            query = """
                SELECT id, user_id, archetype, routine_plan, extracted_at
                FROM holistic_analysis_results 
                WHERE user_id = %s 
                AND DATE(extracted_at) = %s
                AND routine_plan IS NOT NULL
                ORDER BY extracted_at DESC
                LIMIT 1
            """
            
            result = await adapter.fetch_one(query, (user_id, date))
            
            if not result:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No routine plan found for user {user_id} on {date}"
                )
            
            return RoutinePlanResponse(
                status="success",
                user_id=user_id,
                routine_plan=result.get("routine_plan", {}),
                generation_metadata={
                    "date": date,
                    "analysis_id": result.get("id"),
                    "archetype": result.get("archetype"),
                    "extracted_at": result.get("extracted_at").isoformat() if result.get("extracted_at") else None,
                    "source": "historical_analysis"
                },
                cached=True
            )
            
        finally:
            await memory_service.cleanup()
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] [ROUTINE_DATE_API_ERROR] Failed to get routine for {user_id} on {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve routine plan: {str(e)}")

@app.post("/api/user/{user_id}/routine/generate", response_model=RoutinePlanResponse)
@track_endpoint_metrics("routine_generation") if MONITORING_AVAILABLE else lambda x: x
async def generate_fresh_routine_plan(user_id: str, request: PlanGenerationRequest, http_request: Request, api_key: str = Security(api_key_header)):
    """
    Generate a routine plan using shared behavior analysis (eliminates duplicate analysis calls)
    Uses the same pattern as nutrition generation for consistency
    """
    # Validate client API key for external applications (Flutter app)
    api_key = http_request.headers.get("X-API-Key")
    if api_key != "hosa_flutter_app_2024":
        print(f"[AUTH] [AUTH_FAILED] Invalid or missing API key for user {user_id[:8]}... Provided: {api_key}")
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    if IS_DEVELOPMENT:
        print(f"[AUTH] [AUTH_SUCCESS] Valid client API key provided for user {user_id[:8]}...")
    
    from services.request_deduplication_service import request_deduplicator
    
    # Check for duplicate requests
    archetype = request.archetype or "Foundation Builder"
    if request_deduplicator.is_duplicate_request(user_id, archetype, "routine"):
        raise HTTPException(status_code=429, detail="Duplicate routine request detected. Please wait 60 seconds before retrying.")
    
    try:
        # Apply rate limiting if available
        if RATE_LIMITING_AVAILABLE:
            try:
                await rate_limiter.apply_rate_limit(http_request, "routine_generation")
            except Exception as rate_limit_error:
                pass
                raise rate_limit_error
        # print(f"[PROCESS] [ROUTINE_GENERATE] Processing routine request for user {user_id[:8]}...")  # Commented to reduce noise

        # Get behavior analysis from the standalone endpoint
        force_refresh = request.preferences.get('force_refresh', False) if request.preferences else False
        archetype = request.archetype or "Foundation Builder"
        user_timezone = request.timezone  # Extract user's timezone from request

        # MVP-Style Logging: Import and prepare input data (independent of database)
        from services.mvp_style_logger import mvp_logger
        analysis_number = mvp_logger.get_next_analysis_number()
        input_data = {
            "user_id": user_id,
            "archetype": archetype,
            "preferences": request.preferences,
            "endpoint": "/api/user/{user_id}/routine/generate",
            "request_timestamp": datetime.now().isoformat(),
            "force_refresh": force_refresh,
            "analysis_number": analysis_number,
            "request_data": {
                "archetype": request.archetype,
                "preferences": request.preferences
            }
        }

        # NEW: Run parallel behavior + circadian analysis for enhanced routine generation
        print(f"[PROCESS] [ROUTINE_GENERATE] Running parallel behavior + circadian analysis for dynamic planning...")

        # Run both analyses in parallel using same raw data
        import asyncio
        behavior_task = get_or_create_shared_behavior_analysis(user_id, archetype, force_refresh, analysis_number)
        circadian_task = get_or_create_shared_circadian_analysis(user_id, archetype, force_refresh, analysis_number)

        try:
            behavior_analysis, circadian_analysis = await asyncio.gather(
                behavior_task, circadian_task, return_exceptions=True
            )
        except Exception as e:
            print(f"[ERROR] [ROUTINE_GENERATE] Parallel analysis failed: {e}")
            return RoutinePlanResponse(
                status="error",
                user_id=user_id,
                routine_plan={},
                generation_metadata={
                    "error": "Parallel analysis failed",
                    "details": str(e)
                },
                cached=False
            )

        # Check if both analyses succeeded
        behavior_success = behavior_analysis and not isinstance(behavior_analysis, Exception)
        circadian_success = circadian_analysis and not isinstance(circadian_analysis, Exception)

        # CRITICAL: Convert all enums to strings IMMEDIATELY to prevent JSON serialization errors
        if behavior_success:
            behavior_analysis = convert_enums_to_strings(behavior_analysis)
        if circadian_success:
            circadian_analysis = convert_enums_to_strings(circadian_analysis)

        if not behavior_success:
            print(f"[ERROR] [ROUTINE_GENERATE] Behavior analysis failed: {behavior_analysis}")
            return RoutinePlanResponse(
                status="error",
                user_id=user_id,
                routine_plan={},
                generation_metadata={
                    "error": "Behavior analysis failed or returned no results",
                    "suggestion": "Try with force_refresh=true or ensure user has sufficient health data"
                },
                cached=False
            )

        # Log successful parallel execution with detailed data for agent handoff tracking
        pass
        pass

        # DETAILED LOGGING: Log raw data and analysis outputs for agent handoff tracking
        try:
            import json
            import os

            # Create handoff logs directory
            handoff_dir = "logs/agent_handoffs"  # Production: Disabled
            if not os.path.exists(handoff_dir):
                os.makedirs(handoff_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # SIMPLE LOGGING: Just dump the actual agent outputs
            if behavior_success:
                with open(f"{handoff_dir}/01_behavior_analysis_output_{timestamp}.json", 'w') as f:
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "user_id": user_id,
                        "full_behavior_analysis_output": behavior_analysis
                    }, f, indent=2, default=str)

            if circadian_success:
                with open(f"{handoff_dir}/02_circadian_analysis_output_{timestamp}.json", 'w') as f:
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "user_id": user_id,
                        "full_circadian_analysis_output": circadian_analysis
                    }, f, indent=2, default=str)

            pass

        except Exception as log_error:
            pass  # Error logging failed

        # Create combined analysis for routine generation
        combined_analysis = {
            "behavior_analysis": behavior_analysis if behavior_success else {},
            "circadian_analysis": circadian_analysis if circadian_success else {},
            "combined_metadata": {
                "behavior_success": behavior_success,
                "circadian_success": circadian_success,
                "parallel_execution": True,
                "analysis_timestamp": datetime.now().isoformat(),
                "archetype": archetype,
                "force_refresh": force_refresh
            }
        }

        analysis_type = "complete_analysis"  # New analysis type for combined approach
        
        # # Production: Verbose print removed  # Commented to reduce noise
        # print(f"   • Analysis source: Shared behavior analysis service")  # Commented for error-only mode
        # print(f"   • Eliminates duplicate OpenAI calls")  # Commented for error-only mode
        
        # Get user data for routine generation
        from services.user_data_service import UserDataService
        user_service = UserDataService()
        
        try:
            # CRITICAL FIX: Check if behavior analysis has locked timestamp metadata
            locked_timestamp = None
            if isinstance(behavior_analysis, dict) and '_metadata' in behavior_analysis:
                locked_timestamp = behavior_analysis['_metadata'].get('fixed_timestamp')
            
            if locked_timestamp:
                print(f"[AUTH] [RACE_CONDITION_FIX] Using locked timestamp for routine data fetch")
                user_context, _ = await user_service.get_analysis_data(user_id, locked_timestamp)
            else:
        # # Production: Verbose print removed  # Commented to reduce noise
                user_context, _ = await user_service.get_analysis_data(user_id)

            # RAW DATA LOGGING: Log the actual health data that goes into analysis
            try:
                import os
                import json

                handoff_dir = "logs/agent_handoffs"  # Production: Disabled
                if not os.path.exists(handoff_dir):
                    os.makedirs(handoff_dir)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                # SIMPLE LOGGING: Just dump the actual raw data - properly convert to dict
                with open(f"{handoff_dir}/00_raw_health_data_{timestamp}.json", 'w') as f:
                    # Convert user_context to dict if it's a Pydantic model
                    raw_data_dict = user_context.dict() if hasattr(user_context, 'dict') else user_context
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "user_id": user_id,
                        "full_raw_health_data": raw_data_dict
                    }, f, indent=2, default=str)

                # Production: Raw data logging removed

            except Exception as log_error:
                pass  # Raw data logging failed

            # Use the simplified routine generation function
            routine_plan = await run_routine_generation(
                user_id=user_id,
                archetype=archetype,
                behavior_analysis=behavior_analysis,
                circadian_analysis=circadian_analysis if circadian_success else None,
                user_timezone=user_timezone,  # Pass user timezone for accurate date calculation
                preferences=request.preferences  # NEW: Pass user preferences for task selection and scheduling
            )

            # FINAL AGENT HANDOFF: Log the combined analysis → routine generation transformation
            try:
                import os
                import json

                handoff_dir = "logs/agent_handoffs"  # Production: Disabled
                if not os.path.exists(handoff_dir):
                    os.makedirs(handoff_dir)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                # SIMPLE LOGGING: Just dump the actual routine output
                with open(f"{handoff_dir}/03_routine_generation_output_{timestamp}.json", 'w') as f:
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "user_id": user_id,
                        "behavior_analysis_used": behavior_analysis if behavior_success else None,
                        "circadian_analysis_used": circadian_analysis if circadian_success else None,
                        "full_routine_plan_output": routine_plan
                    }, f, indent=2, default=str)

                pass

            except Exception as log_error:
                pass  # Routine generation logging failed

            # STORE PLAN ITEMS: Extract and store plan items for active plan display
            try:
                from services.plan_extraction_service import PlanExtractionService
                
                # Find the most recent behavior analysis ID to associate plan items
                # Query holistic_analysis_results directly via Supabase
                from shared_libs.supabase_client.data_fetcher import get_supabase_client
                supabase = get_supabase_client()
                analysis_result = supabase.table('holistic_analysis_results')\
                    .select('id')\
                    .eq('user_id', user_id)\
                    .eq('analysis_type', 'behavior_analysis')\
                    .order('created_at', desc=True)\
                    .limit(1)\
                    .execute()

                if analysis_result.data and routine_plan:
                    analysis_result_id = str(analysis_result.data[0]['id'])
                    print(f"[STORAGE] [PLAN_STORAGE] Storing plan items for analysis_result_id: {analysis_result_id}")
                    
                    # Extract plan items from the routine plan content
                    extraction_service = PlanExtractionService()
                    
                    # Convert routine plan to extractable format
                    if isinstance(routine_plan, dict) and 'content' in routine_plan:
                        plan_content = routine_plan['content']
                        
                        # Store plan items in database for active plan display
                        stored_items = await extraction_service.extract_and_store_plan_items(
                            analysis_result_id=analysis_result_id,
                            profile_id=user_id
                        )
                        pass
                    
                await memory_service.cleanup()
                    
            except Exception as storage_error:
                pass
                # Don't fail the entire request if plan storage fails
            
            # ARCHETYPE-SPECIFIC TRACKING: Timestamp updates now handled by HolisticMemoryService
            # when storing behavior analysis results - no need for global timestamp update
            
            # Track API cost for rate limiting
            if RATE_LIMITING_AVAILABLE:
                try:
                    await rate_limiter.track_api_cost(user_id, "routine_generation")
                except Exception as cost_error:
                    pass
            
            # Mark request as complete
            request_deduplicator.mark_request_complete(user_id, archetype, "routine")

            # Extract analysis_id from routine_plan if present
            analysis_id = routine_plan.get('analysis_id') if isinstance(routine_plan, dict) else None

            # Prepare response data (exclude analyses from response - only return routine plan)
            response_data = RoutinePlanResponse(
                status="success",
                user_id=user_id,
                routine_plan=routine_plan,
                analysis_id=analysis_id,  # Include analysis_id at top level for easy access
                behavior_analysis=None,  # Excluded from response per user request
                circadian_analysis=None,  # Excluded from response per user request
                generation_metadata={
                    "analysis_decision": "shared_behavior_analysis_service",
                    "analysis_type": analysis_type,
                    "data_quality": "memory_enhanced",
                    "shared_analysis": True,
                    "duplicate_calls_eliminated": True,
                    "personalization_level": "high",
                    "archetype_used": archetype,
                    "preferences_applied": bool(request.preferences),
                    "generation_time": datetime.now().isoformat(),
                    "behavior_analysis_used": behavior_success,  # Indicate if used (but not included in response)
                    "circadian_analysis_used": circadian_success,  # Indicate if used (but not included in response)
                    "sahha_integration": "direct_fetch",  # Indicate Sahha was used
                    "o3_model_used": True  # Indicate o3 model was used
                },
                cached=(analysis_type == "cached")
            )

            # MVP-Style Logging: Log complete routine generation cycle (independent of database)
            try:
                output_data = {
                    "status": response_data.status,
                    "routine_plan": routine_plan,
                    "generation_metadata": response_data.generation_metadata,
                    "analysis_type": analysis_type,
                    "shared_behavior_analysis": True,
                    "cached": response_data.cached,
                    "response_timestamp": datetime.now().isoformat(),
                    "api_cost_tracked": True
                }

                # Collect raw health data if behavior analysis was fresh (not cached)
                raw_health_data = None
                if not response_data.cached and behavior_analysis and behavior_analysis.get("status") == "success":
                    # Raw health data should have been logged during the behavior analysis
                    # For now, we'll log a reference that raw data was generated during behavior analysis
                    raw_health_data = {
                        "data_logged_during_behavior_analysis": True,
                        "behavior_analysis_contained_fresh_data": True,
                        "note": "Raw health data was logged during the shared behavior analysis step",
                        "analysis_number": analysis_number,
                        "user_id": user_id
                    }

                # Log the complete routine generation cycle using enhanced MVP approach
                mvp_logger.log_complete_analysis(
                    input_data=input_data,
                    output_data=output_data,
                    raw_health_data=raw_health_data,
                    user_id=user_id,
                    archetype=archetype
                )
            except Exception as log_error:
                pass  # Never let logging errors break the API response

            return response_data
            
        except Exception as context_error:
            pass
            raise HTTPException(status_code=500, detail=f"Failed to get user data for routine generation: {str(context_error)}")
            
    except Exception as e:
        # Mark request as complete even on error
        request_deduplicator.mark_request_complete(user_id, archetype, "routine")
        print(f"[ERROR] [ROUTINE_GENERATE_ERROR] Failed to generate routine for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate routine plan: {str(e)}")

@app.get("/api/user/{user_id}/nutrition/latest", response_model=NutritionPlanResponse)
async def get_latest_nutrition_plan(user_id: str):
    """
    Get the most recent nutrition plan based on latest behavior analysis
    Fast endpoint - uses cached analysis results
    """
    try:
        # print(f"[NUTRITION] [NUTRITION_API] Getting latest nutrition for user {user_id[:8]}...")  # Commented to reduce noise
        
        # Get latest behavior analysis from memory
        # HolisticMemoryService removed - functionality replaced by AIContextIntegrationService
        memory_service = HolisticMemoryService()
        
        try:
            # Get most recent analysis that includes nutrition plan
            analysis_history = await memory_service.get_analysis_history(user_id, limit=3)
            
            # Find most recent analysis with nutrition plan
            nutrition_plan = None
            behavior_analysis = None
            
            for analysis in analysis_history:
                analysis_result = analysis.analysis_result
                if isinstance(analysis_result, dict) and 'nutrition_plan' in analysis_result:
                    nutrition_plan = analysis_result['nutrition_plan']
                    behavior_analysis = analysis_result.get('behavior_analysis', {})
                    break
            
            if not nutrition_plan:
                return NutritionPlanResponse(
                    status="not_found",
                    user_id=user_id,
                    nutrition_plan={},
                    generation_metadata={
                        "error": "No recent nutrition plan found. Please run a behavior analysis first.",
                        "suggestion": "Use POST /api/analyze to generate initial analysis"
                    },
                    cached=False
                )
            
            # Return cached nutrition with metadata
            return NutritionPlanResponse(
                status="success",
                user_id=user_id,
                nutrition_plan=nutrition_plan,
                generation_metadata={
                    "data_quality": "cached",
                    "personalization_level": "high",
                    "generated_from": "latest_behavior_analysis",
                    "analysis_date": analysis_history[0].created_at.isoformat()
                },
                cached=True
            )
            
        finally:
            await memory_service.cleanup()
            
    except Exception as e:
        print(f"[ERROR] [NUTRITION_API_ERROR] Failed to get nutrition for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve nutrition plan: {str(e)}")

async def _extract_plan_in_background(analysis_id: str, user_id: str):
    """Background task to extract plan items from saved analysis"""
    try:
        from services.plan_extraction_service import PlanExtractionService
        extraction_service = PlanExtractionService()

        logger.info(f"[DATA] [BACKGROUND] Extracting plan for analysis_id: {analysis_id}")

        stored_items = await extraction_service.extract_and_store_plan_items(
            analysis_result_id=analysis_id,
            profile_id=user_id
        )

        logger.info(f"[SUCCESS] [BACKGROUND] Extraction completed: {len(stored_items)} items stored")
    except Exception as e:
        logger.error(f"[ERROR] [BACKGROUND] Extraction failed for {analysis_id}: {e}", exc_info=True)

@app.post("/api/user/{user_id}/routine/regenerate-from-markdown", response_model=MarkdownRegenerationResponse)
@track_endpoint_metrics("markdown_routine_regeneration") if MONITORING_AVAILABLE else lambda x: x
async def regenerate_routine_from_markdown(
    user_id: str,
    request: MarkdownRegenerationRequest,
    http_request: Request,
    background_tasks: BackgroundTasks
):
    """
    Regenerate routine from conversational markdown using existing routine agent

    This endpoint reuses the entire routine generation infrastructure but
    with markdown as input instead of behavior/circadian analysis.

    Flow:
    1. Get user's archetype from latest analysis
    2. Call run_routine_generation() with markdown_plan parameter
    3. Routine agent converts markdown → structured plan
    4. Store in holistic_analysis_results
    5. Trigger extraction to plan_items and time_blocks
    """
    # Validate API key
    api_key = http_request.headers.get("X-API-Key")
    if api_key != "hosa_flutter_app_2024":
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Get archetype first for coordination
    from supabase import create_client, Client
    import os
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

    analysis_result = supabase.table('holistic_analysis_results')\
        .select('archetype')\
        .eq('user_id', user_id)\
        .order('created_at', desc=True)\
        .limit(1)\
        .execute()

    if not analysis_result.data:
        logger.warning(f"[WARNING] [MARKDOWN_REGEN] No previous analysis found for {user_id[:8]}...")
        return MarkdownRegenerationResponse(
            success=False,
            error="No previous analysis found. Please run initial analysis first."
        )

    archetype = analysis_result.data[0]['archetype']

    # COORDINATION: Prevent duplicate markdown regeneration requests
    from services.request_deduplication_service import enhanced_deduplicator

    should_process, cached_result = await enhanced_deduplicator.coordinate_request(
        user_id, archetype, "markdown_routine"
    )

    if not should_process and cached_result:
        logger.info(f"[CACHE] [MARKDOWN_REGEN] Returning cached result for {user_id[:8]}...")
        return MarkdownRegenerationResponse(**cached_result)

    try:
        logger.info(f"[PROCESS] [MARKDOWN_REGEN] Starting markdown regeneration for user {user_id[:8]}...")
        logger.info(f"[SUCCESS] [MARKDOWN_REGEN] Archetype: {archetype}")

        # Create minimal behavior_analysis (required by function signature)
        # The markdown_plan will override this in the prompt
        minimal_behavior = {
            "archetype": archetype,
            "source": "markdown_regeneration",
            "readiness_level": "Medium"
        }

        # Call simplified routine generation with markdown
        logger.info(f"🤖 [MARKDOWN_REGEN] Calling routine agent with markdown ({len(request.updated_plan_markdown)} chars)")
        routine_plan = await run_routine_generation(
            user_id=user_id,
            archetype=archetype,
            behavior_analysis=minimal_behavior,
            circadian_analysis=None,
            markdown_plan=request.updated_plan_markdown  # NEW: Pass markdown
        )

        # Extract analysis_id from the stored result
        # The function already stores in holistic_analysis_results
        analysis_result = supabase.table('holistic_analysis_results')\
            .select('id')\
            .eq('user_id', user_id)\
            .eq('analysis_type', 'routine_plan')\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()

        analysis_id = analysis_result.data[0]['id'] if analysis_result.data else None
        logger.info(f"[CACHE] [MARKDOWN_REGEN] Plan stored with analysis_id: {analysis_id}")

        # Trigger extraction in background (non-blocking for faster response)
        extraction_triggered = False
        if analysis_id and routine_plan:
            logger.info(f"[DATA] [MARKDOWN_REGEN] Scheduling background extraction for analysis_id: {analysis_id}")
            background_tasks.add_task(_extract_plan_in_background, analysis_id, user_id)
            extraction_triggered = True

        # Create response (returns immediately, extraction happens in background)
        response = MarkdownRegenerationResponse(
            success=True,
            analysis_id=analysis_id,
            extraction_triggered=extraction_triggered,
            message="Plan saved successfully. Extraction will complete in background."
        )

        # COORDINATION: Mark request complete and cache result
        enhanced_deduplicator.complete_request(
            user_id, archetype, "markdown_routine", response.dict()
        )

        return response

    except Exception as e:
        logger.error(f"[ERROR] [MARKDOWN_REGEN] Error: {e}")

        # COORDINATION: Mark request complete even on error
        enhanced_deduplicator.complete_request(
            user_id, archetype, "markdown_routine",
            {"success": False, "error": str(e)}
        )

        return MarkdownRegenerationResponse(
            success=False,
            error=str(e)
        )

@app.post("/api/user/{user_id}/nutrition/generate", response_model=NutritionPlanResponse)
@track_endpoint_metrics("nutrition_generation") if MONITORING_AVAILABLE else lambda x: x
async def generate_fresh_nutrition_plan(user_id: str, request: PlanGenerationRequest, http_request: Request):
    """
    Generate a nutrition plan using the standalone behavior analysis endpoint
    Calls POST /api/user/{user_id}/behavior/analyze to get analysis, then generates nutrition plan
    """
    from services.request_deduplication_service import request_deduplicator
    
    # Check for duplicate requests
    archetype = request.archetype or "Foundation Builder"
    if request_deduplicator.is_duplicate_request(user_id, archetype, "nutrition"):
        raise HTTPException(status_code=429, detail="Duplicate nutrition request detected. Please wait 60 seconds before retrying.")
    
    try:
        # Apply rate limiting if available
        if RATE_LIMITING_AVAILABLE:
            try:
                await rate_limiter.apply_rate_limit(http_request, "nutrition_generation")
            except Exception as rate_limit_error:
                pass
                raise rate_limit_error
        # print(f"[PROCESS] [NUTRITION_GENERATE] Processing nutrition request for user {user_id[:8]}...")  # Commented to reduce noise
        
        # Get behavior analysis from the standalone endpoint
        force_refresh = request.preferences.get('force_refresh', False) if request.preferences else False
        archetype = request.archetype or "Foundation Builder"
        
        # Create behavior analysis request
        behavior_request = BehaviorAnalysisRequest(
            force_refresh=force_refresh,
            archetype=archetype
        )
        
        # Use shared behavior analysis (eliminates duplicate analysis calls)
        # print(f"📞 [NUTRITION_GENERATE] Getting shared behavior analysis...")  # Commented for error-only mode
        behavior_analysis = await get_or_create_shared_behavior_analysis(user_id, archetype, force_refresh)
        
        if not behavior_analysis:
            return NutritionPlanResponse(
                status="error",
                user_id=user_id,
                nutrition_plan={},
                generation_metadata={
                    "error": "Behavior analysis failed or returned no results",
                    "suggestion": "Try with force_refresh=true or ensure user has sufficient health data"
                },
                cached=False
            )
        
        analysis_type = "shared"  # Indicates shared analysis was used
        
        # # Production: Verbose print removed  # Commented to reduce noise
        # print(f"   • Analysis source: Shared behavior analysis service")  # Commented for error-only mode
        # print(f"   • Eliminates duplicate OpenAI calls")  # Commented for error-only mode
        
        # Get user data for nutrition generation
        from services.user_data_service import UserDataService
        user_service = UserDataService()
        
        try:
            # CRITICAL FIX: Check if behavior analysis has locked timestamp metadata
            locked_timestamp = None
            if isinstance(behavior_analysis, dict) and '_metadata' in behavior_analysis:
                locked_timestamp = behavior_analysis['_metadata'].get('fixed_timestamp')
            
            if locked_timestamp:
                print(f"[AUTH] [RACE_CONDITION_FIX] Using locked timestamp for nutrition data fetch")
                user_context, _ = await user_service.get_analysis_data(user_id, locked_timestamp)
            else:
        # # Production: Verbose print removed  # Commented to reduce noise
                user_context, _ = await user_service.get_analysis_data(user_id)
            
            # Generate nutrition using existing function
            from shared_libs.utils.system_prompts import get_system_prompt

            # Get nutrition plan generation system prompt
            nutrition_prompt = get_system_prompt("plan_generation")
            
            # Use the memory-enhanced nutrition generation function with all /api/analyze features
            nutrition_plan = await run_memory_enhanced_nutrition_generation(
                user_id=user_id,
                archetype=archetype,
                behavior_analysis=behavior_analysis
            )
            
            # ARCHETYPE-SPECIFIC TRACKING: Timestamp updates now handled by HolisticMemoryService
            # when storing behavior analysis results - no need for global timestamp update
            
            # Track API cost for rate limiting
            if RATE_LIMITING_AVAILABLE:
                try:
                    await rate_limiter.track_api_cost(user_id, "nutrition_generation")
                except Exception as cost_error:
                    pass
            
            # Mark request as complete
            request_deduplicator.mark_request_complete(user_id, archetype, "nutrition")
            
            return NutritionPlanResponse(
                status="success",
                user_id=user_id,
                nutrition_plan=nutrition_plan,
                generation_metadata={
                    "analysis_decision": "shared_behavior_analysis_service",
                    "analysis_type": analysis_type,
                    "data_quality": "memory_enhanced",
                    "shared_analysis": True,
                    "duplicate_calls_eliminated": True,
                    "personalization_level": "high",
                    "archetype_used": archetype,
                    "preferences_applied": bool(request.preferences),
                    "generation_time": datetime.now().isoformat()
                },
                cached=(analysis_type == "cached")
            )
            
        except Exception as context_error:
            pass
            raise HTTPException(status_code=500, detail=f"Failed to get user data for nutrition generation: {str(context_error)}")

            
    except Exception as e:
        # Mark request as complete even on error
        request_deduplicator.mark_request_complete(user_id, archetype, "nutrition")
        print(f"[ERROR] [NUTRITION_GENERATE_ERROR] Failed to generate nutrition for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate nutrition plan: {str(e)}")

@app.get("/api/user/{user_id}/insights/latest")
async def get_latest_insights(user_id: str):
    """Get latest AI insights for user - Phase 4.2 Sprint 3"""
    try:
        # # Production: Verbose print removed  # Commented to reduce noise
        
        # Get latest analysis with insights from memory
        # HolisticMemoryService removed - functionality replaced by AIContextIntegrationService
        memory_service = HolisticMemoryService()
        
        try:
            # Get most recent analysis that includes insights
            analysis_history = await memory_service.get_analysis_history(user_id, limit=3)
            
            insights = None
            analysis_date = None
            
            for analysis in analysis_history:
                analysis_result = analysis.analysis_result
                if isinstance(analysis_result, dict) and 'ai_insights' in analysis_result:
                    insights = analysis_result['ai_insights']
                    analysis_date = analysis.created_at.isoformat()
                    break
            
            if not insights:
                return {
                    "status": "not_found",
                    "user_id": user_id,
                    "insights": {},
                    "message": "No recent insights found. Please run a behavior analysis first.",
                    "suggestion": "Use POST /api/analyze to generate analysis with insights"
                }
            
            return {
                "status": "success",
                "user_id": user_id,
                "insights": insights,
                "analysis_date": analysis_date,
                "cached": True
            }
            
        finally:
            await memory_service.cleanup()
            
    except Exception as e:
        print(f"[ERROR] [INSIGHTS_API_ERROR] Failed to get insights for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve insights: {str(e)}")

@app.post("/api/user/{user_id}/insights/generate")
async def generate_fresh_insights(user_id: str, request: dict):
    """Generate fresh insights on-demand - Phase 4.2 Sprint 3"""
    try:
        print(f"[GENERATE] [INSIGHTS_GENERATE] Generating fresh insights for user {user_id[:8]}...")
        
        # Get latest behavior analysis as context
        # HolisticMemoryService removed - functionality replaced by AIContextIntegrationService
        from services.agents.insights.main import HolisticInsightsAgent
        from shared_libs.event_system.base_agent import AgentEvent
        
        memory_service = HolisticMemoryService()
        
        try:
            # Get most recent analysis for context
            analysis_history = await memory_service.get_analysis_history(user_id, limit=1)
            
            if not analysis_history:
                return {
                    "status": "error",
                    "user_id": user_id,
                    "insights": {},
                    "message": "No behavior analysis found. Please run analysis first.",
                    "suggestion": "Use POST /api/analyze to generate initial analysis"
                }
            
            recent_analysis = analysis_history[0].analysis_result
            archetype = analysis_history[0].archetype_used or "Foundation Builder"
            
            # Generate fresh insights
            insights_agent = HolisticInsightsAgent()
            
            insights_result = await insights_agent.process(AgentEvent(
                event_id=f"ondemand_insights_{datetime.now().timestamp()}",
                event_type="generate_insights",
                source_agent="insights_api",
                payload={
                    "insight_type": request.get("insight_type", "comprehensive"),
                    "time_horizon": request.get("time_horizon", "medium_term"),
                    "focus_areas": request.get("focus_areas", ["behavioral_patterns", "nutrition_adherence", "routine_consistency"]),
                    "trigger_context": recent_analysis
                },
                timestamp=datetime.now(),
                user_id=user_id,
                archetype=archetype
            ))
            
            if insights_result.success:
                insights = insights_result.result
                return {
                    "status": "success",
                    "user_id": user_id,
                    "insights": insights,
                    "generation_metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "insight_type": request.get("insight_type", "comprehensive"),
                        "time_horizon": request.get("time_horizon", "medium_term"),
                        "focus_areas": request.get("focus_areas", ["behavioral_patterns", "nutrition_adherence", "routine_consistency"]),
                        "archetype_used": archetype,
                        "memory_enhanced": True
                    },
                    "cached": False
                }
            else:
                return {
                    "status": "error",
                    "user_id": user_id,
                    "insights": {},
                    "error": insights_result.error_message
                }
                
        finally:
            await memory_service.cleanup()
            
    except Exception as e:
        print(f"[ERROR] [INSIGHTS_GENERATE_ERROR] Failed to generate insights for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@app.post("/api/user/{user_id}/insights/{insight_id}/feedback")
async def provide_insight_feedback(user_id: str, insight_id: str, feedback: dict):
    """Allow users to provide feedback on insights quality - Phase 4.2 Sprint 3"""
    try:
        print(f"[STORAGE] [INSIGHTS_FEEDBACK] Recording feedback for insight {insight_id} from user {user_id[:8]}...")
        
        # Store feedback in memory system for future improvement
        # HolisticMemoryService removed - functionality replaced by AIContextIntegrationService
        memory_service = HolisticMemoryService()
        
        try:
            # Store feedback in working memory for processing
            feedback_data = {
                "insight_id": insight_id,
                "user_feedback": feedback,
                "timestamp": datetime.now().isoformat(),
                "feedback_type": "insights_quality"
            }
            
            await memory_service.store_working_memory(
                user_id=user_id,
                session_id="insights_feedback",
                agent_id="insights_agent",
                memory_type="active_insights",  # Changed from 'insight_feedback' to valid type
                content=feedback_data,
                expires_hours=720  # Keep feedback for 30 days
            )
            
            return {
                "status": "success",
                "user_id": user_id,
                "insight_id": insight_id,
                "message": "Feedback recorded successfully",
                "feedback_stored": True
            }
            
        finally:
            await memory_service.cleanup()
            
    except Exception as e:
        print(f"[ERROR] [INSIGHTS_FEEDBACK_ERROR] Failed to record feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")

@app.post("/api/user/{user_id}/behavior/analyze", response_model=BehaviorAnalysisResponse)
@track_endpoint_metrics("behavior_analysis") if MONITORING_AVAILABLE else lambda x: x
async def analyze_behavior(user_id: str, request: BehaviorAnalysisRequest, http_request: Request):
    """
    Standalone behavior analysis endpoint with 50-item threshold constraint
    Only runs fresh analysis when 50+ new data points exist, otherwise returns cached analysis
    """
    # Apply rate limiting if available (stricter for expensive behavior analysis)
    if RATE_LIMITING_AVAILABLE:
        try:
            await rate_limiter.apply_rate_limit(http_request, "behavior_analysis")
        except Exception as rate_limit_error:
            pass
            raise rate_limit_error

    try:
        # print(f"[ANALYSIS] [BEHAVIOR_ANALYZE] Starting behavior analysis for user {user_id[:8]}...")  # Commented for error-only mode

        # Import required services
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        # HolisticMemoryService removed - functionality replaced by AIContextIntegrationService
        from services.mvp_style_logger import mvp_logger

        # Initialize services
        ondemand_service = await get_ondemand_service()

        # MVP-Style Logging: Prepare input data (independent of database)
        analysis_number = mvp_logger.get_next_analysis_number()
        input_data = {
            "user_id": user_id,
            "archetype": request.archetype or "Foundation Builder",
            "force_refresh": request.force_refresh,
            "endpoint": "/api/user/{user_id}/behavior/analyze",
            "request_timestamp": datetime.now().isoformat(),
            "analysis_number": analysis_number,
            "request_data": {
                "archetype": request.archetype,
                "force_refresh": request.force_refresh
            }
        }
        
        # Check if fresh analysis is needed (50-item threshold)
        decision, metadata = await ondemand_service.should_run_analysis(
            user_id,
            request.force_refresh,
            request.archetype,
            analysis_type="behavior_analysis"  # Track behavior analysis separately
        )

        # Safe enum access for logging
        decision_str = decision.value if hasattr(decision, 'value') else str(decision)
        memory_quality = metadata.get('memory_quality')
        memory_quality_str = memory_quality.value if hasattr(memory_quality, 'value') else str(memory_quality) if memory_quality else 'unknown'

        # # Production: Verbose print removed  # Commented to reduce noise
        # print(f"   • New data points: {metadata['new_data_points']}")  # Commented for error-only mode
        # print(f"   • Threshold: {metadata['threshold_used']}")  # Commented for error-only mode
        # print(f"   • Memory quality: {memory_quality_str}")  # Commented for error-only mode
        # print(f"   • Reason: {metadata['reason']}")  # Commented for error-only mode
        
        behavior_analysis = None
        analysis_type = "unknown"
        
        if decision == AnalysisDecision.FRESH_ANALYSIS or decision == AnalysisDecision.STALE_FORCE_REFRESH:
            # Run fresh behavior analysis using existing logic from /api/analyze
            print(f"[STARTUP] [BEHAVIOR_ANALYZE] Running fresh behavior analysis...")

            # Get archetype from request or use default
            archetype = request.archetype or "Foundation Builder"

            # Use shared behavior analysis with force_refresh=True to ensure fresh analysis
            behavior_analysis = await get_or_create_shared_behavior_analysis(user_id, archetype, force_refresh=True, analysis_number=analysis_number)
            
            if behavior_analysis and behavior_analysis.get("status") == "success":
                analysis_type = "fresh"
                
                # Determine trigger type based on analysis decision
                if decision == AnalysisDecision.FRESH_ANALYSIS:
                    # Add timestamp to make each threshold trigger unique for multiple daily analyses
                    timestamp = datetime.now().strftime("%H%M%S")
                    analysis_trigger = f"threshold_exceeded_{timestamp}"
                else:
                    analysis_trigger = "scheduled"

                # Analysis storage is handled by run_fresh_behavior_analysis_like_api_analyze
                # No need to store again here - would be duplicate
        # # Production: Verbose print removed  # Commented to reduce noise
            else:
                # Fallback to cached if fresh analysis fails
                pass
                behavior_analysis = await ondemand_service.get_cached_behavior_analysis(user_id, archetype)
                analysis_type = "cached_fallback"
                
        else:
            # Use cached analysis
            print(f"[CACHE] [BEHAVIOR_ANALYZE] Using cached analysis (below threshold)")
            behavior_analysis = await ondemand_service.get_cached_behavior_analysis(user_id, request.archetype)
            analysis_type = "cached"
        
        # Validate we have behavior analysis
        if not behavior_analysis:
            return BehaviorAnalysisResponse(
                status="error",
                user_id=user_id,
                analysis_type="none",
                behavior_analysis={},
                metadata={
                    "error": "No behavior analysis available and unable to generate new analysis",
                    "suggestion": "Try with force_refresh=true or ensure user has sufficient health data",
                    "decision_metadata": metadata
                }
            )
        
        # Calculate next eligible analysis time
        next_eligible = None
        if analysis_type == "cached" and metadata.get('new_data_points', 0) < 50:
            needed_points = 50 - metadata.get('new_data_points', 0)
            next_eligible = f"Need {needed_points} more data points to trigger fresh analysis"
        
        # Track API cost for rate limiting (only for fresh analysis, not cached)
        if RATE_LIMITING_AVAILABLE and analysis_type == "fresh":
            try:
                await rate_limiter.track_api_cost(user_id, "behavior_analysis")
            except Exception as cost_error:
                pass

        # Prepare response data
        response_data = BehaviorAnalysisResponse(
            status="success",
            user_id=user_id,
            analysis_type=analysis_type,
            behavior_analysis=behavior_analysis,
            metadata={
                "new_data_points": metadata.get('new_data_points', 0),
                "threshold": metadata.get('threshold_used', 50),
                "cache_age_hours": metadata.get('cache_age_hours', 0),
                "memory_quality": metadata.get('memory_quality').value if hasattr(metadata.get('memory_quality'), 'value') else str(metadata.get('memory_quality', 'unknown')),
                "decision_reason": metadata.get('reason', ''),
                "force_refresh_used": request.force_refresh,
                "next_analysis_info": next_eligible,
                "archetype_used": request.archetype or "Foundation Builder"
            }
        )

        # MVP-Style Logging: Log complete analysis cycle (independent of database)
        try:
            output_data = {
                "status": response_data.status,
                "analysis_type": analysis_type,
                "behavior_analysis": behavior_analysis,
                "decision_metadata": metadata,
                "response_timestamp": datetime.now().isoformat(),
                "analysis_decision": decision_str if 'decision_str' in locals() else str(decision),
                "memory_quality": memory_quality_str if 'memory_quality_str' in locals() else "unknown",
                "api_cost_tracked": analysis_type == "fresh"
            }

            # Log the complete analysis cycle using MVP approach
            mvp_logger.log_complete_analysis(
                input_data=input_data,
                output_data=output_data,
                user_id=user_id,
                archetype=request.archetype or "Foundation Builder"
            )
        except Exception as log_error:
            pass  # Never let logging errors break the API response
        return response_data
        
    except Exception as e:
        print(f"[ERROR] [BEHAVIOR_ANALYZE_ERROR] Failed to analyze behavior for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze behavior: {str(e)}")

@app.post("/api/user/{user_id}/circadian/analyze", response_model=CircadianAnalysisResponse)
@track_endpoint_metrics("circadian_analysis") if MONITORING_AVAILABLE else lambda x: x
async def analyze_circadian_rhythm(user_id: str, request: CircadianAnalysisRequest, http_request: Request):
    """
    Standalone circadian rhythm analysis endpoint with 50-item threshold constraint
    Only runs fresh analysis when 50+ new data points exist, otherwise returns cached analysis

    Uses GPT-4o model for intelligent circadian pattern recognition from biomarker data
    Integrates with existing threshold, memory, and orchestration systems
    """
    # No authentication required (matches behavior/analyze endpoint pattern)
    try:
        # Apply rate limiting if available
        if RATE_LIMITING_AVAILABLE:
            try:
                await rate_limiter.apply_rate_limit(http_request, "circadian_analysis")
            except Exception as rate_limit_error:
                pass
                raise rate_limit_error


        # MVP-Style Logging: Import and prepare input data
        from services.mvp_style_logger import mvp_logger
        analysis_number = mvp_logger.get_next_analysis_number()
        input_data = {
            "user_id": user_id,
            "archetype": request.archetype or "Foundation Builder",
            "force_refresh": request.force_refresh,
            "endpoint": "/api/user/{user_id}/circadian/analyze",
            "request_timestamp": datetime.now().isoformat(),
            "analysis_number": analysis_number,
            "request_data": {
                "archetype": request.archetype,
                "force_refresh": request.force_refresh
            }
        }

        # Use shared circadian analysis orchestration
        archetype = request.archetype or "Foundation Builder"
        circadian_result = await get_or_create_shared_circadian_analysis(
            user_id, archetype, request.force_refresh, analysis_number
        )

        # Determine analysis type and prepare response
        if circadian_result.get("status") == "error":
            return CircadianAnalysisResponse(
                status="error",
                user_id=user_id,
                analysis_type="error",
                circadian_analysis={},
                metadata={
                    "error": circadian_result.get("error", "Unknown error occurred"),
                    "suggestion": "Try with force_refresh=true or check system logs",
                    "analysis_timestamp": datetime.now().isoformat()
                }
            )

        elif circadian_result.get("status") == "skipped":
            return CircadianAnalysisResponse(
                status="success",
                user_id=user_id,
                analysis_type="skipped",
                circadian_analysis={},
                metadata={
                    "reason": "threshold_not_met",
                    "message": "Insufficient new data points for fresh analysis",
                    "suggestion": "Use force_refresh=true to override threshold",
                    "analysis_timestamp": datetime.now().isoformat()
                }
            )

        # Successful analysis - determine if fresh or cached
        analysis_type = "fresh" if circadian_result.get("analysis_type") == "circadian_rhythm" else "cached"

        # Track API cost for rate limiting
        if RATE_LIMITING_AVAILABLE and analysis_type == "fresh":
            try:
                await rate_limiter.track_api_cost(user_id, "circadian_analysis")
            except Exception as cost_error:
                pass

        # Prepare response data
        response_data = CircadianAnalysisResponse(
            status="success",
            user_id=user_id,
            analysis_type=analysis_type,
            circadian_analysis=circadian_result,
            metadata={
                "analysis_decision": f"shared_circadian_analysis_service",
                "data_quality": "threshold_validated",
                "personalization_level": "high",
                "archetype_used": archetype,
                "force_refresh": request.force_refresh,
                "model_used": circadian_result.get("model_used", "gpt-4o"),
                "analysis_timestamp": datetime.now().isoformat()
            }
        )

        # MVP-Style Logging: Complete circadian analysis cycle
        try:
            output_data = {
                "status": response_data.status,
                "circadian_analysis": circadian_result,
                "metadata": response_data.metadata,
                "analysis_type": analysis_type,
                "response_timestamp": datetime.now().isoformat(),
                "api_cost_tracked": analysis_type == "fresh"
            }

            # Log the complete analysis cycle
            mvp_logger.log_complete_analysis(
                input_data=input_data,
                output_data=output_data,
                user_id=user_id,
                archetype=archetype
            )
        except Exception as log_error:
            pass  # Never let logging errors break the API response
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] [CIRCADIAN_ANALYZE_ERROR] Failed to analyze circadian rhythm for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze circadian rhythm: {str(e)}")



# ============================================================================
# ANCHORING ENDPOINT
# ============================================================================

@app.post("/api/v1/anchor/generate")
async def generate_anchors(request: Request):
    """
    Generate anchored tasks by matching plan items to saved schedule events

    Uses Supabase REST API for database access (no database adapters needed)

    Request body:
        {
            "user_id": "user-uuid",
            "date": "2025-11-09",
            "schedule_id": "schedule-uuid" (optional - if null, returns standalone tasks),
            "include_google_calendar": false,
            "confidence_threshold": 0.7
        }

    Response:
        {
            "anchored_tasks": [...],
            "standalone_tasks": [...],
            "message": "Success message"
        }
    """
    try:
        body = await request.json()

        # Use REST API implementation (simpler, no database adapters required)
        from services.api_gateway.anchor_endpoint_rest import generate_anchors_via_rest_api
        result = await generate_anchors_via_rest_api(body)
        return result

    except Exception as e:
        print(f"❌ [ANCHORING] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Anchoring failed: {str(e)}")


async def run_complete_health_analysis(user_id: str, archetype: str) -> dict:
    """
    Complete health analysis with automatic insights generation - Phase 4.2 Sprint 3
    Used by scheduler and on-demand analysis requests
    Integrates insights agent into the main analysis pipeline
    """
    try:
        print(f"[STARTUP] Starting complete health analysis with insights for {user_id}...")
        
        # Run the main analysis using existing analyze_user function
        request = AnalysisRequest(user_id=user_id, archetype=archetype)
        analysis_response = await analyze_user(request)
        
        if analysis_response.status != "success":
            print(f"[ERROR] Main analysis failed: {analysis_response.message}")
            return {
                "status": "error",
                "user_id": user_id,
                "error": analysis_response.message
            }
        
        # Extract analysis results
        analysis_data = analysis_response.analysis
        behavior_analysis = analysis_data.get("behavior_analysis", {})
        nutrition_plan = analysis_data.get("nutrition_plan", {})
        routine_plan = analysis_data.get("routine_plan", {})
        
        # # Production: Verbose print removed  # Commented to reduce noise
        
        # Step 4: Generate AI-Powered Insights using enhanced Insights Agent
        insights = {}
        try:
            from services.agents.insights.main import HolisticInsightsAgent
            from shared_libs.event_system.base_agent import AgentEvent
            
            insights_agent = HolisticInsightsAgent()
            
            insights_result = await insights_agent.process(AgentEvent(
                event_id=f"insights_{datetime.now().timestamp()}",
                event_type="generate_insights",
                source_agent="complete_analysis_pipeline",
                payload={
                    "insight_type": "post_analysis_comprehensive",
                    "time_horizon": "medium_term",
                    "focus_areas": ["behavioral_patterns", "nutrition_adherence", "routine_consistency"],
                    "trigger_context": {
                        "behavior_analysis": behavior_analysis,
                        "nutrition_plan": nutrition_plan, 
                        "routine_plan": routine_plan
                    }
                },
                timestamp=datetime.now(),
                user_id=user_id,
                archetype=archetype
            ))
            
            if insights_result.success:
                insights = insights_result.result
        # # Production: Verbose print removed  # Commented to reduce noise
            else:
                pass
                insights = {"error": insights_result.error_message}
                
        except Exception as insights_error:
            pass
            insights = {"error": str(insights_error)}
        
        # Return enhanced results with insights
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "archetype": archetype,
            "behavior_analysis": behavior_analysis,
            "nutrition_plan": nutrition_plan,
            "routine_plan": routine_plan,
            "ai_insights": insights,  # NEW: AI insights included
            "system_info": analysis_data.get("system_info", {}),
            "models_used": {
                "behavior_analysis": "o3",
                "nutrition_plan": "gpt-4o", 
                "routine_plan": "gpt-4o",
                "ai_insights": "gpt-4"  # NEW: Insights model info
            }
        }
        
    except Exception as e:
        print(f"[ERROR] Complete health analysis failed for {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "user_id": user_id,
            "archetype": archetype,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def prepare_behavior_agent_data(user_context, user_context_summary: str) -> dict:
    """Prepare comprehensive data for behavior analysis agent (o3) - Phase 3.3"""
    try:
        # Behavior agent gets the most comprehensive data for pattern analysis
        behavior_data = {
            "comprehensive_health_context": user_context_summary,
            "detailed_metrics": {
                "data_quality": {
                    "level": (user_context.data_quality.quality_level.value if hasattr(user_context.data_quality, 'quality_level') and hasattr(user_context.data_quality.quality_level, 'value') else str(user_context.data_quality)),

                    "completeness": user_context.data_quality.completeness_score,
                    "scores_count": user_context.data_quality.scores_count,
                    "biomarkers_count": user_context.data_quality.biomarkers_count,
                    "recent_data_available": user_context.data_quality.has_recent_data
                },
                "time_coverage": {
                    "start_date": user_context.date_range.start_date.isoformat(),
                    "end_date": user_context.date_range.end_date.isoformat(),
                    "total_days": user_context.date_range.days
                },
                "activity_patterns": [
                    {
                        "date": get_score_actual_date(score),
                        "type": score.type,
                        "score": score.score,
                        "state": score.data.get("state", "unknown") if score.data else "unknown"
                    }
                    for score in user_context.scores if score.type in ["activity", "sleep", "readiness"]
                ][:15],  # Last 15 key scores for pattern analysis
                "biomarker_categories": {}
            },
            "analysis_focus": "comprehensive_behavior_pattern_analysis"
        }
        
        # Group biomarkers by category for behavior insights
        for bio in user_context.biomarkers[:20]:
            category = bio.category
            if category not in behavior_data["detailed_metrics"]["biomarker_categories"]:
                behavior_data["detailed_metrics"]["biomarker_categories"][category] = []
            behavior_data["detailed_metrics"]["biomarker_categories"][category].append({
                "type": bio.type,
                "date": bio.start_date_time.strftime("%Y-%m-%d")
            })
        
        return behavior_data
        
    except Exception as e:
        return {"error": f"Error preparing behavior data: {str(e)}"}

async def prepare_nutrition_agent_data(user_context, behavior_analysis: dict) -> dict:
    """Prepare nutrition-relevant data for nutrition planning agent (gpt-4o) - Phase 3.3"""
    try:
        # Extract nutrition-relevant insights from behavior analysis
        behavioral_insights = {
            "sophistication_level": behavior_analysis.get("sophistication_assessment", {}).get("category", "unknown"),
            "readiness_level": behavior_analysis.get("readiness_level", "unknown"),
            "primary_goal": behavior_analysis.get("primary_goal", {}),
            "motivation_drivers": behavior_analysis.get("personalized_strategy", {}).get("motivation_drivers", "unknown")
        }
        
        # Filter health data relevant to nutrition planning
        nutrition_relevant_data = {
            "activity_levels": [
                {
                    "date": get_score_actual_date(score),
                    "activity_score": score.score,
                    "state": score.data.get("state", "unknown") if score.data else "unknown"
                }
                for score in user_context.scores if score.type == "activity"
            ][:7],  # Last 7 days of activity
            
            "sleep_quality": [
                {
                    "date": get_score_actual_date(score),
                    "sleep_score": score.score,
                    "state": score.data.get("state", "unknown") if score.data else "unknown"
                }
                for score in user_context.scores if score.type == "sleep"
            ][:7],  # Last 7 days of sleep
            
            "energy_indicators": [
                {
                    "date": get_score_actual_date(score),
                    "readiness_score": score.score,
                    "state": score.data.get("state", "unknown") if score.data else "unknown"
                }
                for score in user_context.scores if score.type == "readiness"
            ][:7],  # Last 7 days of readiness
            
            "nutrition_biomarkers": [
                {
                    "type": bio.type,
                    "category": bio.category,
                    "date": bio.start_date_time.strftime("%Y-%m-%d")
                }
                for bio in user_context.biomarkers 
                if bio.category in ["metabolic", "nutrition", "energy", "recovery"]
            ][:10]  # Nutrition-relevant biomarkers
        }
        
        return {
            "behavioral_insights": behavioral_insights,
            "nutrition_relevant_metrics": nutrition_relevant_data,
            "planning_focus": "nutrition_plan_based_on_activity_sleep_and_goals"
        }
        
    except Exception as e:
        return {"error": f"Error preparing nutrition data: {str(e)}"}

async def prepare_routine_agent_data(user_context, behavior_analysis: dict) -> dict:
    """Prepare routine-relevant data for routine planning agent (gpt-4o) - Phase 3.3"""
    try:
        # Extract routine-relevant insights from behavior analysis
        behavioral_insights = {
            "habit_integration_strategy": behavior_analysis.get("personalized_strategy", {}).get("habit_integration", "unknown"),
            "barrier_mitigation": behavior_analysis.get("personalized_strategy", {}).get("barrier_mitigation", "unknown"),
            "readiness_level": behavior_analysis.get("readiness_level", "unknown"),
            "key_recommendations": behavior_analysis.get("recommendations", [])[:3]  # Top 3 recommendations
        }
        
        # Filter health data relevant to routine planning
        routine_relevant_data = {
            "sleep_patterns": [
                {
                    "date": get_score_actual_date(score),
                    "sleep_score": score.score,
                    "sleep_state": score.data.get("state", "unknown") if score.data else "unknown",
                    "factors": score.data.get("factors", []) if score.data else []
                }
                for score in user_context.scores if score.type == "sleep"
            ][:7],  # Last 7 days for pattern recognition
            
            "activity_patterns": [
                {
                    "date": get_score_actual_date(score),
                    "activity_score": score.score,
                    "activity_state": score.data.get("state", "unknown") if score.data else "unknown",
                    "factors": score.data.get("factors", []) if score.data else []
                }
                for score in user_context.scores if score.type == "activity"
            ][:7],  # Last 7 days for routine optimization
            
            "recovery_readiness": [
                {
                    "date": get_score_actual_date(score),
                    "readiness_score": score.score,
                    "readiness_state": score.data.get("state", "unknown") if score.data else "unknown"
                }
                for score in user_context.scores if score.type == "readiness"
            ][:7],  # Last 7 days for routine timing
            
            "routine_biomarkers": [
                {
                    "type": bio.type,
                    "category": bio.category,
                    "date": bio.start_date_time.strftime("%Y-%m-%d")
                }
                for bio in user_context.biomarkers 
                if bio.category in ["activity", "sleep", "recovery", "stress"]
            ][:10]  # Routine-relevant biomarkers
        }
        
        return {
            "behavioral_insights": behavioral_insights,
            "routine_relevant_metrics": routine_relevant_data,
            "planning_focus": "daily_routine_optimization_based_on_sleep_activity_patterns"
        }
        
    except Exception as e:
        return {"error": f"Error preparing routine data: {str(e)}"}

async def fetch_engagement_context(profile_id: str, days: int = 7) -> dict:
    """Fetch engagement context for AI analysis - privacy-safe"""
    try:
        import aiohttp
        from urllib.parse import urljoin
        
        # Get API base URL
        api_base = os.getenv('API_BASE_URL', 'http://localhost:8001')
        endpoint = f"/api/v1/engagement/engagement-context/{profile_id}"
        url = urljoin(api_base, endpoint)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={'days': days}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    # Return empty context on error
                    return {}
    except Exception as e:
        # Silently fail and return empty context
        return {}

async def format_health_data_for_ai(user_context) -> str:
    """Format health tracking data for AI analysis - Privacy-safe, no IDs exposed"""
    try:
        # Get latest scores for summary (NO IDs)
        recent_scores = {}
        for score in user_context.scores[:10]:  # Latest 10 scores
            score_type = score.type
            if score_type not in recent_scores:
                recent_scores[score_type] = []
            recent_scores[score_type].append({
                'score': score.score,
                'date': get_score_actual_date(score),
                'state': score.data.get('state', 'unknown') if hasattr(score, 'data') and score.data else 'unknown'
            })
        
        # Get key biomarkers (NO IDs)
        key_biomarkers = {}
        for bio in user_context.biomarkers[:20]:  # Latest 20 biomarkers
            bio_type = bio.type
            if bio_type not in key_biomarkers:
                key_biomarkers[bio_type] = []
            # Only include essential data, no IDs
            bio_data_clean = {k: v for k, v in bio.data.items() if not k.endswith('_id') and k != 'id'} if bio.data else {}
            key_biomarkers[bio_type].append({
                'category': bio.category,
                'data': bio_data_clean,
                'date': bio.start_date_time.strftime('%Y-%m-%d') if hasattr(bio, 'start_date_time') else 'unknown'
            })
        
        # Format for AI
        data_summary = []
        
        # Health Scores Summary
        if recent_scores:
            data_summary.append("HEALTH SCORE PATTERNS:")
            for score_type, scores in recent_scores.items():
                avg_score = sum(s['score'] for s in scores) / len(scores)
                latest_state = scores[0]['state']
                data_summary.append(f"  • {score_type.title()} Metrics: {avg_score:.2f} (trend: {latest_state}) - {len(scores)} measurements")
        
        # Biomarkers Summary
        if key_biomarkers:
            data_summary.append("\nBIOMARKER MEASUREMENTS:")
            for bio_type, values in list(key_biomarkers.items())[:10]:  # Top 10 biomarker types
                recent_categories = [v['category'] for v in values[:3]]
                category_summary = ", ".join(set(recent_categories)) if recent_categories else "unknown"
                data_sample_count = len(values)
                data_summary.append(f"  • {bio_type.replace('_', ' ').title()}: {category_summary} category ({data_sample_count} measurements)")
        
        # Activity Patterns
        behavior_data = user_context.behavior_data
        if behavior_data and isinstance(behavior_data, dict):
            data_summary.append("\nACTIVITY PATTERNS:")
            if 'activity_scores' in behavior_data:
                activity_count = len(behavior_data['activity_scores'])
                data_summary.append(f"  • Activity sessions: {activity_count} tracked periods")
            
            if 'sleep_scores' in behavior_data:
                sleep_count = len(behavior_data['sleep_scores'])
                data_summary.append(f"  • Sleep cycles: {sleep_count} recorded periods")
        
        
        return '\n'.join(data_summary) if data_summary else "Health tracking data available for analysis."
        
    except Exception as e:
        return f"Error formatting user data: {str(e)}"

async def run_behavior_analysis(user_id: str, archetype: str) -> dict:
    """
    Behavior analysis that MUST go through OnDemandAnalysisService threshold logic
    This function should only be called by the behavior analysis endpoint after threshold check
    """
    try:
        print(f"[ANALYSIS] [BEHAVIOR_WRAPPER] Starting DIRECT behavior analysis for {user_id[:8]}...")
        pass
        
        # Get user data using existing services
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        
        # Get user context (reuse existing logic from /api/analyze)
        user_context, data_quality = await user_service.get_analysis_data(user_id)
        # Fix datetime bug - safely handle data_quality attribute access
        if hasattr(data_quality, 'value'):
            quality_str = data_quality.value
        elif hasattr(data_quality, 'quality_level') and hasattr(data_quality.quality_level, 'value'):
            quality_str = data_quality.quality_level.value
        else:
            quality_str = str(data_quality) if data_quality else "unknown"
        
        user_context_summary = f"Comprehensive Health Analysis for {archetype} user with {quality_str} data quality."
        
        # Prepare behavior agent data
        behavior_agent_data = await prepare_behavior_agent_data(user_context, user_context_summary)
        
        # Get behavior system prompt
        behavior_prompt = get_system_prompt("behavior_analysis")
        
        # Note: Removed complex logging infrastructure to focus on core functionality
        
        # Run behavior analysis using o3 model (same as /api/analyze)
        print("[ANALYSIS] Running standalone behavior analysis with o3 model...")
        behavior_result = await run_behavior_analysis_o3(behavior_prompt, user_context_summary)
        
        if behavior_result:
        # # Production: Verbose print removed  # Commented to reduce noise
            
            # Note: Agent handoff logging removed - focus on core functionality
            # Safe data quality access
            data_quality_str = data_quality.value if hasattr(data_quality, 'value') else str(data_quality) if data_quality else "unknown"
            
            return {
                "status": "success",
                "behavior_analysis": behavior_result,
                "archetype_used": archetype,
                "data_quality": data_quality_str,
                "model_used": "o3"
            }
        else:
            print(f"[ERROR] [BEHAVIOR_WRAPPER] Behavior analysis failed - no result")
            return {
                "status": "error",
                "error": "Behavior analysis returned no result",
                "behavior_analysis": {}
            }
            
    except Exception as e:
        print(f"[ERROR] [BEHAVIOR_WRAPPER] Error in behavior analysis: {e}")
        return {
            "status": "error", 
            "error": str(e),
            "behavior_analysis": {}
        }


async def run_behavior_analysis_o3(system_prompt: str, user_context: str) -> dict:
    """Run behavior analysis using o3 model for deep analysis - Phase 3.2"""
    try:
        # Use o3 for complex behavior analysis
        client = openai.AsyncOpenAI()
        
        # Note: o3 model only supports default temperature (1)
        response = await client.chat.completions.create(
            model="o3",
            messages=[
                {
                    "role": "system", 
                    "content": f"{system_prompt}\n\nYou are an expert behavioral analyst. Focus on identifying patterns in health tracking data and provide detailed insights."
                },
                {
                    "role": "user", 
                    "content": f"""
{user_context}

Analyze the health tracking patterns and provide a comprehensive behavioral analysis following the HolisticOS framework.

Provide analysis in this JSON structure:
{{
    "behavioral_signature": {{
        "signature": "Detailed behavior pattern description",
        "confidence": 0.0-1.0
    }},
    "sophistication_assessment": {{
        "score": 0-100,
        "category": "Beginner/Intermediate/Advanced/Expert",
        "justification": "Assessment reasoning"
    }},
    "primary_goal": {{
        "goal": "Identified primary health goal",
        "timeline": "Estimated timeline",
        "success_metrics": "Measurable success indicators"
    }},
    "personalized_strategy": {{
        "motivation_drivers": "Key motivation factors",
        "habit_integration": "Habit formation recommendations",
        "barrier_mitigation": "Obstacle management strategies"
    }},
    "readiness_level": "High/Medium/Low",
    "recommendations": ["List of specific recommendations"],
    "data_insights": "Analysis of the provided health data patterns"
}}

Focus on actionable insights from the provided health metrics.
"""
                }
            ],
            # temperature parameter removed - o3 only supports default value of 1
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON response
        try:
            analysis_data = json.loads(content)
            analysis_data["model_used"] = "o3"
            analysis_data["analysis_type"] = "comprehensive_behavior"
            return analysis_data
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return {
                "behavioral_signature": {
                    "signature": "Health Data Analysis Complete",
                    "confidence": 0.85
                },
                "sophistication_assessment": {
                    "score": 75,
                    "category": "Intermediate",
                    "justification": "Analysis based on comprehensive health data"
                },
                "analysis_content": content,
                "model_used": "o3",
                "analysis_type": "comprehensive_behavior"
            }
            
    except Exception as e:
        print(f"Error in o3 behavior analysis: {e}")
        return {
            "error": str(e),
            "model_used": "o3 - fallback",
            "behavioral_signature": {"signature": "Analysis Error", "confidence": 0.5}
        }

async def run_circadian_analysis_gpt4o(system_prompt: str, user_context: str) -> dict:
    """Run circadian rhythm analysis using GPT-4o model with readiness assessment"""
    try:
        client = openai.AsyncOpenAI()

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\nYou are an expert circadian rhythm and readiness analyst. Analyze sleep-wake patterns, energy fluctuations, optimal timing for activities, AND current readiness/recovery status based on biomarker data."
                },
                {
                    "role": "user",
                    "content": f"""
{user_context}

Analyze the circadian rhythm patterns AND readiness status from the biomarker data.

REQUIRED OUTPUT (JSON format):

1. READINESS ASSESSMENT:
   - current_mode: "Performance" | "Productive" | "Recovery"
     * Performance (High readiness, HRV optimal, recovery >75%%): Intense activities, peak output
     * Productive (Medium readiness, stable metrics, recovery 50-75%%): Moderate building activities
     * Recovery (Low readiness, HRV low, recovery <50%%): Gentle, restorative activities
   - confidence: 0.0-1.0 (confidence based on data quality)
   - supporting_biomarkers: Key metrics that support this assessment (HRV, sleep quality, recovery score, readiness score)
   - recommendation: Brief explanation of what this mode means for today's activities

2. CHRONOTYPE ASSESSMENT:
   - primary_chronotype: Type (Early Bird, Intermediate, Night Owl)
   - confidence_score: 0.0-1.0
   - supporting_evidence: Data supporting this assessment
   - individual_variations: User-specific patterns

3. ENERGY WINDOWS:
   Provide time windows for energy levels:
   - peak_energy_window: When energy is highest (80-100) - Format: "HH:MM AM/PM - HH:MM AM/PM"
   - maintenance_energy_window: Moderate energy periods (50-75)
   - low_energy_window: Recovery/low energy periods (<50)

   You can specify multiple windows using "and":
   Example: "8:00 AM - 10:00 AM and 3:00 PM - 5:00 PM"

4. SCHEDULE RECOMMENDATIONS:
   - optimal_wake_time: Best time range to wake up (e.g., "6:30 AM - 7:30 AM")
   - optimal_sleep_time: Best time range to sleep (e.g., "10:00 PM - 11:00 PM")
   - workout_timing: Best time for physical activity

5. BIOMARKER INSIGHTS:
   - key_patterns: Important patterns in the data
   - areas_for_improvement: What can be optimized
   - biomarker_trends: Trends over time

Provide structured JSON output with ALL sections: readiness_assessment, chronotype_assessment, energy_zone_analysis, schedule_recommendations, and biomarker_insights.
                """
                }
            ],
            temperature=0.2,
            max_tokens=3500,  # Increased for readiness assessment
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        # Parse JSON response
        try:
            analysis_data = json.loads(content)
            analysis_data["model_used"] = "gpt-4o"
            analysis_data["analysis_type"] = "circadian_rhythm"
            analysis_data["analysis_timestamp"] = datetime.now().isoformat()

            # Add mode_description for consistency with behavior analysis
            if "readiness_assessment" in analysis_data:
                mode = analysis_data["readiness_assessment"].get("current_mode", "Productive")
                mode_mapping = {
                    'Recovery': 'recovery mode (gentle, restorative activities with reduced intensity)',
                    'Productive': 'productive mode (moderate, building activities with steady progress)',
                    'Performance': 'performance mode (intense, optimization activities with peak output)'
                }
                analysis_data["readiness_assessment"]["mode_description"] = mode_mapping.get(mode, 'balanced activities')

            return analysis_data
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in circadian analysis: {e}")
            return {
                "readiness_assessment": {
                    "current_mode": "Productive",
                    "confidence": 0.5,
                    "supporting_biomarkers": {},
                    "recommendation": "Insufficient data for detailed readiness assessment",
                    "mode_description": "productive mode (moderate, building activities with steady progress)"
                },
                "chronotype_assessment": {
                    "primary_chronotype": "Intermediate",
                    "confidence_score": 0.7,
                    "supporting_evidence": {"data_quality": "limited"}
                },
                "energy_zone_analysis": {
                    "peak_energy_window": "8:00 AM - 10:00 AM",
                    "maintenance_energy_window": "2:00 PM - 4:00 PM",
                    "low_energy_window": "4:00 PM - 6:00 PM"
                },
                "schedule_recommendations": {
                    "optimal_wake_time": "6:30 AM - 7:30 AM",
                    "optimal_sleep_time": "10:00 PM - 11:00 PM",
                    "workout_timing": "Morning or early afternoon"
                },
                "biomarker_insights": {
                    "key_patterns": {},
                    "areas_for_improvement": {},
                    "biomarker_trends": {}
                },
                "model_used": "gpt-4o",
                "analysis_type": "circadian_rhythm"
            }

    except Exception as e:
        logger.error(f"Error in GPT-4o circadian analysis: {e}")
        return {
            "error": str(e),
            "model_used": "gpt-4o - fallback",
            "readiness_assessment": {
                "current_mode": "Productive",
                "confidence": 0.3,
                "supporting_biomarkers": {},
                "recommendation": "Error during analysis",
                "mode_description": "productive mode (moderate, building activities with steady progress)"
            },
            "chronotype_assessment": {"primary_chronotype": "unknown", "confidence_score": 0.3}
        }


def _generate_generous_baseline_energy_timeline(chronotype: str = "moderate", archetype: str = "Foundation Builder") -> dict:
    """
    Generate a generous, motivating energy timeline when data is insufficient.

    Shows:
    - 2 clear peak periods (morning + afternoon)
    - Productive windows for most of waking hours
    - Only recovery during sleep

    This creates a motivating baseline that users can live up to.

    Args:
        chronotype: User's chronotype (default: "moderate")
        archetype: User's archetype (default: "Foundation Builder")

    Returns:
        dict with energy_timeline array, summary, and metadata
    """
    timeline = []

    for slot_index in range(96):  # 24 hours * 4 (15-min slots)
        time_minutes = slot_index * 15
        hour = time_minutes // 60
        minute = time_minutes % 60
        time_str = f"{hour:02d}:{minute:02d}"

        # GENEROUS ENERGY ASSIGNMENT
        if 7 <= hour < 10:  # Morning Peak (07:00-10:00)
            zone = "peak"
            energy = 75 + (slot_index % 4) * 2  # 75-81 (varying within peak range)

        elif 10 <= hour < 13:  # Productive Morning (10:00-13:00)
            zone = "productive"
            energy = 65 + (slot_index % 4)  # 65-68

        elif 13 <= hour < 14 or (hour == 14 and (slot_index % 4) < 2):  # Post-lunch dip (13:00-14:30)
            zone = "maintenance"
            energy = 52 + (slot_index % 4)  # 52-55

        elif (hour == 14 and (slot_index % 4) >= 2) or 15 <= hour < 17:  # Afternoon Peak (14:30-17:00)
            zone = "productive"
            energy = 68 + (slot_index % 4)  # 68-71

        elif 17 <= hour < 21:  # Evening Maintenance (17:00-21:00)
            zone = "maintenance"
            energy = 50 - ((hour - 17) * 2)  # 50 declining to 42

        elif 21 <= hour < 22:  # Sleep Prep (21:00-22:00)
            zone = "recovery"
            energy = 38 - (slot_index % 4) * 2  # 38 declining to 32

        else:  # Sleep Time (22:00-07:00)
            zone = "recovery"
            energy = 25 + (slot_index % 4)  # 25-28

        timeline.append({
            "time": time_str,
            "zone": zone,
            "slot_index": slot_index,
            "energy_level": energy
        })

    # Calculate summary statistics
    peak_slots = [s for s in timeline if s['zone'] == 'peak']
    productive_slots = [s for s in timeline if s['zone'] == 'productive']
    maintenance_slots = [s for s in timeline if s['zone'] == 'maintenance']
    recovery_slots = [s for s in timeline if s['zone'] == 'recovery']

    # Find continuous periods
    def find_continuous_periods(slots: list) -> list:
        """Find continuous time periods from slots"""
        if not slots:
            return []
        periods = []
        start_time = slots[0]['time']
        prev_idx = slots[0]['slot_index']

        for i in range(1, len(slots)):
            if slots[i]['slot_index'] != prev_idx + 1:
                # Gap found - end previous period
                periods.append(f"{start_time}-{slots[i-1]['time']}")
                start_time = slots[i]['time']
            prev_idx = slots[i]['slot_index']

        # Add final period
        periods.append(f"{start_time}-{slots[-1]['time']}")
        return periods

    summary = {
        "peak_energy_periods": find_continuous_periods(peak_slots),
        "productive_periods": find_continuous_periods(productive_slots),
        "maintenance_periods": find_continuous_periods(maintenance_slots),
        "recovery_periods": find_continuous_periods(recovery_slots),
        "total_peak_minutes": len(peak_slots) * 15,
        "total_productive_minutes": len(productive_slots) * 15,
        "total_maintenance_minutes": len(maintenance_slots) * 15,
        "total_recovery_minutes": len(recovery_slots) * 15
    }

    timeline_metadata = {
        "generation_type": "generous_baseline",
        "data_quality": "insufficient",
        "baseline_reasoning": "Insufficient data - using optimistic motivating baseline",
        "archetype": archetype,
        "chronotype": chronotype,
        "note": "This generous baseline will adjust based on your actual performance data"
    }

    return {
        "energy_timeline": timeline,
        "summary": summary,
        "timeline_metadata": timeline_metadata
    }


def _assess_circadian_data_quality(circadian_analysis: dict) -> str:
    """
    Assess the quality of circadian analysis data to determine if generous baseline is needed.

    PRIORITY: Trust AI's own data quality assessment FIRST, then validate with other factors.

    Returns:
        "insufficient" - Use generous baseline
        "moderate" - Use generous baseline with minor adjustments
        "good" - Use data-driven with generous bias
        "excellent" - Use full data-driven analysis
    """
    try:
        # PRIORITY 1: Check AI's own assessment of data quality
        metadata = circadian_analysis.get('analysis_metadata', {})
        ai_data_quality = metadata.get('data_quality', 'insufficient')

        # If AI says insufficient, trust it and use generous baseline
        if ai_data_quality == 'insufficient':
            logger.info("[CIRCADIAN_GENEROUS] AI assessed data as insufficient - using generous baseline")
            return "insufficient"

        # If AI says limited, be moderately generous
        if ai_data_quality == 'limited':
            logger.info("[CIRCADIAN_GENEROUS] AI assessed data as limited - using generous defaults")
            return "moderate"

        # PRIORITY 2: Validate AI's "good" or "excellent" assessment with actual data
        # Check energy zone analysis
        energy_zones = circadian_analysis.get('energy_zone_analysis', {})
        peak_windows = energy_zones.get('peak_windows', [])
        productive_windows = energy_zones.get('productive_windows', [])

        # Check biomarker insights
        biomarker_insights = circadian_analysis.get('biomarker_insights', {})
        circadian_score = biomarker_insights.get('circadian_health_score', 0)

        # Check chronotype assessment
        chronotype = circadian_analysis.get('chronotype_assessment', {})
        confidence = chronotype.get('confidence_score', 0.0)

        # Assess based on multiple factors
        has_peak_windows = len(peak_windows) > 0
        has_productive_windows = len(productive_windows) > 0
        has_good_confidence = confidence >= 0.7
        has_circadian_score = circadian_score > 60  # Require meaningful score

        # Count quality indicators
        quality_indicators = sum([
            has_peak_windows,
            has_productive_windows,
            has_good_confidence,
            has_circadian_score,
            ai_data_quality in ["good", "excellent"]
        ])

        if quality_indicators >= 4:
            logger.info("[CIRCADIAN_GENEROUS] Excellent data quality - using data-driven analysis")
            return "excellent"
        elif quality_indicators >= 3:
            logger.info("[CIRCADIAN_GENEROUS] Good data quality - using data-driven with generous bias")
            return "good"
        elif quality_indicators >= 1:
            logger.info("[CIRCADIAN_GENEROUS] Moderate data quality - using generous defaults")
            return "moderate"
        else:
            logger.info("[CIRCADIAN_GENEROUS] Insufficient validation - using generous baseline")
            return "insufficient"

    except Exception as e:
        logger.warning(f"Error assessing circadian data quality: {e}")
        return "insufficient"


def _generate_energy_timeline_from_analysis(circadian_analysis: dict) -> dict:
    """
    Generate 96-slot energy timeline with interpolation from GPT-4o analysis

    NEW: Uses generous baseline when data is insufficient to provide motivating energy zones.

    Args:
        circadian_analysis: Raw GPT-4o output with time windows

    Returns:
        dict with energy_timeline array, summary, and metadata
    """
    # Assess data quality to determine if generous baseline is needed
    data_quality = _assess_circadian_data_quality(circadian_analysis)

    # Get archetype and chronotype for baseline generation
    archetype = circadian_analysis.get('schedule_recommendations', {}).get('archetype_customization', {}).get('archetype', 'Foundation Builder')
    chronotype = circadian_analysis.get('chronotype_assessment', {}).get('primary_type', 'moderate')

    logger.info(f"[CIRCADIAN_GENEROUS] Data quality: {data_quality}, Archetype: {archetype}, Chronotype: {chronotype}")

    # Use generous baseline if data is insufficient
    if data_quality == "insufficient":
        logger.info("[CIRCADIAN_GENEROUS] Using generous baseline - insufficient data for accurate analysis")
        return _generate_generous_baseline_energy_timeline(chronotype, archetype)

    # If moderate data quality, we'll use the data-driven approach but with generous defaults
    # Continue with existing logic below for good/excellent data quality

    # Energy zone thresholds
    PEAK_THRESHOLD = 75
    MAINTENANCE_THRESHOLD = 50

    # Default energy levels for undefined periods (UPDATED to be more generous)
    if data_quality == "moderate":
        # More generous defaults for moderate data quality
        DEFAULT_EARLY_MORNING = 35  # 00:00-06:00 (slightly higher)
        DEFAULT_LATE_NIGHT = 30     # 22:00-24:00 (slightly higher)
        DEFAULT_UNSPECIFIED = 55    # Any gaps (productive instead of maintenance)
        logger.info("[CIRCADIAN_GENEROUS] Using generous defaults for moderate data quality")
    else:
        # Standard defaults for good/excellent data quality
        DEFAULT_EARLY_MORNING = 30  # 00:00-06:00
        DEFAULT_LATE_NIGHT = 25     # 22:00-24:00
        DEFAULT_UNSPECIFIED = 40    # Any gaps

    # Extract energy windows from GPT-4o analysis
    energy_zones = circadian_analysis.get('energy_zone_analysis', {})
    schedule_recs = circadian_analysis.get('schedule_recommendations', {})

    def parse_time_window(window_str: str) -> List[Tuple[int, int]]:
        """
        Parse time window string to list of (start_minutes, end_minutes)
        Handles "and" conjunctions: "8:00 AM - 10:00 AM and 2:00 PM - 4:00 PM"
        """
        if not window_str or not isinstance(window_str, str):
            return []

        # Split by "and" to handle multiple ranges
        ranges = []
        parts = window_str.split(' and ')

        for part in parts:
            # Parse "HH:MM AM/PM - HH:MM AM/PM"
            match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)\s*-\s*(\d{1,2}):(\d{2})\s*(AM|PM)', part.strip())
            if match:
                start_hour, start_min, start_period, end_hour, end_min, end_period = match.groups()

                # Convert to 24-hour format
                start_hour = int(start_hour)
                end_hour = int(end_hour)

                if start_period == 'PM' and start_hour != 12:
                    start_hour += 12
                elif start_period == 'AM' and start_hour == 12:
                    start_hour = 0

                if end_period == 'PM' and end_hour != 12:
                    end_hour += 12
                elif end_period == 'AM' and end_hour == 12:
                    end_hour = 0

                start_minutes = start_hour * 60 + int(start_min)
                end_minutes = end_hour * 60 + int(end_min)

                ranges.append((start_minutes, end_minutes))

        return ranges

    # Parse all energy windows
    peak_ranges = []
    maintenance_ranges = []
    low_ranges = []

    peak_window = energy_zones.get('peak_energy_window', '')
    if peak_window:
        peak_ranges = parse_time_window(peak_window)

    maintenance_window = energy_zones.get('maintenance_energy_window', '')
    if maintenance_window:
        maintenance_ranges = parse_time_window(maintenance_window)

    low_window = energy_zones.get('low_energy_window', '')
    if low_window:
        low_ranges = parse_time_window(low_window)

    # Create energy blocks with levels
    energy_blocks = []

    # Add peak blocks (energy = 85)
    for start, end in peak_ranges:
        energy_blocks.append({
            'start': start,
            'end': end,
            'energy': 85,
            'zone': 'peak'
        })

    # Add maintenance blocks (energy = 60)
    for start, end in maintenance_ranges:
        energy_blocks.append({
            'start': start,
            'end': end,
            'energy': 60,
            'zone': 'maintenance'
        })

    # Add low energy blocks (energy = 35)
    for start, end in low_ranges:
        energy_blocks.append({
            'start': start,
            'end': end,
            'energy': 35,
            'zone': 'recovery'
        })

    # Sort blocks by start time
    energy_blocks.sort(key=lambda x: x['start'])

    def get_energy_for_slot(slot_minutes: int) -> Tuple[int, str]:
        """
        Calculate energy level and zone for a given time slot
        Handles interpolation between blocks
        """
        # Check if slot is inside any defined block
        for block in energy_blocks:
            if block['start'] <= slot_minutes < block['end']:
                return block['energy'], block['zone']

        # Slot is in a gap - find surrounding blocks for interpolation
        prev_block = None
        next_block = None

        for block in energy_blocks:
            if block['end'] <= slot_minutes:
                prev_block = block  # Most recent block before gap
            elif block['start'] > slot_minutes:
                next_block = block  # Next block after gap
                break

        # Interpolate between blocks
        if prev_block and next_block:
            gap_duration = next_block['start'] - prev_block['end']
            position_in_gap = slot_minutes - prev_block['end']
            progress = position_in_gap / gap_duration  # 0.0 to 1.0

            energy_delta = next_block['energy'] - prev_block['energy']
            interpolated_energy = prev_block['energy'] + (energy_delta * progress)

            # Determine zone based on interpolated energy
            if interpolated_energy >= PEAK_THRESHOLD:
                zone = 'peak'
            elif interpolated_energy >= MAINTENANCE_THRESHOLD:
                zone = 'maintenance'
            else:
                zone = 'recovery'

            return round(interpolated_energy), zone

        # No surrounding blocks - use defaults based on time of day
        hour = slot_minutes // 60

        if hour < 6:  # Early morning (00:00-06:00)
            return DEFAULT_EARLY_MORNING, 'recovery'
        elif hour >= 22:  # Late night (22:00-24:00)
            return DEFAULT_LATE_NIGHT, 'recovery'
        else:  # Daytime unspecified
            return DEFAULT_UNSPECIFIED, 'maintenance'

    # Generate all 96 slots
    timeline = []
    for slot_index in range(96):
        slot_minutes = slot_index * 15
        hour = slot_minutes // 60
        minute = slot_minutes % 60

        time_str = f"{hour:02d}:{minute:02d}"
        energy_level, zone = get_energy_for_slot(slot_minutes)

        timeline.append({
            "time": time_str,
            "energy_level": energy_level,
            "slot_index": slot_index,
            "zone": zone
        })

    # Generate human-readable summary
    def find_continuous_periods(timeline_data: list, zone_filter: str) -> List[str]:
        """Find continuous periods of a specific zone"""
        periods = []
        start_idx = None

        for i, slot in enumerate(timeline_data):
            if slot['zone'] == zone_filter:
                if start_idx is None:
                    start_idx = i
            else:
                if start_idx is not None:
                    # Period ended
                    start_time = timeline_data[start_idx]['time']
                    end_time = timeline_data[i-1]['time']
                    periods.append(f"{start_time}-{end_time}")
                    start_idx = None

        # Handle case where period extends to end of day
        if start_idx is not None:
            start_time = timeline_data[start_idx]['time']
            end_time = timeline_data[-1]['time']
            periods.append(f"{start_time}-{end_time}")

        return periods

    peak_periods = find_continuous_periods(timeline, 'peak')
    maintenance_periods = find_continuous_periods(timeline, 'maintenance')
    low_periods = find_continuous_periods(timeline, 'recovery')

    # Calculate total minutes per zone
    total_peak = sum(1 for slot in timeline if slot['zone'] == 'peak') * 15
    total_maintenance = sum(1 for slot in timeline if slot['zone'] == 'maintenance') * 15
    total_recovery = sum(1 for slot in timeline if slot['zone'] == 'recovery') * 15

    # Find optimal wake/sleep windows from timeline
    # Wake: First sustained rise above 50
    wake_window = None
    for i in range(len(timeline) - 3):
        if all(timeline[i+j]['energy_level'] > 50 for j in range(3)):
            wake_start = timeline[i]['time']
            wake_end = timeline[min(i+4, 95)]['time']
            wake_window = f"{wake_start}-{wake_end}"
            break

    # Sleep: First sustained drop below 35 (starting from 15:00 onwards)
    sleep_window = None
    for i in range(60, len(timeline) - 3):
        if all(timeline[i+j]['energy_level'] < 35 for j in range(3)):
            sleep_start = timeline[max(0, i-4)]['time']
            sleep_end = timeline[i]['time']
            sleep_window = f"{sleep_start}-{sleep_end}"
            break

    summary = {
        "optimal_wake_window": wake_window or "06:30-07:30",
        "peak_energy_periods": peak_periods,
        "maintenance_periods": maintenance_periods,
        "low_energy_periods": low_periods,
        "optimal_sleep_window": sleep_window or "22:00-23:00",
        "total_peak_minutes": total_peak,
        "total_maintenance_minutes": total_maintenance,
        "total_recovery_minutes": total_recovery
    }

    metadata = {
        "total_slots": 96,
        "slot_duration_minutes": 15,
        "interpolation_method": "linear",
        "default_energy_levels": {
            "early_morning": DEFAULT_EARLY_MORNING,
            "late_night": DEFAULT_LATE_NIGHT,
            "unspecified_periods": DEFAULT_UNSPECIFIED
        },
        "zone_thresholds": {
            "peak": PEAK_THRESHOLD,
            "maintenance": MAINTENANCE_THRESHOLD,
            "recovery": MAINTENANCE_THRESHOLD
        }
    }

    return {
        "energy_timeline": timeline,
        "summary": summary,
        "timeline_metadata": metadata
    }

async def run_memory_enhanced_behavior_analysis(user_id: str, archetype: str) -> dict:
    """
    Memory-Enhanced Behavior Analysis - Includes all features from /api/analyze
    Features:
    - Memory context preparation using MemoryIntegrationService
    - Memory-enhanced prompt generation
    - Storing analysis results in memory tables
    - Updating user memory profile
    - Complete logging of analysis data
    """
    try:
        # print(f"[ANALYSIS] [MEMORY_ENHANCED] Starting memory-enhanced behavior analysis for {user_id[:8]}...")  # Commented for error-only mode
        
        # Import memory integration service
        from services.ai_context_integration_service import AIContextIntegrationService
        
        # Initialize memory integration service
        memory_service = AIContextIntegrationService()
        
        # Step 1: Prepare memory-enhanced context
        # # Production: Verbose print removed  # Commented to reduce noise
        memory_context_obj = await memory_service.prepare_memory_enhanced_context(user_id, None, archetype)

        # Convert ContextEnhancedContext object to dict with relevant memory fields
        memory_context = {
            "ai_context_summary": memory_context_obj.ai_context_summary,
            "behavior_analysis_history": memory_context_obj.behavior_analysis_history,
            "circadian_analysis_history": memory_context_obj.circadian_analysis_history,
            "engagement_insights": memory_context_obj.engagement_insights,
            "analysis_mode": memory_context_obj.analysis_mode,
            "days_to_fetch": memory_context_obj.days_to_fetch
        }

        # Step 2: Get user data for analysis
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt

        user_service = UserDataService()

        # Get user data (service handles days internally based on analysis history)
        user_context, data_quality = await user_service.get_analysis_data(user_id)
        
        # Fix datetime bug - safely handle data_quality attribute access
        if hasattr(data_quality, 'value'):
            data_quality_value = data_quality.value
        else:
            data_quality_value = str(data_quality) if data_quality else "unknown"
        
        # # Production: Verbose print removed  # Commented to reduce noise
        # # Production: Verbose print removed  # Commented for error-only mode
        
        # Step 3: Get and enhance system prompt with memory
        system_prompt = get_system_prompt("behavior_analysis")
        enhanced_prompt = await memory_service.enhance_agent_prompt(
            system_prompt, memory_context, "behavior_analysis"
        )
        
        # print(f"[ANALYSIS] [MEMORY_ENHANCED] Enhanced prompt with memory context (+{len(enhanced_prompt) - len(system_prompt)} chars)")  # Commented for error-only mode
        
        # Step 4: Prepare behavior agent data with memory context
        user_context_summary = await format_health_data_for_ai(user_context)
        
        
        
        behavior_data = await prepare_behavior_agent_data(user_context, user_context_summary)
        
        # Step 5: Run behavior analysis with memory-enhanced prompt
        analysis_result = await run_behavior_analysis_o3(enhanced_prompt, user_context_summary)
        
        # Step 6: Store analysis insights using same method as /api/analyze
        # print(f"[CACHE] [MEMORY_ENHANCED] Storing analysis insights like /api/analyze...")  # Commented for error-only mode
        insights_stored = False
        try:
            # Use the same storage method as /api/analyze (line 1523)
            await memory_service.store_analysis_insights(user_id, "behavior_analysis", analysis_result, archetype)
            insights_stored = True
        # # Production: Verbose print removed  # Commented to reduce noise
        except Exception as e:
            pass
        
        # Step 8: Log complete analysis data (input/output logging)
        await log_complete_analysis(
            "behavior_analysis", user_id, archetype, 
            behavior_data, analysis_result, memory_context,
            analysis_source="shared"
        )
        
        # Step 9: Cleanup memory service
        await memory_service.cleanup()
        
        # Add memory enhancement metadata to result
        analysis_result.update({
            "memory_enhanced": True,
            "analysis_mode": memory_context.analysis_mode,
            "days_fetched": memory_context.days_to_fetch,
            "memory_focus_areas": memory_context.personalized_focus_areas,
            "insights_stored": insights_stored
        })
        
        # # Production: Verbose print removed  # Commented to reduce noise
        return analysis_result
        
    except Exception as e:
        print(f"[ERROR] [MEMORY_ENHANCED] Error in memory-enhanced behavior analysis: {e}")
        # No fallback to standalone - all analysis must go through OnDemandAnalysisService
        raise Exception(f"Memory-enhanced behavior analysis failed for user {user_id}: {e}")

async def get_or_create_shared_behavior_analysis(user_id: str, archetype: str, force_refresh: bool = False, analysis_number: int = None) -> dict:
    """
    MVP Shared Behavior Analysis - Extracted from /api/analyze (lines 1257-1386)
    Used by routine/nutrition endpoints to avoid duplicate analysis
    Applies 50-item threshold logic from OnDemandAnalysisService
    
    RACE CONDITION FIX: Uses global coordination to prevent duplicate analyses
    """
    from services.request_deduplication_service import enhanced_deduplicator
    
    try:
        # COORDINATION FIX: Check if analysis is in progress or cached
        should_process, cached_result = await enhanced_deduplicator.coordinate_request(
            user_id, archetype, "behavior_analysis"
        )
        
        if not should_process and cached_result:
            pass
            return cached_result

        # Step 1: Check if fresh analysis needed (50-item threshold logic WITH ARCHETYPE)
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        ondemand_service = await get_ondemand_service()
        decision, metadata = await ondemand_service.should_run_analysis(
            user_id,
            force_refresh,
            archetype,
            analysis_type="behavior_analysis"  # Track behavior analysis separately
        )
        
        # Enhanced debugging for threshold issues
        decision_str = decision.value if hasattr(decision, 'value') else str(decision)
        new_data = metadata.get('new_data_points', 0)
        threshold = metadata.get('threshold_used', 50)
        
        # # Production: Verbose print removed  # Commented for error-only mode
        # # Production: Verbose print removed  # Commented to reduce noise
        # print(f"   📈 New Data Points: {new_data}")  # Commented for error-only mode
        # # Production: Verbose print removed  # Commented for error-only mode
        # print(f"   [CACHE] Memory Quality: {metadata.get('memory_quality', 'unknown')}")  # Commented for error-only mode
        # print(f"   ⏰ Hours Since Last: {metadata.get('hours_since_analysis', 0):.1f}")  # Commented for error-only mode
        # # Production: Verbose print removed  # Commented for error-only mode
        
        logger.debug(f"[SHARED_ANALYSIS] {user_id[:8]}... Decision: {decision_str}, Data: {new_data}/{threshold}")
        
        # Step 2: Use cached if sufficient (only for MEMORY_ENHANCED_CACHE decision)
        if decision == AnalysisDecision.MEMORY_ENHANCED_CACHE:
            # print(f"[CACHE] [THRESHOLD_DEBUG] Decision is MEMORY_ENHANCED_CACHE - fetching cached analysis...")  # Commented for error-only mode
            # Use OnDemandAnalysisService's archetype-aware cache retrieval
            cached_analysis = await ondemand_service.get_cached_behavior_analysis(user_id, archetype)
            if cached_analysis:
        # # Production: Verbose print removed  # Commented to reduce noise
                print(f"   [STORAGE] Cache contains: {len(str(cached_analysis))} characters")
                logger.debug(f"[SHARED_ANALYSIS] {user_id[:8]}... Using cached analysis")
                # Complete coordination with cached result
                enhanced_deduplicator.complete_request(user_id, archetype, "behavior_analysis", cached_analysis)
                return cached_analysis
            else:
                print(f"[ERROR] [THRESHOLD_DEBUG] No cached analysis found - falling back to fresh")
                logger.warning(f"[SHARED_ANALYSIS] {user_id[:8]}... Cache failed, using fresh")
        
        # Step 3: Run fresh analysis for all other decisions
        logger.debug(f"[SHARED_ANALYSIS] {user_id[:8]}... Running fresh analysis")
        fresh_result = await run_fresh_behavior_analysis_like_api_analyze(user_id, archetype, metadata, analysis_number)
        logger.info(f"[SHARED_ANALYSIS] {user_id[:8]}... Fresh analysis completed")
        
        # Complete coordination with fresh result
        enhanced_deduplicator.complete_request(user_id, archetype, "behavior_analysis", fresh_result)
        return fresh_result
        
    except Exception as e:
        logger.error(f"[SHARED_ANALYSIS] {user_id[:8]}... Error: {e}")
        # Complete coordination with error
        enhanced_deduplicator.complete_request(user_id, archetype, "behavior_analysis", {"error": str(e)})
        # No fallback - all analysis must go through OnDemandAnalysisService
        raise Exception(f"Shared behavior analysis failed for user {user_id}: {e}")


async def get_cached_behavior_analysis_from_memory(user_id: str) -> dict:
    """Retrieve cached behavior analysis from memory system"""
    try:
        # HolisticMemoryService removed - functionality replaced by AIContextIntegrationService
        memory_service = HolisticMemoryService()
        
        # Get latest behavior analysis specifically from memory
        analysis_results = await memory_service.get_analysis_history(user_id, analysis_type="behavior_analysis", limit=1)
        if analysis_results:
            latest = analysis_results[0]
            if latest.analysis_type in ["behavior_analysis"]:
                analysis_result = latest.analysis_result
                
                # The database stores behavior analysis directly as JSON
                if isinstance(analysis_result, dict):
                    # Check if it has behavior analysis fields (direct format)
                    if "behavioral_signature" in analysis_result or "sophistication_assessment" in analysis_result:
                        return analysis_result
                    # Check if it's nested under "behavior_analysis"
                    elif "behavior_analysis" in analysis_result:
                        return analysis_result["behavior_analysis"]
                
                return analysis_result
        
        await memory_service.cleanup()
        return None
        
    except Exception as e:
        logger.debug(f"[SHARED_ANALYSIS] Cache retrieval failed: {e}")
        return None

async def get_or_create_shared_circadian_analysis(user_id: str, archetype: str, force_refresh: bool = False, analysis_number: int = None) -> dict:
    """
    Shared Circadian Analysis - Following same pattern as behavior analysis
    Used by circadian endpoints and potential routine/nutrition integration
    Applies 50-item threshold logic from OnDemandAnalysisService

    RACE CONDITION FIX: Uses global coordination to prevent duplicate analyses
    """
    from services.request_deduplication_service import enhanced_deduplicator

    try:
        # COORDINATION FIX: Check if analysis is in progress or cached
        should_process, cached_result = await enhanced_deduplicator.coordinate_request(
            user_id, archetype, "circadian_analysis"
        )

        if not should_process and cached_result:
            pass
            return cached_result

        # FRESH ANALYSIS: Proceed with threshold check via OnDemandAnalysisService
        pass
        pass
        print(f"   [ANALYSIS] [MEMORY] Integrating 4-layer memory system for personalized analysis")

        # Use OnDemandAnalysisService to get proper metadata
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        ondemand_service = await get_ondemand_service()
        decision, ondemand_metadata = await ondemand_service.should_run_analysis(
            user_id,
            force_refresh=force_refresh,
            requested_archetype=archetype,
            analysis_type="circadian_analysis"  # Track circadian separately
        )

        # Check if we should skip (threshold not met)
        if decision == AnalysisDecision.MEMORY_ENHANCED_CACHE and not force_refresh:
            logger.info(f"⏭️  [CIRCADIAN_THRESHOLD] Skipping circadian analysis - threshold not met for {user_id[:8]}... + {archetype}")
            logger.info(f"   Reason: {ondemand_metadata.get('reason', 'insufficient new data')}")
            logger.info(f"   New data points: {ondemand_metadata.get('new_data_points', 0)}, Threshold: {ondemand_metadata.get('threshold_used', 50)}")
            return {"status": "skipped", "reason": "threshold_not_met", "circadian_analysis": {}, "metadata": ondemand_metadata}

        # Run memory-enhanced circadian analysis
        circadian_result = await run_memory_enhanced_circadian_analysis(user_id, archetype)

        # Note: Analysis completion is tracked via database storage and coordination service
        # await ondemand_service.mark_analysis_complete(user_id)  # Method not available

        # Result stored in database - no additional caching needed

        pass
        return circadian_result

    except Exception as e:
        print(f"[ERROR] [SHARED_CIRCADIAN] Error in shared circadian analysis: {e}")
        enhanced_deduplicator.mark_request_complete(user_id, archetype, "circadian_analysis")
        return {"status": "error", "error": str(e), "circadian_analysis": {}}


async def run_fresh_behavior_analysis_like_api_analyze(user_id: str, archetype: str, ondemand_metadata: dict = None, analysis_number: int = None) -> dict:
    """
    Run fresh behavior analysis using EXACT same flow as /api/analyze
    Extracted from /api/analyze lines 1257-1386 - minimal changes, maximum reuse
    
    Args:
        user_id: User identifier
        archetype: User archetype
        ondemand_metadata: Metadata from OnDemandAnalysisService containing analysis_mode and days_to_fetch
    """
    try:
        # Imports for behavior analysis
        from services.ai_context_integration_service import AIContextIntegrationService
        from services.user_data_service import UserDataService
        from services.simple_analysis_tracker import SimpleAnalysisTracker as AnalysisTracker
        from shared_libs.utils.system_prompts import get_system_prompt

        # Service initialization
        user_service = UserDataService()
        analysis_tracker = AnalysisTracker()
        memory_service = AIContextIntegrationService()
        
        try:
            # Use OnDemandAnalysisService metadata for memory context preparation
            memory_context_obj = await memory_service.prepare_memory_enhanced_context(user_id, ondemand_metadata, archetype)

            # Convert ContextEnhancedContext object to dict with relevant memory fields
            memory_context = {
                "ai_context_summary": memory_context_obj.ai_context_summary,
                "behavior_analysis_history": memory_context_obj.behavior_analysis_history,
                "circadian_analysis_history": memory_context_obj.circadian_analysis_history,
                "engagement_insights": memory_context_obj.engagement_insights,
                "analysis_mode": memory_context_obj.analysis_mode,
                "days_to_fetch": memory_context_obj.days_to_fetch
            }

            # CRITICAL FIX: Pass locked timestamp to prevent race conditions
            locked_timestamp = ondemand_metadata.get('fixed_timestamp') if ondemand_metadata else None
            if locked_timestamp:
                print(f"[AUTH] [RACE_CONDITION_FIX] Using locked timestamp from OnDemandAnalysisService")
                user_context, latest_data_timestamp = await user_service.get_analysis_data(user_id, locked_timestamp, analysis_number)
            else:
        # # Production: Verbose print removed  # Commented to reduce noise
                user_context, latest_data_timestamp = await user_service.get_analysis_data(user_id, None, analysis_number)

            # Get behavior analysis system prompt
            behavior_prompt = get_system_prompt("behavior_analysis")

            # EXACT same context summary creation as /api/analyze (lines 1324-1348)
            user_context_summary = await create_context_summary_like_api_analyze(user_context, memory_context_obj, archetype, user_id)

            # NEW: Use BehaviorAnalysisService with Sahha direct integration
            # This replaces the old run_behavior_analysis_o3 call
            from services.behavior_analysis_service import get_behavior_analysis_service

            behavior_service = get_behavior_analysis_service()

            # Prepare enhanced context for new service
            # Convert Pydantic model to dict for JSON serialization
            enhanced_context = {
                "user_context": user_context.model_dump() if hasattr(user_context, 'model_dump') else (user_context.dict() if hasattr(user_context, 'dict') else user_context),
                "archetype": archetype,
                "memory_context": memory_context  # Now a dict with behavior/circadian history
            }

            # Call new service with Sahha integration (will use user_id to fetch Sahha data)
            behavior_analysis = await behavior_service.analyze(
                enhanced_context=enhanced_context,
                user_id=user_id,  # Enables Sahha direct fetch
                archetype=archetype  # For watermark tracking
            )

            # OLD: Commented out - kept for reference
            # behavior_agent_data = await prepare_behavior_agent_data(user_context, user_context_summary)
            # behavior_analysis = await run_behavior_analysis_o3(behavior_prompt, user_context_summary)
            
            # EXACT same memory storage as /api/analyze (lines 1525-1531)
            await memory_service.store_analysis_insights(user_id, "behavior_analysis", behavior_analysis, archetype)
            await memory_service.update_user_memory_profile(user_id, behavior_analysis, {}, {})
            
            # NOTE: timestamp update moved to data fetching phase for proper incremental boundaries
            
        # # Production: Verbose print removed  # Commented to reduce noise
            
            # CRITICAL FIX: Include OnDemand metadata in behavior analysis result
            # This allows downstream services to access the locked timestamp
            if ondemand_metadata:
                # Convert any enum values to strings for JSON serialization
                serializable_metadata = {}
                for key, value in ondemand_metadata.items():
                    if hasattr(value, 'value'):  # Check if it's an enum
                        serializable_metadata[key] = value.value
                    else:
                        serializable_metadata[key] = value
                behavior_analysis['_metadata'] = serializable_metadata
                print(f"[AUTH] [RACE_CONDITION_FIX] Added OnDemand metadata to behavior analysis result")
            
            return behavior_analysis
            
        finally:
            # Cleanup services
            await user_service.cleanup()
            await analysis_tracker.cleanup()
            await memory_service.cleanup()
            
    except Exception as e:
        print(f"[ERROR] [SHARED_ANALYSIS] Fresh analysis failed: {e}")
        # No final fallback - all analysis must go through OnDemandAnalysisService
        raise Exception(f"Fresh behavior analysis failed for user {user_id}: {e}")


async def create_context_summary_like_api_analyze(user_context, memory_context, archetype: str, user_id: str) -> str:
    """
    Create context summary exactly like /api/analyze does (lines 1324-1348)
    Minimal extraction - same logic, same format
    """
    try:
        data_quality = user_context.data_quality
        
        # AI Context summary (updated for ContextEnhancedContext)
        memory_summary = ""
        if memory_context.ai_context_summary:
            memory_summary = f"""
AI-ENHANCED CONTEXT:
- Analysis Mode: {memory_context.analysis_mode.upper()}
- AI Context Available: YES
- Personalized Focus Areas: {', '.join(memory_context.personalized_focus_areas) if memory_context.personalized_focus_areas else 'None'}
- Proven Strategies: {len(memory_context.proven_strategies) if memory_context.proven_strategies else 0} strategies identified
- Behavior Analysis History: {len(memory_context.behavior_analysis_history)} previous analyses
- AI Context Summary: {memory_context.ai_context_summary[:200]}..."""
        else:
            if memory_context.analysis_mode == "follow_up":
                memory_summary = f"""
AI-ENHANCED CONTEXT:
- Analysis Mode: FOLLOW-UP (Building context profile)
- Previous Analysis Available: PARTIAL
- Days Since Last Analysis: {memory_context.days_to_fetch}
- Behavior History: {len(memory_context.behavior_analysis_history)} previous analyses"""
            else:
                memory_summary = f"""
AI-ENHANCED CONTEXT:
- Analysis Mode: {memory_context.analysis_mode.upper()} (New user)
- AI Context Available: NO (Building initial context)"""

        # EXACT same context summary format as /api/analyze (lines 1324-1348)
        user_context_summary = f"""
HEALTH ANALYSIS REQUEST - MEMORY-ENHANCED COMPREHENSIVE DATA:
- Profile Reference: {user_id}
- Health Archetype: {archetype}
- Analysis Date: {datetime.now().strftime('%Y-%m-%d')}
- Mode: Memory-Enhanced Health Analysis (Phase 4.1)

{memory_summary}

HEALTH DATA PROFILE:
- Data Quality Level: {data_quality.quality_level} 
- Health Score Samples: {data_quality.scores_count}
- Biomarker Measurements: {data_quality.biomarkers_count}
- Data Coverage: {data_quality.completeness_score:.1%}
- Recent Measurements: {data_quality.has_recent_data}
- Time Period: {user_context.date_range.start_date.strftime('%Y-%m-%d')} to {user_context.date_range.end_date.strftime('%Y-%m-%d')}

HEALTH TRACKING DATA SUMMARY:
{await format_health_data_for_ai(user_context)}

ANALYSIS INSTRUCTIONS: You have comprehensive health tracking data including sleep patterns, activity metrics, and biomarker readings, enhanced with user memory context. Analyze these health indicators to identify behavioral trends and insights that align with the {archetype} framework. Focus on actionable observations from the provided health metrics while considering the user's memory profile and proven strategies.
"""
        return user_context_summary
        
    except Exception as e:
        logger.error(f"[CONTEXT_SUMMARY_ERROR] Failed to create context summary: {e}", exc_info=True)
        print(f"[ERROR] [CONTEXT_SUMMARY_ERROR] {e}")
        # Minimal fallback
        return f"Health analysis for {archetype} user {user_id}"

async def log_data_collection_summary(user_id: str, user_context, engagement_context, memory_context) -> None:
    """Log comprehensive summary of all data being collected for AI analysis"""
    try:
        import json
        from datetime import datetime
        
        # Create a comprehensive data collection summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id[:8] + "...",  # Partially masked for privacy
            "data_collection": {
                "health_scores": {
                    "count": len(user_context.scores),
                    "types": list(set(s.type for s in user_context.scores)),
                    "date_range": f"{user_context.date_range.start_date} to {user_context.date_range.end_date}"
                },
                "biomarkers": {
                    "count": len(user_context.biomarkers),
                    "categories": list(set(b.category for b in user_context.biomarkers[:10]))
                },
                "engagement": {
                    "has_data": bool(engagement_context),
                    "completion_rate": engagement_context.get('engagement_summary', {}).get('completion_rate', 0) if engagement_context else 0,
                    "total_tasks": engagement_context.get('engagement_summary', {}).get('total_planned', 0) if engagement_context else 0,
                    "timing_adherence": engagement_context.get('timing_patterns', {}).get('timing_adherence', 'no_data') if engagement_context else 'no_data'
                },
                "memory": {
                    "mode": memory_context.analysis_mode,
                    "days_fetched": memory_context.days_to_fetch,
                    "has_history": bool(memory_context.analysis_history),
                    "focus_areas": memory_context.personalized_focus_areas[:3] if memory_context.personalized_focus_areas else []
                }
            }
        }
        
        # Log to console
        print(f"\n{'='*60}")
        pass
        print(f"{'='*60}")
        print(json.dumps(summary, indent=2))
        print(f"{'='*60}\n")
        
        # Also save to a log file for detailed review
        log_dir = "logs/data_collection"
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/data_collection_{user_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(log_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"[CACHE] Data collection log saved to: {log_file}")
        
    except Exception as e:
        pass

async def log_complete_analysis(agent_type: str, user_id: str, archetype: str, 
                               input_data: dict, output_data: dict, memory_context, 
                               analysis_source: str = "shared") -> None:
    """Log complete analysis data - supports both shared and standalone analysis"""
    try:
        # Note: Removed complex logging infrastructure to focus on core functionality
        
        # Determine analysis type based on source
        if analysis_source == "shared":
            analysis_type = "shared_" + agent_type
        else:
            analysis_type = "standalone_" + agent_type
        
        # Prepare complete input data
        complete_input = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": analysis_type,
            "user_id": user_id,
            "archetype": archetype,
            "memory_enhanced": True,
            "analysis_mode": memory_context.analysis_mode,
            "days_to_fetch": memory_context.days_to_fetch,
            "personalized_focus_areas": memory_context.personalized_focus_areas,
            "agent_input_data": input_data
        }
        
        # Prepare complete output data  
        complete_output = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": analysis_type,
            "user_id": user_id,
            "archetype": archetype,
            "memory_enhanced": True,
            "analysis_result": output_data
        }
        
        # Note: Analysis logging removed - focus on core functionality
        # Analysis data available in memory system for retrieval
        
        # print(f"[STORAGE] [MEMORY_ENHANCED] Complete analysis stored in memory system")  # Commented for error-only mode
        
    except Exception as e:
        pass

async def run_memory_enhanced_circadian_analysis(user_id: str, archetype: str) -> dict:
    """
    AI Context-Enhanced Circadian Analysis - Uses AIContextIntegrationService
    Features:
    - AI context preparation using AIContextIntegrationService
    - Context-enhanced circadian prompt generation
    - Storing circadian analysis results in holistic_analysis_results table
    - Complete logging of circadian analysis data
    """
    try:

        # Import AI context integration service
        from services.ai_context_integration_service import AIContextIntegrationService

        # Initialize AI context service
        context_service = AIContextIntegrationService()

        # Step 1: Prepare AI context-enhanced analysis context
        memory_context_obj = await context_service.prepare_memory_enhanced_context(user_id, None, archetype)

        # Convert ContextEnhancedContext object to dict with relevant memory fields
        memory_context = {
            "ai_context_summary": memory_context_obj.ai_context_summary,
            "behavior_analysis_history": memory_context_obj.behavior_analysis_history,
            "circadian_analysis_history": memory_context_obj.circadian_analysis_history,
            "engagement_insights": memory_context_obj.engagement_insights,
            "analysis_mode": memory_context_obj.analysis_mode,
            "days_to_fetch": memory_context_obj.days_to_fetch
        }

        # Step 2: Get user data for circadian analysis (need more days for pattern recognition)
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt

        user_service = UserDataService()

        # Get extended user data for circadian pattern analysis
        user_context, data_quality = await user_service.get_analysis_data(user_id)

        # # Production: Verbose print removed  # Commented for error-only mode

        # Step 3: Get and enhance system prompt with AI context
        system_prompt = get_system_prompt("circadian_analysis")  # Will use default if not exists
        enhanced_prompt = await context_service.enhance_agent_prompt(
            system_prompt, memory_context_obj, "circadian_analysis"
        )

        # Step 4: Format user context for AI analysis
        user_context_summary = await format_health_data_for_ai(user_context)

        # Step 5: NEW - Run AI-powered circadian analysis using CircadianAnalysisService with Sahha
        from services.circadian_analysis_service import CircadianAnalysisService

        circadian_service = CircadianAnalysisService()

        # Prepare enhanced context for new service
        # Convert Pydantic model to dict for JSON serialization
        enhanced_context = {
            "user_context": user_context.model_dump() if hasattr(user_context, 'model_dump') else (user_context.dict() if hasattr(user_context, 'dict') else user_context),
            "archetype": archetype,
            "memory_context": memory_context  # Now a dict with behavior/circadian history
        }

        # Call new service with Sahha integration (will use user_id to fetch Sahha data)
        analysis_result = await circadian_service.analyze(
            enhanced_context=enhanced_context,
            user_id=user_id,  # Enables Sahha direct fetch
            archetype=archetype  # For watermark tracking
        )

        # OLD: Commented out - kept for reference
        # analysis_result = await run_circadian_analysis_gpt4o(enhanced_prompt, user_context_summary)

        # Step 5.5: REMOVED - CircadianAnalysisService already generates the complete timeline
        # with zone_color, zone_label, motivation_message, and _ensure_motivating_distribution()
        #
        # The OLD code below was OVERWRITING the improved timeline with a version missing new fields:
        #
        # try:
        #     timeline_data = _generate_energy_timeline_from_analysis(analysis_result)
        #     analysis_result['energy_timeline'] = timeline_data['energy_timeline']
        #     analysis_result['summary'] = timeline_data['summary']
        #     analysis_result['timeline_metadata'] = timeline_data['timeline_metadata']
        #     logger.info(f"Generated {len(timeline_data['energy_timeline'])} energy timeline slots")
        # except Exception as timeline_error:
        #     logger.error(f"Failed to generate energy timeline: {timeline_error}")
        #     analysis_result['energy_timeline'] = []
        #     analysis_result['summary'] = {}
        #     analysis_result['timeline_metadata'] = {}

        logger.info(f"[CIRCADIAN] Using timeline generated by CircadianAnalysisService with {len(analysis_result.get('energy_timeline', []))} slots")

        # Step 6: Store analysis results (now includes timeline) in holistic_analysis_results table
        storage_success = False
        try:
            # Convert data_quality to dict if it's a Pydantic model
            data_quality_dict = data_quality.dict() if hasattr(data_quality, 'dict') else data_quality

            storage_result = await context_service.store_analysis_insights(
                user_id=user_id,
                analysis_type="circadian_analysis",
                analysis_result=analysis_result,  # Now includes energy_timeline
                archetype=archetype
            )

            if storage_result:
                storage_success = True
                logger.info(f"[SUCCESS] [CIRCADIAN_STORAGE] Stored circadian analysis to holistic_analysis_results for {user_id[:8]}... + {archetype}")
            else:
                logger.error(f"[ERROR] [CIRCADIAN_STORAGE] Storage returned False for {user_id[:8]}... + {archetype}")

        except Exception as storage_error:
            logger.error(f"[ERROR] [CIRCADIAN_STORAGE] Exception storing circadian analysis: {storage_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Continue execution - analysis was successful even if storage failed

        # Step 7: Update archetype_analysis_tracking (only if storage succeeded)
        if storage_success:
            try:
                from services.archetype_analysis_tracker import get_archetype_tracker
                tracker = await get_archetype_tracker()

                # Update last analysis timestamp for this user+archetype+analysis_type
                tracking_success = await tracker.update_last_analysis_date(
                    user_id=user_id,
                    archetype=archetype,
                    analysis_date=datetime.now(timezone.utc),
                    analysis_type="circadian_analysis"  # Track circadian separately from behavior
                )

                if tracking_success:
                    logger.info(f"[SUCCESS] [ARCHETYPE_TRACKING] Updated archetype_analysis_tracking for {user_id[:8]}... + {archetype} + circadian_analysis")
                else:
                    logger.warning(f"[WARNING]  [ARCHETYPE_TRACKING] Failed to update tracking (non-critical)")

            except Exception as tracking_error:
                logger.error(f"[ERROR] [ARCHETYPE_TRACKING] Exception updating tracking: {tracking_error}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Non-critical error - continue even if tracking fails
        else:
            logger.warning(f"[WARNING]  [ARCHETYPE_TRACKING] Skipping tracking update - storage failed")

        return analysis_result

    except Exception as e:
        print(f"[ERROR] [CIRCADIAN_ENHANCED] Error in memory-enhanced circadian analysis: {e}")
        # Return the analysis_result if we got that far, otherwise return None
        try:
            if 'analysis_result' in locals() and analysis_result:
                pass
                return analysis_result
        except:
            pass
        print(f"[ERROR] [CIRCADIAN_ENHANCED] Circadian analysis failed completely")
        return None

async def run_routine_generation(
    user_id: str,
    archetype: str,
    behavior_analysis: dict,
    circadian_analysis: dict = None,
    user_timezone: str = None,
    markdown_plan: str = None,
    preferences: dict = None
) -> dict:
    """
    Simplified Routine Generation - Clean flow with feedback integration

    Includes ONLY:
    - Fresh behavior analysis (TODAY)
    - Fresh circadian analysis (TODAY)
    - TaskPreseeder with check-in feedback (enjoyed, continue_preference, timing)
    - User preferences (wake_time, sleep_time, workout_timing, goals, time_slots)
    - Key insights extraction (4 bullet points for UI)
    - Direct database storage

    REMOVED:
    - Memory system overhead
    - AIContextIntegrationService complexity
    - Historical analysis context

    Args:
        preferences: Optional dict with user scheduling preferences:
            - wake_time: "06:00" (24-hour format)
            - sleep_time: "22:00" (24-hour format)
            - preferred_workout_time: "morning" | "evening" | "flexible"
            - available_time_slots: ["morning", "afternoon", "evening"]
            - goals: ["hydration", "movement", "nutrition", "sleep", "stress"]
            - energy_pattern: "morning_person" | "night_owl" | "balanced"
    """
    try:
        print(f"🏃 [ROUTINE] Starting simplified routine generation for {user_id[:8]}...")

        # Step 1: Fetch health data directly from Sahha API (always fresh)
        import asyncio
        from services.sahha_data_service import get_sahha_data_service
        from shared_libs.utils.system_prompts import get_system_prompt

        print(f"[ENDPOINTS] [SAHHA] Fetching fresh data from Sahha API...")
        from services.sahha.sahha_client import get_sahha_client

        # Fetch Sahha data directly WITHOUT triggering archival
        # (Data was already archived during behavior/circadian analysis)
        sahha_client = get_sahha_client()
        sahha_data = await sahha_client.fetch_health_data(
            external_id=user_id,
            since_timestamp=None,
            days=7
        )

        # Convert to UserHealthContext format
        from shared_libs.data_models.health_models import create_health_context_from_raw_data

        raw_biomarkers = []
        for bio in sahha_data.get("biomarkers", []):
            raw_biomarkers.append({
                "id": bio.get("id", f"sahha_{bio.get('type')}_{bio.get('startDateTime')}"),
                "profile_id": user_id,
                "category": bio.get("category", "other"),
                "type": bio.get("type"),
                "value": bio.get("value"),
                "unit": bio.get("unit"),
                "data": {},
                "start_date_time": bio.get("startDateTime"),
                "end_date_time": bio.get("endDateTime"),
                "created_at": bio.get("createdAt"),
                "updated_at": datetime.now().isoformat()
            })

        raw_scores = []
        for score in sahha_data.get("scores", []):
            raw_scores.append({
                "id": score.get("id"),
                "profile_id": user_id,
                "type": score.get("type"),
                "score": score.get("score"),
                "score_date_time": score.get("scoreDateTime"),
                "state": score.get("state"),
                "data": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })

        user_context = create_health_context_from_raw_data(
            user_id=user_id,
            raw_scores=raw_scores,
            raw_biomarkers=raw_biomarkers,
            raw_archetypes=[],
            days=7
        )

        print(f"[SUCCESS] [SAHHA] Fresh data fetched ({len(raw_biomarkers)} biomarkers, {len(raw_scores)} scores)")
        print(f"ℹ️  [SAHHA] Skipping archival (data already archived during behavior/circadian analysis)")

        user_context_summary = await format_health_data_for_ai(user_context)

        # Step 2: Get system prompt (using existing routine_plan prompt)
        system_prompt = get_system_prompt("routine_plan")

        # Step 3: Run TaskPreseeder with check-in feedback integration
        preselected_tasks_result = None
        try:
            from services.dynamic_personalization.task_preseeder import TaskPreseeder

            readiness_level = behavior_analysis.get('readiness_level', 'Medium')
            mode_mapping = {'Low': 'low', 'Medium': 'medium', 'High': 'high'}
            mode = mode_mapping.get(readiness_level, 'medium')

            preseeder = TaskPreseeder()
            await preseeder.initialize()

            preselected_tasks_result = await preseeder.select_tasks_for_plan(
                user_id=user_id,
                archetype=archetype,
                mode=mode,
                plan_date=datetime.now(),
                preferences=preferences  # NEW: Pass user preferences for task selection
            )

            await preseeder.close()

            if preselected_tasks_result['has_sufficient_feedback']:
                stats = preselected_tasks_result['selection_stats']
                print(f"[SUCCESS] [PRESEED] Selected {stats['total_selected']} tasks from {stats['feedback_count']} days of feedback")
                print(f"   Check-in feedback: {stats['checkin_feedback_used']}")
                print(f"   Excluded categories: {stats['categories_excluded']}")
                print(f"   Boosted categories: {stats['categories_boosted']}")
                print(f"   Learning phase: {stats['learning_phase']}")
            else:
                print(f"⚪ [PRESEED] Cold start - using pure AI ({preselected_tasks_result['selection_stats']['feedback_count']} completed tasks)")

        except Exception as preseed_error:
            print(f"[WARNING] [PRESEED] TaskPreseeder failed: {preseed_error}")
            preselected_tasks_result = None

        # Step 4: Generate routine plan
        print(f"🤖 [ROUTINE] Generating plan with behavior + circadian analysis...")
        routine_result = await run_routine_planning_4o(
            system_prompt=system_prompt,
            user_context=user_context_summary,
            behavior_analysis=behavior_analysis,
            archetype=archetype,
            circadian_analysis=circadian_analysis,
            preselected_tasks=preselected_tasks_result,
            user_timezone=user_timezone,
            markdown_plan=markdown_plan,
            preferences=preferences  # NEW: Pass user preferences to AI prompt
        )

        # Step 5: Extract key insights
        key_insights = []
        try:
            from services.insights_service import get_insights_service
            insights_service = get_insights_service()

            key_insights = insights_service.extract_key_insights(
                behavior_analysis=behavior_analysis,
                circadian_analysis=circadian_analysis,
                preselected_tasks=preselected_tasks_result
            )

            print(f"[INFO] [INSIGHTS] Extracted {len(key_insights)} insights:")
            for i, insight in enumerate(key_insights, 1):
                print(f"   {i}. {insight}")

        except Exception as insights_error:
            print(f"[WARNING] [INSIGHTS] Failed: {insights_error}")
            key_insights = []

        # Step 6: Save to database (direct Supabase, no AIContextIntegrationService)
        analysis_id = None
        try:
            from supabase import create_client
            import os
            import json

            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_KEY")
            )

            # Always insert new record (no upsert constraint exists)
            # Create input_summary for database
            input_summary = json.dumps({
                'analysis_type': 'routine_plan',
                'archetype': archetype,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'user_id': user_id,
                'readiness_mode': behavior_analysis.get('readiness_level', 'Medium') if behavior_analysis else 'Medium',
                'has_feedback': preselected_tasks_result.get('has_sufficient_feedback', False) if preselected_tasks_result else False,
                'feedback_count': preselected_tasks_result.get('selection_stats', {}).get('feedback_available', 0) if preselected_tasks_result else 0
            })

            result = supabase.table('holistic_analysis_results').insert({
                'user_id': user_id,
                'analysis_type': 'routine_plan',
                'analysis_result': routine_result,
                'archetype': archetype,
                'input_summary': input_summary,
                'agent_id': 'routine_plan_agent',
                'key_insights': json.dumps(key_insights),
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()

            if result.data:
                analysis_id = result.data[0]['id']
                print(f"[SUCCESS] [STORAGE] Saved plan with ID: {analysis_id}")

                # Step 7: Extract plan items
                try:
                    from services.plan_extraction_service import PlanExtractionService
                    extraction_service = PlanExtractionService()

                    stored_items = await extraction_service.extract_and_store_plan_items(
                        analysis_result_id=analysis_id,
                        profile_id=user_id,
                        preselected_tasks=preselected_tasks_result
                    )
                    print(f"[SUCCESS] [EXTRACTION] Stored {len(stored_items)} plan items")

                except Exception as extraction_error:
                    print(f"[WARNING] [EXTRACTION] Failed: {extraction_error}")

        except Exception as storage_error:
            print(f"[WARNING] [STORAGE] Failed: {storage_error}")

        # Add metadata to result
        routine_result.update({
            "analysis_id": analysis_id,
            "key_insights": key_insights,
            "simplified_flow": True,
            "memory_enhanced": False
        })

        print(f"[SUCCESS] [ROUTINE] Generation complete for {user_id[:8]}...")
        return routine_result

    except Exception as e:
        print(f"[ERROR] [ROUTINE] Error: {e}")
        raise

async def run_memory_enhanced_nutrition_generation(user_id: str, archetype: str, behavior_analysis: dict) -> dict:
    """
    Memory-Enhanced Nutrition Generation - Includes all features from /api/analyze
    Features:
    - Memory context preparation using MemoryIntegrationService
    - Memory-enhanced prompt generation
    - Storing nutrition plan in memory tables
    - Updating user memory profile
    - Complete logging of nutrition generation data
    """
    try:
        # print(f"[NUTRITION] [MEMORY_ENHANCED] Starting memory-enhanced nutrition generation for {user_id[:8]}...")  # Commented for error-only mode
        
        # Import memory integration service
        from services.ai_context_integration_service import AIContextIntegrationService
        
        # Initialize memory integration service
        memory_service = AIContextIntegrationService()
        
        # Step 1: Prepare memory-enhanced context
        # # Production: Verbose print removed  # Commented to reduce noise
        memory_context_obj = await memory_service.prepare_memory_enhanced_context(user_id, None, archetype)

        # Convert ContextEnhancedContext object to dict with relevant memory fields
        memory_context = {
            "ai_context_summary": memory_context_obj.ai_context_summary,
            "behavior_analysis_history": memory_context_obj.behavior_analysis_history,
            "circadian_analysis_history": memory_context_obj.circadian_analysis_history,
            "engagement_insights": memory_context_obj.engagement_insights,
            "analysis_mode": memory_context_obj.analysis_mode,
            "days_to_fetch": memory_context_obj.days_to_fetch
        }

        # Step 2: Get user data for nutrition generation
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt

        user_service = UserDataService()

        # Get user data (service handles days internally based on analysis history)
        user_context, data_quality = await user_service.get_analysis_data(user_id)

        # # Production: Verbose print removed  # Commented for error-only mode

        # Step 3: Get and enhance system prompt with memory
        system_prompt = get_system_prompt("nutrition_plan")
        enhanced_prompt = await memory_service.enhance_agent_prompt(
            system_prompt, memory_context_obj, "nutrition_plan"
        )
        
        # print(f"[ANALYSIS] [MEMORY_ENHANCED] Enhanced nutrition prompt with memory context (+{len(enhanced_prompt) - len(system_prompt)} chars)")  # Commented for error-only mode
        
        # Step 4: Prepare nutrition agent data with memory context
        user_context_summary = await format_health_data_for_ai(user_context)
        nutrition_data = await prepare_nutrition_agent_data(user_context, behavior_analysis)
        
        # Step 5: Run nutrition planning with memory-enhanced prompt
        nutrition_result = await run_nutrition_planning_4o(enhanced_prompt, user_context_summary, behavior_analysis, archetype)
        
        # Step 6: Store nutrition plan insights in memory
        # print(f"[CACHE] [MEMORY_ENHANCED] Storing nutrition plan insights in memory...")  # Commented for error-only mode
        insights_stored = await memory_service.store_analysis_insights(
            user_id, "nutrition_plan", nutrition_result, archetype
        )
        
        if insights_stored:
            # # Production: Verbose print removed  # Commented to reduce noise
            pass
        else:
            # # Production: Verbose print removed  # Commented for error-only mode
            pass
        
        # Step 7: Store complete nutrition plan in holistic_analysis_results table
        # DISABLED: HolisticMemoryService removed - no replacement storage implemented yet
        # Database storage temporarily disabled - nutrition plan still works but not persisted to DB
        # TODO: Implement proper storage using AIContextIntegrationService or alternative
        pass
        
        # Step 8: Log complete nutrition generation data (input/output logging)
        await log_complete_analysis(
            "nutrition_plan", user_id, archetype, 
            nutrition_data, nutrition_result, memory_context,
            analysis_source="shared"
        )
        
        # Step 9: Cleanup memory service
        await memory_service.cleanup()
        
        # Add memory enhancement metadata to result
        nutrition_result.update({
            "memory_enhanced": True,
            "analysis_mode": memory_context.get("analysis_mode", "initial"),
            "days_fetched": memory_context.get("days_to_fetch", 7),
            "memory_focus_areas": [],  # Removed from dict - agents extract from context
            "insights_stored": insights_stored
        })
        
        # # Production: Verbose print removed  # Commented to reduce noise
        return nutrition_result
        
    except Exception as e:
        print(f"[ERROR] [MEMORY_ENHANCED] Error in memory-enhanced nutrition generation: {e}")
        # Fallback to regular nutrition generation
        # print(f"[PROCESS] [MEMORY_ENHANCED] Falling back to regular nutrition generation...")  # Commented to reduce noise
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        user_context, _ = await user_service.get_analysis_data(user_id)
        user_context_summary = await format_health_data_for_ai(user_context)
        system_prompt = get_system_prompt("nutrition_plan")
        
        return await run_nutrition_planning_4o(system_prompt, user_context_summary, behavior_analysis, archetype)


async def run_nutrition_planning_4o(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str, user_timezone: str = None) -> dict:
    """Run nutrition planning using gpt-4o - now includes readiness mode"""
    try:
        client = openai.AsyncOpenAI()

        # Extract readiness mode from behavior analysis
        readiness_level = behavior_analysis.get('readiness_level', 'Medium')
        mode_mapping = {
            'Low': 'recovery mode (focus on anti-inflammatory foods, easy-to-digest meals, hydration)',
            'Medium': 'productive mode (balanced macros, sustained energy, regular meal timing)',
            'High': 'performance mode (optimized nutrition for peak output, strategic meal timing, nutrient density)'
        }
        mode_description = mode_mapping.get(readiness_level, 'balanced nutrition')

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\nYou are a nutrition planning expert. Create detailed, practical nutrition plans based on health data, behavioral insights, and readiness status."
                },
                {
                    "role": "user",
                    "content": f"""
{user_context}

BEHAVIORAL INSIGHTS:
{json.dumps(behavior_analysis, indent=2, cls=DateTimeEncoder)}

READINESS MODE: {readiness_level} - {mode_description}

Create a comprehensive {archetype} nutrition plan for TODAY using the HolisticOS approach.
Tailor the nutrition strategy to the current readiness mode ({readiness_level}):
- Performance mode: Higher calories, optimized pre/post-workout nutrition, nutrient timing
- Productive mode: Balanced meals, sustained energy, consistent meal timing
- Recovery mode: Anti-inflammatory foods, easy digestion, extra hydration, recovery nutrients

Include the following structure:
1. **Daily Nutritional Targets** (calories, protein, carbs, fats, fiber, vitamins) - adjusted for {readiness_level} mode
2. **7 Meal Blocks** with detailed breakdown:
   - Early_Morning: Hydration/preparation (adjust for readiness mode)
   - Breakfast: Balanced start (lighter for recovery, more substantial for performance)
   - Morning_Snack: Energy maintenance
   - Lunch: Balanced midday nutrition
   - Afternoon_Snack: Sustained energy
   - Dinner: Recovery and satisfaction
   - Evening_Snack: Sleep preparation
3. **Nutrition Tips** for each meal explaining timing, composition, and readiness mode alignment
4. **Health Data Integration** - reference the provided health metrics

Make this plan practical, evidence-based, and specifically tailored to the {archetype} archetype, readiness mode, and health data patterns.
"""
                }
            ],
            temperature=0.4,
            max_tokens=2000
        )

        from shared_libs.utils.timezone_helper import get_user_local_date

        return {
            "date": get_user_local_date(user_timezone),
            "archetype": archetype,
            "content": response.choices[0].message.content,
            "model_used": "gpt-4o",
            "plan_type": "comprehensive_nutrition",
            "system": "HolisticOS",
            "readiness_mode": readiness_level
        }

    except Exception as e:
        from shared_libs.utils.timezone_helper import get_user_local_date
        logger.error(f"Error in nutrition planning: {e}")
        # Return fallback nutrition plan
        return {
            "date": get_user_local_date(user_timezone),
            "archetype": archetype,
            "content": f"HolisticOS {archetype} Nutrition Plan - Fallback plan due to processing error",
            "model_used": "fallback",
            "plan_type": "fallback_nutrition",
            "system": "HolisticOS",
            "error": str(e)
        }

async def run_routine_planning_gpt4o(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str, user_timezone: str = None) -> dict:
    """Run routine planning using gpt-4o for plan generation - Phase 4.2 Direct OpenAI Implementation"""
    try:
        client = openai.AsyncOpenAI()
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": f"{system_prompt}\n\nYou are a routine planning expert. Create detailed, practical daily routine plans based on health data and behavioral insights."
                },
                {
                    "role": "user", 
                    "content": f"""
{user_context}

BEHAVIORAL INSIGHTS:
{json.dumps(behavior_analysis, indent=2, cls=DateTimeEncoder)}

Create a comprehensive {archetype} daily routine plan for TODAY using the HolisticOS approach.

Include the following structure:
1. **Daily Summary** with key focus areas and goals
2. **4 Time Blocks** with detailed breakdown:
   - Morning Wake-up (6:00-7:00 AM): Foundation setting and energy building
   - Focus Block (9:00-11:00 AM): Peak productivity window
   - Afternoon Recharge (3:00-3:30 PM): Energy restoration and movement
   - Evening Wind-down (8:30-9:30 PM): Recovery and preparation for rest
3. **Task Details** for each time block explaining:
   - Specific tasks and activities
   - Why each activity matters for health optimization
   - How it connects to the behavioral insights
4. **Health Data Integration** - reference the provided health metrics

Make this routine practical, evidence-based, and specifically tailored to the {archetype} archetype and the provided health data patterns.
"""
                }
            ],
            temperature=0.4,  # Balanced creativity for practical planning
            max_tokens=2000
        )
        
        from shared_libs.utils.timezone_helper import get_user_local_date

        return {
            "date": get_user_local_date(user_timezone),
            "archetype": archetype,
            "content": response.choices[0].message.content,
            "model_used": "gpt-4o",
            "plan_type": "comprehensive_routine",
            "system": "HolisticOS"
        }

    except Exception as e:
        from shared_libs.utils.timezone_helper import get_user_local_date
        print(f"Error in 4o nutrition planning: {e}")
        return {
            "error": str(e),
            "model_used": "gpt-4o - fallback",
            "archetype": archetype,
            "date": get_user_local_date(user_timezone)
        }

async def run_routine_planning_4o(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str, circadian_analysis: dict = None, markdown_plan: str = None, user_timezone: str = None, preselected_tasks: dict = None, preferences: dict = None) -> dict:
    """
    Run routine planning using gpt-4o

    Four modes:
    - Normal mode: Uses behavior + circadian analysis to generate plan
    - Markdown mode: Converts user's markdown plan to structured format
    - Option B mode: Includes pre-selected library tasks (when preselected_tasks provided)
    - Preferences mode: Respects user preferences for wake/sleep times, workout timing, and goals

    Args:
        preferences: Optional dict with user scheduling preferences:
            - wake_time: "06:00" (24-hour format)
            - sleep_time: "22:00" (24-hour format)
            - preferred_workout_time: "morning" | "evening" | "flexible"
            - available_time_slots: ["morning", "afternoon", "evening"]
            - goals: ["hydration", "movement", "nutrition", "sleep", "stress"]
            - energy_pattern: "morning_person" | "night_owl" | "balanced"
    """
    try:
        # NOTE: Enum conversion now handled at source (see line ~1102)
        # behavior_analysis already has enums converted before reaching this function

        client = openai.AsyncOpenAI()

        # Extract readiness mode from circadian analysis (if available) or behavior analysis
        if circadian_analysis and 'readiness_assessment' in circadian_analysis:
            readiness_level = circadian_analysis['readiness_assessment'].get('current_mode', 'Productive')
            mode_description = circadian_analysis['readiness_assessment'].get('mode_description', 'balanced activities')
        else:
            # Fallback to behavior analysis
            readiness_level = behavior_analysis.get('readiness_level', 'Medium')
            mode_mapping = {
                'Low': 'recovery mode (gentle, restorative activities with reduced intensity)',
                'Medium': 'productive mode (moderate, building activities with steady progress)',
                'High': 'performance mode (intense, optimization activities with peak output)'
            }
            mode_description = mode_mapping.get(readiness_level, 'balanced activities')

        # Prepare circadian context for prompt (only for normal mode)
        circadian_context = ""
        if circadian_analysis and not markdown_plan:
            # Include both timeline (for precise scheduling) and summary (for quick reference)
            timeline_available = 'energy_timeline' in circadian_analysis and len(circadian_analysis.get('energy_timeline', [])) > 0

            if timeline_available:
                circadian_context = f"""
CIRCADIAN ENERGY DATA:

Energy Timeline (96 time slots, 15-minute intervals):
Each slot has: time (HH:MM), energy_level (0-100), zone (peak/maintenance/recovery)

Quick Summary:
- Optimal wake window: {circadian_analysis.get('summary', {}).get('optimal_wake_window', 'N/A')}
- Peak energy periods: {circadian_analysis.get('summary', {}).get('peak_energy_periods', [])}
- Maintenance periods: {circadian_analysis.get('summary', {}).get('maintenance_periods', [])}
- Low energy periods: {circadian_analysis.get('summary', {}).get('low_energy_periods', [])}
- Optimal sleep window: {circadian_analysis.get('summary', {}).get('optimal_sleep_window', 'N/A')}

Full Energy Timeline:
{json.dumps(circadian_analysis.get('energy_timeline', []), indent=2, cls=DateTimeEncoder)}
"""
            else:
                # Fallback to old format if timeline not available
                circadian_context = f"""
CIRCADIAN RHYTHM DATA:
{json.dumps(circadian_analysis, indent=2, cls=DateTimeEncoder)}
"""

        # Build conditional user message
        if markdown_plan:
            # [SUCCESS] PHASE 2: MARKDOWN MODE - Extract and preserve user's exact plan

            # Extract user's plan from between markers (sent from HolisticAI Phase 1)
            user_plan_content = markdown_plan
            if "---USER_PLAN_START---" in markdown_plan and "---USER_PLAN_END---" in markdown_plan:
                # Extract only the user's plan content
                start_marker = "---USER_PLAN_START---"
                end_marker = "---USER_PLAN_END---"
                start_idx = markdown_plan.find(start_marker) + len(start_marker)
                end_idx = markdown_plan.find(end_marker)
                user_plan_content = markdown_plan[start_idx:end_idx].strip()
                logger.info(f"[STORAGE] Extracted user plan from boundaries ({len(user_plan_content)} chars)")

            user_message = f"""🚨 CRITICAL TASK: You are a health science AI. Your ONLY job is to preserve the user's exact plan and add health reasoning.

---

USER'S EXACT PLAN (PRESERVE THIS):

{user_plan_content}

---

[TARGET] YOUR MANDATORY RULES:

[SUCCESS] DO (Required):
1. Count the time blocks in the user's plan above
2. Use the EXACT same number of time blocks
3. Use the EXACT times from each block (e.g., "6:00 AM", "7:00 AM")
4. Use the EXACT activities listed (e.g., "Running", "Protein shake")
5. Add health science reasoning for WHY each activity works at that time
6. Connect to circadian rhythm, {archetype} archetype, and health benefits
7. Output valid JSON matching the standard routine plan format

[ERROR] DO NOT (Forbidden):
1. Create hypothetical examples
2. Say "Since user's plan is not provided"
3. Change any times or activities
4. Add or remove time blocks
5. Replace activities (e.g., yoga when user said running)
6. Generate a new plan from scratch

---

📋 EXPECTED OUTPUT STRUCTURE:

{{
  "markdown_plan": "<formatted markdown with all user's blocks>",
  "time_blocks": [
    {{
      "time_range": "<user's exact time>",
      "title": "<user's exact title>",
      "purpose": "<add health reasoning here>",
      "why_it_matters": "<circadian/archetype connection>",
      "connection_to_insights": "<connect to {archetype}>",
      "health_data_integration": "<reference metrics if relevant>"
    }}
    // ... SAME NUMBER OF BLOCKS AS USER PROVIDED
  ],
  "plan_items": [
    {{
      "time_block": "<matches time_blocks title>",
      "title": "<user's exact activity>",
      "description": "<add health science details>",
      "scheduled_time": "<user's exact start time in HH:MM>",
      "scheduled_end_time": "<user's exact end time in HH:MM>",
      "estimated_duration_minutes": <calculate from times>,
      "task_type": "exercise|nutrition|sleep|focus|recovery|social|wellness",
      "is_trackable": true,
      "priority_level": "high|medium|low"
    }}
    // ... ALL ACTIVITIES FROM USER'S PLAN
  ]
}}

---

🔍 CONCRETE EXAMPLE:

INPUT (User's Plan):
```
## 6:00 AM - Morning Activation
- Running (30 min)
- Protein shake
```

CORRECT OUTPUT:
```json
{{
  "time_blocks": [
    {{
      "time_range": "6:00 AM - 6:45 AM",
      "title": "Morning Activation",
      "purpose": "Cardiovascular activation aligned with cortisol peak for metabolic kickstart",
      "why_it_matters": "Early morning cardio (6-8 AM) syncs with natural cortisol rhythm, enhancing fat burning by 30%. Post-run protein prevents muscle breakdown during catabolic window.",
      "connection_to_insights": "Aligns with {archetype} preference for structured, science-backed morning routines",
      "health_data_integration": "Supports cardiovascular health scores and stress resilience metrics"
    }}
  ],
  "plan_items": [
    {{
      "time_block": "Morning Activation",
      "title": "Running",
      "description": "30-minute outdoor cardiovascular exercise to activate sympathetic nervous system and align with cortisol peak (6-8 AM window). Increases alertness, burns fat efficiently, and primes body for productive day.",
      "scheduled_time": "06:00",
      "scheduled_end_time": "06:30",
      "estimated_duration_minutes": 30,
      "task_type": "exercise",
      "is_trackable": true,
      "priority_level": "high"
    }},
    {{
      "time_block": "Morning Activation",
      "title": "Protein shake",
      "description": "20-30g protein shake immediately post-cardio to support muscle recovery, prevent catabolism, and maintain metabolic rate. Whey or plant-based protein with simple carbs for rapid absorption.",
      "scheduled_time": "06:30",
      "scheduled_end_time": "06:45",
      "estimated_duration_minutes": 15,
      "task_type": "nutrition",
      "is_trackable": true,
      "priority_level": "high"
    }}
  ]
}}
```

---

NOW PROCESS THE USER'S PLAN ABOVE. Output ONLY valid JSON. Count their blocks and preserve everything exactly.
"""
        else:
            # NORMAL MODE: Generate from behavior + circadian analysis using FIXED 5-BLOCK STRUCTURE

            # Calculate times for the 5 fixed blocks based on circadian analysis
            # Default times if no circadian data available
            morning_start = "06:00 AM"
            morning_end = "09:00 AM"
            peak_start = "09:00 AM"
            peak_end = "12:00 PM"
            midday_start = "12:00 PM"
            midday_end = "03:00 PM"
            evening_start = "03:00 PM"
            evening_end = "06:00 PM"
            winddown_start = "06:00 PM"
            winddown_end = "10:00 PM"

            # If circadian timeline is available, calculate optimal times for each block
            if circadian_analysis and 'energy_timeline' in circadian_analysis:
                timeline = circadian_analysis['energy_timeline']

                # Find first high energy slot for morning block
                for slot in timeline:
                    if slot.get('energy_level', 0) > 60 and slot.get('zone') in ['peak', 'maintenance']:
                        morning_start = slot.get('time', morning_start)
                        break

                # Find peak energy period
                peak_slots = [s for s in timeline if s.get('zone') == 'peak']
                if peak_slots:
                    peak_start = peak_slots[0].get('time', peak_start)
                    peak_end = peak_slots[-1].get('time', peak_end) if len(peak_slots) > 1 else peak_end

                # Find recovery/low energy period for midday slump
                recovery_slots = [s for s in timeline if s.get('zone') == 'recovery' and '12:' in s.get('time', '') or '13:' in s.get('time', '') or '14:' in s.get('time', '')]
                if recovery_slots:
                    midday_start = recovery_slots[0].get('time', midday_start)
                    midday_end = recovery_slots[-1].get('time', midday_end) if len(recovery_slots) > 1 else midday_end

                # Evening routine: moderate energy period
                evening_slots = [s for s in timeline if s.get('zone') == 'maintenance' and ('15:' in s.get('time', '') or '16:' in s.get('time', '') or '17:' in s.get('time', ''))]
                if evening_slots:
                    evening_start = evening_slots[0].get('time', evening_start)
                    evening_end = evening_slots[-1].get('time', evening_end) if len(evening_slots) > 1 else evening_end

                # Wind down: evening recovery period
                winddown_slots = [s for s in timeline if s.get('zone') == 'recovery' and ('18:' in s.get('time', '') or '19:' in s.get('time', '') or '20:' in s.get('time', '') or '21:' in s.get('time', ''))]
                if winddown_slots:
                    winddown_start = winddown_slots[0].get('time', winddown_start)
                    winddown_end = winddown_slots[-1].get('time', winddown_end) if len(winddown_slots) > 1 else winddown_end

            # === OPTION B: Build pre-selected tasks context ===
            preselected_tasks_context = ""
            if preselected_tasks and preselected_tasks.get('has_sufficient_feedback') and len(preselected_tasks.get('preselected_tasks', [])) > 0:
                tasks_list = preselected_tasks['preselected_tasks']
                tasks_formatted = []

                for i, task in enumerate(tasks_list, 1):
                    task_str = f"""  {i}. {task.get('name', 'Unknown Task')} ({task.get('category', 'general')}, {task.get('duration_minutes', 'N/A')} min)
     Time Preference: {task.get('time_preference', 'any')}
     Reason: {task.get('selection_reason', 'Selected for you')}
     Details: {task.get('description', 'No description available')}"""
                    tasks_formatted.append(task_str)

                # Extract friction analysis from feedback
                friction_data = preselected_tasks['selection_stats'].get('friction_analysis', {})
                low_friction = preselected_tasks['selection_stats'].get('low_friction_categories', [])
                high_friction = preselected_tasks['selection_stats'].get('high_friction_categories', [])
                feedback_count = preselected_tasks['selection_stats'].get('feedback_count', 0)

                # DEBUG: Log friction data received by AI prompt builder
                logger.info(f"[AI-PROMPT-DEBUG] Friction data received from TaskPreseeder:")
                logger.info(f"[AI-PROMPT-DEBUG]   Low friction: {low_friction}")
                logger.info(f"[AI-PROMPT-DEBUG]   High friction: {high_friction}")
                logger.info(f"[AI-PROMPT-DEBUG]   Friction analysis: {friction_data}")
                logger.info(f"[AI-PROMPT-DEBUG]   Feedback count: {feedback_count}")

                # NEW: Build PREFERENCES context (if provided)
                preferences_context = ""
                if preferences:
                    wake_time = preferences.get('wake_time', 'Not specified')
                    sleep_time = preferences.get('sleep_time', 'Not specified')
                    workout_time = preferences.get('preferred_workout_time', 'Flexible')
                    goals = ', '.join(preferences.get('goals', [])) or 'Balanced health'
                    available_slots = ', '.join(preferences.get('available_time_slots', [])) or 'All day'

                    logger.info(f"[AI-PROMPT-DEBUG] User preferences received:")
                    logger.info(f"[AI-PROMPT-DEBUG]   Wake: {wake_time}, Sleep: {sleep_time}")
                    logger.info(f"[AI-PROMPT-DEBUG]   Workout timing: {workout_time}")
                    logger.info(f"[AI-PROMPT-DEBUG]   Goals: {goals}")

                    preferences_context = f"""

📋 USER PREFERENCES (Direct Input - HIGHEST PRIORITY):

⏰ SCHEDULE PREFERENCES:
   - Preferred Wake Time: {wake_time}
   - Preferred Sleep Time: {sleep_time}
   - Workout Timing Preference: {workout_time}
   - Available Time Slots: {available_slots}

[TARGET] PRIORITY GOALS:
   - Focus Areas: {goals}

[WARNING] CRITICAL SCHEDULING RULES (MUST FOLLOW - OVERRIDE CIRCADIAN DATA IF CONFLICT):
   1. ALWAYS respect user's wake/sleep time preferences
   2. If workout preference is "morning", schedule ALL movement tasks before 12 PM
   3. If workout preference is "evening", schedule ALL movement tasks after 5 PM
   4. Only schedule tasks during user's available_time_slots
   5. Prioritize categories mentioned in goals (give them prime time slots)
   6. If circadian data conflicts with user preferences, USER PREFERENCES WIN

"""

                # Build FRICTION-REDUCTION constraints (NOT exclusion)
                feedback_constraints = ""
                motivation_data = ""

                if low_friction or high_friction:
                    feedback_constraints = f"\n[ANALYSIS] BEHAVIORAL ADAPTATION STRATEGY ({feedback_count} completed tasks analyzed):\n"

                    # Build success stories for low-friction categories
                    success_stories = []
                    for category in low_friction:
                        if category in friction_data:
                            data = friction_data[category]
                            total_attempts = data.get('total_attempts', 0)
                            avg_rating = data.get('avg_experience_rating', 0)
                            yes_rate = data.get('continue_yes_rate', 0)

                            if total_attempts > 0:
                                success_stories.append(
                                    f"  • {category}: {total_attempts} completions, {avg_rating:.1f}/5 rating, {int(yes_rate*100)}% want to continue ⭐"
                                )

                    # Build struggle points for high-friction categories
                    struggle_points = []
                    for category in high_friction:
                        if category in friction_data:
                            data = friction_data[category]
                            friction_score = data.get('friction_score', 0)
                            avg_rating = data.get('avg_experience_rating', 0)
                            no_rate = data.get('continue_no_rate', 0)
                            total_attempts = data.get('total_attempts', 0)

                            struggle_points.append(
                                f"  • {category}: {total_attempts} attempts, friction {friction_score:.2f}/1.0, {avg_rating:.1f}/5 rating, {int(no_rate*100)}% want to stop"
                            )

                    # Add success categories section
                    if success_stories:
                        feedback_constraints += f"""
[SUCCESS] SUCCESS CATEGORIES (Keep & Celebrate):
{chr(10).join(success_stories)}

[INFO] User is CRUSHING these! Keep the momentum, add motivational messages, use as anchors for habit stacking.
"""

                    # Add challenge categories section
                    if struggle_points:
                        feedback_constraints += f"""
[WARNING]  CHALLENGE CATEGORIES (Simplify with Micro-Habits):
{chr(10).join(struggle_points)}

[INFO] User is struggling - SIMPLIFY these with Atomic Habits principles (never exclude!).
"""

                    if high_friction:
                        feedback_constraints += f"""
[WARNING] HIGH-FRICTION CATEGORIES (User struggles, needs SIMPLIFICATION):
   Categories: {', '.join(high_friction)}

   CRITICAL: DO NOT exclude these categories - they're essential for balanced health!

   📚 ATOMIC HABITS PRINCIPLES - Apply friction reduction:

   1️⃣ MAKE IT OBVIOUS (Cue):
      - Add visual/environmental cues: "Place protein shake ingredients on counter night before"
      - Link to existing habits: "After morning coffee, eat one piece of fruit"

   2️⃣ MAKE IT EASY (Reduce friction):
      - Simplify tasks: "Track macros" → "Take photo of 3 meals"
      - Reduce time: 30min meal prep → 5min assembly
      - Lower bar: "Perfect meals" → "Add one vegetable to lunch"
      - Use micro-habits: "Drink water" → "Take one sip when phone buzzes"

   3️⃣ MAKE IT ATTRACTIVE (Temptation bundling):
      - Pair with loved activity: "Protein shake after workout" (links to low-friction exercise)
      - Add immediate reward: "Healthy snack unlocks evening workout"

   4️⃣ MAKE IT SATISFYING (Immediate gratification):
      - Celebrate small wins: "Check off each meal logged"
      - Progress visualization: "3-day streak of vegetable servings"

   ⚙️ REQUIRED ACTIONS for high-friction categories:
      - Include 2-3 tasks from these categories (same count, simpler approach)
      - Use "micro-habits" language: 1-2 minute actions
      - Reduce complexity by 50%: Beginner-level difficulty
      - Add habit stacking: Link to established routines
      - Focus on ONE simple metric: "Did you do it?" not "Did you do it perfectly?"
"""

                    if low_friction:
                        feedback_constraints += f"""
[SUCCESS] LOW-FRICTION CATEGORIES (User succeeds easily, LEVERAGE as anchors):
   Categories: {', '.join(low_friction)}

   📚 ATOMIC HABITS - Use as motivation anchors:

   1️⃣ LEVERAGE SUCCESS:
      - Keep current approach (it's working!)
      - Don't overload: Maintain 2-3 tasks per category
      - Use as identity reinforcement: "I'm someone who works out consistently"

   2️⃣ HABIT STACKING:
      - Chain high-friction to low-friction: "After workout (easy), have protein shake (hard)"
      - Create gateway: "Complete nutrition task to unlock evening run"

   3️⃣ MOTIVATION TRANSFER:
      - Insight message: "Apply your exercise discipline to nutrition"
      - Link mindset: "Same energy that gets you to gym can get you to meal prep"

   ⚙️ REQUIRED ACTIONS for low-friction categories:
      - Maintain current task count and difficulty
      - Use as rewards: "Unlock [loved activity] by completing [struggled activity]"
      - Reference in insights: "Your consistency with [category] shows what you're capable of!"
"""

                # Build motivational context for AI to use in task descriptions
                motivation_context = ""
                if low_friction or high_friction:
                    motivation_context = f"""

TASK DESCRIPTION REQUIREMENTS (Professional & Clean):

**For Low-Friction/Success Categories** ({', '.join(low_friction) if low_friction else 'None'}):
1. Add motivational messages: "You've completed this {feedback_count // len(low_friction) if low_friction else 0} times! Keep the momentum going."
2. Celebrate wins: "5-day streak - excellent progress!" or "{int((feedback_count / len(low_friction)) * 100) if low_friction else 0}% completion rate."
3. Use as habit anchors: "After [this success habit], do [new habit]"
4. Suggest progressions: "Ready to add 5 more minutes?"

**For High-Friction/Challenge Categories** ({', '.join(high_friction) if high_friction else 'None'}):
1. Simplify language: "Just take a quick photo" not "Track comprehensive macros"
2. Show reduced time: "2-min task" instead of "30-min task"
3. Add micro-goals: "3-day photo streak challenge"
4. Stack after success: "Right after Morning Hydration (your anchor habit)"
5. Be encouraging: "Building the habit step by step" not "You should do this"
6. NO EMOJIS: Keep descriptions clean and professional

**Examples of Clean Task Descriptions:**

Success Category (Movement):
  "Morning Victory Stretch (15 min) - You've completed this 18 times! Keep the momentum going."

Challenge Category (Nutrition):
  "Quick Breakfast Photo (2 min) - Just snap a pic to build the habit.
   Stack after: Morning Hydration (your anchor)
   Goal: 3-day photo streak"

"""

                preselected_tasks_context = f"""
🌟 PRE-SELECTED LIBRARY TASKS (OPTION B - MUST INCLUDE):

The following {len(tasks_list)} tasks have been intelligently pre-selected from the task library based on user's feedback and learning phase ({preselected_tasks['selection_stats']['learning_phase']}):

{chr(10).join(tasks_formatted)}
{preferences_context if preferences_context else ''}
{feedback_constraints}
{motivation_context}
[TARGET] CRITICAL INSTRUCTIONS (Behavioral Science Approach):

1. BALANCE OVER PREFERENCE:
   - Include ALL essential health categories (nutrition, exercise, sleep, recovery, hydration)
   - NEVER skip a category because user dislikes it
   - Goal: Optimize compliance, not preference

2. PRE-SELECTED TASKS:
   - Include ALL {len(tasks_list)} pre-selected library tasks
   - Schedule based on time_preference and circadian timing
   - Use exact task names and durations

3. ADDITIONAL TASKS (Fill to ~12 total):
   - High-friction categories: Add 2-3 SIMPLIFIED tasks (micro-habits, 1-2 min)
   - Low-friction categories: Maintain 2-3 tasks (current difficulty)
   - Medium-friction: Add 1-2 tasks (current approach)
   - Ensure balanced distribution across ALL health categories

4. ATOMIC HABITS APPLICATION:
   - High-friction: Reduce to smallest version possible
   - Habit stacking: Link new habits to existing routines
   - Identity-based: "I'm the type of person who..."
   - 2-minute rule: If takes < 2 min, do it now

5. MOTIVATION PSYCHOLOGY:
   - Leverage success: Reference low-friction wins in descriptions
   - Temptation bundling: Pair hard tasks with rewarding tasks
   - Implementation intentions: "After [existing habit], I will [new habit]"

[DATA] Learning Phase: {preselected_tasks['selection_stats']['learning_phase']}
📦 Categories Covered: {', '.join(preselected_tasks['selection_stats']['categories_covered'])}
[SUCCESS] User Feedback Count: {preselected_tasks['selection_stats']['feedback_count']} completed tasks
{f"[WARNING] High Friction (simplify): {', '.join(high_friction)}" if high_friction else ''}
{f"[SUCCESS] Low Friction (leverage): {', '.join(low_friction)}" if low_friction else ''}

"""
                # DEBUG: Log the final prompt context being sent to AI
                logger.info(f"[AI-PROMPT-DEBUG] Final prompt context summary:")
                logger.info(f"[AI-PROMPT-DEBUG]   Feedback constraints length: {len(feedback_constraints)} chars")
                logger.info(f"[AI-PROMPT-DEBUG]   Motivation context length: {len(motivation_context)} chars")
                logger.info(f"[AI-PROMPT-DEBUG]   High-friction instruction present: {'High Friction (simplify)' in preselected_tasks_context}")
                logger.info(f"[AI-PROMPT-DEBUG]   Low-friction instruction present: {'Low Friction (leverage)' in preselected_tasks_context}")
                if high_friction:
                    logger.info(f"[AI-PROMPT-DEBUG]   🚨 HIGH-FRICTION CATEGORIES SENT TO AI: {high_friction}")
                    logger.info(f"[AI-PROMPT-DEBUG]   🚨 AI INSTRUCTION: SIMPLIFY (not exclude) these categories")

            else:
                # Cold start or insufficient feedback - pure AI mode
                if preselected_tasks:
                    preselected_tasks_context = f"""
⚪ PURE AI MODE (Cold Start):

User has only {preselected_tasks.get('selection_stats', {}).get('feedback_count', 0)} completed tasks (threshold: 3).
Generate all tasks from scratch based on archetype ({archetype}) and behavioral insights.
Focus on building foundational habits to collect user feedback for future personalization.

"""
                else:
                    preselected_tasks_context = ""

            user_message = f"""
{user_context}

BEHAVIORAL INSIGHTS:
{json.dumps(behavior_analysis, indent=2, cls=DateTimeEncoder)}

{circadian_context}
{preselected_tasks_context}
READINESS MODE: {readiness_level} - {mode_description}

[TARGET] YOUR TASK: Generate a {archetype} routine plan with EXACTLY 5 FIXED TIME BLOCKS.

You MUST create a JSON response with these EXACT 5 blocks (no more, no less):

1. **Morning Block** ({morning_start} - {morning_end}): Gentle activation, breakfast, morning routine
2. **Peak Energy Block** ({peak_start} - {peak_end}): Most demanding work, important meetings, challenging tasks
3. **Mid-day Slump** ({midday_start} - {midday_end}): Lunch, rest, light activities to recharge
4. **Evening Routine** ({evening_start} - {evening_end}): Moderate work, exercise, evening meal prep
5. **Wind Down** ({winddown_start} - {winddown_end}): Relaxation, preparation for sleep, digital sunset

📋 REQUIRED JSON STRUCTURE:

You MUST respond with EXACTLY 5 time blocks in this structure (block_name, start_time, end_time are FIXED, but purpose and tasks come from YOUR ANALYSIS):

{{
  "time_blocks": [
    {{
      "block_name": "Morning Block",
      "start_time": "{morning_start}",
      "end_time": "{morning_end}",
      "zone_type": "maintenance",
      "purpose": "<ANALYZE behavior + circadian data and write appropriate purpose>",
      "tasks": [
        {{
          "start_time": "<Time within morning block>",
          "end_time": "<Time within morning block>",
          "title": "<Task title based on analysis>",
          "description": "<Task description based on user's needs, archetype, and energy levels>",
          "task_type": "<exercise|nutrition|work|focus|recovery|wellness|social>",
          "category": "<nutrition|exercise|hydration|recovery|movement|mindfulness|sleep|social>",
          "priority": "<high|medium|low>"
        }}
        // Add 2-5 tasks based on circadian energy data and behavioral insights
      ]
    }},
    {{
      "block_name": "Peak Energy Block",
      "start_time": "{peak_start}",
      "end_time": "{peak_end}",
      "zone_type": "peak",
      "purpose": "<ANALYZE and write purpose for peak energy period>",
      "tasks": [
        // Generate 2-5 high-intensity tasks suitable for peak energy
      ]
    }},
    {{
      "block_name": "Mid-day Slump",
      "start_time": "{midday_start}",
      "end_time": "{midday_end}",
      "zone_type": "recovery",
      "purpose": "<ANALYZE and write purpose for recovery period>",
      "tasks": [
        // Generate 2-4 light recovery tasks
      ]
    }},
    {{
      "block_name": "Evening Routine",
      "start_time": "{evening_start}",
      "end_time": "{evening_end}",
      "zone_type": "maintenance",
      "purpose": "<ANALYZE and write purpose for evening routine>",
      "tasks": [
        // Generate 2-5 moderate evening tasks
      ]
    }},
    {{
      "block_name": "Wind Down",
      "start_time": "{winddown_start}",
      "end_time": "{winddown_end}",
      "zone_type": "recovery",
      "purpose": "<ANALYZE and write purpose for wind down period>",
      "tasks": [
        // Generate 2-4 relaxing wind-down tasks
      ]
    }}
  ]
}}

⚡ CRITICAL INSTRUCTIONS:

**FIXED ELEMENTS (DO NOT CHANGE):**
- Exactly 5 time blocks with these exact names: "Morning Block", "Peak Energy Block", "Mid-day Slump", "Evening Routine", "Wind Down"
- Times shown above (calculated from circadian analysis)
- zone_type values: maintenance, peak, recovery as shown

**DYNAMIC ELEMENTS (BASED ON YOUR ANALYSIS):**
1. **purpose**: Analyze behavioral insights, circadian data, archetype ({archetype}), and readiness mode ({readiness_level}) to write appropriate purpose for each block
2. **tasks**: Generate 2-5 tasks per block based on:
   - Circadian energy timeline (match intensity to energy level)
   - Behavioral patterns and needs
   - {archetype} archetype characteristics
   - Readiness mode: {readiness_level}
   - Zone type (peak = high intensity, maintenance = moderate, recovery = light)
3. **task details**: Each task MUST include ALL of these fields:
   - start_time: REQUIRED - Specific time within block range in 12-hour format with AM/PM (e.g., "06:00 AM", "02:30 PM")
     ⚠️ CRITICAL: Use 12-hour format (01-12) with AM/PM, NOT 24-hour format with PM (e.g., "13:00 PM" is INVALID)
   - end_time: REQUIRED - Specific time within block range in 12-hour format with AM/PM (e.g., "06:30 AM", "03:00 PM")
     ⚠️ CRITICAL: Use 12-hour format (01-12) with AM/PM, NOT 24-hour format with PM (e.g., "15:00 PM" is INVALID)
   - title: Clear, actionable task name
   - description: Detailed explanation tailored to user's needs and health data
   - task_type: exercise, nutrition, work, focus, recovery, wellness, or social
   - category: nutrition, exercise, hydration, recovery, movement, mindfulness, sleep, or social (MUST match feedback categories)
   - priority: high, medium, or low based on health impact

🚨 CRITICAL TIME REQUIREMENTS:
- EVERY task MUST have both start_time AND end_time
- Times MUST be within their parent block's time range
- Times MUST be in 12-hour format with AM/PM (e.g., "08:45 AM", "02:15 PM")
- NEVER mix 24-hour format with AM/PM (e.g., "13:00 PM" is INVALID - use "01:00 PM" instead)
- Valid examples: "06:00 AM", "12:30 PM", "01:00 PM", "11:45 PM"
- Invalid examples: "13:00 PM", "15:00 PM", "18:00 PM" (these will be REJECTED)
- Tasks should be scheduled sequentially within each block (no overlaps)
- If you generate a task with invalid times, the system will override them

🚨 YOU MUST OUTPUT ONLY VALID JSON - NO MARKDOWN, NO EXTRA TEXT, JUST JSON.
"""

        # === SAFETY GUARDRAILS: Add safe prompt guidelines ===
        from services.safety_validator import get_safety_validator
        safety_validator = get_safety_validator()
        safety_guidelines = safety_validator.get_safe_prompt_guidelines()

        response = await client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},  # Force structured JSON output
            messages=[
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\nYou are a routine optimization expert. Create actionable daily routines based on health data, behavioral insights, energy timeline, and archetype frameworks.\n\n{safety_guidelines}\n\n🚨 CRITICAL REQUIREMENT: EVERY task MUST have start_time and end_time. Never generate a task without explicit times.\n\nYou MUST respond with ONLY valid JSON in this exact structure:\n{{\n  \"time_blocks\": [\n    {{\n      \"block_name\": \"Morning Block\",\n      \"start_time\": \"06:00 AM\",\n      \"end_time\": \"09:00 AM\",\n      \"zone_type\": \"maintenance\",\n      \"purpose\": \"Gentle activation and preparation for the day\",\n      \"tasks\": [\n        {{\n          \"start_time\": \"06:00 AM\",\n          \"end_time\": \"06:30 AM\",\n          \"title\": \"Morning hydration\",\n          \"description\": \"Start with a glass of water and light stretching\",\n          \"task_type\": \"wellness\",\n          \"category\": \"hydration\",\n          \"priority\": \"high\"\n        }},\n        {{\n          \"start_time\": \"06:30 AM\",\n          \"end_time\": \"07:00 AM\",\n          \"title\": \"Balanced breakfast\",\n          \"description\": \"Nutritious meal with protein and complex carbs\",\n          \"task_type\": \"nutrition\",\n          \"category\": \"nutrition\",\n          \"priority\": \"high\"\n        }}\n      ]\n    }}\n  ]\n}}\n\nNOTE: Each task MUST have both start_time and end_time within the parent block's time range. Sequential scheduling with no overlaps."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.3 if markdown_plan else 0.2,
            max_tokens=2000
        )

        # Parse the JSON response
        content = response.choices[0].message.content
        try:
            structured_data = json.loads(content)

            # === VALIDATION: Check if AI provided times for all tasks ===
            missing_times_count = 0
            invalid_format_count = 0
            total_tasks_count = 0

            # Regex to detect invalid mixed format (24-hour with AM/PM)
            import re
            invalid_time_pattern = re.compile(r'\b(1[3-9]|2[0-3]):[0-5][0-9]\s*(AM|PM)\b', re.IGNORECASE)

            if "time_blocks" in structured_data:
                for block in structured_data["time_blocks"]:
                    if "tasks" in block:
                        for task in block["tasks"]:
                            total_tasks_count += 1
                            start_time = task.get("start_time", "")
                            end_time = task.get("end_time", "")

                            # Check if times exist
                            if not start_time or not end_time:
                                missing_times_count += 1
                                logger.warning(f"[TIME-VALIDATION] Task missing times: '{task.get('title', 'Unknown')}' in block '{block.get('block_name', 'Unknown')}'")
                            # Check if times are in invalid format (e.g., "13:00 PM")
                            elif invalid_time_pattern.search(start_time) or invalid_time_pattern.search(end_time):
                                invalid_format_count += 1
                                logger.error(f"[TIME-VALIDATION] ❌ INVALID TIME FORMAT: '{task.get('title', 'Unknown')}' has invalid times: {start_time} - {end_time}")
                                logger.error(f"[TIME-VALIDATION]    Invalid format detected: Cannot mix 24-hour (13-23) with AM/PM")
                                logger.error(f"[TIME-VALIDATION]    Time inference will override these times")

            if invalid_format_count > 0:
                logger.error(f"[TIME-VALIDATION] ❌ AI generated {invalid_format_count}/{total_tasks_count} tasks with INVALID TIME FORMATS - time inference will override")

            if missing_times_count > 0:
                logger.error(f"[TIME-VALIDATION] AI generated {missing_times_count}/{total_tasks_count} tasks WITHOUT times - time inference will fill gaps")

            if invalid_format_count == 0 and missing_times_count == 0:
                logger.info(f"[TIME-VALIDATION] ✅ All {total_tasks_count} tasks have valid time data")

        except json.JSONDecodeError:
            logger.error(f"[ERROR] Failed to parse JSON response from GPT-4: {content[:500]}")
            # Fallback to text content
            structured_data = {"content": content}

        # === SAFETY VALIDATION: Check generated plan for prohibited content ===
        user_id_for_logging = user_context.get('user_id', 'unknown') if isinstance(user_context, dict) else 'unknown'
        is_safe, violations = safety_validator.validate_plan(structured_data, user_id_for_logging)

        if not is_safe:
            logger.warning(f"[SAFETY] [{user_id_for_logging[:8]}] Plan contains {len(violations)} safety violation(s)")

            # Log violations for monitoring
            for violation in violations:
                logger.warning(f"[SAFETY]   - {violation.category}: {violation.location}")

            # If BLOCK_UNSAFE_PLANS is true, sanitize the plan
            if safety_validator.block_unsafe:
                logger.info(f"[SAFETY] Sanitizing plan to remove violations...")
                structured_data = safety_validator.sanitize_plan(structured_data, violations)
                logger.info(f"[SAFETY] Plan sanitized successfully")

        from shared_libs.utils.timezone_helper import get_user_local_date

        return {
            "date": get_user_local_date(user_timezone),
            "archetype": archetype,
            "content": json.dumps(structured_data),  # Store as JSON string
            "model_used": "gpt-4o",
            "plan_type": "comprehensive_routine",
            "safety_validated": is_safe,  # NEW: Track validation status
            "safety_violations": len(violations) if violations else 0,  # NEW: Track violation count
            "system": "HolisticOS",
            "readiness_mode": readiness_level,
            "structured_format": True  # Flag indicating this uses new format
        }

    except Exception as e:
        from shared_libs.utils.timezone_helper import get_user_local_date
        logger.error(f"Error in routine planning: {e}")
        return {
            "error": str(e),
            "model_used": "gpt-4o - fallback",
            "archetype": archetype,
            "date": get_user_local_date(user_timezone)
        }

# =====================================================================
# LEGACY ENDPOINT - PRESERVED FOR BACKWARD COMPATIBILITY
# =====================================================================

# Import legacy endpoint
try:
    from .legacy.legacy_analyze_endpoint import legacy_analyze_user, AnalysisRequest, AnalysisResponse
    
    @app.post("/api/analyze", response_model=AnalysisResponse)
    @track_endpoint_metrics("legacy_analysis") if MONITORING_AVAILABLE else lambda x: x
    async def analyze_user_legacy_wrapper(request: AnalysisRequest, http_request: Request):
        """
        LEGACY ENDPOINT - PRESERVED FOR BACKWARD COMPATIBILITY
        
        This endpoint has been moved to services/api_gateway/legacy/ and is no longer actively maintained.
        
        [WARNING]  DEPRECATED: Please migrate to modern endpoints:
        - POST /api/user/{user_id}/behavior/analyze
        - POST /api/user/{user_id}/routine/generate  
        - POST /api/user/{user_id}/nutrition/generate
        
        The modern endpoints provide:
        - Better performance with 50-item threshold logic
        - Improved caching and memory management
        - More focused analysis results
        - Better error handling and monitoring
        """
        return await legacy_analyze_user(request, http_request)
    
    print("[LEGACY] Legacy /api/analyze endpoint loaded from legacy folder")
    
except ImportError as e:
    pass
    
    @app.post("/api/analyze", response_model=AnalysisResponse)
    async def analyze_user_fallback(request: AnalysisRequest, http_request: Request):
        """Fallback for legacy endpoint when legacy module is not available"""
        raise HTTPException(
            status_code=503, 
            detail="Legacy endpoint temporarily unavailable. Please use modern endpoints: POST /api/user/{user_id}/behavior/analyze"
        )
