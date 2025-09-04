#!/usr/bin/env python3
"""
Multi-Plan/Archetype Selection Backend Testing Script

Tests the new archetype management and enhanced calendar endpoints
to ensure multi-plan support works correctly.

Usage:
    python test_archetype_features.py
"""

import asyncio
import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Load environment
from dotenv import load_dotenv
load_dotenv()

class ArchetypeAPITester:
    """Test suite for archetype management features"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('API_BASE_URL', 'http://localhost:8002')
        self.test_user_id = os.getenv('TEST_USER_ID', '35pDPUIfAoRl2Y700bFkxPKYjjf2')
        self.results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.results.append({
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_api_health(self):
        """Test basic API health"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                self.log_test("API Health Check", True, f"API responding on {self.base_url}")
                return True
            else:
                self.log_test("API Health Check", False, f"Status code: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("API Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_get_available_archetypes(self) -> Optional[Dict]:
        """Test GET /api/user/{user_id}/available-archetypes"""
        try:
            url = f"{self.base_url}/api/user/{self.test_user_id}/available-archetypes"
            print(f"\n🔍 Testing: {url}")
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ['user_id', 'total_archetypes', 'archetypes', 'has_multiple_plans']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Available Archetypes - Structure", False, 
                                f"Missing fields: {missing_fields}")
                    return None
                
                # Log details
                total_archetypes = data['total_archetypes']
                has_multiple = data['has_multiple_plans']
                archetypes = data['archetypes']
                
                self.log_test("Available Archetypes - API Call", True, 
                            f"Found {total_archetypes} archetypes, multiple: {has_multiple}")
                
                if archetypes:
                    print(f"    📋 Archetypes found:")
                    for i, archetype in enumerate(archetypes):
                        name = archetype.get('archetype_name', 'Unknown')
                        items = archetype.get('total_plan_items', 0)
                        analysis_id = archetype.get('analysis_id', '')[:8] + '...'
                        print(f"      {i+1}. {name} - {items} items ({analysis_id})")
                
                # Test multiple archetypes scenario
                if has_multiple:
                    self.log_test("Multi-Archetype Detection", True, 
                                f"User has {total_archetypes} different plans")
                else:
                    self.log_test("Single Archetype Detection", True, 
                                "User has single plan (expected for new users)")
                
                return data
                
            else:
                self.log_test("Available Archetypes - API Call", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_test("Available Archetypes - API Call", False, str(e))
            return None
    
    def test_archetype_summary(self, analysis_id: str) -> Optional[Dict]:
        """Test GET /api/user/{user_id}/archetype/{analysis_id}/summary"""
        try:
            url = f"{self.base_url}/api/user/{self.test_user_id}/archetype/{analysis_id}/summary"
            print(f"\n🔍 Testing: {url}")
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ['analysis_id', 'archetype_name', 'analysis_type', 'created_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Archetype Summary - Structure", False, 
                                f"Missing fields: {missing_fields}")
                    return None
                
                # Log details
                archetype_name = data['archetype_name']
                analysis_type = data['analysis_type']
                total_items = data.get('total_plan_items', 0)
                total_blocks = data.get('total_time_blocks', 0)
                primary_goal = data.get('primary_goal', 'Not specified')
                
                self.log_test("Archetype Summary - API Call", True, 
                            f"{archetype_name} ({analysis_type})")
                
                print(f"    📊 Plan Details:")
                print(f"      • Goal: {primary_goal[:80]}{'...' if len(primary_goal) > 80 else ''}")
                print(f"      • Items: {total_items} plan items")
                print(f"      • Blocks: {total_blocks} time blocks")
                
                focus_areas = data.get('focus_areas', [])
                if focus_areas:
                    print(f"      • Focus: {', '.join(focus_areas[:3])}")
                
                return data
                
            elif response.status_code == 404:
                self.log_test("Archetype Summary - API Call", False, 
                            "Analysis not found (expected for invalid IDs)")
                return None
            else:
                self.log_test("Archetype Summary - API Call", False, 
                            f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Archetype Summary - API Call", False, str(e))
            return None
    
    def test_enhanced_calendar_endpoint(self, analysis_id: str = None) -> Optional[Dict]:
        """Test enhanced GET /api/calendar/available-items/{profile_id} with archetype data"""
        try:
            url = f"{self.base_url}/api/calendar/available-items/{self.test_user_id}"
            params = {}
            
            if analysis_id:
                params['archetype_filter'] = analysis_id
                print(f"\n🔍 Testing Calendar with Archetype Filter: {url}?archetype_filter={analysis_id[:8]}...")
            else:
                print(f"\n🔍 Testing Enhanced Calendar Endpoint: {url}")
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate enhanced response structure
                required_fields = ['success', 'total_items', 'plan_items', 'archetype_summary']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Enhanced Calendar - Structure", False, 
                                f"Missing fields: {missing_fields}")
                    return None
                
                # Validate archetype_summary structure
                archetype_summary = data.get('archetype_summary', {})
                summary_fields = ['total_archetypes', 'has_multiple_archetypes', 'archetypes']
                summary_missing = [field for field in summary_fields if field not in archetype_summary]
                
                if summary_missing:
                    self.log_test("Enhanced Calendar - Archetype Summary", False, 
                                f"Missing summary fields: {summary_missing}")
                    return None
                
                # Log results
                total_items = data['total_items']
                total_archetypes = archetype_summary['total_archetypes']
                has_multiple = archetype_summary['has_multiple_archetypes']
                applied_filter = archetype_summary.get('applied_filter')
                
                test_name = "Enhanced Calendar - With Filter" if applied_filter else "Enhanced Calendar - All Items"
                self.log_test(test_name, True, 
                            f"{total_items} items from {total_archetypes} archetypes")
                
                print(f"    📅 Calendar Results:")
                print(f"      • Total Items: {total_items}")
                print(f"      • Total Archetypes: {total_archetypes}")
                print(f"      • Multiple Plans: {has_multiple}")
                if applied_filter:
                    print(f"      • Filtered by: {applied_filter[:8]}...")
                
                # Validate plan items have archetype metadata
                plan_items = data.get('plan_items', [])
                items_with_metadata = 0
                
                for item in plan_items[:3]:  # Check first 3 items
                    if 'archetype_metadata' in item:
                        items_with_metadata += 1
                        metadata = item['archetype_metadata']
                        print(f"      • Item: {item.get('title', 'Untitled')[:40]}... ({metadata.get('archetype_name', 'Unknown')})")
                
                if items_with_metadata > 0:
                    self.log_test("Enhanced Calendar - Metadata", True, 
                                f"{items_with_metadata}/{len(plan_items[:3])} items have archetype metadata")
                elif plan_items:
                    self.log_test("Enhanced Calendar - Metadata", False, 
                                "Plan items missing archetype metadata")
                
                return data
                
            else:
                self.log_test("Enhanced Calendar - API Call", False, 
                            f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Enhanced Calendar - API Call", False, str(e))
            return None
    
    def test_archetype_filtering(self, archetypes_data: Dict):
        """Test archetype filtering functionality"""
        if not archetypes_data or not archetypes_data.get('archetypes'):
            self.log_test("Archetype Filtering", False, "No archetypes available for filtering test")
            return
        
        archetypes = archetypes_data['archetypes']
        
        # Test filtering by each available archetype
        for i, archetype in enumerate(archetypes[:2]):  # Test first 2 archetypes max
            analysis_id = archetype['analysis_id']
            archetype_name = archetype['archetype_name']
            
            print(f"\n    🔍 Testing filter for {archetype_name}...")
            
            filtered_data = self.test_enhanced_calendar_endpoint(analysis_id)
            
            if filtered_data:
                filtered_items = filtered_data['total_items']
                expected_items = archetype['total_plan_items']
                
                # The filtered items should match the archetype's item count
                if filtered_items == expected_items:
                    self.log_test(f"Archetype Filter - {archetype_name}", True, 
                                f"Correctly filtered to {filtered_items} items")
                elif filtered_items == 0 and expected_items == 0:
                    self.log_test(f"Archetype Filter - {archetype_name}", True, 
                                "Correctly shows no items (empty archetype)")
                else:
                    self.log_test(f"Archetype Filter - {archetype_name}", False, 
                                f"Expected {expected_items} items, got {filtered_items}")
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Archetype Features Backend Test Suite")
        print("=" * 60)
        
        # Test 1: API Health
        if not self.test_api_health():
            print("❌ API not responding - aborting tests")
            return
        
        # Test 2: Available Archetypes
        archetypes_data = self.test_get_available_archetypes()
        if not archetypes_data:
            print("❌ Cannot get archetypes - skipping dependent tests")
            return
        
        # Test 3: Archetype Summary (for first archetype)
        if archetypes_data.get('archetypes'):
            first_archetype = archetypes_data['archetypes'][0]
            analysis_id = first_archetype['analysis_id']
            self.test_archetype_summary(analysis_id)
        
        # Test 4: Enhanced Calendar Endpoint (all items)
        calendar_data = self.test_enhanced_calendar_endpoint()
        
        # Test 5: Archetype Filtering
        if archetypes_data.get('has_multiple_plans'):
            print(f"\n🔄 Testing Multi-Plan Filtering...")
            self.test_archetype_filtering(archetypes_data)
        else:
            self.log_test("Multi-Plan Filtering", True, 
                        "Single archetype user - filtering not applicable")
        
        # Generate Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"   • {result['test_name']}: {result['details']}")
        
        print(f"\n🎯 Backend Implementation Status:")
        if passed_tests >= 6:  # Adjust based on total expected tests
            print("✅ Multi-archetype backend features are working correctly")
            print("✅ Ready for frontend integration")
        elif passed_tests >= 4:
            print("⚠️  Core features working, some issues need attention")
            print("🔧 Review failed tests before frontend development")
        else:
            print("❌ Major issues detected - fix backend before proceeding")
            print("🛠️  Focus on API connectivity and data structure")

def main():
    """Main test execution"""
    
    # Configuration
    print("🔧 Configuration:")
    print(f"   • API URL: {os.getenv('API_BASE_URL', 'http://localhost:8001')}")
    print(f"   • Test User: {os.getenv('TEST_USER_ID', '35pDPUIfAoRl2Y700bFkxPKYjjf2')}")
    print()
    
    # Run tests
    tester = ArchetypeAPITester()
    tester.run_all_tests()
    
    # Save results
    results_file = f"archetype_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(results_file, 'w') as f:
            json.dump({
                'test_run': {
                    'timestamp': datetime.now().isoformat(),
                    'api_url': tester.base_url,
                    'test_user_id': tester.test_user_id,
                    'total_tests': len(tester.results),
                    'passed': len([r for r in tester.results if r['success']]),
                    'failed': len([r for r in tester.results if not r['success']])
                },
                'results': tester.results
            }, f, indent=2)
        print(f"\n💾 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save results file: {e}")

if __name__ == "__main__":
    main()