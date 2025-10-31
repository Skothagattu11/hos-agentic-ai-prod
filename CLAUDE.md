# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current System Status

**Phase 5.0 - In Progress**: HolisticOS with Friction-Reduction Feedback System and Atomic Habits Integration

### 🚨 SIGNAL: FRICTION_REDUCTION_DEBUGGING

**CURRENT STATUS**: Core friction-reduction logic implemented, debugging data flow to ensure AI receives and acts on friction analysis.

#### Latest Work Session (Phase 5.0 - Debugging Data Flow)

**🔍 Issue Discovered**
- ✅ **Friction Detection Logic**: FeedbackService correctly calculates friction scores
- ✅ **AI Prompt Instructions**: Comprehensive Atomic Habits constraints in place
- ✅ **Motivational Messages**: Task descriptions enhanced with encouragement
- ❌ **Data Flow Gap**: Plans generated with `"feedback_count": 0` despite check-ins existing
- 🔧 **Root Cause**: Friction analysis not reaching AI prompt - need to trace data pipeline

**🛠️ Debug Infrastructure Added (Just Now)**
- ✅ **FeedbackService Debug Logs** (`services/feedback_service.py` lines 255-259)
  - Logs friction categorization: `[FRICTION-DEBUG] Low/Medium/High friction categories`
  - Logs detailed analysis: friction scores, completion rates, satisfaction
- ✅ **TaskPreseeder Debug Logs** (`services/dynamic_personalization/task_preseeder.py` lines 179-184)
  - Logs friction data received from FeedbackService
  - Logs what's being passed to selection_stats
- ✅ **AI Prompt Debug Logs** (`services/api_gateway/openai_main.py` lines 5080-5088)
  - Logs friction data received by AI prompt builder
  - Logs whether high-friction constraints are present in prompt
  - Confirms what high-friction categories are sent to AI

**🎯 Next Steps (Immediate)**
1. Run `python run_feedback_test.py` with new debug logging active
2. Check logs for `[FRICTION-DEBUG]`, `[PRESEED-DEBUG]`, `[AI-PROMPT-DEBUG]` output
3. Identify exact point where friction data is lost or not propagated
4. Fix the broken link in: check-ins → FeedbackService → TaskPreseeder → AI prompt

**📋 Philosophy Established (Implementation In Progress)**
- ❌ **OLD**: "User hates nutrition → Remove nutrition tasks" (exclusion-based)
- ✅ **NEW**: "User struggles with nutrition → Simplify nutrition tasks" (friction-reduction)
- **Goal**: Optimize HOW tasks are delivered (compliance), not WHAT tasks are included (preference)
- **Principle**: Balanced lifestyle requires all health categories - make difficult things easier, not optional

**🧠 Behavioral Science Integration (Atomic Habits)**
- ✅ **Friction Detection**: FeedbackService detects low/medium/high friction categories (not like/dislike)
- ✅ **Adaptation Strategy**: High-friction categories are SIMPLIFIED, not excluded
- ✅ **Atomic Habits Principles**: AI prompt uses 4 laws (Obvious, Easy, Attractive, Satisfying)
- ✅ **Balanced Health**: All essential health categories remain in every plan
- ✅ **Habit Stacking**: Low-friction categories used as anchors for high-friction tasks

**🔄 Feedback Loop Architecture (Under Verification)**
- ✅ **Logic Implemented**: task_checkins → FeedbackService → friction_analysis → AI prompt → simplified tasks
- ⚠️ **Data Flow Issue**: `feedback_count: 0` in generated plans suggests pipeline break
- ✅ **Friction Scoring**: Weighted algorithm (60% experience, 40% continuation)
  - Experience friction: `(5 - rating) / 4.0`
  - Continuation friction: `(no_rate × 0.8) + (maybe_rate × 0.4)`
- ✅ **Strategy Matrix**:
  - Low friction (≤0.3): Leverage as anchors
  - Medium friction (0.3-0.6): Maintain current approach
  - High friction (>0.6): Simplify with micro-habits
- ✅ **User Insights**: Friction-based messaging shows adaptation strategies

#### Previous Accomplishments (Phase 4.5)

**🎯 Dynamic Circadian Integration (Phase 1)**
- ✅ **Circadian Timing**: Dynamic time blocks replace hardcoded schedules (6-8 AM → personalized timing)
- ✅ **Plan Extraction**: Fixed compatibility with new dynamic format
- ✅ **Database Integration**: Tasks and time blocks properly populate plan_items and time_blocks tables
- ✅ **Backward Compatibility**: bio-coach-hub continues working with new implementation

**🤖 AI Extraction Service**
- ✅ **Bulletproof Design**: AI-powered extraction service handles any future format changes
- ✅ **Single API Call**: Optimized from 5 API calls to 1 call (80% cost reduction)
- ✅ **Dual Mode**: Environment-based toggle between regex and AI extraction methods
- ✅ **Future-Proof**: JSON response parsing ready for UI integration

**🏭 Production Infrastructure**
- ✅ **Clean Logging**: Removed all verbose logging (emojis, agent handoffs, raw data) for production
- ✅ **Syntax Resolution**: Fixed all IndentationError issues in openai_main.py
- ✅ **Error Handling**: Comprehensive exception handling with graceful fallbacks
- ✅ **Server Startup**: Successfully starts and fails only at expected point (missing OPENAI_API_KEY)

**📊 Memory System Analysis**
- ✅ **4-Layer Architecture**: Working, Short-term, Long-term, and Meta-memory layers documented
- ✅ **Integration Patterns**: Memory-enhanced analysis workflow and prompt enhancement
- ✅ **Database Schema**: Complete PostgreSQL schema with constraints and indexing
- ✅ **Performance**: Connection pooling and query optimization implemented

### Critical Architecture Decisions

- **No TensorFlow**: Uses OpenAI API directly to avoid compatibility issues
- **50-item threshold**: Analysis triggers only with sufficient new data points
- **Event-driven agents**: All agents inherit from BaseAgent and communicate asynchronously
- **Memory persistence**: PostgreSQL via asyncpg with UPSERT conflict resolution
- **Connection Pooling**: Database pool with 2-8 connections for optimal resource usage
- **Friction-Reduction Philosophy**: SIMPLIFY difficult tasks, never exclude essential health categories
- **Atomic Habits Integration**: Apply behavioral science principles for sustainable habit formation


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
# Runs in ULTRA-QUIET mode on port 8002
python start_openai.py

# Alternative: Run with uvicorn directly
uvicorn services.api_gateway.openai_main:app --host 0.0.0.0 --port 8002 --reload

# Environment validation
python testing/check_env.py

# Core testing suite
python testing/test_ondemand_analysis.py       # Test threshold-based analysis
python testing/test_insight_mvp.py             # Test insights generation
python testing/test_fixes.py                   # Validate production fixes
python testing/test_memory_management.py       # Test 4-layer memory system
python testing/test_user_journey_simple.py     # End-to-end user workflow
python testing/test_rate_limiting.py           # Test rate limiting system
python run_feedback_test.py                    # Test friction-reduction feedback system (Phase 5.0)

# Unit and integration tests
pytest tests/unit/                             # Unit tests
pytest tests/integration/                      # Integration tests
python tests/benchmarks/performance_benchmarks.py  # Performance testing
python tests/load/load_test_suite.py          # Load testing

# Production readiness validation
python testing/run_production_tests.py        # Full production test suite
python testing/validate_fixes.py              # Validate all P0 fixes

# Deployment
git push origin main                           # Auto-deploys via render.yaml
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
User Request → API Gateway → On-Demand Analysis → Threshold Check
                                                      ↓
                                                 Agent Workflow
                                                      ↓
                            Orchestrator → Agents (parallel/sequential)
                                   ↓              ↓
                            Memory Update → Insights Generation
                                   ↓              ↓
                            Database Pool → Response Cache
                                   ↓              ↓
                                Response to User
```

### Critical System Architecture Patterns

**50-Item Threshold System**: Analysis only triggers when sufficient new data points exist, preventing unnecessary API calls and ensuring meaningful insights.

**4-Layer Memory Hierarchy**:
- **Working Memory**: Current session context and immediate decisions
- **Episodic Memory**: Specific user experiences and historical events  
- **Semantic Memory**: General knowledge and learned patterns
- **Procedural Memory**: Skills, habits, and routine optimizations

**Event-Driven Agent System**: All agents inherit from `BaseAgent` in `shared_libs/event_system/base_agent.py` with standardized async event handling.

**Connection Pooling**: Database pool with 2-8 connections optimized for Render's 0.5 CPU instances, preventing connection exhaustion.

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
- **Error Handling**: Comprehensive exception hierarchy in `shared_libs/exceptions/holisticos_exceptions.py`
- **Retry Logic**: Exponential backoff patterns with circuit breaker protection
- **Rate Limiting**: Redis-based with tier controls (5/hour free, 20/hour premium)
- **Cost Protection**: Automatic limits ($1/day free, $10/day premium)
- **Monitoring**: Prometheus metrics, health checks, and alerting system
- **Ultra-Quiet Mode**: `start_openai.py` runs with minimal output (errors only)

## Environment Variables

Required environment variables (in `.env` file):

```env
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration (REQUIRED)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# Database Configuration
# Uses Supabase PostgreSQL - same credentials as above
DATABASE_URL=postgresql://postgres:password@db.supabase_project.supabase.co:5432/postgres

# Environment Configuration (CRITICAL - Controls behavior)
# Options: development, staging, production
ENVIRONMENT=development

# API Configuration
API_HOST=0.0.0.0
API_PORT=8002

# Logging Configuration
LOG_LEVEL=ERROR

# Rate Limiting Configuration
RATE_LIMIT_FREE_TIER=5
RATE_LIMIT_COST_DAILY=1.00

# Timeout Configuration
OPENAI_REQUEST_TIMEOUT=30
DATABASE_QUERY_TIMEOUT=30
BEHAVIOR_ANALYSIS_TIMEOUT=120

# Email Alerting Configuration (Optional for production monitoring)
EMAIL_API_KEY=your_resend_api_key
EMAIL_PROVIDER=resend
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_RECIPIENTS=admin@yourdomain.com

# Redis Configuration (Optional - for production scaling)
REDIS_URL=redis://localhost:6379

# Render Deployment Configuration (when deploying to Render)
PORT=8000
RENDER=true
```


## API Endpoints

### Core Health Analysis
```
POST /api/user/{user_id}/behavior/analyze   # Threshold-based behavior analysis
POST /api/user/{user_id}/routine/generate   # Routine planning with behavior context
POST /api/user/{user_id}/nutrition/generate # Nutrition planning with behavior context
POST /api/analyze                           # Legacy archetype-based analysis
```

### System Monitoring & Health
```
GET  /api/health                           # Basic system health check
GET  /api/health/detailed                  # Comprehensive health status
GET  /api/scheduler/status                 # On-demand analysis system status
GET  /api/metrics                          # Prometheus metrics endpoint
```

### Administrative & Debug
```
GET  /api/admin/rate-limits                # Rate limiting status and usage
GET  /api/admin/cost-tracking              # Cost monitoring dashboard
POST /api/admin/insights/trigger           # Manual insights generation
GET  /api/debug/memory-stats               # Memory system diagnostics
```

### Health Data Integration
```
GET  /api/health-data/{user_id}            # User health data retrieval
POST /api/health-data/{user_id}/sync       # Trigger data synchronization
GET  /api/insights/{user_id}               # User-specific insights
```


## Troubleshooting

### Common Issues & Solutions

**Server won't start**: Run `python testing/check_env.py` to validate environment setup and dependencies

**Threshold not triggering**: Check OnDemandAnalysisService debug logs for race conditions in timestamps

**Database connection errors**: Verify PostgreSQL URL and check connection pool status at `/api/health/detailed`

**Rate limiting issues**: Check Redis connection and rate limit status at `/api/admin/rate-limits`

**Memory errors**: Monitor memory system health with `python testing/test_memory_management.py`

**Duplicate constraint errors**: Verify holistic_analysis_results table constraint columns match check query

**Analysis failing**: Validate OpenAI API key and check cost limits at `/api/admin/cost-tracking`

**Insights not generating**: Ensure 'holistic_insights' is in SupabaseAsyncPGAdapter table list

**Performance issues**: Run load tests with `python tests/load/load_test_suite.py`

### Development Workflow

1. **Environment Setup**: Ensure `.env` file exists with all required variables (see Environment Variables section)
2. **Dependency Check**: Run `pip install -r requirements.txt` 
3. **System Validation**: Execute `python testing/check_env.py` to verify OpenAI API key and database connectivity
4. **Start Development**: Use `python start_openai.py` for ultra-quiet mode (errors only) on port 8002
5. **Test Changes**: Run relevant test scripts in `testing/` directory before committing changes
6. **Production Readiness**: Execute `python testing/validate_fixes.py` to ensure all P0 fixes are working
7. **Deployment**: Push to main branch - auto-deploys via render.yaml

---

## Core Infrastructure Completion Status

### 🚨 SIGNAL: ALL_P0_FIXES_COMPLETE

**Core Stability Agent (Foundation)** - ✅ **COMPLETED**

All critical P0 production fixes have been implemented and tested:

1. **✅ Error Handling & Retry Logic** - Complete
   - Custom exception hierarchy in `shared_libs/exceptions/holisticos_exceptions.py`
   - Retry decorators with exponential backoff patterns
   - Circuit breaker patterns for service resilience
   - Comprehensive error scenarios tested and documented

2. **✅ Database Connection Pooling** - Complete
   - DatabasePool singleton in `shared_libs/database/connection_pool.py`
   - SupabaseAsyncPGAdapter updated with connection pooling
   - Proper startup/shutdown hooks for pool management
   - Load tested with 10+ concurrent connections

3. **✅ Request Timeouts** - Complete
   - Comprehensive timeout configuration system in `config/timeout_config.py`
   - OpenAI client updated with proper timeout handling
   - Service-level timeout decorators implemented
   - All timeout scenarios tested and working

4. **✅ Rate Limiting** - Complete
   - Redis-based rate limiting in `shared_libs/rate_limiting/rate_limiter.py`
   - Cost tracking mechanisms with tier-based limits
   - Free tier: 5 analyses/hour, Premium: 20 analyses/hour
   - Cost control: max $1/day (free), $10/day (premium)
   - Integration with existing timeout and error handling systems
   - Admin monitoring endpoints: `/api/admin/rate-limits`

### 🎯 Production Ready Infrastructure

The HolisticOS system now has enterprise-grade stability:

- **Cost Protection**: Automatic cost limits prevent budget overruns
- **Service Resilience**: Circuit breakers and retry logic handle failures gracefully  
- **Resource Management**: Connection pooling and timeouts prevent resource exhaustion
- **Rate Protection**: Tier-based rate limiting prevents abuse and ensures fair usage
- **Monitoring**: Comprehensive admin dashboards for cost and usage tracking

**Status**: Foundation infrastructure complete. Other agents can now proceed with full confidence in system stability.

**Testing**: All components tested independently and under load conditions.

---

## Friction-Reduction Feedback System (Phase 5.0)

### Overview

The friction-reduction system applies behavioral science principles from "Atomic Habits" to personalize health plans based on user feedback. Instead of removing difficult categories, the system simplifies them using micro-habits and habit stacking.

### Core Components

#### 1. FeedbackService (`services/feedback_service.py`)

**Purpose**: Analyzes user check-in feedback to detect friction patterns

**Key Method**: `_aggregate_feedback()`
- **Input**: List of task check-ins with continue_preference, enjoyed, satisfaction_rating
- **Output**: Friction analysis with categories grouped by friction level

**Friction Scoring Algorithm**:
```python
friction_score = (rejection_rate × 0.4) + (unenjoyment_rate × 0.3) + (dissatisfaction_rate × 0.3)
```

**Friction Categorization**:
- **Low friction (≤0.3)**: User excels → Use as anchor for habit stacking
- **Medium friction (0.3-0.6)**: Manageable → Maintain current approach
- **High friction (>0.6)**: User struggles → Simplify with micro-habits

**Output Format**:
```python
{
    'low_friction_categories': ['movement', 'hydration'],
    'high_friction_categories': ['nutrition', 'stress_management'],
    'friction_analysis': {
        'nutrition': {
            'friction_score': 0.75,
            'strategy': 'simplify_approach',
            'completion_rate': 0.25,
            'enjoyment_rate': 0.20,
            'avg_satisfaction': 2.1
        }
    }
}
```

#### 2. AI Prompt Integration (`services/api_gateway/openai_main.py`)

**Location**: Lines 4876-4987 (routine generation prompt)

**Integration Point**: Feedback constraints section in AI prompt

**Atomic Habits 4 Laws Applied**:

1. **Make it Obvious (Cue)**
   - Example: "Place protein shake ingredients on counter night before"
   - Links tasks to environmental cues

2. **Make it Easy (Reduce Friction)**
   - Example: "Track macros" → "Take photo of 3 meals"
   - Reduces time: 30min → 5min
   - Uses micro-habits: "Drink water" → "Take one sip when phone buzzes"

3. **Make it Attractive (Temptation Bundling)**
   - Example: "Protein shake after workout" (links to low-friction exercise)
   - Pairs difficult tasks with enjoyable activities

4. **Make it Satisfying (Immediate Gratification)**
   - Example: "Check off each meal logged"
   - Progress visualization: "3-day streak of vegetable servings"

**Critical Constraint**:
```
⚠️ CRITICAL: DO NOT exclude high-friction categories - they're essential for balanced health!
```

#### 3. InsightsService (`services/insights_service.py`)

**Purpose**: Generate user-facing insights that reflect adaptation strategies

**Key Method**: `_extract_feedback_insight()`

**Insight Examples**:
- High friction: "Simplified nutrition tasks to reduce friction - focus on micro-habits to build momentum"
- Low friction: "Leveraging your movement success - using habit stacking to strengthen other areas"
- Balanced: "Plan optimized from 7 days of feedback - adapting difficulty, not content"

#### 4. Testing Infrastructure (`testing/test_feedback_interactive.py`)

**Purpose**: Validate friction-reduction system end-to-end

**Test Flow**:
1. Generate Plan 1 (cold start) OR use existing plan
2. Create positive feedback (movement/hydration = low friction)
3. Generate Plan 2 (should leverage low-friction categories)
4. Create high-friction feedback (nutrition/stress = high friction)
5. Generate Plan 3 (should SIMPLIFY high-friction, not exclude)
6. Compare plans to validate all categories present

**Success Criteria**:
- ✅ All health categories present in all plans
- ✅ High-friction categories have simplified tasks (micro-habits)
- ✅ Low-friction categories used as anchors
- ✅ Insights mention friction-reduction strategies

**Run Test**:
```bash
python run_feedback_test.py
```

### Database Schema

**Tables Used**:

1. **task_checkins**: User feedback on completed tasks
   - `continue_preference`: 'yes', 'no', 'maybe'
   - `enjoyed`: boolean
   - `satisfaction_rating`: 1-5 scale
   - `timing_feedback`: 'early', 'perfect', 'late'

2. **plan_items**: Generated tasks from plans
   - `category`: Task category (nutrition, movement, etc.)
   - `title`: Task description
   - `scheduled_time`: When task is scheduled

3. **holistic_analysis_results**: Plan metadata
   - `analysis_id`: Unique plan identifier
   - `archetype`: User archetype
   - `created_at`: Plan generation timestamp

### Key Design Decisions

#### Why Friction-Reduction Instead of Exclusion?

**Problem with Exclusion**:
- User hates nutrition → Remove nutrition → Unbalanced health
- Short-term preference optimization → Long-term health degradation
- User never builds essential habits

**Solution with Friction-Reduction**:
- User struggles with nutrition → Simplify nutrition tasks
- Maintain balanced health categories
- Build sustainable habits through small wins
- Use successful areas to motivate difficult areas

#### Atomic Habits Alignment

**Core Principle**: Make habits easy to start, hard to stop

**Implementation**:
- **2-minute rule**: High-friction tasks become 1-2 minute micro-habits
- **Habit stacking**: Link new habits to established routines
- **Identity-based**: "I'm someone who eats vegetables" vs "I need to diet"
- **Environmental design**: Make cues visible, friction invisible

### Testing & Validation

**Manual Testing**:
```bash
python run_feedback_test.py
```

**Validation Checklist**:
- [ ] FeedbackService detects friction correctly
- [ ] AI prompt receives friction analysis
- [ ] High-friction tasks are simplified (not excluded)
- [ ] Low-friction tasks used as anchors
- [ ] All health categories present in Plan 3
- [ ] Insights mention adaptation strategies

**Expected Results**:
```
Plan 1 (Cold Start): 3 nutrition tasks (normal difficulty)
Plan 2 (After positive feedback): 3 nutrition tasks (normal difficulty)
Plan 3 (After high friction): 2-3 nutrition tasks (SIMPLIFIED - micro-habits)
```

### Troubleshooting

**Issue**: High-friction categories missing from Plan 3
- **Cause**: AI prompt excluding instead of simplifying
- **Fix**: Verify feedback constraints in openai_main.py lines 4876-4987

**Issue**: Friction scores always 0
- **Cause**: No check-in data or wrong date range
- **Fix**: Verify task_checkins table has data within last 7 days

**Issue**: Insights show exclusion messaging
- **Cause**: Old insights logic still active
- **Fix**: Verify InsightsService._extract_feedback_insight() updated

### Quick Reference: Files Modified in Phase 5.0

| File | Purpose | Key Changes |
|------|---------|-------------|
| `services/feedback_service.py` | Feedback analysis | Changed `_aggregate_feedback()` to detect friction levels instead of like/dislike |
| `services/api_gateway/openai_main.py` | AI prompt | Lines 4876-4987: Added Atomic Habits 4 laws, friction-reduction constraints |
| `services/insights_service.py` | User insights | Updated `_extract_feedback_insight()` with friction-based messaging |
| `testing/test_feedback_interactive.py` | Validation test | Updated expectations to validate simplification (not exclusion) |
| `CLAUDE.md` | Documentation | Added Phase 5.0 documentation |

### Implementation Summary (What We Did Today)

**Problem Identified**:
- System was excluding categories users disliked (nutrition, stress_management)
- Plans became imbalanced (only easy, enjoyable tasks)
- Users never built essential habits

**Solution Implemented**:
- Rewrote FeedbackService to detect friction patterns (not preferences)
- Updated AI prompt to use Atomic Habits principles
- Changed InsightsService to show adaptation strategies
- Updated test to validate all categories remain present

**Key Insight**:
> "For a balanced lifestyle, everything has to be done. Our motive with feedback is to make sure user follows the full plan efficiently, not to give more of what they liked."

**Philosophy**:
- OLD: Optimize WHAT tasks (preference-based)
- NEW: Optimize HOW tasks are delivered (compliance-based)

### Latest Debugging Session (October 30, 2025)

**Issue Found**: Plans generated with `feedback_count: 0` despite check-ins existing in database.

**Debug Logging Added**:

1. **FeedbackService** (`services/feedback_service.py:255-259`)
   ```
   [FRICTION-DEBUG] Low friction categories (≤0.3): ['hydration', 'movement']
   [FRICTION-DEBUG] Medium friction categories (0.3-0.6): []
   [FRICTION-DEBUG] High friction categories (>0.6): ['nutrition', 'stress_management']
   [FRICTION-DEBUG] Detailed analysis: {friction_score, completion_rate, etc.}
   ```

2. **TaskPreseeder** (`services/dynamic_personalization/task_preseeder.py:179-184`)
   ```
   [PRESEED-DEBUG] Friction data received from FeedbackService:
   [PRESEED-DEBUG]   Low friction: ['hydration', 'movement']
   [PRESEED-DEBUG]   Medium friction: []
   [PRESEED-DEBUG]   High friction: ['nutrition', 'stress_management']
   [PRESEED-DEBUG]   Friction analysis: {...}
   ```

3. **AI Prompt Builder** (`services/api_gateway/openai_main.py:5080-5088`)
   ```
   [AI-PROMPT-DEBUG] Friction data received from TaskPreseeder:
   [AI-PROMPT-DEBUG]   Low friction: ['hydration', 'movement']
   [AI-PROMPT-DEBUG]   High friction: ['nutrition', 'stress_management']
   [AI-PROMPT-DEBUG]   Friction analysis: {...}
   [AI-PROMPT-DEBUG]   Feedback count: 11
   [AI-PROMPT-DEBUG]   🚨 HIGH-FRICTION CATEGORIES SENT TO AI: ['nutrition', 'stress_management']
   [AI-PROMPT-DEBUG]   🚨 AI INSTRUCTION: SIMPLIFY (not exclude) these categories
   ```

**Expected Data Flow**:
```
task_checkins (11 rows)
    ↓
FeedbackService.get_latest_checkin_feedback()
    ↓ [FRICTION-DEBUG logs here]
friction_analysis = {nutrition: {friction_score: 0.93, ...}}
    ↓
TaskPreseeder.preseed_library_tasks()
    ↓ [PRESEED-DEBUG logs here]
selection_stats = {high_friction_categories: ['nutrition'], ...}
    ↓
openai_main.py - routine generation
    ↓ [AI-PROMPT-DEBUG logs here]
AI prompt with "SIMPLIFY nutrition (never exclude!)"
    ↓
Generated plan with simplified nutrition tasks
```

**How to Verify Fix**:
```bash
cd /Users/kothagattu/Desktop/OG/hos-agentic-ai-prod
python run_feedback_test.py

# Then check logs for debug output
grep -E "\[FRICTION-DEBUG\]|\[PRESEED-DEBUG\]|\[AI-PROMPT-DEBUG\]" logs/server_*.log | tail -50
```

**Success Criteria**:
- All 3 debug log groups appear in sequence
- `feedback_count > 0` in generated plans
- High-friction categories present in Plan 3 with SIMPLIFIED tasks (not excluded)
- Task descriptions show micro-habits: "Just take a photo" instead of "Track comprehensive macros"

---