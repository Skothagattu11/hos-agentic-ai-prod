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
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
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
    description="Multi-Agent Health Optimization System with Memory, Insights, and Adaptation"
)

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

cors_config = get_cors_config()
# Manual override to ensure X-API-Key header is allowed (temporary fix)
cors_config['allow_headers'] = cors_config.get('allow_headers', []) + ['X-API-Key']
app.add_middleware(
    CORSMiddleware,
    **cors_config
)

# Add production error handling middleware (first in chain)
app.middleware("http")(production_error_handler)

# Add input validation middleware (lightweight, non-breaking)  
app.middleware("http")(validate_request_middleware)

# Add request size limit middleware
app.add_middleware(RequestSizeLimit, max_size=2 * 1024 * 1024)  # 2MB limit

# Configure rate limiting
if RATE_LIMITING_AVAILABLE:
    # Add rate limiter to app state
    app.state.limiter = rate_limiter.limiter
    
    # Add exception handler for rate limits
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Add middleware for rate limit headers and context
    app.middleware("http")(add_rate_limit_context_middleware)
    app.middleware("http")(rate_limit_middleware)
    
        # # Production: Verbose print removed  # Commented to reduce noise

# Integrate Phase 2 Health Data Endpoints - CTO Integration
try:
    from .health_data_endpoints import router as health_data_router
    app.include_router(health_data_router)
        # # Production: Verbose print removed  # Commented to reduce noise
    # print("📡 [ENDPOINTS] Real user data endpoints now available:")  # Commented for error-only mode
except ImportError as e:
    pass  # Health data endpoints not available
except Exception as e:
    print(f"❌ [ERROR] Failed to integrate health data endpoints: {e}")

# Integrate Insights Endpoints
        # # Production: Verbose print removed  # Commented to reduce noise
try:
    from .insights_endpoints import router as insights_router
        # # Production: Verbose print removed  # Commented to reduce noise
    app.include_router(insights_router)
        # # Production: Verbose print removed  # Commented to reduce noise
except Exception as e:
    print(f"❌ [ERROR] Failed to integrate insights endpoints: {e}")

# Integrate User Engagement Endpoints - TEMPORARILY DISABLED FOR OPENAPI FIX
try:
    from .engagement_endpoints import router as engagement_router
    app.include_router(engagement_router)
    # Production: Verbose print removed
    print("  - POST /api/v1/engagement/task-checkin")
    print("  - GET /api/v1/engagement/tasks/{profile_id}")
    print("  - POST /api/v1/engagement/journal")
    print("  - POST /api/v1/engagement/extract-plan-items")
except ImportError as e:
    pass  # Engagement endpoints not available
except Exception as e:
    print(f"❌ [ERROR] Failed to integrate engagement endpoints: {e}")

# Integrate Calendar Selection Endpoints
try:
    from .calendar_endpoints import router as calendar_router
    app.include_router(calendar_router)
    # Production: Verbose print removed
    print("  - GET /api/calendar/available-items/{profile_id}")
except Exception as e:
    print(f"❌ [ERROR] Failed to integrate calendar selection endpoints: {e}")

# Integrate Archetype Management Endpoints
try:
    from .archetype_router import router as archetype_router
    app.include_router(archetype_router, prefix="/api")
    # Production: Verbose print removed
    print("  - GET /api/user/{user_id}/available-archetypes")
    print("  - GET /api/user/{user_id}/archetype/{analysis_id}/summary")
except Exception as e:
    print(f"❌ [ERROR] Failed to integrate archetype management endpoints: {e}")

# Integrate Admin API Endpoints
try:
    from .admin_apis import register_admin_routes
    register_admin_routes(app)
    # Production: Verbose print removed
    print("  - GET /api/admin/users")
    print("  - GET /api/admin/user/{user_id}/overview")
    print("  - GET /api/admin/user/{user_id}/analysis-data")
except ImportError as e:
    pass  # Admin API endpoints not available
except Exception as e:
    print(f"❌ [ERROR] Failed to integrate admin API endpoints: {e}")
    print("Full traceback:")
    traceback.print_exc()

# Integrate Analysis Results Endpoints
try:
    from .analysis_results_endpoints import router as analysis_router
    app.include_router(analysis_router)
    # Production: Verbose print removed
    print("  - GET /api/v1/analysis/user/{user_id}/results")
    print("  - GET /api/v1/analysis/user/{user_id}/latest-with-data")
    print("  - GET /api/v1/analysis/result/{analysis_id}/status")
    print("  - POST /api/v1/analysis/user/{user_id}/extract-latest")
except ImportError as e:
    pass  # Analysis results endpoints not available
except Exception as e:
    print(f"❌ [ERROR] Failed to integrate analysis results endpoints: {e}")

# 🔥 ENERGY ZONES SERVICE INTEGRATION
try:
    # Import the energy zones router from the api directory
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../api'))
    from energy_zones_endpoints import router as energy_zones_router
    app.include_router(energy_zones_router)
    # Production: Verbose print removed
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
    print(f"❌ [ERROR] Failed to integrate Energy Zones Service endpoints: {e}")

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

class RoutinePlanResponse(BaseModel):
    status: str
    user_id: str
    routine_plan: Dict[str, Any]
    generation_metadata: Dict[str, Any]
    cached: bool = False

class NutritionPlanResponse(BaseModel):
    status: str
    user_id: str
    nutrition_plan: Dict[str, Any]
    generation_metadata: Dict[str, Any]
    cached: bool = False

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
        # print("🚀 Initializing HolisticOS Multi-Agent System...")  # Commented for error-only mode
        
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
        print(f"❌ Error initializing agents: {e}")
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
        print("🛑 Shutting down HolisticOS Multi-Agent System...")
        
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
        print(f"❌ Error during shutdown: {e}")

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
            # Test database connectivity if available
            from services.agents.memory.holistic_memory_service import HolisticMemoryService
            memory_service = HolisticMemoryService()
            # Quick ping test (with short timeout)
            db_healthy = await asyncio.wait_for(memory_service._test_connection(), timeout=2.0)
            health_status["services"]["database"] = "operational" if db_healthy else "degraded"
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
        
        # Get latest behavior analysis from memory
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        memory_service = HolisticMemoryService()
        
        try:
            # Get most recent analysis that includes routine plan
            analysis_history = await memory_service.get_analysis_history(user_id, limit=3)
            
            # Find most recent analysis with routine plan
            routine_plan = None
            behavior_analysis = None
            
            for analysis in analysis_history:
                analysis_result = analysis.analysis_result
                if isinstance(analysis_result, dict) and 'routine_plan' in analysis_result:
                    routine_plan = analysis_result['routine_plan']
                    behavior_analysis = analysis_result.get('behavior_analysis', {})
                    break
            
            if not routine_plan:
                return RoutinePlanResponse(
                    status="not_found",
                    user_id=user_id,
                    routine_plan={},
                    generation_metadata={
                        "error": "No recent routine plan found. Please run a behavior analysis first.",
                        "suggestion": "Use POST /api/analyze to generate initial analysis"
                    },
                    cached=False
                )
            
            # Return cached routine with metadata
            return RoutinePlanResponse(
                status="success",
                user_id=user_id,
                routine_plan=routine_plan,
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
        print(f"❌ [ROUTINE_API_ERROR] Failed to get routine for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve routine plan: {str(e)}")

# =====================================================================
# SIMPLE CONSOLIDATED ENDPOINT
# =====================================================================

@app.get("/api/user/{user_id}/plans/{date}")
async def get_user_plans_for_date(user_id: str, date: str):
    """Simple endpoint: Get routine plan and extract time blocks for calendar"""
    try:
        from shared_libs.database.supabase_async_pg_adapter import SupabaseAsyncPGAdapter
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
        from shared_libs.database.supabase_async_pg_adapter import SupabaseAsyncPGAdapter
        from shared_libs.services.memory_service import MemoryManagementService
        
        # Validate date format
        try:
            from datetime import datetime
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Date must be in YYYY-MM-DD format")
        
        # Initialize services
        adapter = SupabaseAsyncPGAdapter()
        memory_service = MemoryManagementService(adapter)
        
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
        print(f"❌ [ROUTINE_DATE_API_ERROR] Failed to get routine for {user_id} on {date}: {e}")
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
        print(f"🔒 [AUTH_FAILED] Invalid or missing API key for user {user_id[:8]}... Provided: {api_key}")
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    if IS_DEVELOPMENT:
        print(f"🔑 [AUTH_SUCCESS] Valid client API key provided for user {user_id[:8]}...")
    
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
                pass  # # Production: Verbose print removed
                raise rate_limit_error
        # print(f"🔄 [ROUTINE_GENERATE] Processing routine request for user {user_id[:8]}...")  # Commented to reduce noise

        # Get behavior analysis from the standalone endpoint
        force_refresh = request.preferences.get('force_refresh', False) if request.preferences else False
        archetype = request.archetype or "Foundation Builder"

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
        print(f"🔄 [ROUTINE_GENERATE] Running parallel behavior + circadian analysis for dynamic planning...")

        # Run both analyses in parallel using same raw data
        import asyncio
        behavior_task = get_or_create_shared_behavior_analysis(user_id, archetype, force_refresh, analysis_number)
        circadian_task = get_or_create_shared_circadian_analysis(user_id, archetype, force_refresh, analysis_number)

        try:
            behavior_analysis, circadian_analysis = await asyncio.gather(
                behavior_task, circadian_task, return_exceptions=True
            )
        except Exception as e:
            print(f"❌ [ROUTINE_GENERATE] Parallel analysis failed: {e}")
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

        if not behavior_success:
            print(f"❌ [ROUTINE_GENERATE] Behavior analysis failed: {behavior_analysis}")
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
        # Production: Verbose print removed
        # Production: Verbose print removed
        # Production: Verbose print removed

        # DETAILED LOGGING: Log raw data and analysis outputs for agent handoff tracking
        try:
            import json
            import os

            # Create handoff logs directory
            # handoff_dir = "logs/agent_handoffs"  # Production: Disabled
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

            # Production: Verbose print removed

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
                print(f"🔒 [RACE_CONDITION_FIX] Using locked timestamp for routine data fetch")
                user_context, _ = await user_service.get_analysis_data(user_id, locked_timestamp)
            else:
        # # Production: Verbose print removed  # Commented to reduce noise
                user_context, _ = await user_service.get_analysis_data(user_id)

            # RAW DATA LOGGING: Log the actual health data that goes into analysis
            try:
                import os
                import json

                # handoff_dir = "logs/agent_handoffs"  # Production: Disabled
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

            # Use the memory-enhanced routine generation function with combined parallel analysis
            routine_plan = await run_memory_enhanced_routine_generation(
                user_id=user_id,
                archetype=archetype,
                behavior_analysis=behavior_analysis,
                circadian_analysis=circadian_analysis if circadian_success else None,
                combined_analysis=combined_analysis
            )

            # FINAL AGENT HANDOFF: Log the combined analysis → routine generation transformation
            try:
                import os
                import json

                # handoff_dir = "logs/agent_handoffs"  # Production: Disabled
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

                # Production: Verbose print removed

            except Exception as log_error:
                pass  # Routine generation logging failed

            # STORE PLAN ITEMS: Extract and store plan items for active plan display
            try:
                from services.plan_extraction_service import PlanExtractionService
                
                # Find the most recent behavior analysis ID to associate plan items
                from services.agents.memory.holistic_memory_service import HolisticMemoryService
                memory_service = HolisticMemoryService()
                analysis_history = await memory_service.get_analysis_history(user_id, analysis_type="behavior_analysis", limit=1)
                
                if analysis_history and routine_plan:
                    analysis_result_id = str(analysis_history[0].id)
                    print(f"📝 [PLAN_STORAGE] Storing plan items for analysis_result_id: {analysis_result_id}")
                    
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
                        # Production: Verbose print removed
                    
                await memory_service.cleanup()
                    
            except Exception as storage_error:
                pass  # # Production: Verbose print removed
                # Don't fail the entire request if plan storage fails
            
            # ARCHETYPE-SPECIFIC TRACKING: Timestamp updates now handled by HolisticMemoryService
            # when storing behavior analysis results - no need for global timestamp update
            
            # Track API cost for rate limiting
            if RATE_LIMITING_AVAILABLE:
                try:
                    await rate_limiter.track_api_cost(user_id, "routine_generation")
                except Exception as cost_error:
                    pass  # # Production: Verbose print removed
            
            # Mark request as complete
            request_deduplicator.mark_request_complete(user_id, archetype, "routine")

            # Prepare response data
            response_data = RoutinePlanResponse(
                status="success",
                user_id=user_id,
                routine_plan=routine_plan,
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
            pass  # # Production: Verbose print removed
            raise HTTPException(status_code=500, detail=f"Failed to get user data for routine generation: {str(context_error)}")
            
    except Exception as e:
        # Mark request as complete even on error
        request_deduplicator.mark_request_complete(user_id, archetype, "routine")
        print(f"❌ [ROUTINE_GENERATE_ERROR] Failed to generate routine for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate routine plan: {str(e)}")

@app.get("/api/user/{user_id}/nutrition/latest", response_model=NutritionPlanResponse)
async def get_latest_nutrition_plan(user_id: str):
    """
    Get the most recent nutrition plan based on latest behavior analysis
    Fast endpoint - uses cached analysis results
    """
    try:
        # print(f"🥗 [NUTRITION_API] Getting latest nutrition for user {user_id[:8]}...")  # Commented to reduce noise
        
        # Get latest behavior analysis from memory
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
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
        print(f"❌ [NUTRITION_API_ERROR] Failed to get nutrition for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve nutrition plan: {str(e)}")

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
                pass  # # Production: Verbose print removed
                raise rate_limit_error
        # print(f"🔄 [NUTRITION_GENERATE] Processing nutrition request for user {user_id[:8]}...")  # Commented to reduce noise
        
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
                print(f"🔒 [RACE_CONDITION_FIX] Using locked timestamp for nutrition data fetch")
                user_context, _ = await user_service.get_analysis_data(user_id, locked_timestamp)
            else:
        # # Production: Verbose print removed  # Commented to reduce noise
                user_context, _ = await user_service.get_analysis_data(user_id)
            
            # Generate nutrition using existing function
            from shared_libs.utils.system_prompts import get_system_prompt
            from services.agents.memory.enhanced_memory_prompts import EnhancedMemoryPromptsService
            
            enhanced_prompts_service = EnhancedMemoryPromptsService()
            base_nutrition_prompt = get_system_prompt("plan_generation")
            enhanced_nutrition_prompt = await enhanced_prompts_service.enhance_agent_prompt(
                base_nutrition_prompt, user_id, "nutrition_planning"
            )
            
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
                    pass  # # Production: Verbose print removed
            
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
            pass  # # Production: Verbose print removed
            raise HTTPException(status_code=500, detail=f"Failed to get user data for nutrition generation: {str(context_error)}")

            
    except Exception as e:
        # Mark request as complete even on error
        request_deduplicator.mark_request_complete(user_id, archetype, "nutrition")
        print(f"❌ [NUTRITION_GENERATE_ERROR] Failed to generate nutrition for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate nutrition plan: {str(e)}")

@app.get("/api/user/{user_id}/insights/latest")
async def get_latest_insights(user_id: str):
    """Get latest AI insights for user - Phase 4.2 Sprint 3"""
    try:
        # # Production: Verbose print removed  # Commented to reduce noise
        
        # Get latest analysis with insights from memory
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
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
        print(f"❌ [INSIGHTS_API_ERROR] Failed to get insights for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve insights: {str(e)}")

@app.post("/api/user/{user_id}/insights/generate")
async def generate_fresh_insights(user_id: str, request: dict):
    """Generate fresh insights on-demand - Phase 4.2 Sprint 3"""
    try:
        print(f"✨ [INSIGHTS_GENERATE] Generating fresh insights for user {user_id[:8]}...")
        
        # Get latest behavior analysis as context
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
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
        print(f"❌ [INSIGHTS_GENERATE_ERROR] Failed to generate insights for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@app.post("/api/user/{user_id}/insights/{insight_id}/feedback")
async def provide_insight_feedback(user_id: str, insight_id: str, feedback: dict):
    """Allow users to provide feedback on insights quality - Phase 4.2 Sprint 3"""
    try:
        print(f"📝 [INSIGHTS_FEEDBACK] Recording feedback for insight {insight_id} from user {user_id[:8]}...")
        
        # Store feedback in memory system for future improvement
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
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
        print(f"❌ [INSIGHTS_FEEDBACK_ERROR] Failed to record feedback: {e}")
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
            pass  # # Production: Verbose print removed
            raise rate_limit_error

    try:
        # print(f"🧠 [BEHAVIOR_ANALYZE] Starting behavior analysis for user {user_id[:8]}...")  # Commented for error-only mode

        # Import required services
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        from services.mvp_style_logger import mvp_logger

        # Initialize services
        ondemand_service = await get_ondemand_service()
        memory_service = HolisticMemoryService()

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
        decision, metadata = await ondemand_service.should_run_analysis(user_id, request.force_refresh, request.archetype)

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
            print(f"🚀 [BEHAVIOR_ANALYZE] Running fresh behavior analysis...")

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
                
                # Store the analysis in memory system for future use
                await memory_service.store_analysis_result(
                    user_id=user_id,
                    analysis_type="behavior_analysis",
                    analysis_result=behavior_analysis,
                    archetype_used=archetype,
                    analysis_trigger=analysis_trigger
                )
        # # Production: Verbose print removed  # Commented to reduce noise
            else:
                # Fallback to cached if fresh analysis fails
                # Production: Verbose print removed
                behavior_analysis = await ondemand_service.get_cached_behavior_analysis(user_id, archetype)
                analysis_type = "cached_fallback"
                
        else:
            # Use cached analysis
            print(f"💾 [BEHAVIOR_ANALYZE] Using cached analysis (below threshold)")
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
                pass  # # Production: Verbose print removed

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
        print(f"❌ [BEHAVIOR_ANALYZE_ERROR] Failed to analyze behavior for {user_id}: {e}")
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
    # API key validation (same pattern as other endpoints)
    api_key = http_request.headers.get("X-API-Key")
    if api_key != "hosa_flutter_app_2024":
        print(f"🔒 [AUTH_FAILED] Invalid or missing API key for circadian analysis {user_id[:8]}... Provided: {api_key}")
        raise HTTPException(status_code=401, detail="User not authenticated")

    if IS_DEVELOPMENT:
        print(f"🔑 [AUTH_SUCCESS] Valid client API key provided for circadian analysis {user_id[:8]}...")

    try:
        # Apply rate limiting if available
        if RATE_LIMITING_AVAILABLE:
            try:
                await rate_limiter.apply_rate_limit(http_request, "circadian_analysis")
            except Exception as rate_limit_error:
                pass  # # Production: Verbose print removed
                raise rate_limit_error

        # Production: Verbose print removed  # Enabled for detailed logging

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
                pass  # # Production: Verbose print removed

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
        print(f"❌ [CIRCADIAN_ANALYZE_ERROR] Failed to analyze circadian rhythm for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze circadian rhythm: {str(e)}")


async def run_complete_health_analysis(user_id: str, archetype: str) -> dict:
    """
    Complete health analysis with automatic insights generation - Phase 4.2 Sprint 3
    Used by scheduler and on-demand analysis requests
    Integrates insights agent into the main analysis pipeline
    """
    try:
        print(f"🚀 Starting complete health analysis with insights for {user_id}...")
        
        # Run the main analysis using existing analyze_user function
        request = AnalysisRequest(user_id=user_id, archetype=archetype)
        analysis_response = await analyze_user(request)
        
        if analysis_response.status != "success":
            print(f"❌ Main analysis failed: {analysis_response.message}")
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
                # Production: Verbose print removed
                insights = {"error": insights_result.error_message}
                
        except Exception as insights_error:
            pass  # # Production: Verbose print removed
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
        print(f"❌ Complete health analysis failed for {user_id}: {e}")
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
        print(f"🧠 [BEHAVIOR_WRAPPER] Starting DIRECT behavior analysis for {user_id[:8]}...")
        # Production: Verbose print removed
        
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
        print("🧠 Running standalone behavior analysis with o3 model...")
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
            print(f"❌ [BEHAVIOR_WRAPPER] Behavior analysis failed - no result")
            return {
                "status": "error",
                "error": "Behavior analysis returned no result",
                "behavior_analysis": {}
            }
            
    except Exception as e:
        print(f"❌ [BEHAVIOR_WRAPPER] Error in behavior analysis: {e}")
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
    """Run circadian rhythm analysis using GPT-4o model - Phase 2"""
    try:
        client = openai.AsyncOpenAI()

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\nYou are an expert circadian rhythm analyst. Focus on identifying sleep-wake patterns, energy fluctuations, and optimal timing for activities based on biomarker data."
                },
                {
                    "role": "user",
                    "content": f"""
{user_context}

Analyze the circadian rhythm patterns from the biomarker data and provide comprehensive insights following the HolisticOS framework.

Focus on:
- Sleep-wake cycle patterns and consistency
- Energy level fluctuations throughout the day
- Optimal timing windows for different activities
- Chronotype assessment and recommendations
- Integration opportunities with existing routines

Provide structured JSON output with chronotype_assessment, energy_zone_analysis, schedule_recommendations, and biomarker_insights sections.
                """
                }
            ],
            temperature=0.2,  # Lower temperature for more consistent circadian analysis
            max_tokens=3000,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        # Parse JSON response
        try:
            analysis_data = json.loads(content)
            analysis_data["model_used"] = "gpt-4o"
            analysis_data["analysis_type"] = "circadian_rhythm"
            analysis_data["analysis_timestamp"] = datetime.now().isoformat()
            return analysis_data
        except json.JSONDecodeError as e:
            print(f"JSON parse error in circadian analysis: {e}")
            return {
                "chronotype_assessment": {
                    "primary_type": "intermediate",
                    "confidence_score": 0.7,
                    "assessment_basis": "Limited data available"
                },
                "energy_zone_analysis": {
                    "peak_energy_window": "09:00-11:00",
                    "low_energy_window": "14:00-16:00",
                    "recovery_window": "22:00-06:00"
                },
                "schedule_recommendations": {
                    "optimal_wake_time": "07:00",
                    "optimal_sleep_time": "23:00",
                    "workout_window": "08:00-10:00"
                },
                "analysis_content": content,
                "model_used": "gpt-4o",
                "analysis_type": "circadian_rhythm"
            }

    except Exception as e:
        print(f"Error in GPT-4o circadian analysis: {e}")
        return {
            "error": str(e),
            "model_used": "gpt-4o - fallback",
            "chronotype_assessment": {"primary_type": "unknown", "confidence_score": 0.3}
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
        # print(f"🧠 [MEMORY_ENHANCED] Starting memory-enhanced behavior analysis for {user_id[:8]}...")  # Commented for error-only mode
        
        # Import memory integration service
        from services.memory_integration_service import MemoryIntegrationService
        
        # Initialize memory integration service
        memory_service = MemoryIntegrationService()
        
        # Step 1: Prepare memory-enhanced context
        # # Production: Verbose print removed  # Commented to reduce noise
        memory_context = await memory_service.prepare_memory_enhanced_context(user_id, None, archetype)
        
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
        
        # print(f"🧠 [MEMORY_ENHANCED] Enhanced prompt with memory context (+{len(enhanced_prompt) - len(system_prompt)} chars)")  # Commented for error-only mode
        
        # Step 4: Prepare behavior agent data with memory context
        user_context_summary = await format_health_data_for_ai(user_context)
        
        
        
        behavior_data = await prepare_behavior_agent_data(user_context, user_context_summary)
        
        # Step 5: Run behavior analysis with memory-enhanced prompt
        analysis_result = await run_behavior_analysis_o3(enhanced_prompt, user_context_summary)
        
        # Step 6: Store analysis insights using same method as /api/analyze
        # print(f"💾 [MEMORY_ENHANCED] Storing analysis insights like /api/analyze...")  # Commented for error-only mode
        insights_stored = False
        try:
            # Use the same storage method as /api/analyze (line 1523)
            await memory_service.store_analysis_insights(user_id, "behavior_analysis", analysis_result, archetype)
            insights_stored = True
        # # Production: Verbose print removed  # Commented to reduce noise
        except Exception as e:
            pass  # # Production: Verbose print removed
        
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
        print(f"❌ [MEMORY_ENHANCED] Error in memory-enhanced behavior analysis: {e}")
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
            # Production: Verbose print removed
            return cached_result
        
        # ENHANCED THRESHOLD CHECK: Additional safety before proceeding
        if not force_refresh:
            from services.agents.memory.holistic_memory_service import HolisticMemoryService
            from services.ondemand_analysis_service import get_ondemand_service
            
            memory_service = HolisticMemoryService()
            try:
                # Get most recent behavior analysis for this archetype
                recent_analyses = await memory_service.get_analysis_history(
                    user_id, 
                    analysis_type="behavior_analysis", 
                    archetype=archetype, 
                    limit=1
                )
                
                if recent_analyses:
                    latest_analysis = recent_analyses[0]
                    
                    # Check if threshold exceeded SINCE this analysis was created
                    ondemand_service = await get_ondemand_service()
                    new_data_since_analysis = await ondemand_service._count_new_data_points(
                        user_id, latest_analysis.created_at
                    )
                    
                    # If threshold not exceeded since last analysis, reuse it
                    if new_data_since_analysis < 50:  # Threshold not met
                        # Production: Verbose print removed
                        await memory_service.cleanup()
                        # Complete coordination with the result
                        enhanced_deduplicator.complete_request(user_id, archetype, "behavior_analysis", latest_analysis.analysis_result)
                        return latest_analysis.analysis_result
                    else:
                        print(f"🔄 [SHARED_ANALYSIS] Threshold exceeded since last analysis ({new_data_since_analysis} >= 50) - creating fresh for {archetype}")
                
                await memory_service.cleanup()
            except Exception as e:
                pass  # # Production: Verbose print removed
        
        # Step 1: Check if fresh analysis needed (50-item threshold logic WITH ARCHETYPE)
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        ondemand_service = await get_ondemand_service()
        decision, metadata = await ondemand_service.should_run_analysis(user_id, force_refresh, archetype)
        
        # Enhanced debugging for threshold issues
        decision_str = decision.value if hasattr(decision, 'value') else str(decision)
        new_data = metadata.get('new_data_points', 0)
        threshold = metadata.get('threshold_used', 50)
        
        # # Production: Verbose print removed  # Commented for error-only mode
        # # Production: Verbose print removed  # Commented to reduce noise
        # print(f"   📈 New Data Points: {new_data}")  # Commented for error-only mode
        # # Production: Verbose print removed  # Commented for error-only mode
        # print(f"   💾 Memory Quality: {metadata.get('memory_quality', 'unknown')}")  # Commented for error-only mode
        # print(f"   ⏰ Hours Since Last: {metadata.get('hours_since_analysis', 0):.1f}")  # Commented for error-only mode
        # # Production: Verbose print removed  # Commented for error-only mode
        
        logger.debug(f"[SHARED_ANALYSIS] {user_id[:8]}... Decision: {decision_str}, Data: {new_data}/{threshold}")
        
        # Step 2: Use cached if sufficient (only for MEMORY_ENHANCED_CACHE decision)
        if decision == AnalysisDecision.MEMORY_ENHANCED_CACHE:
            # print(f"💾 [THRESHOLD_DEBUG] Decision is MEMORY_ENHANCED_CACHE - fetching cached analysis...")  # Commented for error-only mode
            # Use OnDemandAnalysisService's archetype-aware cache retrieval
            cached_analysis = await ondemand_service.get_cached_behavior_analysis(user_id, archetype)
            if cached_analysis:
        # # Production: Verbose print removed  # Commented to reduce noise
                print(f"   📝 Cache contains: {len(str(cached_analysis))} characters")
                logger.debug(f"[SHARED_ANALYSIS] {user_id[:8]}... Using cached analysis")
                # Complete coordination with cached result
                enhanced_deduplicator.complete_request(user_id, archetype, "behavior_analysis", cached_analysis)
                return cached_analysis
            else:
                print(f"❌ [THRESHOLD_DEBUG] No cached analysis found - falling back to fresh")
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
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
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
            # Production: Verbose print removed
            return cached_result

        # ENHANCED THRESHOLD CHECK: Additional safety before proceeding
        if not force_refresh:
            from services.agents.memory.holistic_memory_service import HolisticMemoryService
            from services.ondemand_analysis_service import get_ondemand_service

            memory_service = HolisticMemoryService()
            try:
                # Get most recent circadian analysis for this archetype
                recent_analyses = await memory_service.get_analysis_history(
                    user_id,
                    analysis_type="circadian_analysis",
                    archetype=archetype,
                    limit=1
                )

                if recent_analyses:
                    latest_analysis = recent_analyses[0]

                    # Check if threshold exceeded SINCE this analysis was created
                    ondemand_service = await get_ondemand_service()
                    new_data_since_analysis = await ondemand_service._count_new_data_points(
                        user_id, latest_analysis.created_at
                    )

                    # If threshold not exceeded since last analysis, reuse it
                    if new_data_since_analysis < 50:  # Threshold not met
                        # Production: Verbose print removed

                        # Result already cached in database - no additional caching needed

                        return latest_analysis.analysis_result

                await memory_service.cleanup()

            except Exception as threshold_error:
                pass  # # Production: Verbose print removed
                # Continue with fresh analysis on error

        # FRESH ANALYSIS: Threshold exceeded or force_refresh requested
        # Production: Verbose print removed
        # Production: Verbose print removed
        # Production: Verbose print removed
        print(f"   🧠 [MEMORY] Integrating 4-layer memory system for personalized analysis")

        # Use OnDemandAnalysisService to get proper metadata
        from services.ondemand_analysis_service import get_ondemand_service
        ondemand_service = await get_ondemand_service()
        should_run, ondemand_metadata = await ondemand_service.should_run_analysis(
            user_id, force_refresh=force_refresh
        )

        if not should_run and not force_refresh:
            # Production: Verbose print removed
            return {"status": "skipped", "reason": "threshold_not_met", "circadian_analysis": {}}

        # Run memory-enhanced circadian analysis
        circadian_result = await run_memory_enhanced_circadian_analysis(user_id, archetype)

        # Note: Analysis completion is tracked via database storage and coordination service
        # await ondemand_service.mark_analysis_complete(user_id)  # Method not available

        # Result stored in database - no additional caching needed

        # Production: Verbose print removed
        return circadian_result

    except Exception as e:
        print(f"❌ [SHARED_CIRCADIAN] Error in shared circadian analysis: {e}")
        await enhanced_deduplicator.mark_request_failed(user_id, archetype, "circadian_analysis")
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
        # EXACT same imports as /api/analyze (lines 1246-1249)
        from services.memory_integration_service import MemoryIntegrationService
        from services.agents.memory.enhanced_memory_prompts import EnhancedMemoryPromptsService  
        from services.user_data_service import UserDataService
        from services.simple_analysis_tracker import SimpleAnalysisTracker as AnalysisTracker
        from shared_libs.utils.system_prompts import get_system_prompt
        
        # EXACT same service initialization as /api/analyze (lines 1252-1257)
        user_service = UserDataService()
        analysis_tracker = AnalysisTracker()
        memory_service = MemoryIntegrationService()
        enhanced_prompts_service = EnhancedMemoryPromptsService()
        
        try:
            # Use OnDemandAnalysisService metadata for memory context preparation
            memory_context = await memory_service.prepare_memory_enhanced_context(user_id, ondemand_metadata, archetype)
            
            # CRITICAL FIX: Pass locked timestamp to prevent race conditions
            locked_timestamp = ondemand_metadata.get('fixed_timestamp') if ondemand_metadata else None
            if locked_timestamp:
                print(f"🔒 [RACE_CONDITION_FIX] Using locked timestamp from OnDemandAnalysisService")
                user_context, latest_data_timestamp = await user_service.get_analysis_data(user_id, locked_timestamp, analysis_number)
            else:
        # # Production: Verbose print removed  # Commented to reduce noise
                user_context, latest_data_timestamp = await user_service.get_analysis_data(user_id, None, analysis_number)
            
            # EXACT same prompt enhancement as /api/analyze (lines 1282-1289)
            base_behavior_prompt = get_system_prompt("behavior_analysis")
            behavior_prompt = await enhanced_prompts_service.enhance_agent_prompt(base_behavior_prompt, user_id, "behavior_analysis")
            
            # EXACT same context summary creation as /api/analyze (lines 1324-1348)
            user_context_summary = await create_context_summary_like_api_analyze(user_context, memory_context, archetype, user_id)
            
            # EXACT same behavior analysis execution as /api/analyze (lines 1382-1386)  
            # Note: Removed complex logging infrastructure to focus on core functionality
            behavior_agent_data = await prepare_behavior_agent_data(user_context, user_context_summary)
            behavior_analysis = await run_behavior_analysis_o3(behavior_prompt, user_context_summary)
            # Note: Agent handoff logging removed - focus on core functionality
            
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
                print(f"🔒 [RACE_CONDITION_FIX] Added OnDemand metadata to behavior analysis result")
            
            return behavior_analysis
            
        finally:
            # EXACT same cleanup as /api/analyze (lines 1369-1376)
            await user_service.cleanup()
            await analysis_tracker.cleanup()  
            await memory_service.cleanup()
            await enhanced_prompts_service.cleanup()
            
    except Exception as e:
        print(f"❌ [SHARED_ANALYSIS] Fresh analysis failed: {e}")
        # No final fallback - all analysis must go through OnDemandAnalysisService
        raise Exception(f"Fresh behavior analysis failed for user {user_id}: {e}")


async def create_context_summary_like_api_analyze(user_context, memory_context, archetype: str, user_id: str) -> str:
    """
    Create context summary exactly like /api/analyze does (lines 1324-1348)
    Minimal extraction - same logic, same format
    """
    try:
        data_quality = user_context.data_quality
        
        # EXACT same memory summary logic as /api/analyze (lines 1299-1323)
        memory_summary = ""
        if memory_context.longterm_memory:
            memory_summary = f"""
MEMORY-ENHANCED CONTEXT:
- Analysis Mode: {memory_context.analysis_mode.upper()}
- User Memory Profile Available: YES
- Personalized Focus Areas: {', '.join(memory_context.personalized_focus_areas)}
- Proven Strategies: {len(memory_context.proven_strategies)} strategies identified
- Recent Pattern Analysis: {len(memory_context.recent_patterns)} patterns tracked
- Historical Analysis Count: {len(memory_context.analysis_history)}"""
        else:
            if memory_context.analysis_mode == "follow_up":
                memory_summary = f"""
MEMORY-ENHANCED CONTEXT:
- Analysis Mode: FOLLOW-UP (Building memory profile)
- User Memory Profile Available: PARTIAL (Previous analysis detected)
- Days Since Last Analysis: {memory_context.days_to_fetch}
- Analysis History: {len(memory_context.analysis_history)} previous analyses"""
            else:
                memory_summary = f"""
MEMORY-ENHANCED CONTEXT:
- Analysis Mode: {memory_context.analysis_mode.upper()} (New user)
- User Memory Profile Available: NO (Building initial memory)"""

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
        pass  # # Production: Verbose print removed
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
        # Production: Verbose print removed
        print(f"{'='*60}")
        print(json.dumps(summary, indent=2))
        print(f"{'='*60}\n")
        
        # Also save to a log file for detailed review
        log_dir = "logs/data_collection"
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/data_collection_{user_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(log_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"💾 Data collection log saved to: {log_file}")
        
    except Exception as e:
        pass  # # Production: Verbose print removed

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
        
        # print(f"📝 [MEMORY_ENHANCED] Complete analysis stored in memory system")  # Commented for error-only mode
        
    except Exception as e:
        pass  # # Production: Verbose print removed

async def run_memory_enhanced_circadian_analysis(user_id: str, archetype: str) -> dict:
    """
    Memory-Enhanced Circadian Analysis - Following same pattern as behavior analysis
    Features:
    - Memory context preparation using MemoryIntegrationService
    - Memory-enhanced circadian prompt generation
    - Storing circadian analysis results in memory tables
    - Updating user memory profile with circadian insights
    - Complete logging of circadian analysis data
    """
    try:
        # Production: Verbose print removed  # Enabled for detailed logging

        # Import memory integration service
        from services.memory_integration_service import MemoryIntegrationService

        # Initialize memory integration service
        memory_service = MemoryIntegrationService()

        # Step 1: Prepare memory-enhanced context
        # Production: Verbose print removed  # Enabled for detailed logging
        memory_context = await memory_service.prepare_memory_enhanced_context(user_id, None, archetype)

        # Step 2: Get user data for circadian analysis (need more days for pattern recognition)
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt

        user_service = UserDataService()

        # Get extended user data for circadian pattern analysis
        user_context, data_quality = await user_service.get_analysis_data(user_id)

        # # Production: Verbose print removed  # Commented for error-only mode

        # Step 3: Get and enhance system prompt with memory
        system_prompt = get_system_prompt("circadian_analysis")  # Will use default if not exists
        enhanced_prompt = await memory_service.enhance_agent_prompt(
            system_prompt, memory_context, "circadian_analysis"
        )

        # print(f"🧠 [CIRCADIAN_ENHANCED] Enhanced circadian prompt with memory context (+{len(enhanced_prompt) - len(system_prompt)} chars)")  # Commented for error-only mode

        # Step 4: Format user context for AI analysis
        user_context_summary = await format_health_data_for_ai(user_context)

        # Step 5: Run AI-powered circadian analysis
        # Production: Verbose print removed  # Enabled for detailed logging
        analysis_result = await run_circadian_analysis_gpt4o(enhanced_prompt, user_context_summary)

        # Step 6: Store analysis results in memory for future personalization (optional)
        try:
            await memory_service.store_analysis_insights(
                user_id, "circadian_analysis", analysis_result, memory_context
            )
            # Production: Verbose print removed
        except Exception as insights_error:
            pass  # # Production: Verbose print removed

        # Step 7: Update user memory profile with circadian insights (optional)
        try:
            await memory_service.update_user_memory_profile(
                user_id, {}, analysis_result, {}
            )
            # Production: Verbose print removed
        except Exception as memory_error:
            pass  # # Production: Verbose print removed

        # Step 8: Store complete analysis in HolisticMemoryService
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        holistic_memory = HolisticMemoryService()

        # Convert data_quality to dict if it's a Pydantic model
        data_quality_dict = data_quality.dict() if hasattr(data_quality, 'dict') else data_quality

        complete_analysis = {
            "analysis_result": analysis_result,
            "user_context": {
                "data_summary": {
                    "scores_count": len(user_context.scores) if hasattr(user_context, 'scores') else 0,
                    "biomarkers_count": len(user_context.biomarkers) if hasattr(user_context, 'biomarkers') else 0,
                    "date_range": str(user_context.date_range) if hasattr(user_context, 'date_range') else "unknown"
                }
            } if user_context else None,
            "memory_context": {
                "analysis_mode": memory_context.analysis_mode,
                "days_to_fetch": memory_context.days_to_fetch,
                "personalized_focus_areas": memory_context.personalized_focus_areas,
                "created_at": memory_context.created_at.isoformat() if hasattr(memory_context, 'created_at') and memory_context.created_at else None
            } if memory_context else None,
            "data_quality": data_quality_dict,
            "enhanced_prompt_length": len(enhanced_prompt),
            "analysis_type": "memory_enhanced_circadian",
            "timestamp": datetime.now().isoformat()
        }

        # Try to store analysis result, but don't fail if storage has issues
        try:
            # Convert complete_analysis to JSON and back to handle any remaining serialization issues
            import json
            serializable_analysis = json.loads(json.dumps(complete_analysis, default=str))

            await holistic_memory.store_analysis_result(
                user_id=user_id,
                analysis_type="circadian_analysis",
                analysis_result=serializable_analysis,
                archetype_used=archetype
            )
            # Production: Verbose print removed
        except Exception as storage_error:
            pass  # # Production: Verbose print removed

        try:
            await holistic_memory.cleanup()
        except Exception as cleanup_error:
            pass  # # Production: Verbose print removed

        return analysis_result

    except Exception as e:
        print(f"❌ [CIRCADIAN_ENHANCED] Error in memory-enhanced circadian analysis: {e}")
        # Return the analysis_result if we got that far, otherwise return None
        try:
            if 'analysis_result' in locals() and analysis_result:
                # Production: Verbose print removed
                return analysis_result
        except:
            pass
        print(f"❌ [CIRCADIAN_ENHANCED] Circadian analysis failed completely")
        return None

async def run_memory_enhanced_routine_generation(user_id: str, archetype: str, behavior_analysis: dict, circadian_analysis: dict = None, combined_analysis: dict = None) -> dict:
    """
    Memory-Enhanced Routine Generation - Includes all features from /api/analyze
    Features:
    - Memory context preparation using MemoryIntegrationService
    - Memory-enhanced prompt generation
    - Storing routine plan in memory tables
    - Updating user memory profile
    - Complete logging of routine generation data
    """
    try:
        # print(f"🏃 [MEMORY_ENHANCED] Starting memory-enhanced routine generation for {user_id[:8]}...")  # Commented for error-only mode
        
        # Import memory integration service
        from services.memory_integration_service import MemoryIntegrationService
        
        # Initialize memory integration service
        memory_service = MemoryIntegrationService()
        
        # Step 1: Prepare memory-enhanced context
        # # Production: Verbose print removed  # Commented to reduce noise
        memory_context = await memory_service.prepare_memory_enhanced_context(user_id, None, archetype)
        
        # Step 2: Get user data for routine generation
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        
        # Get user data (service handles days internally based on analysis history)
        user_context, data_quality = await user_service.get_analysis_data(user_id)
        
        # # Production: Verbose print removed  # Commented for error-only mode
        
        # Step 3: Get and enhance system prompt with memory
        system_prompt = get_system_prompt("routine_plan")
        enhanced_prompt = await memory_service.enhance_agent_prompt(
            system_prompt, memory_context, "routine_plan"
        )
        
        # print(f"🧠 [MEMORY_ENHANCED] Enhanced routine prompt with memory context (+{len(enhanced_prompt) - len(system_prompt)} chars)")  # Commented for error-only mode
        
        # Step 4: Prepare routine agent data with memory context (including circadian analysis if available)
        user_context_summary = await format_health_data_for_ai(user_context)
        routine_data = await prepare_routine_agent_data(user_context, behavior_analysis)

        # NEW: Log combined analysis information
        if circadian_analysis:
            pass  # Production: Verbose print removed
        else:
            print(f"🏃 [MEMORY_ENHANCED] Using behavior analysis only (circadian analysis not available)")

        # Step 5: Run routine planning with memory-enhanced prompt and combined analysis
        routine_result = await run_routine_planning_4o(enhanced_prompt, user_context_summary, behavior_analysis, archetype, circadian_analysis)
        
        # Step 6: Store routine plan insights in memory
        # print(f"💾 [MEMORY_ENHANCED] Storing routine plan insights in memory...")  # Commented for error-only mode
        insights_stored = await memory_service.store_analysis_insights(
            user_id, "routine_plan", routine_result, archetype
        )
        
        if insights_stored:
            # # Production: Verbose print removed  # Commented to reduce noise
            pass
        else:
            # # Production: Verbose print removed  # Commented for error-only mode
            pass
        
        # Step 7: Store complete routine plan in holistic_analysis_results table
        # print(f"💾 [MEMORY_ENHANCED] Storing complete routine plan in database...")  # Commented for error-only mode
        try:
            from services.agents.memory.holistic_memory_service import HolisticMemoryService
            holistic_memory = HolisticMemoryService()
            
            # Store the complete routine result
            # Determine trigger based on whether threshold was exceeded
            decision, _ = await ondemand_service.should_trigger_analysis(user_id, archetype)
            if decision == AnalysisDecision.FRESH_ANALYSIS:
                # Add timestamp to make each threshold trigger unique for multiple daily analyses
                from datetime import datetime
                timestamp = datetime.now().strftime("%H%M%S")
                analysis_trigger = f"threshold_exceeded_{timestamp}"
            else:
                analysis_trigger = "scheduled"
            
            analysis_id = await holistic_memory.store_analysis_result(
                user_id, "routine_plan", routine_result, archetype, analysis_trigger
            )
        # # Production: Verbose print removed  # Commented to reduce noise

            # NEW: Store combined analysis if available
            if combined_analysis and circadian_analysis:
                try:
                    combined_analysis_id = await holistic_memory.store_analysis_result(
                        user_id, "complete_analysis", combined_analysis, archetype, analysis_trigger
                    )
                    print(f"💾 [MEMORY_ENHANCED] Combined analysis stored with ID: {combined_analysis_id}")
                except Exception as e:
                    pass  # # Production: Verbose print removed

            await holistic_memory.cleanup()
        except Exception as e:
            pass  # # # Production: Verbose print removed  # Commented for error-only mode
            pass

        # Step 8: Log complete routine generation data (input/output logging)
        await log_complete_analysis(
            "routine_plan", user_id, archetype, 
            routine_data, routine_result, memory_context,
            analysis_source="shared"
        )
        
        # Step 9: Cleanup memory service
        await memory_service.cleanup()
        
        # Add memory enhancement metadata to result
        routine_result.update({
            "memory_enhanced": True,
            "analysis_mode": memory_context.analysis_mode,
            "days_fetched": memory_context.days_to_fetch,
            "memory_focus_areas": memory_context.personalized_focus_areas,
            "insights_stored": insights_stored
        })
        
        # # Production: Verbose print removed  # Commented to reduce noise
        return routine_result
        
    except Exception as e:
        print(f"❌ [MEMORY_ENHANCED] Error in memory-enhanced routine generation: {e}")
        # Fallback to regular routine generation
        # print(f"🔄 [MEMORY_ENHANCED] Falling back to regular routine generation...")  # Commented to reduce noise
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        user_context, _ = await user_service.get_analysis_data(user_id)
        user_context_summary = await format_health_data_for_ai(user_context)
        system_prompt = get_system_prompt("routine_plan")
        
        return await run_routine_planning_4o(system_prompt, user_context_summary, behavior_analysis, archetype)

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
        # print(f"🥗 [MEMORY_ENHANCED] Starting memory-enhanced nutrition generation for {user_id[:8]}...")  # Commented for error-only mode
        
        # Import memory integration service
        from services.memory_integration_service import MemoryIntegrationService
        
        # Initialize memory integration service
        memory_service = MemoryIntegrationService()
        
        # Step 1: Prepare memory-enhanced context
        # # Production: Verbose print removed  # Commented to reduce noise
        memory_context = await memory_service.prepare_memory_enhanced_context(user_id, None, archetype)
        
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
            system_prompt, memory_context, "nutrition_plan"
        )
        
        # print(f"🧠 [MEMORY_ENHANCED] Enhanced nutrition prompt with memory context (+{len(enhanced_prompt) - len(system_prompt)} chars)")  # Commented for error-only mode
        
        # Step 4: Prepare nutrition agent data with memory context
        user_context_summary = await format_health_data_for_ai(user_context)
        nutrition_data = await prepare_nutrition_agent_data(user_context, behavior_analysis)
        
        # Step 5: Run nutrition planning with memory-enhanced prompt
        nutrition_result = await run_nutrition_planning_4o(enhanced_prompt, user_context_summary, behavior_analysis, archetype)
        
        # Step 6: Store nutrition plan insights in memory
        # print(f"💾 [MEMORY_ENHANCED] Storing nutrition plan insights in memory...")  # Commented for error-only mode
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
        # print(f"💾 [MEMORY_ENHANCED] Storing complete nutrition plan in database...")  # Commented for error-only mode
        try:
            from services.agents.memory.holistic_memory_service import HolisticMemoryService
            holistic_memory = HolisticMemoryService()
            
            # Store the complete nutrition result
            # Determine trigger based on whether threshold was exceeded
            decision, _ = await ondemand_service.should_trigger_analysis(user_id, archetype)
            if decision == AnalysisDecision.FRESH_ANALYSIS:
                # Add timestamp to make each threshold trigger unique for multiple daily analyses
                from datetime import datetime
                timestamp = datetime.now().strftime("%H%M%S")
                analysis_trigger = f"threshold_exceeded_{timestamp}"
            else:
                analysis_trigger = "scheduled"
            
            analysis_id = await holistic_memory.store_analysis_result(
                user_id, "nutrition_plan", nutrition_result, archetype, analysis_trigger
            )
        # # Production: Verbose print removed  # Commented to reduce noise
            
            await holistic_memory.cleanup()
        except Exception as e:
            pass  # # # Production: Verbose print removed  # Commented for error-only mode
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
            "analysis_mode": memory_context.analysis_mode,
            "days_fetched": memory_context.days_to_fetch,
            "memory_focus_areas": memory_context.personalized_focus_areas,
            "insights_stored": insights_stored
        })
        
        # # Production: Verbose print removed  # Commented to reduce noise
        return nutrition_result
        
    except Exception as e:
        print(f"❌ [MEMORY_ENHANCED] Error in memory-enhanced nutrition generation: {e}")
        # Fallback to regular nutrition generation
        # print(f"🔄 [MEMORY_ENHANCED] Falling back to regular nutrition generation...")  # Commented to reduce noise
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        user_context, _ = await user_service.get_analysis_data(user_id)
        user_context_summary = await format_health_data_for_ai(user_context)
        system_prompt = get_system_prompt("nutrition_plan")
        
        return await run_nutrition_planning_4o(system_prompt, user_context_summary, behavior_analysis, archetype)


async def run_nutrition_planning_4o(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str) -> dict:
    """Run nutrition planning using gpt-4o for plan generation - Phase 3.2"""
    try:
        client = openai.AsyncOpenAI()
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": f"{system_prompt}\n\nYou are a nutrition planning expert. Create detailed, practical nutrition plans based on health data and behavioral insights."
                },
                {
                    "role": "user", 
                    "content": f"""
{user_context}

BEHAVIORAL INSIGHTS:
{json.dumps(behavior_analysis, indent=2, cls=DateTimeEncoder)}

Create a comprehensive {archetype} nutrition plan for TODAY using the HolisticOS approach.

Include the following structure:
1. **Daily Nutritional Targets** (calories, protein, carbs, fats, fiber, vitamins)
2. **7 Meal Blocks** with detailed breakdown:
   - Early_Morning: Light hydration/preparation
   - Breakfast: Balanced start with protein and complex carbs
   - Morning_Snack: Energy maintenance
   - Lunch: Balanced midday nutrition
   - Afternoon_Snack: Sustained energy
   - Dinner: Recovery and satisfaction
   - Evening_Snack: Sleep preparation
3. **Nutrition Tips** for each meal explaining timing and composition
4. **Health Data Integration** - reference the provided health metrics

Make this plan practical, evidence-based, and specifically tailored to the {archetype} archetype and the provided health data patterns.
"""
                }
            ],
            temperature=0.4,  # Balanced creativity for practical planning
            max_tokens=2000
        )
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "archetype": archetype,
            "content": response.choices[0].message.content,
            "model_used": "gpt-4o",
            "plan_type": "comprehensive_nutrition",
            "system": "HolisticOS"
        }
        
    except Exception as e:
        logger.error(f"Error in nutrition planning: {e}")
        # Return fallback nutrition plan
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "archetype": archetype,
            "content": f"HolisticOS {archetype} Nutrition Plan - Fallback plan due to processing error",
            "model_used": "fallback",
            "plan_type": "fallback_nutrition",
            "system": "HolisticOS",
            "error": str(e)
        }

async def run_routine_planning_gpt4o(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str) -> dict:
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
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "archetype": archetype,
            "content": response.choices[0].message.content,
            "model_used": "gpt-4o",
            "plan_type": "comprehensive_routine",
            "system": "HolisticOS"
        }
        
    except Exception as e:
        print(f"Error in 4o nutrition planning: {e}")
        return {
            "error": str(e), 
            "model_used": "gpt-4o - fallback",
            "archetype": archetype,
            "date": datetime.now().strftime("%Y-%m-%d")
        }

async def run_routine_planning_4o(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str, circadian_analysis: dict = None) -> dict:
    """Run routine planning using gpt-4o for plan generation - Phase 3.2"""
    try:
        client = openai.AsyncOpenAI()

        # Extract readiness mode and map to descriptions
        readiness_level = behavior_analysis.get('readiness_level', 'Medium')
        mode_mapping = {
            'Low': 'recovery mode (gentle, restorative activities with reduced intensity)',
            'Medium': 'productive mode (moderate, building activities with steady progress)',
            'High': 'performance mode (intense, optimization activities with peak output)'
        }
        mode_description = mode_mapping.get(readiness_level, 'balanced activities')

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\nYou are a routine optimization expert. Create actionable daily routines based on health data, behavioral insights, and archetype frameworks."
                },
                {
                    "role": "user",
                    "content": f"""
{user_context}

BEHAVIORAL INSIGHTS:
{json.dumps(behavior_analysis, indent=2, cls=DateTimeEncoder)}

{f"CIRCADIAN RHYTHM DATA:{chr(10)}{json.dumps(circadian_analysis, indent=2, cls=DateTimeEncoder)}{chr(10)}" if circadian_analysis else ""}

READINESS MODE: {readiness_level} - {mode_description}

INSTRUCTIONS:
Create a {archetype} routine plan for TODAY with 4 time blocks.

Extract specific time ranges from the circadian data and format each block as:
**Block Name (Specific Time Range): Purpose**

Time block mapping:
- Morning block: Use the exact optimal_wake_time range from circadian data
- Peak block: Use the exact peak_energy_window range from circadian data
- Afternoon block: Use maintenance_energy_window range, avoid low_energy_window
- Evening block: End 1-2 hours before optimal_sleep_time

Format: "**Morning Wake-up (6:30-7:30 AM): Foundation Setting**" (example format)

Include specific time ranges, tasks, and reasoning for each block.
"""
                }
            ],
            temperature=0.4,  # Balanced creativity for practical planning
            max_tokens=2000
        )
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "archetype": archetype,
            "content": response.choices[0].message.content,
            "model_used": "gpt-4o",
            "plan_type": "comprehensive_routine",
            "system": "HolisticOS"
        }
        
    except Exception as e:
        print(f"Error in 4o routine planning: {e}")
        return {
            "error": str(e), 
            "model_used": "gpt-4o - fallback",
            "archetype": archetype,
            "date": datetime.now().strftime("%Y-%m-%d")
        }

async def run_memory_enhanced_routine_generation(user_id: str, archetype: str, behavior_analysis: dict, circadian_analysis: dict = None, combined_analysis: dict = None) -> dict:
    """
    Memory-Enhanced Routine Generation - Includes all features from /api/analyze
    Features:
    - Memory context preparation using MemoryIntegrationService
    - Memory-enhanced prompt generation
    - Storing routine plan in memory tables
    - Updating user memory profile
    - Complete logging of routine generation data
    """
    try:
        # # Production: Verbose print removed  # Commented for error-only mode
        
        # Import memory integration service
        from services.memory_integration_service import MemoryIntegrationService
        
        # Initialize memory integration service
        memory_service = MemoryIntegrationService()
        
        # Step 1: Prepare memory-enhanced context
        # # Production: Verbose print removed  # Commented to reduce noise
        memory_context = await memory_service.prepare_memory_enhanced_context(user_id, None, archetype)
        
        # Step 2: Get user data for routine generation
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        
        # Get user data (service handles days internally based on analysis history)
        user_context, data_quality = await user_service.get_analysis_data(user_id)
        
        # # Production: Verbose print removed  # Commented for error-only mode
        
        # Step 3: Get and enhance system prompt with memory
        system_prompt = get_system_prompt("plan_generation")
        enhanced_prompt = await memory_service.enhance_agent_prompt(
            system_prompt, memory_context, "routine_plan"
        )
        
        # print(f"🧠 [MEMORY_ENHANCED] Enhanced routine prompt with memory context (+{len(enhanced_prompt) - len(system_prompt)} chars)")  # Commented for error-only mode
        
        # Step 4: Prepare routine agent data with memory context
        user_context_summary = await format_health_data_for_ai(user_context)
        routine_data = await prepare_routine_agent_data(user_context, behavior_analysis)
        
        # Step 5: Run routine planning with memory-enhanced prompt
        routine_result = await run_routine_planning_4o(enhanced_prompt, user_context_summary, behavior_analysis, archetype)
        
        # Step 6: Store routine plan insights in memory
        # print(f"💾 [MEMORY_ENHANCED] Storing routine plan insights in memory...")  # Commented for error-only mode
        insights_stored = await memory_service.store_analysis_insights(
            user_id, "routine_plan", routine_result, archetype
        )
        
        if insights_stored:
            # # Production: Verbose print removed  # Commented to reduce noise
            pass
        else:
            # # Production: Verbose print removed  # Commented for error-only mode
            pass
        
        # Step 7: Store complete routine plan in holistic_analysis_results table
        # print(f"💾 [MEMORY_ENHANCED] Storing complete routine plan in database...")  # Commented for error-only mode
        try:
            from services.agents.memory.holistic_memory_service import HolisticMemoryService
            holistic_memory = HolisticMemoryService()
            
            # Store the complete routine result
            # Determine trigger based on whether threshold was exceeded
            decision, _ = await ondemand_service.should_trigger_analysis(user_id, archetype)
            if decision == AnalysisDecision.FRESH_ANALYSIS:
                # Add timestamp to make each threshold trigger unique for multiple daily analyses
                from datetime import datetime
                timestamp = datetime.now().strftime("%H%M%S")
                analysis_trigger = f"threshold_exceeded_{timestamp}"
            else:
                analysis_trigger = "scheduled"
            
            analysis_id = await holistic_memory.store_analysis_result(
                user_id, "routine_plan", routine_result, archetype, analysis_trigger
            )
        # # Production: Verbose print removed  # Commented to reduce noise

            # NEW: Store combined analysis if available
            if combined_analysis and circadian_analysis:
                try:
                    combined_analysis_id = await holistic_memory.store_analysis_result(
                        user_id, "complete_analysis", combined_analysis, archetype, analysis_trigger
                    )
                    print(f"💾 [MEMORY_ENHANCED] Combined analysis stored with ID: {combined_analysis_id}")
                except Exception as e:
                    pass  # # Production: Verbose print removed

            await holistic_memory.cleanup()
        except Exception as e:
            pass  # # # Production: Verbose print removed  # Commented for error-only mode
            pass

        # Step 8: Log complete routine generation data (input/output logging)
        await log_complete_analysis(
            "routine_plan", user_id, archetype, 
            routine_data, routine_result, memory_context,
            analysis_source="shared"
        )
        
        # Step 9: Cleanup memory service
        await memory_service.cleanup()
        
        # Add memory enhancement metadata to result
        routine_result.update({
            "memory_enhanced": True,
            "analysis_mode": memory_context.analysis_mode,
            "days_fetched": memory_context.days_to_fetch,
            "memory_focus_areas": memory_context.personalized_focus_areas,
            "insights_stored": insights_stored
        })
        
        # # Production: Verbose print removed  # Commented to reduce noise
        return routine_result
        
    except Exception as e:
        print(f"❌ [MEMORY_ENHANCED] Error in memory-enhanced routine generation: {e}")
        # Fallback to regular routine generation
        # print(f"🔄 [MEMORY_ENHANCED] Falling back to regular routine generation...")  # Commented to reduce noise
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        user_context, _ = await user_service.get_analysis_data(user_id)
        user_context_summary = await format_health_data_for_ai(user_context)
        system_prompt = get_system_prompt("plan_generation")
        
        return await run_routine_planning_4o(system_prompt, user_context_summary, behavior_analysis, archetype)

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
        
        ⚠️  DEPRECATED: Please migrate to modern endpoints:
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
    
    print("📁 [LEGACY] Legacy /api/analyze endpoint loaded from legacy folder")
    
except ImportError as e:
    pass  # # Production: Verbose print removed
    
    @app.post("/api/analyze", response_model=AnalysisResponse)
    async def analyze_user_fallback(request: AnalysisRequest, http_request: Request):
        """Fallback for legacy endpoint when legacy module is not available"""
        raise HTTPException(
            status_code=503, 
            detail="Legacy endpoint temporarily unavailable. Please use modern endpoints: POST /api/user/{user_id}/behavior/analyze"
        )
