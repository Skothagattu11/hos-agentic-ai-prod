"""
Memory Monitoring Middleware for HolisticOS FastAPI Application
Tracks memory usage per request and provides performance insights
"""

import time
import logging
from typing import Callable, List, Dict, Any
from fastapi import Request, Response

logger = logging.getLogger(__name__)

class MemoryMonitoringMiddleware:
    """Middleware to monitor memory usage per request"""
    
    def __init__(self, memory_limit_mb: int = 400):
        self.memory_limit_mb = memory_limit_mb
        self.high_memory_requests = []
        self._request_count = 0
        
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            logger.warning("psutil not available for memory monitoring")
            return 0.0
        
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        # Increment request counter
        self._request_count += 1
        
        # Get memory before request
        memory_before = self.get_memory_usage_mb()
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Get memory after request
        memory_after = self.get_memory_usage_mb()
        memory_delta = memory_after - memory_before
        
        # Log high memory usage
        if memory_after > self.memory_limit_mb:
            logger.warning(
                f"High memory usage: {memory_after:.1f}MB after {request.url.path}"
            )
            
            # Track high memory requests
            self.high_memory_requests.append({
                "endpoint": str(request.url.path),
                "method": request.method,
                "memory_mb": round(memory_after, 2),
                "memory_delta_mb": round(memory_delta, 2),
                "duration_ms": round(duration * 1000, 2),
                "timestamp": time.time(),
                "request_count": self._request_count
            })
            
            # Keep only recent high memory requests (last 50)
            if len(self.high_memory_requests) > 50:
                self.high_memory_requests = self.high_memory_requests[-50:]
        
        # Log every 10th request for monitoring
        if self._request_count % 10 == 0:
            logger.info(
                f"Memory check: {memory_after:.1f}MB, "
                f"Request #{self._request_count}, "
                f"Delta: {memory_delta:+.1f}MB"
            )
        
        # Add memory headers for debugging
        response.headers["X-Memory-Usage-MB"] = str(round(memory_after, 2))
        response.headers["X-Memory-Delta-MB"] = str(round(memory_delta, 2))
        response.headers["X-Request-Duration-MS"] = str(round(duration * 1000, 2))
        
        return response
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        current_memory = self.get_memory_usage_mb()
        
        return {
            "current_memory_mb": round(current_memory, 2),
            "memory_limit_mb": self.memory_limit_mb,
            "memory_usage_percentage": round((current_memory / self.memory_limit_mb) * 100, 1) if self.memory_limit_mb > 0 else 0,
            "total_requests": self._request_count,
            "high_memory_requests_count": len(self.high_memory_requests),
            "recent_high_memory_requests": self.high_memory_requests[-5:] if self.high_memory_requests else []
        }
    
    def reset_stats(self):
        """Reset monitoring statistics"""
        self.high_memory_requests.clear()
        self._request_count = 0
        logger.info("Memory monitoring statistics reset")

# Create global instance for the application
memory_monitor = MemoryMonitoringMiddleware(memory_limit_mb=400)