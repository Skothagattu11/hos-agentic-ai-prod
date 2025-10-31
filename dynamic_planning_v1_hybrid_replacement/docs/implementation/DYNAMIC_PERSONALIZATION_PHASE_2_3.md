# 🚀 HolisticOS Dynamic Personalization - Phase 2 & 3
## Adaptive Learning & Advanced Personalization

**Document Version:** 1.0
**Created:** 2025-10-24
**Prerequisites:** Phase 1 Complete

---

## **PHASE 2: ADAPTIVE LEARNING (Week 3-4)**
### Goal: System learns and adapts based on user behavior

### Overview

In Phase 2, we move from "variety" to "intelligence". The system now:
- Detects which tasks users love/hate
- Auto-adjusts difficulty based on completion patterns
- Provides weekly personalization summaries
- Implements the 7-day discovery journey

---

### Backend Work

#### 2.1 Adaptive Task Selector (Day 1-2)

**File:** `services/adaptive_task_selector.py` (NEW)

```python
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from services.task_library_service import TaskLibraryService
from services.feedback_analyzer_service import FeedbackAnalyzerService

class AdaptiveTaskSelector:
    """
    Selects tasks based on learned user preferences
    Implements adaptation logic: high completion → keep, low completion → pivot
    """

    def __init__(self):
        self.task_library = TaskLibraryService()
        self.feedback_analyzer = FeedbackAnalyzerService()

    async def select_tasks_for_block(
        self,
        user_id: str,
        category: str,
        archetype: str,
        mode: str,
        time_of_day: str,
        count: int = 1
    ) -> List[Dict]:
        """
        Select tasks with adaptive intelligence

        Adaptation Rules:
        1. High completion rate (>80%) → Prioritize similar tasks
        2. Low completion rate (<40%) → Pivot to alternatives
        3. Moderate rate (40-80%) → Continue testing variations
        """

        # Get user profile
        profile = await self.feedback_analyzer.get_user_profile(user_id)

        if not profile:
            # New user - use default task library selection
            return await self.task_library.get_tasks_for_category(
                category=category,
                archetype=archetype,
                mode=mode,
                limit=count
            )

        # Get learning phase
        learning_phase = profile.get('learning_phase', 'discovery')

        # Get category affinity
        category_affinity = profile.get('category_affinity', {})
        affinity_score = category_affinity.get(category, 0.5)

        # Get subcategory affinity
        subcategory_affinity = profile.get('subcategory_affinity', {})

        # Adaptation strategy based on learning phase
        if learning_phase == 'discovery':
            return await self._discovery_phase_selection(
                user_id, category, archetype, mode, count
            )
        elif learning_phase == 'establishment':
            return await self._establishment_phase_selection(
                user_id, category, archetype, mode, affinity_score, subcategory_affinity, count
            )
        else:  # mastery
            return await self._mastery_phase_selection(
                user_id, category, archetype, mode, affinity_score, subcategory_affinity, count
            )

    async def _discovery_phase_selection(
        self,
        user_id: str,
        category: str,
        archetype: str,
        mode: str,
        count: int
    ) -> List[Dict]:
        """
        Discovery Phase (Week 1): Maximum variety
        Goal: Test 3-5 variations per category
        """

        # Get recently used to maximize variety
        recently_used = await self.task_library.get_recently_used_variation_groups(user_id, days=3)

        # Get diverse tasks
        tasks = await self.task_library.get_tasks_for_category(
            category=category,
            archetype=archetype,
            mode=mode,
            exclude_recently_used=recently_used,
            limit=count * 3  # Get more options
        )

        # Prioritize tasks user hasn't tried
        user_feedback = await self._get_user_feedback_for_category(user_id, category, days=7)
        tried_task_ids = set([fb['task_library_id'] for fb in user_feedback if fb.get('task_library_id')])

        # Separate tried vs untried
        untried = [t for t in tasks if t['id'] not in tried_task_ids]
        tried = [t for t in tasks if t['id'] in tried_task_ids]

        # Prefer untried tasks (80%), include some tried (20%)
        selected = []
        if len(untried) >= count:
            selected = untried[:count]
        else:
            selected = untried + tried[:count - len(untried)]

        return selected[:count]

    async def _establishment_phase_selection(
        self,
        user_id: str,
        category: str,
        archetype: str,
        mode: str,
        affinity_score: float,
        subcategory_affinity: Dict[str, float],
        count: int
    ) -> List[Dict]:
        """
        Establishment Phase (Week 2-3): Balance favorites + exploration
        Goal: Build consistency with proven tasks, continue exploration
        """

        # Get tasks user has completed successfully
        user_feedback = await self._get_user_feedback_for_category(user_id, category, days=14)

        # Calculate task success rates
        task_success = {}
        for fb in user_feedback:
            task_id = fb.get('task_library_id')
            if not task_id:
                continue

            if task_id not in task_success:
                task_success[task_id] = {'completed': 0, 'total': 0}

            task_success[task_id]['total'] += 1
            if fb['completed']:
                task_success[task_id]['completed'] += 1

        # Identify high performers (>70% completion)
        high_performers = [
            task_id for task_id, stats in task_success.items()
            if stats['completed'] / stats['total'] > 0.7 and stats['total'] >= 2
        ]

        # Get recently used
        recently_used = await self.task_library.get_recently_used_variation_groups(user_id, days=2)

        # Strategy: 70% proven favorites, 30% new exploration
        favorite_count = int(count * 0.7)
        explore_count = count - favorite_count

        selected = []

        # Add favorites
        if high_performers:
            for task_id in high_performers[:favorite_count]:
                task = await self.task_library.get_task_by_id(task_id)
                if task and task['variation_group'] not in recently_used:
                    selected.append(task)

        # Fill remaining with exploration
        if len(selected) < count:
            explore_tasks = await self.task_library.get_tasks_for_category(
                category=category,
                archetype=archetype,
                mode=mode,
                exclude_recently_used=recently_used,
                limit=explore_count * 2
            )

            # Filter out already selected
            selected_ids = set([t['id'] for t in selected])
            new_tasks = [t for t in explore_tasks if t['id'] not in selected_ids]

            selected.extend(new_tasks[:count - len(selected)])

        return selected[:count]

    async def _mastery_phase_selection(
        self,
        user_id: str,
        category: str,
        archetype: str,
        mode: str,
        affinity_score: float,
        subcategory_affinity: Dict[str, float],
        count: int
    ) -> List[Dict]:
        """
        Mastery Phase (Week 4+): Optimized personalization
        Goal: Deliver highly personalized, proven tasks with occasional novelty
        """

        # Similar to establishment but more weighted to favorites
        # 85% proven, 15% exploration

        user_feedback = await self._get_user_feedback_for_category(user_id, category, days=30)

        # Calculate task success rates
        task_success = {}
        for fb in user_feedback:
            task_id = fb.get('task_library_id')
            if not task_id:
                continue

            if task_id not in task_success:
                task_success[task_id] = {'completed': 0, 'total': 0, 'avg_satisfaction': 0, 'satisfaction_count': 0}

            task_success[task_id]['total'] += 1
            if fb['completed']:
                task_success[task_id]['completed'] += 1

            # Track satisfaction
            if fb.get('satisfaction_rating'):
                task_success[task_id]['avg_satisfaction'] += fb['satisfaction_rating']
                task_success[task_id]['satisfaction_count'] += 1

        # Calculate final scores (completion rate + satisfaction)
        scored_tasks = []
        for task_id, stats in task_success.items():
            if stats['total'] < 2:  # Need at least 2 data points
                continue

            completion_rate = stats['completed'] / stats['total']
            satisfaction = 0.5  # default
            if stats['satisfaction_count'] > 0:
                satisfaction = stats['avg_satisfaction'] / stats['satisfaction_count'] / 5  # Normalize to 0-1

            # Combined score
            score = (completion_rate * 0.7) + (satisfaction * 0.3)

            scored_tasks.append({
                'task_id': task_id,
                'score': score,
                'completion_rate': completion_rate
            })

        # Sort by score
        scored_tasks.sort(key=lambda x: x['score'], reverse=True)

        # Get recently used
        recently_used = await self.task_library.get_recently_used_variation_groups(user_id, days=1)

        # Select top performers
        selected = []
        for scored in scored_tasks:
            task = await self.task_library.get_task_by_id(scored['task_id'])
            if task and task['variation_group'] not in recently_used:
                selected.append(task)

            if len(selected) >= int(count * 0.85):
                break

        # Add exploration tasks
        if len(selected) < count:
            explore_tasks = await self.task_library.get_tasks_for_category(
                category=category,
                archetype=archetype,
                mode=mode,
                exclude_recently_used=recently_used,
                limit=5
            )

            selected_ids = set([t['id'] for t in selected])
            new_tasks = [t for t in explore_tasks if t['id'] not in selected_ids]
            selected.extend(new_tasks[:count - len(selected)])

        return selected[:count]

    async def _get_user_feedback_for_category(
        self,
        user_id: str,
        category: str,
        days: int
    ) -> List[Dict]:
        """Get user feedback for specific category"""
        from shared_libs.supabase_client import get_supabase_client
        supabase = get_supabase_client()

        cutoff_date = datetime.now() - timedelta(days=days)

        result = supabase.table('user_task_feedback')\
            .select('*, task_library:task_library_id(*)')\
            .eq('user_id', user_id)\
            .gte('scheduled_date', cutoff_date.date())\
            .execute()

        # Filter by category
        filtered = [
            fb for fb in result.data
            if fb.get('task_library') and fb['task_library']['category'] == category
        ]

        return filtered
```

#### 2.2 Learning Phase Manager (Day 2-3)

**File:** `services/learning_phase_manager.py` (NEW)

```python
from datetime import datetime, timedelta
from typing import Optional
from shared_libs.supabase_client import get_supabase_client

class LearningPhaseManager:
    """
    Manages user progression through learning phases
    - Discovery (Week 1): Days 1-7
    - Establishment (Week 2-3): Days 8-21
    - Mastery (Week 4+): Days 22+
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    async def update_learning_phase(self, user_id: str):
        """
        Update user's learning phase based on days since start and data
        """

        # Get user profile
        result = self.supabase.table('user_preference_profile')\
            .select('*')\
            .eq('user_id', user_id)\
            .single()\
            .execute()

        if not result.data:
            # Create new profile
            await self._create_new_profile(user_id)
            return

        profile = result.data
        discovery_start = profile.get('discovery_start_date')

        if not discovery_start:
            # Set discovery start date
            self.supabase.table('user_preference_profile')\
                .update({'discovery_start_date': datetime.now().date()})\
                .eq('user_id', user_id)\
                .execute()
            return

        # Calculate days since start
        days_since_start = (datetime.now().date() - discovery_start).days

        # Determine phase
        new_phase = self._determine_phase(days_since_start, profile)
        current_phase = profile.get('learning_phase', 'discovery')

        if new_phase != current_phase:
            # Phase transition!
            self.supabase.table('user_preference_profile')\
                .update({'learning_phase': new_phase})\
                .eq('user_id', user_id)\
                .execute()

            # Trigger phase transition notification (future: send to user)
            await self._send_phase_transition_insight(user_id, current_phase, new_phase)

    def _determine_phase(self, days: int, profile: Dict) -> str:
        """
        Determine phase based on days and user data quality

        Rules:
        - Discovery: Days 1-7 OR insufficient data (<20 tasks)
        - Establishment: Days 8-21 AND sufficient data (20-50 tasks)
        - Mastery: Days 22+ AND high data quality (50+ tasks, >60% completion)
        """

        total_tasks = profile.get('total_tasks_scheduled', 0)
        completion_rate = profile.get('completion_rate', 0)

        # Force discovery if insufficient data
        if total_tasks < 20:
            return 'discovery'

        # Mastery requires both time and performance
        if days >= 22 and total_tasks >= 50 and completion_rate >= 0.6:
            return 'mastery'

        # Establishment: middle ground
        if days >= 8 and total_tasks >= 20:
            return 'establishment'

        # Default: discovery
        return 'discovery'

    async def _create_new_profile(self, user_id: str):
        """Create initial user preference profile"""
        self.supabase.table('user_preference_profile').insert({
            'user_id': user_id,
            'archetype': 'Foundation Builder',  # Default
            'learning_phase': 'discovery',
            'discovery_start_date': datetime.now().date(),
            'created_at': datetime.now()
        }).execute()

    async def _send_phase_transition_insight(
        self,
        user_id: str,
        old_phase: str,
        new_phase: str
    ):
        """
        Create insight for phase transition
        """
        from services.insights_extraction_service import InsightsExtractionService
        insights_service = InsightsExtractionService()

        messages = {
            'discovery_to_establishment': {
                'title': 'Week 1 Complete! 🎉',
                'message': 'You\'ve tried many different activities. We\'ve learned what energizes you most. Your routine will now focus on your favorites while continuing to explore.',
                'category': 'milestone'
            },
            'establishment_to_mastery': {
                'title': 'Routine Mastery Unlocked! 🌟',
                'message': 'Your personalized routine is now highly optimized. We\'ve identified your preferred activities and optimal timing. Your plan adapts automatically.',
                'category': 'milestone'
            }
        }

        key = f"{old_phase}_to_{new_phase}"
        if key in messages:
            await insights_service.store_simple_insight(
                user_id=user_id,
                insight_text=messages[key]['message'],
                category=messages[key]['category'],
                metadata={'title': messages[key]['title'], 'phase_transition': True}
            )
```

#### 2.3 Modified RoutineGenerationService (Day 3-4)

**Update:** `services/routine_generation_service.py`

```python
from services.adaptive_task_selector import AdaptiveTaskSelector
from services.learning_phase_manager import LearningPhaseManager

class RoutineGenerationService:
    """Enhanced with adaptive task selection"""

    def __init__(self):
        self.task_library = TaskLibraryService()
        self.feedback_analyzer = FeedbackAnalyzerService()
        self.adaptive_selector = AdaptiveTaskSelector()  # NEW
        self.phase_manager = LearningPhaseManager()      # NEW

    async def generate_routine(
        self,
        user_id: str,
        archetype: str,
        preferences: Dict,
        use_dynamic: bool = True
    ) -> Dict:
        """Enhanced with learning phase management"""

        # Update learning phase
        await self.phase_manager.update_learning_phase(user_id)

        # ... existing code

    async def _generate_dynamic_plan(
        self,
        user_id: str,
        archetype: str,
        preferences: Dict
    ) -> Dict:
        """Generate plan using ADAPTIVE task selection"""

        # Get user profile
        user_profile = await self.feedback_analyzer.get_user_profile(user_id)
        mode = user_profile.get('current_mode', 'medium') if user_profile else 'medium'

        # Build time blocks with ADAPTIVE tasks
        time_blocks = []

        # Morning Block
        morning_tasks = []

        # Hydration (adaptive)
        hydration_tasks = await self.adaptive_selector.select_tasks_for_block(
            user_id=user_id,
            category='hydration',
            archetype=archetype,
            mode=mode,
            time_of_day='morning',
            count=1
        )
        if hydration_tasks:
            morning_tasks.append(self._format_task_for_plan(hydration_tasks[0], '06:30 AM'))

        # Movement (adaptive)
        movement_tasks = await self.adaptive_selector.select_tasks_for_block(
            user_id=user_id,
            category='movement',
            archetype=archetype,
            mode=mode,
            time_of_day='morning',
            count=1
        )
        if movement_tasks:
            morning_tasks.append(self._format_task_for_plan(movement_tasks[0], '06:45 AM'))

        # ... continue for all blocks

        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'system': 'HolisticOS',
            'content': {'time_blocks': time_blocks},
            'archetype': archetype,
            'plan_type': 'adaptive_routine',  # Changed from 'dynamic_routine'
            'model_used': 'task_library_v2_adaptive',
            'readiness_mode': mode
        }
```

#### 2.4 Weekly Summary Generator (Day 4-5)

**File:** `services/weekly_summary_service.py` (NEW)

```python
from datetime import datetime, timedelta
from typing import Dict, List
from shared_libs.supabase_client import get_supabase_client

class WeeklySummaryService:
    """
    Generates weekly personalization summaries for users
    Shows what system learned about them
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    async def generate_weekly_summary(self, user_id: str) -> Dict:
        """
        Generate summary of past week's activity and learnings
        """

        # Get past week's feedback
        week_ago = datetime.now() - timedelta(days=7)

        feedback_result = self.supabase.table('user_task_feedback')\
            .select('*, task_library:task_library_id(*)')\
            .eq('user_id', user_id)\
            .gte('scheduled_date', week_ago.date())\
            .execute()

        feedbacks = feedback_result.data

        if not feedbacks:
            return {'error': 'No data for past week'}

        # Analyze patterns
        summary = {
            'week_start': week_ago.strftime('%Y-%m-%d'),
            'week_end': datetime.now().strftime('%Y-%m-%d'),
            'total_tasks_scheduled': len(feedbacks),
            'total_completed': sum(1 for fb in feedbacks if fb['completed']),
            'completion_rate': sum(1 for fb in feedbacks if fb['completed']) / len(feedbacks),
            'top_categories': self._analyze_top_categories(feedbacks),
            'top_tasks': self._analyze_top_tasks(feedbacks),
            'improvement_areas': self._identify_improvement_areas(feedbacks),
            'streaks': self._calculate_streaks(feedbacks),
            'personalization_insights': self._generate_insights(feedbacks)
        }

        # Store as insight
        await self._create_weekly_insight(user_id, summary)

        return summary

    def _analyze_top_categories(self, feedbacks: List[Dict]) -> List[Dict]:
        """Find categories user completed most"""
        from collections import Counter

        category_completion = Counter()
        category_total = Counter()

        for fb in feedbacks:
            task = fb.get('task_library')
            if not task:
                continue

            category = task['category']
            category_total[category] += 1
            if fb['completed']:
                category_completion[category] += 1

        # Calculate completion rates
        results = []
        for category, completed in category_completion.most_common(3):
            total = category_total[category]
            results.append({
                'category': category,
                'completed': completed,
                'total': total,
                'rate': completed / total
            })

        return results

    def _analyze_top_tasks(self, feedbacks: List[Dict]) -> List[Dict]:
        """Find specific tasks user loved"""
        from collections import Counter

        completed_tasks = [
            fb for fb in feedbacks
            if fb['completed'] and fb.get('task_library')
        ]

        task_counter = Counter()
        for fb in completed_tasks:
            task_name = fb['task_library']['name']
            task_counter[task_name] += 1

        return [
            {'task': task, 'count': count}
            for task, count in task_counter.most_common(5)
        ]

    def _identify_improvement_areas(self, feedbacks: List[Dict]) -> List[str]:
        """Identify categories with low completion"""
        from collections import defaultdict

        category_stats = defaultdict(lambda: {'completed': 0, 'total': 0})

        for fb in feedbacks:
            task = fb.get('task_library')
            if not task:
                continue

            category = task['category']
            category_stats[category]['total'] += 1
            if fb['completed']:
                category_stats[category]['completed'] += 1

        # Find low performers (<50% completion)
        improvements = []
        for category, stats in category_stats.items():
            rate = stats['completed'] / stats['total']
            if rate < 0.5 and stats['total'] >= 3:  # At least 3 attempts
                improvements.append(f"{category} tasks (only {rate*100:.0f}% completed)")

        return improvements

    def _calculate_streaks(self, feedbacks: List[Dict]) -> Dict:
        """Calculate streaks"""
        # Sort by date
        sorted_fb = sorted(feedbacks, key=lambda x: x['scheduled_date'])

        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        last_date = None

        for fb in sorted_fb:
            if not fb['completed']:
                temp_streak = 0
                continue

            current_date = fb['scheduled_date']

            if last_date is None or (current_date - last_date).days == 1:
                temp_streak += 1
            else:
                temp_streak = 1

            longest_streak = max(longest_streak, temp_streak)
            last_date = current_date

        current_streak = temp_streak

        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }

    def _generate_insights(self, feedbacks: List[Dict]) -> List[str]:
        """Generate natural language insights"""
        insights = []

        # Completion rate insight
        completion_rate = sum(1 for fb in feedbacks if fb['completed']) / len(feedbacks)
        if completion_rate >= 0.8:
            insights.append(f"You crushed it! {completion_rate*100:.0f}% completion rate this week 🔥")
        elif completion_rate >= 0.6:
            insights.append(f"Solid week! {completion_rate*100:.0f}% completion rate")
        else:
            insights.append(f"Room to grow: {completion_rate*100:.0f}% completion this week")

        # Category preference insight
        top_cats = self._analyze_top_categories(feedbacks)
        if top_cats:
            top_cat = top_cats[0]
            insights.append(f"You love {top_cat['category']} activities! ({top_cat['completed']}/{top_cat['total']} completed)")

        # Unique tasks tried
        unique_tasks = len(set(fb['task_library_id'] for fb in feedbacks if fb.get('task_library_id')))
        if unique_tasks >= 10:
            insights.append(f"Explorer mindset: You tried {unique_tasks} different activities!")

        return insights

    async def _create_weekly_insight(self, user_id: str, summary: Dict):
        """Store weekly summary as insight"""
        from services.insights_extraction_service import InsightsExtractionService
        insights_service = InsightsExtractionService()

        # Format message
        message_parts = []
        message_parts.append(f"**Week of {summary['week_start']}**\n")
        message_parts.append(f"✓ Completed {summary['total_completed']}/{summary['total_tasks_scheduled']} tasks ({summary['completion_rate']*100:.0f}%)\n")

        if summary['top_tasks']:
            message_parts.append("\n**Your Favorites:**\n")
            for task in summary['top_tasks'][:3]:
                message_parts.append(f"• {task['task']} ({task['count']}x)\n")

        if summary['personalization_insights']:
            message_parts.append("\n**Insights:**\n")
            for insight in summary['personalization_insights']:
                message_parts.append(f"• {insight}\n")

        full_message = ''.join(message_parts)

        await insights_service.store_simple_insight(
            user_id=user_id,
            insight_text=full_message,
            category='weekly_summary',
            metadata={'week_start': summary['week_start'], 'completion_rate': summary['completion_rate']}
        )
```

---

### Frontend Work (Day 5-7)

#### 2.5 Weekly Summary UI Component

**File:** `hos_app/lib/presentation/widgets/weekly_summary_card.dart` (NEW)

```dart
import 'package:flutter/material.dart';

class WeeklySummaryCard extends StatelessWidget {
  final Map<String, dynamic> summary;

  const WeeklySummaryCard({Key? key, required this.summary}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final completionRate = (summary['completion_rate'] * 100).toInt();
    final topTasks = summary['top_tasks'] as List;
    final insights = summary['personalization_insights'] as List;

    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Icon(Icons.auto_graph, color: Theme.of(context).primaryColor),
                SizedBox(width: 8),
                Text(
                  'This Week\'s Progress',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ],
            ),
            SizedBox(height: 16),

            // Completion Rate
            LinearProgressIndicator(
              value: summary['completion_rate'],
              backgroundColor: Colors.grey[800],
              valueColor: AlwaysStoppedAnimation(
                completionRate >= 80 ? Colors.green :
                completionRate >= 60 ? Colors.amber : Colors.red
              ),
            ),
            SizedBox(height: 8),
            Text('$completionRate% completion rate'),
            SizedBox(height: 16),

            // Top Tasks
            if (topTasks.isNotEmpty) ...[
              Text('Your Favorites:', style: TextStyle(fontWeight: FontWeight.bold)),
              SizedBox(height: 8),
              ...topTasks.take(3).map((task) => Padding(
                padding: EdgeInsets.only(bottom: 4),
                child: Row(
                  children: [
                    Icon(Icons.favorite, size: 16, color: Colors.red),
                    SizedBox(width: 8),
                    Expanded(child: Text('${task['task']} (${task['count']}x)')),
                  ],
                ),
              )),
              SizedBox(height: 16),
            ],

            // Insights
            if (insights.isNotEmpty) ...[
              Text('Insights:', style: TextStyle(fontWeight: FontWeight.bold)),
              SizedBox(height: 8),
              ...insights.map((insight) => Padding(
                padding: EdgeInsets.only(bottom: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.lightbulb_outline, size: 16),
                    SizedBox(width: 8),
                    Expanded(child: Text(insight)),
                  ],
                ),
              )),
            ],
          ],
        ),
      ),
    );
  }
}
```

#### 2.6 Backend API Endpoint for Weekly Summary

**File:** `services/api_gateway/feedback_endpoints.py` (MODIFY)

```python
from services.weekly_summary_service import WeeklySummaryService

weekly_summary_service = WeeklySummaryService()

@router.get("/weekly-summary/{user_id}")
async def get_weekly_summary(user_id: str):
    """Get weekly personalization summary"""
    summary = await weekly_summary_service.generate_weekly_summary(user_id)
    return summary
```

---

## **PHASE 2 DELIVERABLES SUMMARY**

### What Gets Released (Week 4 End)

**User-Facing:**
- ✅ Adaptive task selection (system learns preferences)
- ✅ Weekly personalization summaries
- ✅ Phase transition milestones ("Week 1 complete!")
- ✅ Improved task matching based on completion patterns

**Backend:**
- ✅ Adaptive task selector with learning phases
- ✅ Learning phase management (discovery → establishment → mastery)
- ✅ Weekly summary generator
- ✅ Preference-based task scoring

**Intelligence:**
- ✅ High completion → More of same
- ✅ Low completion → Pivot to alternatives
- ✅ Tracks category/subcategory affinity
- ✅ Balances favorites with exploration

### Success Metrics (Week 5-6)

- Completion rate improvement: +15-20% from baseline
- User engagement with weekly summaries: >60% open rate
- Phase progression: 80% of users reach "establishment" by Week 3
- Task affinity accuracy: Top 3 categories match 70% of completions

---

## **PHASE 3: ADVANCED PERSONALIZATION (Week 5-6)**
### Goal: Mode integration, archetype transitions, and contextual adaptation

### Overview

Phase 3 adds the final polish:
- Mode system (high/medium/low energy days)
- Smooth archetype transitions
- Time-of-day optimization
- Contextual task adjustments

---

### Backend Work

#### 3.1 Mode Detection Service (Day 1-2)

**File:** `services/mode_detection_service.py` (NEW)

```python
from datetime import datetime, timedelta
from typing import Optional
from shared_libs.supabase_client import get_supabase_client

class ModeDetectionService:
    """
    Automatically detect user's current mode (energy level)
    Based on: sleep quality, completion patterns, HRV (if available)
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    async def detect_mode(self, user_id: str) -> str:
        """
        Detect current mode: 'high', 'medium', 'low'

        Inputs:
        - Last 3 nights sleep quality
        - Last 3 days completion rate
        - Last 7 days trend
        - User manual override (if exists)
        """

        # Check for manual override first
        manual_mode = await self._get_manual_mode_override(user_id)
        if manual_mode:
            return manual_mode

        # Get sleep data (if available from Sahha)
        sleep_score = await self._get_recent_sleep_score(user_id, days=3)

        # Get completion rate (last 3 days)
        completion_rate = await self._get_recent_completion_rate(user_id, days=3)

        # Get trend (is user improving or declining?)
        trend = await self._get_completion_trend(user_id, days=7)

        # Calculate mode
        mode_score = self._calculate_mode_score(sleep_score, completion_rate, trend)

        if mode_score >= 0.7:
            mode = 'high'
        elif mode_score >= 0.4:
            mode = 'medium'
        else:
            mode = 'low'

        # Store mode
        await self._update_user_mode(user_id, mode)

        return mode

    async def _get_manual_mode_override(self, user_id: str) -> Optional[str]:
        """Check if user manually set their mode today"""
        result = self.supabase.table('user_mode_overrides')\
            .select('mode')\
            .eq('user_id', user_id)\
            .eq('date', datetime.now().date())\
            .single()\
            .execute()

        return result.data.get('mode') if result.data else None

    async def _get_recent_sleep_score(self, user_id: str, days: int) -> float:
        """Get average sleep quality from last N days (0-1 scale)"""
        # TODO: Integrate with Sahha API
        # For now, return neutral
        return 0.5

    async def _get_recent_completion_rate(self, user_id: str, days: int) -> float:
        """Get completion rate from last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)

        result = self.supabase.table('user_task_feedback')\
            .select('completed')\
            .eq('user_id', user_id)\
            .gte('scheduled_date', cutoff_date.date())\
            .execute()

        if not result.data:
            return 0.5  # Neutral

        completed = sum(1 for fb in result.data if fb['completed'])
        return completed / len(result.data)

    async def _get_completion_trend(self, user_id: str, days: int) -> float:
        """
        Get trend direction (-1 to 1)
        Positive = improving, Negative = declining
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        result = self.supabase.table('user_task_feedback')\
            .select('scheduled_date, completed')\
            .eq('user_id', user_id)\
            .gte('scheduled_date', cutoff_date.date())\
            .order('scheduled_date')\
            .execute()

        if len(result.data) < 4:
            return 0  # Neutral

        # Split into first half and second half
        mid = len(result.data) // 2
        first_half = result.data[:mid]
        second_half = result.data[mid:]

        first_rate = sum(1 for fb in first_half if fb['completed']) / len(first_half)
        second_rate = sum(1 for fb in second_half if fb['completed']) / len(second_half)

        # Return trend (-1 to 1)
        return (second_rate - first_rate) * 2

    def _calculate_mode_score(
        self,
        sleep_score: float,
        completion_rate: float,
        trend: float
    ) -> float:
        """
        Calculate overall mode score (0-1)

        Weights:
        - Sleep: 40%
        - Completion rate: 40%
        - Trend: 20%
        """
        score = (sleep_score * 0.4) + (completion_rate * 0.4) + ((trend + 1) / 2 * 0.2)
        return max(0, min(1, score))  # Clamp to 0-1

    async def _update_user_mode(self, user_id: str, mode: str):
        """Update user's current mode in profile"""
        self.supabase.table('user_preference_profile')\
            .update({'current_mode': mode})\
            .eq('user_id', user_id)\
            .execute()

    async def set_manual_mode(self, user_id: str, mode: str):
        """Allow user to manually override mode for today"""
        self.supabase.table('user_mode_overrides').upsert({
            'user_id': user_id,
            'date': datetime.now().date(),
            'mode': mode
        }).execute()
```

**Add table:**

```sql
CREATE TABLE user_mode_overrides (
    user_id UUID NOT NULL,
    date DATE NOT NULL,
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('high', 'medium', 'low')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, date)
);
```

#### 3.2 Archetype Transition Manager (Day 2-3)

**File:** `services/archetype_transition_manager.py` (NEW)

```python
from datetime import datetime, timedelta
from typing import Dict, List
from shared_libs.supabase_client import get_supabase_client

class ArchetypeTransitionManager:
    """
    Handles smooth transitions when user changes archetype
    Gradually shifts tasks over 3 days instead of abrupt change
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    async def initiate_transition(
        self,
        user_id: str,
        old_archetype: str,
        new_archetype: str
    ):
        """
        Start archetype transition
        Creates 3-day transition plan
        """

        # Store transition state
        self.supabase.table('archetype_transitions').insert({
            'user_id': user_id,
            'from_archetype': old_archetype,
            'to_archetype': new_archetype,
            'started_at': datetime.now(),
            'status': 'in_progress',
            'current_day': 1
        }).execute()

        # Create transition insight
        from services.insights_extraction_service import InsightsExtractionService
        insights_service = InsightsExtractionService()

        await insights_service.store_simple_insight(
            user_id=user_id,
            insight_text=f"Transitioning to {new_archetype} mode. Your routine will gradually adjust over the next 3 days.",
            category='archetype_change'
        )

    async def get_transition_blend_ratio(self, user_id: str) -> Optional[Dict]:
        """
        Get current transition blend ratio
        Returns: {'old_ratio': 0.7, 'new_ratio': 0.3, 'day': 1} or None
        """

        result = self.supabase.table('archetype_transitions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'in_progress')\
            .single()\
            .execute()

        if not result.data:
            return None

        transition = result.data
        started = transition['started_at']
        days_elapsed = (datetime.now() - started).days

        # 3-day transition
        if days_elapsed >= 3:
            # Complete transition
            self.supabase.table('archetype_transitions')\
                .update({'status': 'completed'})\
                .eq('user_id', user_id)\
                .execute()
            return None

        # Calculate blend ratio
        # Day 1: 70% old, 30% new
        # Day 2: 40% old, 60% new
        # Day 3: 100% new

        ratios = [
            {'old': 0.7, 'new': 0.3, 'day': 1},
            {'old': 0.4, 'new': 0.6, 'day': 2},
            {'old': 0.0, 'new': 1.0, 'day': 3}
        ]

        return ratios[days_elapsed]
```

**Add table:**

```sql
CREATE TABLE archetype_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    from_archetype VARCHAR(50) NOT NULL,
    to_archetype VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'in_progress',
    current_day INT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## **PHASE 3 DELIVERABLES SUMMARY**

### What Gets Released (Week 6 End)

**User-Facing:**
- ✅ Automatic mode detection (adjusts plan difficulty)
- ✅ Manual mode override ("Feeling tired today? Switch to easy mode")
- ✅ Smooth archetype transitions (3-day gradual shift)
- ✅ Context-aware task selection

**Backend:**
- ✅ Mode detection service
- ✅ Archetype transition manager
- ✅ Blended task selection during transitions

**Intelligence:**
- ✅ Sleep + completion patterns → mode detection
- ✅ Gradual archetype shifts (no jarring changes)
- ✅ User can override auto-detection

---

## **FINAL SYSTEM OVERVIEW**

### Complete Data Flow (All Phases)

```
User Opens App
    ↓
Request Daily Plan
    ↓
[Phase 3] Mode Detection → current_mode
[Phase 2] Learning Phase Check → discovery/establishment/mastery
[Phase 3] Archetype Transition Check → blend_ratio (if transitioning)
    ↓
[Phase 2] Adaptive Task Selector
    ├─ User Preference Profile (learned affinities)
    ├─ Task Library (50+ variations)
    ├─ Rotation State (prevent repetition)
    ├─ Mode (high/medium/low)
    └─ Learning Phase Strategy
    ↓
Generate Dynamic Plan
    ├─ 70-85% proven favorites (based on phase)
    ├─ 15-30% exploration tasks
    └─ Mode-appropriate difficulty
    ↓
User Completes Tasks
    ↓
[Phase 1] Feedback Collection
    ├─ Completion tracking
    ├─ Satisfaction ratings (optional)
    └─ Implicit signals (skip patterns, timing)
    ↓
[Phase 2] Preference Update
    ├─ Category affinity recalculation
    ├─ Complexity tolerance
    ├─ Variety seeking score
    └─ Learning phase progression
    ↓
[Phase 2] Weekly Summary
    ├─ Top categories
    ├─ Favorite tasks
    ├─ Completion trends
    └─ Personalization insights
    ↓
[Loop] Next Day → Even More Personalized
```

---

## **ROLLOUT STRATEGY**

### Week-by-Week Deployment

**Week 1-2: Phase 1 to Production**
- Deploy with `ENABLE_DYNAMIC_PLANS=false` initially
- Enable for 10% of users (canary)
- Monitor metrics for 3 days
- If successful: Roll out to 50%, then 100%

**Week 3-4: Phase 2 to Production**
- Deploy adaptive selector with feature flag
- Enable for beta users first
- Collect feedback on weekly summaries
- Full rollout Week 4

**Week 5-6: Phase 3 to Production**
- Deploy mode detection
- Test archetype transitions with volunteers
- Full rollout Week 6

---

## **SUCCESS CRITERIA**

### Phase 1 Success
- ✅ 95%+ dynamic plan generation success rate
- ✅ <500ms API latency
- ✅ 80%+ task variety achieved
- ✅ Zero production incidents

### Phase 2 Success
- ✅ +15-20% completion rate improvement
- ✅ 70%+ affinity accuracy
- ✅ 60%+ weekly summary engagement
- ✅ User feedback: "Feels personalized"

### Phase 3 Success
- ✅ Mode detection accuracy: 75%+
- ✅ Smooth transitions: 90%+ user satisfaction
- ✅ Overall completion rate: 75%+
- ✅ User retention: +25% from baseline

---

**END OF IMPLEMENTATION PLAN**

Ready for production! 🚀
