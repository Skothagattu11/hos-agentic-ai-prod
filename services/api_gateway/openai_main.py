"""
HolisticOS Enhanced API Gateway
Multi-Agent System with Memory, Insights, and Adaptation capabilities
Supports both Phase 1 (simple) and Phase 2 (complete multi-agent) workflows
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import openai

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = FastAPI(
    title="HolisticOS Enhanced API Gateway", 
    version="2.0.0",
    description="Multi-Agent Health Optimization System with Memory, Insights, and Adaptation"
)

# Integrate Phase 2 Health Data Endpoints - CTO Integration
try:
    from .health_data_endpoints import router as health_data_router
    app.include_router(health_data_router)
    print("✅ [INTEGRATION] Health data endpoints added successfully")
    print("📡 [ENDPOINTS] Real user data endpoints now available:")
except ImportError as e:
    print(f"⚠️  [WARNING] Health data endpoints not available: {e}")
except Exception as e:
    print(f"❌ [ERROR] Failed to integrate health data endpoints: {e}")

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Global variables for agent instances (initialized on startup)
orchestrator = None
memory_agent = None
insights_agent = None
adaptation_agent = None

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

# Legacy Phase 1 Models
class AnalysisRequest(BaseModel):
    user_id: str
    archetype: str

class AnalysisResponse(BaseModel):
    status: str
    user_id: str
    archetype: str
    message: str
    analysis: Optional[Dict[str, Any]] = None

# Enhanced Phase 2 Models
class CompleteAnalysisRequest(BaseModel):
    user_id: str
    archetype: str
    analysis_number: Optional[int] = 1
    preferences: Optional[Dict[str, Any]] = None

class CompleteAnalysisResponse(BaseModel):
    status: str
    workflow_id: str
    user_id: str
    archetype: str
    message: str
    current_stage: str
    estimated_completion_minutes: int

class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    user_id: str
    current_stage: str
    completed_stages: List[str]
    progress_percentage: int
    start_time: str
    estimated_completion: Optional[str] = None
    results_available: List[str]

class InsightsRequest(BaseModel):
    user_id: str
    archetype: str
    insight_type: str = "comprehensive"  # comprehensive, patterns, trends
    time_horizon: str = "medium_term"    # short_term, medium_term, long_term
    focus_areas: Optional[List[str]] = None

class InsightsResponse(BaseModel):
    status: str
    user_id: str
    insights: List[Dict[str, Any]]
    confidence_score: float
    recommendations: List[str]
    patterns_identified: int

class AdaptationRequest(BaseModel):
    user_id: str
    archetype: str
    trigger: str  # poor_adherence, engagement_decline, user_feedback, etc.
    context: Dict[str, Any]
    urgency: str = "medium"  # low, medium, high, critical
    user_feedback: Optional[str] = None

class AdaptationResponse(BaseModel):
    status: str
    user_id: str
    adaptations_made: List[Dict[str, Any]]
    confidence: float
    expected_impact: str
    monitoring_plan: Dict[str, Any]

class MemoryRequest(BaseModel):
    user_id: str
    memory_type: str = "all"  # all, working, shortterm, longterm, meta
    category: Optional[str] = None
    query_context: Optional[str] = None

class MemoryResponse(BaseModel):
    status: str
    user_id: str
    memory_data: Dict[str, Any]
    insights: List[str]
    retrieved_at: str

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    version: str
    system: str
    agents_status: Optional[Dict[str, str]] = None

# On-Demand Plan Generation Models
class PlanGenerationRequest(BaseModel):
    archetype: Optional[str] = None  # Use stored archetype if not provided
    preferences: Optional[Dict[str, Any]] = None  # User preferences for customization

class RoutinePlanResponse(BaseModel):
    status: str
    user_id: str
    routine_plan: Dict[str, Any]
    generation_metadata: Dict[str, Any]
    cached: bool = False

class NutritionPlanResponse(BaseModel):
    status: str
    user_id: str
    nutrition_plan: Dict[str, Any]
    generation_metadata: Dict[str, Any]
    cached: bool = False

<<<<<<< HEAD
=======
# New Behavior Analysis Models
class BehaviorAnalysisRequest(BaseModel):
    force_refresh: Optional[bool] = False
    archetype: Optional[str] = None

class BehaviorAnalysisResponse(BaseModel):
    status: str
    user_id: str
    analysis_type: str  # "fresh", "cached"
    behavior_analysis: Dict[str, Any]
    metadata: Dict[str, Any]

>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
# ============================================================================
# AGENT INITIALIZATION
# ============================================================================

@app.on_event("startup")
async def initialize_agents():
    """Initialize all agents on startup"""
    global orchestrator, memory_agent, insights_agent, adaptation_agent
    
    try:
        print("🚀 Initializing HolisticOS Multi-Agent System...")
        
        # Initialize agents
        from services.orchestrator.main import HolisticOrchestrator
        from services.agents.memory.main import HolisticMemoryAgent
        from services.agents.insights.main import HolisticInsightsAgent
        from services.agents.adaptation.main import HolisticAdaptationEngine
        
        orchestrator = HolisticOrchestrator()
        memory_agent = HolisticMemoryAgent()
        insights_agent = HolisticInsightsAgent()
        adaptation_agent = HolisticAdaptationEngine()
        
        # REMOVED: Automatic background scheduler - now using on-demand analysis
        # Behavior analysis will be triggered only when routine/nutrition plans are requested
        print("✅ Using on-demand behavior analysis (automatic scheduler disabled)")
        
        print("✅ All agents initialized successfully")
        
    except Exception as e:
        print(f"❌ Error initializing agents: {e}")
        # Continue with limited functionality
        pass

@app.on_event("shutdown")
async def shutdown_agents():
    """Clean shutdown of all agents and services"""
    try:
        print("🛑 Shutting down HolisticOS Multi-Agent System...")
        
        # Stop behavior analysis scheduler
        from services.scheduler.behavior_analysis_scheduler import stop_behavior_analysis_scheduler
        await stop_behavior_analysis_scheduler()
        
        print("✅ All agents shut down successfully")
        
    except Exception as e:
        print(f"❌ Error during shutdown: {e}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_score_actual_date(score) -> str:
    """
    Get actual data occurrence date from score_date_time, with fallback to created_at
    
    Args:
        score: HealthScore object with score_date_time and created_at fields
        
    Returns:
        str: Date in YYYY-MM-DD format representing when the data actually occurred
    """
    try:
        # Prefer score_date_time (actual data occurrence date)
        if hasattr(score, 'score_date_time') and score.score_date_time:
            if isinstance(score.score_date_time, str):
                # Handle string datetime formats
                return datetime.fromisoformat(score.score_date_time.replace('Z', '+00:00')).strftime("%Y-%m-%d")
            else:
                # Handle datetime objects
                return score.score_date_time.strftime("%Y-%m-%d")
    except (ValueError, AttributeError) as e:
        print(f"⚠️ Date parsing issue for score_date_time: {e}, falling back to created_at")
    
    # Fallback to created_at if score_date_time is unavailable/invalid
    if hasattr(score, 'created_at') and score.created_at:
        return score.created_at.strftime("%Y-%m-%d")
    
    # Last resort fallback
    return datetime.now().strftime("%Y-%m-%d")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with system status"""
    agent_status = {}
    if orchestrator:
        agent_status["orchestrator"] = "ready"
    if memory_agent:
        agent_status["memory"] = "ready"
    if insights_agent:
        agent_status["insights"] = "ready"
    if adaptation_agent:
        agent_status["adaptation"] = "ready"
    
    return {
        "message": "HolisticOS Enhanced API Gateway", 
        "status": "running", 
        "version": "2.0.0",
        "mode": "Phase 2 - Complete Multi-Agent System",
        "agents": agent_status,
        "capabilities": [
            "Legacy Analysis (Phase 1)",
            "Complete Multi-Agent Workflows (Phase 2)",
            "Memory Management",
            "AI-Powered Insights", 
            "Strategy Adaptation",
            "Workflow Orchestration"
        ]
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with agent status"""
    agent_status = {}
    
    # Check each agent's status
    if orchestrator:
        agent_status["orchestrator"] = "healthy"
    else:
        agent_status["orchestrator"] = "not_initialized"
        
    if memory_agent:
        agent_status["memory"] = "healthy"
    else:
        agent_status["memory"] = "not_initialized"
        
    if insights_agent:
        agent_status["insights"] = "healthy"
    else:
        agent_status["insights"] = "not_initialized"
        
    if adaptation_agent:
        agent_status["adaptation"] = "healthy"
    else:
        agent_status["adaptation"] = "not_initialized"
    
    # Overall system health
    all_agents_healthy = all(status == "healthy" for status in agent_status.values())
    system_status = "healthy" if all_agents_healthy else "degraded"
    
    return HealthResponse(
        status=system_status,
        message=f"HolisticOS Enhanced API Gateway - {len([s for s in agent_status.values() if s == 'healthy'])}/4 agents healthy",
        timestamp=datetime.now().isoformat(),
        version="2.0.0", 
        system="HolisticOS Multi-Agent MVP",
        agents_status=agent_status
    )

# ============================================================================
# ON-DEMAND PLAN GENERATION ENDPOINTS
# ============================================================================

@app.get("/api/user/{user_id}/routine/latest", response_model=RoutinePlanResponse)
async def get_latest_routine_plan(user_id: str):
    """
    Get the most recent routine plan based on latest behavior analysis
    Fast endpoint - uses cached analysis results
    """
    try:
        print(f"📋 [ROUTINE_API] Getting latest routine for user {user_id[:8]}...")
        
        # Get latest behavior analysis from memory
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        memory_service = HolisticMemoryService()
        
        try:
            # Get most recent analysis that includes routine plan
            analysis_history = await memory_service.get_analysis_history(user_id, limit=3)
            
            # Find most recent analysis with routine plan
            routine_plan = None
            behavior_analysis = None
            
            for analysis in analysis_history:
                analysis_result = analysis.analysis_result
                if isinstance(analysis_result, dict) and 'routine_plan' in analysis_result:
                    routine_plan = analysis_result['routine_plan']
                    behavior_analysis = analysis_result.get('behavior_analysis', {})
                    break
            
            if not routine_plan:
                return RoutinePlanResponse(
                    status="not_found",
                    user_id=user_id,
                    routine_plan={},
                    generation_metadata={
                        "error": "No recent routine plan found. Please run a behavior analysis first.",
                        "suggestion": "Use POST /api/analyze to generate initial analysis"
                    },
                    cached=False
                )
            
            # Return cached routine with metadata
            return RoutinePlanResponse(
                status="success",
                user_id=user_id,
                routine_plan=routine_plan,
                generation_metadata={
                    "data_quality": "cached",
                    "personalization_level": "high",
                    "generated_from": "latest_behavior_analysis",
                    "analysis_date": analysis_history[0].created_at.isoformat()
                },
                cached=True
            )
            
        finally:
            await memory_service.cleanup()
            
    except Exception as e:
        print(f"❌ [ROUTINE_API_ERROR] Failed to get routine for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve routine plan: {str(e)}")

@app.post("/api/user/{user_id}/routine/generate", response_model=RoutinePlanResponse)
async def generate_fresh_routine_plan(user_id: str, request: PlanGenerationRequest):
    """
<<<<<<< HEAD
    Generate a routine plan with intelligent on-demand behavior analysis
    Checks data threshold and decides whether to run fresh analysis or use cache
=======
    Generate a routine plan using the standalone behavior analysis endpoint
    Calls POST /api/user/{user_id}/behavior/analyze to get analysis, then generates routine
>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
    """
    try:
        print(f"🔄 [ROUTINE_GENERATE] Processing routine request for user {user_id[:8]}...")
        
<<<<<<< HEAD
        # Import required services
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        from services.agents.routine.main import run_routine_planning_gpt4o
        from services.agents.memory.enhanced_memory_prompts import EnhancedMemoryPromptsService
        
        # Initialize services
        ondemand_service = await get_ondemand_service()
        memory_service = HolisticMemoryService()
        enhanced_prompts_service = EnhancedMemoryPromptsService()
        
        try:
            # Check if we should run fresh analysis
            force_refresh = request.preferences.get('force_refresh', False) if request.preferences else False
            decision, metadata = await ondemand_service.should_run_analysis(user_id, force_refresh)
            
            print(f"📊 [ROUTINE_GENERATE] Analysis decision: {decision.value}")
            print(f"   • New data points: {metadata['new_data_points']}")
            print(f"   • Threshold: {metadata['threshold_used']}")
            print(f"   • Memory quality: {metadata['memory_quality'].value}")
            print(f"   • Reason: {metadata['reason']}")
            
            behavior_analysis = None
            analysis_freshness = "unknown"
            
            # Handle decision
            if decision == AnalysisDecision.FRESH_ANALYSIS or decision == AnalysisDecision.STALE_FORCE_REFRESH:
                # Run fresh behavior analysis
                print(f"🚀 [ROUTINE_GENERATE] Running fresh behavior analysis...")
                
                archetype = request.archetype or "Foundation Builder"
                analysis_result = await run_complete_health_analysis(user_id, archetype)
                
                if analysis_result['status'] == 'success':
                    behavior_analysis = analysis_result.get('behavior_analysis', {})
                    analysis_freshness = "fresh"
                    print(f"✅ [ROUTINE_GENERATE] Fresh analysis completed")
                else:
                    print(f"❌ [ROUTINE_GENERATE] Fresh analysis failed, attempting cache...")
                    behavior_analysis = await ondemand_service.get_cached_behavior_analysis(user_id)
                    analysis_freshness = "cache_fallback"
            else:
                # Use cached analysis with memory enhancement
                print(f"💾 [ROUTINE_GENERATE] Using cached analysis with memory enhancement")
                behavior_analysis = await ondemand_service.get_cached_behavior_analysis(user_id)
                analysis_freshness = "memory_enhanced_cache"
            
            # Check if we have behavior analysis
            if not behavior_analysis:
                return RoutinePlanResponse(
                    status="error",
                    user_id=user_id,
                    routine_plan={},
                    generation_metadata={
                        "error": "No behavior analysis available",
                        "suggestion": "Run POST /api/analyze to generate initial analysis",
                        "decision_metadata": metadata
                    },
                    cached=False
                )
            
            # Get archetype from analysis or request
            archetype = request.archetype
            if not archetype:
                # Try to get from memory
                analysis_history = await memory_service.get_analysis_history(user_id, limit=1)
                if analysis_history:
                    archetype = analysis_history[0].archetype_used
                archetype = archetype or "Foundation Builder"
            
            # Get fresh user data context
            from services.user_data_service import UserDataService
            user_service = UserDataService()
            
            try:
                user_context, _ = await user_service.get_analysis_data(user_id)
                
                # Prepare routine data with preferences
                routine_data = await prepare_routine_agent_data(user_context, behavior_analysis)
                
                # Add user preferences if provided
                if request.preferences:
                    routine_data['user_preferences'] = request.preferences
                    print(f"🎯 [ROUTINE_GENERATE] Applied user preferences: {list(request.preferences.keys())}")
                
                # Generate fresh routine with memory-enhanced prompts
                print(f"✨ [ROUTINE_GENERATE] Generating with memory-enhanced {archetype} prompts...")
                
                # Get enhanced prompt with memory context
                from shared_libs.utils.system_prompts import get_system_prompt
                base_routine_prompt = get_system_prompt("plan_generation")
                enhanced_routine_prompt = await enhanced_prompts_service.enhance_agent_prompt(
                    base_routine_prompt, user_id, "routine_planning"
                )
                
                routine_plan = await run_routine_planning_gpt4o(
                    system_prompt=enhanced_routine_prompt,
                    user_context_summary=f"Memory-enhanced routine generation for {archetype} user with recent health data and preferences.",
                    behavior_analysis=behavior_analysis,
                    routine_data=routine_data
                )
                
                return RoutinePlanResponse(
                    status="success",
                    user_id=user_id,
                    routine_plan=routine_plan,
                    generation_metadata={
                        "analysis_decision": decision.value,
                        "analysis_freshness": metadata,
                        "data_quality": "fresh" if decision == AnalysisDecision.FRESH_ANALYSIS else "cached_enhanced",
                        "personalization_level": "high",
                        "archetype_used": archetype,
                        "preferences_applied": bool(request.preferences),
                        "generation_time": datetime.now().isoformat()
                    },
                    cached=(decision == AnalysisDecision.MEMORY_ENHANCED_CACHE)
                )
                
            finally:
                await user_service.cleanup()
                
        finally:
            await memory_service.cleanup()
            await enhanced_prompts_service.cleanup()
            await ondemand_service.cleanup()
=======
        # Get behavior analysis from the standalone endpoint
        force_refresh = request.preferences.get('force_refresh', False) if request.preferences else False
        archetype = request.archetype or "Foundation Builder"
        
        # Create behavior analysis request
        behavior_request = BehaviorAnalysisRequest(
            force_refresh=force_refresh,
            archetype=archetype
        )
        
        # Use shared behavior analysis (eliminates duplicate analysis calls)
        print(f"📞 [ROUTINE_GENERATE] Getting shared behavior analysis...")
        behavior_analysis = await get_or_create_shared_behavior_analysis(user_id, archetype, force_refresh)
        
        if not behavior_analysis:
            return RoutinePlanResponse(
                status="error",
                user_id=user_id,
                routine_plan={},
                generation_metadata={
                    "error": "Behavior analysis failed or returned no results",
                    "suggestion": "Try with force_refresh=true or ensure user has sufficient health data"
                },
                cached=False
            )
        
        analysis_type = "shared"  # Indicates shared analysis was used
        
        print(f"✅ [ROUTINE_GENERATE] Got shared behavior analysis ({analysis_type})")
        print(f"   • Analysis source: Shared behavior analysis service")
        print(f"   • Eliminates duplicate OpenAI calls")
        
        # Get user data for routine generation
        from services.user_data_service import UserDataService
        user_service = UserDataService()
        
        try:
            user_context, _ = await user_service.get_analysis_data(user_id)
            
            # Generate routine using existing function
            from shared_libs.utils.system_prompts import get_system_prompt
            from services.agents.memory.enhanced_memory_prompts import EnhancedMemoryPromptsService
            
            enhanced_prompts_service = EnhancedMemoryPromptsService()
            base_routine_prompt = get_system_prompt("plan_generation")
            enhanced_routine_prompt = await enhanced_prompts_service.enhance_agent_prompt(
                base_routine_prompt, user_id, "routine_planning"
            )
            
            # Use the memory-enhanced routine generation function with all /api/analyze features
            routine_plan = await run_memory_enhanced_routine_generation(
                user_id=user_id,
                archetype=archetype,
                behavior_analysis=behavior_analysis
            )
            
            return RoutinePlanResponse(
                status="success",
                user_id=user_id,
                routine_plan=routine_plan,
                generation_metadata={
                    "analysis_decision": "shared_behavior_analysis_service",
                    "analysis_type": analysis_type,
                    "data_quality": "memory_enhanced",
                    "shared_analysis": True,
                    "duplicate_calls_eliminated": True,
                    "personalization_level": "high",
                    "archetype_used": archetype,
                    "preferences_applied": bool(request.preferences),
                    "generation_time": datetime.now().isoformat()
                },
                cached=(analysis_type == "cached")
            )
            
        except Exception as context_error:
            print(f"⚠️ [ROUTINE_GENERATE] User context error: {context_error}")
            raise HTTPException(status_code=500, detail=f"Failed to get user data for routine generation: {str(context_error)}")
>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
            
    except Exception as e:
        print(f"❌ [ROUTINE_GENERATE_ERROR] Failed to generate routine for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate routine plan: {str(e)}")

@app.get("/api/user/{user_id}/nutrition/latest", response_model=NutritionPlanResponse)
async def get_latest_nutrition_plan(user_id: str):
    """
    Get the most recent nutrition plan based on latest behavior analysis
    Fast endpoint - uses cached analysis results
    """
    try:
        print(f"🥗 [NUTRITION_API] Getting latest nutrition for user {user_id[:8]}...")
        
        # Get latest behavior analysis from memory
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        memory_service = HolisticMemoryService()
        
        try:
            # Get most recent analysis that includes nutrition plan
            analysis_history = await memory_service.get_analysis_history(user_id, limit=3)
            
            # Find most recent analysis with nutrition plan
            nutrition_plan = None
            behavior_analysis = None
            
            for analysis in analysis_history:
                analysis_result = analysis.analysis_result
                if isinstance(analysis_result, dict) and 'nutrition_plan' in analysis_result:
                    nutrition_plan = analysis_result['nutrition_plan']
                    behavior_analysis = analysis_result.get('behavior_analysis', {})
                    break
            
            if not nutrition_plan:
                return NutritionPlanResponse(
                    status="not_found",
                    user_id=user_id,
                    nutrition_plan={},
                    generation_metadata={
                        "error": "No recent nutrition plan found. Please run a behavior analysis first.",
                        "suggestion": "Use POST /api/analyze to generate initial analysis"
                    },
                    cached=False
                )
            
            # Return cached nutrition with metadata
            return NutritionPlanResponse(
                status="success",
                user_id=user_id,
                nutrition_plan=nutrition_plan,
                generation_metadata={
                    "data_quality": "cached",
                    "personalization_level": "high",
                    "generated_from": "latest_behavior_analysis",
                    "analysis_date": analysis_history[0].created_at.isoformat()
                },
                cached=True
            )
            
        finally:
            await memory_service.cleanup()
            
    except Exception as e:
        print(f"❌ [NUTRITION_API_ERROR] Failed to get nutrition for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve nutrition plan: {str(e)}")

@app.post("/api/user/{user_id}/nutrition/generate", response_model=NutritionPlanResponse)
async def generate_fresh_nutrition_plan(user_id: str, request: PlanGenerationRequest):
    """
<<<<<<< HEAD
    Generate a fresh nutrition plan with smart on-demand behavior analysis
    Only runs fresh analysis when data thresholds are exceeded, otherwise uses cached analysis
    """
    try:
        print(f"🔄 [NUTRITION_GENERATE] Smart nutrition generation for user {user_id[:8]}...")
        
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        from services.agents.nutrition.main import run_nutrition_planning_gpt4o
        from services.agents.memory.enhanced_memory_prompts import EnhancedMemoryPromptsService
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        
        memory_service = HolisticMemoryService()
        enhanced_prompts_service = EnhancedMemoryPromptsService()
        ondemand_service = await get_ondemand_service()
        
        try:
            # Smart decision: Should we run fresh analysis?
            decision, metadata = await ondemand_service.should_run_analysis(
                user_id, 
                force_refresh=request.force_refresh if hasattr(request, 'force_refresh') else False
            )
            
            print(f"🧠 [NUTRITION_SMART] Decision: {decision.value} - {metadata['reason']}")
            
            behavior_analysis = None
            
            if decision == AnalysisDecision.FRESH_ANALYSIS or decision == AnalysisDecision.STALE_FORCE_REFRESH:
                # Run fresh behavior analysis
                print(f"🔄 [NUTRITION_SMART] Running fresh behavior analysis...")
                
                # Get archetype for analysis
                archetype = request.archetype or "Foundation Builder"
                
                # Run complete analysis using existing system
                analysis_result = await run_complete_health_analysis(user_id, archetype)
                
                if analysis_result and analysis_result.get('status') == 'success':
                    behavior_analysis = analysis_result.get('behavior_analysis', {})
                    print(f"✅ [NUTRITION_SMART] Fresh analysis completed")
                else:
                    # Fallback to cached if fresh analysis fails
                    print(f"⚠️ [NUTRITION_SMART] Fresh analysis failed, using cached...")
                    behavior_analysis = await ondemand_service.get_cached_behavior_analysis(user_id)
            else:
                # Use cached behavior analysis with memory enhancement
                print(f"📋 [NUTRITION_SMART] Using cached analysis with memory enhancement...")
                behavior_analysis = await ondemand_service.get_cached_behavior_analysis(user_id)
            
            # Validate we have behavior analysis
            if not behavior_analysis:
                return NutritionPlanResponse(
                    status="error",
                    user_id=user_id,
                    nutrition_plan={},
                    generation_metadata={
                        "error": "No behavior analysis available",
                        "suggestion": "Run POST /api/analyze to generate initial analysis",
                        "decision_metadata": metadata
                    },
                    cached=False
                )
            
            # Get archetype from analysis or request
            archetype = request.archetype
            if not archetype:
                # Try to get from memory
                analysis_history = await memory_service.get_analysis_history(user_id, limit=1)
                if analysis_history:
                    archetype = analysis_history[0].archetype_used
                archetype = archetype or "Foundation Builder"
            
            # Get fresh user data context
            from services.user_data_service import UserDataService
            user_service = UserDataService()
            
            try:
                user_context, _ = await user_service.get_analysis_data(user_id)
                
                # Prepare nutrition data with preferences
                nutrition_data = await prepare_nutrition_agent_data(user_context, behavior_analysis)
                
                # Add user preferences if provided
                if request.preferences:
                    nutrition_data['user_preferences'] = request.preferences
                    print(f"🎯 [NUTRITION_GENERATE] Applied user preferences: {list(request.preferences.keys())}")
                
                # Generate fresh nutrition plan with memory-enhanced prompts
                print(f"✨ [NUTRITION_GENERATE] Generating with memory-enhanced {archetype} prompts...")
                
                # Get enhanced prompt with memory context
                from shared_libs.utils.system_prompts import get_system_prompt
                base_nutrition_prompt = get_system_prompt("plan_generation")
                enhanced_nutrition_prompt = await enhanced_prompts_service.enhance_agent_prompt(
                    base_nutrition_prompt, user_id, "nutrition_planning"
                )
                
                nutrition_plan = await run_nutrition_planning_gpt4o(
                    system_prompt=enhanced_nutrition_prompt,
                    user_context_summary=f"Memory-enhanced nutrition planning for {archetype} user with recent health data and preferences.",
                    behavior_analysis=behavior_analysis,
                    nutrition_data=nutrition_data
                )
                
                return NutritionPlanResponse(
                    status="success",
                    user_id=user_id,
                    nutrition_plan=nutrition_plan,
                    generation_metadata={
                        "analysis_decision": decision.value,
                        "analysis_freshness": metadata,
                        "data_quality": "fresh" if decision == AnalysisDecision.FRESH_ANALYSIS else "cached_enhanced",
                        "personalization_level": "high",
                        "archetype_used": archetype,
                        "preferences_applied": bool(request.preferences),
                        "generation_time": datetime.now().isoformat()
                    },
                    cached=(decision == AnalysisDecision.MEMORY_ENHANCED_CACHE)
                )
                
            finally:
                await user_service.cleanup()
                
        finally:
            await memory_service.cleanup()
            await enhanced_prompts_service.cleanup()
            await ondemand_service.cleanup()
=======
    Generate a nutrition plan using the standalone behavior analysis endpoint
    Calls POST /api/user/{user_id}/behavior/analyze to get analysis, then generates nutrition plan
    """
    try:
        print(f"🔄 [NUTRITION_GENERATE] Processing nutrition request for user {user_id[:8]}...")
        
        # Get behavior analysis from the standalone endpoint
        force_refresh = request.preferences.get('force_refresh', False) if request.preferences else False
        archetype = request.archetype or "Foundation Builder"
        
        # Create behavior analysis request
        behavior_request = BehaviorAnalysisRequest(
            force_refresh=force_refresh,
            archetype=archetype
        )
        
        # Use shared behavior analysis (eliminates duplicate analysis calls)
        print(f"📞 [NUTRITION_GENERATE] Getting shared behavior analysis...")
        behavior_analysis = await get_or_create_shared_behavior_analysis(user_id, archetype, force_refresh)
        
        if not behavior_analysis:
            return NutritionPlanResponse(
                status="error",
                user_id=user_id,
                nutrition_plan={},
                generation_metadata={
                    "error": "Behavior analysis failed or returned no results",
                    "suggestion": "Try with force_refresh=true or ensure user has sufficient health data"
                },
                cached=False
            )
        
        analysis_type = "shared"  # Indicates shared analysis was used
        
        print(f"✅ [NUTRITION_GENERATE] Got shared behavior analysis ({analysis_type})")
        print(f"   • Analysis source: Shared behavior analysis service")
        print(f"   • Eliminates duplicate OpenAI calls")
        
        # Get user data for nutrition generation
        from services.user_data_service import UserDataService
        user_service = UserDataService()
        
        try:
            user_context, _ = await user_service.get_analysis_data(user_id)
            
            # Generate nutrition using existing function
            from shared_libs.utils.system_prompts import get_system_prompt
            from services.agents.memory.enhanced_memory_prompts import EnhancedMemoryPromptsService
            
            enhanced_prompts_service = EnhancedMemoryPromptsService()
            base_nutrition_prompt = get_system_prompt("plan_generation")
            enhanced_nutrition_prompt = await enhanced_prompts_service.enhance_agent_prompt(
                base_nutrition_prompt, user_id, "nutrition_planning"
            )
            
            # Use the memory-enhanced nutrition generation function with all /api/analyze features
            nutrition_plan = await run_memory_enhanced_nutrition_generation(
                user_id=user_id,
                archetype=archetype,
                behavior_analysis=behavior_analysis
            )
            
            return NutritionPlanResponse(
                status="success",
                user_id=user_id,
                nutrition_plan=nutrition_plan,
                generation_metadata={
                    "analysis_decision": "shared_behavior_analysis_service",
                    "analysis_type": analysis_type,
                    "data_quality": "memory_enhanced",
                    "shared_analysis": True,
                    "duplicate_calls_eliminated": True,
                    "personalization_level": "high",
                    "archetype_used": archetype,
                    "preferences_applied": bool(request.preferences),
                    "generation_time": datetime.now().isoformat()
                },
                cached=(analysis_type == "cached")
            )
            
        except Exception as context_error:
            print(f"⚠️ [NUTRITION_GENERATE] User context error: {context_error}")
            raise HTTPException(status_code=500, detail=f"Failed to get user data for nutrition generation: {str(context_error)}")
>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
            
    except Exception as e:
        print(f"❌ [NUTRITION_GENERATE_ERROR] Failed to generate nutrition for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate nutrition plan: {str(e)}")

@app.get("/api/user/{user_id}/insights/latest")
async def get_latest_insights(user_id: str):
    """Get latest AI insights for user - Phase 4.2 Sprint 3"""
    try:
        print(f"🔍 [INSIGHTS_API] Getting latest insights for user {user_id[:8]}...")
        
        # Get latest analysis with insights from memory
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        memory_service = HolisticMemoryService()
        
        try:
            # Get most recent analysis that includes insights
            analysis_history = await memory_service.get_analysis_history(user_id, limit=3)
            
            insights = None
            analysis_date = None
            
            for analysis in analysis_history:
                analysis_result = analysis.analysis_result
                if isinstance(analysis_result, dict) and 'ai_insights' in analysis_result:
                    insights = analysis_result['ai_insights']
                    analysis_date = analysis.created_at.isoformat()
                    break
            
            if not insights:
                return {
                    "status": "not_found",
                    "user_id": user_id,
                    "insights": {},
                    "message": "No recent insights found. Please run a behavior analysis first.",
                    "suggestion": "Use POST /api/analyze to generate analysis with insights"
                }
            
            return {
                "status": "success",
                "user_id": user_id,
                "insights": insights,
                "analysis_date": analysis_date,
                "cached": True
            }
            
        finally:
            await memory_service.cleanup()
            
    except Exception as e:
        print(f"❌ [INSIGHTS_API_ERROR] Failed to get insights for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve insights: {str(e)}")

@app.post("/api/user/{user_id}/insights/generate")
async def generate_fresh_insights(user_id: str, request: dict):
    """Generate fresh insights on-demand - Phase 4.2 Sprint 3"""
    try:
        print(f"✨ [INSIGHTS_GENERATE] Generating fresh insights for user {user_id[:8]}...")
        
        # Get latest behavior analysis as context
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        from services.agents.insights.main import HolisticInsightsAgent
        from shared_libs.event_system.base_agent import AgentEvent
        
        memory_service = HolisticMemoryService()
        
        try:
            # Get most recent analysis for context
            analysis_history = await memory_service.get_analysis_history(user_id, limit=1)
            
            if not analysis_history:
                return {
                    "status": "error",
                    "user_id": user_id,
                    "insights": {},
                    "message": "No behavior analysis found. Please run analysis first.",
                    "suggestion": "Use POST /api/analyze to generate initial analysis"
                }
            
            recent_analysis = analysis_history[0].analysis_result
            archetype = analysis_history[0].archetype_used or "Foundation Builder"
            
            # Generate fresh insights
            insights_agent = HolisticInsightsAgent()
            
            insights_result = await insights_agent.process(AgentEvent(
                event_id=f"ondemand_insights_{datetime.now().timestamp()}",
                event_type="generate_insights",
                source_agent="insights_api",
                payload={
                    "insight_type": request.get("insight_type", "comprehensive"),
                    "time_horizon": request.get("time_horizon", "medium_term"),
                    "focus_areas": request.get("focus_areas", ["behavioral_patterns", "nutrition_adherence", "routine_consistency"]),
                    "trigger_context": recent_analysis
                },
                timestamp=datetime.now(),
                user_id=user_id,
                archetype=archetype
            ))
            
            if insights_result.success:
                insights = insights_result.result
                return {
                    "status": "success",
                    "user_id": user_id,
                    "insights": insights,
                    "generation_metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "insight_type": request.get("insight_type", "comprehensive"),
                        "time_horizon": request.get("time_horizon", "medium_term"),
                        "focus_areas": request.get("focus_areas", ["behavioral_patterns", "nutrition_adherence", "routine_consistency"]),
                        "archetype_used": archetype,
                        "memory_enhanced": True
                    },
                    "cached": False
                }
            else:
                return {
                    "status": "error",
                    "user_id": user_id,
                    "insights": {},
                    "error": insights_result.error_message
                }
                
        finally:
            await memory_service.cleanup()
            
    except Exception as e:
        print(f"❌ [INSIGHTS_GENERATE_ERROR] Failed to generate insights for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@app.post("/api/user/{user_id}/insights/{insight_id}/feedback")
async def provide_insight_feedback(user_id: str, insight_id: str, feedback: dict):
    """Allow users to provide feedback on insights quality - Phase 4.2 Sprint 3"""
    try:
        print(f"📝 [INSIGHTS_FEEDBACK] Recording feedback for insight {insight_id} from user {user_id[:8]}...")
        
        # Store feedback in memory system for future improvement
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        memory_service = HolisticMemoryService()
        
        try:
            # Store feedback in working memory for processing
            feedback_data = {
                "insight_id": insight_id,
                "user_feedback": feedback,
                "timestamp": datetime.now().isoformat(),
                "feedback_type": "insights_quality"
            }
            
            await memory_service.store_working_memory(
                user_id=user_id,
                session_id="insights_feedback",
                agent_id="insights_agent",
                memory_type="active_insights",  # Changed from 'insight_feedback' to valid type
                content=feedback_data,
                expires_hours=720  # Keep feedback for 30 days
            )
            
            return {
                "status": "success",
                "user_id": user_id,
                "insight_id": insight_id,
                "message": "Feedback recorded successfully",
                "feedback_stored": True
            }
            
        finally:
            await memory_service.cleanup()
            
    except Exception as e:
        print(f"❌ [INSIGHTS_FEEDBACK_ERROR] Failed to record feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")

<<<<<<< HEAD
=======
@app.post("/api/user/{user_id}/behavior/analyze", response_model=BehaviorAnalysisResponse)
async def analyze_behavior(user_id: str, request: BehaviorAnalysisRequest):
    """
    Standalone behavior analysis endpoint with 50-item threshold constraint
    Only runs fresh analysis when 50+ new data points exist, otherwise returns cached analysis
    """
    try:
        print(f"🧠 [BEHAVIOR_ANALYZE] Starting behavior analysis for user {user_id[:8]}...")
        
        # Import required services
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        
        # Initialize services
        ondemand_service = await get_ondemand_service()
        memory_service = HolisticMemoryService()
        
        # Check if fresh analysis is needed (50-item threshold)
        decision, metadata = await ondemand_service.should_run_analysis(user_id, request.force_refresh)
        
        # Safe enum access for logging
        decision_str = decision.value if hasattr(decision, 'value') else str(decision)
        memory_quality = metadata.get('memory_quality')
        memory_quality_str = memory_quality.value if hasattr(memory_quality, 'value') else str(memory_quality) if memory_quality else 'unknown'
        
        print(f"📊 [BEHAVIOR_ANALYZE] Analysis decision: {decision_str}")
        print(f"   • New data points: {metadata['new_data_points']}")
        print(f"   • Threshold: {metadata['threshold_used']}")
        print(f"   • Memory quality: {memory_quality_str}")
        print(f"   • Reason: {metadata['reason']}")
        
        behavior_analysis = None
        analysis_type = "unknown"
        
        if decision == AnalysisDecision.FRESH_ANALYSIS or decision == AnalysisDecision.STALE_FORCE_REFRESH:
            # Run fresh behavior analysis using existing logic from /api/analyze
            print(f"🚀 [BEHAVIOR_ANALYZE] Running fresh behavior analysis...")
            
            # Get archetype from request or use default
            archetype = request.archetype or "Foundation Builder"
            
            # Use the behavior analysis function that returns correct status format
            behavior_analysis = await run_behavior_analysis(user_id, archetype)
            
            if behavior_analysis and behavior_analysis.get("status") == "success":
                analysis_type = "fresh"
                
                # Store the analysis in memory system for future use
                await memory_service.store_analysis_result(
                    user_id=user_id,
                    analysis_type="behavior_analysis",
                    analysis_result=behavior_analysis,
                    archetype_used=archetype
                )
                print(f"✅ [BEHAVIOR_ANALYZE] Fresh analysis completed and stored")
            else:
                # Fallback to cached if fresh analysis fails
                print(f"⚠️ [BEHAVIOR_ANALYZE] Fresh analysis failed, attempting cached...")
                behavior_analysis = await ondemand_service.get_cached_behavior_analysis(user_id)
                analysis_type = "cached_fallback"
                
        else:
            # Use cached analysis
            print(f"💾 [BEHAVIOR_ANALYZE] Using cached analysis (below threshold)")
            behavior_analysis = await ondemand_service.get_cached_behavior_analysis(user_id)
            analysis_type = "cached"
        
        # Validate we have behavior analysis
        if not behavior_analysis:
            return BehaviorAnalysisResponse(
                status="error",
                user_id=user_id,
                analysis_type="none",
                behavior_analysis={},
                metadata={
                    "error": "No behavior analysis available and unable to generate new analysis",
                    "suggestion": "Try with force_refresh=true or ensure user has sufficient health data",
                    "decision_metadata": metadata
                }
            )
        
        # Calculate next eligible analysis time
        next_eligible = None
        if analysis_type == "cached" and metadata.get('new_data_points', 0) < 50:
            needed_points = 50 - metadata.get('new_data_points', 0)
            next_eligible = f"Need {needed_points} more data points to trigger fresh analysis"
        
        return BehaviorAnalysisResponse(
            status="success",
            user_id=user_id,
            analysis_type=analysis_type,
            behavior_analysis=behavior_analysis,
            metadata={
                "new_data_points": metadata.get('new_data_points', 0),
                "threshold": metadata.get('threshold_used', 50),
                "cache_age_hours": metadata.get('cache_age_hours', 0),
                "memory_quality": metadata.get('memory_quality').value if hasattr(metadata.get('memory_quality'), 'value') else str(metadata.get('memory_quality', 'unknown')),
                "decision_reason": metadata.get('reason', ''),
                "force_refresh_used": request.force_refresh,
                "next_analysis_info": next_eligible,
                "archetype_used": request.archetype or "Foundation Builder"
            }
        )
        
    except Exception as e:
        print(f"❌ [BEHAVIOR_ANALYZE_ERROR] Failed to analyze behavior for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze behavior: {str(e)}")

>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get current status of the on-demand analysis system (replaces background scheduler)"""
    try:
        from services.ondemand_analysis_service import get_ondemand_service
        
        # Get on-demand service status
        ondemand_service = await get_ondemand_service()
        
        return {
<<<<<<< HEAD
            "status": "on_demand_analysis",
            "message": "Background scheduler replaced with intelligent on-demand analysis",
            "system": "Phase 4.2 - Smart Analysis Triggering",
            "active_users": 1,  # Can be updated to get actual count
            "data_threshold": "Dynamic (memory-aware)",
            "analysis_mode": "triggered_on_routine_nutrition_requests",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
=======
            "status": "independent_endpoints",
            "message": "Restructured API with independent behavior analysis endpoint and 50-item threshold",
            "system": "Phase 4.2 - Independent Endpoint Architecture",
            "active_users": 1,  # Can be updated to get actual count
            "data_threshold": 50,  # Fixed 50-item threshold for behavior analysis
            "analysis_mode": "constraint_based_triggering",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
                "behavior_analyze": "POST /api/user/{user_id}/behavior/analyze",
>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
                "routine_latest": "GET /api/user/{user_id}/routine/latest",
                "routine_generate": "POST /api/user/{user_id}/routine/generate", 
                "nutrition_latest": "GET /api/user/{user_id}/nutrition/latest",
                "nutrition_generate": "POST /api/user/{user_id}/nutrition/generate"
            },
<<<<<<< HEAD
            "features": {
                "smart_thresholds": "Rich memory = lower threshold, sparse memory = higher threshold",
                "three_tier_response": "fresh_analysis | memory_enhanced_cache | stale_force_refresh",
                "memory_integration": "4-layer memory system (working, short-term, long-term, meta)",
                "fallback_logic": "Graceful degradation on analysis failures"
=======
            "architecture": {
                "behavior_endpoint": "Standalone endpoint with 50-item threshold constraint",
                "plan_endpoints": "Call behavior analysis endpoint internally when needed",
                "constraint_logic": "Only run behavior analysis if 50+ new data points since last analysis",
                "reusability": "Routine and nutrition endpoints share behavior analysis results"
            },
            "features": {
                "threshold_constraint": "50 new data points required for fresh behavior analysis",
                "caching_strategy": "Use cached analysis until threshold is met",
                "force_refresh": "Optional override of 50-item threshold",
                "memory_integration": "4-layer memory system (working, short-term, long-term, meta)",
                "endpoint_coordination": "Routine/nutrition can trigger behavior analysis when needed"
>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
            }
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# PHASE 2 - COMPLETE MULTI-AGENT WORKFLOWS
# ============================================================================

@app.post("/api/complete-analysis", response_model=CompleteAnalysisResponse)
async def start_complete_analysis(request: CompleteAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start complete multi-agent analysis workflow
    Orchestrates: Behavior → Memory → Plans → Insights → Adaptation
    """
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        print(f"🚀 Starting complete multi-agent workflow for {request.user_id}")
        
        # Import required classes
        from shared_libs.event_system.base_agent import AgentEvent
        
        # Create workflow start event
        workflow_event = AgentEvent(
            event_id=f"api_workflow_{datetime.now().timestamp()}",
            event_type="start_complete_workflow",
            source_agent="api_gateway",
            payload={
                "analysis_number": request.analysis_number,
                "preferences": request.preferences or {}
            },
            timestamp=datetime.now(),
            user_id=request.user_id,
            archetype=request.archetype
        )
        
        # Start workflow via orchestrator
        response = await orchestrator.process(workflow_event)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=f"Failed to start workflow: {response.error_message}")
        
        workflow_id = response.result.get("workflow_id")
        current_stage = response.result.get("current_stage", "started")
        
        print(f"✅ Complete workflow started: {workflow_id}")
        
        return CompleteAnalysisResponse(
            status="workflow_started",
            workflow_id=workflow_id,
            user_id=request.user_id,
            archetype=request.archetype,
            message=f"Complete multi-agent analysis started for {request.archetype} user",
            current_stage=current_stage,
            estimated_completion_minutes=5
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error starting complete analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/api/workflow-status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """Get status of a running workflow"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        # Import required classes
        from shared_libs.event_system.base_agent import AgentEvent
        
        # Create status request event
        status_event = AgentEvent(
            event_id=f"api_status_{datetime.now().timestamp()}",
            event_type="workflow_status_request",
            source_agent="api_gateway",
            payload={"workflow_id": workflow_id},
            timestamp=datetime.now(),
            user_id="api_request"  # Generic user for status requests
        )
        
        # Get status from orchestrator
        response = await orchestrator.process(status_event)
        
        if not response.success:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
        
        result = response.result
        completed_stages = result.get("completed_stages", [])
        
        # Calculate progress percentage
        total_stages = 6  # behavior, memory, plans, insights, adaptation, complete
        progress = min(100, int((len(completed_stages) / total_stages) * 100))
        
        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            user_id=result.get("user_id"),
            current_stage=result.get("current_stage"),
            completed_stages=completed_stages,
            progress_percentage=progress,
            start_time=result.get("start_time"),
            results_available=result.get("results_available", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/api/insights/generate", response_model=InsightsResponse)
async def generate_insights(request: InsightsRequest):
    """Generate AI-powered insights for a user"""
    try:
        if not insights_agent:
            raise HTTPException(status_code=503, detail="Insights agent not initialized")
        
        print(f"💡 Generating insights for {request.user_id}")
        
        # Import required classes
        from shared_libs.event_system.base_agent import AgentEvent
        
        # Create insights generation event
        insights_event = AgentEvent(
            event_id=f"api_insights_{datetime.now().timestamp()}",
            event_type="generate_insights",
            source_agent="api_gateway",
            payload={
                "insight_type": request.insight_type,
                "time_horizon": request.time_horizon,
                "focus_areas": request.focus_areas or ["behavioral_patterns", "goal_progression"]
            },
            timestamp=datetime.now(),
            user_id=request.user_id,
            archetype=request.archetype
        )
        
        # Generate insights
        response = await insights_agent.process(insights_event)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=f"Failed to generate insights: {response.error_message}")
        
        result = response.result
        
        return InsightsResponse(
            status="success",
            user_id=request.user_id,
            insights=result.get("insights", []),
            confidence_score=result.get("confidence_score", 0.7),
            recommendations=result.get("recommendations", []),
            patterns_identified=result.get("patterns_identified", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/api/adaptation/trigger", response_model=AdaptationResponse)
async def trigger_adaptation(request: AdaptationRequest):
    """Trigger strategy adaptation based on user feedback or performance"""
    try:
        if not adaptation_agent:
            raise HTTPException(status_code=503, detail="Adaptation agent not initialized")
        
        print(f"⚡ Triggering adaptation for {request.user_id}")
        
        # Import required classes
        from shared_libs.event_system.base_agent import AgentEvent
        
        # Create adaptation event
        adaptation_event = AgentEvent(
            event_id=f"api_adaptation_{datetime.now().timestamp()}",
            event_type="adapt_strategy",
            source_agent="api_gateway",
            payload={
                "trigger": request.trigger,
                "context": request.context,
                "urgency": request.urgency,
                "user_feedback": request.user_feedback,
                "affected_areas": request.context.get("affected_areas", ["behavior"])
            },
            timestamp=datetime.now(),
            user_id=request.user_id,
            archetype=request.archetype
        )
        
        # Trigger adaptation
        response = await adaptation_agent.process(adaptation_event)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=f"Failed to trigger adaptation: {response.error_message}")
        
        result = response.result
        
        return AdaptationResponse(
            status="success",
            user_id=request.user_id,
            adaptations_made=result.get("adaptations_made", []),
            confidence=result.get("confidence", 0.7),
            expected_impact=result.get("expected_impact", "positive"),
            monitoring_plan=result.get("monitoring_plan", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error triggering adaptation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/api/memory/{user_id}", response_model=MemoryResponse)
async def get_user_memory(user_id: str, memory_type: str = "all", category: Optional[str] = None):
    """Retrieve user memory data"""
    try:
        if not memory_agent:
            raise HTTPException(status_code=503, detail="Memory agent not initialized")
        
        print(f"🧠 Retrieving memory for {user_id}")
        
        # Import required classes
        from shared_libs.event_system.base_agent import AgentEvent
        
        # Create memory retrieval event
        memory_event = AgentEvent(
            event_id=f"api_memory_{datetime.now().timestamp()}",
            event_type="memory_retrieve",
            source_agent="api_gateway",
            payload={
                "memory_type": memory_type,
                "category": category,
                "query_context": "api_request"
            },
            timestamp=datetime.now(),
            user_id=user_id
        )
        
        # Retrieve memory
        response = await memory_agent.process(memory_event)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve memory: {response.error_message}")
        
        result = response.result
        
        return MemoryResponse(
            status="success",
            user_id=user_id,
            memory_data=result.get("memory_data", {}),
            insights=result.get("insights", []),
            retrieved_at=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving memory: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# ============================================================================
# PHASE 1 - LEGACY ENDPOINTS (PRESERVED)
# ============================================================================

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_user(request: AnalysisRequest):
    """
    User analysis endpoint - PHASE 3.1 REAL DATA INTEGRATION
    Now uses real user data from Supabase via UserDataService
    """
    try:
        user_id = request.user_id
        archetype = request.archetype
        
        print(f"🔍 Starting REAL DATA analysis for user: {user_id}, archetype: {archetype}")
        
        # PHASE 3.1: Import real data services
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt, get_archetype_adaptation
        
        # PHASE 4.1: Import memory integration services
        from services.memory_integration_service import MemoryIntegrationService
        # PHASE 4.2: Import enhanced memory prompts service
        from services.agents.memory.enhanced_memory_prompts import EnhancedMemoryPromptsService
        
        # Initialize UserDataService and AnalysisTracker for real data
        user_service = UserDataService()
        from services.simple_analysis_tracker import SimpleAnalysisTracker as AnalysisTracker
        analysis_tracker = AnalysisTracker()
        
        # PHASE 4.1: Initialize Memory Integration Service
        memory_service = MemoryIntegrationService()
        print(f"🧠 Preparing memory-enhanced analysis context for {user_id}...")
        memory_context = await memory_service.prepare_memory_enhanced_context(user_id)
        
        # PHASE 4.2: Initialize Enhanced Memory Prompts Service
        enhanced_prompts_service = EnhancedMemoryPromptsService()
        print(f"✨ Initializing memory-enhanced prompt generation for {user_id}...")
        
        try:
            # SIMPLIFIED INCREMENTAL SYNC: Fetch data since last analysis
            # Use memory context to determine optimal data fetching strategy
            days_to_fetch = memory_context.days_to_fetch
            print(f"📊 Fetching user data with memory-guided incremental sync for {user_id}...")
            print(f"🧠 Analysis mode: {memory_context.analysis_mode}, fetching {days_to_fetch} days of data")
            user_context, latest_data_timestamp = await user_service.get_analysis_data(user_id)
            
            # Extract real data for analysis
            data_quality = user_context.data_quality
            print(f"✅ Real data retrieved:")
            print(f"   • Data Quality: {data_quality.quality_level}")
            print(f"   • Scores: {data_quality.scores_count}")
            print(f"   • Biomarkers: {data_quality.biomarkers_count}")
            print(f"   • Completeness: {data_quality.completeness_score:.2f}")
            
            # Get system prompts and enhance with memory context
            base_behavior_prompt = get_system_prompt("behavior_analysis")
            base_nutrition_prompt = get_system_prompt("plan_generation") 
            base_routine_prompt = get_system_prompt("plan_generation")
            archetype_guidance = get_archetype_adaptation(archetype)
            
            # PHASE 4.2: Enhance prompts with comprehensive memory context using new service
            print("✨ Enhancing prompts with 4-layer memory intelligence...")
            behavior_prompt = await enhanced_prompts_service.enhance_agent_prompt(base_behavior_prompt, user_id, "behavior_analysis")
            nutrition_prompt = await enhanced_prompts_service.enhance_agent_prompt(base_nutrition_prompt, user_id, "nutrition_planning")
            routine_prompt = await enhanced_prompts_service.enhance_agent_prompt(base_routine_prompt, user_id, "routine_planning")
            
            print(f"🧠 Memory-enhanced prompts prepared - Focus areas: {memory_context.personalized_focus_areas}")
            print(f"🧠 Proven strategies available: {len(memory_context.proven_strategies)} strategies")
            
            print(f"✅ System prompts loaded: {len(behavior_prompt):,} chars")
            
            # PHASE 3.2 + 4.1: Create health context summary with AI-friendly language + Memory Context
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

            user_context_summary = f"""
HEALTH ANALYSIS REQUEST - MEMORY-ENHANCED COMPREHENSIVE DATA:
- Profile Reference: {user_id}
- Health Archetype: {archetype}
- Analysis Date: {datetime.now().strftime('%Y-%m-%d')}
- Mode: Memory-Enhanced Health Analysis (Phase 4.1)

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
"""
            
        except Exception as data_error:
            print(f"⚠️  Real data fetch failed for {user_id}: {data_error}")
            print(f"🔄 Falling back to mock data analysis...")
            
            # Fallback to original mock data approach if real data fails
            user_context_summary = f"""
HEALTH ANALYSIS REQUEST - SAMPLE MODE:
- Profile Reference: {user_id}
- Health Archetype: {archetype}
- Analysis Date: {datetime.now().strftime('%Y-%m-%d')}
- Mode: Sample Analysis (Health data unavailable)

ARCHETYPE FRAMEWORK:
{get_archetype_adaptation(archetype)}

Note: Comprehensive health data was unavailable for {user_id}, using sample analysis patterns.
Please provide a detailed analysis that demonstrates the {archetype} approach to health optimization.
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

        # Get analysis number early for logging
        analysis_number = await get_next_analysis_number()
        
        # Step 1: Behavior Analysis (using o3 for deep analysis) - Phase 3.3 Agent-Specific Data
        print("🧠 Running behavior analysis with o3 model...")
        behavior_agent_data = await prepare_behavior_agent_data(user_context if 'user_context' in locals() else None, user_context_summary)
        behavior_analysis = await run_behavior_analysis_o3(behavior_prompt, user_context_summary)
        await log_agent_handoff("behavior_analysis", behavior_agent_data, behavior_analysis, analysis_number)
        print(f"✅ Behavior analysis complete with comprehensive pattern data")
        
        # Step 2: Nutrition Plan (using 4o for plan generation) - Phase 3.3 Agent-Specific Data  
        print("🥗 Generating nutrition plan with gpt-4o...")
        nutrition_agent_data = await prepare_nutrition_agent_data(user_context if 'user_context' in locals() else None, behavior_analysis)
        nutrition_plan = await run_nutrition_planning_4o(nutrition_prompt, user_context_summary, behavior_analysis, archetype)
        await log_agent_handoff("nutrition_plan", nutrition_agent_data, nutrition_plan, analysis_number)
        print(f"✅ Nutrition plan complete with nutrition-specific data filtering")
        
        # Step 3: Routine Plan (using 4o for plan generation) - Phase 3.3 Agent-Specific Data
        print("🏃‍♂️ Generating routine plan with gpt-4o...")
        routine_agent_data = await prepare_routine_agent_data(user_context if 'user_context' in locals() else None, behavior_analysis)
        routine_plan = await run_routine_planning_4o(routine_prompt, user_context_summary, behavior_analysis, archetype)
        await log_agent_handoff("routine_plan", routine_agent_data, routine_plan, analysis_number)
        print(f"✅ Routine plan complete with routine-specific data filtering")
        
        # Log analysis data - PHASE 3.3 UPDATE
        # Determine if we used real data or fallback
        analysis_mode = "Agent-Specific Data Filtering - Phase 3.3" if "Comprehensive Health Analysis" in user_context_summary else "Sample Mode"
        
        # Enhanced input logging with raw data
        input_log_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "archetype": archetype,
            "mode": analysis_mode,
            "analysis_number": analysis_number,
            "phase": "3.3 - Agent-Specific Data Filtering",
            "models_used": {
                "behavior_analysis": "o3",
                "nutrition_plan": "gpt-4o",
                "routine_plan": "gpt-4o"
            },
            "raw_health_data": {
                "data_quality": {
<<<<<<< HEAD
                    "level": data_quality.quality_level.value if 'data_quality' in locals() else "unknown",
=======
                    "level": (data_quality.quality_level.value if hasattr(data_quality, 'quality_level') and hasattr(data_quality.quality_level, 'value') else str(data_quality)) if 'data_quality' in locals() else "unknown",
>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
                    "scores_count": data_quality.scores_count if 'data_quality' in locals() else 0,
                    "biomarkers_count": data_quality.biomarkers_count if 'data_quality' in locals() else 0,
                    "completeness_score": data_quality.completeness_score if 'data_quality' in locals() else 0,
                    "has_recent_data": data_quality.has_recent_data if 'data_quality' in locals() else False
                } if 'data_quality' in locals() else {},
                "date_range": {
                    "start": user_context.date_range.start_date.isoformat() if 'user_context' in locals() else None,
                    "end": user_context.date_range.end_date.isoformat() if 'user_context' in locals() else None,
                    "days": user_context.date_range.days if 'user_context' in locals() else 0
                } if 'user_context' in locals() else {},
                "sql_queries_used": {
                    "scores_query": """
                        SELECT id, profile_id, type, score, data, 
                               score_date_time, created_at, updated_at
                        FROM scores 
                        WHERE profile_id = $1
                        LIMIT $2
                    """,
                    "biomarkers_query": """
                        SELECT id, profile_id, category, type, data,
                               start_date_time, end_date_time, created_at, updated_at
                        FROM biomarkers 
                        WHERE profile_id = $1
                        LIMIT $2
                    """,
                    "archetypes_query": """
                        SELECT id, profile_id, name, periodicity, value, data,
                               start_date_time, end_date_time, created_at, updated_at
                        FROM archetypes 
                        WHERE profile_id = $1
                    """,
                    "query_parameters": {
                        "profile_id": user_id,
                        "max_records": 1000,
                        "date_filter": "No date filtering in current queries (gets all records)"
                    }
                },
                "complete_behavior_analysis_input": behavior_agent_data if 'behavior_agent_data' in locals() else {},
                "all_scores_fetched": [
                    {
                        "id": score.id,
                        "type": score.type,
                        "score": score.score,
                        "data": score.data,
                        "score_date_time": score.score_date_time.isoformat() if hasattr(score.score_date_time, 'isoformat') else str(score.score_date_time),
                        "created_at": score.created_at.isoformat() if hasattr(score, 'created_at') else None
                    } for score in (user_context.scores if 'user_context' in locals() else [])
                ] if 'user_context' in locals() else [],
                "all_biomarkers_fetched": [
                    {
                        "id": bio.id,
                        "type": bio.type,
                        "category": bio.category,
                        "data": bio.data,
                        "start_date_time": bio.start_date_time.isoformat() if hasattr(bio, 'start_date_time') else None,
                        "end_date_time": bio.end_date_time.isoformat() if hasattr(bio, 'end_date_time') and bio.end_date_time else None
                    } for bio in (user_context.biomarkers if 'user_context' in locals() else [])
                ] if 'user_context' in locals() else [],
                "behavior_analysis_filtered_data": {
                    "activity_sleep_readiness_scores": [
                        {
                            "date": get_score_actual_date(score) if hasattr(score, 'created_at') else "unknown",
                            "type": score.type,
                            "score": score.score,
                            "state": score.data.get("state", "unknown") if score.data else "unknown"
                        }
                        for score in (user_context.scores if 'user_context' in locals() else []) 
                        if score.type in ["activity", "sleep", "readiness"]
                    ][:15] if 'user_context' in locals() else [],
                    "first_20_biomarkers_all_types": [
                        {
                            "type": bio.type,
                            "category": bio.category,
                            "date": bio.start_date_time.strftime("%Y-%m-%d") if hasattr(bio, 'start_date_time') else "unknown"
                        }
                        for bio in (user_context.biomarkers[:20] if 'user_context' in locals() else [])
                    ] if 'user_context' in locals() else []
                }
            }
        }
        
        await log_analysis_data(input_log_data, {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "archetype": archetype,
            "behavior_analysis": behavior_analysis,
            "nutrition_plan": nutrition_plan,
            "routine_plan": routine_plan,
            "analysis_number": analysis_number,
            "mode": analysis_mode,
            "phase": "3.3 - Agent-Specific Data Filtering",
            "models_used": {
                "behavior_analysis": "o3",
                "nutrition_plan": "gpt-4o", 
                "routine_plan": "gpt-4o"
            }
        }, analysis_number)
        
        print(f"✅ Complete multi-model analysis finished for {user_id}")
        
        # PHASE 4.1: Store analysis results in memory and update user memory profile
        print(f"🧠 Updating user memory with analysis insights...")
        
        # Store individual analysis insights
        await memory_service.store_analysis_insights(user_id, "behavior_analysis", behavior_analysis, archetype)
        await memory_service.store_analysis_insights(user_id, "nutrition_plan", nutrition_plan, archetype)
        await memory_service.store_analysis_insights(user_id, "routine_plan", routine_plan, archetype)
        
        # Update consolidated memory profile
        await memory_service.update_user_memory_profile(user_id, behavior_analysis, nutrition_plan, routine_plan)
        
        print(f"✅ Memory profile updated with new insights")
        
        # Update last analysis timestamp AFTER successful analysis - use latest data timestamp
        await analysis_tracker.update_analysis_time(user_id, latest_data_timestamp)
        print(f"✅ Updated analysis timestamp for {user_id} to {latest_data_timestamp.isoformat()}")
        
        return AnalysisResponse(
            status="success",
            user_id=user_id,
            archetype=archetype,
            message="Analysis completed successfully using comprehensive health data with memory-enhanced multi-model approach - Phase 4.1",
            analysis={
                "behavior_analysis": behavior_analysis,
                "nutrition_plan": nutrition_plan,
                "routine_plan": routine_plan,
                "system_info": {
                    "mode": analysis_mode,
                    "prompt_system": "HolisticOS",
                    "archetype_applied": archetype,
                    "phase": "4.2 - Memory-Enhanced Intelligence with Insights",
                    "data_source": "Supabase via UserDataService",
                    "models_used": {
                        "behavior_analysis": "o3 (deep analysis)",
                        "nutrition_plan": "gpt-4o (plan generation)",
                        "routine_plan": "gpt-4o (plan generation)",
                        "ai_insights": "gpt-4o (insights generation)"
                    }
                }
            }
        )
        
    except Exception as e:
        print(f"❌ Analysis failed for {request.user_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return AnalysisResponse(
            status="error",
            user_id=request.user_id,
            archetype=request.archetype,
            message=f"Analysis failed: {str(e)}"
        )

async def run_complete_health_analysis(user_id: str, archetype: str) -> dict:
    """
    Complete health analysis with automatic insights generation - Phase 4.2 Sprint 3
    Used by scheduler and on-demand analysis requests
    Integrates insights agent into the main analysis pipeline
    """
    try:
        print(f"🚀 Starting complete health analysis with insights for {user_id}...")
        
        # Run the main analysis using existing analyze_user function
        request = AnalysisRequest(user_id=user_id, archetype=archetype)
        analysis_response = await analyze_user(request)
        
        if analysis_response.status != "success":
            print(f"❌ Main analysis failed: {analysis_response.message}")
            return {
                "status": "error",
                "user_id": user_id,
                "error": analysis_response.message
            }
        
        # Extract analysis results
        analysis_data = analysis_response.analysis
        behavior_analysis = analysis_data.get("behavior_analysis", {})
        nutrition_plan = analysis_data.get("nutrition_plan", {})
        routine_plan = analysis_data.get("routine_plan", {})
        
        print(f"✅ Main analysis complete, generating AI insights...")
        
        # Step 4: Generate AI-Powered Insights using enhanced Insights Agent
        insights = {}
        try:
            from services.agents.insights.main import HolisticInsightsAgent
            from shared_libs.event_system.base_agent import AgentEvent
            
            insights_agent = HolisticInsightsAgent()
            
            insights_result = await insights_agent.process(AgentEvent(
                event_id=f"insights_{datetime.now().timestamp()}",
                event_type="generate_insights",
                source_agent="complete_analysis_pipeline",
                payload={
                    "insight_type": "post_analysis_comprehensive",
                    "time_horizon": "medium_term",
                    "focus_areas": ["behavioral_patterns", "nutrition_adherence", "routine_consistency"],
                    "trigger_context": {
                        "behavior_analysis": behavior_analysis,
                        "nutrition_plan": nutrition_plan, 
                        "routine_plan": routine_plan
                    }
                },
                timestamp=datetime.now(),
                user_id=user_id,
                archetype=archetype
            ))
            
            if insights_result.success:
                insights = insights_result.result
                print(f"✅ Generated {len(insights.get('insights', []))} AI insights")
            else:
                print(f"⚠️ Insights generation failed: {insights_result.error_message}")
                insights = {"error": insights_result.error_message}
                
        except Exception as insights_error:
            print(f"⚠️ Insights generation error: {insights_error}")
            insights = {"error": str(insights_error)}
        
        # Return enhanced results with insights
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "archetype": archetype,
            "behavior_analysis": behavior_analysis,
            "nutrition_plan": nutrition_plan,
            "routine_plan": routine_plan,
            "ai_insights": insights,  # NEW: AI insights included
            "system_info": analysis_data.get("system_info", {}),
            "models_used": {
                "behavior_analysis": "o3",
                "nutrition_plan": "gpt-4o", 
                "routine_plan": "gpt-4o",
                "ai_insights": "gpt-4"  # NEW: Insights model info
            }
        }
        
    except Exception as e:
        print(f"❌ Complete health analysis failed for {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "user_id": user_id,
            "archetype": archetype,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def prepare_behavior_agent_data(user_context, user_context_summary: str) -> dict:
    """Prepare comprehensive data for behavior analysis agent (o3) - Phase 3.3"""
    try:
        # Behavior agent gets the most comprehensive data for pattern analysis
        behavior_data = {
            "comprehensive_health_context": user_context_summary,
            "detailed_metrics": {
                "data_quality": {
<<<<<<< HEAD
                    "level": user_context.data_quality.quality_level.value,
=======
                    "level": (user_context.data_quality.quality_level.value if hasattr(user_context.data_quality, 'quality_level') and hasattr(user_context.data_quality.quality_level, 'value') else str(user_context.data_quality)),
>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
                    "completeness": user_context.data_quality.completeness_score,
                    "scores_count": user_context.data_quality.scores_count,
                    "biomarkers_count": user_context.data_quality.biomarkers_count,
                    "recent_data_available": user_context.data_quality.has_recent_data
                },
                "time_coverage": {
                    "start_date": user_context.date_range.start_date.isoformat(),
                    "end_date": user_context.date_range.end_date.isoformat(),
                    "total_days": user_context.date_range.days
                },
                "activity_patterns": [
                    {
                        "date": get_score_actual_date(score),
                        "type": score.type,
                        "score": score.score,
                        "state": score.data.get("state", "unknown") if score.data else "unknown"
                    }
                    for score in user_context.scores if score.type in ["activity", "sleep", "readiness"]
                ][:15],  # Last 15 key scores for pattern analysis
                "biomarker_categories": {}
            },
            "analysis_focus": "comprehensive_behavior_pattern_analysis"
        }
        
        # Group biomarkers by category for behavior insights
        for bio in user_context.biomarkers[:20]:
            category = bio.category
            if category not in behavior_data["detailed_metrics"]["biomarker_categories"]:
                behavior_data["detailed_metrics"]["biomarker_categories"][category] = []
            behavior_data["detailed_metrics"]["biomarker_categories"][category].append({
                "type": bio.type,
                "date": bio.start_date_time.strftime("%Y-%m-%d")
            })
        
        return behavior_data
        
    except Exception as e:
        return {"error": f"Error preparing behavior data: {str(e)}"}

async def prepare_nutrition_agent_data(user_context, behavior_analysis: dict) -> dict:
    """Prepare nutrition-relevant data for nutrition planning agent (gpt-4o) - Phase 3.3"""
    try:
        # Extract nutrition-relevant insights from behavior analysis
        behavioral_insights = {
            "sophistication_level": behavior_analysis.get("sophistication_assessment", {}).get("category", "unknown"),
            "readiness_level": behavior_analysis.get("readiness_level", "unknown"),
            "primary_goal": behavior_analysis.get("primary_goal", {}),
            "motivation_drivers": behavior_analysis.get("personalized_strategy", {}).get("motivation_drivers", "unknown")
        }
        
        # Filter health data relevant to nutrition planning
        nutrition_relevant_data = {
            "activity_levels": [
                {
                    "date": get_score_actual_date(score),
                    "activity_score": score.score,
                    "state": score.data.get("state", "unknown") if score.data else "unknown"
                }
                for score in user_context.scores if score.type == "activity"
            ][:7],  # Last 7 days of activity
            
            "sleep_quality": [
                {
                    "date": get_score_actual_date(score),
                    "sleep_score": score.score,
                    "state": score.data.get("state", "unknown") if score.data else "unknown"
                }
                for score in user_context.scores if score.type == "sleep"
            ][:7],  # Last 7 days of sleep
            
            "energy_indicators": [
                {
                    "date": get_score_actual_date(score),
                    "readiness_score": score.score,
                    "state": score.data.get("state", "unknown") if score.data else "unknown"
                }
                for score in user_context.scores if score.type == "readiness"
            ][:7],  # Last 7 days of readiness
            
            "nutrition_biomarkers": [
                {
                    "type": bio.type,
                    "category": bio.category,
                    "date": bio.start_date_time.strftime("%Y-%m-%d")
                }
                for bio in user_context.biomarkers 
                if bio.category in ["metabolic", "nutrition", "energy", "recovery"]
            ][:10]  # Nutrition-relevant biomarkers
        }
        
        return {
            "behavioral_insights": behavioral_insights,
            "nutrition_relevant_metrics": nutrition_relevant_data,
            "planning_focus": "nutrition_plan_based_on_activity_sleep_and_goals"
        }
        
    except Exception as e:
        return {"error": f"Error preparing nutrition data: {str(e)}"}

async def prepare_routine_agent_data(user_context, behavior_analysis: dict) -> dict:
    """Prepare routine-relevant data for routine planning agent (gpt-4o) - Phase 3.3"""
    try:
        # Extract routine-relevant insights from behavior analysis
        behavioral_insights = {
            "habit_integration_strategy": behavior_analysis.get("personalized_strategy", {}).get("habit_integration", "unknown"),
            "barrier_mitigation": behavior_analysis.get("personalized_strategy", {}).get("barrier_mitigation", "unknown"),
            "readiness_level": behavior_analysis.get("readiness_level", "unknown"),
            "key_recommendations": behavior_analysis.get("recommendations", [])[:3]  # Top 3 recommendations
        }
        
        # Filter health data relevant to routine planning
        routine_relevant_data = {
            "sleep_patterns": [
                {
                    "date": get_score_actual_date(score),
                    "sleep_score": score.score,
                    "sleep_state": score.data.get("state", "unknown") if score.data else "unknown",
                    "factors": score.data.get("factors", []) if score.data else []
                }
                for score in user_context.scores if score.type == "sleep"
            ][:7],  # Last 7 days for pattern recognition
            
            "activity_patterns": [
                {
                    "date": get_score_actual_date(score),
                    "activity_score": score.score,
                    "activity_state": score.data.get("state", "unknown") if score.data else "unknown",
                    "factors": score.data.get("factors", []) if score.data else []
                }
                for score in user_context.scores if score.type == "activity"
            ][:7],  # Last 7 days for routine optimization
            
            "recovery_readiness": [
                {
                    "date": get_score_actual_date(score),
                    "readiness_score": score.score,
                    "readiness_state": score.data.get("state", "unknown") if score.data else "unknown"
                }
                for score in user_context.scores if score.type == "readiness"
            ][:7],  # Last 7 days for routine timing
            
            "routine_biomarkers": [
                {
                    "type": bio.type,
                    "category": bio.category,
                    "date": bio.start_date_time.strftime("%Y-%m-%d")
                }
                for bio in user_context.biomarkers 
                if bio.category in ["activity", "sleep", "recovery", "stress"]
            ][:10]  # Routine-relevant biomarkers
        }
        
        return {
            "behavioral_insights": behavioral_insights,
            "routine_relevant_metrics": routine_relevant_data,
            "planning_focus": "daily_routine_optimization_based_on_sleep_activity_patterns"
        }
        
    except Exception as e:
        return {"error": f"Error preparing routine data: {str(e)}"}

async def format_health_data_for_ai(user_context) -> str:
    """Format health tracking data for AI analysis - Phase 3.2 (Legacy function)"""
    try:
        # Get latest scores for summary
        recent_scores = {}
        for score in user_context.scores[:10]:  # Latest 10 scores
            score_type = score.type
            if score_type not in recent_scores:
                recent_scores[score_type] = []
            recent_scores[score_type].append({
                'score': score.score,
                'date': get_score_actual_date(score),
                'state': score.data.get('state', 'unknown') if hasattr(score, 'data') and score.data else 'unknown'
            })
        
        # Get key biomarkers
        key_biomarkers = {}
        for bio in user_context.biomarkers[:20]:  # Latest 20 biomarkers
            bio_type = bio.type
            if bio_type not in key_biomarkers:
                key_biomarkers[bio_type] = []
            key_biomarkers[bio_type].append({
                'category': bio.category,
                'data': bio.data,
                'date': bio.start_date_time.strftime('%Y-%m-%d') if hasattr(bio, 'start_date_time') else 'unknown'
            })
        
        # Format for AI
        data_summary = []
        
        # Health Scores Summary
        if recent_scores:
            data_summary.append("HEALTH SCORE PATTERNS:")
            for score_type, scores in recent_scores.items():
                avg_score = sum(s['score'] for s in scores) / len(scores)
                latest_state = scores[0]['state']
                data_summary.append(f"  • {score_type.title()} Metrics: {avg_score:.2f} (trend: {latest_state}) - {len(scores)} measurements")
        
        # Biomarkers Summary
        if key_biomarkers:
            data_summary.append("\nBIOMARKER MEASUREMENTS:")
            for bio_type, values in list(key_biomarkers.items())[:10]:  # Top 10 biomarker types
                recent_categories = [v['category'] for v in values[:3]]
                category_summary = ", ".join(set(recent_categories)) if recent_categories else "unknown"
                data_sample_count = len(values)
                data_summary.append(f"  • {bio_type.replace('_', ' ').title()}: {category_summary} category ({data_sample_count} measurements)")
        
        # Activity Patterns
        behavior_data = user_context.behavior_data
        if behavior_data and isinstance(behavior_data, dict):
            data_summary.append("\nACTIVITY PATTERNS:")
            if 'activity_scores' in behavior_data:
                activity_count = len(behavior_data['activity_scores'])
                data_summary.append(f"  • Activity sessions: {activity_count} tracked periods")
            
            if 'sleep_scores' in behavior_data:
                sleep_count = len(behavior_data['sleep_scores'])
                data_summary.append(f"  • Sleep cycles: {sleep_count} recorded periods")
        
        return '\n'.join(data_summary) if data_summary else "Health tracking data available for analysis."
        
    except Exception as e:
        return f"Error formatting user data: {str(e)}"

<<<<<<< HEAD
=======
async def run_behavior_analysis(user_id: str, archetype: str) -> dict:
    """
    Extracted behavior analysis logic from /api/analyze for reuse
    Returns behavior analysis in the same format as the main endpoint
    """
    try:
        print(f"🧠 [BEHAVIOR_WRAPPER] Starting behavior analysis for {user_id[:8]}...")
        
        # Get user data using existing services
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        
        # Get user context (reuse existing logic from /api/analyze)
        user_context, data_quality = await user_service.get_analysis_data(user_id)
        # Fix datetime bug - safely handle data_quality attribute access
        if hasattr(data_quality, 'value'):
            quality_str = data_quality.value
        elif hasattr(data_quality, 'quality_level') and hasattr(data_quality.quality_level, 'value'):
            quality_str = data_quality.quality_level.value
        else:
            quality_str = str(data_quality) if data_quality else "unknown"
        
        user_context_summary = f"Comprehensive Health Analysis for {archetype} user with {quality_str} data quality."
        
        # Prepare behavior agent data
        behavior_agent_data = await prepare_behavior_agent_data(user_context, user_context_summary)
        
        # Get behavior system prompt
        behavior_prompt = get_system_prompt("behavior_analysis")
        
        # Get analysis number for logging
        analysis_number = await get_next_analysis_number()
        
        # Run behavior analysis using o3 model (same as /api/analyze)
        print("🧠 Running standalone behavior analysis with o3 model...")
        behavior_result = await run_behavior_analysis_o3(behavior_prompt, user_context_summary)
        
        if behavior_result:
            print(f"✅ [BEHAVIOR_WRAPPER] Behavior analysis completed successfully")
            
            # Log agent handoff for standalone behavior analysis
            await log_agent_handoff("behavior_analysis", behavior_agent_data, behavior_result, analysis_number)
            # Safe data quality access
            data_quality_str = data_quality.value if hasattr(data_quality, 'value') else str(data_quality) if data_quality else "unknown"
            
            return {
                "status": "success",
                "behavior_analysis": behavior_result,
                "archetype_used": archetype,
                "data_quality": data_quality_str,
                "model_used": "o3"
            }
        else:
            print(f"❌ [BEHAVIOR_WRAPPER] Behavior analysis failed - no result")
            return {
                "status": "error",
                "error": "Behavior analysis returned no result",
                "behavior_analysis": {}
            }
            
    except Exception as e:
        print(f"❌ [BEHAVIOR_WRAPPER] Error in behavior analysis: {e}")
        return {
            "status": "error", 
            "error": str(e),
            "behavior_analysis": {}
        }

>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
async def run_behavior_analysis_o3(system_prompt: str, user_context: str) -> dict:
    """Run behavior analysis using o3 model for deep analysis - Phase 3.2"""
    try:
        # Use o3 for complex behavior analysis
        client = openai.AsyncOpenAI()
        
        # Note: o3 model only supports default temperature (1)
        response = await client.chat.completions.create(
            model="o3",
            messages=[
                {
                    "role": "system", 
                    "content": f"{system_prompt}\n\nYou are an expert behavioral analyst. Focus on identifying patterns in health tracking data and provide detailed insights."
                },
                {
                    "role": "user", 
                    "content": f"""
{user_context}

Analyze the health tracking patterns and provide a comprehensive behavioral analysis following the HolisticOS framework.

Provide analysis in this JSON structure:
{{
    "behavioral_signature": {{
        "signature": "Detailed behavior pattern description",
        "confidence": 0.0-1.0
    }},
    "sophistication_assessment": {{
        "score": 0-100,
        "category": "Beginner/Intermediate/Advanced/Expert",
        "justification": "Assessment reasoning"
    }},
    "primary_goal": {{
        "goal": "Identified primary health goal",
        "timeline": "Estimated timeline",
        "success_metrics": "Measurable success indicators"
    }},
    "personalized_strategy": {{
        "motivation_drivers": "Key motivation factors",
        "habit_integration": "Habit formation recommendations",
        "barrier_mitigation": "Obstacle management strategies"
    }},
    "readiness_level": "High/Medium/Low",
    "recommendations": ["List of specific recommendations"],
    "data_insights": "Analysis of the provided health data patterns"
}}

Focus on actionable insights from the provided health metrics.
"""
                }
            ],
            # temperature parameter removed - o3 only supports default value of 1
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON response
        try:
            analysis_data = json.loads(content)
            analysis_data["model_used"] = "o3"
            analysis_data["analysis_type"] = "comprehensive_behavior"
            return analysis_data
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return {
                "behavioral_signature": {
                    "signature": "Health Data Analysis Complete",
                    "confidence": 0.85
                },
                "sophistication_assessment": {
                    "score": 75,
                    "category": "Intermediate",
                    "justification": "Analysis based on comprehensive health data"
                },
                "analysis_content": content,
                "model_used": "o3",
                "analysis_type": "comprehensive_behavior"
            }
            
    except Exception as e:
        print(f"Error in o3 behavior analysis: {e}")
        return {
            "error": str(e),
            "model_used": "o3 - fallback",
            "behavioral_signature": {"signature": "Analysis Error", "confidence": 0.5}
        }

<<<<<<< HEAD
=======
async def run_memory_enhanced_behavior_analysis(user_id: str, archetype: str) -> dict:
    """
    Memory-Enhanced Behavior Analysis - Includes all features from /api/analyze
    Features:
    - Memory context preparation using MemoryIntegrationService
    - Memory-enhanced prompt generation
    - Storing analysis results in memory tables
    - Updating user memory profile
    - Complete logging of analysis data
    """
    try:
        print(f"🧠 [MEMORY_ENHANCED] Starting memory-enhanced behavior analysis for {user_id[:8]}...")
        
        # Import memory integration service
        from services.memory_integration_service import MemoryIntegrationService
        
        # Initialize memory integration service
        memory_service = MemoryIntegrationService()
        
        # Step 1: Prepare memory-enhanced context
        print(f"📋 [MEMORY_ENHANCED] Preparing memory context for user {user_id[:8]}...")
        memory_context = await memory_service.prepare_memory_enhanced_context(user_id)
        
        # Step 2: Get user data for analysis
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        
        # Get user data (service handles days internally based on analysis history)
        user_context, data_quality = await user_service.get_analysis_data(user_id)
        
        # Fix datetime bug - safely handle data_quality attribute access
        if hasattr(data_quality, 'value'):
            data_quality_value = data_quality.value
        else:
            data_quality_value = str(data_quality) if data_quality else "unknown"
        
        print(f"📊 [MEMORY_ENHANCED] Data quality: {data_quality_value}")
        print(f"🗓️ [MEMORY_ENHANCED] Using {memory_context.days_to_fetch} days of data (mode: {memory_context.analysis_mode})")
        
        # Step 3: Get and enhance system prompt with memory
        system_prompt = get_system_prompt("behavior_analysis")
        enhanced_prompt = await memory_service.enhance_agent_prompt(
            system_prompt, memory_context, "behavior_analysis"
        )
        
        print(f"🧠 [MEMORY_ENHANCED] Enhanced prompt with memory context (+{len(enhanced_prompt) - len(system_prompt)} chars)")
        
        # Step 4: Prepare behavior agent data with memory context
        user_context_summary = await format_health_data_for_ai(user_context)
        behavior_data = await prepare_behavior_agent_data(user_context, user_context_summary)
        
        # Step 5: Run behavior analysis with memory-enhanced prompt
        analysis_result = await run_behavior_analysis_o3(enhanced_prompt, user_context_summary)
        
        # Step 6: Store analysis insights using same method as /api/analyze
        print(f"💾 [MEMORY_ENHANCED] Storing analysis insights like /api/analyze...")
        insights_stored = False
        try:
            # Use the same storage method as /api/analyze (line 1523)
            await memory_service.store_analysis_insights(user_id, "behavior_analysis", analysis_result, archetype)
            insights_stored = True
            print(f"✅ [MEMORY_ENHANCED] Analysis insights stored successfully")
        except Exception as e:
            print(f"⚠️ [MEMORY_ENHANCED] Failed to store analysis insights: {e}")
        
        # Step 8: Log complete analysis data (input/output logging)
        await log_complete_standalone_analysis(
            "behavior_analysis", user_id, archetype, 
            behavior_data, analysis_result, memory_context
        )
        
        # Step 9: Cleanup memory service
        await memory_service.cleanup()
        
        # Add memory enhancement metadata to result
        analysis_result.update({
            "memory_enhanced": True,
            "analysis_mode": memory_context.analysis_mode,
            "days_fetched": memory_context.days_to_fetch,
            "memory_focus_areas": memory_context.personalized_focus_areas,
            "insights_stored": insights_stored
        })
        
        print(f"✅ [MEMORY_ENHANCED] Memory-enhanced behavior analysis completed for {user_id[:8]}")
        return analysis_result
        
    except Exception as e:
        print(f"❌ [MEMORY_ENHANCED] Error in memory-enhanced behavior analysis: {e}")
        # Fallback to regular behavior analysis
        print(f"🔄 [MEMORY_ENHANCED] Falling back to regular behavior analysis...")
        return await run_behavior_analysis(user_id, archetype)

async def get_or_create_shared_behavior_analysis(user_id: str, archetype: str, force_refresh: bool = False) -> dict:
    """
    MVP Shared Behavior Analysis - Extracted from /api/analyze (lines 1257-1386)
    Used by routine/nutrition endpoints to avoid duplicate analysis
    Applies 50-item threshold logic from OnDemandAnalysisService
    """
    try:
        print(f"🧠 [SHARED_ANALYSIS] Checking behavior analysis for {user_id[:8]}...")
        
        # Step 1: Check if fresh analysis needed (50-item threshold logic)
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        ondemand_service = await get_ondemand_service()
        decision, metadata = await ondemand_service.should_run_analysis(user_id, force_refresh)
        
        # Debug logging
        decision_str = decision.value if hasattr(decision, 'value') else str(decision)
        print(f"📊 [SHARED_ANALYSIS] Decision: {decision_str}, New points: {metadata.get('new_data_points', 0)}, Threshold: {metadata.get('threshold_used', 50)}")
        
        # Step 2: Use cached if sufficient
        if decision == AnalysisDecision.MEMORY_ENHANCED_CACHE:
            print(f"✅ [SHARED_ANALYSIS] Using cached behavior analysis ({metadata.get('new_data_points', 0)} new points < 50)")
            cached_analysis = await get_cached_behavior_analysis_from_memory(user_id)
            if cached_analysis:
                return cached_analysis
            # If cache retrieval fails, fall through to fresh analysis
        
        # Step 3: Run fresh analysis using EXACT /api/analyze flow (lines 1257-1386)
        print(f"🚀 [SHARED_ANALYSIS] Running fresh behavior analysis ({metadata.get('new_data_points', 0)} new points)")
        return await run_fresh_behavior_analysis_like_api_analyze(user_id, archetype)
        
    except Exception as e:
        print(f"❌ [SHARED_ANALYSIS] Error in shared analysis: {e}")
        # Fallback to basic behavior analysis
        return await run_behavior_analysis(user_id, archetype)


async def get_cached_behavior_analysis_from_memory(user_id: str) -> dict:
    """Retrieve cached behavior analysis from memory system"""
    try:
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        memory_service = HolisticMemoryService()
        
        # Get latest behavior analysis from memory
        analysis_results = await memory_service.get_analysis_history(user_id, limit=1)
        if analysis_results:
            latest = analysis_results[0]
            if latest.analysis_type in ["behavior_analysis"]:
                print(f"📋 [SHARED_ANALYSIS] Found cached behavior analysis from {latest.created_at}")
                # Handle nested analysis result format - extract behavior_analysis if needed
                analysis_result = latest.analysis_result
                if isinstance(analysis_result, dict) and "behavior_analysis" in analysis_result:
                    return analysis_result["behavior_analysis"]
                return analysis_result
        
        await memory_service.cleanup()
        return None
        
    except Exception as e:
        print(f"⚠️ [SHARED_ANALYSIS] Cache retrieval failed: {e}")
        return None


async def run_fresh_behavior_analysis_like_api_analyze(user_id: str, archetype: str) -> dict:
    """
    Run fresh behavior analysis using EXACT same flow as /api/analyze
    Extracted from /api/analyze lines 1257-1386 - minimal changes, maximum reuse
    """
    try:
        # EXACT same imports as /api/analyze (lines 1246-1249)
        from services.memory_integration_service import MemoryIntegrationService
        from services.agents.memory.enhanced_memory_prompts import EnhancedMemoryPromptsService  
        from services.user_data_service import UserDataService
        from services.simple_analysis_tracker import SimpleAnalysisTracker as AnalysisTracker
        from shared_libs.utils.system_prompts import get_system_prompt
        
        # EXACT same service initialization as /api/analyze (lines 1252-1257)
        user_service = UserDataService()
        analysis_tracker = AnalysisTracker()
        memory_service = MemoryIntegrationService()
        enhanced_prompts_service = EnhancedMemoryPromptsService()
        
        try:
            # EXACT same memory context preparation as /api/analyze (lines 1258-1259)
            memory_context = await memory_service.prepare_memory_enhanced_context(user_id)
            
            # EXACT same data fetching as /api/analyze (line 1271)
            user_context, latest_data_timestamp = await user_service.get_analysis_data(user_id)
            
            # EXACT same prompt enhancement as /api/analyze (lines 1282-1289)
            base_behavior_prompt = get_system_prompt("behavior_analysis")
            behavior_prompt = await enhanced_prompts_service.enhance_agent_prompt(base_behavior_prompt, user_id, "behavior_analysis")
            
            # EXACT same context summary creation as /api/analyze (lines 1324-1348)
            user_context_summary = await create_context_summary_like_api_analyze(user_context, memory_context, archetype, user_id)
            
            # EXACT same behavior analysis execution as /api/analyze (lines 1382-1386)  
            analysis_number = await get_next_analysis_number()
            behavior_agent_data = await prepare_behavior_agent_data(user_context, user_context_summary)
            behavior_analysis = await run_behavior_analysis_o3(behavior_prompt, user_context_summary)
            await log_agent_handoff("behavior_analysis", behavior_agent_data, behavior_analysis, analysis_number)
            
            # EXACT same memory storage as /api/analyze (lines 1525-1531)
            await memory_service.store_analysis_insights(user_id, "behavior_analysis", behavior_analysis, archetype)
            await memory_service.update_user_memory_profile(user_id, behavior_analysis, {}, {})
            
            # EXACT same timestamp update as /api/analyze (line 1536)
            await analysis_tracker.update_analysis_time(user_id, latest_data_timestamp)
            
            print(f"✅ [SHARED_ANALYSIS] Fresh behavior analysis completed for {user_id[:8]}")
            return behavior_analysis
            
        finally:
            # EXACT same cleanup as /api/analyze (lines 1369-1376)
            await user_service.cleanup()
            await analysis_tracker.cleanup()  
            await memory_service.cleanup()
            await enhanced_prompts_service.cleanup()
            
    except Exception as e:
        print(f"❌ [SHARED_ANALYSIS] Fresh analysis failed: {e}")
        # Final fallback
        return await run_behavior_analysis(user_id, archetype)


async def create_context_summary_like_api_analyze(user_context, memory_context, archetype: str, user_id: str) -> str:
    """
    Create context summary exactly like /api/analyze does (lines 1324-1348)
    Minimal extraction - same logic, same format
    """
    try:
        data_quality = user_context.data_quality
        
        # EXACT same memory summary logic as /api/analyze (lines 1299-1323)
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

        # EXACT same context summary format as /api/analyze (lines 1324-1348)
        user_context_summary = f"""
HEALTH ANALYSIS REQUEST - MEMORY-ENHANCED COMPREHENSIVE DATA:
- Profile Reference: {user_id}
- Health Archetype: {archetype}
- Analysis Date: {datetime.now().strftime('%Y-%m-%d')}
- Mode: Memory-Enhanced Health Analysis (Phase 4.1)

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

ANALYSIS INSTRUCTIONS: You have comprehensive health tracking data including sleep patterns, activity metrics, and biomarker readings, enhanced with user memory context. Analyze these health indicators to identify patterns, trends, and insights that align with the {archetype} framework. Focus on actionable observations from the provided health metrics while considering the user's memory profile and proven strategies.
"""
        return user_context_summary
        
    except Exception as e:
        print(f"⚠️ [SHARED_ANALYSIS] Context summary creation failed: {e}")
        # Minimal fallback
        return f"Health analysis for {archetype} user {user_id}"

async def log_complete_standalone_analysis(agent_type: str, user_id: str, archetype: str, 
                                         input_data: dict, output_data: dict, memory_context) -> None:
    """Log complete standalone analysis data like /api/analyze does"""
    try:
        analysis_number = await get_next_analysis_number()
        
        # Prepare complete input data
        complete_input = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "standalone_" + agent_type,
            "user_id": user_id,
            "archetype": archetype,
            "memory_enhanced": True,
            "analysis_mode": memory_context.analysis_mode,
            "days_to_fetch": memory_context.days_to_fetch,
            "personalized_focus_areas": memory_context.personalized_focus_areas,
            "agent_input_data": input_data
        }
        
        # Prepare complete output data  
        complete_output = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "standalone_" + agent_type,
            "user_id": user_id,
            "archetype": archetype,
            "memory_enhanced": True,
            "analysis_result": output_data
        }
        
        # Log using existing function
        await log_analysis_data(complete_input, complete_output, analysis_number)
        
        print(f"📝 [MEMORY_ENHANCED] Complete standalone analysis logged to files {analysis_number}")
        
    except Exception as e:
        print(f"⚠️ [MEMORY_ENHANCED] Failed to log complete analysis: {e}")

async def run_memory_enhanced_routine_generation(user_id: str, archetype: str, behavior_analysis: dict) -> dict:
    """
    Memory-Enhanced Routine Generation - Includes all features from /api/analyze
    Features:
    - Memory context preparation using MemoryIntegrationService
    - Memory-enhanced prompt generation
    - Storing routine plan in memory tables
    - Updating user memory profile
    - Complete logging of routine generation data
    """
    try:
        print(f"🏃 [MEMORY_ENHANCED] Starting memory-enhanced routine generation for {user_id[:8]}...")
        
        # Import memory integration service
        from services.memory_integration_service import MemoryIntegrationService
        
        # Initialize memory integration service
        memory_service = MemoryIntegrationService()
        
        # Step 1: Prepare memory-enhanced context
        print(f"📋 [MEMORY_ENHANCED] Preparing memory context for routine generation...")
        memory_context = await memory_service.prepare_memory_enhanced_context(user_id)
        
        # Step 2: Get user data for routine generation
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        
        # Get user data (service handles days internally based on analysis history)
        user_context, data_quality = await user_service.get_analysis_data(user_id)
        
        print(f"🗓️ [MEMORY_ENHANCED] Using {memory_context.days_to_fetch} days of data for routine (mode: {memory_context.analysis_mode})")
        
        # Step 3: Get and enhance system prompt with memory
        system_prompt = get_system_prompt("routine_plan")
        enhanced_prompt = await memory_service.enhance_agent_prompt(
            system_prompt, memory_context, "routine_plan"
        )
        
        print(f"🧠 [MEMORY_ENHANCED] Enhanced routine prompt with memory context (+{len(enhanced_prompt) - len(system_prompt)} chars)")
        
        # Step 4: Prepare routine agent data with memory context
        user_context_summary = await format_health_data_for_ai(user_context)
        routine_data = await prepare_routine_agent_data(user_context, behavior_analysis)
        
        # Step 5: Run routine planning with memory-enhanced prompt
        routine_result = await run_routine_planning_4o(enhanced_prompt, user_context_summary, behavior_analysis, archetype)
        
        # Step 6: Store routine plan insights in memory
        print(f"💾 [MEMORY_ENHANCED] Storing routine plan insights in memory...")
        insights_stored = await memory_service.store_analysis_insights(
            user_id, "routine_plan", routine_result, archetype
        )
        
        if insights_stored:
            print(f"✅ [MEMORY_ENHANCED] Routine plan insights stored successfully")
        else:
            print(f"⚠️ [MEMORY_ENHANCED] Failed to store routine plan insights")
        
        # Step 7: Store complete routine plan in holistic_analysis_results table
        print(f"💾 [MEMORY_ENHANCED] Storing complete routine plan in database...")
        try:
            from services.agents.memory.holistic_memory_service import HolisticMemoryService
            holistic_memory = HolisticMemoryService()
            
            # Store the complete routine result
            analysis_id = await holistic_memory.store_analysis_result(
                user_id, "routine_plan", routine_result, archetype
            )
            print(f"✅ [MEMORY_ENHANCED] Complete routine plan stored with ID: {analysis_id}")
            
            await holistic_memory.cleanup()
        except Exception as e:
            print(f"⚠️ [MEMORY_ENHANCED] Failed to store complete routine plan: {e}")
        
        # Step 8: Log complete routine generation data (input/output logging)
        await log_complete_standalone_analysis(
            "routine_plan", user_id, archetype, 
            routine_data, routine_result, memory_context
        )
        
        # Step 9: Cleanup memory service
        await memory_service.cleanup()
        
        # Add memory enhancement metadata to result
        routine_result.update({
            "memory_enhanced": True,
            "analysis_mode": memory_context.analysis_mode,
            "days_fetched": memory_context.days_to_fetch,
            "memory_focus_areas": memory_context.personalized_focus_areas,
            "insights_stored": insights_stored
        })
        
        print(f"✅ [MEMORY_ENHANCED] Memory-enhanced routine generation completed for {user_id[:8]}")
        return routine_result
        
    except Exception as e:
        print(f"❌ [MEMORY_ENHANCED] Error in memory-enhanced routine generation: {e}")
        # Fallback to regular routine generation
        print(f"🔄 [MEMORY_ENHANCED] Falling back to regular routine generation...")
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        user_context, _ = await user_service.get_analysis_data(user_id)
        user_context_summary = await format_health_data_for_ai(user_context)
        system_prompt = get_system_prompt("routine_plan")
        
        return await run_routine_planning_4o(system_prompt, user_context_summary, behavior_analysis, archetype)

async def run_memory_enhanced_nutrition_generation(user_id: str, archetype: str, behavior_analysis: dict) -> dict:
    """
    Memory-Enhanced Nutrition Generation - Includes all features from /api/analyze
    Features:
    - Memory context preparation using MemoryIntegrationService
    - Memory-enhanced prompt generation
    - Storing nutrition plan in memory tables
    - Updating user memory profile
    - Complete logging of nutrition generation data
    """
    try:
        print(f"🥗 [MEMORY_ENHANCED] Starting memory-enhanced nutrition generation for {user_id[:8]}...")
        
        # Import memory integration service
        from services.memory_integration_service import MemoryIntegrationService
        
        # Initialize memory integration service
        memory_service = MemoryIntegrationService()
        
        # Step 1: Prepare memory-enhanced context
        print(f"📋 [MEMORY_ENHANCED] Preparing memory context for nutrition generation...")
        memory_context = await memory_service.prepare_memory_enhanced_context(user_id)
        
        # Step 2: Get user data for nutrition generation
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        
        # Get user data (service handles days internally based on analysis history)
        user_context, data_quality = await user_service.get_analysis_data(user_id)
        
        print(f"🗓️ [MEMORY_ENHANCED] Using {memory_context.days_to_fetch} days of data for nutrition (mode: {memory_context.analysis_mode})")
        
        # Step 3: Get and enhance system prompt with memory
        system_prompt = get_system_prompt("nutrition_plan")
        enhanced_prompt = await memory_service.enhance_agent_prompt(
            system_prompt, memory_context, "nutrition_plan"
        )
        
        print(f"🧠 [MEMORY_ENHANCED] Enhanced nutrition prompt with memory context (+{len(enhanced_prompt) - len(system_prompt)} chars)")
        
        # Step 4: Prepare nutrition agent data with memory context
        user_context_summary = await format_health_data_for_ai(user_context)
        nutrition_data = await prepare_nutrition_agent_data(user_context, behavior_analysis)
        
        # Step 5: Run nutrition planning with memory-enhanced prompt
        nutrition_result = await run_nutrition_planning_4o(enhanced_prompt, user_context_summary, behavior_analysis, archetype)
        
        # Step 6: Store nutrition plan insights in memory
        print(f"💾 [MEMORY_ENHANCED] Storing nutrition plan insights in memory...")
        insights_stored = await memory_service.store_analysis_insights(
            user_id, "nutrition_plan", nutrition_result, archetype
        )
        
        if insights_stored:
            print(f"✅ [MEMORY_ENHANCED] Nutrition plan insights stored successfully")
        else:
            print(f"⚠️ [MEMORY_ENHANCED] Failed to store nutrition plan insights")
        
        # Step 7: Store complete nutrition plan in holistic_analysis_results table
        print(f"💾 [MEMORY_ENHANCED] Storing complete nutrition plan in database...")
        try:
            from services.agents.memory.holistic_memory_service import HolisticMemoryService
            holistic_memory = HolisticMemoryService()
            
            # Store the complete nutrition result
            analysis_id = await holistic_memory.store_analysis_result(
                user_id, "nutrition_plan", nutrition_result, archetype
            )
            print(f"✅ [MEMORY_ENHANCED] Complete nutrition plan stored with ID: {analysis_id}")
            
            await holistic_memory.cleanup()
        except Exception as e:
            print(f"⚠️ [MEMORY_ENHANCED] Failed to store complete nutrition plan: {e}")
        
        # Step 8: Log complete nutrition generation data (input/output logging)
        await log_complete_standalone_analysis(
            "nutrition_plan", user_id, archetype, 
            nutrition_data, nutrition_result, memory_context
        )
        
        # Step 9: Cleanup memory service
        await memory_service.cleanup()
        
        # Add memory enhancement metadata to result
        nutrition_result.update({
            "memory_enhanced": True,
            "analysis_mode": memory_context.analysis_mode,
            "days_fetched": memory_context.days_to_fetch,
            "memory_focus_areas": memory_context.personalized_focus_areas,
            "insights_stored": insights_stored
        })
        
        print(f"✅ [MEMORY_ENHANCED] Memory-enhanced nutrition generation completed for {user_id[:8]}")
        return nutrition_result
        
    except Exception as e:
        print(f"❌ [MEMORY_ENHANCED] Error in memory-enhanced nutrition generation: {e}")
        # Fallback to regular nutrition generation
        print(f"🔄 [MEMORY_ENHANCED] Falling back to regular nutrition generation...")
        from services.user_data_service import UserDataService
        from shared_libs.utils.system_prompts import get_system_prompt
        
        user_service = UserDataService()
        user_context, _ = await user_service.get_analysis_data(user_id)
        user_context_summary = await format_health_data_for_ai(user_context)
        system_prompt = get_system_prompt("nutrition_plan")
        
        return await run_nutrition_planning_4o(system_prompt, user_context_summary, behavior_analysis, archetype)

>>>>>>> 2a82c3b (Safety snapshot before reconnecting to origin)
async def run_nutrition_planning_4o(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str) -> dict:
    """Run nutrition planning using gpt-4o for plan generation - Phase 3.2"""
    try:
        client = openai.AsyncOpenAI()
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": f"{system_prompt}\n\nYou are a nutrition planning expert. Create detailed, practical nutrition plans based on health data and behavioral insights."
                },
                {
                    "role": "user", 
                    "content": f"""
{user_context}

BEHAVIORAL INSIGHTS:
{json.dumps(behavior_analysis, indent=2)}

Create a comprehensive {archetype} nutrition plan for TODAY using the HolisticOS approach.

Include the following structure:
1. **Daily Nutritional Targets** (calories, protein, carbs, fats, fiber, vitamins)
2. **7 Meal Blocks** with detailed breakdown:
   - Early_Morning: Light hydration/preparation
   - Breakfast: Balanced start with protein and complex carbs
   - Morning_Snack: Energy maintenance
   - Lunch: Balanced midday nutrition
   - Afternoon_Snack: Sustained energy
   - Dinner: Recovery and satisfaction
   - Evening_Snack: Sleep preparation
3. **Nutrition Tips** for each meal explaining timing and composition
4. **Health Data Integration** - reference the provided health metrics

Make this plan practical, evidence-based, and specifically tailored to the {archetype} archetype and the provided health data patterns.
"""
                }
            ],
            temperature=0.4,  # Balanced creativity for practical planning
            max_tokens=2000
        )
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "archetype": archetype,
            "content": response.choices[0].message.content,
            "model_used": "gpt-4o",
            "plan_type": "comprehensive_nutrition",
            "system": "HolisticOS"
        }
        
    except Exception as e:
        print(f"Error in 4o nutrition planning: {e}")
        return {
            "error": str(e), 
            "model_used": "gpt-4o - fallback",
            "archetype": archetype,
            "date": datetime.now().strftime("%Y-%m-%d")
        }

async def run_routine_planning_4o(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str) -> dict:
    """Run routine planning using gpt-4o for plan generation - Phase 3.2"""
    try:
        client = openai.AsyncOpenAI()
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": f"{system_prompt}\n\nYou are a routine optimization expert. Create actionable daily routines based on health data, behavioral insights, and archetype frameworks."
                },
                {
                    "role": "user", 
                    "content": f"""
{user_context}

BEHAVIORAL INSIGHTS:
{json.dumps(behavior_analysis, indent=2)}

Create a comprehensive {archetype} routine plan for TODAY using the HolisticOS approach.

Structure the plan with these 4 time blocks:

1. **Morning Wakeup** (6:00 AM - 8:00 AM)
   - Hydration and activation tasks
   - Mindfulness or preparation activities
   - Energy optimization based on sleep data

2. **Focus Block** (9:00 AM - 12:00 PM) 
   - Peak productivity tasks aligned with archetype
   - Break timing based on activity patterns
   - Cognitive optimization strategies

3. **Afternoon Recharge** (1:00 PM - 4:00 PM)
   - Recovery and refueling activities
   - Physical activity aligned with fitness data
   - Energy maintenance strategies

4. **Evening Winddown** (8:00 PM - 10:00 PM)
   - Sleep preparation based on sleep patterns
   - Recovery activities
   - Next-day preparation

For each block include:
- Specific time ranges and tasks
- Scientific reasoning for each element
- Integration with provided health data patterns
- {archetype}-specific customizations

Make this routine actionable, evidence-based, and specifically tailored to the health data insights.
"""
                }
            ],
            temperature=0.4,  # Balanced creativity for practical planning
            max_tokens=2000
        )
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "archetype": archetype,
            "content": response.choices[0].message.content,
            "model_used": "gpt-4o",
            "plan_type": "comprehensive_routine",
            "system": "HolisticOS"
        }
        
    except Exception as e:
        print(f"Error in 4o routine planning: {e}")
        return {
            "error": str(e), 
            "model_used": "gpt-4o - fallback",
            "archetype": archetype,
            "date": datetime.now().strftime("%Y-%m-%d")
        }

@app.get("/api/status/{user_id}")
async def get_analysis_status(user_id: str):
    """Get analysis status for a user"""
    return {
        "user_id": user_id,
        "status": "completed",
        "message": "Phase 1 - OpenAI Direct Integration",
        "timestamp": datetime.now().isoformat()
    }

async def get_next_analysis_number() -> int:
    """Get next analysis number for logging"""
    try:
        import glob
        existing_files = glob.glob("logs/input_*.txt")
        if not existing_files:
            return 1
        
        numbers = []
        for filename in existing_files:
            try:
                number = int(filename.split("_")[1].split(".")[0])
                numbers.append(number)
            except ValueError:
                continue
        
        return max(numbers) + 1 if numbers else 1
        
    except Exception:
        return 1

async def log_analysis_data(input_data: dict, output_data: dict, analysis_number: int):
    """Log analysis data to files with enhanced details"""
    try:
        os.makedirs("logs", exist_ok=True)
        os.makedirs("logs/agent_handoffs", exist_ok=True)
        
        # Enhanced input log with raw data
        with open(f"logs/input_{analysis_number}.txt", 'w') as f:
            json.dump(input_data, f, indent=2, default=str)
        
        # Enhanced output log
        with open(f"logs/output_{analysis_number}.txt", 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
            
        print(f"📝 Analysis logged: logs/input_{analysis_number}.txt, logs/output_{analysis_number}.txt")
        
    except Exception as e:
        print(f"Error logging: {e}")

async def log_agent_handoff(agent_name: str, input_data: dict, output_data: dict, analysis_number: int):
    """Log data at each agent handoff point"""
    try:
        os.makedirs("logs/agent_handoffs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"logs/agent_handoffs/{analysis_number}_{agent_name}_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(f"{'='*60}\n")
            f.write(f"AGENT HANDOFF: {agent_name.upper()}\n")
            f.write(f"Analysis #: {analysis_number}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"{'='*60}\n\n")
            
            f.write("INPUT DATA:\n")
            f.write("-"*40 + "\n")
            json.dump(input_data, f, indent=2, default=str)
            f.write("\n\n")
            
            f.write("OUTPUT DATA:\n")
            f.write("-"*40 + "\n")
            json.dump(output_data, f, indent=2, default=str)
            f.write("\n\n")
            
            f.write(f"{'='*60}\n")
            
        print(f"   📋 Agent handoff logged: {agent_name} → {filename}")
        
    except Exception as e:
        print(f"Error logging agent handoff: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)