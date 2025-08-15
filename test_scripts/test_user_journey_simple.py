#!/usr/bin/env python3
"""
Simple User Journey Test
Mimics real user flow: Routine → Nutrition → Follow-up → Repeat
"""
import asyncio
import sys
import os
import time
import json
from datetime import datetime, timezone
import aiohttp

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
REAL_PROFILE_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
BASE_URL = "http://localhost:8001"
TEST_ARCHETYPE = "Foundation Builder"

def print_section(title, emoji="🎯"):
    """Print formatted section header"""
    print(f"\n{emoji} {title}")
    print("-" * 50)

def get_user_choice(prompt):
    """Get yes/no choice from user"""
    while True:
        response = input(f"\n{prompt} (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no")

async def check_server():
    """Quick server check"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status == 200:
                    print("✅ Server is running")
                    return True
    except:
        print("❌ Server not accessible")
        return False

async def show_generated_logs():
    """Show what log files were created during the test"""
    print_section("GENERATED LOG FILES", "📁")
    
    try:
        import glob
        import os
        from datetime import datetime
        
        logs_dir = "../logs" if os.path.exists("../logs") else "logs"
        
        # Find recent log files
        output_files = glob.glob(f"{logs_dir}/output_*.txt")
        insights_files = glob.glob(f"{logs_dir}/insights_*.txt")
        
        if output_files:
            output_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            print(f"📄 Analysis Output Files ({len(output_files)} total):")
            for file in output_files[:3]:
                mtime = datetime.fromtimestamp(os.path.getmtime(file))
                print(f"   • {os.path.basename(file)} - {mtime.strftime('%H:%M:%S')}")
        
        if insights_files:
            insights_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            print(f"\n✨ Dedicated Insights Files ({len(insights_files)} total):")
            for file in insights_files[:3]:
                mtime = datetime.fromtimestamp(os.path.getmtime(file))
                print(f"   • {os.path.basename(file)} - {mtime.strftime('%H:%M:%S')}")
        
        if not output_files and not insights_files:
            print("⚠️ No log files found")
        else:
            print(f"\n📂 Log files location: {os.path.abspath(logs_dir)}")
            
    except Exception as e:
        print(f"⚠️ Could not check log files: {e}")

async def generate_routine(user_id: str, archetype: str, is_followup: bool = False):
    """Generate routine plan - will create behavior analysis if needed"""
    print_section(f"{'FOLLOW-UP ' if is_followup else ''}ROUTINE GENERATION", "🏃")
    
    try:
        # Routine preferences
        routine_request = {
            "archetype": archetype,
            "preferences": {
                "workout_time": "morning",
                "duration_minutes": 30,
                "intensity": "moderate"
            }
        }
        
        print("⏳ Generating routine plan...")
        if is_followup:
            print("   Using incremental data and previous insights...")
        else:
            print("   Will create behavior analysis if needed...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/user/{user_id}/routine/generate",
                json=routine_request,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Routine generated successfully!")
                    
                    # Show key info
                    metadata = result.get('generation_metadata', {})
                    print(f"   • Analysis Type: {metadata.get('analysis_type', 'unknown')}")
                    print(f"   • Memory Quality: {metadata.get('memory_quality', 'unknown')}")
                    print(f"   • Used Cached Behavior: {result.get('cached', False)}")
                    
                    if is_followup:
                        print(f"   • New Data Points Since Last: {metadata.get('new_data_points', 0)}")
                    
                    # Show routine highlights
                    if result.get('routine'):
                        routine = result['routine']
                        if 'weekly_schedule' in routine:
                            print(f"\n📋 Created {len(routine['weekly_schedule'])}-day workout plan")
                            # Show first day as example
                            if routine['weekly_schedule']:
                                first_day = routine['weekly_schedule'][0]
                                print(f"   Example - {first_day.get('day', 'Day 1')}:")
                                if 'exercises' in first_day:
                                    for ex in first_day['exercises'][:3]:
                                        print(f"     • {ex.get('name', 'Exercise')}")
                    
                    return True
                else:
                    error = await response.text()
                    print(f"❌ Routine generation failed: {error[:100]}...")
                    return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def generate_nutrition(user_id: str, archetype: str, is_followup: bool = False):
    """Generate nutrition plan - uses shared behavior analysis"""
    print_section(f"{'FOLLOW-UP ' if is_followup else ''}NUTRITION GENERATION", "🥗")
    
    try:
        # Nutrition preferences
        nutrition_request = {
            "archetype": archetype,
            "preferences": {
                "dietary_restriction": "none",
                "meal_prep_time": "moderate",
                "cuisine_preference": "mediterranean"
            }
        }
        
        print("⏳ Generating nutrition plan...")
        print("   Using shared behavior analysis from routine...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/user/{user_id}/nutrition/generate",
                json=nutrition_request,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Nutrition plan generated successfully!")
                    
                    # Show key info
                    metadata = result.get('generation_metadata', {})
                    print(f"   • Analysis Type: {metadata.get('analysis_type', 'unknown')}")
                    print(f"   • Used Cached Analysis: {result.get('cached', False)}")
                    
                    # Show nutrition highlights
                    if result.get('nutrition'):
                        nutrition = result['nutrition']
                        if 'meal_plan' in nutrition:
                            print(f"\n📋 Created {len(nutrition['meal_plan'])}-day meal plan")
                            # Show first day as example
                            if nutrition['meal_plan']:
                                first_day = nutrition['meal_plan'][0]
                                print(f"   Example meals for {first_day.get('day', 'Day 1')}:")
                                for meal_type in ['breakfast', 'lunch', 'dinner']:
                                    if meal_type in first_day:
                                        meal = first_day[meal_type]
                                        print(f"     • {meal_type.title()}: {meal.get('name', 'Meal')[:50]}...")
                    
                    return True
                else:
                    error = await response.text()
                    print(f"❌ Nutrition generation failed: {error[:100]}...")
                    return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def generate_insights(user_id: str, archetype: str = "Foundation Builder", force_refresh: bool = True):
    """Generate AI insights using the working insights API"""
    print_section("AI INSIGHTS", "🔍")
    
    try:
        # Use the correct insights API endpoint and format
        insights_request = {
            "user_id": user_id,
            "archetype": archetype,
            "force_refresh": force_refresh
        }
        
        print("⏳ Generating AI insights based on your analysis...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/v1/insights/generate",
                json=insights_request,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        insights = result.get('insights', [])
                        
                        print(f"✅ Generated {len(insights)} insights!")
                        print(f"   • Source: {result.get('source', 'unknown')}")
                        
                        # Show insights with better formatting
                        for i, insight in enumerate(insights[:3], 1):
                            title = insight.get('title', 'Insight')
                            content = insight.get('content', '')
                            insight_type = insight.get('type', 'general')
                            priority = insight.get('priority', 5)
                            actionability = insight.get('actionability_score', 0.0)
                            
                            print(f"\n   📋 Insight {i}: {title}")
                            print(f"      Type: {insight_type} | Priority: {priority} | Actionability: {actionability:.1f}")
                            print(f"      → {content[:120]}{'...' if len(content) > 120 else ''}")
                        
                        if len(insights) > 3:
                            print(f"\n   ... and {len(insights) - 3} more insights available")
                        
                        # Show logging info
                        if result.get('source') == 'fresh':
                            print(f"   📁 Fresh insights extracted from recent analyses and logged")
                        else:
                            print(f"   📁 Retrieved cached insights from database")
                        
                        return True
                    else:
                        print(f"⚠️ Insights API returned success=false")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Insights generation failed (HTTP {response.status})")
                    print(f"   Error: {error_text[:100]}...")
                    return False
    except Exception as e:
        print(f"❌ Error generating insights: {e}")
        return False

async def user_journey():
    """Main user journey flow with insights after each generation"""
    print("\n" + "="*60)
    print("🚀 SIMPLE USER JOURNEY TEST WITH INSIGHTS")
    print("="*60)
    print(f"\nUser: {REAL_PROFILE_ID[:8]}...")
    print(f"Archetype: {TEST_ARCHETYPE}")
    
    # Check server
    if not await check_server():
        print("\n⚠️ Please start the server first!")
        return
    
    cycle_count = 0
    
    while True:
        cycle_count += 1
        is_followup = cycle_count > 1
        
        print(f"\n{'='*60}")
        print(f"📍 {'FOLLOW-UP ' if is_followup else ''}CYCLE {cycle_count}")
        print(f"{'='*60}")
        
        # Step 1: Routine Generation
        success = await generate_routine(REAL_PROFILE_ID, TEST_ARCHETYPE, is_followup)
        if not success:
            print("\n⚠️ Routine generation failed. Stopping.")
            break
        
        # Generate insights after routine
        print("\n🔍 Generating insights based on routine analysis...")
        await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=True)
        
        # Ask if user wants nutrition
        if get_user_choice("📋 Generate nutrition plan using shared behavior analysis?"):
            # Step 2: Nutrition Generation (uses shared behavior)
            success = await generate_nutrition(REAL_PROFILE_ID, TEST_ARCHETYPE, is_followup)
            if not success:
                print("\n⚠️ Nutrition generation failed.")
            else:
                # Generate insights after nutrition
                print("\n🔍 Generating insights based on complete plan...")
                await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=False)
        else:
            print("⏭️ Skipping nutrition generation")
        
        # Ask if user wants to continue with follow-up
        print(f"\n{'='*50}")
        if is_followup:
            continue_prompt = "🔄 Continue with another follow-up cycle?"
        else:
            continue_prompt = "🔄 Simulate progress and generate follow-up plans?"
        
        if not get_user_choice(continue_prompt):
            print("\n✅ User journey completed!")
            print(f"   Total cycles: {cycle_count}")
            
            # Show generated log files
            await show_generated_logs()
            break
        
        if not is_followup:
            print("\n⏳ Simulating time passing and new health data...")
            await asyncio.sleep(3)  # Simulate delay
            print("   📊 New data points added (simulated)")

async def quick_test():
    """Quick automated test without prompts - includes insights"""
    print("\n🚀 QUICK AUTOMATED TEST WITH INSIGHTS")
    print("="*50)
    
    if not await check_server():
        return False
    
    print("\n1️⃣ Initial Routine Generation")
    if not await generate_routine(REAL_PROFILE_ID, TEST_ARCHETYPE, False):
        return False
    await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=True)
    
    print("\n2️⃣ Nutrition with Shared Analysis")
    if not await generate_nutrition(REAL_PROFILE_ID, TEST_ARCHETYPE, False):
        return False
    await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=False)
    
    print("\n3️⃣ Follow-up Routine")
    await asyncio.sleep(2)
    if not await generate_routine(REAL_PROFILE_ID, TEST_ARCHETYPE, True):
        return False
    await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=True)
    
    print("\n✅ Quick test completed successfully!")
    
    # Show generated log files
    await show_generated_logs()
    
    return True

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple User Journey Test")
    parser.add_argument("--quick", "-q", action="store_true",
                       help="Run quick automated test without prompts")
    
    args = parser.parse_args()
    
    if args.quick:
        success = await quick_test()
        sys.exit(0 if success else 1)
    else:
        await user_journey()

if __name__ == "__main__":
    try:
        print("\n🎯 SIMPLE USER JOURNEY TEST WITH INSIGHTS")
        print("This simulates a real user flow:")
        print("  1. Generate Routine (creates behavior analysis)")
        print("  2. Generate AI Insights (extracts actionable insights from analysis)")
        print("  3. Generate Nutrition (uses shared behavior analysis)")
        print("  4. Generate AI Insights (additional insights from complete plan)")
        print("  5. Follow-up Analysis (uses incremental data + memory)")
        print("  6. Generate AI Insights (progress & adaptation insights)")
        print("  7. Repeat as needed\n")
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n\n👋 Test stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)