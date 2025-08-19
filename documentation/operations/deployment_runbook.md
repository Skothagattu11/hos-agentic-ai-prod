# HolisticOS MVP Deployment Runbook

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests pass (`python -m pytest tests/`)
- [ ] Load tests completed successfully (`python tests/load/load_test_suite.py`)
- [ ] Performance benchmarks acceptable (`python tests/benchmarks/performance_benchmarks.py`)
- [ ] Code review approved
- [ ] Security scan completed
- [ ] Dependencies updated and verified

### Environment Setup
- [ ] Environment variables configured in Render
- [ ] Database migrations ready (if any)
- [ ] API keys validated (OpenAI, Supabase)
- [ ] Rate limiting configured
- [ ] Monitoring enabled (health checks, alerts)
- [ ] Slack webhook configured for alerts

### Performance Validation
- [ ] Load test results reviewed (≥15 concurrent users)
- [ ] Memory usage within limits (<400MB peak)
- [ ] Response times acceptable (<5s p95)
- [ ] Cost projections validated (<$50/day)
- [ ] Error handling tested

### Agent Components Validation
- [ ] Orchestrator agent functioning correctly
- [ ] Behavior analysis agent operational
- [ ] Memory management agent with 4-layer hierarchy
- [ ] Routine generation agent working
- [ ] Nutrition planning agent functional
- [ ] Insights extraction service operational
- [ ] All inter-agent communication working

## Deployment Process

### Step 1: Pre-deployment Verification

```bash
# Navigate to project directory
cd /path/to/hos-agentic-ai-mvp

# Activate virtual environment
source venv/bin/activate

# Run comprehensive tests
echo "Running load tests..."
python tests/load/load_test_suite.py

echo "Running performance benchmarks..."
python tests/benchmarks/performance_benchmarks.py

echo "Running end-to-end tests..."
python test_scripts/test_user_journey_simple.py

# Verify health check locally
echo "Verifying health check..."
python start_openai.py &
SERVER_PID=$!
sleep 10
curl -f http://localhost:8001/api/health || (echo "Health check failed" && kill $SERVER_PID && exit 1)
kill $SERVER_PID

# Check environment variables
echo "Checking environment variables..."
python -c "
import os
required_vars = ['OPENAI_API_KEY', 'DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_KEY']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f'❌ Missing env vars: {missing}')
    exit(1)
else:
    print('✅ All required env vars set')
"

# Verify agent fixes are in place
echo "Verifying production-ready fixes..."
python validate_fixes.py

echo "✅ Pre-deployment verification complete"
```

### Step 2: Render Deployment Configuration

Ensure your `render.yaml` is configured correctly:

```yaml
services:
  - type: web
    name: holisticos-mvp
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python start_openai.py"
    plan: starter  # 0.5 CPU, 512MB RAM
    healthCheckPath: "/api/health"
    autoDeploy: false  # Manual deployments for safety
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
      - key: RATE_LIMIT_ENABLED
        value: "true"
      - key: MEMORY_CLEANUP_ENABLED
        value: "true"
      - key: EMAIL_ALERTS_ENABLED
        value: "true"
```

### Step 3: Deploy to Render

1. **Via Render Dashboard:**
   - Go to Render dashboard
   - Select your service
   - Click "Manual Deploy" 
   - Select the branch/commit to deploy
   - Monitor deployment logs

2. **Via CLI (if configured):**
   ```bash
   # Deploy specific commit
   render deploy --service holisticos-mvp --commit $(git rev-parse HEAD)
   ```

### Step 4: Post-deployment Verification

```bash
# Wait for deployment to complete
echo "Waiting for deployment..."
sleep 60

# Health check
echo "Checking service health..."
curl -f https://your-app.onrender.com/api/health || (echo "Health check failed" && exit 1)

# Smoke test - routine generation
echo "Testing routine generation..."
curl -X POST https://your-app.onrender.com/api/user/deploy_test_user/routine/generate \
  -H "Content-Type: application/json" \
  -d '{"archetype": "Foundation Builder"}' \
  --max-time 30 || (echo "Routine generation failed" && exit 1)

# Smoke test - nutrition generation  
echo "Testing nutrition generation..."
curl -X POST https://your-app.onrender.com/api/user/deploy_test_user/nutrition/generate \
  -H "Content-Type: application/json" \
  -d '{"archetype": "Foundation Builder"}' \
  --max-time 30 || (echo "Nutrition generation failed" && exit 1)

# Smoke test - behavior analysis
echo "Testing behavior analysis..."
curl -X POST https://your-app.onrender.com/api/user/deploy_test_user/behavior/analyze \
  -H "Content-Type: application/json" \
  -d '{}' \
  --max-time 30 || (echo "Behavior analysis failed" && exit 1)

# Check monitoring endpoints
echo "Checking monitoring..."
curl -f https://your-app.onrender.com/api/monitoring/health || echo "Warning: Monitoring endpoint failed"

# Run brief load test
echo "Running post-deployment load test..."
python tests/load/load_test_suite.py

echo "✅ Post-deployment verification complete"
```

### Step 5: Monitor Deployment

```bash
# Monitor for 10 minutes
python scripts/deployment_monitor.py --duration 600 --url https://your-app.onrender.com
```

Create `scripts/deployment_monitor.py`:

```python
import asyncio
import aiohttp
import argparse
import time
from datetime import datetime

async def monitor_deployment(url: str, duration: int):
    """Monitor deployment for specified duration"""
    start_time = time.time()
    end_time = start_time + duration
    
    successes = 0
    failures = 0
    
    print(f"🔍 Monitoring {url} for {duration/60:.1f} minutes...")
    
    async with aiohttp.ClientSession() as session:
        while time.time() < end_time:
            try:
                async with session.get(f"{url}/api/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        successes += 1
                        print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Health check OK")
                    else:
                        failures += 1
                        print(f"❌ {datetime.now().strftime('%H:%M:%S')} - Health check failed: {response.status}")
            except Exception as e:
                failures += 1
                print(f"❌ {datetime.now().strftime('%H:%M:%S')} - Health check error: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    total_checks = successes + failures
    uptime_percentage = (successes / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\n📊 Monitoring Summary:")
    print(f"  Total checks: {total_checks}")
    print(f"  Successes: {successes}")
    print(f"  Failures: {failures}")
    print(f"  Uptime: {uptime_percentage:.1f}%")
    
    if uptime_percentage < 95:
        print("⚠️ WARNING: Uptime below 95% - investigate immediately")
        return False
    
    print("✅ Deployment monitoring passed")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Base URL to monitor")
    parser.add_argument("--duration", type=int, default=600, help="Duration in seconds")
    
    args = parser.parse_args()
    asyncio.run(monitor_deployment(args.url, args.duration))
```

### Step 6: Rollback Procedure (if needed)

#### Immediate Rollback via Render Dashboard
1. Go to Render dashboard
2. Select your service
3. Go to "Deploys" tab
4. Find the last known good deployment
5. Click "Redeploy" on that version
6. Monitor health checks

#### Emergency Feature Disable (Alternative)
```bash
# Disable problematic features via environment variables
# Update environment in Render dashboard:
FEATURE_FLAG_NEW_ANALYSIS=false
RATE_LIMIT_STRICT_MODE=true
MEMORY_CLEANUP_AGGRESSIVE=true

# Or via API if configured:
curl -X POST https://api.render.com/v1/services/{service-id}/env-vars \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"key": "FEATURE_FLAG_NEW_ANALYSIS", "value": "false"}'
```

#### Database Rollback (if needed)
```bash
# If database changes were made, rollback via migration
# Connect to Supabase dashboard and run rollback scripts
# Or use backup restoration if available
```

## Monitoring Post-Deployment

### Key Metrics to Watch

1. **Response Times**
   - Target: <5s p95
   - Alert: >10s p95
   - Critical: >30s p95

2. **Error Rates**
   - Target: <1%
   - Alert: >5%
   - Critical: >10%

3. **Memory Usage**
   - Target: <400MB
   - Alert: >450MB
   - Critical: >500MB

4. **API Costs**
   - Target: <$30/day
   - Alert: >$50/day
   - Critical: >$100/day

5. **Concurrent Users**
   - Target: Handle 15+ users
   - Alert: Performance degradation at <10 users
   - Critical: System failure at <5 users

### Alert Thresholds

Configure these in your monitoring system:

```python
alert_thresholds = {
    "response_time_p95_ms": 10000,  # 10 seconds
    "error_rate_percent": 5,
    "memory_usage_mb": 450,
    "daily_cost_usd": 50,
    "cpu_utilization_percent": 80,
    "failed_health_checks": 3  # consecutive failures
}
```

### Monitoring Endpoints

- **Health Check**: `GET /api/health`
- **Detailed Health**: `GET /api/monitoring/health`
- **System Stats**: `GET /api/monitoring/stats`
- **Rate Limits**: `GET /api/admin/rate-limits`

## Environment-Specific Notes

### Production (Render)
- **URL**: https://your-app.onrender.com
- **Health Check**: https://your-app.onrender.com/api/health
- **Logs**: Available in Render dashboard
- **Metrics**: Monitor via `/api/monitoring/stats` endpoint
- **Alerting**: Slack webhook configured
- **Resource Limits**: 0.5 CPU, 512MB RAM

### Staging (Optional)
- Used for final testing before production
- Same configuration as production
- Test with realistic data volume
- Validate all agent interactions

## Common Issues and Solutions

### Issue: High Memory Usage
**Symptoms**: Memory >400MB, slow responses, potential OOM errors

**Immediate Actions**:
1. Check `/api/monitoring/stats` for memory breakdown
2. Trigger memory cleanup: `curl -X POST /api/admin/cleanup`
3. Review recent deployments for memory leaks

**Solutions**:
```bash
# Enable aggressive memory cleanup
export MEMORY_CLEANUP_AGGRESSIVE=true

# Restart service to clear memory
# Via Render dashboard: Manual Deploy (same version)

# Check connection pool settings
export DATABASE_POOL_SIZE=5
export DATABASE_MAX_OVERFLOW=10
```

### Issue: Slow Response Times
**Symptoms**: p95 response time >10s, user complaints

**Immediate Actions**:
1. Check OpenAI API status: https://status.openai.com
2. Verify database connection pool health
3. Review rate limiting configuration

**Solutions**:
```bash
# Increase request timeouts
export REQUEST_TIMEOUT_SECONDS=30

# Reduce concurrent requests to OpenAI
export OPENAI_MAX_CONCURRENT_REQUESTS=3

# Enable response caching
export RESPONSE_CACHE_ENABLED=true
```

### Issue: High Error Rates
**Symptoms**: >5% error rate, 500 status codes

**Immediate Actions**:
1. Check logs for error patterns
2. Verify external service availability (OpenAI, Supabase)
3. Check rate limiting settings

**Solutions**:
```bash
# Enable circuit breaker for external services
export CIRCUIT_BREAKER_ENABLED=true

# Increase retry attempts
export MAX_RETRY_ATTEMPTS=3

# Reduce rate limits temporarily
export RATE_LIMIT_REQUESTS_PER_MINUTE=30
```

### Issue: Cost Overrun
**Symptoms**: Daily costs >$50, budget alerts

**Immediate Actions**:
1. Check daily cost tracking
2. Review user activity patterns
3. Implement emergency rate limiting

**Solutions**:
```bash
# Emergency rate limiting
export RATE_LIMIT_STRICT_MODE=true
export RATE_LIMIT_REQUESTS_PER_MINUTE=10

# Disable expensive endpoints temporarily
export FEATURE_FLAG_BEHAVIOR_ANALYSIS=false

# Contact OpenAI if billing emergency
# Review usage patterns in dashboard
```

### Issue: Agent Communication Failures
**Symptoms**: Agents not responding, incomplete user journeys

**Immediate Actions**:
1. Check agent health endpoints
2. Verify event system functionality
3. Review memory management agent status

**Solutions**:
```bash
# Restart specific agents (via application restart)
# Check orchestrator logs for agent failures
# Verify database connections for memory persistence

# Enable debug logging
export LOG_LEVEL=DEBUG
export AGENT_DEBUG_MODE=true
```

## Deployment Best Practices

### 1. Deployment Timing
- Deploy during low-traffic hours
- Avoid Friday/weekend deployments
- Plan for rollback time if needed

### 2. Change Management
- Document all changes in deployment notes
- Test in staging environment first
- Gradual rollout if possible

### 3. Communication
- Notify stakeholders of deployment window
- Update status page during deployment
- Have emergency contacts available

### 4. Testing
- Always run full test suite before deployment
- Verify all agent components function correctly
- Test with realistic user scenarios

### 5. Monitoring
- Have monitoring dashboard open during deployment
- Watch key metrics for first hour post-deployment
- Set up alerts for immediate notification

## Post-Deployment Checklist

- [ ] Health checks passing
- [ ] All smoke tests successful
- [ ] Error rates within normal range
- [ ] Response times acceptable
- [ ] Memory usage normal
- [ ] Cost tracking enabled
- [ ] Monitoring alerts configured
- [ ] Stakeholders notified of successful deployment
- [ ] Documentation updated
- [ ] Deployment notes recorded

## Emergency Contacts

- **Primary On-Call**: [Your contact information]
- **Secondary**: [Backup contact]
- **Escalation**: [Manager/CTO contact]
- **Slack Channel**: #incidents
- **Email Alerts**: alerts@yourcompany.com

---

**Last Updated**: [Current Date]
**Version**: 1.0
**Next Review**: [Date + 1 month]