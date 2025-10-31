# Aligned MVP Implementation Plan
**Based on Current Backend Implementation (Phase 5.0 Complete)**

## 🎯 Current Status: Backend 95% Complete

### ✅ What You Already Have (Working)

#### **Database Layer** ✅ COMPLETE
- ✅ `task_checkins` table with:
  - `profile_id`, `plan_item_id`, `analysis_result_id`
  - `completion_status` (completed/partial/skipped)
  - `satisfaction_rating` (1-5)
  - `continue_preference` (yes/no/maybe)
  - `enjoyed` (boolean)
  - `timing_feedback` (perfect/early/late)
  - `planned_date`
- ✅ `plan_items` table with:
  - `id`, `profile_id`, `analysis_result_id`
  - `title`, `category`, `task_type`
  - `scheduled_time`, `plan_date`
  - `completed_at`, `source`
- ✅ `daily_journals` table (for holistic reflection)
- ✅ `holistic_analysis_results` (stores generated plans)
- ✅ `time_blocks` (circadian-based time blocks)

#### **Backend APIs** ✅ 95% COMPLETE

**Plan Generation** ✅
- `POST /api/user/{user_id}/routine/generate`
  - Accepts: `archetype`, `preferences`, `timezone`
  - Returns: Generated plan with `analysis_id`
  - ✅ Integrates TaskPreseeder with friction analysis
  - ✅ Integrates preferences (wake/sleep/workout/goals)
  - ✅ Uses Atomic Habits principles

**Check-in System** ✅
- `POST /api/v1/engagement/task-checkin` ✅
  - Saves individual task check-ins
- `GET /api/v1/engagement/tasks/{profile_id}` ✅
  - Fetches plan items for user
- `POST /api/v1/engagement/batch-checkin` ✅
  - Batch submit multiple check-ins
- `GET /api/v1/engagement/checkins/status/{profile_id}` ✅
  - Get check-in status for today

**Daily Journal** ✅
- `POST /api/v1/engagement/journal` ✅
  - Submit daily reflection (energy, mood, sleep, stress, notes)
- `GET /api/v1/engagement/journal/{profile_id}` ✅
  - Get today's journal
- `GET /api/v1/engagement/journal/{profile_id}/history` ✅
  - Get journal history

**Plan Retrieval** ✅
- `GET /api/v1/engagement/plans/{profile_id}/current` ✅
  - Get current active plan with items
- `GET /api/user/{user_id}/plans/{date}` ✅
  - Get plan for specific date

**Analytics** ✅
- `GET /api/v1/engagement/analytics/{profile_id}/completion-summary` ✅
  - Get completion statistics
- `GET /api/v1/engagement/engagement-context/{profile_id}` ✅
  - Get complete engagement context

**Backend Services** ✅
- ✅ `FeedbackService` - Friction analysis from check-ins
- ✅ `TaskPreseeder` - Selects tasks with friction + preference scoring
- ✅ `PlanExtractionService` - Saves plans to database
- ✅ `InsightsService` - Generates friction-based insights

---

## 🔧 Backend Gaps (5% - Nice to Have)

### **Gap 1: Manual Generation Endpoint** ⚠️ OPTIONAL
**Current**: Auto-generation via `POST /api/user/{user_id}/routine/generate`
**MVP Wants**: Explicit manual trigger endpoint

**Solution**: The existing endpoint already works - just document it as the manual trigger.
**Action**: ❌ No code changes needed - existing endpoint is sufficient

---

### **Gap 2: Regenerate from Chat Modifications** ⚠️ OPTIONAL
**Current**: `POST /api/user/{user_id}/routine/regenerate-from-markdown`
**Status**: ✅ Already exists for HolisticAI chat modifications

**Action**: ❌ No changes needed - already working

---

### **Gap 3: Get Completed Tasks for Check-in** ⚠️ OPTIONAL
**MVP Wants**: `GET /api/v1/tasks/completed-today?user_id={uuid}`
**Current**: Can use `GET /api/v1/engagement/tasks/{profile_id}` and filter client-side

**Solution**: Add dedicated endpoint if Flutter needs it
**Priority**: P2 (can filter client-side for now)

**Endpoint to Add** (if needed):
```python
@router.get("/tasks/{profile_id}/completed-today")
async def get_completed_tasks_today(profile_id: str):
    """Get today's completed tasks for check-in screen"""
    # Query plan_items where completed_at IS NOT NULL and plan_date = today
    # Return with timing info
```

**Estimated Time**: 1 hour

---

## 🎨 Frontend Implementation Plan

### **Phase 1: Check-in Screen** (P1 - Critical for MVP)
**Estimated Time**: 6-8 hours

**File**: `hos_coach/lib/presentation/screens/checkin/checkin_screen.dart`

**Tasks**:
1. Create CheckinScreen widget
2. Fetch tasks via `GET /api/v1/engagement/tasks/{profile_id}`
3. Build UI:
   - Task list with completion checkboxes
   - For each task:
     - "Did you enjoy this?" (Yes/No buttons)
     - "Continue tomorrow?" (Yes/No/Maybe chips)
     - "How was timing?" (Perfect/Early/Late buttons)
     - Satisfaction slider (1-5)
4. Submit via `POST /api/v1/engagement/task-checkin` (or batch endpoint)
5. Success animation
6. Navigate to journal screen

**API Integration**:
```dart
// Fetch tasks
GET /api/v1/engagement/tasks/{profile_id}

// Submit check-ins (batch)
POST /api/v1/engagement/batch-checkin
{
  "checkins": [
    {
      "profile_id": "uuid",
      "plan_item_id": "uuid",
      "completion_status": "completed",
      "satisfaction_rating": 5,
      "continue_preference": "yes",
      "enjoyed": true,
      "timing_feedback": "perfect"
    }
  ]
}
```

**Navigation**:
- Accessible from Home screen ("Check in" button)
- Accessible from notification tap
- After submission → Navigate to Daily Journal

---

### **Phase 2: Daily Journal Screen** (P1)
**Estimated Time**: 4-5 hours

**File**: `hos_coach/lib/presentation/screens/journal/daily_journal_screen.dart`

**Tasks**:
1. Create DailyJournalScreen widget
2. Build UI:
   - Energy level slider (1-5)
   - Mood rating slider (1-5)
   - Sleep quality slider (1-5)
   - Stress level slider (1-5)
   - "What went well?" text field
   - "What was challenging?" text field
   - Habit completion toggles (breathing, sunlight, mindfulness)
3. Submit via `POST /api/v1/engagement/journal`
4. Show success message
5. Navigate to Home

**API Integration**:
```dart
POST /api/v1/engagement/journal
{
  "profile_id": "uuid",
  "journal_date": "2025-10-31",
  "energy_level": 4,
  "mood_rating": 5,
  "sleep_quality": 3,
  "stress_level": 2,
  "what_went_well": "Great workout in the morning",
  "what_was_challenging": "Struggled with nutrition timing"
}
```

---

### **Phase 3: Planner Screen Modifications** (P1)
**Estimated Time**: 3-4 hours

**File**: `hos_coach/lib/presentation/screens/planner/coach_program_dashboard.dart`

**Tasks**:
1. Add "Check-in" button at top (shows if tasks completed but no check-in)
2. Add check-in reminder banner at 6 PM
3. Show completion status for each task
4. Tap task → Mark complete → Optimistic UI update
5. Update task via `POST /api/v1/engagement/task-checkin` (background)
6. Show timing feedback ("Perfect timing!", "Completed early!")

**API Calls**:
```dart
// Get current plan
GET /api/v1/engagement/plans/{profile_id}/current

// Mark task complete
POST /api/v1/engagement/task-checkin
{
  "profile_id": "uuid",
  "plan_item_id": "uuid",
  "completion_status": "completed",
  "planned_date": "2025-10-31"
}

// Check if check-in done today
GET /api/v1/engagement/checkins/status/{profile_id}
```

**Conditional Button Logic**:
```dart
// Show "Check-in" button if:
// - Has completed tasks today
// - No check-in submitted yet
// - Time is after 6 PM or user manually wants to check in
```

---

### **Phase 4: Home Screen Modifications** (P2)
**Estimated Time**: 2-3 hours

**File**: `hos_coach/lib/presentation/screens/home/home_screen.dart`

**Tasks**:
1. Add Daily Summary Card:
   - Show tasks completed today (e.g., "5 of 8 tasks completed")
   - Show check-in status ("✅ Checked in" or "⏳ Check in pending")
2. Add Check-in Reminder Card (if time >= 6 PM and no check-in):
   - Message: "Time to check in on your day!"
   - Button: "Check in now" → Navigate to CheckinScreen
3. Show today's journal status

**API Calls**:
```dart
// Get completion summary
GET /api/v1/engagement/analytics/{profile_id}/completion-summary

// Get check-in status
GET /api/v1/engagement/checkins/status/{profile_id}

// Get journal status
GET /api/v1/engagement/journal/{profile_id}
```

---

### **Phase 5: Notification System** (P2 - Optional)
**Estimated Time**: 4-5 hours

**Tasks**:
1. Set up Firebase Cloud Messaging (if not already)
2. Create `NotificationService` class
3. Schedule daily 6 PM notification:
   - Title: "Time to check in!"
   - Body: "Reflect on your day before tomorrow's plan"
   - Deep link: Opens CheckinScreen
4. Handle notification tap → Navigate to CheckinScreen
5. Test notification delivery

**Implementation**:
```dart
// NotificationService
class NotificationService {
  // Schedule daily 6 PM notification
  void scheduleDailyCheckinReminder() {
    // Use flutter_local_notifications or Firebase
    // Schedule for 6 PM daily
  }

  // Handle notification tap
  void handleNotificationTap(String payload) {
    // Navigate to CheckinScreen
  }
}
```

---

### **Phase 6: Services Layer** (P1)
**Estimated Time**: 3-4 hours

**Files**:
- `lib/services/checkin_service.dart`
- `lib/services/journal_service.dart`
- `lib/services/plan_service.dart`

**Tasks**:
1. Create CheckinService class:
   - `submitTaskCheckin(checkinData)`
   - `submitBatchCheckins(List<checkinData>)`
   - `getCheckinStatus(profileId, date)`
   - `getTodaysTasks(profileId)`
2. Create JournalService class:
   - `submitJournal(journalData)`
   - `getTodayJournal(profileId)`
   - `getJournalHistory(profileId, days)`
3. Create PlanService class:
   - `getCurrentPlan(profileId)`
   - `getPlanForDate(profileId, date)`
4. Add local caching (SharedPreferences) for offline support
5. Add retry logic for failed API calls

---

## 📊 Dependency Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Complete ✅)                     │
├─────────────────────────────────────────────────────────────┤
│ • Task Check-in API ✅                                       │
│ • Daily Journal API ✅                                       │
│ • Plan Generation API ✅                                     │
│ • Analytics API ✅                                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND SERVICES (P1)                      │
├─────────────────────────────────────────────────────────────┤
│ Phase 6: CheckinService, JournalService, PlanService        │
│ Estimated: 3-4 hours                                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND UI (P1)                          │
├─────────────────────────────────────────────────────────────┤
│ Phase 1: Check-in Screen (6-8 hours)                        │
│ Phase 2: Daily Journal Screen (4-5 hours)                   │
│ Phase 3: Planner Screen Mods (3-4 hours)                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                FRONTEND ENHANCEMENTS (P2)                    │
├─────────────────────────────────────────────────────────────┤
│ Phase 4: Home Screen Mods (2-3 hours)                       │
│ Phase 5: Notifications (4-5 hours)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Recommended Implementation Order

### **Week 1: Frontend Services + Core UI** (P1)
**Total: 16-21 hours**

**Day 1-2**: Services Layer (3-4 hours)
- Create CheckinService, JournalService, PlanService
- Test API integration
- Add error handling and caching

**Day 3-4**: Check-in Screen (6-8 hours)
- Build task check-in UI
- Integrate with CheckinService
- Add validation and success animations

**Day 4-5**: Daily Journal Screen (4-5 hours)
- Build journal UI
- Integrate with JournalService
- Test submission flow

**Day 5**: Planner Screen Mods (3-4 hours)
- Add check-in button
- Update task completion flow
- Test end-to-end

---

### **Week 2: Enhancements + Testing** (P2)
**Total: 12-18 hours**

**Day 1**: Home Screen Mods (2-3 hours)
- Add summary cards
- Add check-in reminder
- Test navigation

**Day 2-3**: Notifications (4-5 hours)
- Set up Firebase
- Schedule 6 PM reminders
- Test deep linking

**Day 4-5**: Integration Testing (6-10 hours)
- End-to-end user journey
- Test offline mode
- Bug fixes
- Polish UI/UX

---

## ✅ Success Criteria

### **Week 1 Complete**
- ✅ User can check in on tasks via mobile app
- ✅ User can submit daily journal
- ✅ Planner screen shows completion status
- ✅ Check-in data saves to backend
- ✅ Services layer handles errors gracefully

### **Week 2 Complete (Production Ready)**
- ✅ Home screen shows daily summary
- ✅ 6 PM notification triggers daily
- ✅ Deep link opens correct screen
- ✅ Complete user journey works (onboarding → tasks → check-in → journal → next day)
- ✅ Offline mode caches data
- ✅ No critical bugs

---

## 🎯 What You DON'T Need to Build

❌ **Backend APIs** - Already complete
❌ **Database schema** - Already working
❌ **TaskPreseeder** - Already has friction + preferences
❌ **FeedbackService** - Already analyzes check-ins
❌ **Plan generation** - Already working with preferences
❌ **Insights generation** - Already working

---

## 📝 API Quick Reference for Flutter

### **Get Current Plan**
```
GET /api/v1/engagement/plans/{profile_id}/current
Response: { plan_items: [...], time_blocks: [...] }
```

### **Submit Task Check-in**
```
POST /api/v1/engagement/task-checkin
Body: { profile_id, plan_item_id, completion_status, satisfaction_rating, continue_preference, enjoyed, timing_feedback }
```

### **Submit Batch Check-ins**
```
POST /api/v1/engagement/batch-checkin
Body: { checkins: [{ profile_id, plan_item_id, ... }] }
```

### **Submit Daily Journal**
```
POST /api/v1/engagement/journal
Body: { profile_id, journal_date, energy_level, mood_rating, what_went_well, ... }
```

### **Get Check-in Status**
```
GET /api/v1/engagement/checkins/status/{profile_id}
Response: { has_checked_in_today: true/false, completed_tasks: 5, total_tasks: 8 }
```

### **Get Completion Summary**
```
GET /api/v1/engagement/analytics/{profile_id}/completion-summary
Response: { today: { completed: 5, total: 8 }, week: { ... } }
```

### **Generate New Plan**
```
POST /api/user/{user_id}/routine/generate
Body: { archetype, preferences: { wake_time, sleep_time, workout_time, goals }, timezone }
Response: { analysis_id, routine_plan, ... }
```

---

## 🎉 Summary

**Backend Status**: ✅ 95% Complete (excellent work!)

**Frontend Status**: ❌ 0% Complete (needs implementation)

**Next Steps**:
1. Start with **Phase 6** (Services Layer) - 3-4 hours
2. Then **Phase 1** (Check-in Screen) - 6-8 hours
3. Then **Phase 2** (Daily Journal) - 4-5 hours
4. Then **Phase 3** (Planner Mods) - 3-4 hours

**Total MVP Time**: 16-21 hours for P1 features

**Your backend is solid** - all the heavy lifting (friction analysis, preferences, Atomic Habits, plan generation) is done. Now it's just about building the Flutter UI to expose this functionality to users! 🚀
