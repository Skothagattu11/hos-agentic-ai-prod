#!/bin/bash

# ============================================================================
# Run Database Migration - Remove All Profile Dependencies
# ============================================================================

echo "========================================================================"
echo "Database Migration - Remove ALL Profile/User Dependencies"
echo "========================================================================"
echo ""
echo "This script will:"
echo "  1. Connect to your Supabase database"
echo "  2. Remove ALL foreign key constraints to profiles/users tables"
echo "  3. Add performance indexes"
echo "  4. Verify the migration succeeded"
echo ""
echo "Tables affected: biomarkers, scores, archetype_analysis_tracking,"
echo "                 plan_items, task_checkins, daily_journals,"
echo "                 time_blocks, calendar_selections"
echo ""
echo "========================================================================"
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded from .env"
else
    echo "❌ ERROR: .env file not found!"
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set in .env file!"
    exit 1
fi

echo "✅ DATABASE_URL found: ${DATABASE_URL:0:30}..."
echo ""
echo "========================================================================"
echo "Starting Migration..."
echo "========================================================================"
echo ""

# Run the migration
psql "$DATABASE_URL" -f migrations/FINAL_remove_all_profile_dependencies.sql

# Check if migration succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "✅ MIGRATION COMPLETED SUCCESSFULLY!"
    echo "========================================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Restart your server: python start_openai.py"
    echo "  2. Run tests: python testing/test_routine_generation_flow.py"
    echo "  3. Check CRITICAL_FIXES_SUMMARY.md for verification checklist"
    echo ""
else
    echo ""
    echo "========================================================================"
    echo "❌ MIGRATION FAILED!"
    echo "========================================================================"
    echo ""
    echo "Please check the error messages above and:"
    echo "  1. Verify DATABASE_URL is correct"
    echo "  2. Ensure you have database admin permissions"
    echo "  3. Check if psql is installed (command not found error)"
    echo ""
    echo "Alternative: Copy migrations/FINAL_remove_all_profile_dependencies.sql"
    echo "            and run it in Supabase SQL Editor manually"
    echo ""
    exit 1
fi
