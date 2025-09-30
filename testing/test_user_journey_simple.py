#!/usr/bin/env python3
"""
Simple User Journey Test - Updated for AI Context Integration System
Mimics real user flow: Routine → Nutrition → Follow-up → Repeat
Now uses AI Context Integration Service instead of 4-layer memory system
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
# BASE_URL = "https://hos-agentic-ai-prod.onrender.com"  # Production
BASE_URL = "http://localhost:8002"  # Development server
TEST_ARCHETYPE = "Foundation Builder"

# API Authentication for production system
AUTH_HEADERS = {"X-API-Key": "hosa_flutter_app_2024"}

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
            async with session.get(f"{BASE_URL}/api/health") as response:
                if response.status == 200:
                    pass  # Production: Verbose print removed
                    return True
    except:
        print("❌ Server not accessible at localhost:8002")
        pass  # Production: Verbose print removed
        return False

async def show_generated_logs():
    """Show what log files were created during the test with new AI Context Integration system"""
    print_section("GENERATED AI CONTEXT INTEGRATION LOGS", "📁")

    try:
        import glob
        import os
        from datetime import datetime

        logs_dir = "../logs" if os.path.exists("../logs") else "logs"

        # Find AI context flow files
        ai_context_files = glob.glob(f"{logs_dir}/ai_context_flow_*.json")
        flow_files = glob.glob(f"{logs_dir}/complete_ai_context_flow_*.jsonl")

        # Find legacy output files (if any)
        output_files = glob.glob(f"{logs_dir}/output_*.txt")
        insights_files = glob.glob(f"{logs_dir}/insights_*.txt")

        if ai_context_files:
            ai_context_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            print(f"🧠 AI Context Integration Flow Files ({len(ai_context_files)} total):")
            for file in ai_context_files[:5]:
                mtime = datetime.fromtimestamp(os.path.getmtime(file))
                filename = os.path.basename(file)
                stage = filename.split('_')[-1].replace('.json', '').upper()
                print(f"   • {stage}: {filename} - {mtime.strftime('%H:%M:%S')}")

        if flow_files:
            flow_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            print(f"\n📊 Complete Flow Logs ({len(flow_files)} total):")
            for file in flow_files[:3]:
                mtime = datetime.fromtimestamp(os.path.getmtime(file))
                print(f"   • {os.path.basename(file)} - {mtime.strftime('%H:%M:%S')}")

        if output_files:
            output_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            print(f"\n📄 Legacy Analysis Output Files ({len(output_files)} total):")
            for file in output_files[:3]:
                mtime = datetime.fromtimestamp(os.path.getmtime(file))
                print(f"   • {os.path.basename(file)} - {mtime.strftime('%H:%M:%S')}")

        if insights_files:
            insights_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            print(f"\n✨ Insights Files ({len(insights_files)} total):")
            for file in insights_files[:3]:
                mtime = datetime.fromtimestamp(os.path.getmtime(file))
                print(f"   • {os.path.basename(file)} - {mtime.strftime('%H:%M:%S')}")

        print(f"\n📂 Log files location: {os.path.abspath(logs_dir)}")
        print(f"🆕 New architecture: AI Context Integration Service")
        print(f"📝 Look for 'ai_context_flow_*' files for detailed data flow")
        print(f"📊 Look for 'complete_ai_context_flow_*.jsonl' for complete session logs")

    except Exception as e:
        print(f"   ⚠️ Error showing logs: {e}")

async def generate_parallel_analyses(user_id: str, archetype: str, is_followup: bool = False):
    """Run behavior and circadian analysis in parallel on same raw data"""
    print_section(f"{'FOLLOW-UP ' if is_followup else ''}PARALLEL BEHAVIOR + CIRCADIAN ANALYSIS", "🔄")

    print("🚀 Running parallel analysis on same raw health data...")
    pass  # Production: Verbose print removed
    # Production: Verbose print removed

    # Log agent handoff data
    await log_agent_handoff("PARALLEL_ANALYSIS_START", {
        "user_id": user_id,
        "archetype": archetype,
        "is_followup": is_followup,
        "timestamp": datetime.now().isoformat(),
        "raw_data_sources": ["sahha_biomarkers", "user_preferences", "3_day_engagement_analysis"],
        "ai_context_sources": ["calendar_selections", "task_checkins", "daily_journals"],
        "agent_history_sources": ["last_2_behavior_analyses", "last_2_circadian_analyses"],
        "system": "AI_CONTEXT_INTEGRATION_SERVICE"
    })

    try:
        # Prepare requests for both analyses
        behavior_request = {
            "archetype": archetype,
            "force_refresh": True
        }

        circadian_request = {
            "archetype": archetype,
            "force_refresh": True
        }

        # Run both analyses in parallel
        async with aiohttp.ClientSession() as session:
            print("⏳ Executing parallel API calls...")

            # Create both requests simultaneously
            behavior_task = session.post(
                f"{BASE_URL}/api/user/{user_id}/behavior/analyze",
                json=behavior_request,
                headers=AUTH_HEADERS,
                timeout=aiohttp.ClientTimeout(total=300)
            )

            circadian_task = session.post(
                f"{BASE_URL}/api/user/{user_id}/circadian/analyze",
                json=circadian_request,
                headers=AUTH_HEADERS,
                timeout=aiohttp.ClientTimeout(total=300)
            )

            # Wait for both to complete
            behavior_response, circadian_response = await asyncio.gather(
                behavior_task, circadian_task, return_exceptions=True
            )

            # Process behavior analysis results
            behavior_result = None
            if not isinstance(behavior_response, Exception) and behavior_response.status == 200:
                behavior_result = await behavior_response.json()
                pass  # Production: Verbose print removed
                await log_agent_handoff("BEHAVIOR_ANALYSIS_COMPLETE", {
                    "status": "success",
                    "analysis_type": behavior_result.get('analysis_type', 'unknown'),
                    "behavior_data": behavior_result.get('behavior_analysis', {}),
                    "metadata": behavior_result.get('metadata', {}),
                })
            else:
                print(f"❌ Behavior analysis failed")
                await log_agent_handoff("BEHAVIOR_ANALYSIS_FAILED", {
                    "error": str(behavior_response) if isinstance(behavior_response, Exception) else "HTTP error"
                })

            # Process circadian analysis results
            circadian_result = None
            if not isinstance(circadian_response, Exception) and circadian_response.status == 200:
                circadian_result = await circadian_response.json()
                pass  # Production: Verbose print removed
                await log_agent_handoff("CIRCADIAN_ANALYSIS_COMPLETE", {
                    "status": "success",
                    "analysis_type": circadian_result.get('analysis_type', 'unknown'),
                    "circadian_data": circadian_result.get('circadian_analysis', {}),
                    "metadata": circadian_result.get('metadata', {}),
                })
            else:
                print(f"❌ Circadian analysis failed")
                await log_agent_handoff("CIRCADIAN_ANALYSIS_FAILED", {
                    "error": str(circadian_response) if isinstance(circadian_response, Exception) else "HTTP error"
                })

            # Combine the analyses
            combined_analysis = {
                "behavior_analysis": behavior_result.get('behavior_analysis', {}) if behavior_result else {},
                "circadian_analysis": circadian_result.get('circadian_analysis', {}) if circadian_result else {},
                "combined_metadata": {
                    "behavior_success": behavior_result is not None,
                    "circadian_success": circadian_result is not None,
                    "parallel_execution": True,
                    "combination_timestamp": datetime.now().isoformat(),
                    "archetype": archetype
                }
            }

            await log_agent_handoff("COMBINED_ANALYSIS_READY", combined_analysis)
            print("🔄 Combined analysis prepared for routine generation")

            return combined_analysis

    except Exception as e:
        print(f"❌ Parallel analysis error: {e}")
        await log_agent_handoff("PARALLEL_ANALYSIS_ERROR", {"error": str(e)})
        return None

async def generate_routine_with_combined_analysis(user_id: str, archetype: str, combined_analysis: dict, is_followup: bool = False):
    """Generate routine plan using combined behavior + circadian analysis"""
    print_section(f"{'FOLLOW-UP ' if is_followup else ''}COMBINED ROUTINE GENERATION", "🏃")

    try:
        # Log the combined input to routine generation
        await log_agent_handoff("ROUTINE_GENERATION_INPUT", {
            "user_id": user_id,
            "archetype": archetype,
            "has_behavior_data": bool(combined_analysis.get('behavior_analysis')),
            "has_circadian_data": bool(combined_analysis.get('circadian_analysis')),
            "combined_metadata": combined_analysis.get('combined_metadata', {})
        })

        # Extract insights for routine preferences
        routine_preferences = {
            "workout_time": "morning",  # Default
            "duration_minutes": 30,
            "intensity": "moderate",
            "force_refresh": True
        }

        # Use circadian data to optimize timing if available
        circadian_data = combined_analysis.get('circadian_analysis', {})
        if circadian_data:
            energy_zones = circadian_data.get('energy_zone_analysis', {})
            if energy_zones.get('peak_energy_window'):
                routine_preferences["optimal_workout_window"] = energy_zones['peak_energy_window']
                pass  # Production: Verbose print removed

        # Use behavior data to adjust intensity if available
        behavior_data = combined_analysis.get('behavior_analysis', {})
        if behavior_data:
            readiness = behavior_data.get('readiness_level', {})
            if readiness.get('score', 0) > 7:
                routine_preferences["intensity"] = "high"
                print(f"   🧠 High readiness detected, using high intensity")

        routine_request = {
            "archetype": archetype,
            "preferences": routine_preferences
        }

        print("⏳ Generating routine with combined behavior + circadian insights...")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/user/{user_id}/routine/generate",
                json=routine_request,
                headers=AUTH_HEADERS,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    pass  # Production: Verbose print removed

                    # Log the routine generation output
                    await log_agent_handoff("ROUTINE_GENERATION_OUTPUT", {
                        "status": "success",
                        "routine_data": result.get('routine_plan', {}),
                        "generation_metadata": result.get('generation_metadata', {}),
                        "used_combined_analysis": True,
                        "circadian_aligned": bool(circadian_data),
                        "behavior_aligned": bool(behavior_data)
                    })

                    # Show key info
                    metadata = result.get('generation_metadata', {})
                    print(f"   • Analysis Type: {metadata.get('analysis_type', 'unknown')}")
                    print(f"   • Circadian Aligned: {bool(circadian_data)}")
                    print(f"   • Behavior Informed: {bool(behavior_data)}")

                    return True
                else:
                    error = await response.text()
                    print(f"❌ Combined routine generation failed: {error[:100]}...")
                    await log_agent_handoff("ROUTINE_GENERATION_FAILED", {"error": error})
                    return False
    except Exception as e:
        print(f"❌ Error: {e}")
        await log_agent_handoff("ROUTINE_GENERATION_ERROR", {"error": str(e)})
        return False

async def log_agent_handoff(stage: str, data: dict):
    """Enhanced logging for AI Context Integration system data flow"""
    try:
        import os
        import json
        from datetime import datetime

        # Ensure logs directory exists
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        log_file = f"{logs_dir}/ai_context_flow_{timestamp}_{stage.lower()}.json"

        # Enhanced log entry with AI context integration info
        log_entry = {
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "system": "AI_CONTEXT_INTEGRATION_SERVICE",
            "architecture": "AI_Context_Generation_with_Agent_History",
            "data": data,
            "context_info": {
                "replaces": "4_layer_memory_system",
                "uses": "3_day_engagement_analysis_plus_agent_history",
                "agent_specific_context": True,
                "memory_enhanced": False,
                "ai_context_enhanced": True
            }
        }

        with open(log_file, 'w') as f:
            json.dump(log_entry, f, indent=2, default=str)

        print(f"   📝 AI Context Flow logged: {stage} → {log_file}")

        # Also create a comprehensive flow log
        flow_log_file = f"{logs_dir}/complete_ai_context_flow_{timestamp[:8]}.jsonl"
        with open(flow_log_file, 'a') as f:
            json.dump(log_entry, f, default=str)
            f.write('\n')

    except Exception as e:
        print(f"   ⚠️ Logging error: {e}")

async def generate_routine(user_id: str, archetype: str, is_followup: bool = False):
    """Generate routine with integrated parallel behavior + circadian analysis"""
    print_section(f"{'FOLLOW-UP ' if is_followup else ''}ROUTINE GENERATION WITH PARALLEL ANALYSIS", "🏃")

    try:
        # Routine request with archetype and force_refresh for follow-ups
        routine_request = {
            "archetype": archetype,
            "force_refresh": is_followup  # Force fresh analysis for follow-ups
        }

        print("⏳ Generating routine with integrated parallel analysis...")
        print("   • Running behavior + circadian analysis in parallel")
        print("   • Using same raw data for both analyses")
        print("   • Generating dynamic routine with combined insights")
        print("   • Storing combined analysis in database")

        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/user/{user_id}/routine/generate",
                json=routine_request,
                headers=AUTH_HEADERS
            ) as response:
                result = await response.json()

                duration = time.time() - start_time

                if response.status == 200:
                    pass  # Production: Verbose print removed

                    # Enhanced logging for agent handoff tracking
                    pass  # Production: Verbose print removed
                    print(f"   1. Raw Health Data → Behavior Analysis")
                    print(f"   2. Raw Health Data → Circadian Analysis (parallel)")
                    print(f"   3. Combined Analysis → Dynamic Routine Generation")
                    print(f"   4. Results → Database Storage")

                    # Log the complete parallel analysis flow
                    await log_agent_handoff("INTEGRATED_ROUTINE_GENERATION", {
                        "request": routine_request,
                        "response": result,
                        "execution_flow": "parallel_behavior_and_circadian_analysis",
                        "internal_stages": [
                            "raw_data_retrieval",
                            "parallel_analysis_execution",
                            "behavior_analysis_completion",
                            "circadian_analysis_completion",
                            "combined_analysis_creation",
                            "dynamic_routine_generation",
                            "database_storage"
                        ],
                        "combined_analysis_stored": True,
                        "duration_seconds": duration,
                        "archetype": archetype,
                        "is_followup": is_followup,
                        "server_logs": "Check server output for detailed AI context integration handoffs"
                    })

                    return True
                else:
                    print(f"❌ Routine generation failed: {response.status}")
                    print(f"   Error: {result.get('error', 'Unknown error')}")
                    return False

    except Exception as e:
        print(f"❌ Error during routine generation: {e}")
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
                headers=AUTH_HEADERS,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    pass  # Production: Verbose print removed
                    
                    # Show key info
                    metadata = result.get('generation_metadata', {})
                    print(f"   • Analysis Type: {metadata.get('analysis_type', 'unknown')}")
                    print(f"   • Used Cached Analysis: {result.get('cached', False)}")
                    
                    # Show nutrition highlights
                    if result.get('nutrition'):
                        nutrition = result['nutrition']
                        if 'meal_plan' in nutrition:
                            pass  # Production: Verbose print removed
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
                headers=AUTH_HEADERS,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        insights = result.get('insights', [])
                        
                        pass  # Production: Verbose print removed
                        print(f"   • Source: {result.get('source', 'unknown')}")
                        
                        # Show insights with better formatting
                        for i, insight in enumerate(insights[:3], 1):
                            title = insight.get('title', 'Insight')
                            content = insight.get('content', '')
                            insight_type = insight.get('type', 'general')
                            priority = insight.get('priority', 5)
                            actionability = insight.get('actionability_score', 0.0)
                            
                            pass  # Production: Verbose print removed
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
                        pass  # Production: Verbose print removed
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Insights generation failed (HTTP {response.status})")
                    print(f"   Error: {error_text[:100]}...")
                    return False
    except Exception as e:
        print(f"❌ Error generating insights: {e}")
        return False

async def generate_circadian_analysis(user_id: str, archetype: str, is_followup: bool = False):
    """Generate circadian rhythm analysis with detailed logging"""
    print_section(f"{'FOLLOW-UP ' if is_followup else ''}CIRCADIAN RHYTHM ANALYSIS", "🕐")

    try:
        # Circadian analysis request
        circadian_request = {
            "archetype": archetype,
            "force_refresh": True  # Force fresh analysis to see detailed AI process
        }

        print("⏳ Analyzing circadian rhythm patterns...")
        if is_followup:
            print("   Building on previous analysis and new biomarker data...")
        else:
            print("   Processing sleep, HRV, and activity patterns...")

        pass  # Production: Verbose print removed
        # Production: Verbose print removed
        pass  # Production: Verbose print removed
        print("   🧠 Step 3: Integrating AI context and engagement patterns...")
        pass  # Production: Verbose print removed
        print("   💾 Step 5: Storing results in AI context integration system...")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/user/{user_id}/circadian/analyze",
                json=circadian_request,
                headers=AUTH_HEADERS,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    pass  # Production: Verbose print removed

                    # Show key info
                    metadata = result.get('metadata', {})
                    circadian_data = result.get('circadian_analysis', {})

                    pass  # Production: Verbose print removed
                    print(f"   • Analysis Type: {result.get('analysis_type', 'unknown')}")
                    print(f"   • Model Used: {metadata.get('model_used', 'unknown')}")
                    print(f"   • Data Quality: {metadata.get('data_quality', 'unknown')}")
                    print(f"   • Force Refresh: {metadata.get('force_refresh', False)}")

                    # Show detailed circadian insights
                    if circadian_data:
                        pass  # Production: Verbose print removed

                        # Chronotype assessment
                        chronotype = circadian_data.get('chronotype_assessment', {})
                        if chronotype:
                            primary_type = chronotype.get('primary_type', 'unknown')
                            confidence = chronotype.get('confidence_score', 0)
                            print(f"   🌅 Chronotype: {primary_type.title()} (Confidence: {confidence:.2f})")

                            if chronotype.get('assessment_basis'):
                                print(f"      Basis: {chronotype['assessment_basis']}")

                        # Energy zones
                        energy_zones = circadian_data.get('energy_zone_analysis', {})
                        if energy_zones:
                            print(f"   ⚡ Energy Windows:")
                            if energy_zones.get('peak_energy_window'):
                                print(f"      • Peak: {energy_zones['peak_energy_window']}")
                            if energy_zones.get('low_energy_window'):
                                print(f"      • Low: {energy_zones['low_energy_window']}")
                            if energy_zones.get('recovery_window'):
                                print(f"      • Recovery: {energy_zones['recovery_window']}")

                        # Schedule recommendations
                        schedule = circadian_data.get('schedule_recommendations', {})
                        if schedule:
                            print(f"   📅 Optimal Schedule:")
                            if schedule.get('optimal_wake_time'):
                                print(f"      • Wake: {schedule['optimal_wake_time']}")
                            if schedule.get('optimal_sleep_time'):
                                print(f"      • Sleep: {schedule['optimal_sleep_time']}")
                            if schedule.get('workout_window'):
                                print(f"      • Workout: {schedule['workout_window']}")

                        # Biomarker insights
                        biomarkers = circadian_data.get('biomarker_insights', {})
                        if biomarkers and isinstance(biomarkers, dict):
                            print(f"   📈 Key Biomarker Patterns:")
                            for key, value in list(biomarkers.items())[:3]:
                                if isinstance(value, str) and len(value) < 100:
                                    print(f"      • {key.replace('_', ' ').title()}: {value}")

                    # Log internal AI processing details
                    pass  # Production: Verbose print removed
                    if metadata.get('analysis_decision'):
                        print(f"   • Decision Path: {metadata['analysis_decision']}")
                    if metadata.get('personalization_level'):
                        print(f"   • Personalization: {metadata['personalization_level']}")
                    if metadata.get('archetype_used'):
                        print(f"   • Archetype Applied: {metadata['archetype_used']}")

                    # Show the actual AI model response structure
                    if circadian_data.get('model_used'):
                        print(f"   • AI Model Response: GPT-4o generated structured circadian analysis")
                        print(f"   • Response Format: JSON with chronotype, energy zones, schedule recommendations")
                        print(f"   • Prompt Strategy: Expert circadian rhythm analyst with biomarker integration")

                    if is_followup:
                        print(f"   • AI Context Integration: Previous analyses and new engagement data combined for enhanced accuracy")

                    return result
                else:
                    error = await response.text()
                    print(f"❌ Circadian analysis failed (HTTP {response.status})")
                    print(f"   Error: {error[:200]}...")
                    return None
    except Exception as e:
        print(f"❌ Error in circadian analysis: {e}")
        return None

async def user_journey():
    """Main user journey flow with insights after each generation"""
    print("\n" + "="*60)
    print("🚀 SIMPLE USER JOURNEY TEST WITH INSIGHTS")
    print("="*60)
    print(f"\nUser: {REAL_PROFILE_ID[:8]}...")
    print(f"Archetype: {TEST_ARCHETYPE}")
    
    # Check server
    if not await check_server():
        pass  # Production: Verbose print removed
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
            pass  # Production: Verbose print removed
            break
        
        # Generate insights after routine
        pass  # Production: Verbose print removed
        await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=True)

        # Note about integrated circadian analysis
        pass  # Production: Verbose print removed
        print("   • Parallel execution with behavior analysis")
        print("   • Combined data stored in database")
        print("   • Check logs folder for detailed agent handoff data")

        if get_user_choice("🔍 Generate additional insights from combined analysis?"):
            await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=False)
        else:
            pass  # Production: Verbose print removed

        # Ask if user wants nutrition
        if get_user_choice("📋 Generate nutrition plan using shared behavior analysis?"):
            # Step 2: Nutrition Generation (uses shared behavior)
            success = await generate_nutrition(REAL_PROFILE_ID, TEST_ARCHETYPE, is_followup)
            if not success:
                pass  # Production: Verbose print removed
            else:
                # Generate insights after nutrition
                pass  # Production: Verbose print removed
                await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=False)
        else:
            pass  # Production: Verbose print removed
        
        # Ask if user wants to continue with follow-up
        print(f"\n{'='*50}")
        if is_followup:
            continue_prompt = "🔄 Continue with another follow-up cycle?"
        else:
            continue_prompt = "🔄 Simulate progress and generate follow-up plans?"
        
        if not get_user_choice(continue_prompt):
            pass  # Production: Verbose print removed
            print(f"   Total cycles: {cycle_count}")
            
            # Show generated log files
            await show_generated_logs()
            break
        
        if not is_followup:
            print("\n⏳ Simulating time passing and new health data...")
            await asyncio.sleep(3)  # Simulate delay
            pass  # Production: Verbose print removed

async def quick_test():
    """Quick automated test without prompts - uses integrated parallel analysis"""
    print("\n🚀 QUICK AUTOMATED TEST WITH INTEGRATED PARALLEL ANALYSIS")
    print("="*70)

    if not await check_server():
        return False

    pass  # Production: Verbose print removed
    print("   (Includes parallel behavior + circadian analysis)")
    if not await generate_routine(REAL_PROFILE_ID, TEST_ARCHETYPE, False):
        return False
    await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=True)

    pass  # Production: Verbose print removed
    await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=False)

    pass  # Production: Verbose print removed
    if not await generate_nutrition(REAL_PROFILE_ID, TEST_ARCHETYPE, False):
        return False
    await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=False)

    pass  # Production: Verbose print removed
    print("   (Will re-run parallel analysis with AI context integration from previous session)")
    await asyncio.sleep(2)
    if not await generate_routine(REAL_PROFILE_ID, TEST_ARCHETYPE, True):
        return False
    await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=True)

    pass  # Production: Verbose print removed
    await generate_insights(REAL_PROFILE_ID, TEST_ARCHETYPE, force_refresh=False)
    
    pass  # Production: Verbose print removed
    
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
        pass  # Production: Verbose print removed
        print("This simulates a real user flow with the AI Context Integration system:")
        print("  1. Generate Routine (runs parallel behavior + circadian analysis with AI context)")
        print("  2. Generate AI Insights (extracts insights from AI context + analysis results)")
        print("  3. Generate Nutrition (uses shared behavior analysis and AI context)")
        print("  4. Generate AI Insights (additional insights from complete plan)")
        print("  5. Follow-up Analysis (uses 3-day engagement analysis + agent history)")
        print("  6. Generate AI Insights (progress & adaptation insights)")
        print("  7. Repeat as needed\n")
        print("🧠 AI CONTEXT INTEGRATION FLOW: /api/user/{user_id}/routine/generate endpoint now:")
        print("  • Generates 3-day engagement AI context (calendar/journal/checkins)")
        print("  • Retrieves last 2 behavior + circadian analyses for agent-specific history")
        print("  • Runs parallel behavior + circadian analysis with AI context enhancement")
        print("  • Stores results and updates AI context for future analyses")
        print("  • All data flow logged to logs/ folder for inspection\n")
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n\n👋 Test stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)