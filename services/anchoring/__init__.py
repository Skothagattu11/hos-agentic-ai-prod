"""
Calendar Anchoring Services

This package contains services for anchoring AI-generated plan tasks to user's
actual calendar events (from Google Calendar via well-planned-api).

Architecture:
- CalendarIntegrationService: Fetches calendar events from well-planned-api
- CalendarGapFinder: Identifies available time slots
- TaskLoaderService: Loads plan_items with time_blocks context
- PatternAnalyzerService: Analyzes task_checkins for completion patterns
- AnchoringCoordinator: Orchestrates the entire anchoring flow

Anchoring Modes:
1. AI-Only (RECOMMENDED): AIAnchoringAgent with holistic context-aware reasoning
2. Hybrid (Legacy): AI scoring + optimization algorithm
3. Algorithmic (Fast): Rule-based scoring, no AI

Phase 1 (Foundation): ✅
- CalendarIntegrationService, MockCalendarGenerator, CalendarGapFinder, TaskLoaderService

Phase 2 (Algorithmic Anchoring): ✅
- BasicScorerService, GreedyAssignmentService, AnchoringCoordinator

Phase 4 (AI-Enhanced Scoring): ✅
- AIScorerService, HybridScorerService

Phase 5 (AI-Only Holistic): ✅
- AIAnchoringAgent (single-agent holistic reasoning)
"""

__version__ = "1.0.0"
__author__ = "HolisticOS Team"

# Phase 1 exports (Foundation - Complete)
from .calendar_integration_service import (
    CalendarIntegrationService,
    CalendarEvent,
    CalendarConnectionStatus,
    CalendarFetchResult,
    get_calendar_integration_service,
)

from .calendar_gap_finder import (
    CalendarGapFinder,
    AvailableSlot,
    GapType,
    GapSize,
    get_gap_finder,
)

from .task_loader_service import (
    TaskLoaderService,
    PlanItemToAnchor,
    TimeBlockContext,
    get_task_loader_service,
)

# Phase 2 exports (Algorithmic Anchoring - Complete)
from .basic_scorer_service import (
    BasicScorerService,
    TaskToAnchor,
    TaskSlotScore,
    TimeWindowPreference,
    PriorityLevel,
    get_basic_scorer_service,
)

from .greedy_assignment_service import (
    GreedyAssignmentService,
    TaskAssignment,
    AssignmentResult,
    get_greedy_assignment_service,
)

from .anchoring_coordinator import (
    AnchoringCoordinator,
    get_anchoring_coordinator,
)

# Phase 4 exports (AI-Enhanced Scoring - Complete)
from .ai_scorer_service import (
    AIScorerService,
    AITaskSlotScore,
    get_ai_scorer_service,
)

from .hybrid_scorer_service import (
    HybridScorerService,
    HybridTaskSlotScore,
    get_hybrid_scorer_service,
)

# Phase 5 exports (AI-Only Holistic Anchoring - Complete)
from .ai_anchoring_agent import (
    AIAnchoringAgent,
    get_ai_anchoring_agent,
)

__all__ = [
    # Calendar Integration
    "CalendarIntegrationService",
    "CalendarEvent",
    "CalendarConnectionStatus",
    "CalendarFetchResult",
    "get_calendar_integration_service",
    # Gap Finding
    "CalendarGapFinder",
    "AvailableSlot",
    "GapType",
    "GapSize",
    "get_gap_finder",
    # Task Loading
    "TaskLoaderService",
    "PlanItemToAnchor",
    "TimeBlockContext",
    "get_task_loader_service",
    # Algorithmic Scoring
    "BasicScorerService",
    "TaskToAnchor",
    "TaskSlotScore",
    "TimeWindowPreference",
    "PriorityLevel",
    "get_basic_scorer_service",
    # Greedy Assignment
    "GreedyAssignmentService",
    "TaskAssignment",
    "AssignmentResult",
    "get_greedy_assignment_service",
    # Anchoring Coordinator
    "AnchoringCoordinator",
    "get_anchoring_coordinator",
    # AI-Enhanced Scoring
    "AIScorerService",
    "AITaskSlotScore",
    "get_ai_scorer_service",
    # Hybrid Scoring
    "HybridScorerService",
    "HybridTaskSlotScore",
    "get_hybrid_scorer_service",
    # AI-Only Holistic Anchoring
    "AIAnchoringAgent",
    "get_ai_anchoring_agent",
]
