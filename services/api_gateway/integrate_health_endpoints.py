"""
Integration script to add health data endpoints to existing HolisticOS FastAPI app
CTO Approach: Non-invasive integration, preserve existing functionality
"""
from fastapi import FastAPI
from .health_data_endpoints import router as health_data_router
from .insights_endpoints import router as insights_router
import logging

logger = logging.getLogger(__name__)

def integrate_health_data_endpoints(app: FastAPI) -> None:
    """
    Add health data endpoints to existing FastAPI app
    Non-invasive integration - preserves all existing functionality
    """
    try:
        # Add the health data router
        app.include_router(health_data_router)
        
        # Add the insights router
        app.include_router(insights_router)
        
        logger.debug("[INTEGRATION] Health data endpoints added successfully")
        logger.debug("[INTEGRATION] Available endpoints:")
        logger.debug("  - GET /api/v1/health-data/users/{user_id}/health-context")
        logger.debug("  - GET /api/v1/health-data/users/{user_id}/summary")
        logger.debug("  - GET /api/v1/health-data/users/{user_id}/data-quality")
        logger.debug("  - GET /api/v1/health-data/users/{user_id}/agent/{agent_name}/data")
        logger.debug("  - POST /api/v1/health-data/users/{user_id}/analyze")
        logger.debug("  - GET /api/v1/health-data/system/health")
        logger.debug("  - POST /api/v1/insights/generate")
        logger.debug("  - GET /api/v1/insights/{user_id}")
        logger.debug("  - PATCH /api/v1/insights/{insight_id}/acknowledge")
        logger.debug("  - POST /api/v1/insights/{insight_id}/rate")
        
        return True
        
    except Exception as e:
        logger.error(f"[INTEGRATION_ERROR] Failed to add health data endpoints: {e}")
        return False

# Convenience function for manual integration
def setup_health_data_api(app: FastAPI) -> bool:
    """
    Setup function that can be called from your main app
    """
    return integrate_health_data_endpoints(app)