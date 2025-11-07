#!/bin/bash

# Test All Calendar Scenarios
# Runs demo_anchoring.py with 4 different calendar scenarios

set -e

ANALYSIS_ID="$1"
USER_ID="$2"

if [ -z "$ANALYSIS_ID" ] || [ -z "$USER_ID" ]; then
    echo "Usage: bash testing/test_all_calendar_scenarios.sh <analysis_result_id> <user_id>"
    echo ""
    echo "Example:"
    echo "  bash testing/test_all_calendar_scenarios.sh d8fe057d-fe02-4547-b7f2-f4884e424544 a57f70b4-d0a4-4aef-b721-a4b526f64869"
    exit 1
fi

echo "=========================================="
echo " TESTING 4 CALENDAR SCENARIOS"
echo "=========================================="
echo "Analysis ID: $ANALYSIS_ID"
echo "User ID: $USER_ID"
echo ""

# Scenario 1: Busy Professional
echo ""
echo "=========================================="
echo " SCENARIO 1: Busy Professional"
echo "=========================================="
python testing/demo_anchoring.py "$ANALYSIS_ID" "$USER_ID" true true busy_professional

# Scenario 2: Parent Schedule
echo ""
echo "=========================================="
echo " SCENARIO 2: Parent Schedule"
echo "=========================================="
python testing/demo_anchoring.py "$ANALYSIS_ID" "$USER_ID" true true parent_schedule

# Scenario 3: Long Commuter
echo ""
echo "=========================================="
echo " SCENARIO 3: Long Commuter"
echo "=========================================="
python testing/demo_anchoring.py "$ANALYSIS_ID" "$USER_ID" true true long_commuter

# Scenario 4: Flexible Remote
echo ""
echo "=========================================="
echo " SCENARIO 4: Flexible Remote Worker"
echo "=========================================="
python testing/demo_anchoring.py "$ANALYSIS_ID" "$USER_ID" true true flexible_remote

echo ""
echo "=========================================="
echo " ALL 4 SCENARIOS COMPLETE!"
echo "=========================================="
