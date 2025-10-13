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

    def _convert_12h_to_24h(self, time_str: str) -> str:
        """Convert 12-hour format (e.g., '06:00 AM') to 24-hour format (e.g., '06:00')"""
        if not time_str:
            return time_str

        time_str = time_str.strip().upper()

        # Already 24-hour format (no AM/PM)
        if 'AM' not in time_str and 'PM' not in time_str:
            return time_str

        # Parse 12-hour format
        is_pm = 'PM' in time_str
        time_str = time_str.replace('AM', '').replace('PM', '').strip()

        try:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = parts[1] if len(parts) > 1 else '00'

            # Convert to 24-hour format
            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute}"
        except (ValueError, IndexError):
            return time_str

    def can_parse(self, content: str) -> bool:
        """Check if content is JSON with time_blocks (with nested tasks or separate plan_items)"""
        try:
            # Try to find JSON structure markers
            if '"time_blocks"' in content:
                # Try to parse as JSON
                data = json.loads(content)
                time_blocks = data.get('time_blocks', [])
                if isinstance(time_blocks, list) and len(time_blocks) > 0:
                    # Support both formats:
                    # 1. New format: tasks nested inside time_blocks
                    # 2. Old format: separate plan_items array
                    first_block = time_blocks[0] if time_blocks else {}
                    has_nested_tasks = 'tasks' in first_block
                    has_separate_items = 'plan_items' in data
                    return has_nested_tasks or has_separate_items
        except:
            pass
        return False

    def parse(self, content: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON-structured plan (supports both nested and separate task formats)"""
        try:
            data = json.loads(content)
            analysis_id = analysis_result.get('id', 'unknown')
            archetype = analysis_result.get('archetype', 'Unknown')

            # Parse time blocks
            time_blocks = []
            all_tasks = []
            task_counter = 1

            for i, block_data in enumerate(data.get('time_blocks', []), 1):
                block_id = f"{analysis_id}_block_{i}"

                # Build time_range from start_time and end_time
                start_time = block_data.get('start_time', '')
                end_time = block_data.get('end_time', '')
                time_range = f"{start_time} - {end_time}" if start_time and end_time else block_data.get('time_range', '')

                # Build title from block_name and time_range
                block_name = block_data.get('block_name', block_data.get('title', 'Block'))
                title = f"{block_name} ({time_range}): {block_data.get('purpose', '')}"

                time_block = TimeBlockContext(
                    block_id=block_id,
                    title=title,
                    time_range=time_range,
                    purpose=block_data.get('purpose', ''),
                    why_it_matters=block_data.get('why_it_matters'),
                    connection_to_insights=block_data.get('connection_to_insights'),
                    health_data_integration=block_data.get('health_data_integration'),
                    block_order=i,
                    parent_routine_id=analysis_id,
                    archetype=archetype
                )
                time_blocks.append(time_block)

                # NEW FORMAT: Parse nested tasks from this block
                nested_tasks = block_data.get('tasks', [])
                for task_data in nested_tasks:
                    task_id = f"{analysis_id}_task_{task_counter}"
                    task_counter += 1

                    # Parse times - convert 12-hour format to 24-hour first
                    start_time_str = task_data.get('start_time', '')
                    end_time_str = task_data.get('end_time', '')
                    scheduled_time = self._parse_time_string(self._convert_12h_to_24h(start_time_str))
                    scheduled_end_time = self._parse_time_string(self._convert_12h_to_24h(end_time_str))

                    # Calculate duration if not provided
                    duration = task_data.get('estimated_duration_minutes')
                    if not duration and scheduled_time and scheduled_end_time:
                        duration = (datetime.combine(datetime.today(), scheduled_end_time) -
                                   datetime.combine(datetime.today(), scheduled_time)).seconds // 60

                    task = ExtractedTask(
                        task_id=task_id,
                        title=task_data.get('title', 'Task'),
                        description=task_data.get('description', ''),
                        time_block_id=block_id,  # Already linked to this block
                        scheduled_time=scheduled_time,
                        scheduled_end_time=scheduled_end_time,
                        estimated_duration_minutes=duration,
                        task_type=task_data.get('task_type', 'general'),
                        priority_level=task_data.get('priority', task_data.get('priority_level', 'medium')),
                        task_order_in_block=len(all_tasks) + 1,
                        parent_routine_id=analysis_id
                    )
                    all_tasks.append(task)

            # OLD FORMAT: Parse plan_items as a separate array (backward compatibility)
            if 'plan_items' in data:
                for item_data in data.get('plan_items', []):
                    task_id = f"{analysis_id}_task_{task_counter}"
                    task_counter += 1

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
                        task_order_in_block=len(all_tasks) + 1,
                        parent_routine_id=analysis_id
                    )
                    all_tasks.append(task)

            logger.info(f"✅ JSON parser extracted {len(time_blocks)} blocks, {len(all_tasks)} tasks (nested format)")
            return {'time_blocks': time_blocks, 'tasks': all_tasks}

        except Exception as e:
            logger.error(f"❌ JSON parser failed: {e}", exc_info=True)
            return {'time_blocks': [], 'tasks': []}
