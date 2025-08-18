"""
Background Memory Cleanup Service for HolisticOS
Automatic memory management with garbage collection and cache cleanup
"""

import asyncio
import gc
import logging
import time
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MemoryCleanupService:
    """Background service for memory cleanup"""
    
    def __init__(self, cleanup_interval: int = 300):  # 5 minutes
        self.cleanup_interval = cleanup_interval
        self.memory_threshold_mb = 350  # Cleanup when above 350MB
        self.running = False
        self._cleanup_count = 0
        self._last_cleanup = None
        self._task = None
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            logger.warning("psutil not available for memory monitoring")
            return 0.0
    
    async def start_cleanup_loop(self):
        """Start the background cleanup loop"""
        if self.running:
            logger.warning("Memory cleanup service already running")
            return
            
        self.running = True
        logger.info(f"Memory cleanup service started (interval: {self.cleanup_interval}s, threshold: {self.memory_threshold_mb}MB)")
        
        try:
            while self.running:
                try:
                    await self._perform_cleanup()
                except Exception as e:
                    logger.error(f"Memory cleanup error: {e}")
                
                # Sleep in smaller chunks to allow for faster shutdown
                for _ in range(self.cleanup_interval):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
        finally:
            logger.info("Memory cleanup service stopped")
    
    async def _perform_cleanup(self):
        """Perform memory cleanup if needed"""
        current_memory = self.get_memory_usage_mb()
        
        if current_memory > self.memory_threshold_mb:
            logger.info(f"Memory cleanup triggered: {current_memory:.1f}MB > {self.memory_threshold_mb}MB")
            
            cleanup_start = time.time()
            
            # Clean up caches
            try:
                from shared_libs.caching.lru_cache import cache_manager
                cache_cleaned = cache_manager.cleanup_if_needed()
                if cache_cleaned:
                    logger.info("Cache cleanup completed")
            except ImportError:
                logger.warning("Cache manager not available for cleanup")
            
            # Clean up metrics collections
            try:
                from shared_libs.utils.bounded_collections import metrics_collector
                # Don't clear metrics, but log current usage
                stats = metrics_collector.get_stats()
                logger.info(f"Metrics usage: {stats}")
            except ImportError:
                logger.warning("Metrics collector not available")
            
            # Force garbage collection
            collected_objects = gc.collect()
            
            # Log cleanup results
            new_memory = self.get_memory_usage_mb()
            memory_freed = current_memory - new_memory
            cleanup_duration = time.time() - cleanup_start
            
            self._cleanup_count += 1
            self._last_cleanup = datetime.now()
            
            logger.info(
                f"Memory cleanup #{self._cleanup_count} completed: "
                f"freed {memory_freed:.1f}MB, "
                f"collected {collected_objects} objects, "
                f"now using {new_memory:.1f}MB "
                f"(duration: {cleanup_duration:.2f}s)"
            )
        else:
            # Log periodic memory status
            logger.debug(f"Memory check: {current_memory:.1f}MB (under threshold)")
    
    async def force_cleanup(self) -> Dict[str, Any]:
        """Force immediate cleanup and return results"""
        logger.info("Force cleanup requested")
        
        memory_before = self.get_memory_usage_mb()
        cleanup_start = time.time()
        
        # Force cache cleanup
        try:
            from shared_libs.caching.lru_cache import cache_manager
            cache_manager.cleanup_if_needed()
        except ImportError:
            pass
        
        # Force garbage collection
        collected_objects = gc.collect()
        
        memory_after = self.get_memory_usage_mb()
        cleanup_duration = time.time() - cleanup_start
        
        self._cleanup_count += 1
        self._last_cleanup = datetime.now()
        
        result = {
            "forced": True,
            "memory_before_mb": round(memory_before, 2),
            "memory_after_mb": round(memory_after, 2),
            "memory_freed_mb": round(memory_before - memory_after, 2),
            "objects_collected": collected_objects,
            "duration_seconds": round(cleanup_duration, 2),
            "cleanup_count": self._cleanup_count
        }
        
        logger.info(f"Force cleanup completed: {result}")
        return result
    
    def stop(self):
        """Stop the cleanup service"""
        if self.running:
            self.running = False
            logger.info("Memory cleanup service stop requested")
        else:
            logger.warning("Memory cleanup service not running")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cleanup service statistics"""
        current_memory = self.get_memory_usage_mb()
        
        return {
            "running": self.running,
            "current_memory_mb": round(current_memory, 2),
            "memory_threshold_mb": self.memory_threshold_mb,
            "memory_usage_percentage": round((current_memory / self.memory_threshold_mb) * 100, 1) if self.memory_threshold_mb > 0 else 0,
            "cleanup_interval_seconds": self.cleanup_interval,
            "total_cleanups": self._cleanup_count,
            "last_cleanup": self._last_cleanup.isoformat() if self._last_cleanup else None,
            "memory_pressure": current_memory > self.memory_threshold_mb
        }

# Global cleanup service instance
cleanup_service = MemoryCleanupService()

# Convenience functions for FastAPI integration
async def start_memory_cleanup():
    """Start memory cleanup background task"""
    if not cleanup_service.running:
        # Create task but don't await it (runs in background)
        cleanup_service._task = asyncio.create_task(cleanup_service.start_cleanup_loop())
        logger.info("Memory cleanup background task started")

async def stop_memory_cleanup():
    """Stop memory cleanup"""
    cleanup_service.stop()
    if cleanup_service._task:
        try:
            await asyncio.wait_for(cleanup_service._task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Memory cleanup task did not stop within timeout")
        cleanup_service._task = None