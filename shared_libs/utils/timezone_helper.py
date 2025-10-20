"""
Timezone helper utilities for handling user timezones.

Simple, straightforward timezone support for routine/nutrition generation.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_user_local_date(user_timezone: Optional[str] = None) -> str:
    """
    Get current date in user's timezone.

    Args:
        user_timezone: IANA timezone string (e.g., "America/New_York", "Asia/Kolkata")
                      If None, defaults to "America/New_York" (EST)

    Returns:
        Date string in format "YYYY-MM-DD" in user's timezone

    Examples:
        >>> get_user_local_date("America/New_York")
        "2025-01-19"

        >>> get_user_local_date("Asia/Kolkata")
        "2025-01-20"

        >>> get_user_local_date()  # No timezone provided
        "2025-01-19"  # Falls back to EST
    """
    # Default to EST if no timezone provided
    default_tz = "America/New_York"

    try:
        tz_str = user_timezone or default_tz
        user_tz = ZoneInfo(tz_str)
        local_date = datetime.now(user_tz).strftime("%Y-%m-%d")
        return local_date
    except Exception as e:
        # Invalid timezone - fallback to EST
        logger.warning(f"Invalid timezone '{user_timezone}', using EST fallback: {e}")
        est_tz = ZoneInfo(default_tz)
        return datetime.now(est_tz).strftime("%Y-%m-%d")
