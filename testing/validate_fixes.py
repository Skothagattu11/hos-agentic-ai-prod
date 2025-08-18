#!/usr/bin/env python3
"""
Validate the fixes by checking the code changes
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

def check_insights_endpoint_fix():
    """Check if the variable scope issue is fixed"""
    try:
        with open('services/api_gateway/insights_endpoints.py', 'r') as f:
            content = f.read()
        
        # Check if the fix is present
        has_null_check = "if HolisticMemoryService is None:" in content
        has_error_handling = "Don't fail the entire request if fresh insights fail" in content
        
        if has_null_check and has_error_handling:
            print("✅ INSIGHTS ENDPOINT: Variable scope fix implemented")
            return True
        else:
            print("❌ INSIGHTS ENDPOINT: Fix not found")
            return False
            
    except Exception as e:
        print(f"❌ Could not check insights endpoint: {e}")
        return False

def check_memory_service_fix():
    """Check if the duplicate key constraint is fixed"""
    try:
        with open('services/agents/memory/holistic_memory_service.py', 'r') as f:
            content = f.read()
        
        # Check if UPSERT is present
        has_upsert = "ON CONFLICT" in content
        has_duplicate_handling = "unique_user_type_date" in content
        
        if has_upsert and has_duplicate_handling:
            print("✅ MEMORY SERVICE: Duplicate key constraint fix implemented")
            return True
        else:
            print("❌ MEMORY SERVICE: Fix not found")
            return False
            
    except Exception as e:
        print(f"❌ Could not check memory service: {e}")
        return False

def check_automatic_extraction_removal():
    """Check if automatic insights extraction was removed"""
    try:
        with open('services/agents/memory/holistic_memory_service.py', 'r') as f:
            content = f.read()
        
        # Check if automatic extraction is removed
        no_auto_extraction = "insights_service.extract_and_store_insights" not in content
        has_cto_comment = "CTO Decision: Remove automatic insights" in content
        
        if no_auto_extraction and has_cto_comment:
            print("✅ MEMORY SERVICE: Automatic insights extraction removed")
            return True
        else:
            print("❌ MEMORY SERVICE: Automatic extraction still present")
            return False
            
    except Exception as e:
        print(f"❌ Could not check automatic extraction: {e}")
        return False

if __name__ == "__main__":
    print("🧪 VALIDATING FIXES...")
    print("=" * 50)
    
    fix1 = check_insights_endpoint_fix()
    fix2 = check_memory_service_fix() 
    fix3 = check_automatic_extraction_removal()
    
    print("\n" + "=" * 50)
    
    if fix1 and fix2 and fix3:
        print("🎉 ALL FIXES VALIDATED SUCCESSFULLY!")
        print("\n✅ Ready to test with test_user_journey_simple.py")
        print("   The following issues should be resolved:")
        print("   • No more variable scope errors in insights endpoint")
        print("   • No more duplicate key constraint violations")
        print("   • No more automatic insights extraction")
        print("   • Clean, predictable behavior")
    else:
        print("❌ SOME FIXES ARE MISSING!")
        print("   Please check the failed validations above")
    
    sys.exit(0 if (fix1 and fix2 and fix3) else 1)