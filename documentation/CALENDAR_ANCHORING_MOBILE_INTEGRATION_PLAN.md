# 📋 Calendar Anchoring Integration - Mobile App Implementation Plan

## Executive Summary

**Goal**: Integrate the calendar anchoring system from `hos-agentic-ai-prod` into the HolisticOS Flutter app, allowing users to intelligently anchor their daily plan tasks to real Google Calendar events.

**Key Requirements**:
✅ Pull events from user's Google Calendar
✅ Anchor plan tasks to available calendar gaps
✅ If no gaps, allocate as originally scheduled
✅ Store anchored tasks in app (NOT save to Google Calendar)
✅ Add button alongside "Daily Check-in" button

**Architecture Overview**:
```
Flutter App (HolisticOS-app)
    ↓ (1) Trigger Anchoring
Backend API (hos-agentic-ai-prod:8002)
    ↓ (2) Fetch Google Calendar via well-planned-api
    ↓ (3) Run Anchoring Algorithm (Gemini/OpenAI)
    ↓ (4) Return Anchored Plan
Flutter App
    ↓ (5) Display Anchored Tasks (in-app only)
```

---

## Phase 1: Backend API Extension (hos-agentic-ai-prod)

**Duration**: 2-3 days
**Priority**: HIGH (Foundation for all other phases)

### 1.1 Create Anchoring API Endpoint

**File**: `/Users/kothagattu/Desktop/OG/hos-agentic-ai-prod/services/api_gateway/openai_main.py`

**New Endpoint**:
```python
@app.post("/api/user/{user_id}/plan/anchor")
async def anchor_plan_to_calendar(
    user_id: str,
    request: AnchorPlanRequest,
    supabase_token: Optional[str] = Header(None, alias="Authorization")
):
    """
    Anchor user's plan tasks to Google Calendar events

    Request Body:
    {
        "analysis_result_id": "uuid",  # Plan to anchor
        "target_date": "2025-11-07",   # Date to anchor
        "use_ai_scoring": false,       # Speed vs quality trade-off
        "google_calendar_token": "ya29...." # Google OAuth token from app
    }

    Response:
    {
        "success": true,
        "anchored_tasks": [...],       # Tasks with new times
        "tasks_rescheduled": 5,
        "tasks_kept_original": 3,
        "average_confidence": 0.82,
        "calendar_events_found": 4,
        "gaps_available": 6
    }
    """
    # 1. Validate request
    # 2. Fetch plan items from database
    # 3. Fetch Google Calendar events via well-planned-api
    # 4. Run anchoring coordinator
    # 5. Return anchored plan (DO NOT save to database)
```

**Implementation Steps**:

1. **Create Request/Response Models** (`shared_libs/data_models/anchoring_models.py`)
   ```python
   from pydantic import BaseModel
   from datetime import date, time
   from typing import List, Optional

   class AnchorPlanRequest(BaseModel):
       analysis_result_id: str
       target_date: date
       use_ai_scoring: bool = False
       google_calendar_token: Optional[str] = None

   class AnchoredTask(BaseModel):
       task_id: str
       title: str
       original_time: time
       anchored_time: time
       duration_minutes: int
       was_rescheduled: bool
       confidence_score: float
       anchoring_reason: str

   class AnchorPlanResponse(BaseModel):
       success: bool
       anchored_tasks: List[AnchoredTask]
       tasks_rescheduled: int
       tasks_kept_original: int
       average_confidence: float
       calendar_events_found: int
       gaps_available: int
       error_message: Optional[str] = None
   ```

2. **Modify Calendar Integration Service** (`services/anchoring/calendar_integration_service.py`)

   Add new method to fetch from Google Calendar using token:
   ```python
   async def fetch_google_calendar_with_token(
       self,
       user_id: str,
       target_date: date,
       google_token: str
   ) -> CalendarFetchResult:
       """
       Fetch Google Calendar events using user's OAuth token

       Calls well-planned-api with token forwarding
       """
       # Pass token to well-planned-api
       # Return CalendarFetchResult
   ```

3. **Create Anchoring Endpoint Handler**

   Add to `openai_main.py`:
   ```python
   from services.anchoring import get_anchoring_coordinator, get_task_loader_service

   @app.post("/api/user/{user_id}/plan/anchor", response_model=AnchorPlanResponse)
   async def anchor_plan_to_calendar(
       user_id: str,
       request: AnchorPlanRequest,
       supabase_token: Optional[str] = Header(None, alias="Authorization")
   ):
       try:
           # Load plan tasks
           task_loader = get_task_loader_service()
           tasks = await task_loader.load_plan_items_to_anchor(
               analysis_result_id=request.analysis_result_id,
               plan_date=request.target_date,
               include_already_anchored=False
           )

           # Run anchoring
           coordinator = get_anchoring_coordinator(use_ai_scoring=request.use_ai_scoring)
           result = await coordinator.anchor_tasks(
               user_id=user_id,
               tasks=tasks,
               target_date=request.target_date,
               supabase_token=supabase_token,
               use_mock_calendar=not request.google_calendar_token,
               min_gap_minutes=15
           )

           # Format response
           anchored_tasks = [
               AnchoredTask(
                   task_id=assignment.task_id,
                   title=assignment.task_title,
                   original_time=assignment.original_time,
                   anchored_time=assignment.anchored_time,
                   duration_minutes=assignment.duration_minutes,
                   was_rescheduled=assignment.time_adjustment_minutes != 0,
                   confidence_score=assignment.confidence_score,
                   anchoring_reason=assignment.scoring_breakdown.get("reasoning", "")
               )
               for assignment in result.assignments
           ]

           return AnchorPlanResponse(
               success=True,
               anchored_tasks=anchored_tasks,
               tasks_rescheduled=result.tasks_rescheduled,
               tasks_kept_original=result.tasks_kept_original,
               average_confidence=result.average_confidence,
               calendar_events_found=len(result.calendar_events) if hasattr(result, 'calendar_events') else 0,
               gaps_available=len(result.available_gaps) if hasattr(result, 'available_gaps') else 0
           )
       except Exception as e:
           logger.error(f"Anchoring failed: {str(e)}")
           return AnchorPlanResponse(
               success=False,
               anchored_tasks=[],
               tasks_rescheduled=0,
               tasks_kept_original=0,
               average_confidence=0.0,
               calendar_events_found=0,
               gaps_available=0,
               error_message=str(e)
           )
   ```

### 1.2 Testing

**Create Test Script**: `testing/test_anchoring_api.py`
```python
import requests
import json

def test_anchor_plan_api():
    url = "http://localhost:8002/api/user/a57f70b4-d0a4-4aef-b721-a4b526f64869/plan/anchor"

    payload = {
        "analysis_result_id": "d8fe057d-fe02-4547-b7f2-f4884e424544",
        "target_date": "2025-11-07",
        "use_ai_scoring": False,
        "google_calendar_token": None  # Use mock calendar
    }

    response = requests.post(url, json=payload)
    print(json.dumps(response.json(), indent=2))

    assert response.status_code == 200
    assert response.json()["success"] == True
    print("✅ Anchoring API test passed!")

if __name__ == "__main__":
    test_anchor_plan_api()
```

**Deliverables**:
- ✅ `/api/user/{user_id}/plan/anchor` endpoint working
- ✅ Returns anchored tasks with times
- ✅ Works with mock calendar (no Google token)
- ✅ Validated with test script

---

## Phase 2: Flutter App - Data Layer

**Duration**: 2 days
**Priority**: HIGH

### 2.1 Update Data Models

**File**: `/Users/kothagattu/Desktop/OG/HolisticOS-app/lib/core/models/planner_models.dart`

**Add Anchoring Fields to PlanTask**:
```dart
class PlanTask {
  // Existing fields...
  final String id;
  final String name;
  final String time;

  // NEW: Anchoring fields
  final bool isAnchored;
  final DateTime? anchoredAt;
  final String? anchoredTime; // New display time after anchoring
  final String? anchoredStartTime; // 24h format
  final String? anchoredEndTime;
  final double? anchoringConfidence; // 0.0-1.0
  final String? anchoringReason;
  final bool wasRescheduled;

  PlanTask({
    // Existing parameters...
    this.isAnchored = false,
    this.anchoredAt,
    this.anchoredTime,
    this.anchoredStartTime,
    this.anchoredEndTime,
    this.anchoringConfidence,
    this.anchoringReason,
    this.wasRescheduled = false,
  });

  // Update copyWith method
  PlanTask copyWith({
    // Existing parameters...
    bool? isAnchored,
    DateTime? anchoredAt,
    String? anchoredTime,
    String? anchoredStartTime,
    String? anchoredEndTime,
    double? anchoringConfidence,
    String? anchoringReason,
    bool? wasRescheduled,
  }) {
    return PlanTask(
      // Copy all fields...
      isAnchored: isAnchored ?? this.isAnchored,
      anchoredAt: anchoredAt ?? this.anchoredAt,
      anchoredTime: anchoredTime ?? this.anchoredTime,
      anchoredStartTime: anchoredStartTime ?? this.anchoredStartTime,
      anchoredEndTime: anchoredEndTime ?? this.anchoredEndTime,
      anchoringConfidence: anchoringConfidence ?? this.anchoringConfidence,
      anchoringReason: anchoringReason ?? this.anchoringReason,
      wasRescheduled: wasRescheduled ?? this.wasRescheduled,
    );
  }

  // Helper method to get display time (anchored if available, else original)
  String get displayTime => anchoredTime ?? time;
  String? get displayStartTime => anchoredStartTime ?? startTime;
  String? get displayEndTime => anchoredEndTime ?? endTime;
}
```

### 2.2 Create Anchoring Service

**File**: `/Users/kothagattu/Desktop/OG/HolisticOS-app/lib/core/services/calendar_anchoring_service.dart`

```dart
import 'package:dio/dio.dart';
import 'package:holisticos/config/app_config.dart';
import 'package:holisticos/core/models/planner_models.dart';

class AnchoringRequest {
  final String analysisResultId;
  final DateTime targetDate;
  final bool useAiScoring;
  final String? googleCalendarToken;

  AnchoringRequest({
    required this.analysisResultId,
    required this.targetDate,
    this.useAiScoring = false,
    this.googleCalendarToken,
  });

  Map<String, dynamic> toJson() => {
    'analysis_result_id': analysisResultId,
    'target_date': targetDate.toIso8601String().split('T')[0],
    'use_ai_scoring': useAiScoring,
    'google_calendar_token': googleCalendarToken,
  };
}

class AnchoringResponse {
  final bool success;
  final List<AnchoredTaskData> anchoredTasks;
  final int tasksRescheduled;
  final int tasksKeptOriginal;
  final double averageConfidence;
  final int calendarEventsFound;
  final int gapsAvailable;
  final String? errorMessage;

  AnchoringResponse({
    required this.success,
    required this.anchoredTasks,
    required this.tasksRescheduled,
    required this.tasksKeptOriginal,
    required this.averageConfidence,
    required this.calendarEventsFound,
    required this.gapsAvailable,
    this.errorMessage,
  });

  factory AnchoringResponse.fromJson(Map<String, dynamic> json) {
    return AnchoringResponse(
      success: json['success'] ?? false,
      anchoredTasks: (json['anchored_tasks'] as List?)
          ?.map((task) => AnchoredTaskData.fromJson(task))
          .toList() ?? [],
      tasksRescheduled: json['tasks_rescheduled'] ?? 0,
      tasksKeptOriginal: json['tasks_kept_original'] ?? 0,
      averageConfidence: (json['average_confidence'] ?? 0.0).toDouble(),
      calendarEventsFound: json['calendar_events_found'] ?? 0,
      gapsAvailable: json['gaps_available'] ?? 0,
      errorMessage: json['error_message'],
    );
  }
}

class AnchoredTaskData {
  final String taskId;
  final String title;
  final String originalTime;
  final String anchoredTime;
  final int durationMinutes;
  final bool wasRescheduled;
  final double confidenceScore;
  final String anchoringReason;

  AnchoredTaskData({
    required this.taskId,
    required this.title,
    required this.originalTime,
    required this.anchoredTime,
    required this.durationMinutes,
    required this.wasRescheduled,
    required this.confidenceScore,
    required this.anchoringReason,
  });

  factory AnchoredTaskData.fromJson(Map<String, dynamic> json) {
    return AnchoredTaskData(
      taskId: json['task_id'] ?? '',
      title: json['title'] ?? '',
      originalTime: json['original_time'] ?? '',
      anchoredTime: json['anchored_time'] ?? '',
      durationMinutes: json['duration_minutes'] ?? 0,
      wasRescheduled: json['was_rescheduled'] ?? false,
      confidenceScore: (json['confidence_score'] ?? 0.0).toDouble(),
      anchoringReason: json['anchoring_reason'] ?? '',
    );
  }
}

class CalendarAnchoringService {
  final Dio _dio;
  final String _baseUrl;

  CalendarAnchoringService({Dio? dio})
      : _dio = dio ?? Dio(),
        _baseUrl = AppConfig.routineApiBaseUrl {
    _dio.options.baseUrl = _baseUrl;
    _dio.options.connectTimeout = const Duration(seconds: 60);
    _dio.options.receiveTimeout = const Duration(seconds: 60);
  }

  /// Anchor plan tasks to Google Calendar events
  Future<AnchoringResponse> anchorPlanToCalendar({
    required String userId,
    required String analysisResultId,
    required DateTime targetDate,
    bool useAiScoring = false,
    String? googleCalendarToken,
    String? supabaseToken,
  }) async {
    try {
      final request = AnchoringRequest(
        analysisResultId: analysisResultId,
        targetDate: targetDate,
        useAiScoring: useAiScoring,
        googleCalendarToken: googleCalendarToken,
      );

      final response = await _dio.post(
        '/api/user/$userId/plan/anchor',
        data: request.toJson(),
        options: Options(
          headers: {
            'Content-Type': 'application/json',
            if (supabaseToken != null) 'Authorization': 'Bearer $supabaseToken',
          },
        ),
      );

      return AnchoringResponse.fromJson(response.data);
    } on DioException catch (e) {
      print('Anchoring API error: ${e.message}');
      return AnchoringResponse(
        success: false,
        anchoredTasks: [],
        tasksRescheduled: 0,
        tasksKeptOriginal: 0,
        averageConfidence: 0.0,
        calendarEventsFound: 0,
        gapsAvailable: 0,
        errorMessage: e.message ?? 'Network error',
      );
    } catch (e) {
      print('Anchoring error: $e');
      return AnchoringResponse(
        success: false,
        anchoredTasks: [],
        tasksRescheduled: 0,
        tasksKeptOriginal: 0,
        averageConfidence: 0.0,
        calendarEventsFound: 0,
        gapsAvailable: 0,
        errorMessage: e.toString(),
      );
    }
  }

  /// Apply anchoring results to plan tasks (in-memory only)
  List<PlanTask> applyAnchoringToTasks(
    List<PlanTask> originalTasks,
    List<AnchoredTaskData> anchoredData,
  ) {
    // Create lookup map
    final anchoredMap = {
      for (var data in anchoredData) data.taskId: data
    };

    // Update tasks with anchored times
    return originalTasks.map((task) {
      final anchorData = anchoredMap[task.id];
      if (anchorData == null) return task;

      return task.copyWith(
        isAnchored: true,
        anchoredAt: DateTime.now(),
        anchoredTime: _formatTimeForDisplay(anchorData.anchoredTime),
        anchoredStartTime: anchorData.anchoredTime,
        anchoredEndTime: _calculateEndTime(
          anchorData.anchoredTime,
          anchorData.durationMinutes,
        ),
        anchoringConfidence: anchorData.confidenceScore,
        anchoringReason: anchorData.anchoringReason,
        wasRescheduled: anchorData.wasRescheduled,
      );
    }).toList();
  }

  /// Format time from "HH:MM:SS" to "h:MM AM/PM"
  String _formatTimeForDisplay(String time24h) {
    try {
      final parts = time24h.split(':');
      final hour = int.parse(parts[0]);
      final minute = int.parse(parts[1]);

      final period = hour >= 12 ? 'PM' : 'AM';
      final hour12 = hour > 12 ? hour - 12 : (hour == 0 ? 12 : hour);

      return '$hour12:${minute.toString().padLeft(2, '0')} $period';
    } catch (e) {
      return time24h;
    }
  }

  /// Calculate end time from start time and duration
  String _calculateEndTime(String startTime24h, int durationMinutes) {
    try {
      final parts = startTime24h.split(':');
      final hour = int.parse(parts[0]);
      final minute = int.parse(parts[1]);

      final startMinutes = hour * 60 + minute;
      final endMinutes = startMinutes + durationMinutes;

      final endHour = (endMinutes ~/ 60) % 24;
      final endMinute = endMinutes % 60;

      return '${endHour.toString().padLeft(2, '0')}:${endMinute.toString().padLeft(2, '0')}:00';
    } catch (e) {
      return startTime24h;
    }
  }

  /// Remove anchoring from tasks (revert to original times)
  List<PlanTask> removeAnchoring(List<PlanTask> tasks) {
    return tasks.map((task) {
      if (!task.isAnchored) return task;

      return task.copyWith(
        isAnchored: false,
        anchoredAt: null,
        anchoredTime: null,
        anchoredStartTime: null,
        anchoredEndTime: null,
        anchoringConfidence: null,
        anchoringReason: null,
        wasRescheduled: false,
      );
    }).toList();
  }
}
```

**Deliverables**:
- ✅ Updated `PlanTask` model with anchoring fields
- ✅ `CalendarAnchoringService` created
- ✅ Service can call backend API
- ✅ Service can apply anchoring to tasks (in-memory)

---

## Phase 3: Flutter App - UI Layer (Basic)

**Duration**: 3 days
**Priority**: HIGH

### 3.1 Add "Anchor to Calendar" Button

**File**: `/Users/kothagattu/Desktop/OG/HolisticOS-app/lib/presentation/screens/planner/unified_plan_dashboard.dart`

**Location**: Line ~1186-1205 (Quick Actions section)

```dart
// Add after "Log Food" button
Expanded(
  child: _buildQuickActionButton(
    icon: Icons.anchor,
    label: 'Anchor to Calendar',
    color: const Color(0xFF00BCD4), // Cyan color
    onTap: _hasPlansForSelectedDate ? _openCalendarAnchoring : null,
  ),
),

// Add state variable for anchoring
bool _isAnchoring = false;
AnchoringResponse? _lastAnchoringResult;

// Add method to open anchoring
void _openCalendarAnchoring() async {
  if (_planGroups.isEmpty) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('No plans available to anchor')),
    );
    return;
  }

  // Show loading dialog
  setState(() => _isAnchoring = true);

  try {
    final anchoringService = CalendarAnchoringService();
    final userId = _userId ?? '';
    final analysisId = _planGroups.first.analysisId;

    // Get Supabase token
    final supabaseToken = supabase.auth.currentSession?.accessToken;

    // Call anchoring API
    final result = await anchoringService.anchorPlanToCalendar(
      userId: userId,
      analysisResultId: analysisId,
      targetDate: _selectedDate,
      useAiScoring: false, // Start with fast algorithmic mode
      supabaseToken: supabaseToken,
    );

    if (result.success) {
      // Apply anchoring to tasks in UI
      setState(() {
        _applyAnchoringToUI(result);
        _lastAnchoringResult = result;
        _isAnchoring = false;
      });

      // Show success message
      _showAnchoringSuccessDialog(result);
    } else {
      setState(() => _isAnchoring = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Anchoring failed: ${result.errorMessage}')),
      );
    }
  } catch (e) {
    setState(() => _isAnchoring = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Error: $e')),
    );
  }
}

void _applyAnchoringToUI(AnchoringResponse result) {
  final anchoringService = CalendarAnchoringService();

  for (var planGroup in _planGroups) {
    for (var timeBlock in planGroup.timeBlocks) {
      final anchoredTasks = anchoringService.applyAnchoringToTasks(
        timeBlock.tasks,
        result.anchoredTasks,
      );

      // Update time block with anchored tasks
      // (This will require modifying TimeBlock to have mutable tasks or recreating)
      // For now, we'll use local state to track anchored versions
    }
  }
}

void _showAnchoringSuccessDialog(AnchoringResponse result) {
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('✅ Calendar Anchoring Complete'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('📊 ${result.tasksRescheduled} tasks rescheduled'),
          Text('✓ ${result.tasksKeptOriginal} tasks kept original time'),
          Text('📅 ${result.calendarEventsFound} calendar events found'),
          Text('🎯 ${(result.averageConfidence * 100).toStringAsFixed(0)}% average confidence'),
          const SizedBox(height: 16),
          const Text(
            'Anchored tasks are shown with updated times. '
            'Original times are preserved - you can revert anytime.',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Got it!'),
        ),
      ],
    ),
  );
}

// Add method to remove anchoring
void _removeAnchoring() {
  setState(() {
    final anchoringService = CalendarAnchoringService();

    for (var planGroup in _planGroups) {
      for (var timeBlock in planGroup.timeBlocks) {
        final originalTasks = anchoringService.removeAnchoring(timeBlock.tasks);
        // Update UI with original tasks
      }
    }

    _lastAnchoringResult = null;
  });

  ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(content: Text('Anchoring removed - tasks restored to original times')),
  );
}
```

### 3.2 Update Task Display to Show Anchored Times

**File**: `/Users/kothagattu/Desktop/OG/HolisticOS-app/lib/presentation/widgets/planner/time_block_card.dart`

```dart
// In the task item widget (around line 500-600 where tasks are displayed)

// Add badge to show anchored status
Widget _buildTaskItem(PlanTask task) {
  return ListTile(
    leading: Checkbox(
      value: task.status == TaskStatus.completed,
      onChanged: (value) => _onTaskToggled(task, value ?? false),
    ),
    title: Row(
      children: [
        // Show anchored badge if task is anchored
        if (task.isAnchored) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: Colors.cyan.shade100,
              borderRadius: BorderRadius.circular(4),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.anchor, size: 12, color: Colors.cyan),
                SizedBox(width: 4),
                Text(
                  'ANCHORED',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: Colors.cyan,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
        ],
        Expanded(child: Text(task.name)),
      ],
    ),
    subtitle: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Show both original and anchored time if rescheduled
        if (task.isAnchored && task.wasRescheduled) ...[
          Text(
            'Original: ${task.time}',
            style: TextStyle(
              decoration: TextDecoration.lineThrough,
              color: Colors.grey.shade600,
              fontSize: 12,
            ),
          ),
          Text(
            'Anchored: ${task.displayTime} ⚓',
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              color: Colors.cyan,
              fontSize: 12,
            ),
          ),
          if (task.anchoringConfidence != null)
            Text(
              'Confidence: ${(task.anchoringConfidence! * 100).toStringAsFixed(0)}%',
              style: const TextStyle(fontSize: 10, color: Colors.grey),
            ),
        ] else
          Text(task.displayTime),
      ],
    ),
    trailing: task.isAnchored
        ? IconButton(
            icon: const Icon(Icons.info_outline, size: 20),
            onPressed: () => _showAnchoringDetails(task),
          )
        : null,
  );
}

void _showAnchoringDetails(PlanTask task) {
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('Anchoring Details'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Task: ${task.name}'),
          const Divider(),
          Text('Original Time: ${task.time}'),
          Text('Anchored Time: ${task.displayTime}'),
          const SizedBox(height: 8),
          if (task.anchoringReason != null)
            Text(
              'Reason: ${task.anchoringReason}',
              style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic),
            ),
          if (task.anchoringConfidence != null)
            LinearProgressIndicator(
              value: task.anchoringConfidence,
              backgroundColor: Colors.grey.shade300,
              valueColor: AlwaysStoppedAnimation(Colors.cyan),
            ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Close'),
        ),
      ],
    ),
  );
}
```

### 3.3 Add Loading Indicator

**File**: Same file as 3.1 (`unified_plan_dashboard.dart`)

```dart
// Add to build method, overlay when anchoring
@override
Widget build(BuildContext context) {
  return Stack(
    children: [
      // Existing content...
      _buildMainContent(),

      // Anchoring loading overlay
      if (_isAnchoring)
        Container(
          color: Colors.black54,
          child: Center(
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const CircularProgressIndicator(),
                    const SizedBox(height: 16),
                    const Text(
                      'Anchoring tasks to calendar...',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Finding optimal time slots',
                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
    ],
  );
}
```

**Deliverables**:
- ✅ "Anchor to Calendar" button added to planner
- ✅ Button triggers anchoring API call
- ✅ Tasks display anchored times with badge
- ✅ Success dialog shows anchoring statistics
- ✅ Loading indicator during anchoring

---

## Phase 4: Advanced Features

**Duration**: 3-4 days
**Priority**: MEDIUM

### 4.1 Google Calendar Event Selector

Currently, the system uses mock calendar or fetches all events. For production, allow users to select specific anchor events.

**Create**: `/Users/kothagattu/Desktop/OG/HolisticOS-app/lib/presentation/screens/planner/calendar_event_selector_screen.dart`

```dart
class CalendarEventSelectorScreen extends StatefulWidget {
  final DateTime selectedDate;
  final Function(CalendarEvent?) onEventSelected;

  const CalendarEventSelectorScreen({
    Key? key,
    required this.selectedDate,
    required this.onEventSelected,
  }) : super(key: key);

  @override
  State<CalendarEventSelectorScreen> createState() => _CalendarEventSelectorScreenState();
}

class _CalendarEventSelectorScreenState extends State<CalendarEventSelectorScreen> {
  List<CalendarEvent> _events = [];
  bool _loading = true;
  CalendarEvent? _selectedEvent;

  @override
  void initState() {
    super.initState();
    _fetchGoogleCalendarEvents();
  }

  Future<void> _fetchGoogleCalendarEvents() async {
    // Fetch from Google Calendar API
    // Parse and display
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Select Anchor Event'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _events.isEmpty
              ? _buildNoEventsView()
              : _buildEventsList(),
      bottomNavigationBar: _selectedEvent != null
          ? _buildConfirmButton()
          : null,
    );
  }

  Widget _buildEventsList() {
    return ListView.builder(
      itemCount: _events.length,
      itemBuilder: (context, index) {
        final event = _events[index];
        final isSelected = _selectedEvent?.id == event.id;

        return ListTile(
          leading: Radio<String>(
            value: event.id,
            groupValue: _selectedEvent?.id,
            onChanged: (value) {
              setState(() => _selectedEvent = event);
            },
          ),
          title: Text(event.title),
          subtitle: Text(
            '${_formatTime(event.startTime)} - ${_formatTime(event.endTime)}',
          ),
          trailing: isSelected
              ? const Icon(Icons.check_circle, color: Colors.green)
              : null,
          onTap: () {
            setState(() => _selectedEvent = event);
          },
        );
      },
    );
  }

  Widget _buildNoEventsView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.calendar_today, size: 64, color: Colors.grey),
          const SizedBox(height: 16),
          const Text('No calendar events found'),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: () {
              // Skip event selection, use all events
              widget.onEventSelected(null);
              Navigator.pop(context);
            },
            child: const Text('Use All Available Time'),
          ),
        ],
      ),
    );
  }

  Widget _buildConfirmButton() {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: ElevatedButton(
          onPressed: () {
            widget.onEventSelected(_selectedEvent);
            Navigator.pop(context);
          },
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
          child: const Text('Anchor to This Event'),
        ),
      ),
    );
  }

  String _formatTime(DateTime time) {
    final hour = time.hour > 12 ? time.hour - 12 : time.hour;
    final period = time.hour >= 12 ? 'PM' : 'AM';
    return '$hour:${time.minute.toString().padLeft(2, '0')} $period';
  }
}
```

### 4.2 Anchoring Modes

Add different anchoring strategies:

1. **Full Day Anchoring** (current default)
   - Anchors all tasks for the day

2. **Single Time Block Anchoring**
   - Anchors only one time block

3. **Custom Range Anchoring**
   - User selects time range (e.g., 9 AM - 5 PM)

**Implementation**: Add mode selector to anchoring dialog

### 4.3 Visual Timeline Preview

Show before/after timeline visualization before confirming anchoring.

**Create**: `/Users/kothagattu/Desktop/OG/HolisticOS-app/lib/presentation/widgets/planner/anchoring_preview_widget.dart`

```dart
class AnchoringPreviewWidget extends StatelessWidget {
  final List<PlanTask> originalTasks;
  final List<PlanTask> anchoredTasks;

  const AnchoringPreviewWidget({
    Key? key,
    required this.originalTasks,
    required this.anchoredTasks,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const Text('Before vs After', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Before column
            Expanded(
              child: _buildTaskColumn('Original', originalTasks, Colors.grey),
            ),
            const SizedBox(width: 8),
            const Icon(Icons.arrow_forward, color: Colors.cyan),
            const SizedBox(width: 8),
            // After column
            Expanded(
              child: _buildTaskColumn('Anchored', anchoredTasks, Colors.cyan),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildTaskColumn(String title, List<PlanTask> tasks, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: TextStyle(fontWeight: FontWeight.bold, color: color)),
        const SizedBox(height: 8),
        ...tasks.map((task) => _buildTaskItem(task, color)),
      ],
    );
  }

  Widget _buildTaskItem(PlanTask task, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 4),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        border: Border.left(width: 3, color: color),
        color: color.withOpacity(0.1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(task.name, style: const TextStyle(fontSize: 12)),
          Text(
            task.displayTime,
            style: TextStyle(fontSize: 10, color: Colors.grey.shade700),
          ),
        ],
      ),
    );
  }
}
```

**Deliverables**:
- ✅ Event selector screen for choosing anchor point
- ✅ Multiple anchoring modes (full day, single block, custom range)
- ✅ Visual before/after timeline preview
- ✅ Improved user experience with preview before committing

---

## Phase 5: Persistence & State Management

**Duration**: 2 days
**Priority**: MEDIUM-LOW

### 5.1 Local Storage for Anchoring State

Since anchored tasks are NOT saved to database, use local storage to persist anchoring across app restarts.

**File**: `/Users/kothagattu/Desktop/OG/HolisticOS-app/lib/core/repositories/anchoring_cache_repository.dart`

```dart
import 'package:hive/hive.dart';
import 'package:holisticos/core/models/planner_models.dart';

class AnchoringCacheRepository {
  static const String _boxName = 'anchoring_cache';
  late Box<Map> _box;

  Future<void> initialize() async {
    _box = await Hive.openBox<Map>(_boxName);
  }

  /// Save anchored state for a date
  Future<void> saveAnchoredTasks({
    required String userId,
    required DateTime date,
    required List<PlanTask> tasks,
    required AnchoringResponse metadata,
  }) async {
    final key = _buildKey(userId, date);

    await _box.put(key, {
      'tasks': tasks.map((t) => _taskToMap(t)).toList(),
      'metadata': {
        'tasksRescheduled': metadata.tasksRescheduled,
        'tasksKeptOriginal': metadata.tasksKeptOriginal,
        'averageConfidence': metadata.averageConfidence,
        'calendarEventsFound': metadata.calendarEventsFound,
        'anchoredAt': DateTime.now().toIso8601String(),
      },
    });
  }

  /// Load anchored tasks for a date
  Future<Map<String, dynamic>?> loadAnchoredTasks({
    required String userId,
    required DateTime date,
  }) async {
    final key = _buildKey(userId, date);
    return _box.get(key);
  }

  /// Check if date has anchored tasks
  bool hasAnchoredTasks({
    required String userId,
    required DateTime date,
  }) {
    final key = _buildKey(userId, date);
    return _box.containsKey(key);
  }

  /// Remove anchoring for a date
  Future<void> removeAnchoring({
    required String userId,
    required DateTime date,
  }) async {
    final key = _buildKey(userId, date);
    await _box.delete(key);
  }

  /// Clear all anchoring cache
  Future<void> clearAll() async {
    await _box.clear();
  }

  String _buildKey(String userId, DateTime date) {
    return '${userId}_${date.toIso8601String().split('T')[0]}';
  }

  Map<String, dynamic> _taskToMap(PlanTask task) {
    return {
      'id': task.id,
      'isAnchored': task.isAnchored,
      'anchoredTime': task.anchoredTime,
      'anchoredStartTime': task.anchoredStartTime,
      'anchoredEndTime': task.anchoredEndTime,
      'anchoringConfidence': task.anchoringConfidence,
      'anchoringReason': task.anchoringReason,
      'wasRescheduled': task.wasRescheduled,
    };
  }
}
```

### 5.2 Auto-Restore Anchoring on App Launch

**File**: `/Users/kothagattu/Desktop/OG/HolisticOS-app/lib/presentation/screens/planner/unified_plan_dashboard.dart`

```dart
// In initState or when loading plans
@override
void initState() {
  super.initState();
  _loadPlansAndRestoreAnchoring();
}

Future<void> _loadPlansAndRestoreAnchoring() async {
  await _fetchPlansForDate(_selectedDate);

  // Check if anchoring exists in cache
  final anchoringCache = AnchoringCacheRepository();
  final cachedAnchoring = await anchoringCache.loadAnchoredTasks(
    userId: _userId!,
    date: _selectedDate,
  );

  if (cachedAnchoring != null) {
    // Restore anchored state
    setState(() {
      _restoreAnchoringFromCache(cachedAnchoring);
    });

    // Show subtle indicator that tasks are anchored
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('📌 Restored anchored tasks from cache'),
        action: SnackBarAction(
          label: 'Remove',
          onPressed: () async {
            await anchoringCache.removeAnchoring(
              userId: _userId!,
              date: _selectedDate,
            );
            _removeAnchoring();
          },
        ),
      ),
    );
  }
}
```

**Deliverables**:
- ✅ Local storage for anchored tasks
- ✅ Auto-restore anchoring on app launch
- ✅ Cache invalidation when date changes
- ✅ User can clear anchoring cache

---

## Phase 6: Polish & Edge Cases

**Duration**: 2 days
**Priority**: LOW

### 6.1 Handle Edge Cases

1. **No Calendar Events**
   - Show message: "No calendar events found. Tasks will be scheduled as planned."
   - Still run anchoring (will keep original times)

2. **No Available Gaps**
   - Show warning: "Calendar is fully booked. Some tasks may overlap."
   - Let user decide to proceed or cancel

3. **Google Calendar Not Connected**
   - Show setup prompt with button to connect
   - Link to calendar settings page

4. **API Timeout**
   - Show retry button
   - Fall back to cached previous anchoring if available

### 6.2 Add Settings

**File**: `/Users/kothagattu/Desktop/OG/HolisticOS-app/lib/presentation/screens/settings/planner_settings_screen.dart`

```dart
// Add anchoring preferences
class PlannerSettings {
  bool autoAnchorOnPlanGenerate; // Auto-anchor when new plan is created
  bool useAiScoring; // Use AI-enhanced scoring (slower but better)
  int minGapMinutes; // Minimum gap size to consider (default 15)
  bool showAnchoringNotifications; // Notify when anchoring completes

  // Cache settings
  int anchoringCacheDays; // How long to keep anchored state (default 7 days)
}
```

### 6.3 Analytics & Tracking

Track anchoring usage:
- Number of anchorings per user
- Success rate
- Average confidence scores
- Most rescheduled task categories

**Deliverables**:
- ✅ Edge case handling
- ✅ User settings for anchoring preferences
- ✅ Analytics integration
- ✅ Error recovery mechanisms

---

## Phase 7: Testing & Deployment

**Duration**: 2-3 days
**Priority**: CRITICAL

### 7.1 Backend Testing

```bash
# Test anchoring API
cd /Users/kothagattu/Desktop/OG/hos-agentic-ai-prod
python testing/test_anchoring_api.py

# Test with real Google Calendar
python testing/test_anchoring_google_calendar.py

# Load testing
python testing/load_test_anchoring.py
```

### 7.2 Flutter Integration Testing

**Create**: `/Users/kothagattu/Desktop/OG/HolisticOS-app/integration_test/anchoring_test.dart`

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:holisticos/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Calendar Anchoring Integration', () {
    testWidgets('User can anchor plan to calendar', (tester) async {
      app.main();
      await tester.pumpAndSettle();

      // Navigate to planner
      await tester.tap(find.text('Planner'));
      await tester.pumpAndSettle();

      // Tap "Anchor to Calendar" button
      await tester.tap(find.text('Anchor to Calendar'));
      await tester.pumpAndSettle();

      // Wait for anchoring to complete
      await tester.pump(const Duration(seconds: 5));

      // Verify success dialog appears
      expect(find.text('Calendar Anchoring Complete'), findsOneWidget);

      // Verify tasks show anchored badge
      expect(find.text('ANCHORED'), findsWidgets);
    });

    testWidgets('User can remove anchoring', (tester) async {
      // ... test removing anchoring
    });
  });
}
```

### 7.3 Manual Testing Checklist

- [ ] Anchoring with mock calendar works
- [ ] Anchoring with real Google Calendar works
- [ ] Anchored tasks display correctly
- [ ] Original times preserved
- [ ] Removing anchoring reverts to original
- [ ] Anchoring persists across app restarts
- [ ] Loading indicators show properly
- [ ] Error messages are user-friendly
- [ ] Works on both iOS and Android
- [ ] Works with different plan archetypes
- [ ] Works with empty calendar
- [ ] Works with fully booked calendar

**Deliverables**:
- ✅ Backend API tests passing
- ✅ Flutter integration tests passing
- ✅ Manual testing completed
- ✅ Bug fixes implemented
- ✅ Performance validated

---

## Summary Timeline

| Phase | Duration | Priority | Blockers |
|-------|----------|----------|----------|
| **Phase 1**: Backend API | 2-3 days | HIGH | None |
| **Phase 2**: Flutter Data Layer | 2 days | HIGH | Phase 1 |
| **Phase 3**: Flutter UI (Basic) | 3 days | HIGH | Phase 2 |
| **Phase 4**: Advanced Features | 3-4 days | MEDIUM | Phase 3 |
| **Phase 5**: Persistence | 2 days | MEDIUM-LOW | Phase 3 |
| **Phase 6**: Polish | 2 days | LOW | Phase 3 |
| **Phase 7**: Testing | 2-3 days | CRITICAL | All |

**Total Estimated Time**: 16-21 days (3-4 weeks)

**Minimum Viable Product (MVP)**: Phases 1-3 only = **7-8 days**

---

## Quick Start MVP (Phases 1-3 Only)

If you want to get something working quickly, focus on:

1. **Backend** (2 days):
   - Create `/api/user/{user_id}/plan/anchor` endpoint
   - Return anchored tasks with new times
   - Test with `demo_anchoring.py` script

2. **Flutter Data** (1 day):
   - Add anchoring fields to `PlanTask` model
   - Create `CalendarAnchoringService`

3. **Flutter UI** (2 days):
   - Add "Anchor to Calendar" button
   - Display anchored times
   - Show success dialog

**MVP Ready in 5 days!** 🚀

---

## Key Design Decisions

✅ **No database persistence** - Anchored tasks stored in app only (Hive cache)
✅ **Backward compatible** - Original times always preserved
✅ **Flexible modes** - Start with mock calendar, add real Google Calendar later
✅ **Progressive enhancement** - MVP in 5 days, full feature set in 3-4 weeks
✅ **User control** - Easy to remove anchoring and revert to original plan
✅ **Visual feedback** - Clear indicators for anchored vs original times
✅ **Performance** - Fast algorithmic mode by default, AI mode optional

---

## Next Steps

1. **Review this plan** - Ensure all requirements are covered
2. **Start with UI mockups** - Design the anchoring flow visually
3. **Implement MVP** - Focus on Phases 1-3 for quick value
4. **Gather feedback** - Test with users before adding advanced features
5. **Iterate** - Add Phases 4-6 based on user needs

---

**Document Version**: 1.0
**Created**: November 7, 2025
**Status**: Ready for UI Design Phase
