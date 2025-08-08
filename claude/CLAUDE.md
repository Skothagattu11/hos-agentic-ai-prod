# HolisticOS MVP - Claude Memory and Instructions

## Project Overview

This is the **HolisticOS Multi-Agent Health Optimization System MVP** - a sophisticated AI-powered health analysis platform built for 50-100 users scaling to 500-1000 users.

### Architecture Completed

✅ **Phase 1**: OpenAI Direct Integration with HolisticOS system prompts
✅ **Phase 2**: Complete Multi-Agent System with direct method calls

## Current System Status (Ready for Database Integration)

### Working Components:
1. **Multi-Agent Orchestrator** (`services/orchestrator/main.py`)
   - Direct agent method calls (Option A implementation)
   - Complete workflow coordination: Memory → Behavior → Plans → Insights → Adaptation
   - 100% test pass rate with end-to-end workflows

2. **Memory Management Agent** (`services/agents/memory/main.py`)
   - 4-layer hierarchical memory system (Working → Short-term → Long-term → Meta-memory)
   - Ready for database integration

3. **Insights Generation Agent** (`services/agents/insights/main.py`)
   - AI-powered pattern analysis using OpenAI GPT-4
   - Generates actionable health insights

4. **Adaptation Engine Agent** (`services/agents/adaptation/main.py`)
   - Real-time strategy adaptation based on user feedback
   - Dynamic archetype adjustments

5. **Enhanced API Gateway** (`services/api_gateway/openai_main.py`)
   - Phase 1 legacy endpoints (preserved)
   - Phase 2 complete multi-agent workflows
   - All agents initialized on startup

### System Prompts & Configuration:
- **System Prompts**: `shared_libs/utils/system_prompts.py` - centralized HolisticOS prompts
- **Event System**: `shared_libs/event_system/base_agent.py` - agent communication framework
- **Testing**: `test_end_to_end_api.py` - comprehensive API testing suite

## User's Existing Database Schema

The user has an existing Supabase database with:
- **biomarkers** - Health metrics and biomarker data
- **scores** - Health scores (readiness, sleep, activity, mental_wellbeing)
- **archetypes** - User health archetype definitions
- **users** - User account information
- **profiles** - User profile details and preferences
- **Memory tables** - Already added for Phase 2 (5 tables for hierarchical memory)

## Next Implementation Phase: Database Integration

### Immediate Tasks:
1. **Create workflow_executions table** for tracking multi-agent workflows
2. **Connect agents to existing Supabase database** using existing client setup
3. **Map agent operations to existing tables**:
   - Behavior Agent → reads from `biomarkers`, `scores`
   - Memory Agent → reads/writes to memory tables
   - Insights Agent → analyzes patterns across all tables
   - Adaptation Agent → updates user `archetypes` preferences
4. **Replace placeholder agents** with real database operations
5. **Test complete workflows with real user data**

### Database Integration Strategy:
```sql
-- New table needed for workflow tracking
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(id),
    workflow_id TEXT UNIQUE,
    archetype TEXT,
    stage TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    results JSONB,
    errors JSONB,
    success BOOLEAN DEFAULT FALSE
);
```

### Agent-Database Mapping:
- **Memory Agent**: Direct access to all 5 memory tables
- **Behavior Agent**: Query `biomarkers` and `scores` for last 7 days (initial) or 1 day (follow-up)
- **Insights Agent**: Cross-table analysis for pattern identification
- **Adaptation Agent**: Update `archetypes` and user preferences based on insights

## Technical Decisions Made

### Option A: Direct Method Calls (Implemented)
- **Why Chosen**: Simpler for MVP, easier debugging, perfect for 50-500 users
- **Implementation**: Orchestrator calls `agent.process()` directly instead of Redis pub/sub
- **Benefits**: Immediate workflow completion, easier error handling, no Redis dependency

### Archetype System (6 Types):
1. **Foundation Builder** - Simple, sustainable basics
2. **Transformation Seeker** - Ambitious lifestyle changes
3. **Systematic Improver** - Methodical, evidence-based progress
4. **Peak Performer** - Elite-level performance optimization
5. **Resilience Rebuilder** - Recovery and restoration focus
6. **Connected Explorer** - Social and adventure-oriented wellness

## Commands & Testing

### Start API Server:
```bash
cd /mnt/c/dev_skoth/health-agent-main/holisticos-mvp
python services/api_gateway/openai_main.py
```

### Run End-to-End Tests:
```bash
python test_end_to_end_api.py
```

### Test Individual Components:
```bash
python services/agents/memory/main.py
python services/agents/insights/main.py
python services/agents/adaptation/main.py
python services/orchestrator/main.py
```

## Key Files & Locations

### Core System:
- **API Gateway**: `services/api_gateway/openai_main.py`
- **Orchestrator**: `services/orchestrator/main.py`
- **Memory Agent**: `services/agents/memory/main.py`
- **Insights Agent**: `services/agents/insights/main.py`
- **Adaptation Agent**: `services/agents/adaptation/main.py`

### Configuration:
- **System Prompts**: `shared_libs/utils/system_prompts.py`
- **Base Agent**: `shared_libs/event_system/base_agent.py`
- **Memory Tables SQL**: `docs/memory_system_tables.sql`

### Testing:
- **End-to-End Tests**: `test_end_to_end_api.py`
- **Testing Guide**: `END_TO_END_TESTING_GUIDE.md`

### Documentation:
- **Memory Instructions**: `claude/CLAUDE.md` (this file)

## Environment Variables Required

```env
# OpenAI API (required for insights generation)
OPENAI_API_KEY=your_openai_api_key_here

# Database (for upcoming integration)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anonymous_key

# Redis (optional - not used in Option A)
REDIS_URL=redis://localhost:6379
```

## Current Performance & Scale

### Tested & Working:
- **Individual Agent Performance**: Sub-second response times
- **Complete Workflow**: 30-90 seconds (OpenAI dependent)
- **Memory Operations**: Instant with placeholder data
- **API Throughput**: Handles concurrent requests well

### Target Scale:
- **MVP**: 50-100 users (6 months)
- **Growth**: Scale to 500-1000 users
- **Architecture**: Ready for horizontal scaling when needed

## Recent Achievements

🎉 **Successfully implemented Option A (Direct Agent Calls)**:
- Fixed the workflow stuck issue (agents weren't listening for Redis events)
- All 5 test suites passing (100% success rate)
- Complete workflows now execute from start to finish
- Memory, Insights, and Adaptation agents working correctly
- Realistic placeholder agents for behavior, nutrition, routine analysis

## Next Session Continuation

When continuing, the focus will be on:

1. **Database Integration**: Connect to user's existing Supabase tables
2. **Real Data Operations**: Replace placeholders with actual health data queries
3. **Workflow Tracking**: Implement workflow_executions table
4. **Performance Testing**: Test with real user data and concurrent workflows
5. **Deployment Preparation**: Prepare for Render deployment

The system is **production-ready for MVP deployment** once database integration is complete.

---

**System Status**: ✅ Phase 2 Complete - Ready for Database Integration
**Next Phase**: Database Integration & Real Data Operations
**Deployment Target**: Render (cloud-based, simple deployment)
**User Scale**: MVP 50-100 → Growth 500-1000