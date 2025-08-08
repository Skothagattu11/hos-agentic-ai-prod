# 🚀 HolisticOS MVP - Quick Start Guide

## 📁 Essential Files Only

### **🎯 Main Startup (Use This)**
```bash
python start_openai.py
```
- **OpenAI Direct Integration** - No TensorFlow issues
- **Uses HolisticOS system prompts** 
- **All 6 archetypes supported**
- **Same API interface as original**

### **🔍 Setup Verification (Optional)**
```bash
python test_setup.py
```
- Checks file structure
- Tests Python imports
- Verifies environment variables
- Tests Redis connection

### **🧠 Memory Integration Test (Phase 2)**
```bash
python test_memory_integration.py
```
- Tests Memory Management Agent
- Verifies 4-layer memory system
- Tests Behavior-Memory integration
- Validates event-driven memory operations

### **🏗️ Core Architecture**
```
services/
└── api_gateway/
    └── openai_main.py     # Main API Gateway (OpenAI-based)

shared_libs/
├── utils/
│   └── system_prompts.py  # HolisticOS prompts
└── event_system/
    └── base_agent.py      # Agent framework
```

## 🧪 **Testing Commands**

### **Health Check**
```bash
curl http://localhost:8001/api/health
```

### **Foundation Builder Analysis**
```bash
curl -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_foundation", "archetype": "Foundation Builder"}'
```

### **Peak Performer Analysis** 
```bash
curl -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_peak", "archetype": "Peak Performer"}'
```

### **All Archetypes**
- Foundation Builder
- Peak Performer  
- Systematic Improver
- Transformation Seeker
- Resilience Rebuilder
- Connected Explorer

## 📝 **What Happens**
1. **Server starts** with HolisticOS system prompts loaded
2. **Analysis request** triggers OpenAI GPT-4 with your custom prompts
3. **Complete analysis** includes behavior + nutrition + routine plans
4. **Results logged** to `logs/input_N.txt` and `logs/output_N.txt`
5. **Archetype-specific** approaches for each analysis type

## 🎯 **Next Steps After Testing**
- Phase 2: Add remaining agents (Memory, Insights, Adaptation)
- Phase 3: Deploy to Render
- Production: Real user data integration

## 🆘 **If Issues**
1. Run `python test_setup.py` first
2. Check `.env` file has `OPENAI_API_KEY`
3. Ensure Redis is running (optional for basic testing)