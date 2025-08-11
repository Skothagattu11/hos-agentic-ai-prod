# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

### Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Running the System

```bash
# Main startup - OpenAI Direct Integration (RECOMMENDED)
python start_openai.py

# Alternative: Run with uvicorn directly
uvicorn services.api_gateway.openai_main:app --host 0.0.0.0 --port 8001 --reload

# Verify environment setup
python test_setup.py
```

### Testing

```bash
# End-to-end API testing
python test_end_to_end_api.py

# Test orchestrator with multiple agents
python test_multi_agent_orchestrator.py

# Test memory integration
python test_memory_integration.py

# Test adaptation engine
python test_adaptation_engine.py

# Test insights agent
python test_insights_agent.py

# Unit tests
pytest tests/unit/

# Integration tests (when available)
pytest tests/integration/
```

### API Testing Examples

```bash
# Health check
curl http://localhost:8001/api/health

# Analyze with specific archetype
curl -X POST http://localhost:8001/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{"user_id": "test_user", "archetype": "Foundation Builder"}'
```

## High-Level Architecture

### Service Organization

```
services/
├── api_gateway/          # FastAPI entry point
│   └── openai_main.py   # OpenAI-based implementation (no TensorFlow)
├── orchestrator/         # Central workflow coordination
│   └── main.py          # Manages agent interactions and data flow
└── agents/              # Specialized agent services
    ├── behavior/        # Behavioral analysis and pattern recognition
    ├── memory/          # 4-layer hierarchical memory management
    ├── nutrition/       # Personalized nutrition planning
    ├── routine/         # Exercise routine optimization
    ├── insights/        # User insights and recommendations
    └── adaptation/      # Continuous learning and optimization
```

### Shared Libraries

```
shared_libs/
├── data_models/         # Pydantic models for type safety
│   └── base_models.py  # Core data structures
├── event_system/        # Inter-agent communication
│   └── base_agent.py   # Base agent class with event handling
├── supabase_client/     # Data fetching and persistence
│   └── adapter.py      # Supabase integration layer
└── utils/              
    └── system_prompts.py  # HolisticOS agent prompts
```

### Data Flow Architecture

1. **API Gateway** receives user request with archetype
2. **Orchestrator** coordinates workflow:
   - Fetches user data via Supabase adapter
   - Triggers behavioral analysis
   - Updates memory systems
   - Generates personalized plans
   - Creates insights and recommendations
3. **Agents** communicate via event-driven patterns
4. **Results** stream back via Server-Sent Events (SSE)

### Memory System Architecture

The Memory Management Agent implements a 4-layer hierarchical system:
1. **Working Memory**: Immediate context and active processing
2. **Episodic Memory**: Recent interactions and experiences
3. **Semantic Memory**: Learned patterns and knowledge
4. **Procedural Memory**: Established routines and skills

## Key Patterns and Conventions

### Agent Communication
- All agents inherit from `BaseAgent` class
- Event-driven communication using async patterns
- Structured event types for different agent interactions

### Data Models
- All data models use Pydantic for validation
- Models organized by domain (user, behavior, memory, plans)
- Strict type checking and validation rules

### System Prompts
- Each agent has a specialized system prompt from HolisticOS specs
- Prompts stored in `shared_libs/utils/system_prompts.py`
- Prompts include role definition, expertise domains, and operational principles

### Error Handling
- Comprehensive error handling at each layer
- Graceful degradation when agents fail
- Detailed logging for debugging

### Archetype Support
The system supports 6 distinct user archetypes:
1. **Foundation Builder** - Simple, sustainable basics
2. **Transformation Seeker** - Ambitious lifestyle changes
3. **Systematic Improver** - Methodical, evidence-based progress
4. **Peak Performer** - Elite-level performance optimization
5. **Resilience Rebuilder** - Recovery and restoration focus
6. **Connected Explorer** - Social and adventure-oriented wellness

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

## Common Development Tasks

### Adding a New Agent
1. Create agent directory in `services/agents/`
2. Implement agent logic inheriting from `BaseAgent`
3. Add system prompt in `system_prompts.py`
4. Register agent in orchestrator workflow
5. Add corresponding data models
6. Write unit tests

### Modifying Agent Behavior
1. System prompts are in `shared_libs/utils/system_prompts.py`
2. Agent logic is in respective `services/agents/*/main.py`
3. Data models are in `shared_libs/data_models/`

### Debugging
- Logs are written to `logs/` directory (input_*.txt, output_*.txt)
- Use `structlog` for structured logging
- Enable debug mode in environment variables

## Performance Considerations

### OpenAI Integration
- Uses direct OpenAI API to avoid TensorFlow compatibility issues
- Implements retry logic with exponential backoff
- Caches responses where appropriate

### Async Processing
- All agents use async/await for non-blocking operations
- Database queries are async via asyncpg
- Event processing is asynchronous

### Scaling
- Agents can be deployed as separate services
- Redis used for caching and message queuing
- Horizontal scaling supported via load balancing

## Testing Strategy

### Unit Tests
- Test individual agent logic
- Mock external dependencies
- Focus on business logic validation

### Integration Tests
- Test agent interactions
- Verify event flow
- Validate data persistence

### End-to-End Tests
- Test complete workflows
- Verify API responses
- Check system behavior with different archetypes

## Deployment

### Local Development
```bash
python start_openai.py
```

### Production (Render)
- Configuration in `render.yaml`
- Auto-deploy on push to main branch
- Environment variables configured in Render dashboard

## Important Notes

1. **OpenAI vs TensorFlow**: The system uses OpenAI API directly (`start_openai.py`) to avoid TensorFlow compatibility issues while maintaining HolisticOS agent intelligence

2. **Memory Persistence**: The memory system requires PostgreSQL for persistence. Ensure database is properly configured

3. **Archetype-Specific Logic**: Each agent adapts its behavior based on user archetype - this is core to the personalization strategy

4. **Event-Driven Architecture**: Agents communicate asynchronously - ensure proper event handling when modifying agent interactions

5. **System Prompts**: The intelligence of each agent comes from carefully crafted system prompts based on HolisticOS specifications - modify with care

## Resources

- [HolisticOS System Architecture](docs/system_docs/HolisticOS_System_Architecture.pdf)
- [Agent Specifications](docs/system_docs/HolisticOS_Agent_Specifications.pdf)
- [Memory Systems Framework](docs/system_docs/HolisticOS_Memory_Systems_Framework.pdf)
- [Implementation Plan](IMPLEMENTATION_PLAN.md)
- [Quick Start Guide](QUICK_START.md)