#!/usr/bin/env python3
"""
Task Library Cleanup and Replacement
=====================================

Purpose: Replace specific food/supplement tasks with generic, safety-compliant alternatives

Safety Rules:
- ❌ NO specific foods (avocado, salmon, berries, etc.)
- ❌ NO specific beverages (green tea, coconut water, etc.)
- ❌ NO supplements or medications
- ❌ NO temperature specifications (65-68°F)
- ✅ ONLY generic terms (meal, snack, beverage, hydration)

Usage:
    python cleanup_task_library.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Generic, safe task definitions
SAFE_TASKS = [
    # ================================================================
    # HYDRATION (6 tasks) - Generic beverages only
    # ================================================================
    {
        "name": "Morning Hydration",
        "category": "hydration",
        "subcategory": "water",
        "description": "Start your day with water upon waking",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.95, "peak_performer": 0.9, "connected_explorer": 0.85, "systematic_improver": 0.9, "resilience_rebuilder": 0.9, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.95, "medium": 0.9, "high": 0.85}',
        "tags": '["morning", "hydration", "routine"]',
        "variation_group": "hydration_basic",
        "time_of_day_preference": "morning",
        "is_active": True
    },
    {
        "name": "Hydration Break",
        "category": "hydration",
        "subcategory": "water",
        "description": "Take a hydration break during your day",
        "duration_minutes": 3,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.9, "peak_performer": 0.85, "connected_explorer": 0.8, "systematic_improver": 0.85, "resilience_rebuilder": 0.9, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.9, "medium": 0.85, "high": 0.8}',
        "tags": '["hydration", "break", "wellness"]',
        "variation_group": "hydration_basic",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Pre-Activity Hydration",
        "category": "hydration",
        "subcategory": "water",
        "description": "Hydrate before physical activity",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.95, "connected_explorer": 0.85, "systematic_improver": 0.9, "resilience_rebuilder": 0.85, "transformation_seeker": 0.9}',
        "mode_fit": '{"low": 0.7, "medium": 0.85, "high": 0.95}',
        "tags": '["hydration", "exercise", "preparation"]',
        "variation_group": "hydration_exercise",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Afternoon Hydration",
        "category": "hydration",
        "subcategory": "water",
        "description": "Midday hydration checkpoint",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.8, "connected_explorer": 0.75, "systematic_improver": 0.9, "resilience_rebuilder": 0.85, "transformation_seeker": 0.75}',
        "mode_fit": '{"low": 0.85, "medium": 0.9, "high": 0.8}',
        "tags": '["afternoon", "hydration", "check_in"]',
        "variation_group": "hydration_basic",
        "time_of_day_preference": "afternoon",
        "is_active": True
    },
    {
        "name": "Evening Hydration",
        "category": "hydration",
        "subcategory": "water",
        "description": "Evening hydration before winding down",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.9, "peak_performer": 0.75, "connected_explorer": 0.8, "systematic_improver": 0.85, "resilience_rebuilder": 0.9, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.95, "medium": 0.85, "high": 0.7}',
        "tags": '["evening", "hydration", "routine"]',
        "variation_group": "hydration_basic",
        "time_of_day_preference": "evening",
        "is_active": True
    },
    {
        "name": "Herbal Beverage",
        "category": "hydration",
        "subcategory": "beverage",
        "description": "Enjoy a warm herbal beverage for relaxation",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.9, "peak_performer": 0.7, "connected_explorer": 0.8, "systematic_improver": 0.85, "resilience_rebuilder": 0.95, "transformation_seeker": 0.75}',
        "mode_fit": '{"low": 0.95, "medium": 0.75, "high": 0.6}',
        "tags": '["relaxation", "sleep_prep", "calming"]',
        "variation_group": "hydration_evening",
        "time_of_day_preference": "evening",
        "is_active": True
    },

    # ================================================================
    # NUTRITION (8 tasks) - Generic meal/snack terms only
    # ================================================================
    {
        "name": "Morning Meal",
        "category": "nutrition",
        "subcategory": "breakfast",
        "description": "Start your day with a balanced meal",
        "duration_minutes": 20,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.95, "peak_performer": 0.9, "connected_explorer": 0.85, "systematic_improver": 0.9, "resilience_rebuilder": 0.9, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.85, "medium": 0.9, "high": 0.95}',
        "tags": '["morning", "nutrition", "meal"]',
        "variation_group": "nutrition_meals",
        "time_of_day_preference": "morning",
        "is_active": True
    },
    {
        "name": "Mid-Morning Snack",
        "category": "nutrition",
        "subcategory": "snack",
        "description": "Have a healthy mid-morning snack",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.85, "connected_explorer": 0.75, "systematic_improver": 0.8, "resilience_rebuilder": 0.75, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.7, "medium": 0.85, "high": 0.9}',
        "tags": '["morning", "nutrition", "snack"]',
        "variation_group": "nutrition_snacks",
        "time_of_day_preference": "morning",
        "is_active": True
    },
    {
        "name": "Lunch Break",
        "category": "nutrition",
        "subcategory": "lunch",
        "description": "Take time for a proper lunch",
        "duration_minutes": 30,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.95, "peak_performer": 0.9, "connected_explorer": 0.9, "systematic_improver": 0.9, "resilience_rebuilder": 0.9, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.9, "medium": 0.9, "high": 0.85}',
        "tags": '["afternoon", "nutrition", "meal", "break"]',
        "variation_group": "nutrition_meals",
        "time_of_day_preference": "afternoon",
        "is_active": True
    },
    {
        "name": "Afternoon Snack",
        "category": "nutrition",
        "subcategory": "snack",
        "description": "Healthy afternoon snack for sustained energy",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.9, "connected_explorer": 0.8, "systematic_improver": 0.85, "resilience_rebuilder": 0.8, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.75, "medium": 0.85, "high": 0.95}',
        "tags": '["afternoon", "nutrition", "snack", "energy"]',
        "variation_group": "nutrition_snacks",
        "time_of_day_preference": "afternoon",
        "is_active": True
    },
    {
        "name": "Evening Meal",
        "category": "nutrition",
        "subcategory": "dinner",
        "description": "Evening meal to nourish and satisfy",
        "duration_minutes": 30,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.95, "peak_performer": 0.85, "connected_explorer": 0.9, "systematic_improver": 0.9, "resilience_rebuilder": 0.9, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.9, "medium": 0.9, "high": 0.8}',
        "tags": '["evening", "nutrition", "meal"]',
        "variation_group": "nutrition_meals",
        "time_of_day_preference": "evening",
        "is_active": True
    },
    {
        "name": "Meal Planning",
        "category": "nutrition",
        "subcategory": "planning",
        "description": "Plan meals for the day or week ahead",
        "duration_minutes": 15,
        "difficulty": "moderate",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.85, "connected_explorer": 0.7, "systematic_improver": 0.95, "resilience_rebuilder": 0.75, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.7, "medium": 0.85, "high": 0.9}',
        "tags": '["planning", "nutrition", "preparation"]',
        "variation_group": "nutrition_planning",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Mindful Eating",
        "category": "nutrition",
        "subcategory": "mindfulness",
        "description": "Practice eating slowly and mindfully",
        "duration_minutes": 20,
        "difficulty": "moderate",
        "archetype_fit": '{"foundation_builder": 0.75, "peak_performer": 0.7, "connected_explorer": 0.8, "systematic_improver": 0.8, "resilience_rebuilder": 0.85, "transformation_seeker": 0.75}',
        "mode_fit": '{"low": 0.9, "medium": 0.8, "high": 0.6}',
        "tags": '["mindfulness", "nutrition", "awareness"]',
        "variation_group": "nutrition_mindful",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Nutrition Journaling",
        "category": "nutrition",
        "subcategory": "tracking",
        "description": "Log meals and nutrition awareness",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.7, "peak_performer": 0.85, "connected_explorer": 0.65, "systematic_improver": 0.95, "resilience_rebuilder": 0.7, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.6, "medium": 0.8, "high": 0.9}',
        "tags": '["tracking", "nutrition", "awareness"]',
        "variation_group": "nutrition_awareness",
        "time_of_day_preference": "any",
        "is_active": True
    },

    # ================================================================
    # MOVEMENT (10 tasks)
    # ================================================================
    {
        "name": "Morning Stretch",
        "category": "movement",
        "subcategory": "stretch",
        "description": "Gentle morning stretching to wake up your body",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.9, "peak_performer": 0.85, "connected_explorer": 0.8, "systematic_improver": 0.85, "resilience_rebuilder": 0.95, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.95, "medium": 0.9, "high": 0.8}',
        "tags": '["morning", "movement", "stretch", "gentle"]',
        "variation_group": "movement_light",
        "time_of_day_preference": "morning",
        "is_active": True
    },
    {
        "name": "Quick Walk",
        "category": "movement",
        "subcategory": "walking",
        "description": "Take a quick walk to move your body",
        "duration_minutes": 15,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.95, "peak_performer": 0.8, "connected_explorer": 0.9, "systematic_improver": 0.85, "resilience_rebuilder": 0.9, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.85, "medium": 0.9, "high": 0.75}',
        "tags": '["walking", "movement", "cardio", "outdoor"]',
        "variation_group": "movement_cardio",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Cardio Session",
        "category": "movement",
        "subcategory": "cardio",
        "description": "Cardiovascular exercise for heart health",
        "duration_minutes": 30,
        "difficulty": "moderate",
        "archetype_fit": '{"foundation_builder": 0.7, "peak_performer": 0.95, "connected_explorer": 0.85, "systematic_improver": 0.8, "resilience_rebuilder": 0.75, "transformation_seeker": 0.9}',
        "mode_fit": '{"low": 0.6, "medium": 0.8, "high": 0.95}',
        "tags": '["cardio", "movement", "exercise", "heart"]',
        "variation_group": "movement_cardio",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Strength Training",
        "category": "movement",
        "subcategory": "strength",
        "description": "Bodyweight or resistance training session",
        "duration_minutes": 40,
        "difficulty": "moderate",
        "archetype_fit": '{"foundation_builder": 0.75, "peak_performer": 0.95, "connected_explorer": 0.8, "systematic_improver": 0.85, "resilience_rebuilder": 0.8, "transformation_seeker": 0.9}',
        "mode_fit": '{"low": 0.65, "medium": 0.85, "high": 0.95}',
        "tags": '["strength", "movement", "resistance", "training"]',
        "variation_group": "movement_strength",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Flexibility Work",
        "category": "movement",
        "subcategory": "flexibility",
        "description": "Dedicated flexibility and mobility practice",
        "duration_minutes": 20,
        "difficulty": "moderate",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.85, "connected_explorer": 0.75, "systematic_improver": 0.8, "resilience_rebuilder": 0.95, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.85, "medium": 0.85, "high": 0.75}',
        "tags": '["flexibility", "movement", "mobility", "stretch"]',
        "variation_group": "movement_flexibility",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Movement Break",
        "category": "movement",
        "subcategory": "break",
        "description": "Short movement break to counter sitting",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.9, "connected_explorer": 0.8, "systematic_improver": 0.9, "resilience_rebuilder": 0.85, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.8, "medium": 0.9, "high": 0.85}',
        "tags": '["break", "movement", "quick", "desk"]',
        "variation_group": "movement_light",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Evening Walk",
        "category": "movement",
        "subcategory": "walking",
        "description": "Relaxing evening walk to decompress",
        "duration_minutes": 20,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.9, "peak_performer": 0.75, "connected_explorer": 0.95, "systematic_improver": 0.8, "resilience_rebuilder": 0.9, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.95, "medium": 0.85, "high": 0.7}',
        "tags": '["evening", "walking", "movement", "relaxation"]',
        "variation_group": "movement_cardio",
        "time_of_day_preference": "evening",
        "is_active": True
    },
    {
        "name": "Active Recovery",
        "category": "movement",
        "subcategory": "recovery",
        "description": "Light movement for active recovery",
        "duration_minutes": 15,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.85, "connected_explorer": 0.75, "systematic_improver": 0.8, "resilience_rebuilder": 0.95, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.95, "medium": 0.85, "high": 0.75}',
        "tags": '["recovery", "movement", "gentle", "restoration"]',
        "variation_group": "movement_recovery",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Yoga Practice",
        "category": "movement",
        "subcategory": "yoga",
        "description": "Yoga session for flexibility and balance",
        "duration_minutes": 30,
        "difficulty": "moderate",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.8, "connected_explorer": 0.85, "systematic_improver": 0.85, "resilience_rebuilder": 0.95, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.9, "medium": 0.85, "high": 0.75}',
        "tags": '["yoga", "flexibility", "balance", "mindful"]',
        "variation_group": "movement_yoga",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "High Intensity Workout",
        "category": "movement",
        "subcategory": "hiit",
        "description": "High-intensity interval training session",
        "duration_minutes": 20,
        "difficulty": "challenging",
        "archetype_fit": '{"foundation_builder": 0.6, "peak_performer": 0.95, "connected_explorer": 0.8, "systematic_improver": 0.85, "resilience_rebuilder": 0.7, "transformation_seeker": 0.95}',
        "mode_fit": '{"low": 0.5, "medium": 0.8, "high": 0.95}',
        "tags": '["hiit", "intensity", "cardio", "efficiency"]',
        "variation_group": "movement_intense",
        "time_of_day_preference": "morning",
        "is_active": True
    },

    # ================================================================
    # MINDFULNESS (6 tasks)
    # ================================================================
    {
        "name": "Morning Mindfulness Practice",
        "category": "mindfulness",
        "subcategory": "meditation",
        "description": "Start your day with mindful awareness",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.8, "connected_explorer": 0.8, "systematic_improver": 0.9, "resilience_rebuilder": 0.95, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.9, "medium": 0.85, "high": 0.75}',
        "tags": '["morning", "meditation", "mindfulness", "awareness"]',
        "variation_group": "mindfulness_meditation",
        "time_of_day_preference": "morning",
        "is_active": True
    },
    {
        "name": "Gratitude Practice",
        "category": "mindfulness",
        "subcategory": "gratitude",
        "description": "Reflect on things you're grateful for",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.75, "connected_explorer": 0.9, "systematic_improver": 0.8, "resilience_rebuilder": 0.9, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.9, "medium": 0.85, "high": 0.75}',
        "tags": '["gratitude", "mindfulness", "reflection", "positivity"]',
        "variation_group": "mindfulness_reflection",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Midday Pause",
        "category": "mindfulness",
        "subcategory": "meditation",
        "description": "Brief midday pause for presence",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.85, "connected_explorer": 0.75, "systematic_improver": 0.85, "resilience_rebuilder": 0.85, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.85, "medium": 0.9, "high": 0.8}',
        "tags": '["afternoon", "mindfulness", "break", "presence"]',
        "variation_group": "mindfulness_meditation",
        "time_of_day_preference": "afternoon",
        "is_active": True
    },
    {
        "name": "Body Awareness",
        "category": "mindfulness",
        "subcategory": "body_scan",
        "description": "Progressive body awareness meditation",
        "duration_minutes": 15,
        "difficulty": "moderate",
        "archetype_fit": '{"foundation_builder": 0.75, "peak_performer": 0.75, "connected_explorer": 0.7, "systematic_improver": 0.8, "resilience_rebuilder": 0.95, "transformation_seeker": 0.75}',
        "mode_fit": '{"low": 0.95, "medium": 0.8, "high": 0.65}',
        "tags": '["meditation", "mindfulness", "body_awareness", "relaxation"]',
        "variation_group": "mindfulness_meditation",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Journaling Session",
        "category": "mindfulness",
        "subcategory": "journaling",
        "description": "Reflective writing for clarity and insight",
        "duration_minutes": 15,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.75, "connected_explorer": 0.85, "systematic_improver": 0.9, "resilience_rebuilder": 0.85, "transformation_seeker": 0.9}',
        "mode_fit": '{"low": 0.85, "medium": 0.85, "high": 0.8}',
        "tags": '["journaling", "mindfulness", "reflection", "writing"]',
        "variation_group": "mindfulness_reflection",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Evening Reflection",
        "category": "mindfulness",
        "subcategory": "reflection",
        "description": "End-of-day reflection and review",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.8, "connected_explorer": 0.8, "systematic_improver": 0.95, "resilience_rebuilder": 0.85, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.9, "medium": 0.85, "high": 0.75}',
        "tags": '["evening", "reflection", "mindfulness", "review"]',
        "variation_group": "mindfulness_reflection",
        "time_of_day_preference": "evening",
        "is_active": True
    },

    # ================================================================
    # SLEEP (5 tasks) - NO temperature specifications
    # ================================================================
    {
        "name": "Sleep Routine",
        "category": "sleep",
        "subcategory": "preparation",
        "description": "Wind-down routine to prepare for rest",
        "duration_minutes": 30,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.95, "peak_performer": 0.85, "connected_explorer": 0.85, "systematic_improver": 0.9, "resilience_rebuilder": 0.95, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.95, "medium": 0.9, "high": 0.8}',
        "tags": '["evening", "sleep", "routine", "wind_down"]',
        "variation_group": "sleep_hygiene",
        "time_of_day_preference": "evening",
        "is_active": True
    },
    {
        "name": "Screen-Free Time",
        "category": "sleep",
        "subcategory": "hygiene",
        "description": "Device-free time before bed for better sleep",
        "duration_minutes": 60,
        "difficulty": "moderate",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.8, "connected_explorer": 0.75, "systematic_improver": 0.85, "resilience_rebuilder": 0.9, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.9, "medium": 0.85, "high": 0.75}',
        "tags": '["evening", "sleep", "hygiene", "screen_free"]',
        "variation_group": "sleep_hygiene",
        "time_of_day_preference": "evening",
        "is_active": True
    },
    {
        "name": "Sleep Environment",
        "category": "sleep",
        "subcategory": "environment",
        "description": "Optimize bedroom for quality sleep",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.9, "peak_performer": 0.85, "connected_explorer": 0.8, "systematic_improver": 0.95, "resilience_rebuilder": 0.9, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.9, "medium": 0.9, "high": 0.85}',
        "tags": '["evening", "sleep", "environment", "preparation"]',
        "variation_group": "sleep_hygiene",
        "time_of_day_preference": "evening",
        "is_active": True
    },
    {
        "name": "Bedtime Routine",
        "category": "sleep",
        "subcategory": "preparation",
        "description": "Consistent pre-sleep ritual for better rest",
        "duration_minutes": 15,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.95, "peak_performer": 0.85, "connected_explorer": 0.85, "systematic_improver": 0.9, "resilience_rebuilder": 0.95, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.95, "medium": 0.9, "high": 0.8}',
        "tags": '["evening", "sleep", "routine", "bedtime"]',
        "variation_group": "sleep_hygiene",
        "time_of_day_preference": "evening",
        "is_active": True
    },
    {
        "name": "Sleep Tracking",
        "category": "sleep",
        "subcategory": "tracking",
        "description": "Log sleep quality and duration",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.85, "connected_explorer": 0.7, "systematic_improver": 0.95, "resilience_rebuilder": 0.85, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.85, "medium": 0.85, "high": 0.9}',
        "tags": '["morning", "sleep", "tracking", "awareness"]',
        "variation_group": "sleep_awareness",
        "time_of_day_preference": "morning",
        "is_active": True
    },

    # ================================================================
    # STRESS MANAGEMENT (5 tasks)
    # ================================================================
    {
        "name": "Stress Check-In",
        "category": "stress_management",
        "subcategory": "awareness",
        "description": "Brief assessment of current stress levels",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.8, "connected_explorer": 0.75, "systematic_improver": 0.9, "resilience_rebuilder": 0.95, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.9, "medium": 0.85, "high": 0.8}',
        "tags": '["stress", "awareness", "check_in", "monitoring"]',
        "variation_group": "stress_awareness",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Relaxation Break",
        "category": "stress_management",
        "subcategory": "relaxation",
        "description": "Intentional relaxation to reduce tension",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.9, "peak_performer": 0.85, "connected_explorer": 0.85, "systematic_improver": 0.85, "resilience_rebuilder": 0.95, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.95, "medium": 0.9, "high": 0.8}',
        "tags": '["relaxation", "stress", "break", "calm"]',
        "variation_group": "stress_relief",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Stress Journaling",
        "category": "stress_management",
        "subcategory": "journaling",
        "description": "Write about stressors and coping strategies",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.75, "connected_explorer": 0.8, "systematic_improver": 0.95, "resilience_rebuilder": 0.9, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.85, "medium": 0.9, "high": 0.85}',
        "tags": '["journaling", "stress", "processing", "awareness"]',
        "variation_group": "stress_processing",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Nature Time",
        "category": "stress_management",
        "subcategory": "outdoor",
        "description": "Spend time in nature for stress relief",
        "duration_minutes": 15,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.8, "connected_explorer": 0.95, "systematic_improver": 0.8, "resilience_rebuilder": 0.9, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.9, "medium": 0.85, "high": 0.75}',
        "tags": '["nature", "stress", "outdoor", "relaxation"]',
        "variation_group": "stress_relief",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Progressive Muscle Relaxation",
        "category": "stress_management",
        "subcategory": "relaxation",
        "description": "Systematic muscle relaxation technique",
        "duration_minutes": 15,
        "difficulty": "moderate",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.75, "connected_explorer": 0.75, "systematic_improver": 0.85, "resilience_rebuilder": 0.95, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.95, "medium": 0.85, "high": 0.7}',
        "tags": '["relaxation", "stress", "technique", "body"]',
        "variation_group": "stress_relief",
        "time_of_day_preference": "any",
        "is_active": True
    },

    # ================================================================
    # BREATHING (4 tasks)
    # ================================================================
    {
        "name": "Box Breathing Practice",
        "category": "breathing",
        "subcategory": "technique",
        "description": "Calming breath pattern for nervous system regulation",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.9, "connected_explorer": 0.8, "systematic_improver": 0.85, "resilience_rebuilder": 0.95, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.9, "medium": 0.9, "high": 0.85}',
        "tags": '["breathing", "technique", "calm", "quick"]',
        "variation_group": "breathing_calm",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Deep Breathing",
        "category": "breathing",
        "subcategory": "technique",
        "description": "Extended deep breathing practice",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.9, "peak_performer": 0.85, "connected_explorer": 0.85, "systematic_improver": 0.85, "resilience_rebuilder": 0.95, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.95, "medium": 0.9, "high": 0.8}',
        "tags": '["breathing", "deep", "calm", "relaxation"]',
        "variation_group": "breathing_calm",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Energizing Breath",
        "category": "breathing",
        "subcategory": "technique",
        "description": "Breathing technique to boost energy",
        "duration_minutes": 5,
        "difficulty": "moderate",
        "archetype_fit": '{"foundation_builder": 0.7, "peak_performer": 0.95, "connected_explorer": 0.75, "systematic_improver": 0.8, "resilience_rebuilder": 0.75, "transformation_seeker": 0.9}',
        "mode_fit": '{"low": 0.6, "medium": 0.8, "high": 0.95}',
        "tags": '["breathing", "energy", "morning", "activation"]',
        "variation_group": "breathing_energy",
        "time_of_day_preference": "morning",
        "is_active": True
    },
    {
        "name": "Relaxation Breath",
        "category": "breathing",
        "subcategory": "technique",
        "description": "Breathing technique to reduce anxiety",
        "duration_minutes": 3,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.8, "connected_explorer": 0.75, "systematic_improver": 0.8, "resilience_rebuilder": 0.95, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.95, "medium": 0.85, "high": 0.75}',
        "tags": '["anxiety_relief", "quick", "calm", "breathing"]',
        "variation_group": "breathing_calm",
        "time_of_day_preference": "any",
        "is_active": True
    },

    # ================================================================
    # FOCUS (5 tasks)
    # ================================================================
    {
        "name": "Focus Session",
        "category": "focus",
        "subcategory": "deep_work",
        "description": "Dedicated time for focused work",
        "duration_minutes": 30,
        "difficulty": "moderate",
        "archetype_fit": '{"foundation_builder": 0.75, "peak_performer": 0.95, "connected_explorer": 0.7, "systematic_improver": 0.95, "resilience_rebuilder": 0.75, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.65, "medium": 0.85, "high": 0.95}',
        "tags": '["focus", "work", "deep_work", "productivity"]',
        "variation_group": "focus_work",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Priority Setting",
        "category": "focus",
        "subcategory": "planning",
        "description": "Identify and rank daily priorities",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.95, "connected_explorer": 0.75, "systematic_improver": 0.95, "resilience_rebuilder": 0.8, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.8, "medium": 0.9, "high": 0.95}',
        "tags": '["planning", "focus", "priorities", "morning"]',
        "variation_group": "focus_planning",
        "time_of_day_preference": "morning",
        "is_active": True
    },
    {
        "name": "Workspace Setup",
        "category": "focus",
        "subcategory": "environment",
        "description": "Prepare workspace for focused work",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.9, "connected_explorer": 0.7, "systematic_improver": 0.95, "resilience_rebuilder": 0.75, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.75, "medium": 0.85, "high": 0.9}',
        "tags": '["environment", "focus", "preparation", "workspace"]',
        "variation_group": "focus_preparation",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Focus Break",
        "category": "focus",
        "subcategory": "break",
        "description": "Short break to restore concentration",
        "duration_minutes": 5,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.9, "connected_explorer": 0.8, "systematic_improver": 0.85, "resilience_rebuilder": 0.85, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.85, "medium": 0.9, "high": 0.85}',
        "tags": '["break", "focus", "recovery", "rest"]',
        "variation_group": "focus_recovery",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Daily Review",
        "category": "focus",
        "subcategory": "reflection",
        "description": "Review accomplishments and plan ahead",
        "duration_minutes": 10,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.9, "connected_explorer": 0.8, "systematic_improver": 0.95, "resilience_rebuilder": 0.8, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.85, "medium": 0.9, "high": 0.85}',
        "tags": '["evening", "review", "reflection", "planning"]',
        "variation_group": "focus_planning",
        "time_of_day_preference": "evening",
        "is_active": True
    },

    # ================================================================
    # RECOVERY (3 tasks)
    # ================================================================
    {
        "name": "Rest Period",
        "category": "recovery",
        "subcategory": "rest",
        "description": "Intentional rest to recharge",
        "duration_minutes": 20,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.8, "connected_explorer": 0.8, "systematic_improver": 0.8, "resilience_rebuilder": 0.95, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.95, "medium": 0.85, "high": 0.75}',
        "tags": '["recovery", "rest", "recharge", "restoration"]',
        "variation_group": "recovery_rest",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Self-Care Activity",
        "category": "recovery",
        "subcategory": "self_care",
        "description": "Activity dedicated to self-care and renewal",
        "duration_minutes": 30,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.85, "peak_performer": 0.75, "connected_explorer": 0.85, "systematic_improver": 0.8, "resilience_rebuilder": 0.95, "transformation_seeker": 0.85}',
        "mode_fit": '{"low": 0.9, "medium": 0.85, "high": 0.75}',
        "tags": '["self_care", "recovery", "renewal", "wellness"]',
        "variation_group": "recovery_care",
        "time_of_day_preference": "any",
        "is_active": True
    },
    {
        "name": "Recovery Session",
        "category": "recovery",
        "subcategory": "stretching",
        "description": "Gentle stretching and recovery techniques",
        "duration_minutes": 15,
        "difficulty": "easy",
        "archetype_fit": '{"foundation_builder": 0.8, "peak_performer": 0.85, "connected_explorer": 0.75, "systematic_improver": 0.85, "resilience_rebuilder": 0.95, "transformation_seeker": 0.8}',
        "mode_fit": '{"low": 0.95, "medium": 0.85, "high": 0.75}',
        "tags": '["recovery", "stretching", "gentle", "restoration"]',
        "variation_group": "recovery_stretching",
        "time_of_day_preference": "any",
        "is_active": True
    },
]


def cleanup_and_populate():
    """Replace all existing tasks with generic, safe alternatives."""

    print("\n" + "=" * 80)
    print("  TASK LIBRARY CLEANUP AND REPLACEMENT")
    print("=" * 80)
    print()

    # Step 1: Count existing tasks
    result = supabase.table('task_library').select('id', count='exact').eq('is_active', True).execute()
    existing_count = result.count

    print(f"📊 Current Status:")
    print(f"   • Existing active tasks: {existing_count}")
    print()

    # Step 2: DELETE all existing tasks (to avoid unique constraint violations)
    print("🧹 Deleting all existing tasks...")

    # Get all task IDs (both active and inactive to clean everything)
    all_tasks = supabase.table('task_library').select('id').execute()

    if all_tasks.data:
        deleted_count = 0
        # Delete in batches
        for task in all_tasks.data:
            try:
                supabase.table('task_library').delete().eq('id', task['id']).execute()
                deleted_count += 1
            except Exception as e:
                print(f"   ⚠️  Could not delete task {task['id']}: {str(e)[:50]}")

        print(f"   ✅ Deleted {deleted_count} tasks (cleared database)")
    else:
        print("   ℹ️  No existing tasks found")
    print()

    # Step 3: Insert new safe tasks
    print(f"📝 Inserting {len(SAFE_TASKS)} new generic tasks...")
    print("-" * 80)

    inserted_count = 0
    for task in SAFE_TASKS:
        try:
            result = supabase.table('task_library').insert(task).execute()

            if result.data:
                inserted_count += 1
                task_name = result.data[0]['name']
                category = result.data[0]['category']
                print(f"  ✅ {category:20} → {task_name}")
        except Exception as e:
            print(f"  ❌ {task.get('category', 'unknown'):20} → {task.get('name', 'unknown')}")
            print(f"     Error: {str(e)[:100]}")

    print()
    print("=" * 80)
    print(f"✅ COMPLETED: {inserted_count}/{len(SAFE_TASKS)} tasks inserted")
    print("=" * 80)
    print()

    # Step 4: Verify final counts
    print("📊 Updated Task Library Status:")
    print("-" * 80)

    # Get all active tasks and count by category
    all_tasks = supabase.table('task_library').select('category').eq('is_active', True).execute()

    # Count by category manually
    category_counts = {}
    for task in all_tasks.data:
        cat = task['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1

    for category in sorted(category_counts.keys()):
        count = category_counts[category]
        print(f"  {category:20} → {count:2} tasks")

    # Total count
    total_count = len(all_tasks.data)

    print()
    print(f"  {'TOTAL':20} → {total_count:2} tasks")
    print()

    print("🎉 Task Library Cleanup Complete!")
    print()
    print("✅ Safety Compliance:")
    print("   • NO specific foods (avocado, salmon, berries, etc.)")
    print("   • NO specific beverages (green tea, coconut water, etc.)")
    print("   • NO supplements or medications")
    print("   • NO temperature specifications")
    print("   • ONLY generic terms (meal, snack, beverage, hydration)")
    print()


if __name__ == "__main__":
    cleanup_and_populate()
