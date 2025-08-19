# P2: Memory Management

## Why This Issue Exists

### Current Problem
- Unbounded caches and data structures that grow indefinitely
- No memory usage monitoring or limits
- Potential memory leaks in long-running processes
- Risk of OOM (Out of Memory) crashes on 0.5 CPU instance

### Evidence from Current Code
```python
# services/user_data_service.py:35
self.cache = {}  # Unbounded cache - grows forever!

# services/api_gateway/openai_main.py - Multiple agent instances
self.memory_agent = HolisticMemoryAgent()  # Multiple instances created
self.insights_agent = HolisticInsightsAgent()  # No cleanup
```

### Impact on Render 0.5 CPU Instance
- **Memory Limit**: 512MB RAM available
- **Growth Risk**: Caches can consume all available memory
- **Crash Risk**: OOM killer terminates process
- **Performance**: Memory pressure slows garbage collection

### Memory Growth Scenarios
```
Scenario 1: Cache Growth
100 users × 5MB cached data each = 500MB (exceeds limit)

Scenario 2: Agent Instances
10 requests × multiple agent instances × 50MB each = 500MB+

Scenario 3: List Accumulation
Log entries, metrics history, temporary objects accumulate
```

## How to Fix

### Implementation Strategy

#### 1. Implement LRU Caches with Size Limits
```python
# shared_libs/caching/lru_cache.py
from collections import OrderedDict
import threading
from typing import Any, Optional
import time
import logging

logger = logging.getLogger(__name__)

class LRUCache:
    """Thread-safe LRU cache with size and time limits"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key not in self.cache:
                self._misses += 1
                return None
            
            # Check TTL
            if time.time() - self.timestamps[key] > self.ttl_seconds:
                self._remove_key(key)
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            value = self.cache.pop(key)
            self.cache[key] = value
            self._hits += 1
            return value
    
    def set(self, key: str, value: Any) -> None:
        """Set item in cache"""
        with self.lock:
            # Remove if exists
            if key in self.cache:
                self.cache.pop(key)
                self.timestamps.pop(key, None)
            
            # Add new item
            self.cache[key] = value
            self.timestamps[key] = time.time()
            
            # Enforce size limit
            while len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                self._remove_key(oldest_key)
    
    def _remove_key(self, key: str) -> None:
        """Remove key from cache and timestamps"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        with self.lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 3),
                "ttl_seconds": self.ttl_seconds
            }

class MemoryAwareCacheManager:
    """Manages multiple caches with memory monitoring"""
    
    def __init__(self, total_memory_limit_mb: int = 128):
        self.total_memory_limit_mb = total_memory_limit_mb
        self.caches = {}
        
    def create_cache(self, name: str, max_size: int = 50, ttl_seconds: int = 1800) -> LRUCache:
        """Create a new named cache"""
        cache = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)
        self.caches[name] = cache
        logger.info(f"Created cache '{name}' with max_size={max_size}, ttl={ttl_seconds}s")
        return cache
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def get_cache_stats(self) -> dict:
        """Get statistics for all caches"""
        stats = {
            "memory_usage_mb": round(self.get_memory_usage_mb(), 2),
            "memory_limit_mb": self.total_memory_limit_mb,
            "caches": {}
        }
        
        for name, cache in self.caches.items():
            stats["caches"][name] = cache.get_stats()
        
        return stats
    
    def cleanup_if_needed(self) -> bool:
        """Clean up caches if memory usage is high"""
        current_memory = self.get_memory_usage_mb()
        
        if current_memory > self.total_memory_limit_mb * 0.8:  # 80% threshold
            logger.warning(f"High memory usage: {current_memory:.1f}MB, cleaning caches")
            
            # Clear oldest items from all caches
            for cache in self.caches.values():
                # Remove 50% of items from each cache
                current_size = len(cache.cache)
                target_size = current_size // 2
                
                with cache.lock:
                    keys_to_remove = list(cache.cache.keys())[:current_size - target_size]
                    for key in keys_to_remove:
                        cache._remove_key(key)
            
            return True
        
        return False

# Global cache manager
cache_manager = MemoryAwareCacheManager(total_memory_limit_mb=128)
```

#### 2. Update User Data Service with Bounded Cache
```python
# services/user_data_service.py - UPDATED WITH MEMORY MANAGEMENT

from shared_libs.caching.lru_cache import cache_manager
import logging

logger = logging.getLogger(__name__)

class UserDataService:
    """Updated UserDataService with memory-safe caching"""
    
    def __init__(self):
        self.db_adapter = None
        
        # Replace unbounded cache with LRU cache
        self.user_context_cache = cache_manager.create_cache(
            name="user_contexts",
            max_size=50,      # Maximum 50 cached user contexts
            ttl_seconds=1800  # 30 minutes TTL
        )
        
        self.health_data_cache = cache_manager.create_cache(
            name="health_data",
            max_size=30,      # Maximum 30 cached health data sets
            ttl_seconds=600   # 10 minutes TTL
        )
        
        logger.info("UserDataService initialized with memory-safe caching")
    
    async def get_user_health_data(self, user_id: str, days: int = 7) -> UserHealthContext:
        """Get user health data with memory-safe caching"""
        cache_key = f"{user_id}_{days}days"
        
        # Check cache first
        cached_data = self.health_data_cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for user {user_id[:8]}...")
            return cached_data
        
        # Fetch from database
        logger.debug(f"Cache miss for user {user_id[:8]}..., fetching from DB")
        user_context = await self._fetch_user_health_data(user_id, days)
        
        # Cache the result
        self.health_data_cache.set(cache_key, user_context)
        
        # Check memory usage and cleanup if needed
        cache_manager.cleanup_if_needed()
        
        return user_context
    
    def _clean_cache(self):
        """Clean old cache entries - REMOVED (handled by LRU cache)"""
        pass  # No longer needed - LRU cache handles this
    
    async def get_cache_stats(self) -> dict:
        """Get caching statistics for monitoring"""
        return cache_manager.get_cache_stats()
```

#### 3. Implement Singleton Pattern for Agents
```python
# shared_libs/patterns/singleton.py
import threading
from typing import Dict, Any, Type

class SingletonMeta(type):
    """Thread-safe singleton metaclass"""
    _instances = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]

class AgentSingleton:
    """Base class for singleton agents"""
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._setup()
    
    def _setup(self):
        """Override in subclasses for initialization"""
        pass

# Update agent classes to use singleton pattern
# services/agents/memory/main.py - UPDATED
class HolisticMemoryAgent(AgentSingleton, BaseAgent, metaclass=SingletonMeta):
    """Memory agent as singleton to prevent multiple instances"""
    
    def _setup(self):
        """Initialize once per application lifecycle"""
        super().__init__(
            agent_id="memory_management_agent",
            agent_type="memory_management"
        )
        logger.info("HolisticMemoryAgent singleton initialized")

# services/agents/insights/main.py - UPDATED  
class HolisticInsightsAgent(AgentSingleton, BaseAgent, metaclass=SingletonMeta):
    """Insights agent as singleton"""
    
    def _setup(self):
        super().__init__(
            agent_id="insights_generation_agent", 
            agent_type="insights_generation"
        )
        logger.info("HolisticInsightsAgent singleton initialized")
```

#### 4. Memory Monitoring Middleware
```python
# shared_libs/middleware/memory_monitor.py
import psutil
import logging
import time
from fastapi import Request, Response
from typing import Callable

logger = logging.getLogger(__name__)

class MemoryMonitoringMiddleware:
    """Middleware to monitor memory usage per request"""
    
    def __init__(self, memory_limit_mb: int = 400):
        self.memory_limit_mb = memory_limit_mb
        self.high_memory_requests = []
        
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        # Get memory before request
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Get memory after request
        memory_after = process.memory_info().rss / 1024 / 1024
        memory_delta = memory_after - memory_before
        
        # Log high memory usage
        if memory_after > self.memory_limit_mb:
            logger.warning(
                f"High memory usage: {memory_after:.1f}MB after {request.url.path}"
            )
            
            # Track high memory requests
            self.high_memory_requests.append({
                "endpoint": str(request.url.path),
                "memory_mb": memory_after,
                "memory_delta_mb": memory_delta,
                "duration_ms": duration * 1000,
                "timestamp": time.time()
            })
            
            # Keep only recent high memory requests
            cutoff_time = time.time() - 3600  # Last hour
            self.high_memory_requests = [
                req for req in self.high_memory_requests 
                if req["timestamp"] > cutoff_time
            ]
        
        # Add memory headers for debugging
        response.headers["X-Memory-Usage-MB"] = str(round(memory_after, 2))
        response.headers["X-Memory-Delta-MB"] = str(round(memory_delta, 2))
        
        return response
    
    def get_memory_stats(self) -> dict:
        """Get memory usage statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "current_memory_mb": round(memory_info.rss / 1024 / 1024, 2),
            "memory_limit_mb": self.memory_limit_mb,
            "high_memory_requests_last_hour": len(self.high_memory_requests),
            "recent_high_memory_requests": self.high_memory_requests[-5:]  # Last 5
        }

# Add to FastAPI app
from shared_libs.middleware.memory_monitor import MemoryMonitoringMiddleware

memory_monitor = MemoryMonitoringMiddleware(memory_limit_mb=400)
app.middleware("http")(memory_monitor)
```

#### 5. Memory-Safe List Management
```python
# shared_libs/utils/bounded_collections.py
from collections import deque
from typing import Any, List, Optional
import threading

class BoundedList:
    """Thread-safe list with maximum size"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._items = deque(maxlen=max_size)
        self._lock = threading.RLock()
    
    def append(self, item: Any) -> None:
        """Add item to list (removes oldest if at capacity)"""
        with self._lock:
            self._items.append(item)
    
    def extend(self, items: List[Any]) -> None:
        """Add multiple items to list"""
        with self._lock:
            self._items.extend(items)
    
    def get_recent(self, count: int = 10) -> List[Any]:
        """Get most recent items"""
        with self._lock:
            return list(self._items)[-count:]
    
    def get_all(self) -> List[Any]:
        """Get all items"""
        with self._lock:
            return list(self._items)
    
    def clear(self) -> None:
        """Clear all items"""
        with self._lock:
            self._items.clear()
    
    def size(self) -> int:
        """Get current size"""
        return len(self._items)

# Update metrics collection to use bounded lists
# shared_libs/monitoring/metrics.py - UPDATED
from shared_libs.utils.bounded_collections import BoundedList

class MetricsCollector:
    def __init__(self):
        # Replace unbounded lists with bounded ones
        self.recent_requests = BoundedList(max_size=1000)  # Last 1000 requests
        self.error_history = BoundedList(max_size=500)     # Last 500 errors
        self.performance_history = BoundedList(max_size=200)  # Last 200 perf samples
```

#### 6. Automatic Memory Cleanup
```python
# shared_libs/background/memory_cleanup.py
import asyncio
import gc
import logging
import psutil
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryCleanupService:
    """Background service for memory cleanup"""
    
    def __init__(self, cleanup_interval: int = 300):  # 5 minutes
        self.cleanup_interval = cleanup_interval
        self.memory_threshold_mb = 350  # Cleanup when above 350MB
        self.running = False
    
    async def start_cleanup_loop(self):
        """Start the background cleanup loop"""
        self.running = True
        logger.info("Memory cleanup service started")
        
        while self.running:
            try:
                await self._perform_cleanup()
            except Exception as e:
                logger.error(f"Memory cleanup error: {e}")
            
            await asyncio.sleep(self.cleanup_interval)
    
    async def _perform_cleanup(self):
        """Perform memory cleanup if needed"""
        process = psutil.Process()
        current_memory = process.memory_info().rss / 1024 / 1024
        
        if current_memory > self.memory_threshold_mb:
            logger.info(f"Memory cleanup triggered: {current_memory:.1f}MB")
            
            # Clean up caches
            from shared_libs.caching.lru_cache import cache_manager
            cache_manager.cleanup_if_needed()
            
            # Force garbage collection
            collected = gc.collect()
            
            # Log cleanup results
            new_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_freed = current_memory - new_memory
            
            logger.info(
                f"Memory cleanup completed: freed {memory_freed:.1f}MB, "
                f"collected {collected} objects, now using {new_memory:.1f}MB"
            )
    
    def stop(self):
        """Stop the cleanup service"""
        self.running = False
        logger.info("Memory cleanup service stopped")

# Start cleanup service on app startup
cleanup_service = MemoryCleanupService()

@app.on_event("startup")
async def startup_memory_cleanup():
    """Start memory cleanup background task"""
    asyncio.create_task(cleanup_service.start_cleanup_loop())

@app.on_event("shutdown") 
async def shutdown_memory_cleanup():
    """Stop memory cleanup"""
    cleanup_service.stop()
```

## What is the Expected Outcome

### Memory Stability
```python
memory_improvements = {
    "maximum_memory_usage": "400MB (vs unlimited before)",
    "cache_hit_rate": ">80%",
    "memory_leaks": "Eliminated through LRU and cleanup",
    "oom_crashes": "Prevented through monitoring and limits",
    "garbage_collection_efficiency": "Improved through proactive cleanup"
}
```

### Performance Optimization
- **Faster Response Times**: Better memory locality through LRU caching
- **Stable Performance**: No memory pressure spikes
- **Predictable Resource Usage**: Bounded memory consumption

### Monitoring Capabilities
```python
memory_metrics = {
    "current_memory_usage": "Real-time MB usage",
    "cache_statistics": "Hit rates, sizes, TTL effectiveness", 
    "memory_cleanup_events": "When and how much memory freed",
    "high_memory_requests": "Endpoints causing memory spikes",
    "gc_collections": "Garbage collection frequency and efficiency"
}
```

### Before vs After

**Before (Unbounded Growth)**:
```
Application Start: 50MB
After 1 hour: 200MB  
After 6 hours: 450MB
After 12 hours: 600MB → CRASH (OOM)
```

**After (Bounded & Managed)**:
```
Application Start: 50MB
After 1 hour: 120MB
After 6 hours: 150MB  
After 12 hours: 160MB → STABLE
```

### Success Criteria
- [ ] Maximum memory usage stays under 400MB
- [ ] No OOM crashes during load testing
- [ ] Cache hit rates >80% for frequently accessed data
- [ ] Automatic cleanup triggers before critical thresholds
- [ ] Memory usage metrics available in monitoring
- [ ] Singleton agents prevent duplicate instances

### Load Testing Validation
```python
# Memory load test
async def memory_load_test():
    """Test memory behavior under load"""
    initial_memory = get_memory_usage()
    
    # Generate 100 requests
    tasks = [make_api_request() for _ in range(100)]
    await asyncio.gather(*tasks)
    
    # Wait for any cleanup
    await asyncio.sleep(60)
    
    final_memory = get_memory_usage()
    memory_growth = final_memory - initial_memory
    
    # Memory growth should be bounded
    assert memory_growth < 100  # Less than 100MB growth
    assert final_memory < 400   # Under 400MB total
```

### Dependencies
- Memory monitoring tools (psutil already included)
- Background cleanup tasks
- Updated cache implementations

### Risk Mitigation
- Gradual rollout with memory monitoring
- Conservative memory limits initially
- Easy rollback to previous cache implementation
- Alerts for unusual memory patterns

---

**Estimated Effort**: 1 day  
**Risk Level**: Low (improves stability)
**MVP Impact**: Medium - Prevents crashes, improves reliability