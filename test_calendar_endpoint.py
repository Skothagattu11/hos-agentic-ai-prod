#!/usr/bin/env python3
"""
Test the calendar time-blocks endpoint to debug missing items
"""
import requests
import json
import sys

def test_calendar_endpoint():
    # Test the time-blocks endpoint
    url = "http://localhost:8002/api/calendar/time-blocks/35pDPUIfAoRl2Y700bFkxPKYjjf2"
    params = {
        "archetype_filter": "e6b81773-cd19-43a7-9521-318590db091d"
    }
    
    try:
        print("🔍 Testing calendar time-blocks endpoint...")
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response received")
            
            print(f"\n📈 Summary:")
            print(f"  Total time blocks: {data.get('total_time_blocks', 0)}")
            print(f"  Total calendar items: {data.get('total_calendar_items', 0)}")
            
            print(f"\n🕐 Time Blocks:")
            for tb in data.get('time_blocks', []):
                print(f"  - {tb['block_title']}")
                print(f"    ID: {tb['id']}")
                print(f"    Time: {tb['time_range']}")
                print()
            
            print(f"📋 Calendar Items:")
            if data.get('calendar_items'):
                for item in data.get('calendar_items', []):
                    print(f"  - {item['title']}")
                    print(f"    Plan Item ID: {item['plan_item_id']}")
                    print(f"    Time Block ID: {item.get('time_block_id', 'NULL')}")
                    print(f"    Notes: {item.get('calendar_notes', 'None')}")
                    print()
            else:
                print("  ❌ No calendar items found!")
            
            # Check for missing items specifically
            expected_items = [
                'f76628f4-7acc-4f99-bf3e-41b411e65eca',  # Wind-down Ritual
                '2d62fcce-cb4f-41a8-8263-2a3f7b55eb1a'   # Prepare for Bed
            ]
            
            found_items = [item['plan_item_id'] for item in data.get('calendar_items', [])]
            missing_items = [item_id for item_id in expected_items if item_id not in found_items]
            
            if missing_items:
                print(f"\n❌ MISSING ITEMS:")
                for item_id in missing_items:
                    print(f"  - {item_id}")
                print(f"\n🔧 These items should be included because they:")
                print(f"  - Are in calendar_selections table")
                print(f"  - Have analysis_result_id matching the archetype filter")
                print(f"  - Have time_block_id = NULL (which should be allowed)")
            else:
                print(f"\n✅ All expected items found!")
        
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the backend server running on port 8001?")
        print("Please start the backend server with: python start_openai.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_calendar_endpoint()