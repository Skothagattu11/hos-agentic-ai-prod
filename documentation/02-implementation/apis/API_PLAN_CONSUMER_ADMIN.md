# 🎯 **Comprehensive MVP API Plan: Consumer + Admin Portal**

**Document Version:** 1.0  
**Date:** August 19, 2025  
**Status:** Planning Phase  

## **🏗️ Architecture Overview**

### **Two-Tier API Design:**
1. **Consumer APIs** - User-facing, optimized for mobile/web apps
2. **Admin APIs** - Management portal, comprehensive monitoring

### **Design Principles:**
- ✅ Follow successful patterns from existing working endpoints
- ✅ Single responsibility - each endpoint does one thing well  
- ✅ Consistent response format across all APIs
- ✅ Efficient database queries leveraging existing indexes
- ✅ MVP focus - essential features first, advanced features later

---

## 📱 **CONSUMER APIs (User-Facing)**

### **1. Current State APIs (Dashboard)**

```http
GET /api/user/{user_id}/current
```
**Purpose:** Complete current user state for dashboard - single call efficiency  
**Query Parameters:** None (optimized for speed)  
**Use Case:** Mobile app dashboard load, web app home page  

**Response Format:**
```json
{
  "status": "success",
  "user_id": "user123",
  "data": {
    "current_archetype": "Peak Performer",
    "last_analysis_date": "2025-08-19",
    "latest": {
      "behavior_analysis": { 
        "date": "2025-08-19", 
        "summary": "Strong sleep, needs more activity", 
        "goals": ["Increase daily steps to 8000"],
        "readiness": "High"
      },
      "routine_plan": { 
        "date": "2025-08-19", 
        "daily_schedule": [
          {"time": "07:00", "activity": "Morning walk", "duration": 30}
        ]
      },
      "nutrition_plan": { 
        "date": "2025-08-19", 
        "meals": [
          {"meal": "breakfast", "items": ["oatmeal", "berries"]}
        ]
      }
    },
    "recent_insights": [
      { "date": "2025-08-19", "category": "activity", "message": "Great progress on sleep consistency" }
    ],
    "archetype_progress": {
      "current": "Peak Performer",
      "analysis_count": 3,
      "days_active": 12
    }
  },
  "meta": {
    "cache_status": "fresh",
    "last_updated": "2025-08-19T10:30:00Z"
  }
}
```

### **2. Plans APIs (User Plans)**

```http
GET /api/user/{user_id}/plans/current
GET /api/user/{user_id}/plans/history
GET /api/user/{user_id}/plans/{date}
```

**2.1 Current Plans**
```http
GET /api/user/{user_id}/plans/current
```
**Purpose:** Get active routine and nutrition plans  
**Returns:** Latest generated plans for user

**2.2 Plans History**
```http
GET /api/user/{user_id}/plans/history?days=30&type=routine,nutrition
```
**Query Parameters:**
- `days` (optional, default: 30) - Number of days to look back
- `type` (optional) - Filter by plan type: `routine`, `nutrition`, or both
- `archetype` (optional) - Filter by specific archetype

**2.3 Date-Specific Plans**
```http
GET /api/user/{user_id}/plans/{date}
```
**Purpose:** Get all plans generated on a specific date  
**Date Format:** YYYY-MM-DD  
**Use Case:** "What was my plan on August 15th?"

### **3. Analysis APIs (User Analytics)**

```http
GET /api/user/{user_id}/analysis/latest
GET /api/user/{user_id}/analysis/history
GET /api/user/{user_id}/analysis/{date}
```

**3.1 Latest Analysis**
```http
GET /api/user/{user_id}/analysis/latest?type=behavior
```
**Query Parameters:**
- `type` (optional) - Filter by analysis type: `behavior`, `routine`, `nutrition`
- `archetype` (optional) - Get latest for specific archetype

**3.2 Analysis History**
```http
GET /api/user/{user_id}/analysis/history?days=30&archetype=Peak Performer
```
**Query Parameters:**
- `days` (optional, default: 30) - Historical range
- `archetype` (optional) - Filter by archetype
- `type` (optional) - Filter by analysis type

**3.3 Date-Specific Analysis**
```http
GET /api/user/{user_id}/analysis/{date}
```
**Purpose:** All analyses performed on specific date  
**Use Case:** Progress tracking, "How did I progress from last month?"

### **4. Insights APIs (User Insights)**

```http
GET /api/user/{user_id}/insights/recent
GET /api/user/{user_id}/insights/history
GET /api/user/{user_id}/insights/{date}
```

**4.1 Recent Insights**
```http
GET /api/user/{user_id}/insights/recent?days=7
```
**Query Parameters:**
- `days` (optional, default: 7) - How many days back
- `category` (optional) - Filter by category: `activity`, `sleep`, `nutrition`

**4.2 Insights History**
```http
GET /api/user/{user_id}/insights/history?days=30&category=activity
```
**Purpose:** Long-term insights tracking for progress visualization

**4.3 Date-Specific Insights**
```http
GET /api/user/{user_id}/insights/{date}
```
**Purpose:** What insights were generated on specific date

### **5. Progress Tracking APIs**

```http
GET /api/user/{user_id}/progress/archetype
GET /api/user/{user_id}/progress/timeline
```

**5.1 Archetype Progress**
```http
GET /api/user/{user_id}/progress/archetype
```
**Purpose:** Show archetype switching history and success patterns  
**Returns:** All archetypes tried, analysis counts, success metrics

**5.2 Timeline Progress**
```http
GET /api/user/{user_id}/progress/timeline?days=30
```
**Purpose:** Progress visualization over time  
**Use Case:** Charts and graphs for user motivation

---

## 🔧 **ADMIN PORTAL APIs (Management)**

### **6. Daily Snapshot API (Key Admin API)**

```http
GET /api/admin/user/{user_id}/date/{date}
```
**Purpose:** Complete user data for specific date - administrative oversight  
**Use Case:** Support tickets, user investigation, system debugging  

**Response Format:**
```json
{
  "status": "success",
  "user_id": "user123",
  "date": "2025-08-19",
  "data": {
    "analyses": [
      {
        "id": "analysis_123",
        "type": "behavior_analysis",
        "archetype": "Peak Performer",
        "timestamp": "2025-08-19T10:30:00Z",
        "summary": "Strong sleep hygiene, low activity",
        "full_result": { 
          "behavioral_signature": "...",
          "recommendations": [...],
          "data_quality": "excellent"
        }
      }
    ],
    "plans": [
      {
        "id": "plan_456",
        "type": "routine_plan", 
        "archetype": "Peak Performer",
        "timestamp": "2025-08-19T10:45:00Z",
        "plan_data": {
          "daily_schedule": [...],
          "difficulty_level": "intermediate"
        }
      }
    ],
    "insights": [
      {
        "id": "insight_789",
        "category": "activity",
        "message": "User needs more cardio workouts",
        "confidence": 0.85,
        "timestamp": "2025-08-19T10:35:00Z",
        "source_analysis": "analysis_123"
      }
    ],
    "archetype_tracking": {
      "archetype_used": "Peak Performer",
      "analysis_count": 3,
      "first_use": "2025-08-15",
      "total_archetypes_tried": 2
    }
  },
  "system_info": {
    "query_time_ms": 45,
    "cache_status": "miss",
    "data_quality": "excellent",
    "api_calls_made": 3
  }
}
```

### **7. User Management APIs**

```http
GET /api/admin/users
GET /api/admin/user/{user_id}/overview
GET /api/admin/user/{user_id}/activity
```

**7.1 Users List**
```http
GET /api/admin/users?days=30&status=active&limit=50
```
**Query Parameters:**
- `days` (optional, default: 30) - Activity period
- `status` (optional) - Filter: `active`, `inactive`, `new`
- `limit` (optional, default: 50) - Results per page
- `offset` (optional) - Pagination offset

**7.2 User Overview**
```http
GET /api/admin/user/{user_id}/overview
```
**Purpose:** Complete user profile for admin dashboard  
**Returns:** User stats, archetype history, analysis summary, recent activity

**7.3 User Activity**
```http
GET /api/admin/user/{user_id}/activity?days=30
```
**Purpose:** Detailed activity log for user investigation  
**Returns:** All API calls, analyses, plans generated, errors encountered

### **8. System Monitoring APIs**

```http
GET /api/admin/analytics/daily
GET /api/admin/analytics/archetype-usage
GET /api/admin/analytics/api-usage
```

**8.1 Daily Analytics**
```http
GET /api/admin/analytics/daily?date=2025-08-19
```
**Purpose:** System-wide metrics for specific date  
**Returns:** Total analyses, unique users, archetype distribution, errors

**8.2 Archetype Usage Analytics**
```http
GET /api/admin/analytics/archetype-usage?days=30
```
**Purpose:** Which archetypes are most popular, success rates  
**Returns:** Usage stats per archetype, switching patterns

**8.3 API Usage Analytics**
```http
GET /api/admin/analytics/api-usage?days=7
```
**Purpose:** Performance monitoring, rate limiting insights  
**Returns:** Endpoint usage, response times, error rates

---

## 🗄️ **Optimized Database Strategy**

### **Single Query Approaches (Performance Critical)**

**1. Daily Snapshot Query (Admin API):**
```sql
-- Get everything for a user on a specific date - single efficient query
WITH daily_analyses AS (
    SELECT 'analysis' as type, analysis_type as subtype, archetype, 
           created_at, analysis_result as data, id
    FROM holistic_analysis_results 
    WHERE user_id = $1 AND DATE(created_at) = $2
),
daily_insights AS (
    SELECT 'insight' as type, category as subtype, NULL as archetype, 
           created_at, 
           json_build_object('message', insight_text, 'confidence', confidence_score) as data,
           id
    FROM holistic_insights 
    WHERE user_id = $1 AND DATE(created_at) = $2
)
SELECT * FROM daily_analyses 
UNION ALL 
SELECT * FROM daily_insights 
ORDER BY created_at DESC
```

**2. User Current State Query (Consumer API):**
```sql
-- Get latest of everything for user - optimized for dashboard
SELECT DISTINCT ON (analysis_type) 
    analysis_type, archetype, analysis_result, created_at, id
FROM holistic_analysis_results 
WHERE user_id = $1 
ORDER BY analysis_type, created_at DESC
LIMIT 10
```

**3. Archetype Progress Query:**
```sql
-- Get archetype switching history and success patterns
SELECT 
    archetype, 
    last_analysis_at, 
    analysis_count,
    created_at as first_used,
    EXTRACT(DAYS FROM NOW() - last_analysis_at) as days_since_last_use
FROM archetype_analysis_tracking 
WHERE user_id = $1 
ORDER BY last_analysis_at DESC
```

### **Essential Database Indexes:**
```sql
-- Performance-critical indexes for fast API responses
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_user_date 
    ON holistic_analysis_results (user_id, created_at DESC);
    
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_user_type_date 
    ON holistic_analysis_results (user_id, analysis_type, created_at DESC);
    
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_insights_user_date 
    ON holistic_insights (user_id, created_at DESC);
    
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_archetype_tracking_user 
    ON archetype_analysis_tracking (user_id, last_analysis_at DESC);
```

---

## 📋 **Implementation Roadmap**

### **Phase 1: Consumer Essentials (Week 1) - Must Have**
**Priority: CRITICAL**
```http
✅ GET /api/user/{user_id}/current                 # Dashboard foundation
✅ GET /api/user/{user_id}/plans/current           # Active plans display  
✅ GET /api/user/{user_id}/analysis/latest         # Recent analysis status
✅ GET /api/user/{user_id}/insights/recent         # User motivation content
```

### **Phase 2: Consumer History (Week 2) - Should Have**
**Priority: HIGH**
```http
✅ GET /api/user/{user_id}/plans/history           # Progress tracking
✅ GET /api/user/{user_id}/analysis/history        # Historical analysis  
✅ GET /api/user/{user_id}/plans/{date}            # Specific date lookup
✅ GET /api/user/{user_id}/analysis/{date}         # Date-specific analysis
✅ GET /api/user/{user_id}/progress/archetype      # Archetype switching viz
```

### **Phase 3: Admin Portal (Week 3) - Could Have**
**Priority: MEDIUM**
```http
✅ GET /api/admin/user/{user_id}/date/{date}       # Support & debugging
✅ GET /api/admin/user/{user_id}/overview          # User management
✅ GET /api/admin/users                            # User list management
✅ GET /api/admin/analytics/daily                  # System health monitoring
```

### **Phase 4: Advanced Features (Week 4) - Nice to Have**
**Priority: LOW**
```http
✅ GET /api/admin/analytics/archetype-usage        # Business intelligence
✅ GET /api/admin/analytics/api-usage              # Performance monitoring  
✅ GET /api/user/{user_id}/progress/timeline       # Advanced visualizations
```

---

## 🎯 **API Response Standardization**

### **Consumer Response Format (User-Friendly):**
```json
{
  "status": "success",
  "user_id": "user123", 
  "data": {
    // Main payload - simplified for mobile apps
  },
  "meta": {
    "count": 5,
    "date_range": "2025-08-12 to 2025-08-19",
    "archetype": "Peak Performer"
  }
}
```

### **Admin Response Format (Comprehensive):**
```json
{
  "status": "success",
  "user_id": "user123",
  "date": "2025-08-19",
  "data": {
    // Complete data with full details
  },
  "system_info": {
    "query_time_ms": 45,
    "cache_status": "hit", 
    "data_quality": "excellent",
    "records_found": 12
  }
}
```

### **Error Response Format (Consistent):**
```json
{
  "status": "error",
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User with ID 'user123' not found",
    "details": "Verify user_id parameter"
  },
  "request_id": "req_123456789"
}
```

---

## 🚀 **Performance Optimizations**

### **Caching Strategy:**
- **Consumer APIs:** 5-minute cache (fast user experience)
- **Admin APIs:** 1-minute cache (near real-time monitoring)  
- **Historical data:** 1-hour cache (static data, rarely changes)
- **Real-time data:** No cache (current state, insights)

### **Response Size Optimization:**
- **Mobile APIs:** Compress responses, minimal data
- **Web APIs:** Rich data with full details
- **Admin APIs:** Complete data with diagnostics
- **Pagination:** Default 50 items, max 200 items per request

### **Database Connection Management:**
- **Read-only queries:** Use read replicas when available
- **Connection pooling:** Reuse connections for efficiency
- **Query optimization:** Use prepared statements, avoid N+1 queries
- **Timeout handling:** 30-second timeout for admin APIs, 10-second for consumer

---

## 📊 **Usage Scenarios & Examples**

### **Consumer App User Flows:**

**1. Dashboard Load (Mobile App Startup):**
```javascript
// Single API call gets everything needed for dashboard
GET /api/user/123/current
→ Latest plans, analysis, insights, archetype progress
```

**2. View Historical Plans (User wants to see last week):**
```javascript
GET /api/user/123/plans/history?days=7
→ All routine and nutrition plans from last 7 days
```

**3. Check Progress (User motivation):**
```javascript
GET /api/user/123/progress/archetype
→ Archetype switching history, analysis counts, success patterns
```

### **Admin Portal Admin Flows:**

**1. Daily System Review (Admin morning routine):**
```javascript
GET /api/admin/analytics/daily?date=2025-08-19
→ System-wide metrics, user activity, error reports
```

**2. User Support Ticket (User reports issue):**
```javascript
GET /api/admin/user/123/date/2025-08-19
→ Complete user activity for that date, diagnose issues
```

**3. Business Intelligence (Weekly planning):**
```javascript
GET /api/admin/analytics/archetype-usage?days=7
→ Which archetypes are popular, user retention patterns
```

---

## 🔒 **Security & Access Control**

### **Consumer APIs Security:**
- **Authentication:** JWT tokens, user can only access own data
- **Rate Limiting:** 100 requests per minute per user
- **Data Filtering:** Only return data user owns
- **Response Sanitization:** Remove sensitive system information

### **Admin APIs Security:**
- **Authentication:** Admin JWT tokens with elevated permissions
- **Role-Based Access:** Different admin levels (support, analytics, super-admin)
- **Rate Limiting:** 1000 requests per minute per admin
- **Audit Logging:** All admin API calls logged for compliance
- **IP Restrictions:** Admin APIs only accessible from office networks

---

## 📝 **API Documentation Standards**

### **OpenAPI/Swagger Documentation:**
- **Interactive docs:** Available at `/docs` endpoint
- **Request/Response examples:** Real data samples for each endpoint
- **Error scenarios:** Common error cases with solutions
- **Rate limiting info:** Clear limits and retry guidance

### **Integration Examples:**
- **cURL commands:** Ready-to-use command line examples
- **JavaScript examples:** Frontend integration code
- **Python examples:** Backend integration code
- **Postman collection:** Import-ready API collection

---

## ✅ **Success Metrics & KPIs**

### **Technical Performance:**
- **Response Time:** <2 seconds for consumer APIs, <5 seconds for admin
- **Availability:** 99.9% uptime for consumer APIs
- **Error Rate:** <1% error rate across all endpoints
- **Cache Hit Rate:** >80% for historical data endpoints

### **Business Metrics:**
- **API Adoption:** Track which endpoints are most used
- **User Engagement:** Frequency of API calls per user
- **Admin Efficiency:** Time saved using admin portal vs manual queries
- **Data Quality:** Completeness and accuracy of returned data

---

## 🔮 **Future Enhancements (Post-MVP)**

### **Advanced Features (V2):**
- **Real-time notifications:** WebSocket endpoints for live updates
- **Batch operations:** Bulk data retrieval for admin efficiency  
- **Data export:** CSV/JSON export capabilities for user data
- **Advanced filtering:** Complex query builders for admin portal
- **Predictive analytics:** AI-powered insights and recommendations

### **Integration Enhancements:**
- **Webhook support:** Real-time data push to external systems
- **GraphQL endpoints:** Flexible query capabilities for advanced clients
- **API versioning:** Backward compatibility for client upgrades
- **SDK libraries:** Official client libraries for popular languages

---

**Document Status:** ✅ Ready for Implementation  
**Next Steps:** Begin Phase 1 implementation with consumer essential APIs  
**Review Date:** Weekly during implementation phases