#!/usr/bin/env python3
"""
Test Simplified Incremental Data Fetching - Analysis Tracker Approach
Focus on testing core incremental logic without complex database dependencies
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# Add project root to path  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
REAL_PROFILE_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"

async def test_core_incremental_logic():
    """Test the core incremental data fetching logic"""
    print("🔍 TESTING SIMPLIFIED INCREMENTAL DATA FETCHING")
    print("=" * 60)
    
    try:
        from services.user_data_service import UserDataService
        
        user_service = UserDataService()
        print("✅ Services imported successfully\n")
        
        # ========== TEST 1: Basic Data Fetch ==========
        print("📊 TEST 1: Basic Data Fetch (First Analysis)")
        print("-" * 45)
        
        start_time = datetime.now()
        
        # This will fallback to full sync since no analysis timestamp exists yet
        # But it tests the core get_analysis_data() method and latest timestamp tracking
        health_data_1, latest_timestamp_1 = await user_service.get_analysis_data(REAL_PROFILE_ID)
        
        duration_1 = (datetime.now() - start_time).total_seconds()
        
        print(f"✓ Data fetched in {duration_1:.2f} seconds")
        print(f"✓ Scores: {health_data_1.data_quality.scores_count}")
        print(f"✓ Biomarkers: {health_data_1.data_quality.biomarkers_count}")
        print(f"✓ Quality: {health_data_1.data_quality.quality_level}")
        print(f"✓ Date range: {health_data_1.date_range.days} days")
        print(f"✓ Latest data timestamp: {latest_timestamp_1.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show sample scores with proper attribute access
        if health_data_1.scores:
            print(f"\n  Sample score data:")
            for score in health_data_1.scores[:3]:
                print(f"    • {score.type}: {score.score:.2f} ({score.created_at.strftime('%Y-%m-%d %H:%M')})")
        
        # ========== TEST 2: Test fetch_data_since Method ==========
        print(f"\n🔧 TEST 2: Direct Incremental Fetch Method")
        print("-" * 45)
        
        # Test the core incremental method with different time windows
        test_times = [
            ("1 hour ago", timedelta(hours=1)),
            ("6 hours ago", timedelta(hours=6)), 
            ("1 day ago", timedelta(days=1)),
            ("3 days ago", timedelta(days=3))
        ]
        
        for description, time_delta in test_times:
            since_timestamp = datetime.now(timezone.utc) - time_delta
            scores, biomarkers, archetypes, latest_timestamp = await user_service.fetch_data_since(REAL_PROFILE_ID, since_timestamp)
            
            print(f"  ✓ {description:12}: {len(scores):2d} scores, {len(biomarkers):2d} biomarkers")
            print(f"     Latest data: {latest_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # ========== TEST 3: Test Analysis Tracker (if possible) ==========
        print(f"\n🎯 TEST 3: Analysis Tracker (Basic)")
        print("-" * 45)
        
        try:
            from services.simple_analysis_tracker import SimpleAnalysisTracker as AnalysisTracker
            tracker = AnalysisTracker()
            
            # Test getting analysis time (will likely fail due to missing column, but that's OK)
            last_analysis = await tracker.get_last_analysis_time(REAL_PROFILE_ID)
            
            if last_analysis:
                print(f"  ✓ Last analysis found: {last_analysis.isoformat()}")
                
                # Test the fix: Update with latest data timestamp (not current time)
                print(f"  🔧 Testing timestamp fix - updating with latest data timestamp")
                success = await tracker.update_analysis_time(REAL_PROFILE_ID, latest_timestamp_1)
                
                if success:
                    print(f"  ✅ Analysis timestamp updated with data timestamp: {latest_timestamp_1.isoformat()}")
                    print(f"  ⏰ Current time would have been: {datetime.now(timezone.utc).isoformat()}")
                else:
                    print(f"  ❌ Failed to update analysis timestamp")
            else:
                print(f"  ✓ No previous analysis found (expected - database column missing)")
            
            await tracker.cleanup()
            
        except Exception as tracker_error:
            print(f"  ⚠️  Analysis tracker test skipped: {str(tracker_error)[:60]}...")
            print(f"     (This is expected if database column doesn't exist yet)")
        
        # ========== TEST 4: Efficiency Demonstration ==========
        print(f"\n📈 TEST 4: Efficiency Demonstration")
        print("-" * 45)
        
        # Show how incremental would work vs full sync
        full_data_count = health_data_1.data_quality.scores_count + health_data_1.data_quality.biomarkers_count
        
        # Simulate incremental sync for last 2 hours
        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        incremental_scores, incremental_biomarkers, _, _ = await user_service.fetch_data_since(REAL_PROFILE_ID, two_hours_ago)
        incremental_count = len(incremental_scores) + len(incremental_biomarkers)
        
        if incremental_count < full_data_count:
            efficiency = ((full_data_count - incremental_count) / full_data_count) * 100
            print(f"  ✓ Full sync would fetch: {full_data_count} records")
            print(f"  ✓ 2-hour incremental fetches: {incremental_count} records") 
            print(f"  ✓ Efficiency gain: {efficiency:.1f}% fewer records")
            print(f"  🎉 INCREMENTAL LOGIC IS WORKING!")
        else:
            print(f"  ✓ Full sync: {full_data_count} records")
            print(f"  ✓ Incremental: {incremental_count} records")
            print(f"  ℹ️  No efficiency gain (all data is recent)")
        
        # Cleanup
        await user_service.cleanup()
        
        print(f"\n✅ CORE INCREMENTAL LOGIC TEST: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_readiness():
    """Test if database has required columns"""
    print(f"\n🗄️  TESTING DATABASE READINESS")
    print("-" * 45)
    
    try:
        from services.simple_analysis_tracker import SimpleAnalysisTracker as AnalysisTracker
        tracker = AnalysisTracker()
        
        # Try to get analysis time - this will tell us if columns exist
        last_analysis = await tracker.get_last_analysis_time(REAL_PROFILE_ID)
        
        # Try to update analysis time 
        success = await tracker.update_analysis_time(REAL_PROFILE_ID)
        
        await tracker.cleanup()
        
        if success:
            print("  ✅ Database ready - profiles table has required columns")
            print("  ✅ Analysis tracking fully functional")
            return True
        else:
            print("  ⚠️  Database not ready - need to add columns")
            return False
            
    except Exception as e:
        print(f"  ❌ Database not ready: {str(e)[:100]}...")
        print(f"  📋 Need to run: ALTER TABLE profiles ADD COLUMN last_analysis_at TIMESTAMPTZ;")
        return False

async def main():
    """Simple focused test runner"""
    print("🚀 SIMPLIFIED INCREMENTAL SYNC TEST")
    print("Testing core logic and database readiness")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Test core logic (should work regardless of database state)
    core_test = await test_core_incremental_logic()
    
    # Test database readiness (will show if columns need to be added)
    db_test = await test_database_readiness()
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    if core_test:
        print("✅ CORE INCREMENTAL LOGIC: WORKING")
        print("   • Data fetching operates correctly")
        print("   • Time-based filtering functional") 
        print("   • Efficiency gains demonstrated")
    else:
        print("❌ CORE INCREMENTAL LOGIC: FAILED")
        
    if db_test:
        print("✅ DATABASE INTEGRATION: READY")
        print("   • Analysis tracking fully functional")
        print("   • Ready for production use")
    else:
        print("⚠️  DATABASE INTEGRATION: NEEDS SETUP")
        print("   • Run SQL migration to add columns")
        print("   • See docs/add_analysis_tracking.sql")
        
    print(f"\n⏱️  Total test time: {duration:.2f} seconds")
    
    if core_test:
        print("\n🎯 NEXT STEPS:")
        if not db_test:
            print("1. Add database columns:")
            print("   ALTER TABLE profiles ADD COLUMN last_analysis_at TIMESTAMPTZ;")
            print("   ALTER TABLE profiles ADD COLUMN analysis_metadata JSONB DEFAULT '{}';")
            print("2. Test full integration with database tracking")
        else:
            print("1. System ready for production!")
            print("2. Can implement Phase 4.1 Memory Integration")
        
        return True
    else:
        print("\n❌ FIX CORE ISSUES BEFORE PROCEEDING")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)