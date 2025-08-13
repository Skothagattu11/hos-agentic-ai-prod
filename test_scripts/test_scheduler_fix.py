#!/usr/bin/env python3
"""
Quick test to verify the scheduler data counting fix
"""
import asyncio
import sys
import os
from datetime import datetime, timezone

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_scheduler_data_counting():
    """Test if the scheduler can count data points without errors"""
    print("🔧 TESTING SCHEDULER DATA COUNTING FIX")
    print("-" * 50)
    
    try:
        from services.scheduler.behavior_analysis_scheduler import BehaviorAnalysisScheduler
        
        # Initialize scheduler
        scheduler = BehaviorAnalysisScheduler()
        if not await scheduler.initialize():
            print("❌ Failed to initialize scheduler")
            return False
        
        # Test user ID
        test_user_id = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
        
        print(f"📊 Testing data counting for user: {test_user_id[:8]}...")
        
        # Test the count_new_data_points method
        count, last_analysis = await scheduler.count_new_data_points(test_user_id)
        
        print(f"✅ Data counting successful!")
        print(f"   • New data points: {count}")
        print(f"   • Last analysis: {last_analysis.isoformat()}")
        
        # Test trigger check
        should_trigger, reason = await scheduler.should_trigger_analysis(test_user_id)
        print(f"   • Should trigger: {should_trigger}")
        print(f"   • Reason: {reason}")
        
        # Cleanup
        await scheduler.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🧪 SCHEDULER FIX VALIDATION TEST")
    print("=" * 50)
    
    success = await test_scheduler_data_counting()
    
    if success:
        print("\n🎉 Scheduler fix successful!")
        print("   The 'total_count' error should be resolved")
    else:
        print("\n⚠️  Scheduler still has issues")
        print("   Additional debugging may be needed")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test script failed: {e}")
        sys.exit(1)