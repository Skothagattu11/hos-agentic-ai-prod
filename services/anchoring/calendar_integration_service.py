"""
Calendar Integration Service - Phase 1

This service acts as an adapter layer between hos-agentic-ai-prod and well-planned-api.
It fetches Google Calendar events and provides fallback mechanisms.

Integration Points:
- well-planned-api: GET /api/calendars/google/{user_id}/events
- MockCalendarGenerator: Fallback for development/testing

Key Features:
- HTTP client for well-planned-api
- Error handling with automatic fallback
- Response format standardization
- Connection status checking
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from dataclasses import dataclass
from enum import Enum
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class CalendarConnectionStatus(str, Enum):
    """Status of user's calendar connection"""
    CONNECTED = "connected"
    NOT_CONNECTED = "not_connected"
    ERROR = "error"
    MOCK_DATA = "mock_data"


@dataclass
class CalendarEvent:
    """
    Standardized calendar event model

    This model normalizes events from different sources (Google Calendar, Apple Calendar, mock data)
    into a consistent format for the anchoring algorithm.
    """
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    status: str = "confirmed"  # confirmed, tentative, cancelled
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    meeting_provider: Optional[str] = None  # google_meet, zoom, teams, etc.
    attendees: List[Dict[str, str]] = None
    description: Optional[str] = None
    is_recurring: bool = False
    is_all_day: bool = False

    def __post_init__(self):
        """Ensure attendees is a list"""
        if self.attendees is None:
            self.attendees = []

    def duration_minutes(self) -> int:
        """Calculate event duration in minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status,
            "location": self.location,
            "meeting_link": self.meeting_link,
            "meeting_provider": self.meeting_provider,
            "attendees": self.attendees,
            "description": self.description,
            "is_recurring": self.is_recurring,
            "is_all_day": self.is_all_day,
            "duration_minutes": self.duration_minutes()
        }


class CalendarFetchResult(BaseModel):
    """Result of fetching calendar events"""
    success: bool
    events: List[CalendarEvent] = Field(default_factory=list)
    connection_status: CalendarConnectionStatus
    total_events: int = 0
    date: date
    error_message: Optional[str] = None
    is_mock_data: bool = False

    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Calendar Integration Service
# ============================================================================

class CalendarIntegrationService:
    """
    Service for fetching calendar events from well-planned-api

    This service handles:
    - HTTP communication with well-planned-api
    - Error handling and retries
    - Fallback to mock data
    - Response format standardization

    Usage:
        service = CalendarIntegrationService()
        result = await service.fetch_calendar_events(user_id, target_date)

        if result.success:
            for event in result.events:
                print(f"{event.title}: {event.start_time} - {event.end_time}")
    """

    def __init__(
        self,
        well_planned_api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: int = 10,
        retry_count: int = 1
    ):
        """
        Initialize calendar integration service

        Args:
            well_planned_api_url: Base URL for well-planned-api (default: from env)
            api_key: DEPRECATED - Use supabase_token in fetch methods instead
            timeout_seconds: HTTP request timeout
            retry_count: Number of retries on failure
        """
        self.api_url = well_planned_api_url or os.getenv(
            "WELL_PLANNED_API_URL",
            "https://well-planned-api.onrender.com"
        )
        self.timeout = timeout_seconds
        self.retry_count = retry_count

        logger.info(f"[CALENDAR-INTEGRATION] Initialized with API URL: {self.api_url}")
        logger.info("[CALENDAR-INTEGRATION] Authentication: Requires Supabase JWT token per request")

    async def check_calendar_connection(
        self,
        user_id: str,
        supabase_token: Optional[str] = None
    ) -> CalendarConnectionStatus:
        """
        Check if user has connected their Google Calendar

        Args:
            user_id: User's profile ID
            supabase_token: Optional Supabase JWT token for authentication

        Returns:
            CalendarConnectionStatus enum value
        """
        try:
            # Build headers with Supabase JWT authentication
            headers = {}
            if supabase_token:
                headers["Authorization"] = f"Bearer {supabase_token}"
                logger.info("[CALENDAR-INTEGRATION] Using Supabase JWT for authentication")
            else:
                logger.warning("[CALENDAR-INTEGRATION] No Supabase token provided - request may fail")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/api/auth/google/status/{user_id}",
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("connected"):
                        return CalendarConnectionStatus.CONNECTED
                    else:
                        return CalendarConnectionStatus.NOT_CONNECTED
                else:
                    logger.warning(
                        f"[CALENDAR-INTEGRATION] Status check failed: {response.status_code}"
                    )
                    return CalendarConnectionStatus.ERROR

        except Exception as e:
            logger.error(f"[CALENDAR-INTEGRATION] Connection check error: {str(e)}")
            return CalendarConnectionStatus.ERROR

    async def fetch_calendar_events(
        self,
        user_id: str,
        target_date: date,
        supabase_token: Optional[str] = None,
        use_mock_data: bool = False,
        mock_profile: Optional[str] = None
    ) -> CalendarFetchResult:
        """
        Fetch calendar events for a specific date

        This method implements a fallback chain:
        1. If use_mock_data=True → Use MockCalendarGenerator
        2. Try fetching from well-planned-api with Supabase JWT
        3. On error → Retry once
        4. On repeated failure → Fall back to mock data
        5. If no calendar connected → Return empty list (valid state)

        Args:
            user_id: User's profile ID
            target_date: Date to fetch events for
            supabase_token: Supabase JWT token for authentication (REQUIRED for real calendar data)
            use_mock_data: Force mock data usage (for testing)
            mock_profile: Mock profile name (corporate_parent_sarah, etc.)

        Returns:
            CalendarFetchResult with events and metadata
        """
        # Step 1: Use mock data if explicitly requested
        if use_mock_data:
            logger.info("[CALENDAR-INTEGRATION] Using mock data (explicit request)")
            return await self._fetch_mock_data(user_id, target_date, mock_profile)

        # Step 2: Check calendar connection status
        connection_status = await self.check_calendar_connection(user_id, supabase_token)

        if connection_status == CalendarConnectionStatus.NOT_CONNECTED:
            logger.info(
                f"[CALENDAR-INTEGRATION] User {user_id} has not connected Google Calendar"
            )
            return CalendarFetchResult(
                success=True,
                events=[],
                connection_status=connection_status,
                total_events=0,
                date=target_date,
                error_message="User has not connected Google Calendar"
            )

        # Step 3: Try fetching from well-planned-api (with retry)
        for attempt in range(self.retry_count + 1):
            try:
                result = await self._fetch_from_api(user_id, target_date, supabase_token)

                if result.success:
                    logger.info(
                        f"[CALENDAR-INTEGRATION] ✅ Fetched {result.total_events} events "
                        f"for {target_date} (attempt {attempt + 1})"
                    )
                    return result

            except httpx.TimeoutException:
                logger.warning(
                    f"[CALENDAR-INTEGRATION] Timeout on attempt {attempt + 1}/{self.retry_count + 1}"
                )
                if attempt == self.retry_count:
                    break

            except httpx.NetworkError as e:
                logger.warning(
                    f"[CALENDAR-INTEGRATION] Network error on attempt {attempt + 1}: {str(e)}"
                )
                if attempt == self.retry_count:
                    break

            except Exception as e:
                logger.error(
                    f"[CALENDAR-INTEGRATION] Unexpected error on attempt {attempt + 1}: {str(e)}"
                )
                if attempt == self.retry_count:
                    break

        # Step 4: All attempts failed → Fallback to mock data
        logger.warning(
            "[CALENDAR-INTEGRATION] ⚠️  All API attempts failed, falling back to mock data"
        )
        return await self._fetch_mock_data(user_id, target_date, mock_profile)

    async def _fetch_from_api(
        self,
        user_id: str,
        target_date: date,
        supabase_token: Optional[str] = None
    ) -> CalendarFetchResult:
        """
        Fetch events from well-planned-api

        Args:
            user_id: User's profile ID
            target_date: Date to fetch events for
            supabase_token: Supabase JWT token for authentication

        Returns:
            CalendarFetchResult with events

        Raises:
            httpx.HTTPError: On network/timeout errors
        """
        # Construct time range for API call
        time_min = datetime.combine(target_date, time(0, 0, 0)).isoformat() + "Z"
        time_max = datetime.combine(target_date, time(23, 59, 59)).isoformat() + "Z"

        # Build headers with Supabase JWT authentication
        headers = {}
        if supabase_token:
            headers["Authorization"] = f"Bearer {supabase_token}"
            logger.info("[CALENDAR-INTEGRATION] Using Supabase JWT for API request")
        else:
            logger.warning("[CALENDAR-INTEGRATION] No Supabase token - request will likely fail with 403")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/api/calendars/google/{user_id}/events",
                params={
                    "time_min": time_min,
                    "time_max": time_max
                },
                headers=headers
            )

            if response.status_code == 403:
                # Forbidden - authentication issue
                error_detail = "Authentication failed"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_detail)
                except:
                    pass

                logger.error(
                    f"[CALENDAR-INTEGRATION] 403 Forbidden: {error_detail}. "
                    f"Supabase JWT token is required. Pass supabase_token parameter."
                )

                return CalendarFetchResult(
                    success=False,
                    events=[],
                    connection_status=CalendarConnectionStatus.ERROR,
                    total_events=0,
                    date=target_date,
                    error_message=f"403 Forbidden: {error_detail}. Supabase JWT token required."
                )

            if response.status_code == 404:
                # No OAuth tokens found - not an error, just not connected
                return CalendarFetchResult(
                    success=True,
                    events=[],
                    connection_status=CalendarConnectionStatus.NOT_CONNECTED,
                    total_events=0,
                    date=target_date,
                    error_message="No OAuth tokens found"
                )

            response.raise_for_status()

            # Parse response
            data = response.json()

            # Standardize event format
            events = []
            for event_data in data.get("events", []):
                event = self._parse_calendar_event(event_data)
                if event:
                    events.append(event)

            return CalendarFetchResult(
                success=True,
                events=events,
                connection_status=CalendarConnectionStatus.CONNECTED,
                total_events=len(events),
                date=target_date,
                is_mock_data=False
            )

    def _parse_calendar_event(self, event_data: Dict[str, Any]) -> Optional[CalendarEvent]:
        """
        Parse calendar event from well-planned-api response

        Args:
            event_data: Raw event dictionary from API

        Returns:
            CalendarEvent object or None if invalid
        """
        try:
            # Extract required fields
            event_id = event_data.get("id")
            title = event_data.get("title", "Untitled Event")

            # Parse datetimes
            start_time_str = event_data.get("start_time")
            end_time_str = event_data.get("end_time")

            if not start_time_str or not end_time_str:
                logger.warning(f"[CALENDAR-INTEGRATION] Event {event_id} missing start/end time")
                return None

            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))

            # Create event object
            return CalendarEvent(
                id=event_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                status=event_data.get("status", "confirmed"),
                location=event_data.get("location"),
                meeting_link=event_data.get("meeting_link"),
                meeting_provider=event_data.get("meeting_provider"),
                attendees=event_data.get("attendees", []),
                description=event_data.get("description"),
                is_recurring=event_data.get("is_recurring", False),
                is_all_day=event_data.get("is_all_day", False)
            )

        except Exception as e:
            logger.error(f"[CALENDAR-INTEGRATION] Error parsing event: {str(e)}")
            return None

    async def _fetch_mock_data(
        self,
        user_id: str,
        target_date: date,
        profile_name: Optional[str] = None
    ) -> CalendarFetchResult:
        """
        Fetch mock calendar data (fallback for development/testing)

        Args:
            user_id: User's profile ID
            target_date: Date to fetch events for
            profile_name: Mock profile to use (or default)

        Returns:
            CalendarFetchResult with mock events
        """
        # Import mock generator here to avoid circular dependency
        from ..testing.mock_data.mock_calendar_generator import MockCalendarGenerator

        generator = MockCalendarGenerator()

        # Use default profile if none specified
        if not profile_name:
            profile_name = "realistic_day"

        try:
            mock_events = generator.generate_profile(profile_name, target_date)

            return CalendarFetchResult(
                success=True,
                events=mock_events,
                connection_status=CalendarConnectionStatus.MOCK_DATA,
                total_events=len(mock_events),
                date=target_date,
                is_mock_data=True
            )

        except Exception as e:
            logger.error(f"[CALENDAR-INTEGRATION] Mock data generation failed: {str(e)}")

            # Return empty result as last resort
            return CalendarFetchResult(
                success=False,
                events=[],
                connection_status=CalendarConnectionStatus.ERROR,
                total_events=0,
                date=target_date,
                error_message=f"Mock data generation failed: {str(e)}",
                is_mock_data=True
            )


# ============================================================================
# Singleton Instance
# ============================================================================

_calendar_service_instance: Optional[CalendarIntegrationService] = None


def get_calendar_integration_service() -> CalendarIntegrationService:
    """
    Get singleton instance of CalendarIntegrationService

    Returns:
        CalendarIntegrationService instance
    """
    global _calendar_service_instance

    if _calendar_service_instance is None:
        _calendar_service_instance = CalendarIntegrationService()

    return _calendar_service_instance
