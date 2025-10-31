#!/usr/bin/env python3
"""
Populate Missing Task Library Categories
Adds tasks for: mindfulness, stress_management, sleep, breathing, focus
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import uuid

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Default archetype fit (balanced for all archetypes)
DEFAULT_ARCHETYPE_FIT = {
    "peak_performer": 0.8,
    "connected_explorer": 0.75,
    "foundation_builder": 0.85,
    "systematic_improver": 0.8,
    "resilience_rebuilder": 0.85,
    "transformation_seeker": 0.8
}

# Default mode fit
DEFAULT_MODE_FIT = {
    "low": 0.9,
    "high": 0.8,
    "medium": 0.85
}

# Tasks to populate
TASKS = [
    # === MINDFULNESS ===
    {
        "category": "mindfulness",
        "subcategory": "meditation",
        "name": "Morning Mindfulness",
        "description": "5-minute guided meditation to start your day with clarity and calm.",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "systematic_improver": 0.9,
            "resilience_rebuilder": 0.95
        },
        "mode_fit": DEFAULT_MODE_FIT,
        "tags": ["morning", "meditation", "mental_clarity"],
        "variation_group": "mindfulness_practices",
        "time_of_day_preference": "morning"
    },
    {
        "category": "mindfulness",
        "subcategory": "gratitude",
        "name": "Gratitude Reflection",
        "description": "Write down 3 things you're grateful for to boost mood and perspective.",
        "duration_minutes": 3,
        "difficulty": "easy",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "connected_explorer": 0.9
        },
        "mode_fit": DEFAULT_MODE_FIT,
        "tags": ["evening", "gratitude", "journaling"],
        "variation_group": "mindfulness_practices",
        "time_of_day_preference": "evening"
    },
    {
        "category": "mindfulness",
        "subcategory": "meditation",
        "name": "Body Scan Meditation",
        "description": "10-minute body scan to release tension and increase body awareness.",
        "duration_minutes": 10,
        "difficulty": "medium",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "resilience_rebuilder": 0.95,
            "peak_performer": 0.75
        },
        "mode_fit": {"low": 0.95, "high": 0.7, "medium": 0.85},
        "tags": ["relaxation", "body_awareness", "stress_relief"],
        "variation_group": "mindfulness_practices",
        "time_of_day_preference": "any"
    },

    # === STRESS MANAGEMENT ===
    {
        "category": "stress_management",
        "subcategory": "relaxation",
        "name": "Progressive Muscle Relaxation",
        "description": "Systematically tense and relax muscle groups to release physical stress.",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "resilience_rebuilder": 0.95,
            "systematic_improver": 0.9
        },
        "mode_fit": {"low": 0.95, "high": 0.7, "medium": 0.85},
        "tags": ["relaxation", "stress_relief", "body_awareness"],
        "variation_group": "stress_relief",
        "time_of_day_preference": "evening"
    },
    {
        "category": "stress_management",
        "subcategory": "mindset",
        "name": "Stress Journal",
        "description": "Write down what's stressing you and one action to address it.",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "systematic_improver": 0.95
        },
        "mode_fit": DEFAULT_MODE_FIT,
        "tags": ["journaling", "stress_relief", "problem_solving"],
        "variation_group": "stress_relief",
        "time_of_day_preference": "any"
    },
    {
        "category": "stress_management",
        "subcategory": "movement",
        "name": "Stress Relief Walk",
        "description": "10-minute walk outdoors to clear your mind and reduce cortisol.",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "connected_explorer": 0.9
        },
        "mode_fit": DEFAULT_MODE_FIT,
        "tags": ["outdoor", "movement", "stress_relief"],
        "variation_group": "stress_relief",
        "time_of_day_preference": "any"
    },

    # === SLEEP ===
    {
        "category": "sleep",
        "subcategory": "wind_down",
        "name": "Evening Wind-Down Routine",
        "description": "Dim lights, no screens for 30min before bed - prep your body for sleep.",
        "duration_minutes": 30,
        "difficulty": "medium",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "resilience_rebuilder": 0.95,
            "foundation_builder": 0.9
        },
        "mode_fit": {"low": 0.95, "high": 0.7, "medium": 0.85},
        "tags": ["evening", "sleep_hygiene", "routine"],
        "variation_group": "sleep_prep",
        "time_of_day_preference": "evening"
    },
    {
        "category": "sleep",
        "subcategory": "hygiene",
        "name": "Bedroom Temperature Check",
        "description": "Set room to 65-68°F for optimal sleep quality.",
        "duration_minutes": 2,
        "difficulty": "easy",
        "archetype_fit": DEFAULT_ARCHETYPE_FIT,
        "mode_fit": DEFAULT_MODE_FIT,
        "tags": ["sleep_hygiene", "environment"],
        "variation_group": "sleep_prep",
        "time_of_day_preference": "evening"
    },
    {
        "category": "sleep",
        "subcategory": "relaxation",
        "name": "Sleep Meditation",
        "description": "10-minute guided meditation designed to help you fall asleep faster.",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "resilience_rebuilder": 0.95
        },
        "mode_fit": {"low": 0.95, "high": 0.8, "medium": 0.9},
        "tags": ["evening", "meditation", "sleep_aid"],
        "variation_group": "sleep_prep",
        "time_of_day_preference": "evening"
    },

    # === BREATHING ===
    {
        "category": "breathing",
        "subcategory": "calm",
        "name": "Box Breathing",
        "description": "4-4-4-4 breathing pattern to calm your nervous system in 5 minutes.",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "peak_performer": 0.9,
            "resilience_rebuilder": 0.95
        },
        "mode_fit": DEFAULT_MODE_FIT,
        "tags": ["stress_relief", "quick", "calm"],
        "variation_group": "breathing_exercises",
        "time_of_day_preference": "any"
    },
    {
        "category": "breathing",
        "subcategory": "energy",
        "name": "Energizing Breath Work",
        "description": "Kapalabhati breathing (breath of fire) to boost energy and focus.",
        "duration_minutes": 5,
        "difficulty": "medium",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "peak_performer": 0.95,
            "transformation_seeker": 0.9
        },
        "mode_fit": {"low": 0.7, "high": 0.95, "medium": 0.85},
        "tags": ["morning", "energy", "focus"],
        "variation_group": "breathing_exercises",
        "time_of_day_preference": "morning"
    },
    {
        "category": "breathing",
        "subcategory": "calm",
        "name": "4-7-8 Relaxation Breath",
        "description": "Dr. Weil's 4-7-8 technique to reduce anxiety and promote relaxation.",
        "duration_minutes": 3,
        "difficulty": "easy",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "resilience_rebuilder": 0.95
        },
        "mode_fit": {"low": 0.95, "high": 0.75, "medium": 0.85},
        "tags": ["anxiety_relief", "quick", "calm"],
        "variation_group": "breathing_exercises",
        "time_of_day_preference": "any"
    },

    # === FOCUS ===
    {
        "category": "focus",
        "subcategory": "deep_work",
        "name": "Pomodoro Focus Session",
        "description": "25-minute deep work block with zero distractions - one task only.",
        "duration_minutes": 25,
        "difficulty": "medium",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "peak_performer": 0.95,
            "systematic_improver": 0.95
        },
        "mode_fit": {"low": 0.7, "high": 0.95, "medium": 0.85},
        "tags": ["productivity", "deep_work", "focus"],
        "variation_group": "focus_techniques",
        "time_of_day_preference": "morning"
    },
    {
        "category": "focus",
        "subcategory": "planning",
        "name": "Daily Priority Setting",
        "description": "5-minute session to identify your top 3 priorities for the day.",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "systematic_improver": 0.95,
            "peak_performer": 0.9
        },
        "mode_fit": DEFAULT_MODE_FIT,
        "tags": ["morning", "planning", "productivity"],
        "variation_group": "focus_techniques",
        "time_of_day_preference": "morning"
    },
    {
        "category": "focus",
        "subcategory": "environment",
        "name": "Distraction-Free Setup",
        "description": "Clear workspace, phone in drawer, close unnecessary tabs - prep for focus.",
        "duration_minutes": 3,
        "difficulty": "easy",
        "archetype_fit": {
            **DEFAULT_ARCHETYPE_FIT,
            "systematic_improver": 0.9
        },
        "mode_fit": DEFAULT_MODE_FIT,
        "tags": ["productivity", "environment", "quick"],
        "variation_group": "focus_techniques",
        "time_of_day_preference": "any"
    },
]


def main():
    """Populate task library with missing category tasks."""

    print("="*80)
    print("POPULATING TASK LIBRARY - MISSING CATEGORIES")
    print("="*80)
    print()

    # Check existing tasks
    print("📊 Current Task Library Status:")
    print("-"*80)

    categories = ['mindfulness', 'stress_management', 'sleep', 'breathing', 'focus']
    existing_counts = {}

    for category in categories:
        result = supabase.table('task_library').select('id').eq('category', category).eq('is_active', True).execute()
        count = len(result.data)
        existing_counts[category] = count
        print(f"  {category:20} → {count:2} tasks")

    print()

    # Insert tasks
    print(f"📝 Inserting {len(TASKS)} new tasks...")
    print("-"*80)

    inserted_count = 0
    for task in TASKS:
        try:
            # Add timestamps and active status
            task['is_active'] = True

            # Insert task
            result = supabase.table('task_library').insert(task).execute()

            if result.data:
                inserted_count += 1
                print(f"  ✅ {task['category']:20} → {task['name']}")
            else:
                print(f"  ❌ {task['category']:20} → {task['name']} (failed)")

        except Exception as e:
            print(f"  ❌ {task['category']:20} → {task['name']}")
            print(f"     Error: {str(e)}")

    print()
    print("="*80)
    print(f"✅ COMPLETED: Inserted {inserted_count}/{len(TASKS)} tasks")
    print("="*80)
    print()

    # Verify final counts
    print("📊 Updated Task Library Status:")
    print("-"*80)

    for category in categories:
        result = supabase.table('task_library').select('id').eq('category', category).eq('is_active', True).execute()
        count = len(result.data)
        delta = count - existing_counts[category]
        print(f"  {category:20} → {count:2} tasks (+{delta})")

    print()


if __name__ == "__main__":
    main()
