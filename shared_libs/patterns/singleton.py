"""
Memory-Safe Singleton Pattern Implementation for HolisticOS
Prevents multiple agent instances and reduces memory consumption
"""

import threading
import time
from typing import Dict, Any, Type
import logging

logger = logging.getLogger(__name__)

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
                    logger.info(f"Created singleton instance for {cls.__name__}")
        return cls._instances[cls]
    
    @classmethod
    def clear_instances(cls):
        """Clear all singleton instances (useful for testing)"""
        with cls._lock:
            cls._instances.clear()
            logger.info("Cleared all singleton instances")

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
    
    def cleanup(self):
        """Override in subclasses for cleanup"""
        pass

class MemoryOptimizedSingleton:
    """Enhanced singleton with memory monitoring"""
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._creation_time = time.time()
        self._memory_usage_mb = 0
        self._setup()
    
    def _setup(self):
        """Override in subclasses for initialization"""
        pass
    
    def get_memory_usage(self) -> float:
        """Get approximate memory usage of this singleton"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            current_memory = process.memory_info().rss / 1024 / 1024
            return current_memory
        except ImportError:
            return self._memory_usage_mb
    
    def get_stats(self) -> dict:
        """Get singleton statistics"""
        return {
            "class_name": self.__class__.__name__,
            "initialized": hasattr(self, '_initialized'),
            "creation_time": getattr(self, '_creation_time', 0),
            "memory_usage_mb": round(self.get_memory_usage(), 2)
        }