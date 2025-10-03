"""
Holistic Integration API Endpoints
Provides read-only access to holistic analysis data for conversational AI service
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import logging
import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["holistic-integration"])


def serialize_datetime(dt_value):
    """
    Helper to serialize datetime - handles both datetime objects and ISO strings
    When using Supabase REST API, dates come as strings. When using connection pool, they're datetime objects.
    """
    if dt_value is None:
        return None
    if isinstance(dt_value, str):
        return dt_value  # Already a string
    if hasattr(dt_value, 'isoformat'):
        return dt_value.isoformat()  # datetime/date object
    return str(dt_value)  # Fallback


class HolisticDataService:
    """Data service for holistic endpoints - matches pattern from insights_service"""

    def __init__(self):
        self.db_adapter = None

    async def _ensure_db_connection(self) -> SupabaseAsyncPGAdapter:
        """Same connection pattern as other services"""
        if not self.db_adapter or not hasattr(self.db_adapter, 'is_connected') or not self.db_adapter.is_connected:
            try:
                self.db_adapter = SupabaseAsyncPGAdapter()
                await self.db_adapter.connect()
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                raise
        return self.db_adapter


# Create service instance
holistic_data_service = HolisticDataService()


@router.get("/analysis-results/{analysis_result_id}")
async def get_analysis_result(analysis_result_id: str):
    """
    Get specific analysis result by ID

    Returns the complete analysis result including:
    - Analysis type (routine_plan, circadian_analysis, behavior_analysis)
    - Archetype
    - Analysis result (JSON)
    - Metadata (dates, versions, etc.)

    Args:
        analysis_result_id: UUID of the analysis result

    Returns:
        Complete analysis result object
    """
    try:
        logger.info(f"Fetching analysis result: {analysis_result_id}")

        # Get database adapter
        db = await holistic_data_service._ensure_db_connection()

        query = """
            SELECT
                id,
                user_id,
                analysis_type,
                archetype,
                analysis_result,
                input_summary,
                agent_id,
                analysis_version,
                confidence_score,
                completeness_score,
                created_at,
                analysis_date,
                analysis_hash,
                is_duplicate,
                analysis_trigger
            FROM holistic_analysis_results
            WHERE id = $1
        """

        row = await db.fetchrow(query, analysis_result_id)

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis result not found: {analysis_result_id}"
            )

        # Parse analysis_result JSON if it's a string
        analysis_result = row['analysis_result']
        if isinstance(analysis_result, str):
            try:
                analysis_result = json.loads(analysis_result)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse analysis_result as JSON for {analysis_result_id}")

        return {
            "success": True,
            "data": {
                "id": str(row['id']),
                "user_id": row['user_id'],
                "analysis_type": row['analysis_type'],
                "archetype": row['archetype'],
                "analysis_result": analysis_result,
                "input_summary": row['input_summary'],
                "agent_id": row['agent_id'],
                "analysis_version": row['analysis_version'],
                "confidence_score": float(row['confidence_score']) if row['confidence_score'] else None,
                "completeness_score": float(row['completeness_score']) if row['completeness_score'] else None,
                "created_at": serialize_datetime(row['created_at']),
                "analysis_date": serialize_datetime(row['analysis_date']),
                "analysis_hash": row['analysis_hash'],
                "is_duplicate": row['is_duplicate'],
                "analysis_trigger": row['analysis_trigger']
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analysis result {analysis_result_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch analysis result: {str(e)}"
        )


@router.get("/users/{user_id}/behavior-analysis")
async def get_behavior_analysis(
    user_id: str,
    date: Optional[str] = Query(None, description="Specific date in YYYY-MM-DD format")
):
    """
    Get behavior analysis for user

    Returns behavioral signature, archetype, goals, barriers, and recommendations

    Args:
        user_id: User identifier
        date: Optional specific date (defaults to latest)

    Returns:
        Behavior analysis data
    """
    try:
        logger.info(f"Fetching behavior analysis for user: {user_id}, date: {date}")

        db = await holistic_data_service._ensure_db_connection()
        # Build query based on date parameter
        if date:
            query = """
                SELECT
                    id, user_id, analysis_type, archetype, analysis_result,
                    created_at, analysis_date, confidence_score
                FROM holistic_analysis_results
                WHERE user_id = $1
                AND analysis_type = 'behavior_analysis'
                AND analysis_date = $2
                ORDER BY created_at DESC
                LIMIT 1
            """
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            row = await db.fetchrow(query, user_id, parsed_date)
        else:
            query = """
                SELECT
                    id, user_id, analysis_type, archetype, analysis_result,
                    created_at, analysis_date, confidence_score
                FROM holistic_analysis_results
                WHERE user_id = $1
                AND analysis_type = 'behavior_analysis'
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await db.fetchrow(query, user_id)

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Behavior analysis not found for user: {user_id}"
            )

        # Parse analysis result
        analysis_result = row['analysis_result']
        if isinstance(analysis_result, str):
            try:
                analysis_result = json.loads(analysis_result)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse analysis_result as JSON")

        # Extract key behavioral data
        behavioral_signature = analysis_result.get('behavioral_signature', {})
        personalized_strategy = analysis_result.get('personalized_strategy', {})

        return {
            "success": True,
            "data": {
                "analysis_id": str(row['id']),
                "user_id": user_id,
                "archetype": row['archetype'],
                "analysis_date": serialize_datetime(row['analysis_date']),
                "confidence_score": float(row['confidence_score']) if row['confidence_score'] else None,
                "behavioral_signature": {
                    "signature": behavioral_signature.get('signature', ''),
                    "confidence": behavioral_signature.get('confidence', 0)
                },
                "primary_goal": analysis_result.get('primary_goal', {}),
                "readiness_level": analysis_result.get('readiness_level', 'Medium'),
                "sophistication_assessment": analysis_result.get('sophistication_assessment', {}),
                "recommendations": analysis_result.get('recommendations', []),
                "personalized_strategy": {
                    "habit_integration": personalized_strategy.get('habit_integration', ''),
                    "barrier_mitigation": personalized_strategy.get('barrier_mitigation', ''),
                    "motivation_drivers": personalized_strategy.get('motivation_drivers', '')
                },
                "data_insights": analysis_result.get('data_insights', '')
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching behavior analysis for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch behavior analysis: {str(e)}"
        )


@router.get("/users/{user_id}/circadian-analysis")
async def get_circadian_analysis(
    user_id: str,
    date: Optional[str] = Query(None, description="Specific date in YYYY-MM-DD format")
):
    """
    Get circadian rhythm analysis for user

    Returns chronotype, energy zones, sleep schedule, and timing recommendations

    Args:
        user_id: User identifier
        date: Optional specific date (defaults to latest)

    Returns:
        Circadian analysis data including energy zones
    """
    try:
        logger.info(f"Fetching circadian analysis for user: {user_id}, date: {date}")

        db = await holistic_data_service._ensure_db_connection()
        if date:
            query = """
                SELECT
                    id, user_id, analysis_type, archetype, analysis_result,
                    created_at, analysis_date, confidence_score
                FROM holistic_analysis_results
                WHERE user_id = $1
                AND analysis_type = 'circadian_analysis'
                AND analysis_date = $2
                ORDER BY created_at DESC
                LIMIT 1
            """
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            row = await db.fetchrow(query, user_id, parsed_date)
        else:
            query = """
                SELECT
                    id, user_id, analysis_type, archetype, analysis_result,
                    created_at, analysis_date, confidence_score
                FROM holistic_analysis_results
                WHERE user_id = $1
                AND analysis_type = 'circadian_analysis'
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await db.fetchrow(query, user_id)

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Circadian analysis not found for user: {user_id}"
            )

        # Parse analysis result
        analysis_result = row['analysis_result']
        if isinstance(analysis_result, str):
            try:
                analysis_result = json.loads(analysis_result)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse analysis_result as JSON")

        return {
            "success": True,
            "data": {
                "analysis_id": str(row['id']),
                "user_id": user_id,
                "archetype": row['archetype'],
                "analysis_date": serialize_datetime(row['analysis_date']),
                "confidence_score": float(row['confidence_score']) if row['confidence_score'] else None,
                "chronotype_assessment": analysis_result.get('chronotype_assessment', {}),
                "energy_zone_analysis": analysis_result.get('energy_zone_analysis', {}),
                "biomarker_insights": analysis_result.get('biomarker_insights', {}),
                "schedule_recommendations": analysis_result.get('schedule_recommendations', {}),
                "integration_recommendations": analysis_result.get('integration_recommendations', {})
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching circadian analysis for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch circadian analysis: {str(e)}"
        )


@router.get("/users/{user_id}/context-memory")
async def get_context_memory(user_id: str):
    """
    Get engagement context memory for user

    Returns engagement patterns, satisfaction trends, optimization opportunities

    Args:
        user_id: User identifier

    Returns:
        Context memory analysis
    """
    try:
        logger.info(f"Fetching context memory for user: {user_id}")

        db = await holistic_data_service._ensure_db_connection()
        query = """
            SELECT
                id, user_id, context_summary, source_data,
                archetype, engagement_data_included, data_period_days,
                generation_method, created_at
            FROM holistic_memory_analysis_context
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """

        row = await db.fetchrow(query, user_id)

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Context memory not found for user: {user_id}"
            )

        # Parse source_data JSON if it's a string
        source_data = row['source_data']
        if isinstance(source_data, str):
            try:
                source_data = json.loads(source_data)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse source_data as JSON")
                source_data = {}

        return {
            "success": True,
            "data": {
                "id": str(row['id']),
                "user_id": user_id,
                "context_summary": row['context_summary'],
                "source_data": source_data,
                "archetype": row['archetype'],
                "engagement_data_included": row['engagement_data_included'],
                "data_period_days": row['data_period_days'],
                "generation_method": row['generation_method'],
                "created_at": serialize_datetime(row['created_at'])
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching context memory for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch context memory: {str(e)}"
        )


@router.get("/users/{user_id}/analysis-results")
async def list_analysis_results(
    user_id: str,
    analysis_type: Optional[str] = Query(None, description="Filter by analysis type"),
    limit: int = Query(10, description="Number of results to return", ge=1, le=50)
):
    """
    List all analysis results for user (for date picker)

    Returns list of available analyses with dates and types

    Args:
        user_id: User identifier
        analysis_type: Optional filter (routine_plan, circadian_analysis, behavior_analysis)
        limit: Maximum number of results

    Returns:
        List of analysis results with metadata
    """
    try:
        logger.info(f"Listing analysis results for user: {user_id}, type: {analysis_type}")

        db = await holistic_data_service._ensure_db_connection()
        if analysis_type:
            query = """
                SELECT
                    id, user_id, analysis_type, archetype,
                    created_at, analysis_date, confidence_score,
                    is_duplicate, analysis_trigger
                FROM holistic_analysis_results
                WHERE user_id = $1 AND analysis_type = $2
                ORDER BY analysis_date DESC, created_at DESC
                LIMIT $3
            """
            rows = await db.fetch(query, user_id, analysis_type, limit)
        else:
            query = """
                SELECT
                    id, user_id, analysis_type, archetype,
                    created_at, analysis_date, confidence_score,
                    is_duplicate, analysis_trigger
                FROM holistic_analysis_results
                WHERE user_id = $1
                ORDER BY analysis_date DESC, created_at DESC
                LIMIT $2
            """
            rows = await db.fetch(query, user_id, limit)

        results = []
        for row in rows:
            results.append({
                "id": str(row['id']),
                "user_id": user_id,
                "analysis_type": row['analysis_type'],
                "archetype": row['archetype'],
                "created_at": serialize_datetime(row['created_at']),
                "analysis_date": serialize_datetime(row['analysis_date']),
                "confidence_score": float(row['confidence_score']) if row['confidence_score'] else None,
                "is_duplicate": row['is_duplicate'],
                "analysis_trigger": row['analysis_trigger']
            })

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "count": len(results),
                "analyses": results
            }
        }

    except Exception as e:
        logger.error(f"Error listing analysis results for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list analysis results: {str(e)}"
        )


@router.get("/analysis-results/{analysis_result_id}/full-context")
async def get_full_context(analysis_result_id: str):
    """
    Get complete context for a specific analysis (mega endpoint)

    Returns:
    - Plan data (if routine_plan)
    - Behavior analysis
    - Circadian analysis
    - Context memory
    - Plan items (if routine_plan)

    This is an optimization endpoint to reduce multiple API calls

    Args:
        analysis_result_id: UUID of the primary analysis result

    Returns:
        Complete context bundle
    """
    try:
        logger.info(f"Fetching full context for analysis: {analysis_result_id}")

        db = await holistic_data_service._ensure_db_connection()
        # Get primary analysis
        primary_query = """
            SELECT
                id, user_id, analysis_type, archetype, analysis_result,
                created_at, analysis_date, confidence_score
            FROM holistic_analysis_results
            WHERE id = $1
        """

        primary = await db.fetchrow(primary_query, analysis_result_id)

        if not primary:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis result not found: {analysis_result_id}"
            )

        user_id = primary['user_id']
        analysis_date = primary['analysis_date']

        # Parse primary analysis result
        primary_result = primary['analysis_result']
        if isinstance(primary_result, str):
            try:
                primary_result = json.loads(primary_result)
            except json.JSONDecodeError:
                pass

        # Build context bundle
        context = {
            "analysis_id": str(primary['id']),
            "user_id": user_id,
            "analysis_type": primary['analysis_type'],
            "archetype": primary['archetype'],
            "analysis_date": serialize_datetime(analysis_date),
            "primary_analysis": primary_result
        }

        # Get behavior analysis
        behavior_query = """
            SELECT analysis_result
            FROM holistic_analysis_results
            WHERE user_id = $1
            AND analysis_type = 'behavior_analysis'
            ORDER BY created_at DESC
            LIMIT 1
        """
        behavior = await db.fetchrow(behavior_query, user_id)
        if behavior:
            behavior_result = behavior['analysis_result']
            if isinstance(behavior_result, str):
                try:
                    behavior_result = json.loads(behavior_result)
                except json.JSONDecodeError:
                    behavior_result = {}
            context['behavior_analysis'] = behavior_result

        # Get circadian analysis
        circadian_query = """
            SELECT analysis_result
            FROM holistic_analysis_results
            WHERE user_id = $1
            AND analysis_type = 'circadian_analysis'
            ORDER BY created_at DESC
            LIMIT 1
        """
        circadian = await db.fetchrow(circadian_query, user_id)
        if circadian:
            circadian_result = circadian['analysis_result']
            if isinstance(circadian_result, str):
                try:
                    circadian_result = json.loads(circadian_result)
                except json.JSONDecodeError:
                    circadian_result = {}
            context['circadian_analysis'] = circadian_result

        # Get context memory
        memory_query = """
            SELECT context_summary, source_data
            FROM holistic_memory_analysis_context
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """
        memory = await db.fetchrow(memory_query, user_id)
        if memory:
            source_data = memory['source_data']
            if isinstance(source_data, str):
                try:
                    source_data = json.loads(source_data)
                except json.JSONDecodeError:
                    source_data = {}
            context['context_memory'] = {
                "summary": memory['context_summary'],
                "source_data": source_data
            }

        # Get plan items if this is a routine_plan
        if primary['analysis_type'] == 'routine_plan':
            items_query = """
                SELECT
                    id, item_id, time_block, title,
                    scheduled_time, task_type
                FROM plan_items
                WHERE analysis_result_id = $1
                ORDER BY scheduled_time
            """
            items = await db.fetch(items_query, analysis_result_id)
            context['plan_items'] = [
                {
                    "id": str(item['id']),
                    "item_id": item['item_id'],
                    "time_block": item['time_block'],
                    "title": item['title'],
                    "scheduled_time": serialize_datetime(item['scheduled_time']),
                    "task_type": item['task_type']
                }
                for item in items
            ]

        return {
            "success": True,
            "data": context
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching full context for analysis {analysis_result_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch full context: {str(e)}"
        )


# Health check endpoint
@router.get("/holistic-integration/health")
async def holistic_integration_health():
    """Health check for holistic integration endpoints"""
    try:
        # Test database connection with actual table query (works with both pool and REST API)
        db = await holistic_data_service._ensure_db_connection()
        result = await db.fetchrow("SELECT COUNT(*) as count FROM holistic_analysis_results LIMIT 1")

        return {
            "success": True,
            "service": "holistic_integration",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Holistic integration health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )
