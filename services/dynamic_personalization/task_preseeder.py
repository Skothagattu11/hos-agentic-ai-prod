"""
Task Pre-Seeder Service (Option B + Check-in Feedback Integration)
===================================================================

Purpose: Select library tasks BEFORE AI generation based on user feedback + check-in preferences.

This is the core of Option B (Feedback-Driven Pre-seeding):
- Day 1 (Cold Start): Returns empty (user has <3 feedback) → Pure AI plan
- Day 2+ (Warm Start): Returns 5-8 library tasks → AI schedules them

Enhancements:
- Integrates check-in feedback (continue_preference, enjoyed, timing)
- Excludes categories user wants to avoid
- Boosts categories user enjoys
- Respects timing preferences (earlier/later)
- Maintains category diversity (max 2 per category for MVP)

Flow:
1. Check user feedback count (requires ≥3 completed tasks)
2. Fetch check-in preferences (FeedbackService)
3. If sufficient feedback:
   - Filter out excluded categories
   - Prioritize enjoyed categories
   - Select across diverse categories (1-2 per category)
   - Apply timing adjustments
   - Return 5-8 tasks with metadata
4. If insufficient feedback:
   - Return empty → Fallback to pure AI

Author: HolisticOS Team
Date: 2025-10-30
"""

from typing import List, Dict, Optional
from datetime import datetime
import logging
import os
from supabase import create_client, Client
from dotenv import load_dotenv

from services.dynamic_personalization.adaptive_task_selector import AdaptiveTaskSelector
from services.dynamic_personalization.feedback_analyzer_service import FeedbackAnalyzerService
from services.feedback_service import FeedbackService  # NEW: Check-in feedback
from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter

logger = logging.getLogger(__name__)
load_dotenv()


class TaskPreseeder:
    """Pre-selects library tasks for AI prompt enhancement with check-in feedback integration."""

    # Configuration constants
    MIN_FEEDBACK_THRESHOLD = 3  # Minimum completed tasks required
    MIN_TASKS = 5  # Minimum library tasks to select
    MAX_TASKS = 8  # Maximum library tasks to select
    MAX_TASKS_PER_CATEGORY = 2  # NEW: Category diversity limit for MVP

    # Category distribution for diverse selection
    DEFAULT_CATEGORIES = [
        'hydration',
        'movement',
        'nutrition',
        'stress_management',
        'sleep',
        'breathing',
        'mindfulness'
    ]

    def __init__(self, db_adapter: Optional[SupabaseAsyncPGAdapter] = None):
        """Initialize TaskPreseeder.

        Args:
            db_adapter: Database adapter (creates new if None)
        """
        self.db = db_adapter or SupabaseAsyncPGAdapter()
        self.adaptive_selector = AdaptiveTaskSelector(db_adapter=self.db)
        self.feedback_service = FeedbackAnalyzerService(db_adapter=self.db)
        self.checkin_feedback = FeedbackService(db_adapter=self.db)  # NEW

        # Direct Supabase client for simple queries (avoid adapter complexity)
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )

        self._initialized = False

    async def initialize(self):
        """Initialize all services."""
        if not self._initialized:
            await self.db.connect()
            await self.adaptive_selector.initialize()
            await self.feedback_service.initialize()
            await self.checkin_feedback.initialize()  # NEW
            self._initialized = True
            logger.info("TaskPreseeder initialized with check-in feedback")

    async def close(self):
        """Close all services."""
        if self._initialized:
            await self.adaptive_selector.close()
            await self.feedback_service.close()
            await self.checkin_feedback.close()  # NEW
            await self.db.close()
            self._initialized = False
            logger.info("TaskPreseeder closed")

    async def select_tasks_for_plan(
        self,
        user_id: str,
        archetype: str,
        mode: str,
        plan_date: datetime,
        preferences: dict = None
    ) -> Dict:
        """
        Main entry point: Select library tasks for daily plan with check-in feedback AND user preferences.

        This is called BEFORE AI generation to pre-select tasks based on
        user feedback, learning phase, and direct user preferences.

        Args:
            user_id: User ID (profile_id)
            archetype: User archetype (foundation_builder, peak_performer, etc.)
            mode: Energy mode (high, medium, low)
            plan_date: Date for the plan
            preferences: Optional dict with user scheduling preferences:
                - wake_time: "06:00" (24-hour format)
                - sleep_time: "22:00" (24-hour format)
                - preferred_workout_time: "morning" | "evening" | "flexible"
                - available_time_slots: ["morning", "afternoon", "evening"]
                - goals: ["hydration", "movement", "nutrition", "sleep", "stress"]
                - energy_pattern: "morning_person" | "night_owl" | "balanced"

        Returns:
            {
                'has_sufficient_feedback': bool,
                'preselected_tasks': List[Dict],  # 5-8 tasks or empty
                'selection_stats': {
                    'total_selected': int,
                    'feedback_count': int,
                    'checkin_feedback_used': bool,  # NEW
                    'categories_excluded': List[str],  # NEW
                    'categories_boosted': List[str],  # NEW
                    'learning_phase': str,
                    'categories_covered': List[str]
                }
            }
        """
        try:
            # Step 1: Check if user has sufficient feedback
            feedback_count = await self._get_feedback_count(user_id)

            logger.info(f"[PRESEED] User {user_id[:8]}: feedback_count={feedback_count}, threshold={self.MIN_FEEDBACK_THRESHOLD}")

            if feedback_count < self.MIN_FEEDBACK_THRESHOLD:
                logger.info(f"[PRESEED] Insufficient feedback ({feedback_count}/{self.MIN_FEEDBACK_THRESHOLD}) - using pure AI")
                return self._empty_response(feedback_count)

            # Step 2: Fetch check-in preferences (NEW)
            checkin_prefs = await self.checkin_feedback.get_latest_checkin_feedback(user_id)

            # Step 3: Get user preferences and learning phase
            user_prefs = await self.feedback_service.get_user_preferences(user_id)
            learning_phase = user_prefs.get('current_learning_phase', 'discovery') if user_prefs else 'discovery'

            logger.info(f"[PRESEED] User {user_id[:8]} in {learning_phase} phase")
            logger.info(f"[PRESEED] Check-in feedback: {checkin_prefs.get('feedback_count', 0)} entries")

            # Step 4: Select diverse tasks with check-in integration + direct preferences (ENHANCED)
            preselected_tasks = await self._select_diverse_tasks(
                user_id=user_id,
                archetype=archetype,
                mode=mode,
                learning_phase=learning_phase,
                user_prefs=user_prefs,
                checkin_prefs=checkin_prefs,  # NEW
                preferences=preferences  # NEW: Direct user preferences from API
            )

            # Step 5: Build response
            categories_covered = list(set(task['category'] for task in preselected_tasks))

            logger.info(f"[PRESEED] Selected {len(preselected_tasks)} tasks")
            logger.info(f"[PRESEED] Categories: {categories_covered}")

            # DEBUG: Log friction data being passed to selection_stats
            logger.info(f"[PRESEED-DEBUG] Friction data received from FeedbackService:")
            logger.info(f"[PRESEED-DEBUG]   Low friction: {checkin_prefs.get('low_friction_categories', [])}")
            logger.info(f"[PRESEED-DEBUG]   Medium friction: {checkin_prefs.get('medium_friction_categories', [])}")
            logger.info(f"[PRESEED-DEBUG]   High friction: {checkin_prefs.get('high_friction_categories', [])}")
            logger.info(f"[PRESEED-DEBUG]   Friction analysis: {checkin_prefs.get('friction_analysis', {})}")

            return {
                'has_sufficient_feedback': True,
                'preselected_tasks': preselected_tasks,
                'selection_stats': {
                    'total_selected': len(preselected_tasks),
                    'feedback_count': feedback_count,
                    'checkin_feedback_used': checkin_prefs.get('has_feedback', False),
                    # NEW: Friction-based fields (replaces exclusion-based)
                    'low_friction_categories': checkin_prefs.get('low_friction_categories', []),
                    'medium_friction_categories': checkin_prefs.get('medium_friction_categories', []),
                    'high_friction_categories': checkin_prefs.get('high_friction_categories', []),
                    'friction_analysis': checkin_prefs.get('friction_analysis', {}),
                    # Backward compatibility (deprecated)
                    'categories_excluded': checkin_prefs.get('exclude_categories', []),
                    'categories_boosted': checkin_prefs.get('enjoyed_categories', []),
                    'learning_phase': learning_phase,
                    'categories_covered': categories_covered
                }
            }

        except Exception as e:
            logger.error(f"[PRESEED] Error selecting tasks for user {user_id}: {e}", exc_info=True)
            return self._empty_response(0, error=str(e))

    async def _select_diverse_tasks(
        self,
        user_id: str,
        archetype: str,
        mode: str,
        learning_phase: str,
        user_prefs: Optional[Dict],
        checkin_prefs: Dict,  # NEW
        preferences: Optional[Dict] = None  # NEW: Direct user preferences
    ) -> List[Dict]:
        """
        Select diverse tasks with check-in feedback integration AND user preferences.

        New logic:
        - Exclude categories user said 'no' to
        - Boost categories user enjoyed
        - Limit 2 tasks per category (MVP requirement)
        - Adjust timing based on user feedback
        - Prioritize categories from user's goals (preferences)
        - Filter movement tasks by preferred_workout_time
        - Filter tasks by available_time_slots

        Strategy:
        - Prioritize high-affinity categories (based on user_prefs + check-in)
        - Select 1-2 tasks per category for diversity
        - Use AdaptiveTaskSelector for intelligent selection
        - Stop when we have MIN_TASKS to MAX_TASKS

        Args:
            user_id: User ID
            archetype: User archetype
            mode: Energy mode
            learning_phase: Current learning phase
            user_prefs: User preferences from FeedbackAnalyzerService
            checkin_prefs: Check-in preferences from FeedbackService

        Returns:
            List of 5-8 tasks with metadata
        """
        selected_tasks = []
        category_counts = {}  # NEW: Track tasks per category

        # Determine category priority (with check-in boost + direct preferences) (NEW)
        categories_to_try = self._prioritize_categories_with_checkin(
            user_prefs,
            checkin_prefs,
            preferences  # NEW: Direct user preferences
        )

        logger.debug(f"[PRESEED] Category priority (check-in adjusted): {categories_to_try}")

        # Select tasks with category diversity limits
        for category in categories_to_try:
            # Check if we have enough tasks
            if len(selected_tasks) >= self.MAX_TASKS:
                break

            # Check category limit (NEW: max 2 per category)
            if category_counts.get(category, 0) >= self.MAX_TASKS_PER_CATEGORY:
                logger.debug(f"[PRESEED] Skipping {category} - limit reached")
                continue

            try:
                # Use AdaptiveTaskSelector for intelligent selection
                tasks = await self.adaptive_selector.select_tasks_for_block(
                    user_id=user_id,
                    category=category,
                    archetype=archetype,
                    mode=mode,
                    time_of_day=None,  # No time filter - include all tasks
                    count=1  # Select 1 at a time for controlled diversity
                )

                if tasks and len(tasks) > 0:
                    task = tasks[0]  # Take first (best) task

                    # Apply check-in enhancements (NEW)
                    task = await self._enhance_task_with_checkin(task, checkin_prefs)

                    # NEW: Apply user preference enhancements
                    if preferences:
                        task = self._enhance_task_with_preferences(task, preferences)

                    # Enrich with selection metadata
                    task['selection_reason'] = await self._get_selection_reason(user_id, task, checkin_prefs, preferences)
                    task['source'] = 'library'
                    task['time_preference'] = task.get('time_of_day_preference', 'any')

                    selected_tasks.append(task)
                    category_counts[category] = category_counts.get(category, 0) + 1

                    logger.debug(f"[PRESEED] Added {task['name']} ({category}) - count: {category_counts[category]}")

            except Exception as e:
                logger.warning(f"[PRESEED] Could not select task for category {category}: {e}")
                continue

        # Ensure we have at least MIN_TASKS
        if len(selected_tasks) < self.MIN_TASKS:
            logger.warning(f"[PRESEED] Only selected {len(selected_tasks)} tasks, target was {self.MIN_TASKS}")
            # Try to add more from allowed categories
            await self._fill_to_minimum(
                selected_tasks,
                category_counts,
                user_id,
                archetype,
                mode,
                categories_to_try,
                checkin_prefs
            )

        logger.info(f"[PRESEED] Final selection: {len(selected_tasks)} tasks")
        return selected_tasks[:self.MAX_TASKS]  # Ensure we don't exceed max

    def _prioritize_categories_with_checkin(
        self,
        user_prefs: Optional[Dict],
        checkin_prefs: Dict,
        preferences: Optional[Dict] = None
    ) -> List[str]:
        """
        Prioritize categories with friction-based feedback integration + user preferences.

        NEW FRICTION-REDUCTION LOGIC:
        1. KEEP all categories (no exclusion - balanced health requirement)
        2. Prioritize low-friction categories (user excels)
        3. Include medium/high-friction categories (but lower priority)
        4. Use existing preference scoring as secondary factor
        5. BOOST categories from user's goals (preferences.goals)
        """
        # Start with ALL default categories (no exclusion!)
        all_categories = self.DEFAULT_CATEGORIES.copy()

        # Get friction data
        low_friction = checkin_prefs.get('low_friction_categories', [])
        medium_friction = checkin_prefs.get('medium_friction_categories', [])
        high_friction = checkin_prefs.get('high_friction_categories', [])

        logger.debug(f"[PRESEED] Low friction: {low_friction}")
        logger.debug(f"[PRESEED] High friction: {high_friction}")

        # Score each category based on friction level
        category_scores = {}

        for category in all_categories:
            # Base score determined by friction level
            if category in low_friction:
                score = 0.8  # High priority - user excels
                logger.debug(f"[PRESEED] Low friction: {category} (score=0.8)")
            elif category in medium_friction:
                score = 0.5  # Medium priority - manageable
                logger.debug(f"[PRESEED] Medium friction: {category} (score=0.5)")
            elif category in high_friction:
                score = 0.3  # Lower priority but NOT excluded (needs simplification)
                logger.debug(f"[PRESEED] High friction: {category} (score=0.3, will simplify)")
            else:
                score = 0.4  # Default for categories without feedback

            # Boost from existing preferences (secondary factor)
            if user_prefs:
                category_affinity = user_prefs.get('category_affinity', {})
                if category in category_affinity:
                    score += category_affinity[category] * 0.1  # Smaller weight

            # NEW: Boost from direct user preferences (goals)
            if preferences and 'goals' in preferences:
                user_goals = preferences['goals']
                if category in user_goals:
                    score += 0.2  # Significant boost for user's stated goals
                    logger.debug(f"[PRESEED] Goal boost: {category} (score +0.2)")

            category_scores[category] = score

        # Sort by score (highest first)
        sorted_categories = sorted(
            category_scores.keys(),
            key=lambda c: category_scores[c],
            reverse=True
        )

        return sorted_categories

    async def _get_feedback_count(self, user_id: str) -> int:
        """
        Count completed tasks with feedback using direct Supabase REST API.

        Args:
            user_id: User ID (profile_id)

        Returns:
            Number of completed tasks
        """
        try:
            # Use direct Supabase REST API with count
            result = self.supabase.table('task_checkins').select(
                '*', count='exact'
            ).eq('profile_id', user_id).eq(
                'completion_status', 'completed'
            ).execute()

            count = result.count if result.count is not None else 0

            # DEBUG: Log the result
            logger.info(f"🔍 [DEBUG] TaskPreseeder found {count} completed check-ins for user {user_id[:8]}...")

            if count == 0:
                # Check if ANY check-ins exist (any status)
                total_result = self.supabase.table('task_checkins').select(
                    '*', count='exact'
                ).eq('profile_id', user_id).execute()

                total_count = total_result.count if total_result.count is not None else 0

                if total_count > 0:
                    logger.info(f"🔍 [DEBUG] Found {total_count} check-ins with ANY status")

                    # Get sample to check status values
                    sample_result = self.supabase.table('task_checkins').select(
                        'planned_date, completion_status, continue_preference, experience_rating, created_at'
                    ).eq('profile_id', user_id).order(
                        'created_at', desc=True
                    ).limit(3).execute()

                    if sample_result.data:
                        logger.info(f"🔍 [DEBUG] Sample check-ins:")
                        for idx, checkin in enumerate(sample_result.data, 1):
                            logger.info(f"    {idx}. date={checkin.get('planned_date')}, status='{checkin.get('completion_status')}', rating={checkin.get('experience_rating')}")
                else:
                    logger.info(f"🔍 [DEBUG] No check-ins found at all for user {user_id[:8]}")

            return count

        except Exception as e:
            logger.error(f"[PRESEED] Error getting feedback count: {e}")
            return 0

    def _generate_motivational_message(
        self,
        task: Dict,
        category: str,
        friction_level: str,
        completion_count: int,
        avg_rating: float
    ) -> str:
        """
        Generate motivational message based on friction level.

        Args:
            task: Task dictionary
            category: Task category
            friction_level: 'low', 'medium', or 'high'
            completion_count: Number of times completed
            avg_rating: Average satisfaction rating

        Returns:
            Motivational message to add to task description
        """
        import random

        if friction_level == 'low' and completion_count > 0:
            # Success category - celebrate!
            messages = [
                f"✅ You've completed this {completion_count} times! Keep the momentum going!",
                f"💪 {completion_count}-time streak - you're crushing this!",
                f"⭐ Rated {avg_rating:.1f}/5 by you - clearly working!",
                f"🔥 {completion_count} completions - this is your anchor habit!"
            ]
            return random.choice(messages)

        elif friction_level == 'high':
            # Challenge category - encourage!
            messages = [
                "📸 Just take it one step at a time - building the habit!",
                "🎯 Start small - you've got this!",
                "✨ Every attempt is progress - keep going!",
                "🌱 Growing this habit step by step!"
            ]
            return random.choice(messages)

        else:
            # Medium friction or no data
            return ""

    async def _enhance_task_with_checkin(
        self,
        task: Dict,
        checkin_prefs: Dict
    ) -> Dict:
        """
        Enhance task metadata with check-in feedback.

        NEW: Adds timing adjustments, selection reasons, and motivational messages
        """
        # Apply timing adjustments
        category = task.get('category')
        timing_adjustments = checkin_prefs.get('timing_adjustments', {})

        if category in timing_adjustments:
            adjustment = timing_adjustments[category]
            task['timing_adjustment'] = adjustment  # 'earlier' or 'later'
            logger.debug(f"[PRESEED] Timing adjustment for {task['name']}: {adjustment}")

        # Add motivational messages based on friction analysis (FIX #7)
        friction_analysis = checkin_prefs.get('friction_analysis', {})
        if category in friction_analysis:
            data = friction_analysis[category]
            friction_score = data.get('friction_score', 0.5)
            total_attempts = data.get('total_attempts', 0)
            avg_rating = data.get('avg_experience_rating', 3.0)

            # Determine friction level
            if friction_score <= 0.3:
                friction_level = 'low'
            elif friction_score <= 0.6:
                friction_level = 'medium'
            else:
                friction_level = 'high'

            # Generate motivational message
            motivational_msg = self._generate_motivational_message(
                task=task,
                category=category,
                friction_level=friction_level,
                completion_count=total_attempts,
                avg_rating=avg_rating
            )

            # Add to task description if message exists
            if motivational_msg:
                current_description = task.get('description', '')
                task['description'] = f"{current_description}\n\n{motivational_msg}"
                task['has_motivational_message'] = True
                logger.debug(f"[PRESEED] Added motivational message to {task['name']}")

        return task

    async def _get_selection_reason(self, user_id: str, task: Dict, checkin_prefs: Dict) -> str:
        """
        Generate human-readable reason with check-in context.

        Args:
            user_id: User ID
            task: Task dictionary
            checkin_prefs: Check-in preferences

        Returns:
            Reason string (e.g., "You enjoyed similar tasks")
        """
        category = task.get('category', 'general')
        reasons = []

        # Check-in reasons (NEW)
        if category in checkin_prefs.get('enjoyed_categories', []):
            reasons.append("you enjoyed similar tasks")

        if category in checkin_prefs.get('continue_categories', []):
            reasons.append("you want to continue this")

        # Category score
        category_scores = checkin_prefs.get('category_scores', {})
        if category in category_scores:
            score = category_scores[category]
            if score > 0.7:
                reasons.append(f"high preference score ({score:.1f})")

        # Fallback to existing logic
        if not reasons:
            task_id = task.get('id')
            if task_id:
                try:
                    query = """
                        SELECT
                            AVG(satisfaction_rating) as avg_satisfaction,
                            COUNT(*) as total_count,
                            SUM(CASE WHEN completion_status = 'completed' THEN 1 ELSE 0 END) as completed_count
                        FROM task_feedback_complete
                        WHERE profile_id = $1
                          AND task_library_id = $2
                    """

                    result = await self.db.fetchrow(query, user_id, task_id)

                    if result:
                        # Use .get() for safer dictionary access (adapter might return different field names)
                        total_count = result.get('total_count', result.get('count', 0))
                        completed_count = result.get('completed_count', 0)
                        avg_sat = result.get('avg_satisfaction')

                        if total_count and total_count > 0:
                            completion_rate = completed_count / total_count

                            if avg_sat and avg_sat >= 4.0:
                                reasons.append(f"high satisfaction ({avg_sat:.1f}/5)")
                            elif completion_rate >= 0.8:
                                reasons.append(f"high completion rate ({int(completion_rate * 100)}%)")
                            else:
                                reasons.append("previously completed")
                        else:
                            reasons.append("new task - exploration")
                    else:
                        reasons.append("new task - exploration")

                except Exception as e:
                    logger.warning(f"[PRESEED] Could not get selection reason: {e}")
                    reasons.append("selected for you")
            else:
                reasons.append("matches your archetype")

        return ", ".join(reasons)

    async def _fill_to_minimum(
        self,
        selected_tasks: List[Dict],
        category_counts: Dict[str, int],
        user_id: str,
        archetype: str,
        mode: str,
        allowed_categories: List[str],
        checkin_prefs: Dict
    ):
        """Try to add more tasks to reach minimum."""
        while len(selected_tasks) < self.MIN_TASKS:
            # Try categories that haven't hit limit
            added = False

            for category in allowed_categories:
                if category_counts.get(category, 0) < self.MAX_TASKS_PER_CATEGORY:
                    try:
                        tasks = await self.adaptive_selector.select_tasks_for_block(
                            user_id=user_id,
                            category=category,
                            archetype=archetype,
                            mode=mode,
                            time_of_day='any',
                            count=1
                        )

                        if tasks:
                            task = tasks[0]
                            task = await self._enhance_task_with_checkin(task, checkin_prefs)
                            task['selection_reason'] = await self._get_selection_reason(user_id, task, checkin_prefs, preferences=None)
                            task['source'] = 'library'
                            task['time_preference'] = task.get('time_of_day_preference', 'any')
                            selected_tasks.append(task)
                            category_counts[category] = category_counts.get(category, 0) + 1
                            added = True
                            break

                    except Exception:
                        continue

            if not added:
                break  # Can't add more tasks

    def _enhance_task_with_preferences(self, task: Dict, preferences: Dict) -> Dict:
        """
        Enhance task with user preference data for scheduling.

        Args:
            task: Task dict from library
            preferences: User preferences dict with wake_time, sleep_time, workout_timing, etc.

        Returns:
            Enhanced task with preference-based metadata
        """
        # Set workout timing preference for movement tasks
        if task.get('category') == 'movement':
            preferred_workout_time = preferences.get('preferred_workout_time')
            if preferred_workout_time:
                if preferred_workout_time == 'morning':
                    task['time_preference'] = 'morning'
                    logger.debug(f"[PRESEED] Set {task['name']} to morning (user prefers morning workouts)")
                elif preferred_workout_time == 'evening':
                    task['time_preference'] = 'evening'
                    logger.debug(f"[PRESEED] Set {task['name']} to evening (user prefers evening workouts)")

        # Check if task fits user's available time slots
        available_slots = preferences.get('available_time_slots', [])
        if available_slots:
            task_time = task.get('time_of_day_preference', 'any')
            if task_time != 'any' and task_time not in available_slots:
                # Task doesn't fit user's schedule - mark for downprioritization
                task['schedule_fit'] = 'poor'
                logger.debug(f"[PRESEED] Task {task['name']} has poor schedule fit (wants {task_time}, user has {available_slots})")
            else:
                task['schedule_fit'] = 'good'

        return task

    async def _get_selection_reason(
        self,
        user_id: str,
        task: Dict,
        checkin_prefs: Dict,
        preferences: Optional[Dict] = None
    ) -> str:
        """
        Generate selection reason for task including preferences.

        Args:
            user_id: User ID
            task: Task dict
            checkin_prefs: Check-in feedback
            preferences: User preferences

        Returns:
            Selection reason string
        """
        reasons = []
        category = task.get('category', 'general')

        # Friction-based reason
        low_friction = checkin_prefs.get('low_friction_categories', [])
        high_friction = checkin_prefs.get('high_friction_categories', [])

        if category in low_friction:
            reasons.append(f"You've excelled at {category}")
        elif category in high_friction:
            reasons.append(f"Simplified {category} task to reduce friction")

        # Preference-based reason
        if preferences:
            if 'goals' in preferences and category in preferences['goals']:
                reasons.append(f"Matches your {category} goal")

            if task.get('category') == 'movement' and preferences.get('preferred_workout_time'):
                workout_time = preferences['preferred_workout_time']
                reasons.append(f"Scheduled for {workout_time} as preferred")

        # Default
        if not reasons:
            reasons.append(f"Selected for {category} balance")

        return ". ".join(reasons)

    def _empty_response(self, feedback_count: int, error: Optional[str] = None) -> Dict:
        """Return empty response (fallback to pure AI)."""
        response = {
            'has_sufficient_feedback': False,
            'preselected_tasks': [],
            'selection_stats': {
                'total_selected': 0,
                'feedback_count': feedback_count,
                'checkin_feedback_used': False,
                # NEW: Friction-based fields
                'low_friction_categories': [],
                'medium_friction_categories': [],
                'high_friction_categories': [],
                'friction_analysis': {},
                # Backward compatibility (deprecated)
                'categories_excluded': [],
                'categories_boosted': [],
                'learning_phase': 'discovery',
                'categories_covered': []
            }
        }

        if error:
            response['selection_stats']['error'] = error

        return response
