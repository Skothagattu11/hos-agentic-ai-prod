"""
Memory-Safe LRU Cache Implementation for HolisticOS
Provides bounded memory usage with automatic cleanup and monitoring
"""

from collections import OrderedDict
import threading
from typing import Any, Optional, Dict
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
        logger.debug(f"Created cache '{name}' with max_size={max_size}, ttl={ttl_seconds}s")
        return cache
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            logger.debug("psutil not available for memory monitoring")
            return 0.0
    
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
            logger.debug(f"High memory usage: {current_memory:.1f}MB, cleaning caches")
            
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

# Global cache manager - single instance for the application
cache_manager = MemoryAwareCacheManager(total_memory_limit_mb=128)