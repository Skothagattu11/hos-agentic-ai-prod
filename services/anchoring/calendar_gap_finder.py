"""
Calendar Gap Finder - Phase 1

This service identifies available time slots (gaps) between calendar events
for anchoring AI-generated wellness tasks.

Algorithm:
1. Sort events by start time
2. Detect gaps between consecutive events
3. Filter gaps by minimum duration (default: 15 minutes)
4. Exclude user sleep hours (default: 10 PM - 6 AM)
5. Categorize gaps by size (small, medium, large)

Key Features:
- Pure algorithmic (no AI, no database)
- Fast execution (<100ms)
- Handles edge cases (overlapping events, all-day events)
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime, date, time, timedelta
from dataclasses import dataclass
from enum import Enum

from .calendar_integration_service import CalendarEvent

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class GapType(str, Enum):
    """Type of time gap relative to calendar events"""
    MORNING_START = "morning_start"      # Before first event
    BETWEEN_EVENTS = "between_events"    # Between two events
    EVENING_END = "evening_end"          # After last event
    FULL_DAY = "full_day"               # No events at all


class GapSize(str, Enum):
    """Size category of time gap"""
    SMALL = "small"      # 15-30 minutes
    MEDIUM = "medium"    # 30-60 minutes
    LARGE = "large"      # 60+ minutes


@dataclass
class AvailableSlot:
    """
    Represents an available time slot for task anchoring

    This model is used by the anchoring algorithm to determine
    where tasks can be placed in the user's schedule.
    """
    slot_id: str
    start_time: time
    end_time: time
    duration_minutes: int
    gap_type: GapType
    gap_size: GapSize
    before_event_title: Optional[str] = None
    after_event_title: Optional[str] = None
    before_event_id: Optional[str] = None
    after_event_id: Optional[str] = None

    def can_fit_task(self, task_duration_minutes: int) -> bool:
        """
        Check if a task can fit in this slot

        Args:
            task_duration_minutes: Duration of task to check

        Returns:
            True if task fits, False otherwise
        """
        return self.duration_minutes >= task_duration_minutes

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "slot_id": self.slot_id,
            "start_time": self.start_time.strftime("%H:%M:%S"),
            "end_time": self.end_time.strftime("%H:%M:%S"),
            "duration_minutes": self.duration_minutes,
            "gap_type": self.gap_type.value,
            "gap_size": self.gap_size.value,
            "before_event_title": self.before_event_title,
            "after_event_title": self.after_event_title,
        }


# ============================================================================
# Calendar Gap Finder Service
# ============================================================================

class CalendarGapFinder:
    """
    Service for finding available time slots in user's calendar

    This service analyzes calendar events and identifies gaps where
    wellness tasks can be anchored.

    Usage:
        finder = CalendarGapFinder()
        slots = finder.find_gaps(
            calendar_events=events,
            target_date=date(2025, 11, 6),
            min_gap_minutes=15
        )
    """

    def __init__(
        self,
        min_gap_minutes: int = 15,
        sleep_start_hour: int = 22,  # 10 PM
        sleep_end_hour: int = 6,     # 6 AM
    ):
        """
        Initialize calendar gap finder

        Args:
            min_gap_minutes: Minimum gap duration to consider (default: 15)
            sleep_start_hour: Hour when sleep time starts (default: 22 = 10 PM)
            sleep_end_hour: Hour when sleep time ends (default: 6 = 6 AM)
        """
        self.min_gap_minutes = min_gap_minutes
        self.sleep_start = time(sleep_start_hour, 0, 0)
        self.sleep_end = time(sleep_end_hour, 0, 0)

        logger.info(
            f"[GAP-FINDER] Initialized with min_gap={min_gap_minutes}min, "
            f"sleep={sleep_start_hour}:00-{sleep_end_hour}:00"
        )

    def find_gaps(
        self,
        calendar_events: List[CalendarEvent],
        target_date: date,
        min_gap_minutes: Optional[int] = None,
    ) -> List[AvailableSlot]:
        """
        Find available time slots in calendar

        Args:
            calendar_events: List of calendar events
            target_date: Date to analyze
            min_gap_minutes: Override minimum gap duration

        Returns:
            List of AvailableSlot objects sorted by start time
        """
        min_gap = min_gap_minutes or self.min_gap_minutes

        # Filter and sort events
        valid_events = self._filter_valid_events(calendar_events, target_date)
        sorted_events = sorted(valid_events, key=lambda e: e.start_time)

        logger.info(
            f"[GAP-FINDER] Analyzing {len(sorted_events)} events for {target_date}"
        )

        # Handle empty calendar (full day available)
        if not sorted_events:
            return self._handle_empty_calendar(target_date)

        # Find gaps between events
        gaps = []
        slot_counter = 1

        # Gap before first event (morning start)
        first_gap = self._find_morning_gap(
            sorted_events[0], target_date, slot_counter
        )
        if first_gap and first_gap.duration_minutes >= min_gap:
            gaps.append(first_gap)
            slot_counter += 1

        # Gaps between consecutive events
        for i in range(len(sorted_events) - 1):
            current_event = sorted_events[i]
            next_event = sorted_events[i + 1]

            gap = self._find_gap_between_events(
                current_event, next_event, target_date, slot_counter
            )

            if gap and gap.duration_minutes >= min_gap:
                gaps.append(gap)
                slot_counter += 1

        # Gap after last event (evening end)
        last_gap = self._find_evening_gap(
            sorted_events[-1], target_date, slot_counter
        )
        if last_gap and last_gap.duration_minutes >= min_gap:
            gaps.append(last_gap)

        logger.info(
            f"[GAP-FINDER] ✅ Found {len(gaps)} available slots "
            f"(total: {sum(g.duration_minutes for g in gaps)} minutes)"
        )

        return gaps

    def _filter_valid_events(
        self,
        events: List[CalendarEvent],
        target_date: date
    ) -> List[CalendarEvent]:
        """
        Filter events to only include valid ones for gap finding

        Args:
            events: List of calendar events
            target_date: Target date

        Returns:
            Filtered list of events
        """
        valid_events = []

        for event in events:
            # Skip cancelled events
            if event.status == "cancelled":
                continue

            # Skip all-day events (don't block time slots)
            if event.is_all_day:
                continue

            # Ensure event is on target date
            if event.start_time.date() != target_date:
                continue

            valid_events.append(event)

        return valid_events

    def _handle_empty_calendar(self, target_date: date) -> List[AvailableSlot]:
        """
        Handle case where user has no calendar events

        Returns a single large gap from wake time to sleep time.

        Args:
            target_date: Target date

        Returns:
            List with one AvailableSlot covering the full day
        """
        # Create one large slot from wake to sleep
        start_datetime = datetime.combine(target_date, self.sleep_end)
        end_datetime = datetime.combine(target_date, self.sleep_start)

        duration = int((end_datetime - start_datetime).total_seconds() / 60)

        logger.info(
            f"[GAP-FINDER] Empty calendar - full day available "
            f"({self.sleep_end} to {self.sleep_start})"
        )

        return [
            AvailableSlot(
                slot_id="slot_001",
                start_time=self.sleep_end,
                end_time=self.sleep_start,
                duration_minutes=duration,
                gap_type=GapType.FULL_DAY,
                gap_size=GapSize.LARGE,
            )
        ]

    def _find_morning_gap(
        self,
        first_event: CalendarEvent,
        target_date: date,
        slot_number: int
    ) -> Optional[AvailableSlot]:
        """
        Find gap before first calendar event (morning start)

        Args:
            first_event: First event of the day
            target_date: Target date
            slot_number: Slot counter for ID generation

        Returns:
            AvailableSlot or None if no valid gap
        """
        # Gap from wake time to first event
        start_time = self.sleep_end
        end_time = first_event.start_time.time()

        # Calculate duration
        start_datetime = datetime.combine(target_date, start_time)
        end_datetime = datetime.combine(target_date, end_time)
        duration = int((end_datetime - start_datetime).total_seconds() / 60)

        if duration <= 0:
            return None

        return AvailableSlot(
            slot_id=f"slot_{slot_number:03d}",
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            gap_type=GapType.MORNING_START,
            gap_size=self._categorize_gap_size(duration),
            after_event_title=first_event.title,
            after_event_id=first_event.id,
        )

    def _find_gap_between_events(
        self,
        current_event: CalendarEvent,
        next_event: CalendarEvent,
        target_date: date,
        slot_number: int
    ) -> Optional[AvailableSlot]:
        """
        Find gap between two consecutive events

        Args:
            current_event: Earlier event
            next_event: Later event
            target_date: Target date
            slot_number: Slot counter for ID generation

        Returns:
            AvailableSlot or None if no valid gap
        """
        # Gap from end of current to start of next
        start_time = current_event.end_time.time()
        end_time = next_event.start_time.time()

        # Calculate duration
        start_datetime = datetime.combine(target_date, start_time)
        end_datetime = datetime.combine(target_date, end_time)
        duration = int((end_datetime - start_datetime).total_seconds() / 60)

        # Handle overlapping events (negative duration)
        if duration <= 0:
            logger.debug(
                f"[GAP-FINDER] Overlapping events: "
                f"'{current_event.title}' and '{next_event.title}'"
            )
            return None

        return AvailableSlot(
            slot_id=f"slot_{slot_number:03d}",
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=self._categorize_gap_size(duration),
            before_event_title=current_event.title,
            after_event_title=next_event.title,
            before_event_id=current_event.id,
            after_event_id=next_event.id,
        )

    def _find_evening_gap(
        self,
        last_event: CalendarEvent,
        target_date: date,
        slot_number: int
    ) -> Optional[AvailableSlot]:
        """
        Find gap after last calendar event (evening end)

        Args:
            last_event: Last event of the day
            target_date: Target date
            slot_number: Slot counter for ID generation

        Returns:
            AvailableSlot or None if no valid gap
        """
        # Gap from last event to sleep time
        start_time = last_event.end_time.time()
        end_time = self.sleep_start

        # Calculate duration
        start_datetime = datetime.combine(target_date, start_time)
        end_datetime = datetime.combine(target_date, end_time)
        duration = int((end_datetime - start_datetime).total_seconds() / 60)

        if duration <= 0:
            return None

        return AvailableSlot(
            slot_id=f"slot_{slot_number:03d}",
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            gap_type=GapType.EVENING_END,
            gap_size=self._categorize_gap_size(duration),
            before_event_title=last_event.title,
            before_event_id=last_event.id,
        )

    def _categorize_gap_size(self, duration_minutes: int) -> GapSize:
        """
        Categorize gap by size

        Args:
            duration_minutes: Gap duration in minutes

        Returns:
            GapSize enum value
        """
        if duration_minutes < 30:
            return GapSize.SMALL
        elif duration_minutes < 60:
            return GapSize.MEDIUM
        else:
            return GapSize.LARGE


# ============================================================================
# Singleton Instance
# ============================================================================

_gap_finder_instance: Optional[CalendarGapFinder] = None


def get_gap_finder() -> CalendarGapFinder:
    """
    Get singleton instance of CalendarGapFinder

    Returns:
        CalendarGapFinder instance
    """
    global _gap_finder_instance

    if _gap_finder_instance is None:
        _gap_finder_instance = CalendarGapFinder()

    return _gap_finder_instance
