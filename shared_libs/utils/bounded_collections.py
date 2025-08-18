"""
Memory-Safe Bounded Collections for HolisticOS
Provides thread-safe collections with automatic size limits to prevent memory leaks
"""

from collections import deque
from typing import Any, List, Optional, Dict
import threading
import time
import logging

logger = logging.getLogger(__name__)

class BoundedList:
    """Thread-safe list with maximum size"""
    
    def __init__(self, max_size: int = 1000, name: str = "bounded_list"):
        self.max_size = max_size
        self.name = name
        self._items = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self._total_items_added = 0
    
    def append(self, item: Any) -> None:
        """Add item to list (removes oldest if at capacity)"""
        with self._lock:
            if len(self._items) >= self.max_size:
                logger.debug(f"BoundedList '{self.name}' at capacity, removing oldest item")
            self._items.append(item)
            self._total_items_added += 1
    
    def extend(self, items: List[Any]) -> None:
        """Add multiple items to list"""
        with self._lock:
            for item in items:
                self.append(item)
    
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
            logger.info(f"BoundedList '{self.name}' cleared")
    
    def size(self) -> int:
        """Get current size"""
        return len(self._items)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        with self._lock:
            return {
                "name": self.name,
                "current_size": len(self._items),
                "max_size": self.max_size,
                "total_items_added": self._total_items_added,
                "usage_percentage": round((len(self._items) / self.max_size) * 100, 1)
            }

class BoundedDict:
    """Thread-safe dictionary with maximum size using LRU eviction"""
    
    def __init__(self, max_size: int = 500, name: str = "bounded_dict"):
        self.max_size = max_size
        self.name = name
        self._items = {}
        self._access_order = deque()
        self._lock = threading.RLock()
        self._total_items_added = 0
    
    def set(self, key: str, value: Any) -> None:
        """Set item in dictionary"""
        with self._lock:
            # If key exists, remove from access order
            if key in self._items:
                self._access_order.remove(key)
            else:
                self._total_items_added += 1
            
            # Add/update item
            self._items[key] = value
            self._access_order.append(key)
            
            # Enforce size limit
            while len(self._items) > self.max_size:
                oldest_key = self._access_order.popleft()
                del self._items[oldest_key]
                logger.debug(f"BoundedDict '{self.name}' evicted key: {oldest_key}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get item from dictionary"""
        with self._lock:
            if key in self._items:
                # Move to end (most recently used)
                self._access_order.remove(key)
                self._access_order.append(key)
                return self._items[key]
            return default
    
    def keys(self) -> List[str]:
        """Get all keys"""
        with self._lock:
            return list(self._items.keys())
    
    def values(self) -> List[Any]:
        """Get all values"""
        with self._lock:
            return list(self._items.values())
    
    def items(self) -> List[tuple]:
        """Get all items"""
        with self._lock:
            return list(self._items.items())
    
    def clear(self) -> None:
        """Clear all items"""
        with self._lock:
            self._items.clear()
            self._access_order.clear()
            logger.info(f"BoundedDict '{self.name}' cleared")
    
    def size(self) -> int:
        """Get current size"""
        return len(self._items)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        with self._lock:
            return {
                "name": self.name,
                "current_size": len(self._items),
                "max_size": self.max_size,
                "total_items_added": self._total_items_added,
                "usage_percentage": round((len(self._items) / self.max_size) * 100, 1)
            }

class MetricsCollector:
    """Memory-safe metrics collector using bounded collections"""
    
    def __init__(self):
        # Replace unbounded lists with bounded ones
        self.recent_requests = BoundedList(max_size=1000, name="requests")
        self.error_history = BoundedList(max_size=500, name="errors")
        self.performance_history = BoundedList(max_size=200, name="performance")
        self.agent_metrics = BoundedDict(max_size=100, name="agent_metrics")
        
        logger.info("MetricsCollector initialized with bounded collections")
    
    def record_request(self, endpoint: str, method: str, duration_ms: float, status_code: int):
        """Record request metrics"""
        self.recent_requests.append({
            "endpoint": endpoint,
            "method": method,
            "duration_ms": duration_ms,
            "status_code": status_code,
            "timestamp": time.time()
        })
    
    def record_error(self, error_type: str, message: str, endpoint: str = None):
        """Record error metrics"""
        self.error_history.append({
            "error_type": error_type,
            "message": message,
            "endpoint": endpoint,
            "timestamp": time.time()
        })
    
    def record_performance(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record performance metrics"""
        self.performance_history.append({
            "metric_name": metric_name,
            "value": value,
            "tags": tags or {},
            "timestamp": time.time()
        })
    
    def record_agent_metric(self, agent_id: str, metric_data: Dict[str, Any]):
        """Record agent-specific metrics"""
        self.agent_metrics.set(agent_id, {
            **metric_data,
            "timestamp": time.time()
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive metrics statistics"""
        return {
            "requests": self.recent_requests.get_stats(),
            "errors": self.error_history.get_stats(),
            "performance": self.performance_history.get_stats(),
            "agents": self.agent_metrics.get_stats(),
            "memory_efficient": True
        }
    
    def cleanup(self):
        """Clean up all metrics collections"""
        self.recent_requests.clear()
        self.error_history.clear()
        self.performance_history.clear()
        self.agent_metrics.clear()
        logger.info("MetricsCollector cleaned up")

# Global metrics collector instance
metrics_collector = MetricsCollector()