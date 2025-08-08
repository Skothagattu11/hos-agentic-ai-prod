# HolisticOS MVP

A sophisticated multi-agent AI system for personalized health optimization, evolved from the existing health-agent-main system.

## Overview

HolisticOS MVP implements a 6-agent architecture with event-driven communication, hierarchical memory systems, and advanced behavioral analysis capabilities while preserving all existing data flow and functionality from the original health-agent-main system.

## Quick Start

### Prerequisites
- Python 3.11+
- Redis server
- PostgreSQL database
- Render account for deployment

### Local Development
```bash
# Clone and setup
git clone <repository>
cd holisticos-mvp

# Install dependencies
pip install -r requirements.txt

# Start local development server
uvicorn services.api_gateway.main:app --reload
```

### Render Deployment
```bash
# Connect to Render and deploy
git push origin main  # Auto-deploys via render.yaml
```

## Architecture

### Services
- **api-gateway**: FastAPI entry point
- **orchestrator**: Central workflow coordination
- **agents/**: 6 specialized agent services
  - behavior: Behavioral analysis and pattern recognition
  - memory: 4-layer hierarchical memory management
  - nutrition: Personalized nutrition plan generation
  - routine: Exercise routine optimization
  - insights: User-facing insights and recommendations
  - adaptation: Continuous learning and optimization

### Shared Libraries
- **data-models**: Pydantic models and schemas
- **supabase-client**: Data fetching and persistence
- **utils**: Common utilities and helpers
- **event-system**: Inter-agent communication

## Documentation

- [Implementation Plan](./IMPLEMENTATION_PLAN.md) - Complete development strategy
- [Phase 1 Guide](./docs/PHASE1_GUIDE.md) - Detailed first phase implementation
- [API Documentation](./docs/API.md) - Endpoint specifications
- [Agent Specifications](./docs/AGENTS.md) - Individual agent details

## Development Status

- [x] Project structure created
- [x] Implementation plan documented
- [x] **Phase 1: Foundation & Migration (Weeks 1-2) - COMPLETED** ✅
  - [x] HolisticOS system prompts extracted and organized
  - [x] Event-driven agent framework implemented
  - [x] Behavior analysis agent with HolisticOS integration
  - [x] Nutrition plan agent with existing logic preservation
  - [x] Routine plan agent with multi-archetype support
  - [x] Orchestrator workflow coordination
  - [x] API gateway with backward compatibility
  - [x] Comprehensive testing and startup scripts
- [ ] Phase 2: HolisticOS Enhancement (Weeks 3-4)  
- [ ] Phase 3: Testing & Production (Weeks 5-6)

## Running Phase 1 System

### **🚀 Main Startup (Recommended)**
```bash
python start_openai.py
```
*OpenAI Direct Integration - No TensorFlow issues*

### **🔍 Setup Verification**
```bash
python test_setup.py
```
*Verify environment and dependencies*

### **📖 Quick Start Guide**
See [QUICK_START.md](./QUICK_START.md) for detailed testing instructions.

## Contributing

See [Phase 1 Implementation Guide](./docs/PHASE1_GUIDE.md) for detailed development instructions.