"""
Parser Factory - Auto-detects format and routes to appropriate parser
"""
import logging
from typing import Dict, Any, Optional

from services.parsers.json_parser import JsonPlanParser
from services.parsers.markdown_parser import MarkdownPlanParser
from services.plan_extraction_service import ExtractedPlan

logger = logging.getLogger(__name__)


class PlanParserFactory:
    """Factory that detects format and selects appropriate parser"""

    def __init__(self):
        # Register all available parsers (order matters - try most specific first)
        self.parsers = [
            JsonPlanParser(),        # Try JSON first (most structured)
            MarkdownPlanParser(),    # Then markdown
        ]
        logger.info(f"✅ Parser factory initialized with {len(self.parsers)} parsers")

    def parse(self, content: str, analysis_result: Dict[str, Any], profile_id: str) -> Optional[ExtractedPlan]:
        """
        Auto-detect format and parse

        Returns ExtractedPlan or None if all parsers fail
        """
        analysis_id = analysis_result.get('id', 'unknown')
        archetype = analysis_result.get('archetype', 'Unknown')

        # Try each parser
        for parser in self.parsers:
            parser_name = parser.__class__.__name__

            try:
                if parser.can_parse(content):
                    logger.info(f"🎯 Using {parser_name} for extraction")

                    result = parser.parse(content, analysis_result)

                    if result and result.get('time_blocks') and result.get('tasks'):
                        # Build ExtractedPlan
                        from datetime import datetime

                        extracted_plan = ExtractedPlan(
                            plan_id=analysis_id,
                            time_blocks=result['time_blocks'],
                            tasks=result['tasks'],
                            archetype=archetype,
                            user_id=profile_id,
                            date=datetime.now().strftime('%Y-%m-%d')
                        )

                        logger.info(f"✅ {parser_name} successfully extracted {len(extracted_plan.time_blocks)} blocks, {len(extracted_plan.tasks)} tasks")
                        return extracted_plan
                    else:
                        logger.warning(f"⚠️ {parser_name} returned empty results")

            except Exception as e:
                logger.error(f"❌ {parser_name} failed: {e}")
                continue

        logger.error("❌ All parsers failed to extract plan")
        return None


# Global singleton
parser_factory = PlanParserFactory()
