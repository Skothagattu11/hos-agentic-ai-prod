#!/bin/bash

# Schedule Anchoring Test Runner
# Runs the schedule anchoring integration test

echo "🚀 Starting Schedule Anchoring Test..."
echo ""

# Check if user_id is provided
if [ -z "$1" ]; then
    echo "Usage: ./run_schedule_anchoring_test.sh <user_id>"
    echo ""
    echo "Example:"
    echo "  ./run_schedule_anchoring_test.sh test-user-123"
    echo ""
    echo "If you don't have a user_id, you can use a test one:"
    echo "  ./run_schedule_anchoring_test.sh $(uuidgen)"
    exit 1
fi

USER_ID=$1

echo "📋 Test Configuration:"
echo "   User ID: $USER_ID"
echo "   Date: $(date +%Y-%m-%d)"
echo ""

# Run the test
python testing/test_schedule_anchoring.py "$USER_ID"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ Test completed successfully!"
else
    echo ""
    echo "❌ Test failed with exit code: $exit_code"
fi

exit $exit_code
