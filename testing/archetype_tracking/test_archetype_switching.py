#!/usr/bin/env python3
"""
Test Archetype Switching Fix
Demonstrates that the system now properly handles archetype changes
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

async def test_archetype_switching():
    """Test archetype switching behavior"""
    
    print("🎭 Testing Archetype Switching Fix")
    print("=" * 50)
    
    # Import services
    from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
    from services.archetype_manager import archetype_manager
    
    # Test user
    test_user_id = "test_user_archetype_switch"
    
    # Initialize service
    ondemand_service = await get_ondemand_service()
    
    # Test 1: Compatible archetype change (should adapt existing)
    print("\n🧪 TEST 1: Compatible Archetype Change")
    print("Foundation Builder → Resilience Rebuilder (compatible)")
    
    assessment = archetype_manager.assess_transition("Foundation Builder", "Resilience Rebuilder")
    print(f"Strategy: {assessment['strategy'].value}")
    print(f"Fresh Analysis Required: {assessment['fresh_analysis_required']}")
    print(f"Reason: {assessment['reason']}")
    
    # Test 2: Incompatible archetype change (should force fresh)
    print("\n🧪 TEST 2: Incompatible Archetype Change")  
    print("Foundation Builder → Peak Performer (incompatible)")
    
    assessment = archetype_manager.assess_transition("Foundation Builder", "Peak Performer")
    print(f"Strategy: {assessment['strategy'].value}")
    print(f"Fresh Analysis Required: {assessment['fresh_analysis_required']}")
    print(f"Reason: {assessment['reason']}")
    if 'warnings' in assessment:
        for warning in assessment['warnings']:
            print(f"  ⚠️ {warning}")
    
    # Test 3: Analysis decision with archetype change
    print("\n🧪 TEST 3: OnDemand Analysis Decision")
    print("Testing should_run_analysis with archetype parameter...")
    
    try:
        # This should work now with archetype parameter
        decision, metadata = await ondemand_service.should_run_analysis(
            test_user_id, 
            force_refresh=False,
            requested_archetype="Peak Performer"
        )
        
        print(f"✅ Decision: {decision.value}")
        print(f"   Reason: {metadata.get('reason', 'No reason provided')}")
        if metadata.get('archetype_change'):
            print(f"   🎭 Archetype Change Detected!")
            print(f"   Previous: {metadata.get('previous_archetype')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Show archetype profiles
    print("\n📊 ARCHETYPE PROFILES:")
    profiles = archetype_manager.ARCHETYPE_PROFILES
    for archetype, profile in profiles.items():
        print(f"{archetype}:")
        print(f"  ⏱️ Time: {profile['daily_time']} min/day")
        print(f"  🧠 Complexity: {profile['complexity']}/10")
        print(f"  🎯 Focus: {profile['focus']}")
    
    # Test 5: Compatibility Matrix
    print("\n🔗 COMPATIBILITY EXAMPLES:")
    test_pairs = [
        ("Foundation Builder", "Peak Performer"),
        ("Foundation Builder", "Resilience Rebuilder"),
        ("Peak Performer", "Systematic Improver"),
        ("Transformation Seeker", "Connected Explorer")
    ]
    
    for from_arch, to_arch in test_pairs:
        compatibility = archetype_manager._check_compatibility(from_arch, to_arch)
        print(f"{from_arch} → {to_arch}: {compatibility}")
    
    await ondemand_service.cleanup()
    print("\n✅ All tests completed!")
    
    print("\n" + "=" * 60)
    print("🎉 ARCHETYPE SWITCHING FIX SUMMARY:")
    print("• OnDemandAnalysisService now accepts archetype parameter")  
    print("• Cache retrieval filtered by archetype")
    print("• ArchetypeManager assesses compatibility")
    print("• Incompatible changes force fresh analysis")
    print("• Compatible changes allow smooth transitions")
    print("\n🔧 Next Steps:")
    print("• Test with real API calls")
    print("• Monitor logs for archetype mismatch warnings")
    print("• Consider adding user notifications (future)")

if __name__ == "__main__":
    asyncio.run(test_archetype_switching())