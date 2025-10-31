# Development vs Production Environment Guide

## 🎯 Purpose

This guide explains how to configure the system for **local development (WSL2/local machine)** vs **production deployment (server)**.

---

## 📊 Key Differences

| Aspect | Development (Local) | Production (Server) |
|--------|---------------------|---------------------|
| **Environment Variable** | `ENVIRONMENT=development` | `ENVIRONMENT=production` |
| **Database Access** | Supabase REST API | PostgreSQL Connection Pool |
| **Query Support** | Limited (no OR conditions) | Full SQL support |
| **Connection Issues** | Works in WSL2 | Requires stable network |
| **Performance** | Slower (multiple REST calls) | Faster (direct SQL) |
| **Dynamic Task Selection** | Limited functionality | Full functionality |

---

## 🔧 Local Development Setup (WSL2/Local Machine)

### Configuration

```env
# .env file
ENVIRONMENT=development

# Database URL (not actually used in development, but required)
DATABASE_URL=postgresql://postgres.project:password@aws-0-us-west-1.pooler.supabase.com:5432/postgres
```

### How It Works

1. **Connection Attempt**: System tries to connect to PostgreSQL
2. **Connection Fails**: DNS resolution fails in WSL2 (`getaddrinfo failed`)
3. **Automatic Fallback**: System falls back to Supabase REST API
4. **REST API Mode**: All queries use Supabase REST API

### Limitations

**❌ OR Conditions Not Supported**

Queries like this **will not work correctly**:
```sql
WHERE (time_of_day_preference = 'morning' OR time_of_day_preference = 'any')
```

**Result**: Only the first condition before OR is applied, returning fewer results.

**❌ Complex Subqueries Not Supported**

Queries like this **will fail**:
```sql
WHERE variation_group NOT IN (SELECT unnest($1::text[]))
```

**Impact on Dynamic Task Selection**:
- Task library queries return fewer results
- Some tasks may be missed due to OR condition skipping
- System will still function but with reduced task variety

### When to Use Development Mode

✅ Local development on WSL2
✅ Testing basic functionality
✅ UI/UX development
✅ Quick prototyping

❌ Testing dynamic task selection thoroughly
❌ Performance testing
❌ Production-like behavior testing

---

## 🚀 Production Setup (Deployed Server)

### Configuration

```env
# .env file
ENVIRONMENT=production

# Use pooler URL for better performance
DATABASE_URL=postgresql://postgres.project:password@aws-0-us-west-1.pooler.supabase.com:5432/postgres
```

### How It Works

1. **Connection Pool**: System creates PostgreSQL connection pool (2-8 connections)
2. **Direct SQL**: All queries execute directly on PostgreSQL
3. **Full Support**: Complex queries with OR, subqueries, joins all work

### Full Feature Support

✅ OR conditions in WHERE clauses
✅ Complex subqueries
✅ Array operations (`unnest`, `array_agg`, etc.)
✅ Full SQL feature set
✅ Optimal performance

### When to Use Production Mode

✅ Deployed server (Render, AWS, etc.)
✅ Testing dynamic task selection
✅ Performance testing
✅ Final testing before release

---

## 🔄 How to Switch Between Modes

### Switch to Development Mode

```bash
# 1. Edit .env file
nano .env

# 2. Change ENVIRONMENT
ENVIRONMENT=development

# 3. Restart server
# Stop with Ctrl+C, then:
python start_openai.py
```

### Switch to Production Mode

```bash
# 1. Edit .env file
nano .env

# 2. Change ENVIRONMENT
ENVIRONMENT=production

# 3. Restart server
# Stop with Ctrl+C, then:
python start_openai.py
```

---

## 🐛 Troubleshooting

### Issue: "getaddrinfo failed" in Development Mode

**Expected behavior** - this is normal in WSL2. The system automatically falls back to REST API.

**Logs you'll see:**
```
ERROR:shared_libs.database.connection_pool:Unexpected error during pool initialization: [Errno 11001] getaddrinfo failed
WARNING:shared_libs.supabase_client.adapter: Database pool failed, falling back to Supabase REST API only
```

**Solution**: None needed - this is expected in development mode.

---

### Issue: "Skipping unsupported WHERE clause with OR/parentheses"

**Appears in**: Development mode only

**Logs you'll see:**
```
WARNING:shared_libs.supabase_client.adapter:Skipping unsupported WHERE clause with OR/parentheses: (time_of_day_preference = $1 OR time_of_day_preference = 'any')
WARNING:shared_libs.supabase_client.adapter:Complex queries should use ENVIRONMENT=production with PostgreSQL connection
```

**Solution**: Switch to production mode for testing dynamic task selection:
```bash
ENVIRONMENT=production
```

---

### Issue: Dynamic Task Selection Returns 0% Replacement

**Cause**: Row Level Security (RLS) blocking REST API access

**Symptoms**:
- All tasks show `source: ai`
- No tasks have `task_library_id` populated
- Replacement rate: 0%
- Logs show `[DEVELOPMENT] Fetched 0 tasks` despite table having data

**Root Cause**: System was using `SUPABASE_KEY` (anon key) instead of `SUPABASE_SERVICE_KEY` for REST API calls. The RLS policies on `task_library` only allow `authenticated` or `service_role` access.

**Solution**: Fixed in `shared_libs/supabase_client/adapter.py` to prioritize `SUPABASE_SERVICE_KEY` over `SUPABASE_KEY`.

---

### Issue: Connection Pool Errors in Production

**Symptoms**:
```
ERROR: could not connect to server
ERROR: connection pool exhausted
```

**Possible Causes**:
1. Invalid DATABASE_URL
2. Firewall blocking connection
3. Too many concurrent connections

**Solutions**:
1. Verify DATABASE_URL is correct
2. Use pooler URL instead of direct connection
3. Check connection pool settings (2-8 connections)

---

## 📋 Test Mode vs Environment Mode

**These are DIFFERENT settings:**

### Test Mode
```env
ENABLE_TEST_MODE=true  # For multi-day testing with future dates
```

**Purpose**: Allows testing with future dates (creates separate plans for each date)

### Environment Mode
```env
ENVIRONMENT=development  # or production
```

**Purpose**: Controls database access method (REST API vs PostgreSQL)

**You can combine them:**
- `ENABLE_TEST_MODE=true` + `ENVIRONMENT=development` → Multi-day testing with REST API
- `ENABLE_TEST_MODE=true` + `ENVIRONMENT=production` → Multi-day testing with full SQL
- `ENABLE_TEST_MODE=false` + `ENVIRONMENT=production` → Normal production behavior

---

## ✅ Recommended Configuration

### For Local Development (WSL2)
```env
ENVIRONMENT=development
ENABLE_TEST_MODE=false
```

### For Testing Dynamic Task Selection
```env
ENVIRONMENT=production
ENABLE_TEST_MODE=true
```

### For Production Deployment
```env
ENVIRONMENT=production
ENABLE_TEST_MODE=false
```

---

## 🔍 Verification

### Check Current Mode

Look for these log messages when the server starts:

**Development Mode:**
```
WARNING:shared_libs.supabase_client.adapter: Database pool failed, falling back to Supabase REST API only
```

**Production Mode:**
```
INFO:shared_libs.database.connection_pool: Database pool initialized successfully
```

### Test Dynamic Task Selection

1. Generate a plan
2. Check logs for:
   ```
   [INFO] [HYBRID] Dynamic task selection enabled
   [OK] [HYBRID] Replaced X/Y tasks with library selections
   ```
3. Verify replacement rate > 0%

---

## 📝 Summary

**Key Takeaway**:

- **Local Development (WSL2)** → Use `ENVIRONMENT=development` (REST API mode)
- **Production Server** → Use `ENVIRONMENT=production` (PostgreSQL mode)
- **Testing Dynamic Features** → Must use `ENVIRONMENT=production`

The system is designed to **automatically fallback** to REST API when PostgreSQL connection fails, making it seamless to work in WSL2 environments.

---

## 🆘 Still Having Issues?

1. Check `.env` file has correct `ENVIRONMENT` value
2. Restart server after changing `.env`
3. Check logs for connection errors
4. Verify Supabase credentials are correct
5. Check `task_library` table exists and has data

For complex SQL query testing (OR conditions, subqueries), you **must** use `ENVIRONMENT=production`.
