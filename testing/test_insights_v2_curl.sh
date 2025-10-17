#!/bin/bash

# Quick curl tests for Insights V2 API
# Usage: bash testing/test_insights_v2_curl.sh

BASE_URL="http://localhost:8002"
API_KEY="hosa_flutter_app_2024"
USER_ID="fc65e36e-00f8-448c-9ef4-4d53994d5e48"

echo "=========================================="
echo "  Insights V2 - Quick Curl Tests"
echo "=========================================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "--------------------"
curl -s "$BASE_URL/api/v2/insights/health" | python -m json.tool
echo ""
echo ""

# Test 2: Generate Insights - Foundation Builder
echo "Test 2: Generate Insights (Foundation Builder)"
echo "----------------------------------------------"
curl -s -X POST "$BASE_URL/api/v2/insights/$USER_ID/generate" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "archetype": "Foundation Builder",
    "timeframe_days": 3,
    "force_refresh": false
  }' | python -m json.tool
echo ""
echo ""

# Test 3: Generate Insights - Peak Performer
echo "Test 3: Generate Insights (Peak Performer)"
echo "------------------------------------------"
curl -s -X POST "$BASE_URL/api/v2/insights/$USER_ID/generate" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "archetype": "Peak Performer",
    "timeframe_days": 7,
    "force_refresh": true
  }' | python -m json.tool
echo ""
echo ""

# Test 4: Invalid API Key (should fail with 401)
echo "Test 4: Invalid API Key (Should Return 401)"
echo "-------------------------------------------"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$BASE_URL/api/v2/insights/$USER_ID/generate" \
  -H "X-API-Key: invalid_key" \
  -H "Content-Type: application/json" \
  -d '{
    "archetype": "Foundation Builder",
    "timeframe_days": 3
  }' | python -m json.tool
echo ""
echo ""

# Test 5: Get Latest Insights (not yet implemented)
echo "Test 5: Get Latest Insights (Not Yet Implemented)"
echo "-------------------------------------------------"
curl -s "$BASE_URL/api/v2/insights/$USER_ID/latest" | python -m json.tool
echo ""
echo ""

echo "=========================================="
echo "  Tests Complete"
echo "=========================================="
