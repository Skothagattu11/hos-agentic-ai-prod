"""
Mock Calendar Generator - Phase 1

Generates realistic mock calendar data for testing calendar anchoring without
requiring actual Google Calendar connection.

Profiles:
1. realistic_day - Simple realistic calendar (like Test456 event pattern)
2. corporate_parent_sarah - Busy parent with work meetings and family commitments
3. hybrid_athlete_peak - Athlete with morning runs and gym sessions
4. empty_calendar - Minimal calendar (foundation builder archetype)
5. overscheduled - Stressed professional with back-to-back meetings

Usage:
    generator = MockCalendarGenerator()
    events = generator.generate_profile("realistic_day", date(2025, 11, 6))
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, date, time, timedelta
from services.anchoring.calendar_integration_service import CalendarEvent

logger = logging.getLogger(__name__)


class MockCalendarGenerator:
    """
    Generates realistic mock calendar data for testing

    This generator creates calendar events that mimic real user schedules,
    enabling testing and development without Google Calendar OAuth.
    """

    def __init__(self):
        """Initialize mock calendar generator"""
        self.profiles = {
            "realistic_day": self._generate_realistic_day,
            "corporate_parent_sarah": self._generate_corporate_parent,
            "hybrid_athlete_peak": self._generate_hybrid_athlete,
            "empty_calendar": self._generate_empty_calendar,
            "overscheduled": self._generate_overscheduled
        }

    def generate_profile(
        self,
        profile_name: str,
        target_date: date
    ) -> List[CalendarEvent]:
        """
        Generate mock calendar events for a specific profile

        Args:
            profile_name: Name of mock profile (corporate_parent_sarah, etc.)
            target_date: Date to generate events for

        Returns:
            List of CalendarEvent objects

        Raises:
            ValueError: If profile_name is invalid
        """
        if profile_name not in self.profiles:
            raise ValueError(
                f"Invalid profile: {profile_name}. "
                f"Available: {list(self.profiles.keys())}"
            )

        generator_func = self.profiles[profile_name]
        events = generator_func(target_date)

        logger.info(
            f"[MOCK-CALENDAR] Generated {len(events)} events for profile '{profile_name}'"
        )

        return events

    def get_available_profiles(self) -> List[str]:
        """
        Get list of available mock profiles

        Returns:
            List of profile names
        """
        return list(self.profiles.keys())

    # ========================================================================
    # Profile 1: Realistic Day (Simple/Common Schedule)
    # ========================================================================

    def _generate_realistic_day(self, target_date: date) -> List[CalendarEvent]:
        """
        Realistic day with common calendar patterns

        Mimics real calendar usage like the Test456 event pattern.
        Perfect for testing Phase 2 anchoring algorithms.

        Schedule:
        - 06:00-07:00: Morning Exercise
        - 09:00-10:00: Team Standup
        - 11:00-12:00: Project Planning
        - 13:00-13:30: Lunch Break
        - 15:00-16:00: Client Meeting
        - 18:00-18:45: Dinner

        Total: 6 events with natural gaps between them
        """
        events = [
            self._create_event(
                event_id="realistic_001",
                title="Morning Exercise",
                target_date=target_date,
                start_time=time(6, 0),
                end_time=time(7, 0),
                status="confirmed",
                is_recurring=True,
                description="Morning workout session"
            ),
            self._create_event(
                event_id="realistic_002",
                title="Team Standup",
                target_date=target_date,
                start_time=time(9, 0),
                end_time=time(10, 0),
                status="confirmed",
                meeting_link="https://meet.google.com/abc-defg-hij",
                meeting_provider="google_meet",
                attendees=[
                    {"email": "teammate@company.com", "name": "Teammate"}
                ],
                description="Daily team sync"
            ),
            self._create_event(
                event_id="realistic_003",
                title="Project Planning",
                target_date=target_date,
                start_time=time(11, 0),
                end_time=time(12, 0),
                status="confirmed",
                description="Planning next sprint"
            ),
            self._create_event(
                event_id="realistic_004",
                title="Lunch Break",
                target_date=target_date,
                start_time=time(13, 0),
                end_time=time(13, 30),
                status="confirmed",
                is_recurring=True,
                description="Lunch and rest"
            ),
            self._create_event(
                event_id="realistic_005",
                title="Client Meeting",
                target_date=target_date,
                start_time=time(15, 0),
                end_time=time(16, 0),
                status="confirmed",
                meeting_link="https://zoom.us/j/1234567890",
                meeting_provider="zoom",
                attendees=[
                    {"email": "client@external.com", "name": "Client Name"}
                ],
                description="Weekly client check-in"
            ),
            self._create_event(
                event_id="realistic_006",
                title="Dinner",
                target_date=target_date,
                start_time=time(18, 0),
                end_time=time(18, 45),
                status="confirmed",
                is_recurring=True,
                description="Evening meal"
            )
        ]

        return events

    # ========================================================================
    # Profile 2: Corporate Parent (Sarah)
    # ========================================================================

    def _generate_corporate_parent(self, target_date: date) -> List[CalendarEvent]:
        """
        Corporate parent with work meetings and family commitments

        Schedule:
        - 06:00-06:45: Wake up routine
        - 06:45-07:15: Breakfast with family
        - 07:30-08:15: Kids school drop-off
        - 09:30-10:00: Team Standup
        - 12:30-13:15: Lunch break
        - 14:00-15:00: Client Strategy Call
        - 17:30-18:00: Kids pickup
        - 18:30-19:15: Family dinner

        Total: 8 events
        """
        events = [
            self._create_event(
                event_id="mock_event_001",
                title="Wake up routine",
                target_date=target_date,
                start_time=time(6, 0),
                end_time=time(6, 45),
                is_recurring=True,
                description="Morning routine and personal time"
            ),
            self._create_event(
                event_id="mock_event_002",
                title="Breakfast with family",
                target_date=target_date,
                start_time=time(6, 45),
                end_time=time(7, 15),
                is_recurring=True,
                description="Family breakfast and preparation for day"
            ),
            self._create_event(
                event_id="mock_event_003",
                title="Kids school drop-off",
                target_date=target_date,
                start_time=time(7, 30),
                end_time=time(8, 15),
                is_recurring=True,
                location="Elementary School"
            ),
            self._create_event(
                event_id="mock_event_004",
                title="Team Standup",
                target_date=target_date,
                start_time=time(9, 30),
                end_time=time(10, 0),
                meeting_link="https://meet.google.com/mock-standup",
                meeting_provider="google_meet",
                attendees=[
                    {"email": "colleague1@company.com", "name": "John Doe"},
                    {"email": "colleague2@company.com", "name": "Jane Smith"}
                ],
                description="Daily team standup meeting"
            ),
            self._create_event(
                event_id="mock_event_005",
                title="Lunch break",
                target_date=target_date,
                start_time=time(12, 30),
                end_time=time(13, 15),
                is_recurring=True,
                description="Lunch and midday break"
            ),
            self._create_event(
                event_id="mock_event_006",
                title="Client Strategy Call",
                target_date=target_date,
                start_time=time(14, 0),
                end_time=time(15, 0),
                meeting_link="https://meet.google.com/mock-client",
                meeting_provider="google_meet",
                attendees=[
                    {"email": "client@company.com", "name": "Client Name"}
                ],
                description="Important client strategy discussion"
            ),
            self._create_event(
                event_id="mock_event_007",
                title="Kids pickup",
                target_date=target_date,
                start_time=time(17, 30),
                end_time=time(18, 0),
                is_recurring=True,
                location="Elementary School"
            ),
            self._create_event(
                event_id="mock_event_008",
                title="Family dinner",
                target_date=target_date,
                start_time=time(18, 30),
                end_time=time(19, 15),
                is_recurring=True,
                description="Family dinner and evening routine"
            )
        ]

        return events

    # ========================================================================
    # Profile 2: Hybrid Athlete (Peak Performer)
    # ========================================================================

    def _generate_hybrid_athlete(self, target_date: date) -> List[CalendarEvent]:
        """
        Athlete with morning run and gym sessions

        Schedule:
        - 05:30-06:30: Morning Run
        - 09:00-17:00: Work Block
        - 18:00-19:30: Gym Session

        Total: 3 events
        """
        events = [
            self._create_event(
                event_id="mock_event_101",
                title="Morning Run",
                target_date=target_date,
                start_time=time(5, 30),
                end_time=time(6, 30),
                is_recurring=True,
                description="5K morning run"
            ),
            self._create_event(
                event_id="mock_event_102",
                title="Work Block",
                target_date=target_date,
                start_time=time(9, 0),
                end_time=time(17, 0),
                description="Deep work session"
            ),
            self._create_event(
                event_id="mock_event_103",
                title="Gym Session",
                target_date=target_date,
                start_time=time(18, 0),
                end_time=time(19, 30),
                is_recurring=True,
                location="Fitness Center",
                description="Strength training"
            )
        ]

        return events

    # ========================================================================
    # Profile 3: Empty Calendar (Foundation Builder)
    # ========================================================================

    def _generate_empty_calendar(self, target_date: date) -> List[CalendarEvent]:
        """
        Minimal calendar for foundation builder archetype

        Schedule: No events

        Total: 0 events
        """
        return []

    # ========================================================================
    # Profile 4: Overscheduled (Stressed Professional)
    # ========================================================================

    def _generate_overscheduled(self, target_date: date) -> List[CalendarEvent]:
        """
        Stressed professional with back-to-back meetings

        Schedule:
        - 08:00-08:30: Morning Prep
        - 08:30-09:00: Morning Meeting 1
        - 09:00-09:30: Morning Meeting 2
        - 09:30-10:30: Strategy Session
        - 10:30-11:00: Quick Sync
        - 11:00-12:00: Project Review
        - 12:00-12:30: Lunch (working lunch)
        - 12:30-13:30: Client Call 1
        - 13:30-14:30: Client Call 2
        - 14:30-15:30: Team Meeting
        - 15:30-16:30: Budget Review
        - 16:30-18:00: End of Day Wrap-up

        Total: 12 events (very little gaps)
        """
        events = [
            self._create_event(
                event_id="mock_event_201",
                title="Morning Prep",
                target_date=target_date,
                start_time=time(8, 0),
                end_time=time(8, 30)
            ),
            self._create_event(
                event_id="mock_event_202",
                title="Morning Meeting 1",
                target_date=target_date,
                start_time=time(8, 30),
                end_time=time(9, 0),
                meeting_link="https://zoom.us/mock1"
            ),
            self._create_event(
                event_id="mock_event_203",
                title="Morning Meeting 2",
                target_date=target_date,
                start_time=time(9, 0),
                end_time=time(9, 30),
                meeting_link="https://zoom.us/mock2"
            ),
            self._create_event(
                event_id="mock_event_204",
                title="Strategy Session",
                target_date=target_date,
                start_time=time(9, 30),
                end_time=time(10, 30),
                meeting_link="https://meet.google.com/strategy"
            ),
            self._create_event(
                event_id="mock_event_205",
                title="Quick Sync",
                target_date=target_date,
                start_time=time(10, 30),
                end_time=time(11, 0)
            ),
            self._create_event(
                event_id="mock_event_206",
                title="Project Review",
                target_date=target_date,
                start_time=time(11, 0),
                end_time=time(12, 0)
            ),
            self._create_event(
                event_id="mock_event_207",
                title="Lunch (working)",
                target_date=target_date,
                start_time=time(12, 0),
                end_time=time(12, 30)
            ),
            self._create_event(
                event_id="mock_event_208",
                title="Client Call 1",
                target_date=target_date,
                start_time=time(12, 30),
                end_time=time(13, 30),
                attendees=[{"email": "client1@external.com"}]
            ),
            self._create_event(
                event_id="mock_event_209",
                title="Client Call 2",
                target_date=target_date,
                start_time=time(13, 30),
                end_time=time(14, 30),
                attendees=[{"email": "client2@external.com"}]
            ),
            self._create_event(
                event_id="mock_event_210",
                title="Team Meeting",
                target_date=target_date,
                start_time=time(14, 30),
                end_time=time(15, 30)
            ),
            self._create_event(
                event_id="mock_event_211",
                title="Budget Review",
                target_date=target_date,
                start_time=time(15, 30),
                end_time=time(16, 30)
            ),
            self._create_event(
                event_id="mock_event_212",
                title="End of Day Wrap-up",
                target_date=target_date,
                start_time=time(16, 30),
                end_time=time(18, 0)
            )
        ]

        return events

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _create_event(
        self,
        event_id: str,
        title: str,
        target_date: date,
        start_time: time,
        end_time: time,
        status: str = "confirmed",
        location: str = None,
        meeting_link: str = None,
        meeting_provider: str = None,
        attendees: List[Dict[str, str]] = None,
        description: str = None,
        is_recurring: bool = False,
        is_all_day: bool = False
    ) -> CalendarEvent:
        """
        Create a CalendarEvent object

        Args:
            event_id: Unique event identifier
            title: Event title
            target_date: Date of event
            start_time: Start time
            end_time: End time
            (other args): Optional event metadata

        Returns:
            CalendarEvent object
        """
        start_datetime = datetime.combine(target_date, start_time)
        end_datetime = datetime.combine(target_date, end_time)

        return CalendarEvent(
            id=event_id,
            title=title,
            start_time=start_datetime,
            end_time=end_datetime,
            status=status,
            location=location,
            meeting_link=meeting_link,
            meeting_provider=meeting_provider,
            attendees=attendees or [],
            description=description,
            is_recurring=is_recurring,
            is_all_day=is_all_day
        )
