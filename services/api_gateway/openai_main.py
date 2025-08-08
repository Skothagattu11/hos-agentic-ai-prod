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
    User analysis endpoint - OpenAI direct implementation
    Uses HolisticOS system prompts with OpenAI API directly
    """
    try:
        user_id = request.user_id
        archetype = request.archetype
        
        print(f"🔍 Starting OpenAI-based analysis for user: {user_id}, archetype: {archetype}")
        
        # Import system prompts
        from shared_libs.utils.system_prompts import get_system_prompt, get_archetype_adaptation
        
        # Get system prompts
        behavior_prompt = get_system_prompt("behavior_analysis")
        nutrition_prompt = get_system_prompt("plan_generation") 
        routine_prompt = get_system_prompt("plan_generation")
        archetype_guidance = get_archetype_adaptation(archetype)
        
        print(f"✅ System prompts loaded: {len(behavior_prompt):,} chars")
        
        # Create user context summary for analysis
        user_context_summary = f"""
USER ANALYSIS REQUEST:
- User ID: {user_id}
- Selected Archetype: {archetype}
- Analysis Date: {datetime.now().strftime('%Y-%m-%d')}
- Mode: Phase 1 Testing (Fallback data)

ARCHETYPE GUIDANCE:
{archetype_guidance}

Note: This is a test analysis using fallback data patterns since no real user data is available for {user_id}.
Please provide a comprehensive analysis that demonstrates the {archetype} approach to health optimization.
"""

        # Step 1: Behavior Analysis
        print("🧠 Running behavior analysis with OpenAI...")
        behavior_analysis = await run_behavior_analysis(behavior_prompt, user_context_summary)
        print(f"✅ Behavior analysis complete")
        
        # Step 2: Nutrition Plan
        print("🥗 Generating nutrition plan with OpenAI...")
        nutrition_plan = await run_nutrition_planning(nutrition_prompt, user_context_summary, behavior_analysis, archetype)
        print(f"✅ Nutrition plan complete")
        
        # Step 3: Routine Plan
        print("🏃‍♂️ Generating routine plan with OpenAI...")
        routine_plan = await run_routine_planning(routine_prompt, user_context_summary, behavior_analysis, archetype)
        print(f"✅ Routine plan complete")
        
        # Log analysis data
        analysis_number = await get_next_analysis_number()
        await log_analysis_data({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "archetype": archetype,
            "mode": "OpenAI Direct",
            "analysis_number": analysis_number
        }, {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "archetype": archetype,
            "behavior_analysis": behavior_analysis,
            "nutrition_plan": nutrition_plan,
            "routine_plan": routine_plan,
            "analysis_number": analysis_number
        }, analysis_number)
        
        print(f"✅ Complete analysis finished for {user_id}")
        
        return AnalysisResponse(
            status="success",
            user_id=user_id,
            archetype=archetype,
            message="Analysis completed successfully using HolisticOS system prompts",
            analysis={
                "behavior_analysis": behavior_analysis,
                "nutrition_plan": nutrition_plan,
                "routine_plan": routine_plan,
                "system_info": {
                    "mode": "OpenAI Direct Integration",
                    "prompt_system": "HolisticOS",
                    "archetype_applied": archetype
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

async def run_behavior_analysis(system_prompt: str, user_context: str) -> dict:
    """Run behavior analysis using OpenAI with HolisticOS prompts"""
    try:
        response = await asyncio.to_thread(
            openai.chat.completions.create,
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
{user_context}

Please provide a comprehensive behavioral analysis following the HolisticOS framework. 
Return a JSON-structured analysis including:
- behavioral_signature (with signature and confidence)
- sophistication_assessment (with score, category, justification)  
- primary_goal (with goal, timeline, success_metrics)
- personalized_strategy (with motivation_drivers, habit_integration, barrier_mitigation)
- readiness_level
- recommendations

Make this analysis realistic and detailed as if for a real user.
"""}
            ],
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        # Try to parse as JSON, fallback to structured text
        try:
            return json.loads(content)
        except:
            return {
                "behavioral_signature": {
                    "signature": "OpenAI Generated Analysis",
                    "confidence": 0.85
                },
                "sophistication_assessment": {
                    "score": 75,
                    "category": "Advanced",
                    "justification": "Generated using HolisticOS system prompts"
                },
                "analysis_content": content,
                "mode": "OpenAI Direct"
            }
            
    except Exception as e:
        print(f"Error in behavior analysis: {e}")
        return {
            "error": str(e),
            "mode": "OpenAI Direct - Fallback",
            "behavioral_signature": {"signature": "Fallback Analysis", "confidence": 0.5}
        }

async def run_nutrition_planning(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str) -> dict:
    """Run nutrition planning using OpenAI with HolisticOS prompts"""
    try:
        response = await asyncio.to_thread(
            openai.chat.completions.create,
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
{user_context}

BEHAVIOR ANALYSIS RESULTS:
{json.dumps(behavior_analysis, indent=2)}

Create a detailed {archetype} nutrition plan for TODAY using the HolisticOS approach.
Include:
- Complete daily nutritional targets (calories, macros, vitamins)
- 7 meal blocks: Early_Morning, Breakfast, Morning_Snack, Lunch, Afternoon_Snack, Dinner, Evening_Snack
- Each meal with specific foods, calories, protein, and macro breakdown
- Nutrition tips explaining timing and composition

Make this practical and {archetype}-appropriate.
"""}
            ],
            temperature=0.7
        )
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "archetype": archetype,
            "content": response.choices[0].message.content,
            "mode": "OpenAI Direct",
            "system": "HolisticOS"
        }
        
    except Exception as e:
        print(f"Error in nutrition planning: {e}")
        return {"error": str(e), "mode": "OpenAI Direct - Fallback"}

async def run_routine_planning(system_prompt: str, user_context: str, behavior_analysis: dict, archetype: str) -> dict:
    """Run routine planning using OpenAI with HolisticOS prompts"""
    try:
        response = await asyncio.to_thread(
            openai.chat.completions.create,
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
{user_context}

BEHAVIOR ANALYSIS RESULTS:
{json.dumps(behavior_analysis, indent=2)}

Create a detailed {archetype} routine plan for TODAY using the HolisticOS approach.
Include:
- 4 time blocks: morning_wakeup, focus_block, afternoon_recharge, evening_winddown
- Each block with specific time ranges, tasks, and scientific reasoning
- Tasks should reflect the {archetype} philosophy and approach
- Explain why each routine element matters for this archetype

Make this actionable and {archetype}-specific.
"""}
            ],
            temperature=0.7
        )
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "archetype": archetype,
            "content": response.choices[0].message.content,
            "mode": "OpenAI Direct",
            "system": "HolisticOS"
        }
        
    except Exception as e:
        print(f"Error in routine planning: {e}")
        return {"error": str(e), "mode": "OpenAI Direct - Fallback"}

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
    """Log analysis data to files"""
    try:
        os.makedirs("logs", exist_ok=True)
        
        with open(f"logs/input_{analysis_number}.txt", 'w') as f:
            json.dump(input_data, f, indent=2, default=str)
        
        with open(f"logs/output_{analysis_number}.txt", 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
            
        print(f"📝 Analysis logged: logs/input_{analysis_number}.txt, logs/output_{analysis_number}.txt")
        
    except Exception as e:
        print(f"Error logging: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)