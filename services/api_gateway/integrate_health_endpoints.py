"""
Integration script to add health data endpoints to existing HolisticOS FastAPI app
CTO Approach: Non-invasive integration, preserve existing functionality
"""
from fastapi import FastAPI
from .health_data_endpoints import router as health_data_router
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
        
        logger.info("[INTEGRATION] Health data endpoints added successfully")
        logger.info("[INTEGRATION] Available endpoints:")
        logger.info("  - GET /api/v1/health-data/users/{user_id}/health-context")
        logger.info("  - GET /api/v1/health-data/users/{user_id}/summary")
        logger.info("  - GET /api/v1/health-data/users/{user_id}/data-quality")
        logger.info("  - GET /api/v1/health-data/users/{user_id}/agent/{agent_name}/data")
        logger.info("  - POST /api/v1/health-data/users/{user_id}/analyze")
        logger.info("  - GET /api/v1/health-data/system/health")
        
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