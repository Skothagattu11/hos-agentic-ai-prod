# HolisticOS MVP Incident Response Playbook

## Incident Classification

### P0 - Critical (Resolve within 1 hour)
- Complete service outage (health checks failing)
- Data corruption or loss
- Security breach or unauthorized access
- >50% error rate across all endpoints
- Memory usage causing OOM crashes
- Agent system completely non-functional

### P1 - High (Resolve within 4 hours)  
- Performance degradation affecting >20% of users
- Key agent (routine/nutrition generation) completely broken
- Cost overrun alerts (>$100/day)
- Database connectivity issues
- Memory usage >450MB sustained
- Single agent failure affecting user journeys

### P2 - Medium (Resolve within 24 hours)
- Single endpoint/feature broken
- Performance degradation affecting <20% of users
- Non-critical monitoring alerts
- Slow response times (>10s but <30s)
- Memory cleanup issues
- Agent communication delays

### P3 - Low (Resolve within 72 hours)
- Minor UI/response formatting issues
- Documentation problems
- Enhancement requests
- Non-critical logging issues
- Optimization opportunities

## Incident Response Process

### Step 1: Detection and Alert

**Alert Sources:**
- Slack alerts from monitoring system
- Email alerts from health monitoring
- User reports via support channels
- Health check failures from Render
- Cost alerts from OpenAI/monitoring
- Manual detection during routine checks

**Alert Flow:**
```
Alert Received → Acknowledge → Assess Severity → Escalate if needed → Begin Response
```

### Step 2: Initial Response (within 15 minutes)

#### 1. Acknowledge the Incident
```bash
# Update incident tracking system
# Notify stakeholders immediately for P0/P1
# Post to #incidents Slack channel

echo "Incident acknowledged at $(date)"
echo "Severity: [P0/P1/P2/P3]"
echo "Initial description: [Brief description]"
```

#### 2. Quick Assessment
```bash
# Check service health
curl -f https://your-app.onrender.com/api/health
echo "Health check status: $?"

# Check detailed health
curl https://your-app.onrender.com/api/monitoring/health

# Check system stats
curl https://your-app.onrender.com/api/monitoring/stats

# Check recent logs via Render dashboard
# Look for error patterns in the last 30 minutes

# Check external service status
curl https://api.openai.com/v1/models
echo "OpenAI API status: $?"

# Check Supabase status
# Visit Supabase dashboard or status page
```

#### 3. Immediate Mitigation (if possible)
```bash
# For service unresponsive - restart via Render dashboard
# For high error rates - enable strict rate limiting
export RATE_LIMIT_STRICT_MODE=true

# For memory issues - trigger cleanup
curl -X POST https://your-app.onrender.com/api/admin/cleanup

# For cost overrun - disable expensive features
export FEATURE_FLAG_BEHAVIOR_ANALYSIS=false

# For agent failures - check agent status
curl https://your-app.onrender.com/api/monitoring/agents
```

### Step 3: Investigation and Resolution

#### For Performance Issues (P1/P2)
```bash
# Deep dive into system resources
curl https://your-app.onrender.com/api/monitoring/stats

# Check response time patterns
# Review last 1 hour of monitoring data

# Check database performance
# Look for slow queries in Supabase dashboard

# Check OpenAI API performance
# Review OpenAI usage dashboard

# Test individual endpoints
curl -X POST https://your-app.onrender.com/api/user/incident_test/routine/generate \
  -H "Content-Type: application/json" \
  -d '{"archetype": "Foundation Builder"}' \
  --max-time 30

curl -X POST https://your-app.onrender.com/api/user/incident_test/nutrition/generate \
  -H "Content-Type: application/json" \
  -d '{"archetype": "Foundation Builder"}' \
  --max-time 30

curl -X POST https://your-app.onrender.com/api/user/incident_test/behavior/analyze \
  -H "Content-Type: application/json" \
  -d '{}' \
  --max-time 30

# Check agent communication
# Review orchestrator logs for agent failures
```

#### For Error Rate Issues (P0/P1)
```bash
# Check error distribution by endpoint
# Review structured logs for error patterns

# Check rate limiting status
curl https://your-app.onrender.com/api/admin/rate-limits

# Verify environment variables
# Check Render dashboard for missing/incorrect env vars

# Test database connectivity
# Try direct Supabase connection test

# Check OpenAI API key validity
# Verify quota and billing status

# Review recent deployments
# Check if issue correlates with recent changes
```

#### For Memory Issues (P0/P1)
```bash
# Check memory breakdown
curl https://your-app.onrender.com/api/monitoring/stats

# Force memory cleanup
curl -X POST https://your-app.onrender.com/api/admin/cleanup

# Check for memory leaks
# Review memory patterns over time

# Check database connection pool
# Verify pool size and active connections

# Review agent memory usage
# Check memory management agent status

# Consider service restart if memory critically high
# Via Render dashboard: Manual Deploy (same version)
```

#### For Cost Overrun (P1)
```bash
# Check daily cost tracking
curl https://your-app.onrender.com/api/admin/cost-tracking

# Review user activity patterns
# Check for unusual API usage spikes

# Implement emergency rate limiting
export RATE_LIMIT_REQUESTS_PER_MINUTE=10
export RATE_LIMIT_STRICT_MODE=true

# Disable expensive endpoints temporarily
export FEATURE_FLAG_BEHAVIOR_ANALYSIS=false
export FEATURE_FLAG_NUTRITION_GENERATION=false

# Contact OpenAI support if billing emergency
# Review usage dashboard for anomalies
```

#### For Agent System Failures (P0/P1)
```bash
# Check orchestrator agent status
curl https://your-app.onrender.com/api/monitoring/agents

# Test individual agent endpoints
# Routine generation agent
curl -X POST https://your-app.onrender.com/api/user/test/routine/generate \
  -H "Content-Type: application/json" \
  -d '{"archetype": "Foundation Builder"}'

# Nutrition planning agent  
curl -X POST https://your-app.onrender.com/api/user/test/nutrition/generate \
  -H "Content-Type: application/json" \
  -d '{"archetype": "Foundation Builder"}'

# Behavior analysis agent
curl -X POST https://your-app.onrender.com/api/user/test/behavior/analyze \
  -H "Content-Type: application/json" \
  -d '{}'

# Memory management agent
curl https://your-app.onrender.com/api/monitoring/memory

# Check database connections for memory persistence
# Verify Supabase connection and memory tables

# Check event system functionality
# Review agent communication logs

# Restart application if agents unresponsive
# Via Render dashboard: Manual Deploy
```

### Step 4: Communication

#### Internal Communication
- **Slack**: Real-time updates in #incidents channel
- **Status**: Update internal status tracking
- **Stakeholders**: Email updates for P0/P1 incidents

```bash
# Slack notification template
curl -X POST YOUR_SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "🚨 INCIDENT [P0/P1]: [Brief Description]",
    "attachments": [{
      "color": "danger",
      "fields": [
        {"title": "Severity", "value": "P0", "short": true},
        {"title": "Status", "value": "Investigating", "short": true},
        {"title": "ETA", "value": "[Time estimate]", "short": true}
      ]
    }]
  }'
```

#### External Communication (if needed)
- **Users**: In-app notifications for service issues
- **Status Page**: Update service status (if available)
- **Social Media**: For widespread outages only

### Step 5: Resolution and Recovery

#### 1. Implement Fix
Based on investigation findings, implement appropriate fix:

```bash
# For configuration issues
# Update environment variables in Render dashboard

# For code issues  
# Deploy hotfix via emergency deployment process

# For resource issues
# Scale resources or optimize configuration

# For external service issues
# Implement workarounds or wait for service recovery
```

#### 2. Verify Resolution
```bash
# Run smoke tests
curl -f https://your-app.onrender.com/api/health

# Test affected functionality
python test_scripts/test_user_journey_simple.py

# Run focused tests on fixed area
python tests/unit/test_specific_fix.py

# Monitor for 30 minutes
python scripts/incident_monitor.py --duration 1800
```

Create `scripts/incident_monitor.py`:

```python
import asyncio
import aiohttp
import argparse
import time
from datetime import datetime

async def monitor_incident_resolution(url: str, duration: int):
    """Monitor system after incident resolution"""
    start_time = time.time()
    end_time = start_time + duration
    
    health_checks = []
    endpoint_checks = []
    
    print(f"🔍 Monitoring incident resolution for {duration/60:.1f} minutes...")
    
    async with aiohttp.ClientSession() as session:
        while time.time() < end_time:
            check_time = datetime.now().strftime('%H:%M:%S')
            
            # Health check
            try:
                async with session.get(f"{url}/api/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    health_success = response.status == 200
                    health_checks.append(health_success)
                    print(f"{'✅' if health_success else '❌'} {check_time} - Health: {'OK' if health_success else 'FAIL'}")
            except Exception as e:
                health_checks.append(False)
                print(f"❌ {check_time} - Health: ERROR - {e}")
            
            # Test key endpoint
            try:
                payload = {"archetype": "Foundation Builder"}
                async with session.post(f"{url}/api/user/monitor_test/routine/generate", 
                                      json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    endpoint_success = response.status == 200
                    endpoint_checks.append(endpoint_success)
                    print(f"{'✅' if endpoint_success else '❌'} {check_time} - Endpoint: {'OK' if endpoint_success else 'FAIL'}")
            except Exception as e:
                endpoint_checks.append(False)
                print(f"❌ {check_time} - Endpoint: ERROR - {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    # Calculate success rates
    health_success_rate = (sum(health_checks) / len(health_checks) * 100) if health_checks else 0
    endpoint_success_rate = (sum(endpoint_checks) / len(endpoint_checks) * 100) if endpoint_checks else 0
    
    print(f"\n📊 Incident Monitoring Summary:")
    print(f"  Health Check Success Rate: {health_success_rate:.1f}%")
    print(f"  Endpoint Success Rate: {endpoint_success_rate:.1f}%")
    
    if health_success_rate >= 95 and endpoint_success_rate >= 95:
        print("✅ Incident appears resolved - system stable")
        return True
    else:
        print("⚠️ WARNING: System still showing issues")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://your-app.onrender.com", help="Base URL to monitor")
    parser.add_argument("--duration", type=int, default=1800, help="Duration in seconds")
    
    args = parser.parse_args()
    asyncio.run(monitor_incident_resolution(args.url, args.duration))
```

#### 3. Update Stakeholders
```bash
# Post resolution update to Slack
curl -X POST YOUR_SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "✅ RESOLVED: [Incident Description]",
    "attachments": [{
      "color": "good",
      "fields": [
        {"title": "Resolution Time", "value": "[Duration]", "short": true},
        {"title": "Root Cause", "value": "[Brief cause]", "short": true},
        {"title": "Status", "value": "Monitoring", "short": true}
      ]
    }]
  }'

# Send email update for P0/P1 incidents
# Update internal tracking system
```

### Step 6: Post-Incident Review

#### Incident Documentation Template

```markdown
# Incident Report: [YYYY-MM-DD] [Brief Description]

## Incident Summary
- **Date/Time**: [Start] - [End] (Duration: [X hours])
- **Severity**: P[0-3]
- **Impact**: [Description of user impact]
- **Root Cause**: [Technical root cause]

## Timeline
- [Time] - Incident detected
- [Time] - Response initiated
- [Time] - Mitigation implemented
- [Time] - Resolution deployed
- [Time] - Incident resolved

## Technical Details
### What Happened
[Detailed technical description]

### Root Cause
[Deep dive into why it happened]

### Resolution
[What was done to fix it]

## Impact Assessment
- **Users Affected**: [Number/percentage]
- **Duration**: [How long users were impacted]
- **Financial Impact**: [If any]
- **Data Impact**: [Any data loss/corruption]

## Response Analysis
### What Went Well
- [Positive aspects of response]

### What Could Be Improved
- [Areas for improvement]

## Action Items
- [ ] [Specific action item 1] - [Owner] - [Due date]
- [ ] [Specific action item 2] - [Owner] - [Due date]
- [ ] [Process improvement 1] - [Owner] - [Due date]

## Prevention Measures
- [Changes to prevent recurrence]
- [Monitoring improvements]
- [Process updates]
```

#### Action Item Types
1. **Technical Fixes**: Code changes, configuration updates
2. **Monitoring**: New alerts, improved detection
3. **Process**: Updated runbooks, training
4. **Testing**: New test cases, load testing improvements

## Emergency Contacts

### Primary Team
- **Primary On-Call**: [Name] - [Phone] - [Email]
- **Secondary On-Call**: [Name] - [Phone] - [Email]
- **Technical Lead**: [Name] - [Phone] - [Email]

### Escalation Chain
- **Level 1**: On-call engineer
- **Level 2**: Technical lead
- **Level 3**: Engineering manager
- **Level 4**: CTO/VP Engineering

### External Contacts
- **OpenAI Support**: [Contact information if enterprise]
- **Supabase Support**: [Contact information]
- **Render Support**: [Contact information]

### Communication Channels
- **Slack**: #incidents (for real-time updates)
- **Email**: incidents@yourcompany.com
- **Phone**: [Emergency contact number]

## Recovery Procedures

### Database Recovery
```bash
# For database connection issues
# 1. Check Supabase status dashboard
# 2. Verify connection string in environment
# 3. Test direct database connection
# 4. Check connection pool settings
# 5. Restart application if needed

# For data corruption (rare)
# 1. Stop write operations immediately
# 2. Assess scope of corruption
# 3. Use point-in-time recovery if available
# 4. Contact Supabase support
```

### Service Recovery
```bash
# Complete service restart
# Via Render dashboard:
# 1. Go to service page
# 2. Click "Manual Deploy"
# 3. Select same commit/branch
# 4. Monitor deployment

# Verify recovery
curl -f https://your-app.onrender.com/api/health
python test_scripts/test_user_journey_simple.py
```

### Agent System Recovery
```bash
# Agent-specific recovery
# 1. Check orchestrator agent first
# 2. Verify database connections for memory agent
# 3. Test individual agent endpoints
# 4. Check event system communication
# 5. Restart application if agents unresponsive

# Memory system recovery
# 1. Check memory management agent
# 2. Verify memory tables in database
# 3. Clear corrupted memory if needed
# 4. Restart memory integration service
```

### Cost Control Emergency
```bash
# Emergency cost controls
export RATE_LIMIT_STRICT_MODE=true
export RATE_LIMIT_REQUESTS_PER_MINUTE=5
export FEATURE_FLAG_BEHAVIOR_ANALYSIS=false
export FEATURE_FLAG_NUTRITION_GENERATION=false

# Monitor cost reduction
# Check OpenAI usage dashboard
# Verify rate limiting is effective
```

## Prevention Strategies

### Proactive Monitoring
- Comprehensive health checks every 30 seconds
- Performance baseline monitoring
- Cost tracking and alerts
- Memory usage trending
- Agent communication monitoring

### Regular Testing
- Weekly load testing
- Monthly disaster recovery testing
- Quarterly incident response drills
- Continuous integration testing

### Documentation Maintenance
- Monthly runbook reviews
- Post-incident documentation updates
- Regular procedure validation
- Team training on new procedures

### System Improvements
- Automated failover where possible
- Circuit breakers for external services
- Graceful degradation patterns
- Enhanced monitoring and alerting

## Incident Response Training

### New Team Member Onboarding
1. Review this playbook thoroughly
2. Shadow incident response (if opportunity)
3. Practice with test incidents
4. Understand escalation procedures

### Regular Training
- Quarterly incident response drills
- Annual playbook review and updates
- Cross-training on different components
- External training on incident management

### Simulation Exercises
```bash
# Simulate different incident types
# 1. High load scenario
python tests/load/load_test_suite.py --users 50

# 2. Memory pressure test
python tests/memory_pressure_test.py

# 3. External service failure simulation
# Mock OpenAI API failures

# 4. Database connectivity issues
# Simulate network partitions
```

---

**Last Updated**: [Current Date]  
**Version**: 1.0  
**Next Review**: [Date + 3 months]  
**Owner**: [Primary Contact]