"""
AI Context Integration Service
Replaces MemoryIntegrationService with AI-powered context generation
Maintains same interface for seamless integration with existing agents
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from services.ai_context_generation_service import AIContextGeneratorService

logger = logging.getLogger(__name__)

@dataclass
class ContextEnhancedContext:
    """Context object containing health data enhanced with AI context (replaces MemoryEnhancedContext)"""
    user_id: str
    analysis_mode: str  # "initial", "follow_up", "adaptation"
    days_to_fetch: int

    # AI Context (replaces 4-layer memory)
    ai_context_summary: str
    engagement_insights: Dict[str, Any]

    # Agent-specific historical context
    behavior_analysis_history: List[Dict[str, Any]]  # Last 2 behavior analyses
    circadian_analysis_history: List[Dict[str, Any]]  # Last 2 circadian analyses

    # Analysis guidance
    personalized_focus_areas: List[str]
    proven_strategies: Dict[str, Any]
    adaptation_preferences: Dict[str, Any]

    created_at: datetime

class AIContextIntegrationService:
    """
    AI-powered context integration service
    Replaces MemoryIntegrationService with AI Context Service while maintaining same interface
    """

    def __init__(self):
        self.ai_context_service = AIContextGeneratorService()

        # Session tracking for working memory
        self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.debug("[AI_CONTEXT_INTEGRATION] Initialized with AI Context Service")

    async def prepare_memory_enhanced_context(self, user_id: str, ondemand_metadata: dict = None, archetype: str = None) -> ContextEnhancedContext:
        """
        Prepare AI context-enhanced context for analysis
        SAME INTERFACE as MemoryIntegrationService.prepare_memory_enhanced_context()

        Args:
            user_id: User identifier
            ondemand_metadata: Metadata from OnDemandAnalysisService containing analysis_mode and days_to_fetch
            archetype: User archetype for personalization
        """
        try:
            logger.debug(f"[AI_CONTEXT_INTEGRATION] Preparing AI context for user {user_id}")

            # Use OnDemandAnalysisService decision for analysis mode
            if ondemand_metadata and 'analysis_mode' in ondemand_metadata:
                analysis_mode = ondemand_metadata['analysis_mode']
                days_to_fetch = ondemand_metadata['days_to_fetch']
            else:
                # Fallback to defaults
                analysis_mode = "initial"
                days_to_fetch = 7

            # Check for recent AI context (< 10 minutes old) to avoid regeneration
            recent_context = await self._get_recent_context(user_id, max_age_minutes=10)
            if recent_context:
                ai_context_summary = recent_context
            else:
                ai_context_summary = await self.ai_context_service.generate_user_context(user_id, archetype, days=3)

            # Get agent-specific historical analyses
            behavior_history = await self._get_agent_analysis_history(user_id, "behavior_analysis", archetype, limit=2)
            circadian_history = await self._get_agent_analysis_history(user_id, "circadian_analysis", archetype, limit=2)

            context = ContextEnhancedContext(
                user_id=user_id,
                analysis_mode=analysis_mode,
                days_to_fetch=days_to_fetch,
                ai_context_summary=ai_context_summary,
                engagement_insights={},  # Removed - info is in AI context
                behavior_analysis_history=behavior_history,
                circadian_analysis_history=circadian_history,
                personalized_focus_areas=[],  # Removed - agents extract from context
                proven_strategies={},  # Removed - agents extract from history
                adaptation_preferences={},  # Removed - agents determine this
                created_at=datetime.now(timezone.utc)
            )

            # Store working context for this session
            await self._store_session_context(context)

            return context

        except Exception as e:
            logger.error(f"[AI_CONTEXT_INTEGRATION_ERROR] Failed to prepare context for {user_id}: {e}")
            # Return minimal context on error
            return ContextEnhancedContext(
                user_id=user_id,
                analysis_mode="initial",
                days_to_fetch=7,
                ai_context_summary=f"Context generation failed: {str(e)}",
                engagement_insights={},
                behavior_analysis_history=[],
                circadian_analysis_history=[],
                personalized_focus_areas=[],
                proven_strategies={},
                adaptation_preferences={},
                created_at=datetime.now(timezone.utc)
            )

    async def enhance_agent_prompt(self, base_prompt: str, context: ContextEnhancedContext,
                                 agent_type: str) -> str:
        """
        Enhance agent prompt with AI context and agent-specific historical data
        Different agents get different context perspectives
        """
        try:
            # Build agent-specific context enhancement
            agent_specific_context = self._build_agent_specific_context(context, agent_type)

            if agent_specific_context:
                enhanced_prompt = f"""
{base_prompt}

{agent_specific_context}

Use this personalized context to provide highly tailored {agent_type} analysis.
Focus on building upon proven patterns and avoiding consistently failed strategies.
"""
                logger.debug(f"[AI_CONTEXT_INTEGRATION] Enhanced {agent_type} prompt for {context.user_id}")
                return enhanced_prompt
            else:
                return base_prompt

        except Exception as e:
            logger.error(f"[AI_CONTEXT_INTEGRATION_ERROR] Failed to enhance prompt: {e}")
            return base_prompt

    async def _get_recent_context(self, user_id: str, max_age_minutes: int = 5) -> Optional[str]:
        """
        Get recent AI context if it exists (< max_age_minutes old)
        Returns context_summary string or None
        """
        try:
            from datetime import timedelta

            # Calculate cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)

            # Query for recent context WITH timestamp
            recent_context = await self.ai_context_service._get_last_context_with_timestamp(user_id)

            if recent_context:
                # Check if context is recent enough
                context_time = recent_context.get('created_at')
                if context_time:
                    # Parse timestamp if it's a string
                    if isinstance(context_time, str):
                        from dateutil import parser
                        context_time = parser.parse(context_time)

                    # Make timezone-aware if needed
                    if context_time.tzinfo is None:
                        context_time = context_time.replace(tzinfo=timezone.utc)

                    # Check if recent enough
                    if context_time >= cutoff_time:
                        logger.info(f"[AI_CONTEXT_INTEGRATION] ♻️ Reusing recent context for {user_id[:8]}... (age: {(datetime.now(timezone.utc) - context_time).seconds}s)")
                        return recent_context.get('context_summary')

            logger.debug(f"[AI_CONTEXT_INTEGRATION] No recent context found for {user_id[:8]}... (older than {max_age_minutes}m)")
            return None

        except Exception as e:
            logger.warning(f"[AI_CONTEXT_INTEGRATION] Error checking recent context for {user_id}: {e}")
            return None

    async def _get_agent_analysis_history(self, user_id: str, analysis_type: str, archetype: str = None, limit: int = 2) -> List[Dict]:
        """Get last N analyses for specific agent type"""
        try:
            # Use the same method as AI Context Service for consistency
            history = await self.ai_context_service._get_last_plans(user_id, archetype, limit=limit)

            # Filter by analysis type
            filtered_history = [
                analysis for analysis in history
                if analysis.get('analysis_type') == analysis_type
            ]

            return filtered_history[:limit]

        except Exception as e:
            logger.error(f"Failed to get {analysis_type} history for {user_id}: {e}")
            return []

    def _extract_focus_areas_from_context(self, ai_context: str, engagement_data: Dict) -> List[str]:
        """Extract focus areas from AI context summary"""
        focus_areas = set()

        # Extract from AI context text analysis
        context_lower = ai_context.lower()
        if 'morning' in context_lower or 'early' in context_lower:
            focus_areas.add("morning_optimization")
        if 'evening' in context_lower or 'night' in context_lower:
            focus_areas.add("evening_routine")
        if 'exercise' in context_lower or 'activity' in context_lower:
            focus_areas.add("activity_improvement")
        if 'sleep' in context_lower:
            focus_areas.add("sleep_optimization")
        if 'energy' in context_lower:
            focus_areas.add("energy_management")
        if 'completion' in context_lower or 'productive' in context_lower:
            focus_areas.add("productivity_enhancement")

        # Extract from engagement patterns
        calendar_count = len(engagement_data.get('calendar_selections', []))
        checkin_count = len(engagement_data.get('task_checkins', []))

        if calendar_count > checkin_count * 1.5:
            focus_areas.add("planning_vs_execution_gap")
        if checkin_count > 10:
            focus_areas.add("consistent_tracking")

        return list(focus_areas) if focus_areas else ["general_health", "behavior_optimization"]

    def _extract_proven_strategies_from_history(self, behavior_history: List[Dict], circadian_history: List[Dict]) -> Dict[str, Any]:
        """Extract strategies that have worked from historical analyses"""
        strategies = {}

        # Extract from behavior analysis patterns
        for analysis in behavior_history:
            result = analysis.get('analysis_result', {})
            if isinstance(result, dict):
                recommendations = result.get('recommendations', [])
                if recommendations:
                    strategies['behavior_recommendations'] = recommendations[:3]  # Top 3

        # Extract from circadian analysis patterns
        for analysis in circadian_history:
            result = analysis.get('analysis_result', {})
            if isinstance(result, dict):
                chronotype = result.get('chronotype_assessment', {})
                if chronotype:
                    strategies['chronotype_insights'] = chronotype

        return strategies

    def _extract_adaptation_preferences(self, ai_context: str) -> Dict[str, Any]:
        """Extract adaptation preferences from AI context"""
        preferences = {
            "complexity_tolerance": 0.5,
            "change_pace": "moderate",
            "preferred_communication_style": "supportive"
        }

        # Simple AI context analysis for adaptation cues
        context_lower = ai_context.lower()
        if 'consistent' in context_lower or 'regular' in context_lower:
            preferences["change_pace"] = "gradual"
        if 'struggle' in context_lower or 'difficult' in context_lower:
            preferences["complexity_tolerance"] = 0.3
        if 'successful' in context_lower or 'effective' in context_lower:
            preferences["complexity_tolerance"] = 0.7

        return preferences

    def _build_agent_specific_context(self, context: ContextEnhancedContext, agent_type: str) -> str:
        """Build agent-specific context enhancement"""
        if agent_type == "behavior_analysis":
            return self._build_behavior_agent_context(context)
        elif agent_type == "circadian_analysis":
            return self._build_circadian_agent_context(context)
        elif agent_type == "routine_generation":
            return self._build_routine_agent_context(context)
        else:
            return ""

    def _build_behavior_agent_context(self, context: ContextEnhancedContext) -> str:
        """Build behavior-specific context"""
        context_parts = ["BEHAVIOR ANALYSIS CONTEXT:"]

        # Add AI context summary
        context_parts.append(f"User Engagement Patterns:\n{context.ai_context_summary}")

        # Add engagement insights
        insights = context.engagement_insights
        context_parts.append(f"Recent Engagement: {insights.get('calendar_selections_count', 0)} planned tasks, {insights.get('task_checkins_count', 0)} completed")

        # Add historical behavior patterns
        if context.behavior_analysis_history:
            context_parts.append("Previous Behavior Analysis Results:")
            for i, analysis in enumerate(context.behavior_analysis_history[:2], 1):
                result = analysis.get('analysis_result', {})
                if isinstance(result, dict):
                    recommendations = result.get('recommendations', [])
                    if recommendations:
                        context_parts.append(f"  Analysis {i}: {recommendations[0] if recommendations else 'No specific recommendations'}")

        # Add proven strategies
        if context.proven_strategies.get('behavior_recommendations'):
            context_parts.append(f"Proven Strategies: {context.proven_strategies['behavior_recommendations']}")

        return "\n  ".join(context_parts)

    def _build_circadian_agent_context(self, context: ContextEnhancedContext) -> str:
        """Build circadian-specific context"""
        context_parts = ["CIRCADIAN ANALYSIS CONTEXT:"]

        # Add AI context summary focused on timing
        context_parts.append(f"User Timing Patterns:\n{context.ai_context_summary}")

        # Add engagement timing insights
        insights = context.engagement_insights
        context_parts.append(f"Engagement Timing Data Available: {insights.get('calendar_selections_count', 0)} scheduled activities")

        # Add historical circadian patterns
        if context.circadian_analysis_history:
            context_parts.append("Previous Circadian Analysis Results:")
            for i, analysis in enumerate(context.circadian_analysis_history[:2], 1):
                result = analysis.get('analysis_result', {})
                if isinstance(result, dict):
                    chronotype = result.get('chronotype_assessment', {})
                    if chronotype:
                        primary_type = chronotype.get('primary_type', 'unknown')
                        context_parts.append(f"  Analysis {i}: Chronotype - {primary_type}")

        # Add timing preferences
        if context.proven_strategies.get('chronotype_insights'):
            chronotype_info = context.proven_strategies['chronotype_insights']
            context_parts.append(f"Established Chronotype: {chronotype_info}")

        return "\n  ".join(context_parts)

    def _build_routine_agent_context(self, context: ContextEnhancedContext) -> str:
        """Build routine-specific context"""
        context_parts = ["ROUTINE GENERATION CONTEXT:"]

        # Combine behavior and circadian insights
        context_parts.append(f"User Patterns Summary:\n{context.ai_context_summary}")

        # Add comprehensive historical context
        context_parts.append(f"Historical Context Available:")
        context_parts.append(f"  - {len(context.behavior_analysis_history)} behavior analyses")
        context_parts.append(f"  - {len(context.circadian_analysis_history)} circadian analyses")

        # Add adaptation preferences
        if context.adaptation_preferences:
            prefs = context.adaptation_preferences
            context_parts.append(f"Adaptation Preferences: {prefs.get('change_pace', 'moderate')} pace, {prefs.get('complexity_tolerance', 0.5)} complexity tolerance")

        return "\n  ".join(context_parts)

    async def _store_session_context(self, context: ContextEnhancedContext):
        """Store session context for reference"""
        session_data = {
            "analysis_mode": context.analysis_mode,
            "focus_areas": context.personalized_focus_areas,
            "session_start": context.created_at.isoformat(),
            "ai_context_length": len(context.ai_context_summary),
            "engagement_insights": context.engagement_insights
        }

        # Store in AI context service for consistency
        try:
            # Simple storage without complex working memory system
            logger.debug(f"[AI_CONTEXT_INTEGRATION] Session context prepared for {context.user_id}")
        except Exception as e:
            logger.error(f"Failed to store session context: {e}")

    async def store_analysis_insights(self, user_id: str, analysis_type: str, analysis_result: dict, archetype: str = None) -> bool:
        """
        Store analysis insights in holistic_analysis_results table
        Maintains compatibility with the original memory service interface
        """
        try:
            # Import database service - use Supabase client without connection pool for development
            from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
            import os

            # In development, disable connection pool to use Supabase REST API directly
            environment = os.getenv("ENVIRONMENT", "development").lower()
            use_pool = (environment != "development")

            db = SupabaseAsyncPGAdapter(use_connection_pool=use_pool)
            await db.connect()

            # Prepare analysis result for storage - convert to JSON if needed
            import json
            if isinstance(analysis_result, dict):
                # Supabase client expects dict directly, not JSON string
                analysis_result_data = analysis_result
            else:
                analysis_result_data = analysis_result

            # Store in holistic_analysis_results table using INSERT SQL
            # Generate input_summary for database constraint
            import json as json_lib
            if isinstance(analysis_result_data, dict):
                # Create a summary of the analysis for the input_summary column
                input_summary = {
                    "analysis_type": analysis_type,
                    "archetype": archetype or 'unknown',
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user_id": user_id[:8] + "..."
                }
                input_summary_json = json_lib.dumps(input_summary)
            else:
                input_summary_json = "{}"

            # For routine_plan, use UPSERT to update today's plan instead of creating duplicates
            if analysis_type == "routine_plan":
                # Use direct Supabase client for UPSERT (REST API doesn't support complex SQL parsing)
                if use_pool:
                    # Production: Use PostgreSQL UPSERT
                    today = datetime.now(timezone.utc).date()
                    check_query = """
                        SELECT id FROM holistic_analysis_results
                        WHERE user_id = $1 AND analysis_type = $2 AND archetype = $3
                        AND analysis_date = $4
                        LIMIT 1
                    """
                    existing = await db.fetchrow(check_query, user_id, analysis_type, archetype or 'unknown', today)

                    if existing:
                        # Update existing routine plan
                        update_query = """
                            UPDATE holistic_analysis_results
                            SET analysis_result = $1, input_summary = $2, created_at = $3
                            WHERE id = $4
                        """
                        result = await db.execute(
                            update_query,
                            analysis_result_data,
                            input_summary_json,
                            datetime.now(timezone.utc).isoformat(),
                            existing['id']
                        )
                    else:
                        # Insert new routine plan
                        insert_query = """
                            INSERT INTO holistic_analysis_results (user_id, analysis_type, archetype, analysis_result, input_summary, agent_id, created_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """
                        result = await db.execute(
                            insert_query,
                            user_id,
                            analysis_type,
                            archetype or 'unknown',
                            analysis_result_data,
                            input_summary_json,
                            'memory_service',
                            datetime.now(timezone.utc).isoformat()
                        )
                else:
                    # Development: Use Supabase REST API for UPSERT
                    # Check if today's routine exists
                    today = datetime.now(timezone.utc).date().isoformat()
                    from supabase import create_client
                    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

                    existing_result = supabase.table('holistic_analysis_results')\
                        .select('id')\
                        .eq('user_id', user_id)\
                        .eq('analysis_type', analysis_type)\
                        .eq('archetype', archetype or 'unknown')\
                        .eq('analysis_date', today)\
                        .limit(1)\
                        .execute()

                    update_data = {
                        'analysis_result': analysis_result_data,
                        'input_summary': input_summary_json,
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }

                    if existing_result.data:
                        # Update existing
                        result = supabase.table('holistic_analysis_results')\
                            .update(update_data)\
                            .eq('id', existing_result.data[0]['id'])\
                            .execute()
                    else:
                        # Insert new
                        insert_data = {
                            'user_id': user_id,
                            'analysis_type': analysis_type,
                            'archetype': archetype or 'unknown',
                            'analysis_result': analysis_result_data,
                            'input_summary': input_summary_json,
                            'agent_id': 'memory_service',
                            'created_at': datetime.now(timezone.utc).isoformat()
                        }
                        result = supabase.table('holistic_analysis_results')\
                            .insert(insert_data)\
                            .execute()

                    result = "UPDATE 1" if existing_result.data else "INSERT 1"
            else:
                # For behavior_analysis and circadian_analysis, always insert
                insert_query = """
                    INSERT INTO holistic_analysis_results (user_id, analysis_type, archetype, analysis_result, input_summary, agent_id, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                result = await db.execute(
                    insert_query,
                    user_id,
                    analysis_type,
                    archetype or 'unknown',
                    analysis_result_data,
                    input_summary_json,
                    'memory_service',
                    datetime.now(timezone.utc).isoformat()
                )

            if result:
                logger.info(f"[AI_CONTEXT_INTEGRATION] ✅ Stored {analysis_type} analysis for {user_id[:8]}...")
                return True
            else:
                logger.error(f"[AI_CONTEXT_INTEGRATION] ❌ Failed to store {analysis_type} analysis for {user_id}")
                return False

        except Exception as e:
            logger.error(f"[AI_CONTEXT_INTEGRATION] Error storing analysis insights: {e}", exc_info=True)
            return False
        finally:
            if 'db' in locals():
                await db.close()

    async def update_user_memory_profile(self, user_id: str, behavior_analysis: dict = None,
                                       nutrition_plan: dict = None, routine_plan: dict = None) -> bool:
        """
        Update user memory profile - simplified for AI context integration
        In the new system, this is handled by AI context generation, so this is a compatibility method
        """
        try:
            logger.debug(f"[AI_CONTEXT_INTEGRATION] Memory profile update for {user_id} - handled by AI context system")

            # In the AI context system, user profiles are updated through AI context generation
            # This method exists for API compatibility but actual updates happen via AI context

            return True

        except Exception as e:
            logger.error(f"[AI_CONTEXT_INTEGRATION] Error updating user memory profile: {e}")
            return False

    async def cleanup(self):
        """Clean shutdown"""
        if self.ai_context_service:
            await self.ai_context_service.cleanup()
            logger.debug("[AI_CONTEXT_INTEGRATION] Service cleaned up")

# Convenience function for easy integration (same as MemoryIntegrationService)
async def create_memory_enhanced_analysis_context(user_id: str, archetype: str = None) -> ContextEnhancedContext:
    """
    Convenience function to create AI context-enhanced context
    SAME INTERFACE as memory service for drop-in replacement
    """
    service = AIContextIntegrationService()
    try:
        context = await service.prepare_memory_enhanced_context(user_id, archetype=archetype)
        return context
    finally:
        await service.cleanup()