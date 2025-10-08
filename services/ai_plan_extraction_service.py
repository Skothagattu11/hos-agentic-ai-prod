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
from datetime import datetime
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
        self.client = openai_client or openai.OpenAI()

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

        prompt = f"""
        Extract the complete plan structure from this routine content. Return JSON with this exact format:

        {{
          "time_blocks": [
            {{
              "title": "Morning Activation (6:30-7:30 AM): Foundation Setting",
              "time_range": "6:30-7:30 AM",
              "purpose": "Foundation Setting",
              "block_order": 1
            }}
          ],
          "tasks": [
            {{
              "title": "10-minute mindfulness meditation",
              "description": "Begin with a 10-minute mindfulness meditation to boost mental clarity",
              "time_block_order": 1,
              "scheduled_time": "06:30",
              "scheduled_end_time": "06:40",
              "estimated_duration_minutes": 10,
              "task_type": "wellness",
              "priority_level": "medium"
            }}
          ]
        }}

        Content to analyze:
        {content}

        CRITICAL INSTRUCTIONS:
        1. Extract ALL time blocks and their individual actionable tasks
        2. For each task, MUST extract the scheduled_time and scheduled_end_time in HH:MM format (24-hour)
        3. Look for patterns like "6:00 AM - 6:30 AM" or "6:00-6:30 AM" or "10:00 AM - 11:30 AM"
        4. Convert to 24-hour format: "6:00 AM" → "06:00", "2:00 PM" → "14:00", "10:00 PM" → "22:00"
        5. Only extract times that are explicitly specified in the content - do NOT infer, calculate, or generate times
        6. If no time is specified for a task, leave scheduled_time and scheduled_end_time as null

        Task types: wellness/exercise/nutrition/productivity/recovery
        Priority levels: low/medium/high

        Return only valid JSON, no explanation.
        """

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )

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
                    why_it_matters=None,
                    connection_to_insights=None,
                    health_data_integration=None,
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

                task = ExtractedTask(
                    task_id=task_id,
                    title=task_data.get('title', 'Activity'),
                    description=task_data.get('description', ''),
                    time_block_id=time_block_id,
                    scheduled_time=task_data.get('scheduled_time'),
                    scheduled_end_time=task_data.get('scheduled_end_time'),
                    estimated_duration_minutes=task_data.get('estimated_duration_minutes'),
                    task_type=task_data.get('task_type', 'general'),
                    priority_level=task_data.get('priority_level', 'medium'),
                    task_order_in_block=global_task_order,
                    parent_routine_id=analysis_id
                )
                tasks.append(task)
                global_task_order += 1

            return {
                'time_blocks': time_blocks,
                'tasks': tasks
            }

        except Exception as e:
            logger.error(f"❌ Single AI extraction failed: {str(e)}")
            return {'time_blocks': [], 'tasks': []}


# Convenience function for easy integration
async def extract_plan_with_ai(content: str, analysis_result: Dict[str, Any]) -> ExtractedPlan:
    """Convenience function - same signature as regex version"""
    service = AIPlanExtractionService()
    return await service.extract_plan_with_ai(content, analysis_result)