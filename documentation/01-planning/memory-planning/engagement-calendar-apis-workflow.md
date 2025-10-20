# Engagement and Calendar APIs Workflow Guide

## Overview

This document explains how the engagement and calendar APIs work, what inputs they need, and how data flows through the system for AI context generation.

## 📅 Calendar APIs Flow

### 1. Calendar Selection Process
```
User Plan Generated → User Selects Items → Calendar API Stores Selections
```

**API: `POST /api/calendar/select`**
- **Input needed**:
  ```json
  {
    "profile_id": "user123",
    "selected_plan_items": ["plan_item_id_1", "plan_item_id_2", "plan_item_id_3"],
    "date": "2024-01-15",
    "selection_notes": "Adding my top priorities for tomorrow"
  }
  ```
- **What it does**: Takes plan item IDs that user wants to add to their calendar
- **Database effect**: Creates records in `calendar_selections` table
- **Validation**: Ensures all plan items belong to same user and analysis

### 2. Calendar Retrieval
**API: `GET /api/calendar/selections/{profile_id}`**
- **Input**: Just the profile_id in URL
- **Output**: List of items user selected for calendar
- **Use case**: Show user what they've added to calendar

## ✅ Engagement APIs Flow

### 1. Task Check-ins (Individual completions)
```
User Completes Task → Check-in API → Records Completion Status
```

**API: `POST /api/v1/engagement/task-checkin`**
- **Input needed**:
  ```json
  {
    "profile_id": "user123",
    "plan_item_id": "plan_item_uuid_here",
    "completion_status": "completed",  // or "partial", "skipped"
    "satisfaction_rating": 4,          // 1-5 scale
    "planned_date": "2024-01-15",
    "user_notes": "Felt energized after this task"
  }
  ```
- **What it does**: Records individual task completion with feedback
- **Database effect**: Creates record in `task_checkins` table

### 2. Daily Journal (Holistic reflection)
```
End of Day → User Reflects → Journal API → Stores Daily Summary
```

**API: `POST /api/v1/engagement/journal`**
- **Input needed**:
  ```json
  {
    "profile_id": "user123",
    "journal_date": "2024-01-15",
    "energy_level": 4,           // 1-5 scale
    "mood_rating": 4,            // 1-5 scale
    "sleep_quality": 3,          // 1-5 scale
    "stress_level": 2,           // 1-5 scale
    "what_went_well": "Morning routine was smooth",
    "what_was_challenging": "Afternoon energy dip",
    "tomorrow_intentions": "Try 10min walk after lunch"
  }
  ```
- **What it does**: Captures daily wellbeing and reflection
- **Database effect**: Creates record in `daily_journals` table

## 📊 Data Retrieval (For AI Context)

### Get Engagement Context
**API: `GET /api/v1/engagement/engagement-context/{profile_id}?days=30`**
- **Input**: profile_id and number of days to analyze
- **Output**: Raw engagement data ready for AI analysis
- **What it returns**:
  ```json
  {
    "engagement_summary": {
      "total_planned": 25,
      "completed": 18,
      "completion_rate": 0.72
    },
    "recent_tasks": [
      {
        "title": "Morning HRV Check",
        "status": "completed",
        "satisfaction": 4,
        "time_block": "morning"
      }
    ],
    "timing_patterns": {
      "morning_completion_rate": 0.85,
      "afternoon_completion_rate": 0.60
    }
  }
  ```

## 🔄 How Data Flows Through System

### Step 1: Plan Generation
```
AI Analysis → Generates Plan → Extracts to plan_items table
```

### Step 2: User Calendar Selection
```
plan_items → User sees options → Selects subset → calendar_selections table
```

### Step 3: User Engagement
```
Selected items → User completes tasks → task_checkins table
Daily reflection → Daily journal → daily_journals table
```

### Step 4: AI Context Generation
```
calendar_selections + task_checkins + daily_journals → Raw data → AI analysis → Context
```

## 💡 Key Dependencies

### Calendar APIs need:
- `plan_items` table populated (from plan extraction)
- Valid `profile_id`
- Valid `plan_item_id`s from existing plans

### Engagement APIs need:
- `calendar_selections` or `plan_items` table (for valid plan_item_ids)
- Valid `profile_id`
- Realistic dates and ratings

### AI Context APIs need:
- Historical data in `calendar_selections`, `task_checkins`, `daily_journals`
- Enough data points (at least a few days worth)

## 🚀 Normal Application Flow

1. **Plan Creation**: AI generates routine → plan_items table populated
2. **Calendar Selection**: User picks items → calendar_selections table populated
3. **Daily Usage**: User completes tasks → task_checkins table populated
4. **Daily Reflection**: User journals → daily_journals table populated
5. **Context Generation**: AI reads all tables → creates personalized context

## 📋 Database Tables Involved

### plan_items
- **Source**: Plan extraction from analysis results
- **Contains**: Individual tasks/activities from routine plans
- **Key fields**: id, profile_id, analysis_result_id, title, task_type, scheduled_time

### calendar_selections
- **Source**: User calendar selection API
- **Contains**: Which plan items user chose to add to calendar
- **Key fields**: profile_id, plan_item_id, selection_timestamp, calendar_notes

### task_checkins
- **Source**: User task check-in API
- **Contains**: Individual task completion records
- **Key fields**: profile_id, plan_item_id, completion_status, satisfaction_rating, user_notes

### daily_journals
- **Source**: User daily journal API
- **Contains**: Daily holistic reflection and wellbeing data
- **Key fields**: profile_id, journal_date, energy_level, mood_rating, what_went_well

## 🎯 For AI Context Generation

### Raw Data Sources
1. **Calendar Selections**: What user planned to do
2. **Task Check-ins**: What user actually did and how they felt
3. **Daily Journals**: Overall patterns and qualitative insights

### AI Analysis Process
1. **Load raw data** from all three sources
2. **Let AI analyze patterns** (completion rates, timing preferences, satisfaction trends)
3. **Generate context summary** with actionable insights
4. **Store context** for future analysis enhancement

## 🔧 Integration Points

### With Plan Generation
- Plan extraction populates `plan_items` table
- These items become available for calendar selection

### With Calendar Workflow
- Users select subset of plan items for calendar
- Creates foundation for engagement tracking

### With Daily Engagement
- Users check in on tasks throughout day
- Daily journal captures holistic experience

### With AI Context Service
- Raw engagement data feeds into context generation
- Context enhances future plan personalization

## 📝 Key Design Principles

1. **User-Centric**: APIs follow natural user workflow
2. **Granular + Holistic**: Both task-level and day-level tracking
3. **Privacy-Safe**: Context APIs expose no system IDs
4. **AI-Ready**: Raw data structured for AI analysis
5. **Iterative**: Each analysis builds on previous engagement data

The APIs are designed to capture real user behavior and preferences, providing rich data for AI-powered personalization of health recommendations.