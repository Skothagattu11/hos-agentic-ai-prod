"""
Insights Generation Service - Phase 1, Sprint 1.2

Responsible for:
- Generating personalized insights using AI (Claude Sonnet 4 or GPT-4o)
- Building context-rich prompts from InsightContext
- Validating insight quality (confidence, actionability)
- Returning structured insights with metadata

This is the core intelligence of the insights system.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from .data_aggregation_service import InsightContext


class InsightCategory(str, Enum):
    """Insight category types"""
    SLEEP = "sleep"
    ACTIVITY = "activity"
    NUTRITION = "nutrition"
    ENERGY = "energy"
    ROUTINE = "routine"
    RECOVERY = "recovery"
    MOTIVATION = "motivation"


class InsightPriority(str, Enum):
    """Insight priority levels"""
    HIGH = "high"  # Actionable now, significant impact
    MEDIUM = "medium"  # Important but not urgent
    LOW = "low"  # Nice to know, low urgency


@dataclass
class Insight:
    """
    Single generated insight with metadata

    Insights are short, actionable recommendations based on recent data.
    """
    insight_id: str  # UUID
    user_id: str
    category: InsightCategory
    priority: InsightPriority

    # Content
    title: str  # Short headline (max 60 chars)
    content: str  # Full insight text (max 200 chars)
    recommendation: Optional[str] = None  # Specific action to take

    # Quality metrics
    confidence_score: float = 0.0  # 0-1, how confident the AI is
    actionability_score: float = 0.0  # 0-1, how actionable this is
    relevance_score: float = 0.0  # 0-1, how relevant to current goals

    # Context
    data_points_used: List[str] = field(default_factory=list)
    timeframe: str = "3_days"  # "3_days", "7_days", "14_days"

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    archetype: Optional[str] = None
    acknowledged: bool = False
    user_feedback: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "insight_id": self.insight_id,
            "user_id": self.user_id,
            "category": self.category.value,
            "priority": self.priority.value,
            "title": self.title,
            "content": self.content,
            "recommendation": self.recommendation,
            "confidence_score": self.confidence_score,
            "actionability_score": self.actionability_score,
            "relevance_score": self.relevance_score,
            "data_points_used": self.data_points_used,
            "timeframe": self.timeframe,
            "generated_at": self.generated_at.isoformat(),
            "archetype": self.archetype,
            "acknowledged": self.acknowledged,
            "user_feedback": self.user_feedback
        }


@dataclass
class InsightsGenerationResult:
    """Result of insights generation process"""
    success: bool
    insights: List[Insight] = field(default_factory=list)
    error_message: Optional[str] = None
    generation_time_ms: Optional[int] = None
    model_used: Optional[str] = None
    token_count: Optional[int] = None


class InsightsGenerationService:
    """
    AI-powered insights generation engine

    Phase 1, Sprint 1.2 Implementation:
    - Build context-rich prompts from InsightContext
    - Call AI model (Claude Sonnet 4 or GPT-4o)
    - Parse AI response into structured Insight objects
    - Validate insight quality
    - Return InsightsGenerationResult
    """

    def __init__(
        self,
        openai_client=None,
        anthropic_client=None,
        model: str = "gpt-4o"  # or "claude-sonnet-4"
    ):
        """
        Initialize with AI client dependencies

        Args:
            openai_client: OpenAI async client
            anthropic_client: Anthropic async client
            model: Model to use for generation
        """
        self.openai_client = openai_client
        self.anthropic_client = anthropic_client
        self.model = model

        # Quality thresholds - strict to ensure personalized, actionable insights
        self.min_confidence_score = 0.75  # Only high-confidence insights
        self.min_actionability_score = 0.70  # Must be actionable

    async def generate_daily_insights(
        self,
        context: InsightContext
    ) -> InsightsGenerationResult:
        """
        Generate daily insights from InsightContext

        Main entry point for insights generation.

        Strategy:
        1. Build prompt from context
        2. Call AI model
        3. Parse response
        4. Validate quality
        5. Return structured insights

        Args:
            context: InsightContext with all data

        Returns:
            InsightsGenerationResult with generated insights
        """
        start_time = datetime.now()

        try:
            # Build prompt
            prompt = self._build_insights_prompt(context)

            # Call AI model
            ai_response = await self._call_ai_model(prompt)

            # Parse response
            insights = self._parse_ai_response(
                ai_response,
                context.user_id,
                context.archetype
            )

            # Validate quality
            validated_insights = self._validate_insights(insights)

            generation_time = (datetime.now() - start_time).total_seconds() * 1000

            return InsightsGenerationResult(
                success=True,
                insights=validated_insights,
                generation_time_ms=int(generation_time),
                model_used=self.model
            )

        except Exception as e:
            return InsightsGenerationResult(
                success=False,
                error_message=f"Failed to generate insights: {str(e)}"
            )

    def _build_insights_prompt(self, context: InsightContext) -> str:
        """
        Build context-rich prompt for AI model

        Prompt Structure:
        1. System context (HolisticOS, user archetype)
        2. Recent health data (3 days)
        3. Recent behavioral data (3 days)
        4. Baseline comparisons
        5. Task: Generate 3-5 actionable insights
        6. Format requirements (JSON)

        Args:
            context: InsightContext with all data

        Returns:
            Formatted prompt string
        """
        # Extract key metrics
        health = context.health_data
        behavior = context.behavior_data
        baselines = context.baselines

        prompt = f"""You are an expert health coach for HolisticOS. Analyze this user's REAL health data and engagement metrics to generate DEEPLY PERSONALIZED, improvement-focused insights.

**CRITICAL RULES:**
1. ONLY generate insights if you find something INTERESTING or ACTIONABLE in the data
2. Each insight MUST reference SPECIFIC numbers from the data (e.g., "7.2 hours sleep", "6,500 steps")
3. Each recommendation MUST connect health data to their routine/tasks for improvement
4. DO NOT generate generic advice - every insight must be unique to THIS user's data
5. Maximum 5 insights, but generate FEWER if data isn't interesting enough
6. If data is mostly N/A or unavailable, generate 0-2 insights acknowledging limited data

**User Profile:**
- Archetype: {context.archetype}
- Current Phase: {context.current_phase or 'building'}

**RAW HEALTH DATA (Last 3 Days):**
- Sleep Duration: {health.sleep_duration_avg or 'N/A'} hours avg | Baseline: {baselines.baseline_sleep_duration or 'N/A'} hours
- Sleep Quality: {health.sleep_quality_avg or 'N/A'}/100 | Baseline: {baselines.baseline_sleep_quality or 'N/A'}/100
- Sleep Consistency: {health.sleep_consistency or 'N/A'} (variance)
- Steps: {health.steps_avg or 'N/A'} steps/day | Baseline: {baselines.baseline_steps or 'N/A'} steps
- Active Minutes: {health.active_minutes_avg or 'N/A'} min/day | Baseline: {baselines.baseline_active_minutes or 'N/A'} min
- Resting Heart Rate: {health.resting_heart_rate_avg or 'N/A'} bpm
- HRV: {health.heart_rate_variability_avg or 'N/A'} ms
- Energy Score: {health.energy_score_avg or 'N/A'}/100 | Baseline: {baselines.baseline_energy_score or 'N/A'}/100
- Readiness Score: {health.readiness_score_avg or 'N/A'}/100 | Baseline: {baselines.baseline_readiness_score or 'N/A'}/100
- Calories Burned: {health.calories_burned_avg or 'N/A'} kcal/day

**ENGAGEMENT METRICS (Last 3 Days):**
- Tasks Completed: {behavior.completed_tasks}/{behavior.total_tasks} ({behavior.completion_rate:.1%})
- Baseline Completion: {baselines.baseline_completion_rate or 'N/A'}
- Morning Tasks: {behavior.morning_completion_rate:.1%} completion
- Afternoon Tasks: {behavior.afternoon_completion_rate:.1%} completion
- Evening Tasks: {behavior.evening_completion_rate:.1%} completion
- Daily Check-ins: {behavior.daily_check_in_count} times
- Avg Energy (self-reported): {behavior.avg_energy_level or 'N/A'}/10
- Avg Mood: {behavior.avg_mood_level or 'N/A'}/10
- Avg Stress: {behavior.avg_stress_level or 'N/A'}/10
- Task Consistency: {behavior.task_consistency_score or 'N/A'}

**YOUR TASK:**
Analyze this data and generate 1-5 insights that are:
1. **Data-Driven**: Each insight MUST cite specific metrics (e.g., "Your 6,800 steps is 400 below your baseline")
2. **Improvement-Focused**: Identify gaps, trends, or opportunities for optimization
3. **Routine-Connected**: Recommendations must link health data to specific routine adjustments
4. **Personalized**: Use archetype-appropriate language ({context.archetype})
5. **Interesting**: Skip generic advice - only generate if data shows something notable

**Examples of GOOD insights:**
- "Your sleep dropped to 6.2 hours (vs 7.5 baseline) coinciding with 40% evening task completion. Try moving evening tasks earlier."
- "Morning energy at 8/10 but steps only 4,200. Add a 2,000-step morning walk to leverage high energy."
- "3-day streak of 85%+ task completion with 7+ hours sleep. This pattern is your optimal performance zone."

**Examples of BAD (generic) insights to AVOID:**
- "Sleep is important for health" ❌
- "Try to exercise more" ❌
- "Stay motivated" ❌

**Output Format (JSON):**
```json
{{
  "insights": [
    {{
      "category": "sleep|activity|energy|routine|recovery",
      "priority": "high|medium|low",
      "title": "Specific headline with numbers (max 60 chars)",
      "content": "Insight with EXACT data points and comparison to baseline (max 200 chars)",
      "recommendation": "Actionable routine adjustment connecting health data to tasks",
      "confidence_score": 0.70-0.95,
      "actionability_score": 0.70-0.95,
      "relevance_score": 0.70-0.95,
      "data_points_used": ["specific_metric_1", "specific_metric_2"]
    }}
  ]
}}
```

**REMEMBER:** Generate 0-5 insights. Only include insights that are genuinely interesting and improvement-focused based on THIS user's actual data. Quality over quantity.

Generate insights now:"""

        return prompt

    async def _call_ai_model(self, prompt: str) -> Dict[str, Any]:
        """
        Call AI model (GPT-4o or Claude Sonnet 4) - Real AI only

        Args:
            prompt: Formatted prompt string

        Returns:
            AI response as dictionary
        """
        if self.model.startswith("gpt"):
            return await self._call_openai(prompt)
        elif self.model.startswith("claude"):
            return await self._call_anthropic(prompt)
        else:
            raise ValueError(f"Unsupported model: {self.model}. Use 'gpt-4o' or 'claude-sonnet-4'")

    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API - Real AI only, no mock data"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized. Check OPENAI_API_KEY environment variable.")

        # Real OpenAI API call only
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1500
        )
        return json.loads(response.choices[0].message.content)

    async def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Call Anthropic Claude API"""
        # TODO: Implement Anthropic API call
        # response = await self.anthropic_client.messages.create(
        #     model=self.model,
        #     max_tokens=1024,
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # return json.loads(response.content[0].text)

        raise NotImplementedError("Anthropic client not yet implemented")

    def _parse_ai_response(
        self,
        response: Dict[str, Any],
        user_id: str,
        archetype: str
    ) -> List[Insight]:
        """
        Parse AI response into Insight objects

        Args:
            response: AI model response (JSON)
            user_id: User identifier
            archetype: User archetype

        Returns:
            List of Insight objects
        """
        insights = []

        for insight_data in response.get("insights", []):
            try:
                insight = Insight(
                    insight_id=self._generate_insight_id(),
                    user_id=user_id,
                    category=InsightCategory(insight_data["category"]),
                    priority=InsightPriority(insight_data["priority"]),
                    title=insight_data["title"],
                    content=insight_data["content"],
                    recommendation=insight_data.get("recommendation"),
                    confidence_score=insight_data.get("confidence_score", 0.0),
                    actionability_score=insight_data.get("actionability_score", 0.0),
                    relevance_score=insight_data.get("relevance_score", 0.0),
                    data_points_used=insight_data.get("data_points_used", []),
                    archetype=archetype
                )
                insights.append(insight)
            except Exception as e:
                # Skip malformed insights
                print(f"Failed to parse insight: {e}")
                continue

        return insights

    def _validate_insights(self, insights: List[Insight]) -> List[Insight]:
        """
        Validate insight quality and filter low-quality insights

        Quality Criteria:
        - Confidence score >= 0.7
        - Actionability score >= 0.6
        - Title length <= 60 chars
        - Content length <= 200 chars

        Args:
            insights: List of Insight objects

        Returns:
            Filtered list of high-quality insights
        """
        validated = []

        for insight in insights:
            # Check quality thresholds
            if insight.confidence_score < self.min_confidence_score:
                continue
            if insight.actionability_score < self.min_actionability_score:
                continue

            # Check length constraints
            if len(insight.title) > 60:
                insight.title = insight.title[:57] + "..."
            if len(insight.content) > 200:
                insight.content = insight.content[:197] + "..."

            validated.append(insight)

        return validated

    def _generate_insight_id(self) -> str:
        """Generate unique insight ID"""
        import uuid
        return str(uuid.uuid4())


# Service singleton
_insights_generation_service: Optional[InsightsGenerationService] = None


async def get_insights_generation_service() -> InsightsGenerationService:
    """Get or create InsightsGenerationService singleton"""
    global _insights_generation_service

    if _insights_generation_service is None:
        # Initialize with OpenAI client
        import os
        from openai import AsyncOpenAI

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai_client = AsyncOpenAI(api_key=openai_api_key)
            _insights_generation_service = InsightsGenerationService(
                openai_client=openai_client,
                model="gpt-4o"
            )
            print("[INSIGHTS_V2] Initialized with OpenAI GPT-4o client")
        else:
            print("[INSIGHTS_V2] Warning: No OPENAI_API_KEY found, using mock data")
            _insights_generation_service = InsightsGenerationService()

    return _insights_generation_service
