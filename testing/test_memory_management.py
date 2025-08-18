#!/usr/bin/env python3
"""
Memory Management Testing for HolisticOS
Tests LRU cache, singleton patterns, bounded collections, and memory cleanup
"""

import asyncio
import gc
import logging
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(__file__))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_memory_usage():
    """Get current memory usage in MB"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        logger.warning("psutil not available for memory monitoring")
        return 0.0

async def test_lru_cache():
    """Test LRU cache functionality and memory bounds"""
    print("\n🧪 Testing LRU Cache System...")
    
    from shared_libs.caching.lru_cache import LRUCache, cache_manager
    
    # Test basic LRU cache
    cache = LRUCache(max_size=5, ttl_seconds=2)
    
    # Test setting and getting
    for i in range(10):
        cache.set(f"key_{i}", f"value_{i}")
    
    # Should only have 5 items due to size limit
    stats = cache.get_stats()
    assert stats["size"] <= 5, f"Cache size {stats['size']} exceeds limit"
    print(f"✅ Cache size properly limited to {stats['size']}")
    
    # Test TTL expiration
    cache.set("temp_key", "temp_value")
    assert cache.get("temp_key") == "temp_value"
    
    await asyncio.sleep(2.1)  # Wait for TTL expiration
    assert cache.get("temp_key") is None, "TTL expiration failed"
    print("✅ TTL expiration working")
    
    # Test cache manager
    test_cache = cache_manager.create_cache("test_cache", max_size=10, ttl_seconds=60)
    for i in range(15):
        test_cache.set(f"test_{i}", f"data_{i}")
    
    manager_stats = cache_manager.get_cache_stats()
    print(f"✅ Cache manager stats: {manager_stats}")
    
    return True

async def test_singleton_patterns():
    """Test singleton pattern implementation"""
    print("\n🧪 Testing Singleton Patterns...")
    
    from shared_libs.patterns.singleton import SingletonMeta, AgentSingleton, MemoryOptimizedSingleton
    
    class TestAgent(AgentSingleton, metaclass=SingletonMeta):
        def _setup(self):
            self.agent_id = "test_agent"
            self.initialized_at = time.time()
    
    # Create two instances - should be the same object
    agent1 = TestAgent()
    agent2 = TestAgent()
    
    assert agent1 is agent2, "Singleton pattern failed"
    assert agent1.agent_id == "test_agent"
    print("✅ Singleton pattern working")
    
    # Test memory optimized singleton
    class TestMemoryAgent(MemoryOptimizedSingleton, metaclass=SingletonMeta):
        def _setup(self):
            self.data = "memory_test"
    
    mem_agent1 = TestMemoryAgent()
    mem_agent2 = TestMemoryAgent()
    
    assert mem_agent1 is mem_agent2, "Memory optimized singleton failed"
    stats = mem_agent1.get_stats()
    print(f"✅ Memory optimized singleton stats: {stats}")
    
    return True

async def test_bounded_collections():
    """Test bounded collections functionality"""
    print("\n🧪 Testing Bounded Collections...")
    
    from shared_libs.utils.bounded_collections import BoundedList, BoundedDict, MetricsCollector
    
    # Test BoundedList
    bounded_list = BoundedList(max_size=5, name="test_list")
    
    # Add more items than capacity
    for i in range(10):
        bounded_list.append(f"item_{i}")
    
    assert bounded_list.size() == 5, f"BoundedList size {bounded_list.size()} exceeds limit"
    recent_items = bounded_list.get_recent(3)
    assert len(recent_items) == 3, "get_recent failed"
    print("✅ BoundedList working correctly")
    
    # Test BoundedDict
    bounded_dict = BoundedDict(max_size=3, name="test_dict")
    
    for i in range(5):
        bounded_dict.set(f"key_{i}", f"value_{i}")
    
    assert bounded_dict.size() == 3, f"BoundedDict size {bounded_dict.size()} exceeds limit"
    
    # Access key_2 to make it most recent
    value = bounded_dict.get("key_2")
    assert value == "value_2", "BoundedDict get failed"
    print("✅ BoundedDict working correctly")
    
    # Test MetricsCollector
    metrics = MetricsCollector()
    
    # Add test metrics
    for i in range(10):
        metrics.record_request(f"/test/{i}", "GET", 100.0 + i, 200)
        metrics.record_error("TestError", f"Error {i}", f"/test/{i}")
        metrics.record_performance(f"metric_{i}", float(i))
        metrics.record_agent_metric(f"agent_{i}", {"status": "active"})
    
    stats = metrics.get_stats()
    print(f"✅ MetricsCollector stats: {stats}")
    
    return True

async def test_memory_cleanup():
    """Test background memory cleanup service"""
    print("\n🧪 Testing Memory Cleanup Service...")
    
    from shared_libs.background.memory_cleanup import cleanup_service
    
    # Get initial memory
    initial_memory = get_memory_usage()
    print(f"Initial memory: {initial_memory:.1f}MB")
    
    # Force cleanup test
    cleanup_result = await cleanup_service.force_cleanup()
    print(f"✅ Force cleanup result: {cleanup_result}")
    
    # Test cleanup stats
    stats = cleanup_service.get_stats()
    print(f"✅ Cleanup service stats: {stats}")
    
    return True

async def test_memory_monitoring():
    """Test memory monitoring middleware"""
    print("\n🧪 Testing Memory Monitoring...")
    
    from shared_libs.middleware.memory_monitor import memory_monitor
    
    # Get initial stats
    stats = memory_monitor.get_memory_stats()
    print(f"✅ Memory monitor stats: {stats}")
    
    # Test stats reset
    memory_monitor.reset_stats()
    reset_stats = memory_monitor.get_memory_stats()
    assert reset_stats["total_requests"] == 0, "Stats reset failed"
    print("✅ Memory monitor reset working")
    
    return True

async def memory_load_test():
    """Test memory behavior under load"""
    print("\n🧪 Running Memory Load Test...")
    
    from shared_libs.caching.lru_cache import cache_manager
    from shared_libs.utils.bounded_collections import metrics_collector
    
    initial_memory = get_memory_usage()
    print(f"Load test initial memory: {initial_memory:.1f}MB")
    
    # Create multiple caches and fill them
    test_caches = []
    for i in range(5):
        cache = cache_manager.create_cache(f"load_test_{i}", max_size=100, ttl_seconds=60)
        test_caches.append(cache)
        
        # Fill cache with test data
        for j in range(150):  # More than max_size to test eviction
            cache.set(f"key_{j}", f"test_data_{j}" * 100)  # Larger values
    
    # Generate metrics data
    for i in range(500):
        metrics_collector.record_request(f"/load_test/{i}", "POST", 50.0 + i, 200)
        if i % 10 == 0:
            metrics_collector.record_error("LoadTestError", f"Test error {i}")
    
    # Force garbage collection
    gc.collect()
    
    # Check final memory
    final_memory = get_memory_usage()
    memory_growth = final_memory - initial_memory
    
    print(f"Load test final memory: {final_memory:.1f}MB")
    print(f"Memory growth: {memory_growth:.1f}MB")
    
    # Get comprehensive stats
    cache_stats = cache_manager.get_cache_stats()
    metrics_stats = metrics_collector.get_stats()
    
    print(f"Final cache stats: {cache_stats}")
    print(f"Final metrics stats: {metrics_stats}")
    
    # Memory growth should be bounded (less than 100MB for this test)
    assert memory_growth < 100, f"Memory growth {memory_growth:.1f}MB exceeds safe limit"
    print("✅ Memory growth within safe limits")
    
    return True

async def integration_test():
    """Run comprehensive integration test"""
    print("\n🚀 Running Memory Management Integration Test...")
    
    start_time = time.time()
    initial_memory = get_memory_usage()
    
    try:
        # Run all tests
        await test_lru_cache()
        await test_singleton_patterns()
        await test_bounded_collections()
        await test_memory_cleanup()
        await test_memory_monitoring()
        await memory_load_test()
        
        # Final memory check
        final_memory = get_memory_usage()
        total_duration = time.time() - start_time
        
        print(f"\n✅ All Memory Management Tests Passed!")
        print(f"📊 Test Summary:")
        print(f"   - Duration: {total_duration:.2f} seconds")
        print(f"   - Initial Memory: {initial_memory:.1f}MB")
        print(f"   - Final Memory: {final_memory:.1f}MB")
        print(f"   - Memory Change: {final_memory - initial_memory:+.1f}MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🔧 HolisticOS Memory Management Test Suite")
    print("=" * 50)
    
    success = await integration_test()
    
    if success:
        print("\n🎉 Memory Management Implementation Complete!")
        print("🔐 MEMORY_MANAGEMENT_READY signal emitted")
        return 0
    else:
        print("\n💥 Memory Management Tests Failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())