"""
Base Parser Interface - All format parsers inherit from this
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import time


class BasePlanParser(ABC):
    """Base interface for all plan parsers"""

    @abstractmethod
    def can_parse(self, content: str) -> bool:
        """Check if this parser can handle the given content format"""
        pass

    @abstractmethod
    def parse(self, content: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse content and return structured data

        Returns:
        {
            'time_blocks': [TimeBlockContext],
            'tasks': [ExtractedTask]
        }
        """
        pass

    def _parse_time_string(self, time_str: str) -> time:
        """Helper: Convert HH:MM string to time object"""
        if not time_str:
            return None
        try:
            # Handle both "06:00" and "6:00" formats
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1])
            return time(hour=hour, minute=minute)
        except (ValueError, IndexError, AttributeError):
            return None
