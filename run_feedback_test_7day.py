#!/usr/bin/env python3
"""
7-Day Friction-Reduction Feedback Test with Preference Variations
=================================================================

Simulates a full week of user feedback + varying user preferences:

PREFERENCE VARIATIONS (simulating quiz changes):
- Day 1: Morning person (wake 6AM), hydration+movement goals
- Day 2: Evening person (wake 8AM), nutrition+sleep, evening workouts
- Day 3: Flexible schedule (wake 7AM), recovery focus
- Day 4: Morning routine (wake 6:30AM), stress+mindfulness focus
- Day 5: Balanced schedule (wake 7:30AM), all core goals
- Day 6: Night owl (wake 8:30AM), evening workouts
- Day 7: Optimized (wake 6:30AM), all goals integrated

FEEDBACK EVOLUTION:
- Day 1: Cold start (no feedback)
- Day 2: Positive feedback (loves movement/hydration)
- Day 3: Continue positive (building on success)
- Day 4: Introduce high friction (nutrition becomes difficult)
- Day 5: High friction continues (stress added)
- Day 6: Mixed feedback (some improvements)
- Day 7: Final adapted plan (full learning + preferences)

TESTS:
- Progressive adaptation over time
- Friction-reduction strategies compounding
- All categories maintained (no exclusion)
- Task complexity evolution (simplification for high-friction)
- Preference adherence (workout timing, goal prioritization)

Usage:
    python run_feedback_test_7day.py
"""

import os
import sys

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run the extended test
sys.path.insert(0, os.getcwd())

if __name__ == "__main__":
    import asyncio
    from testing.test_feedback_7day import run_7day_test

    asyncio.run(run_7day_test())
