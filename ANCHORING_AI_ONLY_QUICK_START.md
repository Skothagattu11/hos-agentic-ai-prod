# AI-Only Anchoring System - Quick Start Guide

## Overview

The AI-Only Anchoring system uses Google Gemini Flash for fast, cost-effective task anchoring. This document provides quick commands to get started.

**Model**: Gemini 2.0 Flash (2-3 seconds, ~$0.005 per request)

## What Changed

✅ **AI-Only Agent**: Complete implementation in `services/anchoring/ai_anchoring_agent.py`
✅ **Coordinator Updated**: `anchoring_coordinator.py` now supports 3 modes (AI-Only, Hybrid, Algorithmic)
✅ **Package Exports**: All components properly exported in `__init__.py`
✅ **Test Script Updated**: `testing/demo_anchoring_no_emoji.py` supports AI-only mode
✅ **100% Backward Compatible**: Same AssignmentResult format - no Flutter UI changes needed

## Testing the AI-Only System

### Option 1: Using REST API (RECOMMENDED)

The REST API endpoint at `/generate-anchors` supports AI-only mode.

#### Step 1: Get Your User ID and Plan ID

First, find your user_id and a recent analysis_result_id from the database:

```sql
-- Get your user_id
SELECT id, email FROM user_profiles LIMIT 5;

-- Get recent plans for your user
SELECT id, user_id, analysis_date, archetype, created_at
FROM holistic_analysis_results
WHERE user_id = 'your-user-id-here'
ORDER BY created_at DESC
LIMIT 5;

-- Get your saved schedule ID (optional)
SELECT id, user_id, schedule_name
FROM saved_schedules
WHERE user_id = 'your-user-id-here'
LIMIT 5;
```

#### Step 2: Call the REST API

```bash
# Replace these with your actual IDs:
USER_ID="a57f70b4-d0a4-4aef-b721-a4b526f64869"
SCHEDULE_ID="your-schedule-id-from-db"
TODAY=$(date +%Y-%m-%d)

curl -X POST http://localhost:8002/generate-anchors \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"date\": \"$TODAY\",
    \"schedule_id\": \"$SCHEDULE_ID\",
    \"use_ai_only\": true,
    \"use_ai_scoring\": false,
    \"confidence_threshold\": 0.7
  }"
```

**Request Parameters:**
- `user_id`: User's profile UUID (from user_profiles table)
- `date`: Target date in ISO format (YYYY-MM-DD) - use today's date
- `schedule_id`: Saved schedule UUID (from saved_schedules table, optional)
- `use_ai_only`: `true` for AI-only mode (RECOMMENDED)
- `use_ai_scoring`: `false` (legacy hybrid mode)
- `confidence_threshold`: Minimum confidence score (0.0-1.0, default 0.7)

**Response:**
```json
{
  "anchored_tasks": [
    {
      "task_id": "uuid",
      "task_name": "Morning Meditation",
      "duration_minutes": 15,
      "anchored_time": "2025-01-10T07:00:00",
      "confidence": 0.92,
      "reasoning": "Placed in morning routine after wake-up, aligns with user's chronotype..."
    }
  ],
  "standalone_tasks": [...],
  "message": "Successfully anchored 5 tasks using AI-Only anchoring"
}
```

### Option 2: Using Test Script

The existing test script `testing/demo_anchoring_no_emoji.py` provides a visual demo with detailed output.

#### Step 1: Get Your IDs from Database

```sql
-- Get a recent plan ID with tasks scheduled for today
SELECT
    har.id as analysis_id,
    har.user_id,
    har.analysis_date,
    har.archetype,
    COUNT(pi.id) as task_count
FROM holistic_analysis_results har
LEFT JOIN plan_items pi ON pi.analysis_result_id = har.id
WHERE har.analysis_date = CURRENT_DATE
GROUP BY har.id
ORDER BY har.created_at DESC
LIMIT 5;
```

#### Step 2: Run the Test Script

```bash
cd /mnt/c/dev_skoth/hos/hos-agentic-ai-prod/hos-agentic-ai-prod

# Set your IDs (replace with values from database query above)
PLAN_ID="d8fe057d-fe02-4547-b7f2-f4884e424544"
USER_ID="a57f70b4-d0a4-4aef-b721-a4b526f64869"

# AI-Only mode (RECOMMENDED)
python3 testing/demo_anchoring_no_emoji.py \
  $PLAN_ID \
  $USER_ID \
  true \
  false \
  true

# Or run with explicit values:
python3 testing/demo_anchoring_no_emoji.py \
  d8fe057d-fe02-4547-b7f2-f4884e424544 \
  a57f70b4-d0a4-4aef-b721-a4b526f64869 \
  true \
  false \
  true
```

**What the script shows:**
- Fetches real plan_items from database
- Loads mock calendar events (or real Google Calendar if available)
- Runs AI-only anchoring
- Displays before/after comparison with visual timeline
- Shows confidence scores and reasoning for each assignment

### Command Parameters

| Position | Parameter | Description | AI-Only Value |
|----------|-----------|-------------|---------------|
| 1 | analysis_result_id | Plan UUID from database | (your plan ID) |
| 2 | user_id | User profile UUID | (your user ID) |
| 3 | use_mock_calendar | Use mock vs real calendar | `true` (for testing) |
| 4 | use_ai_scoring | Hybrid AI scoring (legacy) | `false` |
| 5 | use_ai_only | AI-only holistic mode | `true` ⭐ |

### Comparison: All Three Modes (Side-by-Side)

To see the difference between all three anchoring modes with your real data:

```bash
# Get your IDs first
PLAN_ID="your-analysis-id-from-db"
USER_ID="your-user-id-from-db"

echo "=== Running All 3 Modes for Comparison ==="

echo -e "\n1️⃣  ALGORITHMIC MODE (Fast, Rule-Based)"
python3 testing/demo_anchoring_no_emoji.py $PLAN_ID $USER_ID true false false

echo -e "\n2️⃣  HYBRID AI MODE (AI Scoring + Optimization)"
python3 testing/demo_anchoring_no_emoji.py $PLAN_ID $USER_ID true true false

echo -e "\n3️⃣  AI-ONLY MODE (Gemini Holistic Reasoning - RECOMMENDED)"
python3 testing/demo_anchoring_no_emoji.py $PLAN_ID $USER_ID true false true
```

**Expected Results:**
- **Algorithmic**: Fast (~200ms), simple scoring, may miss context
- **Hybrid**: Medium speed (~500ms), better scoring, still loses holistic view
- **AI-Only (Gemini)**: Fast (~2-3s), best context awareness, natural explanations

## Code Integration

### Using in Python Code

```python
from services.anchoring import get_anchoring_coordinator

# AI-Only mode (recommended for N≤15 tasks)
coordinator = get_anchoring_coordinator(use_ai_only=True)

result = await coordinator.anchor_tasks(
    user_id="user_123",
    tasks=task_list,
    target_date=date.today(),
    use_mock_calendar=True,
    user_profile={
        "chronotype": "morning_lark",
        "behavioral_patterns": {...},
        "preferences": {...}
    }
)

# Result format is identical to existing implementation
print(f"Anchored: {result.tasks_anchored}/{result.total_tasks}")
print(f"Confidence: {result.average_confidence:.2%}")
```

### API Endpoint Integration

No changes needed to existing API endpoints! The same request/response format works:

```python
# In your API route
coordinator = get_anchoring_coordinator(use_ai_only=True)  # Just add this parameter
# Everything else stays the same
```

## Architecture Modes

### 1. Algorithmic Only (Fast, No AI)

```python
coordinator = get_anchoring_coordinator()
# Uses rule-based scoring: duration fit + time window + priority
# Speed: ~200ms
# Cost: $0
```

### 2. Hybrid AI-Enhanced (Legacy)

```python
coordinator = get_anchoring_coordinator(use_ai_scoring=True)
# Uses AI scoring + greedy optimization
# Speed: ~500ms
# Cost: ~$0.002/request
```

### 3. AI-Only Holistic (RECOMMENDED)

```python
coordinator = get_anchoring_coordinator(use_ai_only=True)
# Uses Gemini 2.0 Flash with full context reasoning
# Speed: 2-3 seconds
# Cost: ~$0.005/request
# Best for: N≤15 tasks with context awareness needs
```

## File Structure

```
services/anchoring/
├── __init__.py                          # ✅ Updated with AI-Only exports
├── anchoring_coordinator.py             # ✅ Updated with 3-mode support
├── ai_anchoring_agent.py                # ✅ NEW - AI-only implementation
├── basic_scorer_service.py              # (Algorithmic mode)
├── ai_scorer_service.py                 # (Hybrid mode)
├── hybrid_scorer_service.py             # (Hybrid mode)
├── greedy_assignment_service.py         # (Algorithmic/Hybrid modes)
├── calendar_integration_service.py      # (Shared)
└── calendar_gap_finder.py               # (Shared)

services/api_gateway/
└── anchor_endpoint_rest.py              # ✅ Updated with AI-only support

testing/
└── demo_anchoring_no_emoji.py           # ✅ Updated with AI-only support

docs/
├── ANCHORING_AI_ARCHITECTURE.md         # ✅ Complete architecture docs
├── ANCHORING_IMPLEMENTATION_GUIDE.md    # ✅ Developer guide
└── ANCHORING_AI_ONLY_QUICK_START.md     # ✅ This file - Quick start guide
```

## Key Features

### AI-Only Advantages

✅ **Holistic Reasoning**: Sees all context at once (calendar, tasks, user profile, preferences)
✅ **Context-Aware**: Understands task semantics from descriptions
✅ **Natural Explanations**: Provides reasoning in plain language
✅ **User Preferences**: Respects stated preferences ("I prefer evening workouts")
✅ **Circadian Understanding**: Optimizes based on chronotype and energy patterns
✅ **Workflow Intelligence**: Understands task relationships and sequencing

### Backward Compatibility Guarantees

✅ **Same Input Format**: TaskToAnchor objects unchanged
✅ **Same Output Format**: AssignmentResult structure identical
✅ **No Flutter Changes**: UI code works without modification
✅ **No API Changes**: Existing endpoints work as-is
✅ **Drop-in Replacement**: Just add `use_ai_only=True` parameter

## Performance Expectations

| Metric | Algorithmic | Hybrid AI | AI-Only (Gemini) |
|--------|-------------|-----------|------------------|
| **Speed** | ~200ms | ~500ms | 2-3 seconds |
| **Cost** | $0 | ~$0.002 | ~$0.005 |
| **Context Awareness** | Low | Medium | High |
| **Explanation Quality** | Scores only | Scores + AI | Natural language |
| **Best For** | N>20 tasks | N=10-20 | N≤15 tasks |

## Troubleshooting

### "No module named 'google.generativeai'"

```bash
pip install google-generativeai
```

### "Missing GEMINI_API_KEY"

Add to `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### "AI agent import error"

Verify the package exports:
```python
from services.anchoring import AIAnchoringAgent, get_ai_anchoring_agent
```

## Next Steps

1. ✅ **Test**: Run the demo script with AI-only mode
2. ✅ **Validate**: Check that AssignmentResult format matches existing
3. ✅ **Compare**: Run all 3 modes to see differences
4. 🔄 **Deploy**: Update production code to use AI-only mode
5. 🔄 **Monitor**: Track performance and cost metrics

## Documentation

- **Architecture**: See `ANCHORING_AI_ARCHITECTURE.md`
- **Implementation**: See `ANCHORING_IMPLEMENTATION_GUIDE.md`
- **API Reference**: See `services/anchoring/__init__.py` docstrings

## Support

For issues or questions:
1. Check existing test scripts in `testing/`
2. Review architecture docs
3. Check logs for `[ANCHORING-COORDINATOR]` and `[AI-ANCHORING]` messages
