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
    print("   • GET /api/v1/health-data/users/{user_id}/health-context")
    print("   • GET /api/v1/health-data/users/{user_id}/summary") 
    print("   • GET /api/v1/health-data/users/{user_id}/data-quality")
    print("   • GET /api/v1/health-data/users/{user_id}/agent/{agent}/data")
    print("   • POST /api/v1/health-data/users/{user_id}/analyze")
    print("   • GET /api/v1/health-data/system/health")
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
        
        print("✅ All agents initialized successfully")
        print(f"   🏗️  Orchestrator: {orchestrator.agent_id}")
        print(f"   🧠 Memory Agent: {memory_agent.agent_id}")
        print(f"   🔍 Insights Agent: {insights_agent.agent_id}")
        print(f"   ⚡ Adaptation Engine: {adaptation_agent.agent_id}")
        
    except Exception as e:
        print(f"❌ Error initializing agents: {e}")
        # Continue with limited functionality
        pass

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
        
        # Initialize UserDataService for real data
        user_service = UserDataService()
        
        try:
            # PHASE 4.0 MVP: Use incremental sync for efficiency  
            print(f"📊 Fetching user data with incremental sync for {user_id}...")
            user_context = await user_service.get_incremental_health_data(user_id)
            
            # Extract real data for analysis
            data_quality = user_context.data_quality
            print(f"✅ Real data retrieved:")
            print(f"   • Data Quality: {data_quality.quality_level}")
            print(f"   • Scores: {data_quality.scores_count}")
            print(f"   • Biomarkers: {data_quality.biomarkers_count}")
            print(f"   • Completeness: {data_quality.completeness_score:.2f}")
            
            # Get system prompts
            behavior_prompt = get_system_prompt("behavior_analysis")
            nutrition_prompt = get_system_prompt("plan_generation") 
            routine_prompt = get_system_prompt("plan_generation")
            archetype_guidance = get_archetype_adaptation(archetype)
            
            print(f"✅ System prompts loaded: {len(behavior_prompt):,} chars")
            
            # PHASE 3.2: Create health context summary with AI-friendly language
            user_context_summary = f"""
HEALTH ANALYSIS REQUEST - COMPREHENSIVE DATA:
- Profile Reference: {user_id}
- Health Archetype: {archetype}
- Analysis Date: {datetime.now().strftime('%Y-%m-%d')}
- Mode: Comprehensive Health Analysis (Phase 3.2)

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

ANALYSIS INSTRUCTIONS: You have comprehensive health tracking data including sleep patterns, activity metrics, and biomarker readings. Analyze these health indicators to identify patterns, trends, and insights that align with the {archetype} framework. Focus on actionable observations from the provided health metrics.
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
            # Always cleanup the service
            await user_service.cleanup()

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
                    "level": data_quality.quality_level.value if 'data_quality' in locals() else "unknown",
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
                            "date": score.created_at.strftime("%Y-%m-%d") if hasattr(score, 'created_at') else "unknown",
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
        
        return AnalysisResponse(
            status="success",
            user_id=user_id,
            archetype=archetype,
            message="Analysis completed successfully using comprehensive health data with multi-model approach - Phase 3.2",
            analysis={
                "behavior_analysis": behavior_analysis,
                "nutrition_plan": nutrition_plan,
                "routine_plan": routine_plan,
                "system_info": {
                    "mode": analysis_mode,
                    "prompt_system": "HolisticOS",
                    "archetype_applied": archetype,
                    "phase": "3.3 - Agent-Specific Data Filtering",
                    "data_source": "Supabase via UserDataService",
                    "models_used": {
                        "behavior_analysis": "o3 (deep analysis)",
                        "nutrition_plan": "gpt-4o (plan generation)",
                        "routine_plan": "gpt-4o (plan generation)"
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

async def prepare_behavior_agent_data(user_context, user_context_summary: str) -> dict:
    """Prepare comprehensive data for behavior analysis agent (o3) - Phase 3.3"""
    try:
        # Behavior agent gets the most comprehensive data for pattern analysis
        behavior_data = {
            "comprehensive_health_context": user_context_summary,
            "detailed_metrics": {
                "data_quality": {
                    "level": user_context.data_quality.quality_level.value,
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
                        "date": score.created_at.strftime("%Y-%m-%d"),
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
                    "date": score.created_at.strftime("%Y-%m-%d"),
                    "activity_score": score.score,
                    "state": score.data.get("state", "unknown") if score.data else "unknown"
                }
                for score in user_context.scores if score.type == "activity"
            ][:7],  # Last 7 days of activity
            
            "sleep_quality": [
                {
                    "date": score.created_at.strftime("%Y-%m-%d"),
                    "sleep_score": score.score,
                    "state": score.data.get("state", "unknown") if score.data else "unknown"
                }
                for score in user_context.scores if score.type == "sleep"
            ][:7],  # Last 7 days of sleep
            
            "energy_indicators": [
                {
                    "date": score.created_at.strftime("%Y-%m-%d"),
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
                    "date": score.created_at.strftime("%Y-%m-%d"),
                    "sleep_score": score.score,
                    "sleep_state": score.data.get("state", "unknown") if score.data else "unknown",
                    "factors": score.data.get("factors", []) if score.data else []
                }
                for score in user_context.scores if score.type == "sleep"
            ][:7],  # Last 7 days for pattern recognition
            
            "activity_patterns": [
                {
                    "date": score.created_at.strftime("%Y-%m-%d"),
                    "activity_score": score.score,
                    "activity_state": score.data.get("state", "unknown") if score.data else "unknown",
                    "factors": score.data.get("factors", []) if score.data else []
                }
                for score in user_context.scores if score.type == "activity"
            ][:7],  # Last 7 days for routine optimization
            
            "recovery_readiness": [
                {
                    "date": score.created_at.strftime("%Y-%m-%d"),
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
                'date': score.created_at.strftime('%Y-%m-%d'),
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