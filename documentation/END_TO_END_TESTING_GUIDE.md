# 🧪 HolisticOS End-to-End Testing Guide

## 📋 Overview

This guide covers testing the **complete multi-agent system** via the enhanced API Gateway. The testing validates all Phase 2 capabilities including Memory Management, Insights Generation, and Strategy Adaptation.

## 🚀 Quick Start

### 1. Start the Enhanced API Server
```bash
cd /mnt/c/dev_skoth/health-agent-main/holisticos-mvp
python services/api_gateway/openai_main.py
```

**Alternative startup:**
```bash
uvicorn services.api_gateway.openai_main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Run End-to-End Tests
```bash
python test_end_to_end_api.py
```

## 🎯 Expected Results

### ✅ **Perfect Success (100%)**
All systems working correctly:
- **System Health**: All 4 agents initialized and healthy
- **Legacy Endpoints**: Phase 1 compatibility maintained  
- **Complete Workflow**: Full multi-agent orchestration working
- **Individual Agents**: Memory, Insights, Adaptation all functional
- **Error Handling**: Proper validation and error responses

### ⚠️ **Mostly Successful (80-99%)**
System functional with minor issues:
- Core workflows working
- Some edge cases may fail
- Check server logs for details

### ❌ **Needs Attention (<80%)**
Significant issues requiring investigation:
- Agent initialization problems
- Workflow coordination failures
- Check environment setup

## 📊 Test Suites Breakdown

### **1. 🏥 System Health (2 tests)**
**What it tests:**
- Root endpoint accessibility and system info
- Health check with agent status monitoring

**Expected Output:**
```
✅ Root endpoint accessible
   Version: 2.0.0
   Mode: Phase 2 - Complete Multi-Agent System
   Agents: ['orchestrator', 'memory', 'insights', 'adaptation']

✅ Health check passed
   System Status: healthy
   Agents Health: 4/4 healthy
   ✅ orchestrator: healthy
   ✅ memory: healthy
   ✅ insights: healthy
   ✅ adaptation: healthy
```

### **2. 🔄 Legacy Endpoints (1 test)**
**What it tests:**
- Phase 1 compatibility maintained
- Original `/api/analyze` endpoint still works

**Expected Output:**
```
✅ Legacy analysis completed
   Status: success
   Analysis components: ['behavior_analysis', 'nutrition_plan', 'routine_plan']
```

### **3. 🚀 Complete Workflow (2 tests)**
**What it tests:**
- Full multi-agent workflow orchestration
- Workflow progress monitoring
- Stage-by-stage progression tracking

**Expected Workflow Stages:**
1. `started` → `memory_storage` → `behavior_analysis`
2. `plan_generation` (nutrition + routine in parallel)
3. `insights_generation` (auto-triggered after both plans)
4. `strategy_adaptation` (auto-triggered after insights)
5. `completed` (workflow finalization)

**Expected Output:**
```
✅ Complete workflow started
   Workflow ID: test_user_1725123456789.0
   Current Stage: behavior_analysis
   Estimated Completion: 5 minutes

📊 Monitoring workflow progress...
   Progress: 20% - Stage: plan_generation
   Progress: 60% - Stage: insights_generation  
   Progress: 80% - Stage: strategy_adaptation
   ✅ Workflow completed successfully!
   Results available: ['behavior_analysis', 'nutrition_plan', 'routine_plan', 'insights', 'adaptation']
```

### **4. 🤖 Individual Agents (3 tests)**
**What it tests:**
- Standalone agent functionality via API
- Memory retrieval, Insights generation, Adaptation triggering

**Expected Outputs:**

**Insights Generation:**
```
✅ Insights generated successfully
   Insights count: 2-5
   Confidence score: 0.70-0.90
   Patterns identified: 1-3
   Recommendations: 3-7
```

**Adaptation Trigger:**
```
✅ Adaptation triggered successfully
   Adaptations made: 1-3
   Confidence: 0.70-0.90
   Expected impact: positive
   Monitoring plan: true
```

**Memory Retrieval:**
```
✅ Memory retrieved successfully
   Memory data keys: ['working', 'shortterm', 'longterm', 'meta']
   Insights: 3-5
```

### **5. 🛡️ Error Handling (3 tests)**
**What it tests:**
- Invalid input validation
- Non-existent resource handling
- Graceful error responses

**Expected behavior:**
- Invalid requests return appropriate HTTP status codes (400, 404, 422)
- Error messages are informative
- System remains stable after errors

## 🔧 Troubleshooting

### **Common Issues & Solutions:**

#### **❌ "Connection failed - is the server running?"**
**Solution:**
```bash
# Start the API server
cd holisticos-mvp
python services/api_gateway/openai_main.py
```

#### **⚠️ "Agent not initialized" errors**
**Causes:**
- Missing dependencies
- Import errors
- Redis connection issues (optional for basic testing)

**Solution:**
```bash
# Check environment
python -c "import sys; print(sys.path)"
python -c "from services.orchestrator.main import HolisticOrchestrator; print('OK')"
```

#### **🐌 Workflow timeout (>2 minutes)**
**Normal for:**
- First run (agents initializing)
- Complex AI analysis with OpenAI API
- Network latency

**Check server logs for details**

#### **⚡ OpenAI API Issues**
**Symptoms:**
- Insights generation fails
- Analysis takes very long
- "OpenAI API key not available" warnings

**Solutions:**
```bash
# Verify OpenAI key
echo $OPENAI_API_KEY

# Check .env file
cat .env | grep OPENAI_API_KEY
```

## 📈 Performance Expectations

### **Timing Benchmarks:**
- **System startup**: 5-15 seconds (first run)
- **Health check**: <1 second
- **Legacy analysis**: 30-90 seconds (with OpenAI)
- **Complete workflow**: 2-8 minutes (depends on OpenAI response times)
- **Individual agents**: 10-60 seconds each

### **Resource Usage:**
- **Memory**: ~200-500MB (all agents loaded)
- **CPU**: Moderate during AI processing
- **Network**: OpenAI API calls for AI analysis

## 🎯 Success Criteria

### **✅ Minimum Viable (80% pass rate):**
- System health checks pass
- At least one complete workflow finishes
- Core agents respond to API calls
- Basic error handling works

### **🎉 Production Ready (95%+ pass rate):**
- All test suites pass
- Workflows complete within 5 minutes
- All agents healthy and responsive
- Comprehensive error handling

### **🚀 Optimal Performance (100% pass rate):**
- All tests pass quickly
- No timeout issues
- Robust error recovery
- Ready for database integration

## 🔄 Next Steps After Testing

### **If Tests Pass (≥95%):**
1. **Database Integration** - Set up PostgreSQL with memory tables
2. **Real Data Integration** - Connect to actual Supabase data
3. **Performance Optimization** - Tune for production load
4. **Deployment Preparation** - Ready for Render deployment

### **If Tests Partially Pass (80-94%):**
1. **Review Failed Tests** - Check server logs
2. **Fix Agent Issues** - Address initialization problems
3. **Retry Testing** - Verify fixes work
4. **Proceed with Caution** - May be ready for database integration

### **If Tests Mostly Fail (<80%):**
1. **Check Environment** - Verify all dependencies
2. **Review Agent Code** - Fix import/initialization issues
3. **Test Individual Components** - Isolate problems
4. **Retry After Fixes** - Re-run tests

## 🆘 Support & Debugging

### **Useful Commands:**
```bash
# Check agent imports
python -c "from services.agents.memory.main import HolisticMemoryAgent; print('Memory OK')"
python -c "from services.agents.insights.main import HolisticInsightsAgent; print('Insights OK')"
python -c "from services.agents.adaptation.main import HolisticAdaptationEngine; print('Adaptation OK')"

# Test individual agents
python services/agents/memory/main.py
python services/agents/insights/main.py  
python services/agents/adaptation/main.py

# Check API server
curl http://localhost:8001/
curl http://localhost:8001/api/health
```

### **Log Locations:**
- **API Server**: Console output where server is running
- **Agent Logs**: Individual agent console outputs
- **Analysis Results**: `logs/input_N.txt` and `logs/output_N.txt`

### **Common Error Patterns:**
- **Import Errors**: Check `sys.path` and relative imports
- **Agent Initialization**: Verify all dependencies available
- **OpenAI Timeout**: Normal for complex analysis - wait longer
- **Redis Connection**: Optional for basic testing

---

**🎯 Goal**: Validate that your complete multi-agent HolisticOS system is working end-to-end via HTTP API and ready for production deployment!