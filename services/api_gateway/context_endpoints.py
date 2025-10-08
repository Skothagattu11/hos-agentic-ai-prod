"""
Context API - Single endpoint for chatbot context
Fetches all data needed for personalized responses in one call
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
from services.user_data_service import UserDataService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/context", tags=["context"])

# Database adapter (lazy initialization)
db_adapter = None

# Dependency for user data service
def get_user_service() -> UserDataService:
    return UserDataService()

async def get_db_adapter() -> SupabaseAsyncPGAdapter:
    """Get or create database adapter with connection"""
    global db_adapter
    if db_adapter is None:
        db_adapter = SupabaseAsyncPGAdapter()
        await db_adapter.connect()
    return db_adapter


@router.get("/user/{user_id}/chat-context")
async def get_chat_context(
    user_id: str,
    service: UserDataService = Depends(get_user_service)
):
    """
    Single endpoint to fetch all chatbot context:
    - Raw health data (last 3 days via existing health data service)
    - Behavior analysis (pre-analyzed)
    - Circadian analysis (pre-analyzed)
    - Plan data (time blocks + tasks)

    Returns everything needed for personalized chat responses
    """
    start_time = datetime.now()

    try:
        logger.info(f"Fetching chat context for user {user_id}")

        context = {
            "success": True,
            "user_id": user_id,
            "health_data": None,
            "behavior_analysis": None,
            "circadian_analysis": None,
            "plan": None,
            "metadata": {}
        }

        # 1. Fetch raw health data (last 3 days) using existing service
        health_context = await service.get_user_health_data(user_id, days=3)
        context["health_data"] = {
            "scores": [score.dict() for score in health_context.scores] if health_context.scores else [],
            "biomarkers": [biomarker.dict() for biomarker in health_context.biomarkers] if health_context.biomarkers else [],
            "date_range": {
                "start": health_context.date_range.start_date.isoformat(),
                "end": health_context.date_range.end_date.isoformat()
            }
        }

        # 2. Fetch latest behavior analysis
        behavior_analysis = await _fetch_behavior_analysis(user_id)
        context["behavior_analysis"] = behavior_analysis

        # 3. Fetch latest circadian analysis
        circadian_analysis = await _fetch_circadian_analysis(user_id)
        context["circadian_analysis"] = circadian_analysis

        # 4. Fetch plan data (time blocks + tasks)
        plan_data = await _fetch_plan_data(user_id)
        context["plan"] = plan_data

        # Metadata
        duration = (datetime.now() - start_time).total_seconds()
        context["metadata"] = {
            "fetch_duration_seconds": round(duration, 3),
            "data_freshness": datetime.now().isoformat(),
            "days_of_health_data": 3,
            "has_health_data": len(context["health_data"]["scores"]) > 0 or len(context["health_data"]["biomarkers"]) > 0,
            "has_behavior_analysis": behavior_analysis is not None,
            "has_circadian_analysis": circadian_analysis is not None,
            "has_plan": plan_data is not None
        }

        logger.info(f"✅ Chat context fetched in {duration:.3f}s")
        return context

    except Exception as e:
        logger.error(f"❌ Failed to fetch chat context for {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch chat context: {str(e)}"
        )


async def _fetch_behavior_analysis(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch latest pre-analyzed behavior analysis"""
    try:
        db = await get_db_adapter()

        query = """
        SELECT
            id,
            analysis_result,
            archetype,
            created_at
        FROM holistic_analysis_results
        WHERE user_id = $1
        AND analysis_type = 'behavior_analysis'
        ORDER BY created_at DESC
        LIMIT 1
        """

        result = await db.fetchrow(query, user_id)

        if not result:
            logger.warning(f"No behavior analysis found for {user_id}")
            return None

        analysis_result = result.get('analysis_result', {})

        created_at = result.get('created_at')
        if created_at and hasattr(created_at, 'isoformat'):
            created_at = created_at.isoformat()

        return {
            "id": result.get('id'),
            "archetype": result.get('archetype'),
            "created_at": created_at,
            "analysis": analysis_result
        }

    except Exception as e:
        logger.error(f"Failed to fetch behavior analysis: {e}")
        return None


async def _fetch_circadian_analysis(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch latest circadian analysis from routine plan"""
    try:
        db = await get_db_adapter()

        query = """
        SELECT
            id,
            analysis_result,
            created_at
        FROM holistic_analysis_results
        WHERE user_id = $1
        AND analysis_type IN ('routine_plan', 'circadian_analysis')
        ORDER BY created_at DESC
        LIMIT 1
        """

        result = await db.fetchrow(query, user_id)

        if not result:
            logger.warning(f"No circadian analysis found for {user_id}")
            return None

        analysis_result = result.get('analysis_result', {})

        # Debug: Log the keys available
        if analysis_result:
            logger.info(f"Circadian analysis_result keys: {list(analysis_result.keys())}")

        # Try multiple keys where circadian data might be stored
        circadian_data = (
            analysis_result.get('circadian_analysis') or
            analysis_result.get('circadian_rhythm') or
            analysis_result.get('energy_analysis') or
            analysis_result.get('circadian') or
            analysis_result  # If the whole result IS the circadian analysis
        )

        created_at = result.get('created_at')
        if created_at and hasattr(created_at, 'isoformat'):
            created_at = created_at.isoformat()

        return {
            "id": result.get('id'),
            "created_at": created_at,
            "analysis": circadian_data if circadian_data else {}
        }

    except Exception as e:
        logger.error(f"Failed to fetch circadian analysis: {e}")
        return None


async def _fetch_plan_data(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch latest plan (time blocks + tasks)"""
    try:
        db = await get_db_adapter()

        # Get latest routine plan
        plan_query = """
        SELECT
            id,
            archetype,
            created_at
        FROM holistic_analysis_results
        WHERE user_id = $1
        AND analysis_type = 'routine_plan'
        ORDER BY created_at DESC
        LIMIT 1
        """

        plan_result = await db.fetchrow(plan_query, user_id)

        if not plan_result:
            logger.warning(f"No plan found for {user_id}")
            return None

        analysis_id = plan_result.get('id')

        # Get time blocks
        blocks_query = """
        SELECT
            id,
            block_title,
            time_range,
            purpose,
            why_it_matters,
            connection_to_insights,
            block_order
        FROM time_blocks
        WHERE analysis_result_id = $1
        ORDER BY block_order
        """

        blocks = await db.fetch(blocks_query, analysis_id)

        # Get tasks
        tasks_query = """
        SELECT
            id,
            title,
            description,
            scheduled_time,
            scheduled_end_time,
            estimated_duration_minutes,
            task_type,
            priority_level,
            time_block_id
        FROM plan_items
        WHERE analysis_result_id = $1
        ORDER BY scheduled_time
        """

        tasks = await db.fetch(tasks_query, analysis_id)

        created_at = plan_result.get('created_at')
        if created_at and hasattr(created_at, 'isoformat'):
            created_at = created_at.isoformat()

        return {
            "plan_id": analysis_id,
            "archetype": plan_result.get('archetype'),
            "created_at": created_at,
            "time_blocks": [dict(row) for row in blocks] if blocks else [],
            "tasks": [dict(row) for row in tasks] if tasks else []
        }

    except Exception as e:
        logger.error(f"Failed to fetch plan data: {e}")
        return None
