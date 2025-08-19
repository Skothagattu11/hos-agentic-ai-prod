# P2: Testing & Documentation

## Why This Issue Exists

### Current Problem
- No load testing to validate performance under production conditions
- Missing deployment runbook for consistent releases
- No incident response playbook for when things go wrong
- Limited production testing procedures
- Knowledge silos without documentation

### Evidence of Testing Gaps
```python
# Current: Basic unit tests only
test_scripts/test_user_journey_simple.py  # Single user simulation
test_end_to_end_api.py                    # Basic API testing

# Missing: Production-grade testing
- Load testing under concurrent users
- Performance benchmarks for 0.5 CPU instance
- Failover and recovery testing
- Cost validation under load
```

### Impact on Production Readiness
- **Unknown Limits**: Don't know system capacity
- **Deployment Risk**: No standardized release process
- **Slow Recovery**: No incident response procedures
- **Performance Uncertainty**: No baseline metrics for optimization

### Real-World Scenarios
```
Scenario 1: Launch Day Traffic Spike
No load testing → System crashes → Manual recovery → User churn

Scenario 2: Production Issue
No runbook → Panic deployment → More issues → Extended downtime

Scenario 3: Performance Degradation  
No benchmarks → Unknown if issue or normal → Investigation delays
```

## How to Fix

### Implementation Strategy

#### 1. Comprehensive Load Testing Suite
```python
# tests/load/load_test_suite.py
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
import json

@dataclass
class LoadTestResult:
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    p95_response_time: float
    p99_response_time: float
    errors: List[str]
    throughput_rps: float

class HolisticOSLoadTester:
    """Comprehensive load testing for HolisticOS MVP"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.results = []
    
    async def simulate_user_journey(self, user_id: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Simulate complete user journey"""
        start_time = time.time()
        journey_results = {"user_id": user_id, "steps": []}
        
        # Step 1: Health check
        step_result = await self._make_request(
            session, "GET", "/api/health", expected_status=200
        )
        journey_results["steps"].append({"step": "health_check", **step_result})
        
        # Step 2: Routine generation
        routine_payload = {
            "archetype": "Foundation Builder",
            "preferences": {"focus_areas": ["strength", "cardio"]}
        }
        step_result = await self._make_request(
            session, "POST", f"/api/user/{user_id}/routine/generate",
            payload=routine_payload, expected_status=200
        )
        journey_results["steps"].append({"step": "routine_generation", **step_result})
        
        # Step 3: Nutrition generation
        nutrition_payload = {
            "archetype": "Foundation Builder",
            "dietary_preferences": ["vegetarian"]
        }
        step_result = await self._make_request(
            session, "POST", f"/api/user/{user_id}/nutrition/generate",
            payload=nutrition_payload, expected_status=200
        )
        journey_results["steps"].append({"step": "nutrition_generation", **step_result})
        
        # Step 4: Insights generation
        step_result = await self._make_request(
            session, "POST", f"/api/user/{user_id}/insights/generate",
            payload={}, expected_status=200
        )
        journey_results["steps"].append({"step": "insights_generation", **step_result})
        
        journey_results["total_duration"] = time.time() - start_time
        return journey_results
    
    async def _make_request(self, session: aiohttp.ClientSession, method: str, 
                          endpoint: str, payload: dict = None, expected_status: int = 200) -> Dict:
        """Make HTTP request and measure performance"""
        start_time = time.time()
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                async with session.get(url) as response:
                    duration = time.time() - start_time
                    content = await response.text()
                    return {
                        "success": response.status == expected_status,
                        "status_code": response.status,
                        "duration_ms": duration * 1000,
                        "response_size": len(content),
                        "error": None if response.status == expected_status else content
                    }
            else:
                async with session.post(url, json=payload) as response:
                    duration = time.time() - start_time
                    content = await response.text()
                    return {
                        "success": response.status == expected_status,
                        "status_code": response.status,
                        "duration_ms": duration * 1000,
                        "response_size": len(content),
                        "error": None if response.status == expected_status else content
                    }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "duration_ms": (time.time() - start_time) * 1000,
                "response_size": 0,
                "error": str(e)
            }
    
    async def run_concurrent_user_test(self, concurrent_users: int = 10, 
                                     test_duration_minutes: int = 5) -> Dict[str, Any]:
        """Test with concurrent users over time"""
        print(f"🚀 Starting load test: {concurrent_users} concurrent users for {test_duration_minutes} minutes")
        
        start_time = time.time()
        end_time = start_time + (test_duration_minutes * 60)
        
        user_results = []
        
        async with aiohttp.ClientSession() as session:
            while time.time() < end_time:
                # Create batch of concurrent users
                tasks = []
                for i in range(concurrent_users):
                    user_id = f"load_test_user_{int(time.time())}_{i}"
                    tasks.append(self.simulate_user_journey(user_id, session))
                
                # Execute batch
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        user_results.append({"error": str(result)})
                    else:
                        user_results.append(result)
                
                # Brief pause between batches
                await asyncio.sleep(2)
        
        return self._analyze_load_test_results(user_results, concurrent_users, test_duration_minutes)
    
    def _analyze_load_test_results(self, user_results: List[Dict], 
                                 concurrent_users: int, duration_minutes: int) -> Dict[str, Any]:
        """Analyze load test results"""
        total_users = len(user_results)
        successful_journeys = len([r for r in user_results if "error" not in r])
        failed_journeys = total_users - successful_journeys
        
        # Analyze response times by step
        step_analysis = {}
        for result in user_results:
            if "steps" in result:
                for step in result["steps"]:
                    step_name = step["step"]
                    if step_name not in step_analysis:
                        step_analysis[step_name] = []
                    step_analysis[step_name].append(step["duration_ms"])
        
        # Calculate percentiles for each step
        step_stats = {}
        for step_name, durations in step_analysis.items():
            if durations:
                step_stats[step_name] = {
                    "avg_ms": statistics.mean(durations),
                    "p95_ms": statistics.quantiles(durations, n=20)[18],  # 95th percentile
                    "p99_ms": statistics.quantiles(durations, n=100)[98], # 99th percentile
                    "min_ms": min(durations),
                    "max_ms": max(durations)
                }
        
        return {
            "test_config": {
                "concurrent_users": concurrent_users,
                "duration_minutes": duration_minutes,
                "total_user_journeys": total_users
            },
            "overall_results": {
                "successful_journeys": successful_journeys,
                "failed_journeys": failed_journeys,
                "success_rate": (successful_journeys / total_users) * 100 if total_users > 0 else 0,
                "throughput_journeys_per_minute": total_users / duration_minutes
            },
            "step_performance": step_stats,
            "errors": [r.get("error", "") for r in user_results if "error" in r]
        }
    
    async def run_stress_test(self) -> Dict[str, Any]:
        """Test system limits by gradually increasing load"""
        print("🔥 Running stress test to find system limits")
        
        stress_results = []
        user_counts = [1, 5, 10, 15, 20, 25, 30]  # Gradually increase load
        
        for user_count in user_counts:
            print(f"Testing with {user_count} concurrent users...")
            result = await self.run_concurrent_user_test(
                concurrent_users=user_count, 
                test_duration_minutes=2  # Shorter duration for stress test
            )
            
            stress_results.append({
                "concurrent_users": user_count,
                "success_rate": result["overall_results"]["success_rate"],
                "avg_response_time": result["step_performance"].get("routine_generation", {}).get("avg_ms", 0)
            })
            
            # Stop if success rate drops below 80%
            if result["overall_results"]["success_rate"] < 80:
                print(f"⚠️ System degraded at {user_count} users, stopping stress test")
                break
        
        return {
            "stress_test_results": stress_results,
            "recommended_max_users": self._find_recommended_limit(stress_results)
        }
    
    def _find_recommended_limit(self, stress_results: List[Dict]) -> int:
        """Find recommended user limit based on performance degradation"""
        for result in stress_results:
            if (result["success_rate"] < 95 or 
                result["avg_response_time"] > 10000):  # 10 second response time
                return max(1, result["concurrent_users"] - 5)  # Back off 5 users
        
        return stress_results[-1]["concurrent_users"] if stress_results else 1

# Load test execution script
async def run_production_load_tests():
    """Run comprehensive load testing suite"""
    tester = HolisticOSLoadTester()
    
    print("=" * 60)
    print("HolisticOS MVP Production Load Testing")
    print("=" * 60)
    
    # Test 1: Normal load test
    normal_load_result = await tester.run_concurrent_user_test(
        concurrent_users=10, 
        test_duration_minutes=5
    )
    
    print("📊 Normal Load Test Results:")
    print(json.dumps(normal_load_result, indent=2))
    
    # Test 2: Stress test
    stress_test_result = await tester.run_stress_test()
    
    print("🔥 Stress Test Results:")
    print(json.dumps(stress_test_result, indent=2))
    
    # Generate report
    with open("load_test_report.json", "w") as f:
        json.dump({
            "normal_load": normal_load_result,
            "stress_test": stress_test_result,
            "test_timestamp": time.time()
        }, f, indent=2)
    
    print("✅ Load testing complete. Report saved to load_test_report.json")

if __name__ == "__main__":
    asyncio.run(run_production_load_tests())
```

#### 2. Performance Benchmarking
```python
# tests/benchmarks/performance_benchmarks.py
import asyncio
import time
import psutil
import aiohttp
from typing import Dict, Any

class PerformanceBenchmarks:
    """Establish performance baselines for 0.5 CPU instance"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.benchmarks = {}
    
    async def benchmark_cold_start(self) -> Dict[str, Any]:
        """Measure cold start performance"""
        # Wait for potential cold start
        await asyncio.sleep(5)
        
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/health") as response:
                cold_start_time = time.time() - start_time
                return {
                    "cold_start_ms": cold_start_time * 1000,
                    "status_code": response.status
                }
    
    async def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Measure memory usage patterns"""
        initial_memory = psutil.virtual_memory().used
        
        # Simulate load
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(10):
                tasks.append(session.post(
                    f"{self.base_url}/api/user/bench_user_{i}/routine/generate",
                    json={"archetype": "Foundation Builder"}
                ))
            
            await asyncio.gather(*tasks, return_exceptions=True)
        
        peak_memory = psutil.virtual_memory().used
        memory_delta = (peak_memory - initial_memory) / 1024 / 1024  # MB
        
        return {
            "initial_memory_mb": initial_memory / 1024 / 1024,
            "peak_memory_mb": peak_memory / 1024 / 1024,
            "memory_delta_mb": memory_delta
        }
    
    async def benchmark_cost_efficiency(self) -> Dict[str, Any]:
        """Estimate API costs under load"""
        cost_estimates = {
            "routine_generation": 0.02,  # Estimated GPT-4 cost
            "nutrition_generation": 0.02,
            "behavior_analysis": 0.03,
            "insights_generation": 0.01
        }
        
        # Simulate 100 users over 1 hour
        users_per_hour = 100
        cost_per_user = sum(cost_estimates.values())
        hourly_cost = users_per_hour * cost_per_user
        daily_cost = hourly_cost * 24
        monthly_cost = daily_cost * 30
        
        return {
            "cost_per_user_usd": cost_per_user,
            "hourly_cost_usd": hourly_cost,
            "daily_cost_usd": daily_cost,
            "monthly_cost_usd": monthly_cost,
            "cost_breakdown": cost_estimates
        }
    
    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        results = {}
        
        print("🏃 Running performance benchmarks...")
        
        results["cold_start"] = await self.benchmark_cold_start()
        results["memory_usage"] = await self.benchmark_memory_usage()
        results["cost_efficiency"] = await self.benchmark_cost_efficiency()
        
        return results

# Benchmark execution
async def main():
    benchmarks = PerformanceBenchmarks()
    results = await benchmarks.run_all_benchmarks()
    
    with open("performance_benchmarks.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("📊 Benchmark results:", json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
```

#### 3. Deployment Runbook
```markdown
# docs/deployment_runbook.md

# HolisticOS MVP Deployment Runbook

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests pass (`python -m pytest tests/`)
- [ ] Load tests completed successfully
- [ ] Code review approved
- [ ] Security scan completed
- [ ] Dependencies updated and verified

### Environment Setup
- [ ] Environment variables configured in Render
- [ ] Database migrations ready (if any)
- [ ] API keys validated
- [ ] Rate limiting configured
- [ ] Monitoring enabled

### Performance Validation
- [ ] Load test results reviewed
- [ ] Memory usage within limits (<400MB)
- [ ] Response times acceptable (<5s p95)
- [ ] Cost projections validated

## Deployment Process

### Step 1: Pre-deployment Verification
```bash
# Run comprehensive tests
python tests/load/load_test_suite.py
python tests/benchmarks/performance_benchmarks.py

# Verify health check
curl -f http://localhost:8001/api/health || exit 1

# Check environment variables
python -c "import os; print('✅ All required env vars set' if all([
    os.getenv('OPENAI_API_KEY'),
    os.getenv('DATABASE_URL'),
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
]) else '❌ Missing env vars')"
```

### Step 2: Render Deployment
```yaml
# render.yaml deployment configuration
services:
  - type: web
    name: holisticos-mvp
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python start_openai.py"
    plan: starter  # 0.5 CPU, 512MB RAM
    healthCheckPath: "/api/health"
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: OPENAI_API_KEY
        sync: false
      - key: DATABASE_URL
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: SLACK_WEBHOOK_URL
        sync: false
```

### Step 3: Post-deployment Verification
```bash
# Wait for deployment
sleep 30

# Health check
curl -f https://your-app.onrender.com/api/health

# Smoke test
curl -X POST https://your-app.onrender.com/api/user/test_user/routine/generate \
  -H "Content-Type: application/json" \
  -d '{"archetype": "Foundation Builder"}'

# Monitor for 10 minutes
python scripts/deployment_monitor.py --duration 600
```

### Step 4: Rollback Procedure (if needed)
```bash
# Immediate rollback via Render dashboard
# 1. Go to Render dashboard
# 2. Select service
# 3. Click "Rollback" to previous deployment
# 4. Monitor health

# Alternative: Environment variable rollback
# Update environment to disable new features
export FEATURE_FLAG_NEW_ANALYSIS=false
```

## Monitoring Post-Deployment

### Key Metrics to Watch
- Response times (should be <5s p95)
- Error rates (should be <1%)
- Memory usage (should stay <400MB)
- API costs (track daily spending)
- User satisfaction (response times)

### Alert Thresholds
- Response time >10s: Immediate investigation
- Error rate >5%: Immediate investigation  
- Memory usage >450MB: Scale up or optimize
- Daily cost >$50: Cost review needed

## Environment-Specific Notes

### Production (Render)
- Health check: https://your-app.onrender.com/api/health
- Logs: Available in Render dashboard
- Metrics: Monitor via `/metrics` endpoint
- Alerting: Slack webhook configured

### Staging
- Used for final testing before production
- Same configuration as production
- Test with realistic data volume

## Common Issues and Solutions

### Issue: High Memory Usage
**Symptoms**: Memory >400MB, slow responses
**Solution**: 
1. Check `/api/monitoring/stats` for memory breakdown
2. Clear caches via admin endpoint
3. Consider connection pool tuning

### Issue: Slow Response Times
**Symptoms**: p95 response time >10s
**Solution**:
1. Check OpenAI API status
2. Verify database connection pool
3. Review rate limiting configuration

### Issue: High Error Rates
**Symptoms**: >5% error rate
**Solution**:
1. Check logs for error patterns
2. Verify external service availability
3. Check rate limiting settings
```

#### 4. Incident Response Playbook
```markdown
# docs/incident_response_playbook.md

# HolisticOS MVP Incident Response Playbook

## Incident Classification

### P0 - Critical (Resolve within 1 hour)
- Complete service outage
- Data corruption or loss
- Security breach
- >50% error rate

### P1 - High (Resolve within 4 hours)  
- Performance degradation affecting >20% of users
- Key feature completely broken
- Cost overrun alerts

### P2 - Medium (Resolve within 24 hours)
- Single feature broken
- Performance degradation affecting <20% of users
- Non-critical monitoring alerts

### P3 - Low (Resolve within 72 hours)
- Minor UI issues
- Documentation problems
- Enhancement requests

## Incident Response Process

### Step 1: Detection and Alert
```
Alert Received → Acknowledge → Assess Severity → Escalate if needed
```

**Detection Sources:**
- Slack alerts from monitoring
- User reports
- Health check failures
- Performance monitoring

### Step 2: Initial Response (within 15 minutes)
1. **Acknowledge the incident**
   - Update status page (if available)
   - Notify stakeholders

2. **Quick assessment**
   ```bash
   # Check service health
   curl https://your-app.onrender.com/api/health
   
   # Check recent logs
   # Via Render dashboard or monitoring
   
   # Check key metrics
   curl https://your-app.onrender.com/api/monitoring/stats
   ```

3. **Immediate mitigation (if possible)**
   - Restart service if unresponsive
   - Toggle feature flags to disable problematic features
   - Scale resources if needed

### Step 3: Investigation and Resolution

#### For Performance Issues
```bash
# Check system resources
curl https://your-app.onrender.com/api/monitoring/stats

# Review error patterns
# Check Slack alerts for patterns

# Check external services
curl https://api.openai.com/v1/models
# Check Supabase status

# Test key endpoints
curl -X POST https://your-app.onrender.com/api/user/test/routine/generate \
  -H "Content-Type: application/json" \
  -d '{"archetype": "Foundation Builder"}'
```

#### For Error Rate Issues
```bash
# Check error distribution by endpoint
# Review structured logs for error patterns
# Check rate limiting status
# Verify environment variables
```

#### For Cost Overrun
```bash
# Check daily cost tracking
curl https://your-app.onrender.com/api/admin/rate-limits

# Review user activity patterns
# Check for unusual API usage
# Implement emergency rate limiting if needed
```

### Step 4: Communication

#### Internal Communication
- **Slack**: Real-time updates in #incidents channel
- **Status**: Update internal status board
- **Stakeholders**: Email updates for P0/P1 incidents

#### External Communication (if needed)
- **Users**: In-app notifications for service issues
- **Status Page**: Update service status
- **Social Media**: For widespread outages

### Step 5: Resolution and Recovery
1. **Implement fix**
2. **Verify resolution**
   ```bash
   # Run smoke tests
   python tests/smoke_tests.py
   
   # Monitor for 30 minutes
   python scripts/incident_monitor.py --duration 1800
   ```
3. **Update stakeholders**
4. **Document resolution**

### Step 6: Post-Incident Review
1. **Incident timeline**
2. **Root cause analysis**
3. **Action items to prevent recurrence**
4. **Update runbooks and procedures**

## Emergency Contacts

- **Primary On-Call**: [Your contact]
- **Secondary**: [Backup contact]
- **Escalation**: [Manager/CTO contact]

## Recovery Procedures

### Database Recovery
```bash
# If database connection issues
# Check Supabase status
# Verify connection pool configuration
# Test with manual connection
```

### Service Recovery
```bash
# Complete service restart via Render
# Check health after restart
curl https://your-app.onrender.com/api/health

# Verify key functionality
python tests/smoke_tests.py
```

### Cost Control Emergency
```bash
# Emergency rate limiting
# Temporarily disable expensive endpoints
# Contact OpenAI if billing emergency
```

## Prevention Strategies

### Proactive Monitoring
- Set up alerts for key metrics
- Regular health checks
- Performance baseline monitoring
- Cost tracking and alerts

### Regular Testing
- Weekly load testing
- Monthly disaster recovery testing
- Quarterly incident response drills

### Documentation
- Keep runbooks updated
- Document all incident resolutions
- Regular review of procedures
```

## What is the Expected Outcome

### Testing Coverage
```python
testing_improvements = {
    "load_testing": "Validate system under production-like conditions",
    "performance_benchmarks": "Establish baselines for optimization",
    "stress_testing": "Identify system breaking points",
    "cost_validation": "Predict and control operational expenses"
}
```

### Operational Readiness
- **Deployment Confidence**: Standardized, repeatable deployments
- **Incident Response**: Quick resolution of production issues
- **Performance Predictability**: Known system limits and capacity
- **Cost Control**: Validated cost projections and limits

### Before vs After Operations

**Before (No Documentation)**:
```
Issue occurs → Panic → Manual investigation → Slow resolution → Learning from scratch
```

**After (With Runbooks)**:
```
Issue occurs → Follow playbook → Systematic investigation → Fast resolution → Documented learning
```

### Success Criteria
- [ ] Load testing validates 10+ concurrent users
- [ ] Performance benchmarks establish baselines
- [ ] Deployment runbook enables consistent releases
- [ ] Incident response playbook reduces resolution time by 50%
- [ ] Cost projections accurate within 20%

### Key Performance Targets
```python
performance_targets = {
    "concurrent_users": 15,          # 0.5 CPU instance capacity
    "response_time_p95": "5s",       # 95% of requests under 5s
    "uptime": "99.5%",               # Minimal downtime target
    "incident_resolution": "1h",      # P0 incidents resolved within 1h
    "deployment_frequency": "daily",  # Enable daily deployments if needed
    "cost_per_user": "$0.10/day"     # Target operational cost
}
```

### Documentation Deliverables
- **Load Testing Report**: Performance under various loads
- **Deployment Runbook**: Step-by-step deployment guide
- **Incident Response Playbook**: Emergency procedures
- **Performance Benchmarks**: Baseline metrics for optimization
- **Cost Analysis**: Operational cost projections

### Dependencies
- Load testing tools (aiohttp, asyncio)
- Monitoring integration (Slack webhooks)
- Environment configuration documentation
- Access to production metrics

### Risk Mitigation
- Test in staging environment first
- Gradual load increase in testing
- Rollback procedures documented
- Multiple communication channels for incidents

---

**Estimated Effort**: 1 day  
**Risk Level**: Low (improves reliability and confidence)  
**MVP Impact**: High - Essential for production operations and scaling