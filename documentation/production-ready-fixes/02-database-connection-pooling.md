# P0: Database Connection Pooling

## Why This Issue Exists

### Current Problem
- New database connection created for every request
- No connection reuse across requests
- Connection overhead adds 50-100ms to each request
- Potential connection exhaustion under load
- PostgreSQL has default max_connections = 100

### Evidence from Current Code
```python
# services/user_data_service.py:127
async def _ensure_db_connection(self):
    if not self.db_adapter:
        self.db_adapter = SupabaseAsyncPGAdapter()
        await self.db_adapter.connect()  # New connection every time!
```

### Impact on 0.5 CPU Render Instance
- **Connection Limit**: Render PostgreSQL starter allows 20 connections
- **Memory Usage**: Each connection uses ~8MB RAM
- **Performance**: Connection overhead affects response time
- **Reliability**: Connection exhaustion = service outage

### Real-World Scenario
```
10 concurrent users × 3 requests/minute = 30 connections/minute
Without pooling: 30 new connections
With pooling: 5 reused connections
```

## How to Fix

### Implementation Strategy

#### 1. Create Connection Pool Manager
```python
# shared_libs/database/connection_pool.py
import asyncpg
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)

class DatabasePool:
    """Singleton connection pool manager"""
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self, database_url: str = None):
        """Initialize the connection pool"""
        if self._pool is not None:
            return  # Already initialized
        
        database_url = database_url or os.getenv("DATABASE_URL")
        
        # Pool configuration for 0.5 CPU instance
        pool_config = {
            "dsn": database_url,
            "min_size": 2,      # Minimum connections (always ready)
            "max_size": 8,      # Maximum connections (for 0.5 CPU)
            "max_queries": 1000, # Recycle connection after 1000 queries
            "max_inactive_connection_lifetime": 300,  # 5 minutes idle timeout
            "command_timeout": 30,  # 30 second query timeout
            "server_settings": {
                "application_name": "holisticos_mvp",
                "timezone": "UTC"
            }
        }
        
        try:
            self._pool = await asyncpg.create_pool(**pool_config)
            logger.info(f"Database pool initialized: {pool_config['min_size']}-{pool_config['max_size']} connections")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def get_connection(self):
        """Get a connection from the pool"""
        if self._pool is None:
            await self.initialize()
        
        try:
            return self._pool.acquire()
        except Exception as e:
            logger.error(f"Failed to acquire connection: {e}")
            raise
    
    async def execute_query(self, query: str, *args):
        """Execute a query using a pooled connection"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_one(self, query: str, *args):
        """Execute a query and return one result"""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)
    
    async def execute_command(self, command: str, *args):
        """Execute a command (INSERT/UPDATE/DELETE)"""
        async with self.get_connection() as conn:
            return await conn.execute(command, *args)
    
    async def close(self):
        """Close the connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")
    
    async def get_pool_status(self):
        """Get pool statistics for monitoring"""
        if not self._pool:
            return {"status": "not_initialized"}
        
        return {
            "size": self._pool.get_size(),
            "idle_connections": self._pool.get_idle_size(),
            "max_size": self._pool.get_max_size(),
            "min_size": self._pool.get_min_size(),
            "status": "healthy"
        }

# Global pool instance
db_pool = DatabasePool()
```

#### 2. Update Supabase Adapter to Use Pool
```python
# shared_libs/supabase_client/adapter.py - UPDATED VERSION
from shared_libs.database.connection_pool import db_pool
from shared_libs.exceptions.holisticos_exceptions import DatabaseException

class SupabaseAsyncPGAdapter:
    """Updated adapter using connection pooling"""
    
    def __init__(self):
        self.connected = False
    
    async def connect(self):
        """Initialize connection pool (replaces individual connection)"""
        try:
            await db_pool.initialize()
            self.connected = True
            logger.info("Supabase adapter connected via pool")
        except Exception as e:
            logger.error(f"Adapter connection failed: {e}")
            raise DatabaseException(f"Failed to connect to database: {e}")
    
    async def fetch(self, query: str, *args):
        """Execute SELECT query using pool"""
        try:
            return await db_pool.execute_query(query, *args)
        except asyncpg.PostgresError as e:
            logger.error(f"Query failed: {query[:100]}... Error: {e}")
            raise DatabaseException(f"Database query failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            raise DatabaseException(f"Unexpected database error: {e}")
    
    async def fetchrow(self, query: str, *args):
        """Execute SELECT query returning single row"""
        try:
            return await db_pool.execute_one(query, *args)
        except Exception as e:
            logger.error(f"Fetchrow failed: {e}")
            raise DatabaseException(f"Database fetchrow failed: {e}")
    
    async def execute(self, command: str, *args):
        """Execute INSERT/UPDATE/DELETE command"""
        try:
            return await db_pool.execute_command(command, *args)
        except Exception as e:
            logger.error(f"Execute failed: {e}")
            raise DatabaseException(f"Database execute failed: {e}")
    
    async def close(self):
        """Close connection (pool handles actual connections)"""
        self.connected = False
        # Don't close pool here - it's shared across all adapters
        logger.info("Adapter disconnected from pool")

    async def health_check(self):
        """Health check using pool"""
        try:
            result = await db_pool.execute_one("SELECT 1 as health_check")
            pool_status = await db_pool.get_pool_status()
            return {
                "database": "connected",
                "pool_status": pool_status,
                "query_test": "passed" if result else "failed"
            }
        except Exception as e:
            return {
                "database": "error",
                "error": str(e),
                "pool_status": await db_pool.get_pool_status()
            }
```

#### 3. Update User Data Service
```python
# services/user_data_service.py - KEY CHANGES
class UserDataService:
    def __init__(self):
        self.db_adapter = None
        # Remove connection caching - pool handles this
    
    async def _ensure_db_connection(self):
        """Ensure we have a database adapter (pool-based)"""
        if not self.db_adapter:
            self.db_adapter = SupabaseAsyncPGAdapter()
            await self.db_adapter.connect()  # Initializes pool once
        
        # No more individual connection management needed
        return self.db_adapter
    
    async def cleanup(self):
        """Cleanup adapter (pool remains for other services)"""
        if self.db_adapter:
            await self.db_adapter.close()
            self.db_adapter = None
        # Note: Don't close the pool - other services use it
```

#### 4. Application Startup Hook
```python
# services/api_gateway/openai_main.py - Add startup/shutdown hooks
from shared_libs.database.connection_pool import db_pool

@app.on_event("startup")
async def startup_event():
    """Initialize database pool on application startup"""
    logger.info("🚀 Initializing HolisticOS...")
    try:
        await db_pool.initialize()
        logger.info("✅ Database pool initialized")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown"""
    logger.info("🔄 Shutting down HolisticOS...")
    try:
        await db_pool.close()
        logger.info("✅ Database pool closed")
    except Exception as e:
        logger.error(f"⚠️ Shutdown error: {e}")

# Add pool status to health check
@app.get("/api/health")
async def health_check():
    pool_status = await db_pool.get_pool_status()
    return {
        "status": "healthy",
        "database": pool_status,
        "timestamp": datetime.now().isoformat()
    }
```

### Configuration for Render 0.5 CPU

```python
# config/database_config.py
RENDER_POOL_CONFIG = {
    "min_size": 2,        # Always keep 2 connections ready
    "max_size": 8,        # Maximum 8 connections (safe for 0.5 CPU)
    "max_queries": 1000,  # Recycle connections to prevent memory leaks
    "max_inactive_connection_lifetime": 300,  # 5 minutes
    "command_timeout": 30,  # Prevent hanging queries
}

# Environment variables for Render
RENDER_ENV_VARS = {
    "DATABASE_POOL_MIN_SIZE": "2",
    "DATABASE_POOL_MAX_SIZE": "8", 
    "DATABASE_COMMAND_TIMEOUT": "30",
    "DATABASE_MAX_IDLE_TIME": "300"
}
```

## What is the Expected Outcome

### Performance Improvements
- **Connection Time**: Reduced from 50-100ms to <1ms
- **Memory Usage**: Fixed 16MB vs unlimited growth
- **Concurrent Users**: Support 50+ users instead of 20
- **Response Time**: 15-30% faster API responses

### Resource Optimization
```
Before (per request):
- New connection: 50ms
- Memory per connection: 8MB
- Connection limit: 20 total

After (pooled):
- Get from pool: <1ms  
- Shared memory: 64MB total (8 connections)
- Efficient connection reuse
```

### Monitoring Metrics
```python
pool_metrics = {
    "pool_size": "Current number of connections",
    "idle_connections": "Available connections", 
    "connection_wait_time": "Time to get connection",
    "query_duration": "Average query execution time",
    "connection_errors": "Failed connection attempts"
}
```

### Before vs After Code

**Before**:
```python
# Every request creates new connection
async def get_user_data():
    adapter = SupabaseAsyncPGAdapter()  # New connection
    await adapter.connect()             # 50ms overhead
    result = await adapter.fetch(query)
    await adapter.close()               # Close connection
    return result
```

**After**:
```python
# Reuse pooled connections
async def get_user_data():
    adapter = SupabaseAsyncPGAdapter()  # Uses pool
    await adapter.connect()             # <1ms (pool already ready)
    result = await adapter.fetch(query) # Reused connection
    # Connection returns to pool automatically
    return result
```

### Success Criteria
- [ ] Pool initialization on startup
- [ ] Maximum 8 concurrent connections
- [ ] Connection reuse >90%
- [ ] Query timeout protection
- [ ] Pool status in health check
- [ ] Graceful connection recycling

### Load Testing Validation
```python
# Test script to validate pooling
async def load_test():
    tasks = []
    for i in range(20):  # 20 concurrent requests
        tasks.append(make_api_request())
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start_time
    
    # Should complete in <10 seconds (not 20+ seconds)
    assert duration < 10
    assert all(r.status_code == 200 for r in results)
```

### Dependencies
- `pip install asyncpg` (if not already installed)
- Update startup sequence in main.py
- Environment variables for pool configuration

### Risk Mitigation
- Pool gracefully handles connection failures
- Minimum connections ensure service availability
- Connection recycling prevents memory leaks
- Timeout protection prevents hanging

---

**Estimated Effort**: 1 day
**Risk Level**: Medium (affects core database access)
**MVP Impact**: Critical - Required for concurrent users