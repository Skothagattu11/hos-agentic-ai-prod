# Frontend UI Flow Guide for hos_app

**Date**: October 31, 2025
**Purpose**: Complete UI/UX implementation guide for hos_app Flutter application
**Backend Status**: Phase 5.0 Complete ✅
**Frontend Status**: Not Started ❌

---

## 📊 Current State Assessment

### Backend (Phase 5.0) ✅ **COMPLETE**
- ✅ Friction-reduction feedback system working
- ✅ Task check-ins with preferences tracking
- ✅ Daily journal API endpoints
- ✅ Plan generation with Atomic Habits integration
- ✅ Always-live Sahha data fetch with fallback
- ✅ Background scheduler for data refresh
- ✅ FeedbackService detects friction patterns
- ✅ TaskPreseeder applies friction + preference scoring
- ✅ InsightsService generates friction-based insights

### Frontend (hos_app) ❌ **NOT STARTED**
- ❌ No check-in screens implemented
- ❌ No journal submission UI
- ❌ No plan display integrated with friction analysis
- ❌ No feedback collection UI
- ❌ No friction insights visualization

---

## 🎯 Critical UI Flows for MVP (Aligned with Backend)

### **Flow 1: Plan Generation & Display** ⭐ **P0 - CRITICAL**

#### User Journey
```
┌──────────────────────────────────────────────────────────────┐
│ 1. USER OPENS APP                                             │
│    ↓                                                           │
│ 2. HOME SCREEN (Planner Tab)                                  │
│    • Show current plan (if exists)                            │
│    • Show "Generate New Plan" button (if no plan)             │
│    • Display today's tasks with time blocks                   │
│    ↓                                                           │
│ 3. TAP "Generate Plan" OR "Regenerate"                        │
│    • Modal appears with archetype selection                   │
│    • Preferences input (wake/sleep/workout times, goals)      │
│    ↓                                                           │
│ 4. SUBMIT PREFERENCES                                         │
│    • Loading state (70-100 seconds)                           │
│    • Progress indicator "Analyzing health data..."            │
│    • Progress indicator "Creating personalized plan..."       │
│    ↓                                                           │
│ 5. PLAN GENERATED                                             │
│    • Display routine plan with time blocks                    │
│    • Show task list by category (nutrition, movement, etc.)   │
│    • Mark tasks as scheduled in calendar view                 │
│    • Show circadian-optimized timing                          │
└──────────────────────────────────────────────────────────────┘
```

#### API Integration
```dart
// Generate plan
POST /api/user/{user_id}/routine/generate
Body: {
  "archetype": "Peak Performer",
  "preferences": {
    "wake_time": "06:00",
    "sleep_time": "22:00",
    "workout_time": "morning",
    "goals": ["muscle_gain", "better_sleep"]
  },
  "timezone": "America/Los_Angeles"
}

Response: {
  "analysis_id": "uuid",
  "routine_plan": {
    "time_blocks": [
      {
        "time_block": "Morning Activation",
        "start_time": "06:00",
        "end_time": "08:00",
        "tasks": [...]
      }
    ]
  },
  "feedback_count": 0  // First plan
}
```

#### UI Components Needed
- `PlanGenerationModal.dart` - Archetype + preferences input
  - Archetype selection cards (6 archetypes)
  - Time pickers (wake, sleep, workout)
  - Goals multi-select
  - Submit button

- `LoadingPlanScreen.dart` - With progress indicators
  - Animated loading spinner
  - Progress text updates
  - Cancel button (optional)

- `PlanDisplay.dart` - Timeline view with tasks
  - Time block headers
  - Task cards grouped by time
  - Swipe to navigate days

- `TaskCard.dart` - Individual task with category, time, description
  - Category icon + color
  - Task title
  - Scheduled time
  - Duration estimate
  - Tap to expand details

- `TimeBlockIndicator.dart` - Circadian time block visualization
  - Color-coded blocks (morning, afternoon, evening)
  - Time range display
  - Energy level indicator

#### Screen Files to Create
```
lib/presentation/screens/planner/
├── plan_generation_modal.dart
├── loading_plan_screen.dart
├── plan_display_screen.dart
└── widgets/
    ├── archetype_selection_card.dart
    ├── preferences_form.dart
    ├── task_card.dart
    ├── time_block_header.dart
    └── time_block_indicator.dart
```

---

### **Flow 2: Task Check-in Flow** ⭐ **P0 - CRITICAL FOR FRICTION ANALYSIS**

#### User Journey (Evening - 6 PM+)
```
┌──────────────────────────────────────────────────────────────┐
│ 1. NOTIFICATION TRIGGERS                                      │
│    • 6 PM notification: "Time to check in on your day!"      │
│    • Deep link opens CheckinScreen                            │
│    ↓                                                           │
│ 2. CHECK-IN SCREEN                                            │
│    • List of today's completed/skipped tasks                  │
│    • For each task, user answers:                             │
│      - ☑️  "Did you complete this?" (checkbox)                │
│      - 😊 "Did you enjoy this?" (Yes/No buttons)              │
│      - 🔄 "Continue tomorrow?" (Yes/No/Maybe chips)           │
│      - ⏰ "How was timing?" (Perfect/Early/Late buttons)       │
│      - ⭐ "Satisfaction?" (1-5 star slider)                    │
│    ↓                                                           │
│ 3. SUBMIT CHECK-INS                                           │
│    • Batch submit all responses                               │
│    • Success animation (checkmark)                            │
│    • "Thanks for checking in!" message                        │
│    ↓                                                           │
│ 4. NAVIGATE TO DAILY JOURNAL                                  │
│    • Automatic transition to journal screen                   │
└──────────────────────────────────────────────────────────────┘
```

#### API Integration
```dart
// Fetch today's tasks
GET /api/v1/engagement/tasks/{profile_id}

Response: [
  {
    "id": "task-uuid-1",
    "title": "Morning protein shake",
    "category": "nutrition",
    "scheduled_time": "06:30",
    "completed_at": "2025-10-31T06:35:00Z",
    "plan_date": "2025-10-31"
  },
  {
    "id": "task-uuid-2",
    "title": "30-min strength training",
    "category": "movement",
    "scheduled_time": "07:00",
    "completed_at": null,
    "plan_date": "2025-10-31"
  }
]

// Submit check-ins (batch)
POST /api/v1/engagement/batch-checkin
Body: {
  "profile_id": "user123",
  "planned_date": "2025-10-31",
  "checkins": [
    {
      "plan_item_id": "task-uuid-1",
      "completion_status": "completed",
      "enjoyed": true,
      "continue_preference": "yes",
      "timing_feedback": "perfect",
      "satisfaction_rating": 5
    },
    {
      "plan_item_id": "task-uuid-2",
      "completion_status": "partial",
      "enjoyed": false,
      "continue_preference": "maybe",
      "timing_feedback": "late",
      "satisfaction_rating": 2
    }
  ]
}

Response: {
  "success": true,
  "message": "Successfully checked in 2 tasks",
  "items_processed": 2
}
```

#### UI Components Needed
- `CheckinScreen.dart` - Main check-in interface
  - Scrollable list of tasks
  - Filter by completed/all
  - Submit button (disabled until all answered)
  - Progress indicator (e.g., "3 of 8 answered")

- `TaskCheckinCard.dart` - Individual task with feedback inputs
  - Task info header
  - Completion checkbox
  - Feedback question sections
  - Expandable/collapsible

- `EnjoymentToggle.dart` - Yes/No buttons
  - Toggle button group
  - Happy/sad icons
  - Active state styling

- `ContinuePreferenceChips.dart` - Yes/No/Maybe chips
  - Three-option chip selector
  - Active state with background color
  - Icons for each option

- `TimingFeedbackButtons.dart` - Perfect/Early/Late
  - Three-option button group
  - Clock icons
  - Color coding (green/blue/orange)

- `SatisfactionSlider.dart` - 1-5 star rating
  - Interactive star display
  - Tap or drag to rate
  - Label showing rating number

#### Screen Files to Create
```
lib/presentation/screens/checkin/
├── checkin_screen.dart
├── checkin_success_screen.dart
└── widgets/
    ├── task_checkin_card.dart
    ├── enjoyment_toggle.dart
    ├── continue_preference_chips.dart
    ├── timing_feedback_buttons.dart
    ├── satisfaction_slider.dart
    └── checkin_progress_indicator.dart
```

---

### **Flow 3: Daily Journal Flow** ⭐ **P0 - HOLISTIC REFLECTION**

#### User Journey (After Check-in)
```
┌──────────────────────────────────────────────────────────────┐
│ 1. AUTOMATIC NAVIGATION FROM CHECK-IN                        │
│    • OR: Manual tap "Daily Journal" button                    │
│    ↓                                                           │
│ 2. DAILY JOURNAL SCREEN                                       │
│    • Date display: "Thursday, October 31"                     │
│    • Energy level slider (1-5) with icons                     │
│    • Mood rating slider (1-5) with emoji faces                │
│    • Sleep quality slider (1-5) with moon icons               │
│    • Stress level slider (1-5) with icons                     │
│    • Text field: "What went well today?" (multiline)          │
│    • Text field: "What was challenging?" (multiline)          │
│    • Habit completion toggles:                                │
│      ☑️  Did 3+ deep breaths                                  │
│      ☑️  Got morning sunlight                                 │
│      ☑️  Practiced mindfulness                                │
│    ↓                                                           │
│ 3. SUBMIT JOURNAL                                             │
│    • Success animation                                        │
│    • "Journal saved!" message                                 │
│    ↓                                                           │
│ 4. RETURN TO HOME                                             │
│    • Show "✅ Checked in + Journaled" status                  │
└──────────────────────────────────────────────────────────────┘
```

#### API Integration
```dart
// Submit journal
POST /api/v1/engagement/journal
Body: {
  "profile_id": "user123",
  "journal_date": "2025-10-31",
  "energy_level": 4,
  "mood_rating": 5,
  "sleep_quality": 3,
  "stress_level": 2,
  "what_went_well": "Great workout in the morning, felt energized all day",
  "what_was_challenging": "Struggled with nutrition timing, skipped lunch",
  "habit_completions": {
    "breathing_exercises": true,
    "morning_sunlight": true,
    "mindfulness": false
  }
}

Response: {
  "success": true,
  "message": "Journal saved successfully",
  "journal_id": "journal-uuid"
}

// Get today's journal (to check if already submitted)
GET /api/v1/engagement/journal/{profile_id}

Response: {
  "journal_date": "2025-10-31",
  "energy_level": 4,
  "mood_rating": 5,
  // ... full journal data
  "created_at": "2025-10-31T18:45:00Z"
}
```

#### UI Components Needed
- `DailyJournalScreen.dart` - Main journal interface
  - Scrollable form
  - Date header
  - Section headers
  - Submit button
  - "Skip for now" option

- `EnergyLevelSlider.dart` - Custom slider with icons
  - 1-5 scale with labels
  - Battery/energy icons
  - Color gradient (red to green)

- `MoodRatingSlider.dart` - Emoji-based slider
  - 5 emoji faces (😢 😕 😐 🙂 😄)
  - Animated selection
  - Label below ("Very Bad" to "Very Good")

- `SleepQualitySlider.dart` - Moon icon slider
  - 1-5 scale with moon phases
  - Color coding

- `StressLevelSlider.dart` - Stress indicator
  - 1-5 scale
  - Wave/tension icons
  - Color gradient (green to red)

- `ReflectionTextField.dart` - Multiline text input
  - Expandable height
  - Character counter (optional)
  - Placeholder text

- `HabitToggle.dart` - Checkbox with label
  - Checkmark animation
  - Icon + label
  - Tap to toggle

#### Screen Files to Create
```
lib/presentation/screens/journal/
├── daily_journal_screen.dart
├── journal_success_screen.dart
├── journal_history_screen.dart (optional)
└── widgets/
    ├── energy_level_slider.dart
    ├── mood_rating_slider.dart
    ├── sleep_quality_slider.dart
    ├── stress_level_slider.dart
    ├── reflection_text_field.dart
    └── habit_toggle.dart
```

---

### **Flow 4: Plan Adaptation Visualization** ⭐ **P1 - SHOWS FRICTION-REDUCTION**

#### User Journey (After 3+ Days of Check-ins)
```
┌──────────────────────────────────────────────────────────────┐
│ 1. HOME SCREEN - INSIGHTS CARD APPEARS                        │
│    • Banner: "Your plan is adapting based on feedback"        │
│    • Tap banner to see details                                │
│    ↓                                                           │
│ 2. FRICTION INSIGHTS SCREEN                                   │
│    • "What you're excelling at:" (Low friction)               │
│      ✅ Movement - Using as anchor                            │
│      ✅ Hydration - Keep it up!                               │
│    • "What we're simplifying:" (High friction)                │
│      ⚠️  Nutrition - Reduced to micro-habits                  │
│      ⚠️  Stress Management - Simplified approach              │
│    • Visualization:                                           │
│      📊 Friction score chart by category                      │
│      📈 Completion rate trends                                │
│      📉 Satisfaction scores over time                         │
│    ↓                                                           │
│ 3. REGENERATE PLAN BUTTON                                     │
│    • "Generate Adapted Plan" (with friction insights)         │
│    • Plan regenerates with simplified high-friction tasks     │
│    ↓                                                           │
│ 4. NEW PLAN DISPLAYS                                          │
│    • High-friction tasks are now micro-habits:                │
│      OLD: "Track macros for 3 meals (30 min)"                │
│      NEW: "Take photo of 3 meals (5 min)"                     │
│    • Low-friction tasks used as anchors:                      │
│      "After your morning walk → Take one photo of breakfast"  │
│    • Insights badge: "🎯 Adapted for you"                     │
└──────────────────────────────────────────────────────────────┘
```

#### API Integration
```dart
// Get friction insights
GET /api/v1/engagement/engagement-context/{profile_id}

Response: {
  "feedback_count": 11,
  "friction_analysis": {
    "low_friction_categories": ["movement", "hydration"],
    "high_friction_categories": ["nutrition", "stress_management"],
    "detailed_analysis": {
      "nutrition": {
        "friction_score": 0.75,
        "completion_rate": 0.25,
        "enjoyment_rate": 0.20,
        "avg_satisfaction": 2.1,
        "strategy": "simplify_approach"
      },
      "movement": {
        "friction_score": 0.15,
        "completion_rate": 0.90,
        "enjoyment_rate": 0.95,
        "avg_satisfaction": 4.8,
        "strategy": "leverage_as_anchor"
      }
    }
  },
  "insights": [
    {
      "type": "friction_adaptation",
      "message": "We've simplified nutrition tasks to reduce friction - focus on micro-habits to build momentum",
      "priority": 10
    }
  ]
}

// Regenerate plan with friction awareness
POST /api/user/{user_id}/routine/generate
// Backend automatically applies friction-reduction based on check-in history
```

#### UI Components Needed
- `InsightsBanner.dart` - Home screen notification
  - Eye-catching design
  - Badge indicator
  - Tap to open full screen

- `FrictionInsightsScreen.dart` - Detailed friction breakdown
  - Section headers
  - Scrollable content
  - Regenerate plan CTA

- `FrictionCategoryCard.dart` - Low/Medium/High friction display
  - Category name + icon
  - Friction score visualization (bar chart)
  - Color coding (green/yellow/red)
  - Completion rate
  - Enjoyment rate
  - Satisfaction score

- `StrategyExplanation.dart` - Shows adaptation approach
  - Icon for strategy type
  - Description text
  - Example task

- `TaskComparisonCard.dart` - Before/After task simplification
  - Side-by-side or stacked layout
  - Strike-through for old task
  - Highlight for new task
  - Time savings indicator

- `FrictionScoreChart.dart` - Visual friction trends
  - Bar chart by category
  - Color-coded
  - Legend

#### Screen Files to Create
```
lib/presentation/screens/insights/
├── friction_insights_screen.dart
├── adaptation_explanation_screen.dart
└── widgets/
    ├── insights_banner.dart
    ├── friction_category_card.dart
    ├── strategy_explanation.dart
    ├── task_comparison_card.dart
    ├── friction_score_chart.dart
    └── completion_trend_chart.dart
```

---

### **Flow 5: Home Dashboard** ⭐ **P1 - CENTRAL HUB**

#### Home Screen Layout
```
┌──────────────────────────────────────────────────────────────┐
│ 📅 Thursday, October 31                                       │
│ ☀️  Good morning, [User Name]!                                │
│                                                                │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 📊 TODAY'S PROGRESS                                     │  │
│ │ ● 5 of 8 tasks completed                                │  │
│ │ ● ✅ Checked in + Journaled                             │  │
│ │ ● Next task: "Afternoon protein shake" (2:00 PM)       │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                                │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ ⚠️  FRICTION INSIGHTS (if available)                    │  │
│ │ "We simplified your nutrition tasks based on feedback"  │  │
│ │ [Tap to see details]                                    │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                                │
│ 📋 TODAY'S PLAN                                               │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 🌅 Morning Activation (6:00 AM - 8:00 AM)              │  │
│ │   ✅ Morning protein shake (6:30 AM)                    │  │
│ │   ✅ 30-min strength training (7:00 AM)                 │  │
│ │   ⬜ 10-min meditation (7:45 AM)                        │  │
│ └────────────────────────────────────────────────────────┘  │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ ☀️  Daytime Performance (8:00 AM - 5:00 PM)            │  │
│ │   ✅ Take photo of lunch (12:00 PM)                     │  │
│ │   ⬜ Afternoon protein shake (2:00 PM) ⏰ NEXT          │  │
│ │   ⬜ 15-min walk (3:00 PM)                              │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                                │
│ 🔔 REMINDERS                                                  │
│ ● Check in at 6 PM                                            │
│ ● Daily journal pending                                       │
│                                                                │
│ [Bottom Nav: Home | Health | Calendar | Planner | Profile]   │
└──────────────────────────────────────────────────────────────┘
```

#### API Integration
```dart
// Get completion summary
GET /api/v1/engagement/analytics/{profile_id}/completion-summary

Response: {
  "today": {
    "completed": 5,
    "total": 8,
    "completion_rate": 0.625
  },
  "week": {
    "completed": 28,
    "total": 56,
    "completion_rate": 0.50
  }
}

// Get check-in status
GET /api/v1/engagement/checkins/status/{profile_id}

Response: {
  "has_checked_in_today": true,
  "has_journaled_today": true,
  "completed_tasks": 5,
  "total_tasks": 8,
  "last_checkin_date": "2025-10-31"
}

// Get current plan
GET /api/v1/engagement/plans/{profile_id}/current

Response: {
  "analysis_id": "uuid",
  "plan_date": "2025-10-31",
  "time_blocks": [
    {
      "time_block": "Morning Activation",
      "start_time": "06:00",
      "end_time": "08:00",
      "tasks": [...]
    }
  ],
  "plan_items": [...]
}
```

#### UI Components Needed
- `HomeScreen.dart` - Main dashboard
  - Scrollable layout
  - Greeting header
  - Multiple card sections
  - Bottom navigation

- `ProgressSummaryCard.dart` - Daily stats
  - Circular progress indicator
  - Task count
  - Completion percentage
  - Check-in/journal status badges

- `FrictionInsightsBanner.dart` - Adaptation notification
  - Warning/info icon
  - Brief message
  - Tap action
  - Dismissible

- `TodaysPlanTimeline.dart` - Time block visualization
  - Grouped by time blocks
  - Task list with checkboxes
  - Next task highlight
  - Expandable/collapsible blocks

- `NextTaskCard.dart` - Upcoming task highlight
  - Large display
  - Time countdown
  - Task details
  - Quick complete button

- `RemindersCard.dart` - Upcoming actions
  - Icon list
  - Time display
  - Tap to navigate

#### Screen Files to Create
```
lib/presentation/screens/home/
├── home_screen.dart
└── widgets/
    ├── greeting_header.dart
    ├── progress_summary_card.dart
    ├── friction_insights_banner.dart
    ├── todays_plan_timeline.dart
    ├── time_block_section.dart
    ├── next_task_card.dart
    └── reminders_card.dart
```

---

## 🎨 Design System for hos_app

### Color Palette

```dart
class AppColors {
  // Primary
  static const Color primaryGreen = Color(0xFF4E8FE8); // Electric Blue (legacy name)

  // Backgrounds
  static const Color bg0 = Color(0xFF0D0D0D); // Darkest
  static const Color bg1 = Color(0xFF1A1A1A);
  static const Color bg2 = Color(0xFF252525);
  static const Color bg3 = Color(0xFF2F2F2F); // Lightest

  // Text
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xFFB0B0B0);
  static const Color textTertiary = Color(0xFF808080);

  // Accents
  static const Color success = Color(0xFF4CAF50); // Completed/Low friction
  static const Color warning = Color(0xFFFFA726); // Medium friction
  static const Color error = Color(0xFFE74C3C);   // High friction

  // Friction Indicators
  static const Color lowFriction = success;
  static const Color mediumFriction = warning;
  static const Color highFriction = error;

  // Category Colors
  static const Color nutrition = Color(0xFF4CAF50);
  static const Color movement = Color(0xFF2196F3);
  static const Color stress = Color(0xFF9C27B0);
  static const Color sleep = Color(0xFF3F51B5);
  static const Color hydration = Color(0xFF00BCD4);
  static const Color mindfulness = Color(0xFFFF9800);
}
```

### Typography (Material 3)

```dart
class AppTextStyles {
  static const TextStyle headlineLarge = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.w600, // SemiBold
    color: AppColors.textPrimary,
  );

  static const TextStyle titleMedium = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w600, // SemiBold
    color: AppColors.textPrimary,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w400, // Regular
    color: AppColors.textPrimary,
  );

  static const TextStyle labelMedium = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w600, // SemiBold
    color: AppColors.textPrimary,
  );

  static const TextStyle caption = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w400, // Regular
    color: AppColors.textSecondary,
  );

  static const TextStyle metricValue = TextStyle(
    fontSize: 40,
    fontWeight: FontWeight.w700, // Bold
    color: AppColors.textPrimary,
  );
}
```

### Spacing System (8pt grid)

```dart
class AppDimensions {
  // Spacing
  static const double spacingXS = 4.0;
  static const double spacingSM = 8.0;
  static const double spacingMD = 12.0;
  static const double spacingLG = 16.0; // ⭐ Most common
  static const double spacingXL = 24.0;
  static const double spacing2XL = 32.0;

  // Border Radius
  static const double radiusSM = 8.0;
  static const double radiusMD = 12.0;
  static const double radiusLG = 16.0;
  static const double radiusXL = 24.0;

  // Icon Sizes
  static const double iconXS = 16.0;
  static const double iconSM = 20.0;
  static const double iconMD = 24.0;
  static const double iconLG = 32.0;

  // Card Padding
  static const EdgeInsets cardPadding = EdgeInsets.all(spacingLG);
  static const EdgeInsets cardPaddingSmall = EdgeInsets.all(spacingMD);

  // Screen Padding
  static const EdgeInsets screenPadding = EdgeInsets.symmetric(
    horizontal: spacingLG,
    vertical: spacingXL,
  );
}
```

### Component Styles

```dart
class AppDecorations {
  static BoxDecoration card = BoxDecoration(
    color: AppColors.bg2,
    borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
    border: Border.all(
      color: AppColors.bg3,
      width: 1,
    ),
  );

  static BoxDecoration cardHighlighted = BoxDecoration(
    color: AppColors.bg2,
    borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
    border: Border.all(
      color: AppColors.primaryGreen,
      width: 2,
    ),
  );

  static BoxDecoration modal = BoxDecoration(
    color: AppColors.bg1,
    borderRadius: BorderRadius.vertical(
      top: Radius.circular(AppDimensions.radiusXL),
    ),
  );

  // Glassmorphism effect
  static BoxDecoration glassmorphism = BoxDecoration(
    color: AppColors.bg1.withOpacity(0.8),
    borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
    border: Border.all(
      color: AppColors.bg3.withOpacity(0.3),
      width: 1,
    ),
  );
}
```

---

## 📱 Implementation Priority

### **Week 1: Core Friction-Reduction Flow** (P0)

#### Day 1-2: Plan Generation UI
**Estimated Time**: 8-10 hours

**Tasks**:
1. Create `PlanGenerationModal`
   - 6 archetype selection cards
   - Preferences form (time pickers, goals)
   - Validation

2. Create `LoadingPlanScreen`
   - Animated progress indicator
   - Progress text updates
   - Handle 70-100 second wait

3. Create `PlanDisplay`
   - Time block headers
   - Task cards grouped by time
   - Category colors

4. Integrate with API
   - POST /api/user/{user_id}/routine/generate
   - Handle success/error states
   - Store plan locally

**Success Criteria**:
- ✅ User can select archetype and set preferences
- ✅ Loading state shows progress
- ✅ Generated plan displays correctly
- ✅ Plan persists in local storage

---

#### Day 3-4: Check-in Screen
**Estimated Time**: 10-12 hours

**Tasks**:
1. Create `CheckinScreen`
   - Fetch today's tasks
   - List view with task cards
   - Progress indicator

2. Create `TaskCheckinCard`
   - All feedback inputs
   - Validation
   - Expand/collapse

3. Create feedback widgets
   - EnjoymentToggle (Yes/No)
   - ContinuePreferenceChips (Yes/No/Maybe)
   - TimingFeedbackButtons (Perfect/Early/Late)
   - SatisfactionSlider (1-5 stars)

4. Integrate with API
   - GET /api/v1/engagement/tasks/{profile_id}
   - POST /api/v1/engagement/batch-checkin
   - Handle success/error states

**Success Criteria**:
- ✅ User can see today's tasks
- ✅ User can provide feedback for each task
- ✅ Batch submission works
- ✅ Success animation shows
- ✅ Navigates to journal screen

---

#### Day 4-5: Daily Journal
**Estimated Time**: 8-10 hours

**Tasks**:
1. Create `DailyJournalScreen`
   - Date header
   - All slider inputs
   - Text fields
   - Habit toggles

2. Create slider widgets
   - EnergyLevelSlider (with icons)
   - MoodRatingSlider (with emojis)
   - SleepQualitySlider (with moon icons)
   - StressLevelSlider (with icons)

3. Create reflection inputs
   - ReflectionTextField (multiline)
   - HabitToggle (with animation)

4. Integrate with API
   - POST /api/v1/engagement/journal
   - GET /api/v1/engagement/journal/{profile_id}
   - Handle success/error states

**Success Criteria**:
- ✅ User can input all journal fields
- ✅ Sliders work smoothly
- ✅ Text fields expand properly
- ✅ Journal submits successfully
- ✅ Returns to home screen

---

### **Week 2: Adaptation & Polish** (P1)

#### Day 1-2: Friction Insights
**Estimated Time**: 8-10 hours

**Tasks**:
1. Create `FrictionInsightsScreen`
   - Low friction section
   - High friction section
   - Friction score visualizations

2. Create insight widgets
   - FrictionCategoryCard
   - StrategyExplanation
   - TaskComparisonCard
   - FrictionScoreChart

3. Create `InsightsBanner`
   - Home screen integration
   - Tap to navigate
   - Dismissible

4. Integrate with API
   - GET /api/v1/engagement/engagement-context/{profile_id}
   - Display friction analysis
   - Show adaptation strategies

**Success Criteria**:
- ✅ Banner appears on home after 3+ check-ins
- ✅ Friction insights display correctly
- ✅ Charts show friction scores
- ✅ Task comparisons show simplification
- ✅ Regenerate plan applies friction insights

---

#### Day 3-4: Home Dashboard
**Estimated Time**: 10-12 hours

**Tasks**:
1. Create `HomeScreen`
   - Greeting header
   - Progress summary
   - Insights banner (conditional)
   - Today's plan timeline
   - Reminders card

2. Create dashboard widgets
   - ProgressSummaryCard
   - TodaysPlanTimeline
   - TimeBlockSection
   - NextTaskCard
   - RemindersCard

3. Integrate with APIs
   - GET /api/v1/engagement/analytics/{profile_id}/completion-summary
   - GET /api/v1/engagement/checkins/status/{profile_id}
   - GET /api/v1/engagement/plans/{profile_id}/current

4. Add navigation
   - Bottom navigation bar
   - Tab switching
   - Deep linking

**Success Criteria**:
- ✅ Home screen shows all relevant info
- ✅ Progress updates in real-time
- ✅ Today's plan displays correctly
- ✅ Next task is highlighted
- ✅ Navigation works smoothly

---

#### Day 5: Testing & Polish
**Estimated Time**: 6-8 hours

**Tasks**:
1. End-to-end testing
   - Full user journey
   - All API integrations
   - Error scenarios

2. UI/UX refinements
   - Animation polish
   - Loading states
   - Empty states
   - Error messages

3. Performance optimization
   - Lazy loading
   - Image optimization
   - State management

4. Accessibility
   - Semantic labels
   - Font scaling
   - Color contrast

**Success Criteria**:
- ✅ Complete flow works without errors
- ✅ All animations are smooth
- ✅ App feels responsive
- ✅ Accessible to all users

---

## 🔑 Key Integration Points (Backend ↔ Frontend)

| Backend API | Frontend Screen | Purpose | Priority |
|-------------|-----------------|---------|----------|
| `POST /api/user/{user_id}/routine/generate` | Plan Generation Modal | Create personalized plan | P0 |
| `GET /api/v1/engagement/tasks/{profile_id}` | Check-in Screen | Fetch today's tasks | P0 |
| `POST /api/v1/engagement/batch-checkin` | Check-in Screen | Submit feedback | P0 |
| `POST /api/v1/engagement/journal` | Daily Journal Screen | Submit reflection | P0 |
| `GET /api/v1/engagement/engagement-context/{profile_id}` | Friction Insights Screen | Show adaptation | P1 |
| `GET /api/v1/engagement/plans/{profile_id}/current` | Home Dashboard | Display current plan | P1 |
| `GET /api/v1/engagement/analytics/{profile_id}/completion-summary` | Home Dashboard | Show progress stats | P1 |
| `GET /api/v1/engagement/checkins/status/{profile_id}` | Home Dashboard | Check-in status | P1 |

---

## 📦 Required Flutter Packages

```yaml
dependencies:
  flutter:
    sdk: flutter

  # State Management
  flutter_bloc: ^8.1.0
  equatable: ^2.0.5

  # UI & Design
  google_fonts: ^6.1.0
  flutter_animate: ^4.3.0
  shimmer: ^3.0.0

  # Charts
  fl_chart: ^0.65.0

  # Networking
  dio: ^5.4.0
  retrofit: ^4.0.0

  # Storage
  shared_preferences: ^2.2.0
  flutter_secure_storage: ^9.0.0

  # Notifications
  flutter_local_notifications: ^16.0.0

  # Utilities
  intl: ^0.18.0
  uuid: ^4.0.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
  build_runner: ^2.4.0
  retrofit_generator: ^7.0.0
```

---

## ✅ Success Criteria

### User Experience
- ✅ User can generate a plan in < 2 minutes
- ✅ Check-in takes < 3 minutes to complete
- ✅ Daily journal takes < 2 minutes
- ✅ User sees friction insights after 3+ days
- ✅ Adapted plans are visibly simplified
- ✅ App feels fast and responsive
- ✅ Animations are smooth (60fps)

### Technical
- ✅ All API integrations working
- ✅ Offline mode caches data
- ✅ Error handling graceful
- ✅ Loading states informative
- ✅ State management clean (BLoC pattern)
- ✅ No memory leaks
- ✅ Battery efficient

### Friction-Reduction System
- ✅ Check-ins properly capture friction data
- ✅ High-friction tasks get simplified
- ✅ Low-friction tasks used as anchors
- ✅ Insights accurately reflect adaptation
- ✅ All health categories remain in plans
- ✅ Users understand the adaptation strategy

---

## 🚧 Out of Scope (Phase 2)

The following features are intentionally excluded from this MVP:

❌ **Backend Integration** (beyond APIs listed above)
- Real-time Sahha health data sync
- Advanced analytics processing
- Machine learning model training

❌ **Payment/Subscription System**
- In-app purchases
- Subscription management
- Premium features gating

❌ **Social Features**
- User communities
- Sharing plans
- Leaderboards

❌ **Advanced Customization**
- Custom task creation
- Advanced plan editing
- White-label configuration

❌ **Third-party Integrations**
- Wearable device sync (Garmin, Fitbit, etc.)
- Calendar integration
- Social media sharing

---

## 📝 Notes & Considerations

### Design Philosophy
1. **Friction-Reduction First**: Every UI decision should support the friction-reduction philosophy
2. **Simplicity Over Features**: Better to do less, extremely well
3. **Immediate Feedback**: Users should always know what's happening
4. **Behavioral Science**: Apply Atomic Habits principles in UI (make it obvious, easy, attractive, satisfying)

### Technical Considerations
1. **State Management**: Use BLoC pattern for consistency
2. **API Calls**: Use Dio with interceptors for auth/logging
3. **Local Storage**: Cache plan data for offline access
4. **Animations**: Use Flutter's built-in animation controllers
5. **Testing**: Write widget tests for all custom components

### User Experience Priorities
1. **Speed**: Minimize loading times wherever possible
2. **Clarity**: Always show what's happening (loading states)
3. **Recovery**: Handle errors gracefully with retry options
4. **Guidance**: Provide helpful tooltips for first-time users
5. **Delight**: Add subtle animations and transitions

---

## 🎯 Next Steps

1. **Review this document** with your team
2. **Set up Flutter project** with dependencies
3. **Implement design system** (colors, typography, spacing)
4. **Start with Week 1 tasks** (Plan Generation → Check-in → Journal)
5. **Test end-to-end** after each major component
6. **Iterate based on feedback**

---

**Your backend (Phase 5.0) is ready and waiting!** This guide gives you everything you need to build the Flutter UI that exposes your AI-powered, friction-reduction health planning system to users. 🚀

**Status**: ✅ Ready for Implementation
**Last Updated**: October 31, 2025
**Version**: 1.0
