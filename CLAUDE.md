# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current System Status

**Phase 4.3 Complete**: HolisticOS with intelligent threshold system and comprehensive insights.

### Critical Architecture Decisions

- **No TensorFlow**: Uses OpenAI API directly to avoid compatibility issues
- **50-item threshold**: Analysis triggers only with sufficient new data points
- **Event-driven agents**: All agents inherit from BaseAgent and communicate asynchronously
- **Memory persistence**: PostgreSQL via asyncpg with UPSERT conflict resolution


## Project Overview

HolisticOS MVP is a sophisticated multi-agent AI system for personalized health optimization. It implements a 6-agent architecture with event-driven communication, hierarchical memory systems, and advanced behavioral analysis capabilities.

### System Architecture

The system consists of six specialized AI agents working in concert:
- **Orchestrator Agent**: Central coordination hub for all system operations
- **Behavior Analysis Agent**: User behavior pattern recognition and psychological assessment
- **Memory Management Agent**: Long-term learning and knowledge repository with 4-layer hierarchy
- **Plan Generation Agent (Routine/Nutrition)**: Personalized daily routines and nutrition plans
- **Adaptation Engine Agent**: Real-time monitoring and adaptive modification
- **Insights & Recommendations Agent**: User-facing intelligence and motivational content

### Core Technologies
- **Framework**: FastAPI with async/await patterns
- **AI Integration**: OpenAI GPT-4 via direct API (avoids TensorFlow compatibility issues)
- **Data Models**: Pydantic for type safety and validation
- **Event System**: Event-driven architecture for inter-agent communication
- **Database**: PostgreSQL (via asyncpg) for memory persistence, Supabase for data fetching
- **Caching**: Redis for performance optimization

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Main startup (RECOMMENDED - uses OpenAI API directly)
python start_openai.py

# Alternative: Run with uvicorn directly
uvicorn services.api_gateway.openai_main:app --host 0.0.0.0 --port 8001 --reload

# Testing
python test_ondemand_analysis.py     # Test on-demand analysis service
python test_insight_mvp.py           # Test insights generation
python test_fixes.py                 # Validate recent fixes
pytest tests/unit/                   # Run unit tests
```

## High-Level Architecture

### Core Services

1. **API Gateway** (`services/api_gateway/openai_main.py`)
   - FastAPI entry point using OpenAI API directly
   - Includes health data and insights routers
   - Handles authentication and request routing

2. **On-Demand Analysis** (`services/ondemand_analysis_service.py`)
   - Intelligent threshold-based analysis decisions
   - Tracks data points and determines when to refresh
   - Manages cache staleness and memory quality

3. **Memory System** (`services/agents/memory/`)
   - 4-layer hierarchy: Working, Episodic, Semantic, Procedural
   - PostgreSQL persistence via asyncpg
   - Conflict resolution with UPSERT operations

4. **Insights System** (`services/insights_extraction_service.py`)
   - Auto-extracts insights with deduplication
   - Stores insights in Supabase
   - Provides user-facing recommendations

### Agent Communication Flow

All agents inherit from `BaseAgent` and use async event-driven patterns:

```
User Request → API Gateway → Orchestrator → Agents (parallel/sequential)
                                           ↓
                                     Memory Update
                                           ↓
                                     Insights Generation
                                           ↓
                                     Response to User
```

## Key Patterns and Conventions

### Archetype Support
The system supports 6 distinct user archetypes:
1. **Foundation Builder** - Simple, sustainable basics
2. **Transformation Seeker** - Ambitious lifestyle changes
3. **Systematic Improver** - Methodical, evidence-based progress
4. **Peak Performer** - Elite-level performance optimization
5. **Resilience Rebuilder** - Recovery and restoration focus
6. **Connected Explorer** - Social and adventure-oriented wellness

### Important Implementation Details

- **Agent Communication**: All agents inherit from `BaseAgent` and use async event-driven patterns
- **System Prompts**: Stored in `shared_libs/utils/system_prompts.py` with HolisticOS specifications
- **Data Models**: Pydantic models in `shared_libs/data_models/` with strict validation
- **Error Handling**: Graceful degradation when agents fail, detailed logging throughout

## Environment Variables

Required environment variables (in `.env` file):

```env
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/holisticos
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Redis Configuration (for production)
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
ENVIRONMENT=development
```


## API Endpoints

```
POST /api/user/{user_id}/behavior/analyze   # Standalone with 50-item threshold
POST /api/user/{user_id}/routine/generate   # Calls behavior endpoint internally  
POST /api/user/{user_id}/nutrition/generate # Calls behavior endpoint internally
POST /api/analyze                           # Legacy endpoint (archetype-based)
GET  /api/scheduler/status                  # On-demand system status
GET  /api/health                           # System health check
```


## Troubleshooting

**Threshold not triggering**: Check OnDemandAnalysisService debug logs for race conditions in timestamps

**Duplicate constraint errors**: Verify holistic_analysis_results table constraint columns match check query

**Insights not generating**: Ensure 'holistic_insights' is in SupabaseAsyncPGAdapter table list

**Analysis mode inconsistency**: Verify ondemand_metadata passes through MemoryIntegrationService

**HTTP 500 on endpoints**: Check that functions `run_routine_planning_4o` and `run_nutrition_planning_4o` exist in openai_main.py