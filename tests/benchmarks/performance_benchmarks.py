import asyncio
import time
import psutil
import aiohttp
from typing import Dict, Any
import json
import sys
import os
from datetime import datetime, timedelta

class PerformanceBenchmarks:
    """Establish performance baselines for 0.5 CPU instance"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.benchmarks = {}
        self.process = psutil.Process()
    
    async def benchmark_cold_start(self) -> Dict[str, Any]:
        """Measure cold start performance"""
        print("🥶 Benchmarking cold start performance...")
        
        # Wait for potential cold start
        await asyncio.sleep(2)
        
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/api/health", 
                                     timeout=aiohttp.ClientTimeout(total=30)) as response:
                    cold_start_time = time.time() - start_time
                    response_text = await response.text()
                    
                    return {
                        "cold_start_ms": cold_start_time * 1000,
                        "status_code": response.status,
                        "response_size": len(response_text),
                        "success": response.status == 200
                    }
            except Exception as e:
                return {
                    "cold_start_ms": (time.time() - start_time) * 1000,
                    "status_code": 0,
                    "error": str(e),
                    "success": False
                }
    
    async def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Measure memory usage patterns under load"""
        print("🧠 Benchmarking memory usage patterns...")
        
        # Get baseline memory
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_samples = [initial_memory]
        
        # Simulate realistic load pattern
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # Create concurrent requests to different endpoints
            endpoints = [
                ("POST", "/api/user/bench_user_1/routine/generate", {"archetype": "Foundation Builder"}),
                ("POST", "/api/user/bench_user_2/nutrition/generate", {"archetype": "Peak Performer"}),
                ("POST", "/api/user/bench_user_3/behavior/analyze", {}),
                ("GET", "/api/health", None),
                ("POST", "/api/user/bench_user_4/routine/generate", {"archetype": "Transformation Seeker"}),
            ]
            
            # Run 3 rounds of concurrent requests
            for round_num in range(3):
                round_tasks = []
                for method, endpoint, payload in endpoints:
                    if method == "GET":
                        round_tasks.append(session.get(f"{self.base_url}{endpoint}"))
                    else:
                        round_tasks.append(session.post(f"{self.base_url}{endpoint}", json=payload))
                
                # Execute round and sample memory
                await asyncio.gather(*round_tasks, return_exceptions=True)
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                
                # Brief pause between rounds
                await asyncio.sleep(1)
        
        # Final memory sample after cleanup
        await asyncio.sleep(2)
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_samples.append(final_memory)
        
        return {
            "initial_memory_mb": initial_memory,
            "peak_memory_mb": max(memory_samples),
            "final_memory_mb": final_memory,
            "memory_growth_mb": max(memory_samples) - initial_memory,
            "memory_cleanup_mb": max(memory_samples) - final_memory,
            "samples": memory_samples,
            "average_memory_mb": sum(memory_samples) / len(memory_samples)
        }
    
    async def benchmark_response_times(self) -> Dict[str, Any]:
        """Benchmark response times for each endpoint"""
        print("⏱️ Benchmarking endpoint response times...")
        
        endpoints = {
            "health_check": ("GET", "/api/health", None),
            "routine_generation": ("POST", "/api/user/benchmark_user/routine/generate", 
                                 {"archetype": "Foundation Builder", "preferences": {"focus_areas": ["strength"]}}),
            "nutrition_generation": ("POST", "/api/user/benchmark_user/nutrition/generate", 
                                   {"archetype": "Foundation Builder", "dietary_preferences": ["vegetarian"]}),
            "behavior_analysis": ("POST", "/api/user/benchmark_user/behavior/analyze", {}),
        }
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint_name, (method, path, payload) in endpoints.items():
                times = []
                
                # Run each endpoint 5 times to get average
                for i in range(5):
                    start_time = time.time()
                    
                    try:
                        if method == "GET":
                            async with session.get(f"{self.base_url}{path}",
                                                 timeout=aiohttp.ClientTimeout(total=30)) as response:
                                duration = (time.time() - start_time) * 1000
                                times.append(duration)
                                success = response.status == 200
                        else:
                            async with session.post(f"{self.base_url}{path}", json=payload,
                                                  timeout=aiohttp.ClientTimeout(total=30)) as response:
                                duration = (time.time() - start_time) * 1000
                                times.append(duration)
                                success = response.status == 200
                    except Exception as e:
                        duration = (time.time() - start_time) * 1000
                        times.append(duration)
                        success = False
                
                if times:
                    results[endpoint_name] = {
                        "average_ms": sum(times) / len(times),
                        "min_ms": min(times),
                        "max_ms": max(times),
                        "all_times": times,
                        "success_rate": (sum(1 for t in times if t < 30000) / len(times)) * 100  # Success if < 30s
                    }
        
        return results
    
    async def benchmark_throughput(self) -> Dict[str, Any]:
        """Measure system throughput under concurrent load"""
        print("🚀 Benchmarking system throughput...")
        
        concurrent_levels = [1, 3, 5, 8, 10]
        throughput_results = []
        
        async with aiohttp.ClientSession() as session:
            for concurrent_users in concurrent_levels:
                start_time = time.time()
                
                # Create concurrent requests
                tasks = []
                for i in range(concurrent_users):
                    user_id = f"throughput_user_{i}"
                    task = self._simulate_mini_journey(session, user_id)
                    tasks.append(task)
                
                # Execute all tasks
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                duration = time.time() - start_time
                successful_requests = len([r for r in results if not isinstance(r, Exception)])
                
                throughput_results.append({
                    "concurrent_users": concurrent_users,
                    "duration_seconds": duration,
                    "successful_requests": successful_requests,
                    "requests_per_second": successful_requests / duration if duration > 0 else 0,
                    "success_rate": (successful_requests / concurrent_users) * 100
                })
        
        return {
            "throughput_by_concurrency": throughput_results,
            "max_sustainable_rps": max(r["requests_per_second"] for r in throughput_results),
            "optimal_concurrency": self._find_optimal_concurrency(throughput_results)
        }
    
    async def _simulate_mini_journey(self, session: aiohttp.ClientSession, user_id: str) -> Dict[str, Any]:
        """Simulate a mini user journey for throughput testing"""
        try:
            # Just test health + one generation endpoint
            async with session.get(f"{self.base_url}/api/health") as response:
                health_success = response.status == 200
            
            if health_success:
                async with session.post(
                    f"{self.base_url}/api/user/{user_id}/routine/generate",
                    json={"archetype": "Foundation Builder"}
                ) as response:
                    return {"success": response.status == 200, "user_id": user_id}
            
            return {"success": False, "user_id": user_id}
        except Exception as e:
            return {"success": False, "user_id": user_id, "error": str(e)}
    
    def _find_optimal_concurrency(self, throughput_results: list) -> int:
        """Find the optimal concurrency level based on efficiency"""
        best_efficiency = 0
        optimal_level = 1
        
        for result in throughput_results:
            # Efficiency = (requests_per_second / concurrent_users) * success_rate
            efficiency = (result["requests_per_second"] / result["concurrent_users"]) * (result["success_rate"] / 100)
            
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                optimal_level = result["concurrent_users"]
        
        return optimal_level
    
    async def benchmark_cost_efficiency(self) -> Dict[str, Any]:
        """Estimate API costs under various load scenarios"""
        print("💰 Benchmarking cost efficiency...")
        
        # Estimated OpenAI API costs (GPT-4 pricing)
        cost_estimates = {
            "routine_generation": 0.03,  # ~1000 tokens output
            "nutrition_generation": 0.025, # ~800 tokens output
            "behavior_analysis": 0.035,   # ~1200 tokens output + context
            "insights_generation": 0.015,  # ~500 tokens output
            "health_check": 0.0           # No API cost
        }
        
        # Simulate different usage patterns
        usage_scenarios = {
            "light_usage": {
                "users_per_day": 50,
                "avg_sessions_per_user": 1,
                "endpoints_per_session": {
                    "routine_generation": 1,
                    "nutrition_generation": 0.5,  # Not every session
                    "behavior_analysis": 0.3,
                    "insights_generation": 0.2,
                    "health_check": 3  # Multiple health checks
                }
            },
            "moderate_usage": {
                "users_per_day": 200,
                "avg_sessions_per_user": 1.5,
                "endpoints_per_session": {
                    "routine_generation": 1.2,
                    "nutrition_generation": 0.8,
                    "behavior_analysis": 0.6,
                    "insights_generation": 0.4,
                    "health_check": 4
                }
            },
            "heavy_usage": {
                "users_per_day": 500,
                "avg_sessions_per_user": 2,
                "endpoints_per_session": {
                    "routine_generation": 1.5,
                    "nutrition_generation": 1.2,
                    "behavior_analysis": 1.0,
                    "insights_generation": 0.8,
                    "health_check": 6
                }
            }
        }
        
        cost_projections = {}
        
        for scenario_name, scenario in usage_scenarios.items():
            daily_requests = {}
            daily_cost = 0
            
            total_sessions = scenario["users_per_day"] * scenario["avg_sessions_per_user"]
            
            for endpoint, requests_per_session in scenario["endpoints_per_session"].items():
                total_requests = total_sessions * requests_per_session
                endpoint_cost = total_requests * cost_estimates[endpoint]
                
                daily_requests[endpoint] = total_requests
                daily_cost += endpoint_cost
            
            cost_projections[scenario_name] = {
                "daily_requests": daily_requests,
                "daily_cost_usd": daily_cost,
                "monthly_cost_usd": daily_cost * 30,
                "cost_per_user_per_day": daily_cost / scenario["users_per_day"],
                "total_daily_api_calls": sum(daily_requests.values())
            }
        
        return {
            "cost_estimates_per_call": cost_estimates,
            "usage_scenarios": cost_projections,
            "recommended_rate_limits": self._calculate_rate_limits(cost_projections)
        }
    
    def _calculate_rate_limits(self, cost_projections: Dict) -> Dict[str, Any]:
        """Calculate recommended rate limits based on cost projections"""
        heavy_usage = cost_projections["heavy_usage"]
        daily_api_calls = heavy_usage["total_daily_api_calls"]
        
        # Distribute calls across 24 hours with peak hour considerations
        # Assume 4x peak traffic during 6 peak hours
        avg_calls_per_hour = daily_api_calls / 24
        peak_calls_per_hour = avg_calls_per_hour * 4
        
        return {
            "calls_per_hour_average": avg_calls_per_hour,
            "calls_per_hour_peak": peak_calls_per_hour,
            "recommended_rate_limit_per_minute": peak_calls_per_hour / 60 * 1.2,  # 20% buffer
            "daily_cost_cap_recommended": cost_projections["heavy_usage"]["daily_cost_usd"] * 1.5
        }
    
    async def benchmark_resource_utilization(self) -> Dict[str, Any]:
        """Benchmark CPU and memory utilization patterns"""
        print("📊 Benchmarking resource utilization...")
        
        # Get baseline metrics
        baseline_cpu = psutil.cpu_percent(interval=1)
        baseline_memory = self.process.memory_info().rss / 1024 / 1024
        
        resource_samples = []
        
        # Run load and sample resources every second for 30 seconds
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            
            # Create continuous background load
            background_tasks = []
            for i in range(3):  # 3 concurrent background requests
                background_tasks.append(
                    self._continuous_load(session, f"resource_user_{i}", duration=30)
                )
            
            # Start background load
            load_task = asyncio.create_task(asyncio.gather(*background_tasks, return_exceptions=True))
            
            # Sample resources every second
            while time.time() - start_time < 30:
                sample_time = time.time()
                cpu_percent = psutil.cpu_percent()
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                
                resource_samples.append({
                    "timestamp": sample_time,
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_mb
                })
                
                await asyncio.sleep(1)
            
            # Wait for background tasks to complete
            await load_task
        
        # Analyze resource usage
        cpu_values = [s["cpu_percent"] for s in resource_samples]
        memory_values = [s["memory_mb"] for s in resource_samples]
        
        return {
            "baseline": {
                "cpu_percent": baseline_cpu,
                "memory_mb": baseline_memory
            },
            "under_load": {
                "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
                "peak_cpu_percent": max(cpu_values),
                "avg_memory_mb": sum(memory_values) / len(memory_values),
                "peak_memory_mb": max(memory_values)
            },
            "resource_efficiency": {
                "cpu_utilization_score": min(100, (sum(cpu_values) / len(cpu_values)) / 50 * 100),  # 50% CPU = 100% score
                "memory_efficiency_score": max(0, 100 - (max(memory_values) / 512 * 100))  # 512MB = 0% score
            },
            "samples": resource_samples
        }
    
    async def _continuous_load(self, session: aiohttp.ClientSession, user_id: str, duration: int):
        """Generate continuous load for resource testing"""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # Alternate between endpoints
                if int(time.time()) % 2 == 0:
                    await session.post(
                        f"{self.base_url}/api/user/{user_id}/routine/generate",
                        json={"archetype": "Foundation Builder"}
                    )
                else:
                    await session.get(f"{self.base_url}/api/health")
                
                await asyncio.sleep(2)  # Request every 2 seconds
            except Exception:
                pass  # Continue load generation even if requests fail
    
    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        results = {
            "benchmark_timestamp": time.time(),
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "available_memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "cpu_count": psutil.cpu_count()
            }
        }
        
        print("🏃 Running comprehensive performance benchmarks...")
        print("This may take several minutes...")
        
        try:
            results["cold_start"] = await self.benchmark_cold_start()
            results["memory_usage"] = await self.benchmark_memory_usage()
            results["response_times"] = await self.benchmark_response_times()
            results["throughput"] = await self.benchmark_throughput()
            results["cost_efficiency"] = await self.benchmark_cost_efficiency()
            results["resource_utilization"] = await self.benchmark_resource_utilization()
            
            # Generate overall assessment
            results["assessment"] = self._generate_performance_assessment(results)
            
        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Benchmarking failed: {e}")
        
        return results
    
    def _generate_performance_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall performance assessment"""
        assessment = {
            "overall_score": 0,
            "production_ready": False,
            "recommendations": [],
            "alerts": []
        }
        
        score_components = []
        
        # Assess cold start
        if "cold_start" in results and results["cold_start"].get("success"):
            cold_start_ms = results["cold_start"]["cold_start_ms"]
            if cold_start_ms < 2000:  # < 2 seconds
                score_components.append(("cold_start", 100))
            elif cold_start_ms < 5000:  # < 5 seconds
                score_components.append(("cold_start", 75))
            else:
                score_components.append(("cold_start", 50))
                assessment["alerts"].append(f"Slow cold start: {cold_start_ms:.0f}ms")
        
        # Assess memory usage
        if "memory_usage" in results:
            peak_memory = results["memory_usage"]["peak_memory_mb"]
            if peak_memory < 300:
                score_components.append(("memory", 100))
            elif peak_memory < 400:
                score_components.append(("memory", 85))
            elif peak_memory < 500:
                score_components.append(("memory", 70))
                assessment["recommendations"].append("Monitor memory usage in production")
            else:
                score_components.append(("memory", 50))
                assessment["alerts"].append(f"High memory usage: {peak_memory:.1f}MB")
        
        # Assess response times
        if "response_times" in results:
            avg_response_times = [
                results["response_times"].get(endpoint, {}).get("average_ms", 0)
                for endpoint in ["routine_generation", "nutrition_generation", "behavior_analysis"]
            ]
            
            if avg_response_times:
                max_response_time = max(avg_response_times)
                if max_response_time < 3000:  # < 3 seconds
                    score_components.append(("response_times", 100))
                elif max_response_time < 5000:  # < 5 seconds
                    score_components.append(("response_times", 85))
                elif max_response_time < 10000:  # < 10 seconds
                    score_components.append(("response_times", 70))
                else:
                    score_components.append(("response_times", 50))
                    assessment["alerts"].append(f"Slow response times: {max_response_time:.0f}ms")
        
        # Assess throughput
        if "throughput" in results:
            max_rps = results["throughput"]["max_sustainable_rps"]
            if max_rps > 1.0:  # > 1 request per second
                score_components.append(("throughput", 100))
            elif max_rps > 0.5:
                score_components.append(("throughput", 75))
            else:
                score_components.append(("throughput", 50))
                assessment["alerts"].append(f"Low throughput: {max_rps:.2f} RPS")
        
        # Calculate overall score
        if score_components:
            assessment["overall_score"] = sum(score for _, score in score_components) / len(score_components)
        
        # Determine production readiness
        assessment["production_ready"] = (
            assessment["overall_score"] >= 75 and
            len(assessment["alerts"]) == 0
        )
        
        # Add general recommendations
        if assessment["overall_score"] < 85:
            assessment["recommendations"].extend([
                "Consider implementing connection pooling",
                "Add response caching for frequently requested data",
                "Monitor resource usage in production"
            ])
        
        return assessment

async def main():
    """Main benchmark execution function"""
    benchmarks = PerformanceBenchmarks()
    results = await benchmarks.run_all_benchmarks()
    
    # Save detailed results
    with open("performance_benchmarks.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate human-readable summary
    generate_benchmark_summary(results)
    
    print("📊 Benchmark results saved to:")
    print("  - performance_benchmarks.json (detailed)")
    print("  - benchmark_summary.txt (summary)")
    
    return results

def generate_benchmark_summary(results: Dict[str, Any]):
    """Generate human-readable benchmark summary"""
    summary = []
    summary.append("HolisticOS MVP Performance Benchmarks")
    summary.append("=" * 40)
    summary.append(f"Test Date: {datetime.fromtimestamp(results.get('benchmark_timestamp', time.time()))}")
    summary.append("")
    
    # System Info
    if "system_info" in results:
        info = results["system_info"]
        summary.append("System Information:")
        summary.append(f"  Python: {info.get('python_version', 'Unknown').split()[0]}")
        summary.append(f"  Platform: {info.get('platform', 'Unknown')}")
        summary.append(f"  Memory: {info.get('available_memory_gb', 0):.1f} GB")
        summary.append(f"  CPU Cores: {info.get('cpu_count', 'Unknown')}")
        summary.append("")
    
    # Cold Start
    if "cold_start" in results and results["cold_start"].get("success"):
        cold_start = results["cold_start"]
        summary.append("Cold Start Performance:")
        summary.append(f"  ✓ Time: {cold_start['cold_start_ms']:.0f}ms")
        summary.append(f"  ✓ Status: {'PASS' if cold_start['cold_start_ms'] < 5000 else 'SLOW'}")
        summary.append("")
    
    # Memory Usage
    if "memory_usage" in results:
        memory = results["memory_usage"]
        summary.append("Memory Usage:")
        summary.append(f"  ✓ Baseline: {memory['initial_memory_mb']:.1f} MB")
        summary.append(f"  ✓ Peak: {memory['peak_memory_mb']:.1f} MB")
        summary.append(f"  ✓ Growth: {memory['memory_growth_mb']:.1f} MB")
        summary.append(f"  ✓ Status: {'PASS' if memory['peak_memory_mb'] <= 400 else 'HIGH'}")
        summary.append("")
    
    # Response Times
    if "response_times" in results:
        summary.append("Response Times:")
        for endpoint, data in results["response_times"].items():
            summary.append(f"  {endpoint}:")
            summary.append(f"    Average: {data['average_ms']:.0f}ms")
            summary.append(f"    Range: {data['min_ms']:.0f}-{data['max_ms']:.0f}ms")
            summary.append(f"    Success: {data['success_rate']:.1f}%")
        summary.append("")
    
    # Throughput
    if "throughput" in results:
        throughput = results["throughput"]
        summary.append("Throughput Analysis:")
        summary.append(f"  ✓ Max RPS: {throughput['max_sustainable_rps']:.2f}")
        summary.append(f"  ✓ Optimal Concurrency: {throughput['optimal_concurrency']} users")
        summary.append("")
    
    # Cost Analysis
    if "cost_efficiency" in results:
        cost = results["cost_efficiency"]["usage_scenarios"]["moderate_usage"]
        summary.append("Cost Projections (Moderate Usage):")
        summary.append(f"  ✓ Daily Cost: ${cost['daily_cost_usd']:.2f}")
        summary.append(f"  ✓ Monthly Cost: ${cost['monthly_cost_usd']:.2f}")
        summary.append(f"  ✓ Cost per User: ${cost['cost_per_user_per_day']:.3f}/day")
        summary.append("")
    
    # Overall Assessment
    if "assessment" in results:
        assessment = results["assessment"]
        summary.append("Production Readiness Assessment:")
        summary.append(f"  ✓ Overall Score: {assessment['overall_score']:.1f}/100")
        summary.append(f"  ✓ Production Ready: {'YES' if assessment['production_ready'] else 'NO'}")
        
        if assessment["alerts"]:
            summary.append("  ⚠️ Alerts:")
            for alert in assessment["alerts"]:
                summary.append(f"    - {alert}")
        
        if assessment["recommendations"]:
            summary.append("  💡 Recommendations:")
            for rec in assessment["recommendations"]:
                summary.append(f"    - {rec}")
        
        summary.append("")
    
    # Resource Utilization
    if "resource_utilization" in results:
        resources = results["resource_utilization"]
        summary.append("Resource Utilization:")
        summary.append(f"  ✓ CPU Peak: {resources['under_load']['peak_cpu_percent']:.1f}%")
        summary.append(f"  ✓ Memory Peak: {resources['under_load']['peak_memory_mb']:.1f} MB")
        summary.append(f"  ✓ CPU Score: {resources['resource_efficiency']['cpu_utilization_score']:.1f}/100")
        summary.append(f"  ✓ Memory Score: {resources['resource_efficiency']['memory_efficiency_score']:.1f}/100")
    
    # Write summary to file
    with open("benchmark_summary.txt", "w") as f:
        f.write("\n".join(summary))

if __name__ == "__main__":
    asyncio.run(main())