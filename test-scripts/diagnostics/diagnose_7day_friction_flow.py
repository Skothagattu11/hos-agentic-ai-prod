#!/usr/bin/env python3
"""
Enhanced 7-Day Friction-Reduction Flow Diagnostic

Traces the complete data flow:
1. Check-ins created → Database
2. FeedbackService calculates friction
3. TaskPreseeder passes to AI
4. AI receives friction data in prompt
5. AI generates simplified/adapted tasks
"""

import os
import json
from supabase import create_client
from dotenv import load_dotenv
from collections import defaultdict
import asyncio

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# The 7 test plans from your run
PLAN_IDS = [
    '9b2cd15c-3ceb-40b9-880b-be3afdcbbc00',  # Day 1 (cold start)
    '8be584c0-dbde-4921-acfe-8957066c0714',  # Day 2 (positive feedback)
    '34f187e6-e423-4ff1-a4ee-fc0c6392c079',  # Day 3 (building success)
    'e553e186-4f36-49e4-b580-1b4e795705f8',  # Day 4 (friction introduced)
    '9acba60f-18af-4b1b-a2f7-18d44f78fbc4',  # Day 5 (high friction peak)
    '8c8bd367-0258-413b-ae4e-55f0a08dc167',  # Day 6 (recovery)
    '7f7c036c-99d1-45c2-ad76-3da89ebc7e24',  # Day 7 (final adapted)
]

USER_ID = 'a57f70b4-d0a4-4aef-b721-a4b526f64869'

print("="*80)
print("7-DAY FRICTION-REDUCTION FLOW DIAGNOSTIC")
print("="*80)
print()

# SECTION 1: Check-ins Database Verification
print("="*80)
print("[1] CHECK-INS DATABASE VERIFICATION")
print("="*80)

all_checkins = supabase.table('task_checkins').select(
    'plan_item_id, continue_preference, experience_rating, planned_date, completion_status'
).eq('profile_id', USER_ID).execute()

print(f"\n✅ Total check-ins in database: {len(all_checkins.data)}")
print(f"✅ User ID: {USER_ID}")

if all_checkins.data:
    # Check completion status breakdown
    status_counts = defaultdict(int)
    for checkin in all_checkins.data:
        status = checkin.get('completion_status', 'NULL')
        status_counts[status] += 1

    print(f"\nCompletion status breakdown:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    # Sample check-in
    print(f"\nSample check-in:")
    sample = all_checkins.data[0]
    print(f"  plan_item_id: {sample['plan_item_id']}")
    print(f"  completion_status: {sample['completion_status']}")
    print(f"  experience_rating: {sample['experience_rating']}")
    print(f"  continue_preference: {sample['continue_preference']}")
else:
    print("❌ NO CHECK-INS FOUND!")

# SECTION 2: TaskPreseeder Query Test
print("\n" + "="*80)
print("[2] TASKPRESEEDER QUERY TEST (PostgreSQL)")
print("="*80)

async def test_taskpreseeder_query():
    """Test the exact query TaskPreseeder uses"""
    from shared_libs.database.supabase_asyncpg_adapter import SupabaseAsyncPGAdapter

    db = SupabaseAsyncPGAdapter()
    await db.connect()

    # Exact query from TaskPreseeder line 368-372
    query = """
        SELECT COUNT(*) as count
        FROM task_checkins
        WHERE profile_id = $1
          AND completion_status = 'completed'
    """

    result = await db.fetchrow(query, USER_ID)
    count = result['count'] if result else 0

    print(f"\n✅ TaskPreseeder query result: {count} completed check-ins")

    if count == 0:
        print("\n⚠️  PROBLEM: TaskPreseeder sees 0 check-ins!")
        print("   Checking for data mismatch...")

        # Check if profile_id field exists and matches
        check_query = """
            SELECT COUNT(*) as count,
                   COUNT(DISTINCT profile_id) as unique_profiles
            FROM task_checkins
        """
        check_result = await db.fetchrow(check_query)
        print(f"\n   Total check-ins (any user): {check_result['count']}")
        print(f"   Unique profile_ids: {check_result['unique_profiles']}")

        # Try finding check-ins without status filter
        query2 = """
            SELECT COUNT(*) as count
            FROM task_checkins
            WHERE profile_id = $1
        """
        result2 = await db.fetchrow(query2, USER_ID)
        print(f"   Check-ins for user (any status): {result2['count'] if result2 else 0}")

    await db.close()

asyncio.run(test_taskpreseeder_query())

# SECTION 3: Friction Analysis Per Day
print("\n" + "="*80)
print("[3] FRICTION ANALYSIS PROGRESSION")
print("="*80)

# Get all check-ins with plan associations
all_items = supabase.table('plan_items').select(
    'id, category, analysis_result_id, profile_id'
).eq('profile_id', USER_ID).execute()

item_map = {item['id']: item for item in all_items.data}

# Group check-ins by plan (day)
checkins_by_plan = defaultdict(list)
for checkin in all_checkins.data:
    item_id = checkin['plan_item_id']
    if item_id in item_map:
        plan_id = item_map[item_id]['analysis_result_id']
        checkins_by_plan[plan_id].append({
            'category': item_map[item_id].get('category'),
            'continue_preference': checkin.get('continue_preference'),
            'experience_rating': checkin.get('experience_rating')
        })

# Calculate friction for each day
for day_idx, plan_id in enumerate(PLAN_IDS[:-1], 1):  # Exclude Day 7 (no checkins yet)
    if plan_id in checkins_by_plan:
        checkins = checkins_by_plan[plan_id]

        # Calculate nutrition friction
        nutrition_checkins = [c for c in checkins if c['category'] == 'nutrition']

        if nutrition_checkins:
            yes_count = sum(1 for c in nutrition_checkins if c['continue_preference'] == 'yes')
            no_count = sum(1 for c in nutrition_checkins if c['continue_preference'] == 'no')
            maybe_count = len(nutrition_checkins) - yes_count - no_count

            ratings = [c['experience_rating'] for c in nutrition_checkins if c['experience_rating']]
            avg_rating = sum(ratings) / len(ratings) if ratings else 3.0

            # Friction calculation
            total = len(nutrition_checkins)
            no_rate = no_count / total if total > 0 else 0
            experience_friction = (5 - avg_rating) / 4.0
            continuation_friction = (no_rate * 0.8)
            friction_score = (experience_friction * 0.6) + (continuation_friction * 0.4)

            sentiment = "✅" if friction_score <= 0.3 else "😐" if friction_score <= 0.6 else "❌"

            print(f"\nDay {day_idx} Nutrition Friction: {sentiment} {friction_score:.2f}")
            print(f"  Check-ins: {total} (yes:{yes_count}, maybe:{maybe_count}, no:{no_count})")
            print(f"  Avg rating: {avg_rating:.1f}/5")

# SECTION 4: AI Input Verification (Did AI receive friction data?)
print("\n" + "="*80)
print("[4] AI PROMPT INPUT VERIFICATION")
print("="*80)

for day_idx, plan_id in enumerate(PLAN_IDS, 1):
    result = supabase.table('holistic_analysis_results').select(
        'input_summary, created_at'
    ).eq('id', plan_id).execute()

    if result.data and result.data[0].get('input_summary'):
        input_summary = result.data[0]['input_summary']

        # Parse input_summary
        try:
            if isinstance(input_summary, str):
                summary = json.loads(input_summary)
            else:
                summary = input_summary

            has_feedback = summary.get('has_feedback', False)
            feedback_count = summary.get('feedback_count', 0)

            status = "✅" if has_feedback else "⚪"
            print(f"\nDay {day_idx}: {status} Feedback={'YES' if has_feedback else 'NO'}, Count={feedback_count}")

            if day_idx >= 2 and not has_feedback:
                print(f"   ⚠️  WARNING: Day {day_idx} should have feedback from Day {day_idx-1}!")

        except Exception as e:
            print(f"\nDay {day_idx}: ⚠️  Could not parse input_summary: {e}")

# SECTION 5: Nutrition Task Complexity Analysis
print("\n" + "="*80)
print("[5] NUTRITION TASK SIMPLIFICATION CHECK")
print("="*80)

print("\nComparing nutrition task complexity across 7 days:")
print("Looking for: micro-habits, simplified language, shorter descriptions\n")

for day_idx, plan_id in enumerate(PLAN_IDS, 1):
    items = supabase.table('plan_items').select(
        'title, description, category'
    ).eq('analysis_result_id', plan_id).eq('category', 'nutrition').execute()

    if items.data:
        print(f"\nDay {day_idx}: {len(items.data)} nutrition tasks")
        for item in items.data:
            title = item['title']
            desc = item.get('description', '')[:60]
            print(f"  • {title}")
            if desc:
                print(f"    → {desc}...")

        # Analyze complexity
        avg_title_length = sum(len(item['title']) for item in items.data) / len(items.data)
        avg_desc_length = sum(len(item.get('description', '')) for item in items.data) / len(items.data)

        # Check for micro-habit indicators
        micro_habit_keywords = ['photo', 'one', '1', 'simple', 'quick', 'easy', 'small', 'add']
        has_micro_habits = any(
            any(keyword in item['title'].lower() or keyword in item.get('description', '').lower()
                for keyword in micro_habit_keywords)
            for item in items.data
        )

        complexity_indicator = "📉 SIMPLIFIED" if (avg_title_length < 20 or has_micro_habits) else "📊 STANDARD"
        print(f"  {complexity_indicator} (avg title: {avg_title_length:.0f} chars, micro-habits: {has_micro_habits})")

# SECTION 6: Expected vs Actual Results
print("\n" + "="*80)
print("[6] EXPECTED vs ACTUAL BEHAVIOR")
print("="*80)

print("\n🎯 EXPECTED BEHAVIOR:")
print("  Day 1-3: Standard nutrition tasks (3 meals)")
print("  Day 4-5: Friction increases (continue_preference='no', rating=1-2)")
print("  Day 6-7: Tasks SIMPLIFY (micro-habits: 'Take photo of meal', 'Add 1 vegetable')")

print("\n📊 ACTUAL BEHAVIOR:")
day7_items = supabase.table('plan_items').select('category, title').eq(
    'analysis_result_id', PLAN_IDS[6]
).execute()

day7_categories = set(item.get('category') for item in day7_items.data if item.get('category'))
nutrition_day7 = [item['title'] for item in day7_items.data if item.get('category') == 'nutrition']

print(f"  Day 7 categories: {sorted(day7_categories)}")

if 'nutrition' in day7_categories:
    print(f"  ✅ Nutrition present (not excluded)")
    print(f"  Day 7 nutrition tasks:")
    for task in nutrition_day7:
        print(f"    • {task}")

    # Check if simplified
    day1_items = supabase.table('plan_items').select('title').eq(
        'analysis_result_id', PLAN_IDS[0]
    ).eq('category', 'nutrition').execute()

    day1_tasks = [item['title'] for item in day1_items.data]

    if day1_tasks == nutrition_day7:
        print(f"\n  ⚠️  WARNING: Day 7 nutrition tasks IDENTICAL to Day 1!")
        print(f"  ❌ FAILED: Tasks did not simplify despite friction")
    else:
        print(f"\n  ✅ PASSED: Tasks evolved from Day 1")
else:
    print(f"  ❌ Nutrition missing (incorrectly excluded)")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)

print("\n💡 SUMMARY:")
print("  1. Check if check-ins are in database ✓")
print("  2. Check if TaskPreseeder can query them")
print("  3. Check if friction data reaches AI prompt")
print("  4. Check if AI generated simplified tasks")
print("  5. Compare task complexity Day 1 vs Day 7")
