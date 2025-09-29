#!/usr/bin/env python3
"""
AI Context Generation Service

Implements the simple, AI-powered context generation approach designed to replace
the complex 4-layer memory system. Uses raw engagement data to create focused
context for personalized behavior and circadian analysis.

This service leverages the proven engagement APIs to gather raw data and uses
AI to generate actionable context summaries.
"""

import json
import logging
import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import openai
from supabase import create_client, Client
from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Get Supabase client instance with proper service role authentication"""
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    anon_key = os.getenv('SUPABASE_KEY')

    if not supabase_url:
        raise ValueError("SUPABASE_URL is required")

    # Prefer service key for API operations (bypasses RLS)
    if service_key:
        return create_client(supabase_url, service_key)
    else:
        return create_client(supabase_url, anon_key)

class SimpleEngagementDataService:
    """Fetch raw engagement data for AI analysis using proven APIs"""

    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        if self.environment == 'production':
            self.db = None  # Will use SupabaseAsyncPGAdapter
            self.use_rest_api = False
        else:
            self.supabase_client = get_supabase_client()  # Use the proven pattern
            self.db = None
            self.use_rest_api = True

    async def _ensure_db_connection(self):
        """Ensure database connection is available"""
        if not self.use_rest_api and not self.db:
            self.db = SupabaseAsyncPGAdapter()
            await self.db.connect()
        return self.db

    async def get_raw_engagement_data(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get all raw engagement data for AI analysis using existing APIs
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            if self.use_rest_api:
                # Use same logic as APIs but directly via Supabase client
                engagement_context = await self._get_engagement_context_direct(user_id, days)
                journal_history = await self._get_journal_history_direct(user_id, min(days, 30))

                # Parse engagement context to separate calendar and checkins
                calendar_items = []
                checkin_data = []
                plan_items = []

                if engagement_context and 'planned_tasks' in engagement_context:
                    for task in engagement_context['planned_tasks']:
                        # Tasks with calendar info are calendar selections
                        if task.get('added_to_calendar'):
                            calendar_items.append({
                                'title': task.get('title'),
                                'task_type': task.get('task_type'),
                                'time_block': task.get('time_block'),
                                'estimated_duration_minutes': task.get('estimated_duration_minutes'),
                                'selection_timestamp': task.get('calendar_added_at'),
                                'calendar_notes': task.get('calendar_notes')
                            })

                        # Tasks with completion status are check-ins
                        if 'completion_status' in task:
                            checkin_data.append({
                                'title': task.get('title'),
                                'task_type': task.get('task_type'),
                                'time_block': task.get('time_block'),
                                'completion_status': task.get('completion_status'),
                                'satisfaction_rating': task.get('satisfaction_rating'),
                                'user_notes': task.get('user_notes'),
                                'planned_date': task.get('planned_date'),
                                'completed_at': task.get('completed_at')
                            })

                        # All tasks are plan items
                        plan_items.append({
                            'title': task.get('title'),
                            'description': task.get('description'),
                            'task_type': task.get('task_type'),
                            'time_block': task.get('time_block'),
                            'estimated_duration_minutes': task.get('estimated_duration_minutes'),
                            'plan_date': task.get('plan_date'),
                            'is_trackable': task.get('is_trackable')
                        })

                return {
                    "calendar_selections": calendar_items,
                    "task_checkins": checkin_data,
                    "daily_journals": journal_history or [],
                    "recent_plan_items": plan_items,
                    "data_period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "days_analyzed": days
                    }
                }
            else:
                # Production - use database adapter
                return await self._get_engagement_data_db(user_id, days)

        except Exception as e:
            logger.error(f"Failed to get raw engagement data for {user_id}: {e}")
            return {
                "calendar_selections": [],
                "task_checkins": [],
                "daily_journals": [],
                "recent_plan_items": [],
                "data_period": {"error": str(e)}
            }

    async def _get_engagement_context_direct(self, user_id: str, days: int) -> Optional[Dict]:
        """Get engagement data using separate, simple queries"""
        try:
            from datetime import timedelta
            start_date = (date.today() - timedelta(days=days)).isoformat()

            # Get plan items first
            plan_items = self.supabase_client.table("plan_items")\
                .select("*")\
                .eq("profile_id", user_id)\
                .gte("plan_date", start_date)\
                .order("plan_date", desc=True)\
                .execute()

            # Get calendar selections - use specific date filtering
            calendar_selections = self.supabase_client.table("calendar_selections")\
                .select("*")\
                .eq("profile_id", user_id)\
                .gte("selection_timestamp", start_date + "T00:00:00")\
                .execute()

            # Get task checkins - use specific date filtering
            task_checkins = self.supabase_client.table("task_checkins")\
                .select("*")\
                .eq("profile_id", user_id)\
                .gte("planned_date", start_date)\
                .execute()

            # Combine the data
            planned_tasks = []
            if plan_items.data:
                for plan_item in plan_items.data:
                    task_data = plan_item.copy()

                    # Add calendar selection info if exists
                    calendar_info = None
                    if calendar_selections.data:
                        calendar_info = next((cs for cs in calendar_selections.data
                                            if cs.get('plan_item_id') == plan_item.get('id')), None)
                    if calendar_info:
                        task_data.update({
                            'added_to_calendar': True,
                            'calendar_added_at': calendar_info.get('selection_timestamp'),
                            'calendar_notes': calendar_info.get('calendar_notes')
                        })

                    # Add task checkin info if exists
                    checkin_info = None
                    if task_checkins.data:
                        checkin_info = next((tc for tc in task_checkins.data
                                           if tc.get('plan_item_id') == plan_item.get('id')), None)
                    if checkin_info:
                        task_data.update({
                            'completion_status': checkin_info.get('completion_status'),
                            'satisfaction_rating': checkin_info.get('satisfaction_rating'),
                            'user_notes': checkin_info.get('user_notes'),
                            'completed_at': checkin_info.get('completed_at')
                        })

                    planned_tasks.append(task_data)

            return {"planned_tasks": planned_tasks}

        except Exception as e:
            logger.error(f"Failed to get engagement context directly: {e}")
            return None

    async def _get_journal_history_direct(self, user_id: str, days: int) -> Optional[List[Dict]]:
        """Use the same logic as journal history API but directly"""
        try:
            from datetime import timedelta
            start_date = (date.today() - timedelta(days=days)).isoformat()

            # Same query pattern as engagement_endpoints.py
            result = self.supabase_client.table("daily_journals")\
                .select("*")\
                .eq("profile_id", user_id)\
                .gte("journal_date", start_date)\
                .order("journal_date", desc=True)\
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Failed to get journal history directly: {e}")
            return None

    async def _get_engagement_data_db(self, user_id: str, days: int) -> Dict[str, Any]:
        """Fallback database method for production"""
        try:
            db = await self._ensure_db_connection()
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Use database adapter queries for production
            calendar_query = """
                SELECT cs.*, pi.title, pi.task_type, pi.time_block
                FROM calendar_selections cs
                JOIN plan_items pi ON cs.plan_item_id = pi.id
                WHERE cs.profile_id = $1 AND cs.selection_timestamp >= $2
            """
            calendar_items = await db.fetch(calendar_query, user_id, start_date)

            checkin_query = """
                SELECT tc.*, pi.title, pi.task_type, pi.time_block
                FROM task_checkins tc
                JOIN plan_items pi ON tc.plan_item_id = pi.id
                WHERE tc.profile_id = $1 AND tc.planned_date >= $2
            """
            checkin_data = await db.fetch(checkin_query, user_id, start_date.date())

            journal_query = """
                SELECT * FROM daily_journals
                WHERE profile_id = $1 AND journal_date >= $2
                ORDER BY journal_date DESC
            """
            journal_data = await db.fetch(journal_query, user_id, start_date.date())

            plan_query = """
                SELECT pi.*, ar.archetype FROM plan_items pi
                LEFT JOIN holistic_analysis_results ar ON pi.analysis_result_id = ar.id
                WHERE pi.profile_id = $1 AND pi.plan_date >= $2
                ORDER BY pi.created_at DESC LIMIT 20
            """
            plan_items = await db.fetch(plan_query, user_id, start_date.date())

            return {
                "calendar_selections": [dict(row) for row in calendar_items] if calendar_items else [],
                "task_checkins": [dict(row) for row in checkin_data] if checkin_data else [],
                "daily_journals": [dict(row) for row in journal_data] if journal_data else [],
                "recent_plan_items": [dict(row) for row in plan_items] if plan_items else [],
                "data_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days_analyzed": days
                }
            }
        except Exception as e:
            logger.error(f"Failed to get engagement data via database: {e}")
            return {
                "calendar_selections": [],
                "task_checkins": [],
                "daily_journals": [],
                "recent_plan_items": [],
                "data_period": {"error": str(e)}
            }

    async def cleanup(self):
        """Cleanup database connections"""
        if self.db and hasattr(self.db, 'close'):
            await self.db.close()
        elif self.db and hasattr(self.db, 'cleanup'):
            await self.db.cleanup()


class AIEngagementAnalyzer:
    """Use AI to analyze raw engagement data and generate context"""

    def __init__(self):
        self.openai_client = openai.AsyncOpenAI()

    async def generate_context(self, raw_data: Dict[str, Any], user_id: str, archetype: str = None) -> str:
        """Generate context from raw engagement data"""
        try:
            # Prepare data summary for AI analysis
            calendar_count = len(raw_data.get('calendar_selections', []))
            checkin_count = len(raw_data.get('task_checkins', []))
            journal_count = len(raw_data.get('daily_journals', []))
            plan_items_count = len(raw_data.get('recent_plan_items', []))

            # Calculate completion patterns
            checkins = raw_data.get('task_checkins', [])
            completed_count = sum(1 for c in checkins if c.get('completion_status') == 'completed')
            completion_rate = (completed_count / len(checkins) * 100) if checkins else 0

            # Prepare AI prompt
            prompt = f"""
Analyze this user's health engagement data and create a focused context summary for personalized behavior and circadian rhythm analysis.

USER PROFILE:
- User ID: {user_id[:8]}...
- Archetype: {archetype or 'Not specified'}
- Data Period: {raw_data.get('data_period', {}).get('days_analyzed', 30)} days

ENGAGEMENT METRICS:
- Calendar Selections: {calendar_count} items planned
- Task Check-ins: {checkin_count} tasks tracked
- Completion Rate: {completion_rate:.1f}%
- Daily Journals: {journal_count} entries
- Recent Plan Items: {plan_items_count} tasks analyzed

CALENDAR SELECTIONS (What they planned to focus on):
{json.dumps(raw_data.get('calendar_selections', []), indent=2, default=str)}

TASK CHECK-INS (What they actually did and how they felt):
{json.dumps(raw_data.get('task_checkins', []), indent=2, default=str)}

DAILY JOURNALS (Overall patterns and reflections):
{json.dumps(raw_data.get('daily_journals', []), indent=2, default=str)}

RECENT PLAN ITEMS (Available tasks and structure):
{json.dumps(raw_data.get('recent_plan_items', [])[:10], indent=2, default=str)}

Create a concise context summary covering:
1. **Engagement Patterns**: What types of tasks they consistently complete vs struggle with
2. **Timing Preferences**: When they're most successful (morning, afternoon, evening patterns)
3. **Satisfaction Trends**: What activities give them highest satisfaction ratings
4. **Recent Changes**: Any shifts in behavior, energy, or preferences
5. **Optimization Opportunities**: Key insights for improving future behavior and circadian analysis
6. **Avoid Patterns**: What strategies or timings have consistently failed

Focus on actionable insights that will help personalize behavior analysis and circadian rhythm recommendations.
Keep it concise but specific to this user's actual patterns.
"""

            # Generate AI analysis
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )

            context_summary = response.choices[0].message.content

            logger.info(f"Generated AI context for user {user_id[:8]}... ({len(context_summary)} chars)")
            return context_summary

        except Exception as e:
            logger.error(f"Failed to generate AI context for {user_id}: {e}")
            return f"Context generation failed: {str(e)}"


class AIContextGeneratorService:
    """Main orchestrator for AI-powered context generation"""

    def __init__(self):
        self.engagement_service = SimpleEngagementDataService()
        self.ai_analyzer = AIEngagementAnalyzer()
        self.environment = os.getenv('ENVIRONMENT', 'development')
        if self.environment == 'production':
            self.db = None  # Will use SupabaseAsyncPGAdapter
            self.use_rest_api = False
        else:
            self.supabase_client = get_supabase_client()  # Use the proven pattern
            self.db = None
            self.use_rest_api = True

    async def _ensure_db_connection(self):
        """Ensure database connection is available"""
        if not self.db:
            self.db = SupabaseAsyncPGAdapter()
            await self.db.connect()
        return self.db

    async def generate_user_context(self, user_id: str, archetype: str = None, days: int = 30) -> str:
        """
        Generate complete user context including engagement data
        This is the main method that replaces the complex memory system
        """
        try:
            logger.info(f"Generating AI context for user {user_id[:8]}... (archetype: {archetype})")

            # 1. Get raw engagement data
            raw_data = await self.engagement_service.get_raw_engagement_data(user_id, days)

            # 2. Get previous context for iterative improvement
            previous_context = await self._get_last_context(user_id)

            # 3. Get last 3 plans for pattern analysis
            last_plans = await self._get_last_plans(user_id, archetype, limit=3)

            # Add previous context and plans to raw data
            raw_data['previous_context'] = previous_context
            raw_data['last_plans'] = last_plans

            # 4. Generate AI context
            context_summary = await self.ai_analyzer.generate_context(raw_data, user_id, archetype)

            # 5. Store context for future reference
            await self._store_context(user_id, context_summary, raw_data, archetype)

            logger.info(f"Successfully generated context for user {user_id[:8]}...")
            return context_summary

        except Exception as e:
            logger.error(f"Failed to generate user context for {user_id}: {e}")
            return f"Failed to generate personalized context: {str(e)}"

    async def enhance_analysis_prompt(self, base_prompt: str, user_id: str, archetype: str = None) -> str:
        """
        Add user context to analysis prompts
        This replaces the complex memory prompt enhancement
        """
        try:
            # Get or generate current context
            context = await self.generate_user_context(user_id, archetype)

            if context and not context.startswith("Failed"):
                enhanced_prompt = f"""
{base_prompt}

USER PERSONALIZATION CONTEXT:
{context}

Use this context to personalize your analysis. Focus on:
- Building on what has worked for this user previously
- Avoiding patterns that have consistently failed
- Optimizing timing based on their successful patterns
- Adapting recommendations to their engagement style and preferences

Make your analysis specific to this user's proven patterns and preferences.
"""
                logger.info(f"Enhanced prompt for user {user_id[:8]}... with AI context")
                return enhanced_prompt
            else:
                logger.warning(f"No valid context available for user {user_id[:8]}..., using base prompt")
                return base_prompt

        except Exception as e:
            logger.error(f"Failed to enhance prompt for {user_id}: {e}")
            return base_prompt

    async def _get_last_context(self, user_id: str) -> Optional[str]:
        """Get most recent context for this user"""
        try:
            if self.use_rest_api:
                # Use REST API in development
                context = self.supabase_client.table('holistic_memory_analysis_context')\
                    .select('context_summary, created_at')\
                    .eq('user_id', user_id)\
                    .order('created_at', desc=True)\
                    .limit(1)\
                    .execute()
                return context.data[0]['context_summary'] if context.data else None
            else:
                # Use database adapter in production
                db = await self._ensure_db_connection()
                query = """
                    SELECT context_summary, created_at
                    FROM holistic_memory_analysis_context
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                result = await db.fetchrow(query, user_id)
                return result['context_summary'] if result else None

        except Exception as e:
            logger.error(f"Failed to get last context for {user_id}: {e}")
            return None

    async def _get_last_plans(self, user_id: str, archetype: str = None, limit: int = 3) -> List[Dict]:
        """Get last N plans from analysis results, optionally filtered by archetype"""
        try:
            if self.use_rest_api:
                # Use REST API in development
                query = self.supabase_client.table('holistic_analysis_results')\
                    .select('id, analysis_type, archetype, analysis_result, created_at')\
                    .eq('user_id', user_id)

                if archetype:
                    query = query.eq('archetype', archetype)

                plans = query.order('created_at', desc=True)\
                    .limit(limit)\
                    .execute()
                return plans.data
            else:
                # Use database adapter in production
                db = await self._ensure_db_connection()
                base_query = """
                    SELECT id, analysis_type, archetype, analysis_result, created_at
                    FROM holistic_analysis_results
                    WHERE user_id = $1
                """
                params = [user_id]
                if archetype:
                    base_query += " AND archetype = $2"
                    params.append(archetype)
                base_query += " ORDER BY created_at DESC LIMIT ${}".format(len(params) + 1)
                params.append(limit)
                result = await db.fetch(base_query, *params)
                return [dict(row) for row in result] if result else []

        except Exception as e:
            logger.error(f"Failed to get last plans for {user_id}: {e}")
            return []

    async def _store_context(self, user_id: str, context_summary: str, source_data: Dict, archetype: str = None):
        """Store generated context in database"""
        try:
            # Prepare source data for storage (remove large objects for performance)
            storage_data = {
                'calendar_count': len(source_data.get('calendar_selections', [])),
                'checkin_count': len(source_data.get('task_checkins', [])),
                'journal_count': len(source_data.get('daily_journals', [])),
                'data_period': source_data.get('data_period', {}),
                'generation_timestamp': datetime.now().isoformat()
            }

            if self.use_rest_api:
                # Use REST API in development
                result = self.supabase_client.table('holistic_memory_analysis_context')\
                    .insert({
                        'user_id': user_id,
                        'context_summary': context_summary,
                        'source_data': storage_data,
                        'archetype': archetype,
                        'engagement_data_included': True,
                        'data_period_days': 30,
                        'generation_method': 'ai_raw_data'
                    })\
                    .execute()
                logger.info(f"Stored context for user {user_id[:8]}... via REST API")
            else:
                # Use database adapter in production
                db = await self._ensure_db_connection()
                await self._ensure_context_table()
                query = """
                    INSERT INTO holistic_memory_analysis_context (
                        user_id, context_summary, source_data, archetype,
                        engagement_data_included, data_period_days, generation_method
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """
                result = await db.fetchrow(
                    query, user_id, context_summary, json.dumps(storage_data),
                    archetype, True, 30, 'ai_raw_data'
                )
                logger.info(f"Stored context for user {user_id[:8]}... (ID: {result['id'] if result else 'unknown'})")

        except Exception as e:
            logger.error(f"Failed to store context for {user_id}: {e}")

    async def _ensure_context_table(self):
        """Ensure the holistic_memory_analysis_context table exists"""
        try:
            db = await self._ensure_db_connection()

            create_table_query = """
                CREATE TABLE IF NOT EXISTS holistic_memory_analysis_context (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id TEXT NOT NULL,
                    context_summary TEXT NOT NULL,
                    source_data JSONB,
                    archetype TEXT,
                    engagement_data_included BOOLEAN DEFAULT FALSE,
                    data_period_days INTEGER DEFAULT 30,
                    generation_method VARCHAR(50) DEFAULT 'ai_raw_data',
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_holistic_memory_analysis_context_user_date
                ON holistic_memory_analysis_context (user_id, created_at DESC);
            """

            await db.execute(create_table_query)

        except Exception as e:
            logger.error(f"Failed to ensure context table: {e}")

    async def cleanup(self):
        """Cleanup all services"""
        try:
            await self.engagement_service.cleanup()
            if self.db and hasattr(self.db, 'close'):
                await self.db.close()
            elif self.db and hasattr(self.db, 'cleanup'):
                await self.db.cleanup()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Export main service class
__all__ = ['AIContextGeneratorService', 'SimpleEngagementDataService', 'AIEngagementAnalyzer']