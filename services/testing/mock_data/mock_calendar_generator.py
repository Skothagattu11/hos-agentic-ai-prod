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
            "overscheduled": self._generate_overscheduled,
            # New scenario profiles for calendar testing
            "busy_professional": self._generate_busy_professional,
            "parent_schedule": self._generate_parent_schedule,
            "long_commuter": self._generate_long_commuter,
            "flexible_remote": self._generate_flexible_remote
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
    # Scenario Testing Profiles (Phase 4 - Calendar Integration Testing)
    # ========================================================================

    def _generate_busy_professional(self, target_date: date) -> List[CalendarEvent]:
        """
        Busy Professional - Back-to-back meetings all day

        Schedule:
        - 09:00-09:30: Morning Team Standup (30 min)
        - 09:30-10:30: Client Presentation Prep (60 min)
        - 10:30-12:00: Executive Leadership Meeting (90 min)
        - 12:00-13:00: Working Lunch with Stakeholders (60 min)
        - 13:00-14:30: Client Presentation (90 min)
        - 14:30-15:30: Project Review Meeting (60 min)
        - 15:30-17:00: Budget Planning Session (90 min)
        - 17:00-17:30: Team Debrief (30 min)

        Challenge: Very few gaps - algorithm must maximize limited availability
        """
        events = [
            self._create_event(
                event_id="busy_prof_1",
                title="Morning Team Standup",
                target_date=target_date,
                start_time=time(9, 0),
                end_time=time(9, 30),
                description="Daily standup"
            ),
            self._create_event(
                event_id="busy_prof_2",
                title="Client Presentation Prep",
                target_date=target_date,
                start_time=time(9, 30),
                end_time=time(10, 30),
                description="Prepare for client meeting"
            ),
            self._create_event(
                event_id="busy_prof_3",
                title="Executive Leadership Meeting",
                target_date=target_date,
                start_time=time(10, 30),
                end_time=time(12, 0),
                description="Weekly leadership sync"
            ),
            self._create_event(
                event_id="busy_prof_4",
                title="Working Lunch with Stakeholders",
                target_date=target_date,
                start_time=time(12, 0),
                end_time=time(13, 0),
                description="Lunch meeting"
            ),
            self._create_event(
                event_id="busy_prof_5",
                title="Client Presentation",
                target_date=target_date,
                start_time=time(13, 0),
                end_time=time(14, 30),
                description="Major client presentation"
            ),
            self._create_event(
                event_id="busy_prof_6",
                title="Project Review Meeting",
                target_date=target_date,
                start_time=time(14, 30),
                end_time=time(15, 30),
                description="Quarterly project review"
            ),
            self._create_event(
                event_id="busy_prof_7",
                title="Budget Planning Session",
                target_date=target_date,
                start_time=time(15, 30),
                end_time=time(17, 0),
                description="Annual budget planning"
            ),
            self._create_event(
                event_id="busy_prof_8",
                title="Team Debrief",
                target_date=target_date,
                start_time=time(17, 0),
                end_time=time(17, 30),
                description="End of day sync"
            ),
        ]
        return events

    def _generate_parent_schedule(self, target_date: date) -> List[CalendarEvent]:
        """
        Parent Schedule - Kids' activities and school runs

        Schedule:
        - 06:30-07:30: Wake Kids & Breakfast (60 min)
        - 07:30-08:15: School Drop-off (45 min)
        - 09:00-10:30: Work Meeting (90 min)
        - 11:00-12:00: Grocery Shopping (60 min)
        - 14:45-15:15: School Pick-up (30 min)
        - 15:30-16:30: Kids Soccer Practice (60 min)
        - 17:00-18:00: Prepare Dinner (60 min)
        - 18:00-18:45: Family Dinner (45 min)
        - 20:00-20:45: Kids Bedtime Routine (45 min)

        Challenge: Fragmented schedule with unpredictable gaps
        """
        events = [
            self._create_event(
                event_id="parent_1",
                title="Wake Kids & Breakfast",
                target_date=target_date,
                start_time=time(6, 30),
                end_time=time(7, 30),
                description="Morning routine with kids"
            ),
            self._create_event(
                event_id="parent_2",
                title="School Drop-off",
                target_date=target_date,
                start_time=time(7, 30),
                end_time=time(8, 15),
                description="Drive kids to school"
            ),
            self._create_event(
                event_id="parent_3",
                title="Work Meeting",
                target_date=target_date,
                start_time=time(9, 0),
                end_time=time(10, 30),
                description="Team meeting"
            ),
            self._create_event(
                event_id="parent_4",
                title="Grocery Shopping",
                target_date=target_date,
                start_time=time(11, 0),
                end_time=time(12, 0),
                description="Weekly grocery run"
            ),
            self._create_event(
                event_id="parent_5",
                title="School Pick-up",
                target_date=target_date,
                start_time=time(14, 45),
                end_time=time(15, 15),
                description="Pick up kids from school"
            ),
            self._create_event(
                event_id="parent_6",
                title="Kids Soccer Practice",
                target_date=target_date,
                start_time=time(15, 30),
                end_time=time(16, 30),
                description="Take kids to soccer"
            ),
            self._create_event(
                event_id="parent_7",
                title="Prepare Dinner",
                target_date=target_date,
                start_time=time(17, 0),
                end_time=time(18, 0),
                description="Cook dinner"
            ),
            self._create_event(
                event_id="parent_8",
                title="Family Dinner",
                target_date=target_date,
                start_time=time(18, 0),
                end_time=time(18, 45),
                description="Dinner with family"
            ),
            self._create_event(
                event_id="parent_9",
                title="Kids Bedtime Routine",
                target_date=target_date,
                start_time=time(20, 0),
                end_time=time(20, 45),
                description="Bath, stories, bedtime"
            ),
        ]
        return events

    def _generate_long_commuter(self, target_date: date) -> List[CalendarEvent]:
        """
        Long Commuter - 90-minute commutes bookend the day

        Schedule:
        - 07:00-08:30: Morning Commute (90 min)
        - 09:00-10:30: Desk Work (90 min)
        - 11:00-12:00: Team Meeting (60 min)
        - 12:30-13:15: Lunch Break (45 min)
        - 14:00-15:00: Client Call (60 min)
        - 15:30-17:00: Project Work (90 min)
        - 17:30-19:00: Evening Commute (90 min)
        - 19:30-20:15: Dinner (45 min)

        Challenge: Large unavailable blocks + limited evening availability
        """
        events = [
            self._create_event(
                event_id="commuter_1",
                title="Morning Commute",
                target_date=target_date,
                start_time=time(7, 0),
                end_time=time(8, 30),
                description="Train to office"
            ),
            self._create_event(
                event_id="commuter_2",
                title="Desk Work",
                target_date=target_date,
                start_time=time(9, 0),
                end_time=time(10, 30),
                description="Focus work"
            ),
            self._create_event(
                event_id="commuter_3",
                title="Team Meeting",
                target_date=target_date,
                start_time=time(11, 0),
                end_time=time(12, 0),
                description="Weekly team sync"
            ),
            self._create_event(
                event_id="commuter_4",
                title="Lunch Break",
                target_date=target_date,
                start_time=time(12, 30),
                end_time=time(13, 15),
                description="Lunch"
            ),
            self._create_event(
                event_id="commuter_5",
                title="Client Call",
                target_date=target_date,
                start_time=time(14, 0),
                end_time=time(15, 0),
                description="Client check-in"
            ),
            self._create_event(
                event_id="commuter_6",
                title="Project Work",
                target_date=target_date,
                start_time=time(15, 30),
                end_time=time(17, 0),
                description="Project development"
            ),
            self._create_event(
                event_id="commuter_7",
                title="Evening Commute",
                target_date=target_date,
                start_time=time(17, 30),
                end_time=time(19, 0),
                description="Train home"
            ),
            self._create_event(
                event_id="commuter_8",
                title="Dinner",
                target_date=target_date,
                start_time=time(19, 30),
                end_time=time(20, 15),
                description="Evening meal"
            ),
        ]
        return events

    def _generate_flexible_remote(self, target_date: date) -> List[CalendarEvent]:
        """
        Flexible Remote Worker - Few fixed events, lots of gaps

        Schedule:
        - 09:30-10:00: Morning Standup (Video) (30 min)
        - 11:00-12:30: Focus Block (90 min)
        - 13:00-14:00: Lunch Break (60 min)
        - 15:00-16:00: Client Video Call (60 min)

        Challenge: High flexibility but potential for procrastination
        """
        events = [
            self._create_event(
                event_id="remote_1",
                title="Morning Standup (Video)",
                target_date=target_date,
                start_time=time(9, 30),
                end_time=time(10, 0),
                description="Remote standup"
            ),
            self._create_event(
                event_id="remote_2",
                title="Focus Block",
                target_date=target_date,
                start_time=time(11, 0),
                end_time=time(12, 30),
                description="Deep work session"
            ),
            self._create_event(
                event_id="remote_3",
                title="Lunch Break",
                target_date=target_date,
                start_time=time(13, 0),
                end_time=time(14, 0),
                description="Lunch"
            ),
            self._create_event(
                event_id="remote_4",
                title="Client Video Call",
                target_date=target_date,
                start_time=time(15, 0),
                end_time=time(16, 0),
                description="Client meeting"
            ),
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
