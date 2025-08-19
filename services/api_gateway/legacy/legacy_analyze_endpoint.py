"""
Legacy /api/analyze endpoint - moved from openai_main.py for maintainability
This endpoint is preserved for backward compatibility but not actively maintained

⚠️  DEPRECATED: Please migrate to modern endpoints:
- POST /api/user/{user_id}/behavior/analyze
- POST /api/user/{user_id}/routine/generate  
- POST /api/user/{user_id}/nutrition/generate
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

import openai
from fastapi import HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Legacy models
class AnalysisRequest(BaseModel):
    user_id: str
    archetype: str

class AnalysisResponse(BaseModel):
    status: str
    user_id: str
    archetype: str
    message: str
    analysis: Optional[Dict[str, Any]] = None

async def legacy_analyze_user(request: AnalysisRequest, http_request: Request):
    """
    LEGACY: User analysis endpoint - PHASE 3.1 REAL DATA INTEGRATION
    This endpoint has been moved from openai_main.py and is preserved for backward compatibility only.
    
    ⚠️  DEPRECATED: Please use modern endpoints:
    - POST /api/user/{user_id}/behavior/analyze
    - POST /api/user/{user_id}/routine/generate
    - POST /api/user/{user_id}/nutrition/generate
    
    The modern endpoints provide:
    - Better performance with 50-item threshold logic
    - Improved caching and memory management
    - More focused analysis results
    - Better error handling and monitoring
    """
    # Import rate limiting if available
    try:
        from shared_libs.rate_limiting.rate_limiter import rate_limiter
        RATE_LIMITING_AVAILABLE = True
    except ImportError:
        RATE_LIMITING_AVAILABLE = False
    
    # Apply rate limiting if available (strictest for expensive legacy analysis)
    if RATE_LIMITING_AVAILABLE:
        try:
            await rate_limiter.apply_rate_limit(http_request, "behavior_analysis")
        except Exception as rate_limit_error:
            print(f"⚠️ [RATE_LIMIT] Rate limit exceeded for user {request.user_id}: {rate_limit_error}")
            raise rate_limit_error
    
    try:
        user_id = request.user_id
        archetype = request.archetype
        
        print(f"🔍 [LEGACY] Starting LEGACY analysis for user: {user_id}, archetype: {archetype}")
        print(f"⚠️ [LEGACY] WARNING: This endpoint is deprecated. Use specific endpoints instead:")
        print(f"   • POST /api/user/{user_id}/behavior/analyze")
        print(f"   • POST /api/user/{user_id}/routine/generate")
        print(f"   • POST /api/user/{user_id}/nutrition/generate")
        
        # Import real data services
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt, get_archetype_adaptation
        
        # Import memory integration services
        from services.memory_integration_service import MemoryIntegrationService
        from services.agents.memory.enhanced_memory_prompts import EnhancedMemoryPromptsService
        from services.simple_analysis_tracker import SimpleAnalysisTracker as AnalysisTracker
        
        # Initialize UserDataService and AnalysisTracker for real data
        user_service = UserDataService()
        analysis_tracker = AnalysisTracker()
        
        # Initialize Memory Integration Service
        memory_service = MemoryIntegrationService()
        print(f"🧠 [LEGACY] Preparing memory-enhanced analysis context for {user_id}...")
        memory_context = await memory_service.prepare_memory_enhanced_context(user_id, None, archetype)
        
        # Initialize Enhanced Memory Prompts Service
        enhanced_prompts_service = EnhancedMemoryPromptsService()
        print(f"✨ [LEGACY] Initializing memory-enhanced prompt generation for {user_id}...")
        
        try:
            # SIMPLIFIED INCREMENTAL SYNC: Fetch data since last analysis
            # Use memory context to determine optimal data fetching strategy
            days_to_fetch = memory_context.days_to_fetch
            print(f"🧠 [LEGACY] Analysis mode: {memory_context.analysis_mode}, fetching {days_to_fetch} days of data")
            user_context, latest_data_timestamp = await user_service.get_analysis_data(user_id)
            
            # Extract real data for analysis
            data_quality = user_context.data_quality
            
            # Get system prompts and enhance with memory context
            base_behavior_prompt = get_system_prompt("behavior_analysis")
            base_nutrition_prompt = get_system_prompt("plan_generation") 
            base_routine_prompt = get_system_prompt("plan_generation")
            archetype_guidance = get_archetype_adaptation(archetype)
            
            # Enhance prompts with comprehensive memory context using new service
            print("✨ [LEGACY] Enhancing prompts with 4-layer memory intelligence...")
            behavior_prompt = await enhanced_prompts_service.enhance_agent_prompt(base_behavior_prompt, user_id, "behavior_analysis")
            nutrition_prompt = await enhanced_prompts_service.enhance_agent_prompt(base_nutrition_prompt, user_id, "nutrition_planning")
            routine_prompt = await enhanced_prompts_service.enhance_agent_prompt(base_routine_prompt, user_id, "routine_planning")
            
            print(f"🧠 [LEGACY] Memory-enhanced prompts prepared - Focus areas: {memory_context.personalized_focus_areas}")
            print(f"🧠 [LEGACY] Proven strategies available: {len(memory_context.proven_strategies)} strategies")
            
            # Create health context summary with AI-friendly language + Memory Context
            memory_summary = ""
            if memory_context.longterm_memory:
                memory_summary = f"""
MEMORY-ENHANCED CONTEXT:
- Analysis Mode: {memory_context.analysis_mode.upper()}
- User Memory Profile Available: YES
- Personalized Focus Areas: {', '.join(memory_context.personalized_focus_areas)}
- Proven Strategies: {len(memory_context.proven_strategies)} strategies identified
- Recent Pattern Analysis: {len(memory_context.recent_patterns)} patterns tracked
- Historical Analysis Count: {len(memory_context.analysis_history)}"""
            else:
                # Check if it's actually a follow-up despite no longterm memory yet
                if memory_context.analysis_mode == "follow_up":
                    memory_summary = f"""
MEMORY-ENHANCED CONTEXT:
- Analysis Mode: FOLLOW-UP (Building memory profile)
- User Memory Profile Available: PARTIAL (Previous analysis detected)
- Days Since Last Analysis: {memory_context.days_to_fetch}
- Analysis History: {len(memory_context.analysis_history)} previous analyses"""
                else:
                    memory_summary = f"""
MEMORY-ENHANCED CONTEXT:
- Analysis Mode: {memory_context.analysis_mode.upper()} (New user)
- User Memory Profile Available: NO (Building initial memory)"""

            # Import helper functions
            from services.api_gateway.openai_main import format_health_data_for_ai
            
            user_context_summary = f"""
HEALTH ANALYSIS REQUEST - LEGACY MEMORY-ENHANCED COMPREHENSIVE DATA:
- Profile Reference: {user_id}
- Health Archetype: {archetype}
- Analysis Date: {datetime.now().strftime('%Y-%m-%d')}
- Mode: LEGACY Memory-Enhanced Health Analysis

{memory_summary}

HEALTH DATA PROFILE:
- Data Quality Level: {data_quality.quality_level} 
- Health Score Samples: {data_quality.scores_count}
- Biomarker Measurements: {data_quality.biomarkers_count}
- Data Coverage: {data_quality.completeness_score:.1%}
- Recent Measurements: {data_quality.has_recent_data}
- Time Period: {user_context.date_range.start_date.strftime('%Y-%m-%d')} to {user_context.date_range.end_date.strftime('%Y-%m-%d')}

HEALTH TRACKING DATA SUMMARY:
{await format_health_data_for_ai(user_context)}

ARCHETYPE FRAMEWORK:
{archetype_guidance}

ANALYSIS INSTRUCTIONS: You have comprehensive health tracking data including sleep patterns, activity metrics, and biomarker readings, enhanced with user memory context. Analyze these health indicators to identify patterns, trends, and insights that align with the {archetype} framework. Focus on actionable observations from the provided health metrics while considering the user's memory profile and proven strategies.

⚠️  LEGACY MODE: This is a deprecated endpoint with limited functionality compared to modern endpoints.
"""
            
        except Exception as data_error:
            print(f"⚠️ [LEGACY] Real data fetch failed for {user_id}: {data_error}")
            
            # Fallback to original mock data approach if real data fails
            user_context_summary = f"""
HEALTH ANALYSIS REQUEST - LEGACY SAMPLE MODE:
- Profile Reference: {user_id}
- Health Archetype: {archetype}
- Analysis Date: {datetime.now().strftime('%Y-%m-%d')}
- Mode: Legacy Sample Analysis (Health data unavailable)

ARCHETYPE FRAMEWORK:
{get_archetype_adaptation(archetype)}

Note: Comprehensive health data was unavailable for {user_id}, using legacy sample analysis patterns.
Please provide a detailed analysis that demonstrates the {archetype} approach to health optimization.

⚠️  LEGACY MODE: This endpoint is deprecated. Use modern endpoints for better functionality.
"""
        finally:
            # Always cleanup the services
            await user_service.cleanup()
            if 'analysis_tracker' in locals():
                await analysis_tracker.cleanup()
            if 'memory_service' in locals():
                await memory_service.cleanup()
            if 'enhanced_prompts_service' in locals():
                await enhanced_prompts_service.cleanup()

        # Run simplified legacy analysis
        print("🧠 [LEGACY] Running legacy behavior analysis...")
        behavior_analysis = await run_legacy_behavior_analysis(behavior_prompt, user_context_summary)
        
        print("🥗 [LEGACY] Running legacy nutrition planning...")
        nutrition_plan = await run_legacy_nutrition_planning(nutrition_prompt, user_context_summary, behavior_analysis, archetype)
        
        print("🏃‍♂️ [LEGACY] Running legacy routine planning...")
        routine_plan = await run_legacy_routine_planning(routine_prompt, user_context_summary, behavior_analysis, archetype)
        
        # Store results in memory if available
        try:
            await memory_service.store_analysis_insights(user_id, "behavior_analysis", behavior_analysis, archetype)
            await memory_service.store_analysis_insights(user_id, "nutrition_plan", nutrition_plan, archetype)
            await memory_service.store_analysis_insights(user_id, "routine_plan", routine_plan, archetype)
            await memory_service.update_user_memory_profile(user_id, behavior_analysis, nutrition_plan, routine_plan)
        except Exception as e:
            print(f"⚠️ [LEGACY] Failed to store memory insights: {e}")
        
        # Track API cost if available
        if RATE_LIMITING_AVAILABLE:
            try:
                await rate_limiter.track_api_cost(user_id, "behavior_analysis")
            except Exception as cost_error:
                print(f"⚠️ [LEGACY] Failed to track cost: {cost_error}")
        
        return AnalysisResponse(
            status="success",
            user_id=user_id,
            archetype=archetype,
            message="LEGACY analysis completed. ⚠️  Please migrate to modern endpoints for better performance and features.",
            analysis={
                "behavior_analysis": behavior_analysis,
                "nutrition_plan": nutrition_plan,
                "routine_plan": routine_plan,
                "system_info": {
                    "mode": "DEPRECATED_LEGACY",
                    "prompt_system": "HolisticOS Legacy",
                    "archetype_applied": archetype,
                    "phase": "Legacy - Deprecated",
                    "deprecation_warning": "This endpoint is deprecated. Use specific user endpoints instead.",
                    "modern_endpoints": {
                        "behavior": f"POST /api/user/{user_id}/behavior/analyze",
                        "routine": f"POST /api/user/{user_id}/routine/generate", 
                        "nutrition": f"POST /api/user/{user_id}/nutrition/generate"
                    },
                    "models_used": {
                        "behavior_analysis": "gpt-4o (legacy)",
                        "nutrition_plan": "gpt-4o (legacy)",
                        "routine_plan": "gpt-4o (legacy)"
                    }
                }
            }
        )
        
    except Exception as e:
        print(f"❌ [LEGACY] Analysis failed for {request.user_id}: {str(e)}")
        return AnalysisResponse(
            status="error",
            user_id=request.user_id,
            archetype=request.archetype,
            message=f"Legacy analysis failed: {str(e)}. Consider using modern endpoints."
        )

async def run_legacy_behavior_analysis(system_prompt: str, user_context: str) -> dict:
    """Simplified legacy behavior analysis"""
    try:
        client = openai.AsyncOpenAI()
        
        response = await client.chat.completions.create(
            model="gpt-4o",  # Use 4o for legacy compatibility
            messages=[
                {"role": "system", "content": f"{system_prompt}\n\nLEGACY MODE: Provide simplified behavioral analysis."},
                {"role": "user", "content": f"{user_context}\n\nProvide a behavioral analysis in JSON format."}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        try:
            analysis_data = json.loads(content)
            analysis_data["model_used"] = "gpt-4o (legacy)"
            analysis_data["mode"] = "DEPRECATED_LEGACY"
            return analysis_data
        except json.JSONDecodeError:
            return {
                "error": "JSON parse error", 
                "model_used": "gpt-4o (legacy)", 
                "mode": "DEPRECATED_LEGACY",
                "content": content
            }
            
    except Exception as e:
        return {
            "error": str(e), 
            "model_used": "gpt-4o (legacy fallback)",
            "mode": "DEPRECATED_LEGACY"
        }

async def run_legacy_nutrition_planning(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str) -> dict:
    """Simplified legacy nutrition planning"""
    try:
        client = openai.AsyncOpenAI()
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"{system_prompt}\n\nLEGACY MODE: Provide simplified nutrition planning."},
                {"role": "user", "content": f"{user_context}\n\nBehavioral Context: {json.dumps(behavior_analysis, cls=DateTimeEncoder)}\n\nCreate a basic {archetype} nutrition plan."}
            ],
            temperature=0.4,
            max_tokens=1500
        )
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "archetype": archetype,
            "content": response.choices[0].message.content,
            "model_used": "gpt-4o (legacy)",
            "plan_type": "legacy_nutrition",
            "mode": "DEPRECATED_LEGACY"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "model_used": "gpt-4o (legacy fallback)",
            "archetype": archetype,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "mode": "DEPRECATED_LEGACY"
        }

async def run_legacy_routine_planning(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str) -> dict:
    """Simplified legacy routine planning"""
    try:
        client = openai.AsyncOpenAI()
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"{system_prompt}\n\nLEGACY MODE: Provide simplified routine planning."},
                {"role": "user", "content": f"{user_context}\n\nBehavioral Context: {json.dumps(behavior_analysis, cls=DateTimeEncoder)}\n\nCreate a basic {archetype} routine plan."}
            ],
            temperature=0.4,
            max_tokens=1500
        )
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "archetype": archetype,
            "content": response.choices[0].message.content,
            "model_used": "gpt-4o (legacy)",
            "plan_type": "legacy_routine",
            "mode": "DEPRECATED_LEGACY"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "model_used": "gpt-4o (legacy fallback)",
            "archetype": archetype,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "mode": "DEPRECATED_LEGACY"
        }