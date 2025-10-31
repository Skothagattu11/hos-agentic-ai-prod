#!/usr/bin/env python3
"""
AI-Powered Plan Extraction Service

Bulletproof task extraction using OpenAI models - format agnostic.
Provides the same output as regex-based extraction but handles any future format changes.
"""

import json
import logging
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, time
import openai
from dataclasses import asdict

from services.plan_extraction_service import ExtractedTask, ExtractedPlan, TimeBlockContext
from shared_libs.exceptions.holisticos_exceptions import HolisticOSException

logger = logging.getLogger(__name__)

# Production logging control - only errors and warnings in production
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
PRODUCTION_MODE = ENVIRONMENT == 'production'

class AIPlanExtractionService:
    """AI-powered plan extraction service - bulletproof for any format changes"""

    def __init__(self, openai_client=None):
        """Initialize with OpenAI client"""
        # Configure with AGGRESSIVE timeout settings for fast failure
        self.client = openai_client or openai.OpenAI(
            max_retries=1,  # Only retry once (fail fast)
            timeout=10.0    # 10 second timeout per request (total max: ~20s with retry)
        )

    def _parse_time_string(self, time_str: Optional[str]) -> Optional[time]:
        """Convert HH:MM string to datetime.time object"""
        if not time_str:
            return None
        try:
            # Parse HH:MM format (24-hour)
            hour, minute = map(int, time_str.split(':'))
            return time(hour=hour, minute=minute)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse time string '{time_str}': {e}")
            return None

    async def extract_plan_with_ai(self, content: str, analysis_result: Dict[str, Any]) -> ExtractedPlan:
        """
        Extract plan using AI - single call for everything, fast and efficient

        Returns same structure as regex-based extraction for perfect compatibility
        """
        try:
            # Extract metadata
            archetype = analysis_result.get('archetype', 'Unknown')
            analysis_id = analysis_result.get('id', 'unknown')
            user_id = analysis_result.get('user_id', 'unknown')
            date = datetime.now().strftime('%Y-%m-%d')

            # SINGLE AI CALL: Extract everything at once
            extraction_result = await self._extract_complete_plan_ai(content, analysis_id, archetype)

            return ExtractedPlan(
                plan_id=analysis_id,  # Add missing plan_id
                time_blocks=extraction_result['time_blocks'],
                tasks=extraction_result['tasks'],
                archetype=archetype,
                user_id=user_id,
                date=date
            )

        except Exception as e:
            logger.error(f"❌ AI extraction failed: {str(e)}")
            raise HolisticOSException(f"AI plan extraction failed: {str(e)}")

    async def _extract_complete_plan_ai(self, content: str, analysis_id: str, archetype: str) -> Dict[str, Any]:
        """Single AI call to extract both time blocks and tasks - efficient and fast"""

        # OPTIMIZED: Shorter prompt = faster response
        prompt = f"""Extract plan structure as JSON:

{{
  "time_blocks": [{{"title": "Zone (time): purpose", "time_range": "HH:MM-HH:MM AM/PM", "purpose": "text", "block_order": 1}}],
  "tasks": [{{"title": "task", "description": "desc", "time_block_order": 1, "scheduled_time": "HH:MM", "scheduled_end_time": "HH:MM", "estimated_duration_minutes": 30, "task_type": "wellness", "category": "exercise", "priority_level": "medium"}}]
}}

Rules:
1. Extract time blocks with UNIQUE titles including time range
2. Extract tasks with 24-hour HH:MM times (06:00 not 6:00 AM)
3. Link tasks to blocks via time_block_order (1=first block, 2=second, etc)
4. Only extract explicit times, don't infer
5. Types: wellness/exercise/nutrition/productivity/recovery
6. Categories: nutrition/exercise/hydration/recovery/movement/mindfulness/sleep/social

Content:
{content[:3000]}

Return JSON only."""

        try:
            import time
            start_time = time.time()

            # Use gpt-4o-mini - best balance of speed, cost, and quality
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4o-mini",  # Fast, accurate, cost-effective
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000  # Limit response size for speed
            )

            api_time = time.time() - start_time
            logger.info(f"⚡ OpenAI API call completed in {api_time:.2f}s")

            result = json.loads(response.choices[0].message.content)

            # Process time blocks
            time_blocks = []
            blocks_data = result.get('time_blocks', [])

            for i, block_data in enumerate(blocks_data, 1):
                block_id = f"{analysis_id}_block_{i}"
                time_block = TimeBlockContext(
                    block_id=block_id,
                    title=block_data.get('title', f'Time Block {i}'),
                    time_range=block_data.get('time_range', 'Not specified'),
                    purpose=block_data.get('purpose', 'General activity'),
                    why_it_matters=block_data.get('why_it_matters'),
                    connection_to_insights=block_data.get('connection_to_insights'),
                    health_data_integration=block_data.get('health_data_integration'),
                    block_order=block_data.get('block_order', i),
                    parent_routine_id=analysis_id,
                    archetype=archetype
                )
                time_blocks.append(time_block)

            # Process tasks
            tasks = []
            tasks_data = result.get('tasks', [])
            global_task_order = 1

            for task_data in tasks_data:
                task_id = f"{analysis_id}_task_{global_task_order}"
                time_block_order = task_data.get('time_block_order', 1)

                # Find corresponding time block
                time_block_id = f"{analysis_id}_block_{time_block_order}"

                # Parse time strings to time objects
                scheduled_time = self._parse_time_string(task_data.get('scheduled_time'))
                scheduled_end_time = self._parse_time_string(task_data.get('scheduled_end_time'))

                task = ExtractedTask(
                    task_id=task_id,
                    title=task_data.get('title', 'Activity'),
                    description=task_data.get('description', ''),
                    time_block_id=time_block_id,
                    scheduled_time=scheduled_time,
                    scheduled_end_time=scheduled_end_time,
                    estimated_duration_minutes=task_data.get('estimated_duration_minutes'),
                    task_type=task_data.get('task_type', 'general'),
                    category=task_data.get('category'),  # Extract category from AI response
                    priority_level=task_data.get('priority_level', 'medium'),
                    task_order_in_block=global_task_order,
                    parent_routine_id=analysis_id
                )
                tasks.append(task)
                global_task_order += 1

            # Extract archetype connection for overall plan context
            archetype_connection = result.get('archetype_connection')

            return {
                'time_blocks': time_blocks,
                'tasks': tasks,
                'archetype_connection': archetype_connection
            }

        except Exception as e:
            logger.error(f"❌ Single AI extraction failed: {str(e)}")
            return {'time_blocks': [], 'tasks': [], 'archetype_connection': None}


# Convenience function for easy integration
async def extract_plan_with_ai(content: str, analysis_result: Dict[str, Any]) -> ExtractedPlan:
    """Convenience function - same signature as regex version"""
    service = AIPlanExtractionService()
    return await service.extract_plan_with_ai(content, analysis_result)