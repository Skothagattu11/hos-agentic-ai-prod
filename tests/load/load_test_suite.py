import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
import json
import psutil
import sys
import os

@dataclass
class LoadTestResult:
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    p95_response_time: float
    p99_response_time: float
    errors: List[str]
    throughput_rps: float

class HolisticOSLoadTester:
    """Comprehensive load testing for HolisticOS MVP"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.results = []
        self.memory_samples = []
    
    async def simulate_user_journey(self, user_id: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Simulate complete user journey"""
        start_time = time.time()
        journey_results = {"user_id": user_id, "steps": []}
        
        # Step 1: Health check
        step_result = await self._make_request(
            session, "GET", "/api/health", expected_status=200
        )
        journey_results["steps"].append({"step": "health_check", **step_result})
        
        if not step_result["success"]:
            journey_results["total_duration"] = time.time() - start_time
            journey_results["error"] = "Health check failed"
            return journey_results
        
        # Step 2: Routine generation
        routine_payload = {
            "archetype": "Foundation Builder",
            "preferences": {"focus_areas": ["strength", "cardio"]}
        }
        step_result = await self._make_request(
            session, "POST", f"/api/user/{user_id}/routine/generate",
            payload=routine_payload, expected_status=200
        )
        journey_results["steps"].append({"step": "routine_generation", **step_result})
        
        # Step 3: Nutrition generation
        nutrition_payload = {
            "archetype": "Foundation Builder",
            "dietary_preferences": ["vegetarian"]
        }
        step_result = await self._make_request(
            session, "POST", f"/api/user/{user_id}/nutrition/generate",
            payload=nutrition_payload, expected_status=200
        )
        journey_results["steps"].append({"step": "nutrition_generation", **step_result})
        
        # Step 4: Behavior analysis
        step_result = await self._make_request(
            session, "POST", f"/api/user/{user_id}/behavior/analyze",
            payload={}, expected_status=200
        )
        journey_results["steps"].append({"step": "behavior_analysis", **step_result})
        
        journey_results["total_duration"] = time.time() - start_time
        return journey_results
    
    async def _make_request(self, session: aiohttp.ClientSession, method: str, 
                          endpoint: str, payload: dict = None, expected_status: int = 200) -> Dict:
        """Make HTTP request and measure performance"""
        start_time = time.time()
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    duration = time.time() - start_time
                    content = await response.text()
                    return {
                        "success": response.status == expected_status,
                        "status_code": response.status,
                        "duration_ms": duration * 1000,
                        "response_size": len(content),
                        "error": None if response.status == expected_status else content[:200]
                    }
            else:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    duration = time.time() - start_time
                    content = await response.text()
                    return {
                        "success": response.status == expected_status,
                        "status_code": response.status,
                        "duration_ms": duration * 1000,
                        "response_size": len(content),
                        "error": None if response.status == expected_status else content[:200]
                    }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "duration_ms": (time.time() - start_time) * 1000,
                "response_size": 0,
                "error": str(e)
            }
    
    def _sample_memory_usage(self):
        """Sample current memory usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            self.memory_samples.append({
                "timestamp": time.time(),
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024
            })
        except Exception as e:
            print(f"Warning: Could not sample memory: {e}")
    
    async def run_concurrent_user_test(self, concurrent_users: int = 10, 
                                     test_duration_minutes: int = 5) -> Dict[str, Any]:
        """Test with concurrent users over time"""
        print(f"🚀 Starting load test: {concurrent_users} concurrent users for {test_duration_minutes} minutes")
        
        start_time = time.time()
        end_time = start_time + (test_duration_minutes * 60)
        
        user_results = []
        
        # Start memory monitoring
        memory_monitor_task = asyncio.create_task(self._monitor_memory())
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=30)
        ) as session:
            while time.time() < end_time:
                # Create batch of concurrent users
                tasks = []
                for i in range(concurrent_users):
                    user_id = f"load_test_user_{int(time.time())}_{i}"
                    tasks.append(self.simulate_user_journey(user_id, session))
                
                # Execute batch
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        user_results.append({"error": str(result)})
                    else:
                        user_results.append(result)
                
                # Brief pause between batches
                await asyncio.sleep(2)
        
        # Stop memory monitoring
        memory_monitor_task.cancel()
        
        return self._analyze_load_test_results(user_results, concurrent_users, test_duration_minutes)
    
    async def _monitor_memory(self):
        """Monitor memory usage during test"""
        try:
            while True:
                self._sample_memory_usage()
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
    
    def _analyze_load_test_results(self, user_results: List[Dict], 
                                 concurrent_users: int, duration_minutes: int) -> Dict[str, Any]:
        """Analyze load test results"""
        total_users = len(user_results)
        successful_journeys = len([r for r in user_results if "error" not in r])
        failed_journeys = total_users - successful_journeys
        
        # Analyze response times by step
        step_analysis = {}
        for result in user_results:
            if "steps" in result:
                for step in result["steps"]:
                    step_name = step["step"]
                    if step_name not in step_analysis:
                        step_analysis[step_name] = []
                    step_analysis[step_name].append(step["duration_ms"])
        
        # Calculate percentiles for each step
        step_stats = {}
        for step_name, durations in step_analysis.items():
            if durations:
                step_stats[step_name] = {
                    "avg_ms": statistics.mean(durations),
                    "p95_ms": statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations),
                    "p99_ms": statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else max(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "total_requests": len(durations)
                }
        
        # Analyze memory usage
        memory_stats = {}
        if self.memory_samples:
            rss_values = [sample["rss_mb"] for sample in self.memory_samples]
            memory_stats = {
                "peak_memory_mb": max(rss_values),
                "avg_memory_mb": statistics.mean(rss_values),
                "min_memory_mb": min(rss_values),
                "samples": len(self.memory_samples)
            }
        
        return {
            "test_config": {
                "concurrent_users": concurrent_users,
                "duration_minutes": duration_minutes,
                "total_user_journeys": total_users
            },
            "overall_results": {
                "successful_journeys": successful_journeys,
                "failed_journeys": failed_journeys,
                "success_rate": (successful_journeys / total_users) * 100 if total_users > 0 else 0,
                "throughput_journeys_per_minute": total_users / duration_minutes
            },
            "step_performance": step_stats,
            "memory_usage": memory_stats,
            "errors": [r.get("error", "") for r in user_results if "error" in r]
        }
    
    async def run_stress_test(self) -> Dict[str, Any]:
        """Test system limits by gradually increasing load"""
        print("🔥 Running stress test to find system limits")
        
        stress_results = []
        user_counts = [1, 5, 10, 15, 20, 25, 30]  # Gradually increase load
        
        for user_count in user_counts:
            print(f"Testing with {user_count} concurrent users...")
            self.memory_samples = []  # Reset memory samples for each test
            
            result = await self.run_concurrent_user_test(
                concurrent_users=user_count, 
                test_duration_minutes=2  # Shorter duration for stress test
            )
            
            stress_results.append({
                "concurrent_users": user_count,
                "success_rate": result["overall_results"]["success_rate"],
                "avg_response_time": result["step_performance"].get("routine_generation", {}).get("avg_ms", 0),
                "peak_memory_mb": result["memory_usage"].get("peak_memory_mb", 0)
            })
            
            # Stop if success rate drops below 80% or memory exceeds 450MB
            if (result["overall_results"]["success_rate"] < 80 or 
                result["memory_usage"].get("peak_memory_mb", 0) > 450):
                print(f"⚠️ System degraded at {user_count} users, stopping stress test")
                break
            
            # Brief pause between stress levels
            await asyncio.sleep(10)
        
        return {
            "stress_test_results": stress_results,
            "recommended_max_users": self._find_recommended_limit(stress_results)
        }
    
    def _find_recommended_limit(self, stress_results: List[Dict]) -> int:
        """Find recommended user limit based on performance degradation"""
        for result in stress_results:
            if (result["success_rate"] < 95 or 
                result["avg_response_time"] > 10000 or  # 10 second response time
                result["peak_memory_mb"] > 400):  # Memory limit
                return max(1, result["concurrent_users"] - 5)  # Back off 5 users
        
        return stress_results[-1]["concurrent_users"] if stress_results else 1
    
    async def run_endurance_test(self, duration_hours: int = 1) -> Dict[str, Any]:
        """Test system stability over extended period"""
        print(f"⏱️ Running endurance test for {duration_hours} hour(s)")
        
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        test_results = []
        memory_samples = []
        
        while time.time() < end_time:
            # Run a short load test every 10 minutes
            result = await self.run_concurrent_user_test(
                concurrent_users=5,
                test_duration_minutes=2
            )
            
            test_results.append({
                "timestamp": time.time(),
                "success_rate": result["overall_results"]["success_rate"],
                "avg_response_time": result["step_performance"].get("routine_generation", {}).get("avg_ms", 0),
                "memory_usage": result["memory_usage"]
            })
            
            # Wait 10 minutes before next test
            await asyncio.sleep(480)  # 8 minutes (2 min test + 8 min wait = 10 min cycle)
        
        return {
            "endurance_results": test_results,
            "total_duration_hours": duration_hours,
            "stability_score": self._calculate_stability_score(test_results)
        }
    
    def _calculate_stability_score(self, test_results: List[Dict]) -> float:
        """Calculate system stability score based on consistency"""
        if not test_results:
            return 0.0
        
        success_rates = [r["success_rate"] for r in test_results]
        response_times = [r["avg_response_time"] for r in test_results]
        
        # Stability is based on consistency of success rates and response times
        success_rate_std = statistics.stdev(success_rates) if len(success_rates) > 1 else 0
        response_time_std = statistics.stdev(response_times) if len(response_times) > 1 else 0
        
        # Lower standard deviation = higher stability
        stability_score = max(0, 100 - (success_rate_std * 10) - (response_time_std / 1000))
        return min(100, stability_score)

async def run_production_load_tests():
    """Run comprehensive load testing suite"""
    tester = HolisticOSLoadTester()
    
    print("=" * 60)
    print("HolisticOS MVP Production Load Testing")
    print("=" * 60)
    
    all_results = {
        "test_timestamp": time.time(),
        "system_info": {
            "python_version": sys.version,
            "platform": sys.platform,
            "available_memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024
        }
    }
    
    try:
        # Test 1: Normal load test (10 users, 5 minutes)
        print("📊 Running normal load test...")
        normal_load_result = await tester.run_concurrent_user_test(
            concurrent_users=10, 
            test_duration_minutes=5
        )
        all_results["normal_load"] = normal_load_result
        
        print("✅ Normal Load Test Results:")
        print(f"  Success Rate: {normal_load_result['overall_results']['success_rate']:.1f}%")
        print(f"  Peak Memory: {normal_load_result['memory_usage'].get('peak_memory_mb', 0):.1f} MB")
        
        # Test 2: Stress test (find limits)
        print("\n🔥 Running stress test...")
        stress_test_result = await tester.run_stress_test()
        all_results["stress_test"] = stress_test_result
        
        print("✅ Stress Test Results:")
        print(f"  Recommended Max Users: {stress_test_result['recommended_max_users']}")
        
        # Test 3: Brief endurance test (15 minutes)
        print("\n⏱️ Running brief endurance test...")
        endurance_result = await tester.run_endurance_test(duration_hours=0.25)  # 15 minutes
        all_results["endurance_test"] = endurance_result
        
        print("✅ Endurance Test Results:")
        print(f"  Stability Score: {endurance_result['stability_score']:.1f}/100")
        
    except Exception as e:
        print(f"❌ Load testing failed: {e}")
        all_results["error"] = str(e)
    
    # Generate comprehensive report
    with open("load_test_report.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    # Generate summary report
    generate_load_test_summary(all_results)
    
    print("\n✅ Load testing complete. Reports saved to:")
    print("  - load_test_report.json (detailed)")
    print("  - load_test_summary.txt (summary)")
    
    return all_results

def generate_load_test_summary(results: Dict[str, Any]):
    """Generate human-readable summary report"""
    summary = []
    summary.append("HolisticOS MVP Load Testing Summary")
    summary.append("=" * 40)
    summary.append(f"Test Date: {time.ctime(results.get('test_timestamp', time.time()))}")
    summary.append("")
    
    # Normal Load Test Summary
    if "normal_load" in results:
        normal = results["normal_load"]
        summary.append("Normal Load Test (10 users, 5 minutes):")
        summary.append(f"  ✓ Success Rate: {normal['overall_results']['success_rate']:.1f}%")
        summary.append(f"  ✓ Peak Memory: {normal['memory_usage'].get('peak_memory_mb', 0):.1f} MB")
        summary.append(f"  ✓ Throughput: {normal['overall_results']['throughput_journeys_per_minute']:.1f} journeys/min")
        summary.append("")
    
    # Stress Test Summary
    if "stress_test" in results:
        stress = results["stress_test"]
        summary.append("Stress Test Results:")
        summary.append(f"  ✓ Recommended Max Users: {stress['recommended_max_users']}")
        
        # Show progression
        for result in stress["stress_test_results"]:
            summary.append(f"    {result['concurrent_users']} users: {result['success_rate']:.1f}% success, {result['peak_memory_mb']:.1f} MB peak")
        summary.append("")
    
    # Endurance Test Summary
    if "endurance_test" in results:
        endurance = results["endurance_test"]
        summary.append("Endurance Test Results:")
        summary.append(f"  ✓ Stability Score: {endurance['stability_score']:.1f}/100")
        summary.append(f"  ✓ Test Duration: {endurance['total_duration_hours']} hours")
        summary.append("")
    
    # Production Readiness Assessment
    summary.append("Production Readiness Assessment:")
    
    # Assess based on results
    if "normal_load" in results:
        normal = results["normal_load"]
        success_rate = normal['overall_results']['success_rate']
        peak_memory = normal['memory_usage'].get('peak_memory_mb', 0)
        
        if success_rate >= 95:
            summary.append("  ✅ Success Rate: PASS (≥95%)")
        else:
            summary.append("  ❌ Success Rate: FAIL (<95%)")
        
        if peak_memory <= 400:
            summary.append("  ✅ Memory Usage: PASS (≤400MB)")
        else:
            summary.append("  ❌ Memory Usage: FAIL (>400MB)")
    
    if "stress_test" in results:
        max_users = results["stress_test"]["recommended_max_users"]
        if max_users >= 15:
            summary.append("  ✅ Concurrent Users: PASS (≥15 users)")
        else:
            summary.append("  ❌ Concurrent Users: FAIL (<15 users)")
    
    summary.append("")
    summary.append("Recommendations:")
    
    if "stress_test" in results:
        max_users = results["stress_test"]["recommended_max_users"]
        summary.append(f"  • Set rate limiting to {max_users} concurrent users")
    
    if "normal_load" in results:
        peak_memory = results["normal_load"]["memory_usage"].get("peak_memory_mb", 0)
        if peak_memory > 300:
            summary.append("  • Monitor memory usage closely in production")
            summary.append("  • Consider implementing memory cleanup routines")
    
    # Write summary to file
    with open("load_test_summary.txt", "w") as f:
        f.write("\n".join(summary))

if __name__ == "__main__":
    asyncio.run(run_production_load_tests())