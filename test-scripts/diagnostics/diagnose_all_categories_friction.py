#!/usr/bin/env python3
"""
Complete Category Friction Analysis
Checks ALL categories (not just nutrition) for friction-reduction adaptation
"""

import os
import json
from supabase import create_client
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# The 7 test plans (Latest run: Oct 30, 2025 20:36)
PLAN_IDS = [
    '6c497287-25db-44ea-b6f4-44e1d27d6f69',  # Day 1
    '3bee5b8e-6d4a-47f8-a2c2-b2e2075252f0',  # Day 2
    '6d1677f1-559a-4726-818e-668a25a4a35a',  # Day 3
    '8b19b97a-b6a2-42b6-b873-dc3aebee081b',  # Day 4
    '6e30b485-23f7-4322-9385-c3bb69db3f39',  # Day 5
    '45bfa0f7-cba6-43e1-9f37-390c506251e5',  # Day 6
    'bee21f4b-0452-489a-9575-9148a1167396',  # Day 7
]

USER_ID = 'a57f70b4-d0a4-4aef-b721-a4b526f64869'

print("="*80)
print("COMPLETE CATEGORY FRICTION ANALYSIS")
print("="*80)

# Get all plan items and check-ins
all_items = supabase.table('plan_items').select(
    'id, category, analysis_result_id, title, description'
).eq('profile_id', USER_ID).execute()

all_checkins = supabase.table('task_checkins').select(
    'plan_item_id, continue_preference, experience_rating, planned_date'
).eq('profile_id', USER_ID).execute()

# Create item map
item_map = {item['id']: item for item in all_items.data}

# SECTION 1: Friction Scores for ALL Categories
print("\n" + "="*80)
print("[1] ALL CATEGORIES FRICTION SCORES")
print("="*80)

# Calculate cumulative friction by category
category_feedback = defaultdict(lambda: {
    'yes': 0, 'maybe': 0, 'no': 0,
    'rating_sum': 0, 'rating_count': 0
})

for checkin in all_checkins.data:
    item_id = checkin['plan_item_id']
    if item_id in item_map:
        cat = item_map[item_id].get('category') or 'NULL'

        pref = checkin.get('continue_preference')
        if pref == 'yes':
            category_feedback[cat]['yes'] += 1
        elif pref == 'no':
            category_feedback[cat]['no'] += 1
        else:
            category_feedback[cat]['maybe'] += 1

        rating = checkin.get('experience_rating')
        if rating:
            category_feedback[cat]['rating_sum'] += rating
            category_feedback[cat]['rating_count'] += 1

print("\nCategory Friction Levels (Cumulative):")
print(f"{'Category':<20} {'Total':>5} {'Yes':>4} {'Maybe':>5} {'No':>3} {'Rating':>7} {'Friction':>8} {'Status':>6}")
print("-" * 80)

high_friction_categories = []
low_friction_categories = []

for cat in sorted(category_feedback.keys()):
    feedback = category_feedback[cat]
    total = feedback['yes'] + feedback['maybe'] + feedback['no']

    if total > 0:
        yes_rate = feedback['yes'] / total
        no_rate = feedback['no'] / total

        avg_rating = 0
        if feedback['rating_count'] > 0:
            avg_rating = feedback['rating_sum'] / feedback['rating_count']

        # Friction calculation
        experience_friction = (5 - avg_rating) / 4.0
        continuation_friction = (no_rate * 0.8) + ((total - feedback['yes']) / total * 0.4)
        friction_score = (experience_friction * 0.6) + (continuation_friction * 0.4)

        if friction_score <= 0.3:
            sentiment = "✅ LOW"
            low_friction_categories.append(cat)
        elif friction_score <= 0.6:
            sentiment = "😐 MED"
            high_friction_categories.append(cat)
        else:
            sentiment = "❌ HIGH"
            high_friction_categories.append(cat)

        print(f"{cat:<20} {total:5} {feedback['yes']:4} {feedback['maybe']:5} {feedback['no']:3} {avg_rating:7.1f} {friction_score:8.2f} {sentiment:>6}")

print(f"\n📊 Summary:")
print(f"  Low friction (≤0.3): {len(low_friction_categories)} categories - {low_friction_categories}")
print(f"  Med/High friction (>0.3): {len(high_friction_categories)} categories - {high_friction_categories}")

# SECTION 2: Category Evolution Across 7 Days
print("\n" + "="*80)
print("[2] CATEGORY PRESENCE ACROSS 7 DAYS")
print("="*80)

# Track which categories appear in each day
category_by_day = defaultdict(lambda: [0] * 7)

for day_idx, plan_id in enumerate(PLAN_IDS):
    items = supabase.table('plan_items').select('category').eq(
        'analysis_result_id', plan_id
    ).execute()

    for item in items.data:
        cat = item.get('category') or 'NULL'
        category_by_day[cat][day_idx] += 1

print(f"\n{'Category':<20} {'D1':>4} {'D2':>4} {'D3':>4} {'D4':>4} {'D5':>4} {'D6':>4} {'D7':>4} {'Trend':>12}")
print("-" * 80)

for cat in sorted(category_by_day.keys()):
    counts = category_by_day[cat]
    trend = ""

    if counts[-1] > counts[0]:
        trend = "↗️ Growing"
    elif counts[-1] < counts[0]:
        trend = "↘️ Declining"
    else:
        trend = "➡️ Stable"

    print(f"{cat:<20} {counts[0]:4} {counts[1]:4} {counts[2]:4} {counts[3]:4} {counts[4]:4} {counts[5]:4} {counts[6]:4} {trend:>12}")

# SECTION 3: Task Complexity Analysis for HIGH FRICTION Categories
print("\n" + "="*80)
print("[3] TASK SIMPLIFICATION FOR HIGH-FRICTION CATEGORIES")
print("="*80)

if high_friction_categories:
    print(f"\nAnalyzing {len(high_friction_categories)} high-friction categories for simplification...")

    for cat in high_friction_categories:
        if cat == 'NULL':
            continue

        print(f"\n{'='*80}")
        print(f"CATEGORY: {cat} (Friction: {category_feedback[cat]['rating_sum'] / category_feedback[cat]['rating_count'] if category_feedback[cat]['rating_count'] > 0 else 0:.2f})")
        print(f"{'='*80}")

        # Get tasks for this category across all 7 days
        for day_idx, plan_id in enumerate(PLAN_IDS, 1):
            items = supabase.table('plan_items').select(
                'title, description'
            ).eq('analysis_result_id', plan_id).eq('category', cat).execute()

            if items.data:
                print(f"\nDay {day_idx}: {len(items.data)} tasks")
                for item in items.data:
                    title = item['title']
                    desc = item.get('description', '')[:50]
                    print(f"  • {title}")
                    if desc:
                        print(f"    → {desc}...")

                # Analyze complexity
                avg_title_length = sum(len(item['title']) for item in items.data) / len(items.data)

                # Check for micro-habit indicators
                micro_habit_keywords = ['photo', 'one', '1', 'simple', 'quick', 'easy', 'small', 'add', 'take']
                has_micro_habits = any(
                    any(keyword in item['title'].lower() or keyword in item.get('description', '').lower()
                        for keyword in micro_habit_keywords)
                    for item in items.data
                )

                if has_micro_habits or avg_title_length < 20:
                    print(f"  📉 SIMPLIFIED (avg: {avg_title_length:.0f} chars, micro-habits: {has_micro_habits})")
                else:
                    print(f"  📊 STANDARD (avg: {avg_title_length:.0f} chars)")
else:
    print("\n✅ No high-friction categories detected!")

# SECTION 4: Low-Friction Categories (Should be used as anchors)
print("\n" + "="*80)
print("[4] LOW-FRICTION ANCHOR CATEGORIES")
print("="*80)

if low_friction_categories:
    print(f"\nThese {len(low_friction_categories)} categories should be used as ANCHORS (habit stacking):")

    for cat in low_friction_categories:
        if cat == 'NULL':
            continue

        friction_data = category_feedback[cat]
        avg_rating = friction_data['rating_sum'] / friction_data['rating_count'] if friction_data['rating_count'] > 0 else 0

        print(f"\n✅ {cat} (Rating: {avg_rating:.1f}/5)")

        # Check if this category appears consistently
        presence = [category_by_day[cat][i] for i in range(7)]
        consistency = sum(1 for x in presence if x > 0)

        print(f"   Present in {consistency}/7 days")

        # Sample task
        sample_item = None
        for plan_id in PLAN_IDS:
            items = supabase.table('plan_items').select('title').eq(
                'analysis_result_id', plan_id
            ).eq('category', cat).execute()

            if items.data:
                sample_item = items.data[0]
                break

        if sample_item:
            print(f"   Example: \"{sample_item['title']}\"")
else:
    print("\n⚠️  No low-friction anchor categories found!")

# SECTION 5: Day 1 vs Day 7 Comparison for ALL Categories
print("\n" + "="*80)
print("[5] DAY 1 vs DAY 7 COMPARISON (ALL CATEGORIES)")
print("="*80)

day1_items = supabase.table('plan_items').select(
    'category, title'
).eq('analysis_result_id', PLAN_IDS[0]).execute()

day7_items = supabase.table('plan_items').select(
    'category, title'
).eq('analysis_result_id', PLAN_IDS[6]).execute()

# Group by category
day1_by_cat = defaultdict(list)
day7_by_cat = defaultdict(list)

for item in day1_items.data:
    cat = item.get('category') or 'NULL'
    day1_by_cat[cat].append(item['title'])

for item in day7_items.data:
    cat = item.get('category') or 'NULL'
    day7_by_cat[cat].append(item['title'])

all_categories = set(day1_by_cat.keys()) | set(day7_by_cat.keys())

print("\nCategory-by-Category Evolution:")
print()

for cat in sorted(all_categories):
    if cat == 'NULL':
        continue

    day1_tasks = day1_by_cat.get(cat, [])
    day7_tasks = day7_by_cat.get(cat, [])

    print(f"{'='*80}")
    print(f"{cat}")
    print(f"{'='*80}")
    print(f"Day 1: {len(day1_tasks)} tasks")
    print(f"Day 7: {len(day7_tasks)} tasks")

    # Check if tasks changed
    if set(day1_tasks) == set(day7_tasks):
        print("⚠️  IDENTICAL TASKS (no evolution)")
    else:
        print("✅ TASKS EVOLVED")

    # Show difference
    only_day1 = set(day1_tasks) - set(day7_tasks)
    only_day7 = set(day7_tasks) - set(day1_tasks)

    if only_day1:
        print(f"\nRemoved from Day 7:")
        for task in list(only_day1)[:3]:
            print(f"  - {task}")

    if only_day7:
        print(f"\nAdded in Day 7:")
        for task in list(only_day7)[:3]:
            print(f"  + {task}")

    print()

# SECTION 6: Final Verdict
print("="*80)
print("FINAL VERDICT")
print("="*80)

print("\n🎯 EXPECTED BEHAVIOR:")
print("  1. High-friction categories should SIMPLIFY (not exclude)")
print("  2. Low-friction categories should be used as ANCHORS")
print("  3. Tasks should EVOLVE from Day 1 to Day 7")
print("  4. All essential categories should remain present")

print("\n📊 ACTUAL RESULTS:")

# Check 1: Are high-friction categories present in Day 7?
day7_categories = set(item.get('category') for item in day7_items.data if item.get('category'))

missing_high_friction = [cat for cat in high_friction_categories if cat not in day7_categories and cat != 'NULL']

if missing_high_friction:
    print(f"  ❌ FAIL: High-friction categories MISSING from Day 7: {missing_high_friction}")
    print(f"     These should be SIMPLIFIED, not EXCLUDED!")
else:
    print(f"  ✅ PASS: All high-friction categories present in Day 7")

# Check 2: Are low-friction categories present as anchors?
missing_low_friction = [cat for cat in low_friction_categories if cat not in day7_categories and cat != 'NULL']

if missing_low_friction:
    print(f"  ⚠️  WARNING: Low-friction anchors missing: {missing_low_friction}")
else:
    print(f"  ✅ PASS: Low-friction anchors maintained")

# Check 3: Did tasks evolve?
unchanged_categories = []
for cat in all_categories:
    if cat != 'NULL':
        day1_tasks = set(day1_by_cat.get(cat, []))
        day7_tasks = set(day7_by_cat.get(cat, []))
        if day1_tasks == day7_tasks and day1_tasks:
            unchanged_categories.append(cat)

if unchanged_categories:
    print(f"  ⚠️  WARNING: {len(unchanged_categories)} categories unchanged: {unchanged_categories}")
    print(f"     System may not be adapting to feedback")
else:
    print(f"  ✅ PASS: Tasks evolved across all categories")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)
