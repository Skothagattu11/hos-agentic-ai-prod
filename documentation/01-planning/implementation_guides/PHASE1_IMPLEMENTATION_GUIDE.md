# Phase 1 Implementation Guide - Detailed Action Plan

## Overview

This guide provides step-by-step instructions for implementing Phase 1 of the HolisticOS MVP, focusing on foundation setup and basic agent architecture while preserving existing system functionality.

## Week 1: Project Setup & Foundation

### Day 1-2: Environment Setup & Dependencies

**Step 1: Create Core Configuration Files**

**Action Items:**
1. **Create requirements.txt**
   ```txt
   fastapi==0.104.1
   uvicorn==0.24.0
   pydantic==2.5.0
   redis==5.0.1
   asyncpg==0.29.0
   supabase==2.0.0
   python-dotenv==1.0.0
   structlog==23.2.0
   pytest==7.4.3
   pytest-asyncio==0.21.1
   ```

2. **Create .env.example**
   ```env
   # Supabase Configuration (preserve existing)
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_KEY=your_supabase_key_here
   
   # New HolisticOS Configuration  
   REDIS_URL=redis://localhost:6379
   DATABASE_URL=postgresql://user:pass@localhost:5432/holistic_memory
   ENVIRONMENT=development
   LOG_LEVEL=INFO
   
   # OpenAI (preserve existing)
   OPENAI_API_KEY=your_openai_key_here
   ```

3. **Create basic render.yaml**
   ```yaml
   services:
     - type: web
       name: holistic-api
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: uvicorn services.api_gateway.main:app --host 0.0.0.0 --port $PORT
   ```

**Step 2: Migrate Existing Code to Shared Libraries**

**Action Items:**
1. **Copy existing models**
   ```bash
   cp ../health-agent-main/health_agents/models.py shared-libs/data-models/base_models.py
   ```

2. **Copy Supabase adapter**
   ```bash
   cp ../health-agent-main/health_agents/supabase_adapter.py shared-libs/supabase-client/adapter.py
   ```

3. **Copy existing agent logic**
   ```bash
   cp ../health-agent-main/health_agents/behavior_analysis_agent.py shared-libs/utils/existing_agents.py
   cp ../health-agent-main/health_agents/nutrition_plan_agent.py shared-libs/utils/existing_agents.py
   cp ../health-agent-main/health_agents/routine_plan_agent.py shared-libs/utils/existing_agents.py
   ```

### Day 3-4: Basic API Gateway Setup

**Step 3: Create API Gateway Service**

**File: `services/api-gateway/main.py`**
**Action Items:**
1. **Basic FastAPI setup with existing endpoint compatibility**
2. **Preserve exact same API interface as current system**
3. **Add Redis connection for future event publishing**
4. **Maintain Supabase data fetching mechanism**

**Implementation Structure:**
```python
# services/api-gateway/main.py
from fastapi import FastAPI
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
from shared_libs.data_models.base_models import UserProfileContext

app = FastAPI(title="HolisticOS API Gateway")

@app.get("/")
async def root():
    return {"message": "HolisticOS API Gateway", "status": "active"}

@app.post("/api/analyze")  
async def analyze_user(user_id: str, archetype: str):
    # PRESERVE: Same data fetching as current system
    # TODO: Add orchestrator communication
    pass

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

**Step 4: Test Basic API Gateway Locally**

**Action Items:**
1. **Start local development server**
   ```bash
   cd holisticos-mvp
   uvicorn services.api_gateway.main:app --reload --host 0.0.0.0 --port 8001
   ```

2. **Test endpoints**
   ```bash
   curl http://localhost:8001/
   curl http://localhost:8001/api/health
   ```

3. **Verify Supabase connection works**

### Day 5-7: Basic Render Deployment

**Step 5: Initial Render Deployment**

**Action Items:**
1. **Create GitHub repository for holisticos-mvp**
2. **Connect repository to Render**
3. **Configure basic environment variables in Render**
4. **Deploy and test basic API endpoints**
5. **Verify deployment health and accessibility**

**Expected Result:** Working API gateway deployed on Render with health endpoints responding

## Week 2: Agent Service Architecture

### Day 8-10: Agent Worker Foundation

**Step 6: Create Base Agent Framework**

**File: `shared-libs/event-system/base_agent.py`**
**Action Items:**
1. **Create base agent class for all agents to inherit**
2. **Implement Redis Pub/Sub communication pattern**
3. **Add structured logging and error handling**
4. **Create event publishing/subscribing mechanisms**

**Step 7: Implement Behavior Agent Worker**

**File: `services/agents/behavior/main.py`**
**Action Items:**
1. **Convert existing behavior_analysis_agent.py to background worker**
2. **Preserve all existing analysis logic**
3. **Add Redis event listening**
4. **Implement result publishing to orchestrator**
5. **Maintain input_N.txt logging functionality**

**Implementation Structure:**
```python
# services/agents/behavior/main.py
import asyncio
import redis
import json
from shared_libs.utils.existing_agents import BehaviorAnalysisAgent
from shared_libs.event_system.base_agent import BaseAgent

class BehaviorWorker(BaseAgent):
    def __init__(self):
        super().__init__("behavior_agent")
        self.analysis_agent = BehaviorAnalysisAgent()  # Your existing agent
        
    async def process_analysis_request(self, user_context: dict):
        # Use existing analysis logic
        result = await self.analysis_agent.analyze(user_context)
        
        # Preserve input logging
        self.log_input_output(user_context, result)
        
        # Publish result for next agent
        await self.publish_event("behavior_analysis_complete", {
            "user_id": user_context["user_id"],
            "analysis_result": result.dict(),
            "next_agent": "nutrition"
        })
        
    async def run(self):
        await self.subscribe_to_events(["analysis_request"], self.process_analysis_request)

if __name__ == "__main__":
    worker = BehaviorWorker()
    asyncio.run(worker.run())
```

### Day 11-14: Memory System & Additional Agents

**Step 8: Implement Memory Agent**

**File: `services/agents/memory/main.py`**
**Action Items:**
1. **Convert existing memory_manager.py to background worker**
2. **Implement 4-layer memory hierarchy**
3. **Add pattern learning and consolidation**
4. **Preserve existing user memory functionality**

**Step 9: Convert Nutrition & Routine Agents**

**Files: `services/agents/nutrition/main.py` & `services/agents/routine/main.py`**
**Action Items:**
1. **Convert existing nutrition and routine agents to workers**
2. **Preserve all existing plan generation logic**
3. **Add event-driven communication**
4. **Maintain compatibility with current output formats**

**Step 10: Basic Orchestrator Implementation**

**File: `services/orchestrator/main.py`**
**Action Items:**
1. **Create workflow coordination logic**
2. **Implement agent sequencing (Behavior → Nutrition → Routine)**
3. **Add progress tracking and status updates**
4. **Handle error scenarios and agent failures**

## Testing Strategy for Phase 1

### Unit Testing Setup

**Action Items:**
1. **Create test fixtures using existing input data**
2. **Test individual agent functionality**
3. **Verify Supabase connection and data retrieval**
4. **Test Redis communication between agents**

### Integration Testing

**Action Items:**
1. **Test complete workflow: API → Orchestrator → Agents → Results**
2. **Verify data preservation and output format compatibility**
3. **Test error handling and recovery scenarios**
4. **Performance testing with sample user data**

### Local Development Workflow

**Daily Development Process:**
1. **Make code changes locally**
2. **Test with `uvicorn` locally** 
3. **Run unit tests with `pytest`**
4. **Commit and push to trigger Render deployment**
5. **Test deployed version on Render**

## Expected Outcomes After Phase 1

### Week 1 Completion:
- ✅ Project structure established
- ✅ Basic API gateway deployed on Render
- ✅ Existing code migrated to shared libraries
- ✅ Development workflow established

### Week 2 Completion:
- ✅ 3-4 agents converted to background workers
- ✅ Redis communication system working
- ✅ Basic orchestrator coordinating workflow
- ✅ End-to-end analysis working (simplified version)

### System Capabilities After Phase 1:
- **Functional API**: Same endpoints as current system
- **Agent Communication**: Basic event-driven architecture
- **Data Preservation**: All existing data fetching maintained
- **Deployment**: Cloud-based system on Render
- **Fallback Ready**: Original system still available if needed

## Risk Management

### Technical Risks & Mitigation:
1. **Agent Communication Issues**: Start with simple Redis patterns, add complexity gradually
2. **Data Loss**: Extensive testing with existing data, preserve all input logging
3. **Performance Issues**: Monitor response times, optimize Redis usage
4. **Deployment Problems**: Start with minimal Render config, add services incrementally

### Rollback Plan:
- Original health-agent-main system remains untouched
- Can route traffic back to original system instantly
- All data and analysis history preserved
- No user impact during development

## File Structure After Phase 1

```
holisticos-mvp/
├── requirements.txt
├── .env.example
├── render.yaml
├── services/
│   ├── api-gateway/
│   │   └── main.py
│   ├── orchestrator/
│   │   └── main.py
│   └── agents/
│       ├── behavior/
│       │   └── main.py
│       ├── memory/
│       │   └── main.py
│       ├── nutrition/
│       │   └── main.py
│       └── routine/
│           └── main.py
├── shared-libs/
│   ├── data-models/
│   │   └── base_models.py
│   ├── supabase-client/
│   │   └── adapter.py
│   ├── event-system/
│   │   └── base_agent.py
│   └── utils/
│       └── existing_agents.py
└── tests/
    ├── unit/
    ├── integration/
    └── performance/
```

## Next Steps After Phase 1

Once Phase 1 is complete, you'll be ready for:
- **Phase 2**: Adding HolisticOS advanced features (Insights & Adaptation agents)
- **Phase 3**: Production optimization, monitoring, and scaling
- **User Migration**: Gradual transition from original to new system

## Commands Reference

### Local Development
```bash
# Start API gateway
uvicorn services.api_gateway.main:app --reload --host 0.0.0.0 --port 8001

# Run tests
python -m pytest tests/unit/
python -m pytest tests/integration/

# Start individual agents (for testing)
python services/agents/behavior/main.py
python services/orchestrator/main.py
```

### Deployment
```bash
# Deploy to Render
git add .
git commit -m "Phase 1: Add basic agent architecture"
git push origin main
```

### Testing Endpoints
```bash
# Health check
curl https://your-render-app.onrender.com/api/health

# Analysis request
curl -X POST https://your-render-app.onrender.com/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "archetype": "Peak Performer"}'
```