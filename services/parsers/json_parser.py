"""
JSON Format Parser - For /routine/generate-markdown API
Parses pre-structured JSON with time_blocks and plan_items arrays
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from services.parsers.base_parser import BasePlanParser
from services.plan_extraction_service import TimeBlockContext, ExtractedTask

logger = logging.getLogger(__name__)


class JsonPlanParser(BasePlanParser):
    """Parser for JSON-structured plans from chatbot"""

    def can_parse(self, content: str) -> bool:
        """Check if content is JSON with time_blocks and plan_items"""
        try:
            # Try to find JSON structure markers
            if '"time_blocks"' in content and '"plan_items"' in content:
                # Try to parse as JSON
                data = json.loads(content)
                return isinstance(data.get('time_blocks'), list) and isinstance(data.get('plan_items'), list)
        except:
            pass
        return False

    def parse(self, content: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON-structured plan"""
        try:
            data = json.loads(content)
            analysis_id = analysis_result.get('id', 'unknown')
            archetype = analysis_result.get('archetype', 'Unknown')

            # Parse time blocks
            time_blocks = []
            for i, block_data in enumerate(data.get('time_blocks', []), 1):
                block_id = f"{analysis_id}_block_{i}"

                time_block = TimeBlockContext(
                    block_id=block_id,
                    title=f"{block_data.get('title', 'Block')} ({block_data.get('time_range', 'Time')}): {block_data.get('purpose', '')}",
                    time_range=block_data.get('time_range', ''),
                    purpose=block_data.get('purpose', ''),
                    why_it_matters=block_data.get('why_it_matters'),
                    connection_to_insights=block_data.get('connection_to_insights'),
                    health_data_integration=block_data.get('health_data_integration'),
                    block_order=i,
                    parent_routine_id=analysis_id,
                    archetype=archetype
                )
                time_blocks.append(time_block)

            # Parse plan items (tasks)
            tasks = []
            for i, item_data in enumerate(data.get('plan_items', []), 1):
                task_id = f"{analysis_id}_task_{i}"

                # Find matching time block by title
                time_block_title = item_data.get('time_block', '')
                time_block_id = None
                for idx, tb in enumerate(time_blocks, 1):
                    if time_block_title in tb.title or tb.title.startswith(time_block_title):
                        time_block_id = f"{analysis_id}_block_{idx}"
                        break

                # Fallback to first block if no match
                if not time_block_id and time_blocks:
                    time_block_id = f"{analysis_id}_block_1"

                # Parse times
                scheduled_time = self._parse_time_string(item_data.get('scheduled_time', ''))
                scheduled_end_time = self._parse_time_string(item_data.get('scheduled_end_time', ''))

                task = ExtractedTask(
                    task_id=task_id,
                    title=item_data.get('title', 'Task'),
                    description=item_data.get('description', ''),
                    time_block_id=time_block_id,
                    scheduled_time=scheduled_time,
                    scheduled_end_time=scheduled_end_time,
                    estimated_duration_minutes=item_data.get('estimated_duration_minutes'),
                    task_type=item_data.get('task_type', 'general'),
                    priority_level=item_data.get('priority_level', 'medium'),
                    task_order_in_block=i,
                    parent_routine_id=analysis_id
                )
                tasks.append(task)

            logger.info(f"✅ JSON parser extracted {len(time_blocks)} blocks, {len(tasks)} tasks")
            return {'time_blocks': time_blocks, 'tasks': tasks}

        except Exception as e:
            logger.error(f"❌ JSON parser failed: {e}")
            return {'time_blocks': [], 'tasks': []}
