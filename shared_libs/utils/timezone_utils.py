"""
Timezone utility functions for converting UTC timestamps to EST/EDT
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Union


def utc_to_est(timestamp: Union[str, datetime, None]) -> Optional[str]:
    """
    Convert UTC timestamp to EST/EDT timezone
    
    Args:
        timestamp: UTC timestamp as string, datetime object, or None
        
    Returns:
        Formatted timestamp string in EST/EDT or None if input is None
    """
    if timestamp is None:
        return None
    
    try:
        # Parse string timestamp if needed
        if isinstance(timestamp, str):
            # Handle different timestamp formats
            if 'T' in timestamp:
                # ISO format: 2024-08-21T15:30:00.123456+00:00
                if timestamp.endswith('Z'):
                    timestamp = timestamp[:-1] + '+00:00'
                elif '+' not in timestamp and timestamp.count(':') >= 2:
                    # Add UTC timezone if missing
                    timestamp = timestamp + '+00:00'
                
                utc_dt = datetime.fromisoformat(timestamp)
            else:
                # Assume it's already a datetime string
                utc_dt = datetime.fromisoformat(timestamp + '+00:00')
        elif isinstance(timestamp, datetime):
            utc_dt = timestamp
        else:
            return None
        
        # Ensure timezone is UTC
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        elif utc_dt.tzinfo != timezone.utc:
            utc_dt = utc_dt.astimezone(timezone.utc)
        
        # Convert to EST/EDT (handles daylight saving time automatically)
        eastern = ZoneInfo("America/New_York")
        est_dt = utc_dt.astimezone(eastern)
        
        # Format as readable string
        return est_dt.strftime("%Y-%m-%d %I:%M:%S %p %Z")
        
    except Exception as e:
        # Log error and return original timestamp as fallback
        print(f"Warning: Failed to convert timestamp {timestamp}: {e}")
        return str(timestamp) if timestamp else None


def utc_to_est_short(timestamp: Union[str, datetime, None]) -> Optional[str]:
    """
    Convert UTC timestamp to EST/EDT timezone in short format
    
    Args:
        timestamp: UTC timestamp as string, datetime object, or None
        
    Returns:
        Short formatted timestamp string in EST/EDT (MM/DD HH:MM AM/PM) or None if input is None
    """
    if timestamp is None:
        return None
    
    try:
        # Parse string timestamp if needed
        if isinstance(timestamp, str):
            # Handle different timestamp formats
            if 'T' in timestamp:
                # ISO format: 2024-08-21T15:30:00.123456+00:00
                if timestamp.endswith('Z'):
                    timestamp = timestamp[:-1] + '+00:00'
                elif '+' not in timestamp and timestamp.count(':') >= 2:
                    # Add UTC timezone if missing
                    timestamp = timestamp + '+00:00'
                
                utc_dt = datetime.fromisoformat(timestamp)
            else:
                # Assume it's already a datetime string
                utc_dt = datetime.fromisoformat(timestamp + '+00:00')
        elif isinstance(timestamp, datetime):
            utc_dt = timestamp
        else:
            return None
        
        # Ensure timezone is UTC
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        elif utc_dt.tzinfo != timezone.utc:
            utc_dt = utc_dt.astimezone(timezone.utc)
        
        # Convert to EST/EDT (handles daylight saving time automatically)
        eastern = ZoneInfo("America/New_York")
        est_dt = utc_dt.astimezone(eastern)
        
        # Format as short readable string
        return est_dt.strftime("%m/%d %I:%M %p")
        
    except Exception as e:
        # Log error and return original timestamp as fallback
        print(f"Warning: Failed to convert timestamp {timestamp}: {e}")
        return str(timestamp) if timestamp else None


def get_current_est() -> str:
    """
    Get current time in EST/EDT timezone
    
    Returns:
        Current timestamp string in EST/EDT format
    """
    eastern = ZoneInfo("America/New_York")
    now_est = datetime.now(eastern)
    return now_est.strftime("%Y-%m-%d %I:%M:%S %p %Z")