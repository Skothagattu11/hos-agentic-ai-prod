"""
Markdown Format Parser - For /routine/generate API

STRICT FORMAT SPECIFICATION:
This parser expects plans in the following format:

TIME BLOCK HEADERS (with COLON after time range):
**6:00 AM - 9:45 AM: Maintenance Zone - Gentle morning activation**
**10:00 AM - 12:00 PM: Peak Zone - Capitalize on peak energy**

TASK ITEMS (with COLON after time range):
- **6:00 AM - 6:30 AM:** Wake-up and hydration. Start with a glass of water.
- **10:00 AM - 11:30 AM:** Important meetings. Focus on challenging tasks.

PARSING RULES:
1. Time blocks MUST use colon (:) after the time range
2. Tasks MUST be bullet points (- ) with times in ** ** and colon after
3. Time format: "H:MM AM/PM" or "HH:MM AM/PM"
4. Tasks are nested under their time block

This format is enforced by the routine generation prompt in openai_main.py:4361-4405
"""
import re
import logging
from typing import Dict, Any, List
from datetime import datetime

from services.parsers.base_parser import BasePlanParser
from services.plan_extraction_service import TimeBlockContext, ExtractedTask

logger = logging.getLogger(__name__)


class MarkdownPlanParser(BasePlanParser):
    """Parser for markdown-formatted plans"""

    def can_parse(self, content: str) -> bool:
        """
        Check if content is markdown format with STRICT format requirements:
        - Time block headers: **H:MM AM/PM - H:MM AM/PM: Purpose**
        - Task items: - **H:MM AM/PM - H:MM AM/PM:** Task description

        This ensures we only parse content that matches our strict format specification.
        """
        # Primary pattern: **6:00 AM - 9:45 AM: Maintenance Zone**
        # This is the STRICT format we expect from generation
        strict_time_block_pattern = r'\*\*\d{1,2}:\d{2}\s*(?:AM|PM)?\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM)?\s*:\s*.+?\*\*'

        # Task pattern: - **6:00 AM - 6:30 AM:** Wake-up and hydration
        strict_task_pattern = r'-\s*\*\*\d{1,2}:\d{2}\s*(?:AM|PM)?\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM)?\s*:\*\*'

        has_time_blocks = bool(re.search(strict_time_block_pattern, content))
        has_tasks = bool(re.search(strict_task_pattern, content))

        # Must have at least time blocks in the correct format
        return has_time_blocks

    def parse(self, content: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse markdown-formatted plan using regex"""
        try:
            analysis_id = analysis_result.get('id', 'unknown')
            archetype = analysis_result.get('archetype', 'Unknown')

            # Extract time blocks using regex
            time_blocks = self._extract_time_blocks(content, analysis_id, archetype)

            # Extract tasks using regex
            tasks = self._extract_tasks(content, analysis_id, time_blocks)

            logger.info(f"✅ Markdown parser extracted {len(time_blocks)} blocks, {len(tasks)} tasks")
            return {'time_blocks': time_blocks, 'tasks': tasks}

        except Exception as e:
            logger.error(f"❌ Markdown parser failed: {e}")
            return {'time_blocks': [], 'tasks': []}

    def _extract_time_blocks(self, content: str, analysis_id: str, archetype: str) -> List[TimeBlockContext]:
        """
        Extract time blocks from markdown using STRICT format pattern.

        Expected format: **6:00 AM - 9:45 AM: Maintenance Zone**

        Pattern breakdown:
        - \*\* : Opening bold markers
        - (\d{1,2}:\d{2}\s*(?:AM|PM)?) : Start time (e.g., "6:00 AM")
        - \s*-\s* : Dash separator with optional whitespace
        - (\d{1,2}:\d{2}\s*(?:AM|PM)?) : End time (e.g., "9:45 AM")
        - :\s* : COLON separator (CRITICAL - this is what makes format strict)
        - ([^*]+) : Purpose/zone name (everything until closing **)
        - \*\* : Closing bold markers
        """
        time_blocks = []

        # Pattern: **6:00 AM - 9:45 AM: Maintenance Zone**
        block_pattern = r'\*\*(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*-\s*(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*:\s*([^*]+)\*\*'

        matches = re.finditer(block_pattern, content, re.MULTILINE)

        match_count = 0
        for i, match in enumerate(matches, 1):
            match_count += 1
            start_time = match.group(1).strip()
            end_time = match.group(2).strip()
            zone_name = match.group(3).strip()

            time_range = f"{start_time} - {end_time}"
            block_id = f"{analysis_id}_block_{i}"

            # Extract purpose/description from following lines
            block_start = match.end()
            next_block_match = re.search(block_pattern, content[block_start:])
            block_end = block_start + next_block_match.start() if next_block_match else len(content)
            block_content = content[block_start:block_end]

            # Look for Purpose
            purpose_match = re.search(r'-\s*\*\*Purpose:\*\*\s*(.+?)(?:\n|$)', block_content)
            purpose = purpose_match.group(1).strip() if purpose_match else zone_name

            time_block = TimeBlockContext(
                block_id=block_id,
                title=f"{zone_name} ({time_range}): {purpose}",
                time_range=time_range,
                purpose=purpose,
                why_it_matters=None,
                connection_to_insights=None,
                health_data_integration=None,
                block_order=i,
                parent_routine_id=analysis_id,
                archetype=archetype
            )
            time_blocks.append(time_block)
            logger.debug(f"📦 Extracted block {i}: {time_range} - {zone_name}")

        if match_count == 0:
            logger.warning("⚠️ No time blocks matched the strict format pattern. Expected: **H:MM AM/PM - H:MM AM/PM: Purpose**")
            # Log first 500 chars to help debug format issues
            logger.debug(f"Content preview: {content[:500]}")

        logger.info(f"✅ Extracted {len(time_blocks)} time blocks from markdown")
        return time_blocks

    def _extract_tasks(self, content: str, analysis_id: str, time_blocks: List[TimeBlockContext]) -> List[ExtractedTask]:
        """
        Extract tasks from markdown using flexible pattern.

        Expected format: - **6:00 AM - 6:30 AM:** Task title. Task description.

        The pattern handles:
        - Tasks with parentheses: "Workout (e.g., HIIT). Details here."
        - Tasks with multiple sentences: "Task. More details. Even more."
        - Tasks stopping at next task or time block header
        """
        tasks = []

        # Pattern: - **6:00 AM - 6:30 AM:** Full task content (until next task/block)
        # We'll parse title/description separately after matching
        task_pattern = r'-\s*\*\*(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*-\s*(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*:\*\*\s*(.+?)(?=\n\s*-\s*\*\*\d|\n\s*\*\*\d|\n\n|$)'

        matches = re.finditer(task_pattern, content, re.MULTILINE | re.DOTALL)

        for i, match in enumerate(matches, 1):
            start_time_str = match.group(1).strip()
            end_time_str = match.group(2).strip()
            full_content = match.group(3).strip()

            # Split title and description at first period
            # Handle cases like "Workout (e.g., HIIT). Details" correctly
            title = full_content
            description = ""

            # Find first period that's followed by space or newline (not like "e.g." or "etc.")
            period_match = re.search(r'\.(?:\s|$)', full_content)
            if period_match:
                split_pos = period_match.start() + 1
                title = full_content[:split_pos-1].strip()  # Remove the period
                description = full_content[split_pos:].strip()

            # Clean up: Remove any embedded time block headers from description
            description = re.sub(r'\*\*\d{1,2}:\d{2}\s*(?:AM|PM)?\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM)?\s*:.*?\*\*', '', description).strip()

            # Convert times
            scheduled_time = self._parse_time_string(self._convert_to_24h(start_time_str))
            scheduled_end_time = self._parse_time_string(self._convert_to_24h(end_time_str))

            # Calculate duration
            duration = None
            if scheduled_time and scheduled_end_time:
                duration = (datetime.combine(datetime.today(), scheduled_end_time) -
                           datetime.combine(datetime.today(), scheduled_time)).seconds // 60

                # Warn about suspicious durations (> 4 hours = 240 minutes)
                if duration > 240:
                    logger.warning(f"⚠️ Task {i} has suspicious duration: {duration} min ({start_time_str} - {end_time_str}). Title: '{title[:50]}'")

            # Find matching time block
            time_block_id = self._find_matching_block(scheduled_time, time_blocks, analysis_id)

            task_id = f"{analysis_id}_task_{i}"

            task = ExtractedTask(
                task_id=task_id,
                title=title,
                description=description,
                time_block_id=time_block_id,
                scheduled_time=scheduled_time,
                scheduled_end_time=scheduled_end_time,
                estimated_duration_minutes=duration,
                task_type='general',
                priority_level='medium',
                task_order_in_block=i,
                parent_routine_id=analysis_id
            )
            tasks.append(task)
            logger.debug(f"📝 Extracted task {i}: {start_time_str}-{end_time_str} | {title[:40]}")

        logger.info(f"✅ Extracted {len(tasks)} tasks from markdown")
        return tasks

    def _convert_to_24h(self, time_str: str) -> str:
        """Convert '6:00 AM' to '06:00'"""
        time_str = time_str.upper().strip()

        if 'AM' in time_str or 'PM' in time_str:
            is_pm = 'PM' in time_str
            time_str = time_str.replace('AM', '').replace('PM', '').strip()

            parts = time_str.split(':')
            hour = int(parts[0])
            minute = parts[1] if len(parts) > 1 else '00'

            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute}"

        return time_str

    def _find_matching_block(self, task_time, time_blocks: List[TimeBlockContext], analysis_id: str) -> str:
        """Find which time block this task belongs to"""
        if not task_time or not time_blocks:
            return f"{analysis_id}_block_1"

        for i, block in enumerate(time_blocks, 1):
            # Parse block time range
            time_range = block.time_range
            if '-' in time_range:
                start_str, end_str = time_range.split('-')
                start_time = self._parse_time_string(self._convert_to_24h(start_str.strip()))
                end_time = self._parse_time_string(self._convert_to_24h(end_str.strip()))

                if start_time and end_time:
                    if start_time <= task_time < end_time:
                        return f"{analysis_id}_block_{i}"

        # Default to first block
        return f"{analysis_id}_block_1"
