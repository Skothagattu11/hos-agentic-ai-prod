"""
Plan Parsers Package

Format-specific parsers for different routine generation APIs:
- JsonPlanParser: For /routine/generate-markdown (JSON format)
- MarkdownPlanParser: For /routine/generate (Markdown format)

New formats can be added by:
1. Creating a new parser class inheriting from BasePlanParser
2. Registering it in parser_factory.py
"""

from services.parsers.base_parser import BasePlanParser
from services.parsers.json_parser import JsonPlanParser
from services.parsers.markdown_parser import MarkdownPlanParser
from services.parsers.parser_factory import parser_factory

__all__ = [
    'BasePlanParser',
    'JsonPlanParser',
    'MarkdownPlanParser',
    'parser_factory'
]
