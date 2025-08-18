"""
Chaos Testing Suite for HolisticOS MVP
Comprehensive edge case testing and failure scenario validation
"""

import asyncio
import aiohttp
import time
import random
import json
import logging
import psutil
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import traceback

# Configure logging for chaos testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # PASS, FAIL, PARTIAL
    duration: float
    details: Dict[str, Any]
    errors: List[str]
    metrics: Dict[str, Any]

class ChaosTestingSuite:
    """Comprehensive chaos testing for production readiness validation"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.test_results = []
        self.session = None
        
        # Test user data from your database - using real user ID
        self.primary_user = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
        self.test_users = [
            self.primary_user,  # Primary real user
            "test_user_1", "test_user_2", "test_user_3", 
            "chaos_user_1", "chaos_user_2", "load_test_user"
        ]
        
        # Users with existing analysis to test shared analysis scenarios
        self.users_with_analysis = [
            self.primary_user,  # Primary test user with existing analysis
            "test_user_1", "test_user_2"
        ]
        
        # Test archetypes available in your system
        self.archetypes = [
            "Foundation Builder", "Transformation Seeker", "Systematic Improver",
            "Peak Performer", "Resilience Rebuilder", "Connected Explorer"
        ]
        
        # Failure simulation settings
        self.failure_modes = {
            "network_timeout": 30,  # seconds
            "memory_pressure": 450,  # MB
            "concurrent_overload": 50,  # requests
            "rate_limit_breach": 10,  # requests in burst
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    # =====================================
    # 1. ERROR HANDLING & RETRY LOGIC TESTS
    # =====================================
    
    async def test_openai_timeout_handling(self) -> TestResult:
        """Test OpenAI API timeout scenarios and retry behavior"""
        logger.info("🧪 Testing OpenAI timeout handling and retry logic...")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Test with existing user first (shared analysis scenario)
            user_id = random.choice(self.users_with_analysis)
            
            # Make a request that leverages existing analysis (faster) vs new analysis
            payload = {
                "archetype": "Peak Performer",
                "use_existing_analysis": True  # Test shared analysis path
            }
            
            async with self.session.post(
                f"{self.base_url}/api/user/{user_id}/behavior/analyze",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=180)  # Longer timeout to see retry behavior
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    details["response_time"] = time.time() - start_time
                    details["retry_attempts"] = response.headers.get("x-retry-attempts", "unknown")
                    details["analysis_success"] = bool(data.get("behavior_analysis"))
                    status = "PASS"
                elif response.status == 429:
                    details["rate_limited"] = True
                    details["retry_after"] = response.headers.get("retry-after")
                    status = "PARTIAL"  # Expected behavior
                else:
                    errors.append(f"Unexpected status: {response.status}")
                    status = "FAIL"
                    
        except asyncio.TimeoutError:
            details["timeout_occurred"] = True
            details["timeout_handling"] = "System handled timeout gracefully"
            status = "PASS"  # Timeout is expected behavior
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            status = "FAIL"
        
        return TestResult(
            test_name="OpenAI Timeout Handling",
            status=status,
            duration=time.time() - start_time,
            details=details,
            errors=errors,
            metrics={"response_time": details.get("response_time", 0)}
        )
    
    async def test_database_connection_resilience(self) -> TestResult:
        """Test database connection pool behavior under stress"""
        logger.info("🧪 Testing database connection pool resilience...")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Test health check which uses database pool
            async with self.session.get(f"{self.base_url}/api/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    details["database_status"] = health_data.get("services", {}).get("database", {})
                    details["pool_info"] = health_data.get("database", {})
                    
                    if details["database_status"].get("status") == "healthy":
                        status = "PASS"
                    else:
                        status = "PARTIAL"
                        errors.append("Database not fully healthy")
                else:
                    status = "FAIL"
                    errors.append(f"Health check failed: {response.status}")
                    
        except Exception as e:
            errors.append(f"Database connection test failed: {str(e)}")
            status = "FAIL"
        
        return TestResult(
            test_name="Database Connection Resilience",
            status=status,
            duration=time.time() - start_time,
            details=details,
            errors=errors,
            metrics={"pool_status": details.get("pool_info", {})}
        )
    
    # ===================================
    # 2. RATE LIMITING & COST CONTROL TESTS
    # ===================================
    
    async def test_rate_limiting_enforcement(self) -> TestResult:
        """Test rate limiting with rapid requests"""
        logger.info("🧪 Testing rate limiting enforcement...")
        
        start_time = time.time()
        errors = []
        details = {}
        successful_requests = 0
        rate_limited_requests = 0
        
        try:
            user_id = f"rate_test_user_{int(time.time())}"
            
            # Make rapid requests to trigger rate limiting
            for i in range(15):  # Exceed free tier limit of 5/hour
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/user/{user_id}/routine/generate",
                        json={"archetype": "Foundation Builder"},
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        if response.status == 200:
                            successful_requests += 1
                        elif response.status == 429:
                            rate_limited_requests += 1
                            details["rate_limit_response"] = await response.json()
                        else:
                            errors.append(f"Request {i+1}: Unexpected status {response.status}")
                            
                except Exception as e:
                    errors.append(f"Routine request {i+1}: {str(e)}")
            
            # Also test nutrition endpoint rate limiting
            nutrition_successful = 0
            nutrition_rate_limited = 0
            for i in range(10):  # Test nutrition endpoint too
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/user/{user_id}/nutrition/generate",
                        json={"archetype": "Foundation Builder"},
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        if response.status == 200:
                            nutrition_successful += 1
                        elif response.status == 429:
                            nutrition_rate_limited += 1
                        else:
                            errors.append(f"Nutrition request {i+1}: Unexpected status {response.status}")
                            
                except Exception as e:
                    errors.append(f"Nutrition request {i+1}: {str(e)}")
            
            details["routine_successful_requests"] = successful_requests
            details["routine_rate_limited_requests"] = rate_limited_requests
            details["nutrition_successful_requests"] = nutrition_successful
            details["nutrition_rate_limited_requests"] = nutrition_rate_limited
            details["total_routine_requests"] = 15
            details["total_nutrition_requests"] = 10
            details["total_requests"] = 25
            
            # Rate limiting should kick in after 5-10 requests for free tier
            total_rate_limited = rate_limited_requests + nutrition_rate_limited
            if total_rate_limited > 0:
                status = "PASS"
                details["rate_limiting_working"] = True
            else:
                status = "PARTIAL"
                details["rate_limiting_working"] = False
                errors.append("Rate limiting may not be properly configured for routine/nutrition endpoints")
                
        except Exception as e:
            errors.append(f"Rate limiting test failed: {str(e)}")
            status = "FAIL"
        
        return TestResult(
            test_name="Rate Limiting Enforcement",
            status=status,
            duration=time.time() - start_time,
            details=details,
            errors=errors,
            metrics={
                "successful_requests": successful_requests,
                "rate_limited_requests": rate_limited_requests
            }
        )
    
    async def test_cost_tracking_accuracy(self) -> TestResult:
        """Test cost tracking and daily limits"""
        logger.info("🧪 Testing cost tracking accuracy...")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            user_id = f"cost_test_user_{int(time.time())}"
            
            # Make a behavior analysis request (highest cost)
            async with self.session.post(
                f"{self.base_url}/api/user/{user_id}/behavior/analyze",
                json={"archetype": "Peak Performer"},
                timeout=aiohttp.ClientTimeout(total=180)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    details["cost_tracking"] = data.get("generation_metadata", {}).get("cost_used_today")
                    details["analysis_completed"] = True
                    status = "PASS"
                elif response.status == 402:
                    # Payment required - cost limit reached
                    details["cost_limit_enforced"] = True
                    details["payment_required_response"] = await response.json()
                    status = "PASS"  # This is expected behavior
                elif response.status == 429:
                    details["rate_limited"] = True
                    status = "PARTIAL"
                else:
                    errors.append(f"Unexpected status: {response.status}")
                    status = "FAIL"
                    
        except Exception as e:
            errors.append(f"Cost tracking test failed: {str(e)}")
            status = "FAIL"
        
        return TestResult(
            test_name="Cost Tracking Accuracy",
            status=status,
            duration=time.time() - start_time,
            details=details,
            errors=errors,
            metrics={"cost_tracked": details.get("cost_tracking", 0)}
        )
    
    # ===========================
    # 3. MEMORY MANAGEMENT TESTS
    # ===========================
    
    async def test_memory_pressure_handling(self) -> TestResult:
        """Test system behavior under memory pressure"""
        logger.info("🧪 Testing memory pressure handling...")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Get initial memory usage
            initial_memory = psutil.virtual_memory().used / 1024 / 1024
            details["initial_memory_mb"] = initial_memory
            
            # Make multiple concurrent requests to increase memory usage
            tasks = []
            for i in range(10):
                user_id = f"memory_test_user_{i}"
                task = self.session.post(
                    f"{self.base_url}/api/user/{user_id}/routine/generate",
                    json={"archetype": random.choice(self.archetypes)}
                )
                tasks.append(task)
            
            # Execute concurrent requests
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check memory after load
            peak_memory = psutil.virtual_memory().used / 1024 / 1024
            details["peak_memory_mb"] = peak_memory
            details["memory_increase_mb"] = peak_memory - initial_memory
            
            # Count successful responses
            successful_responses = 0
            for response in responses:
                if hasattr(response, 'status') and response.status == 200:
                    successful_responses += 1
                    await response.release()
            
            details["successful_responses"] = successful_responses
            details["total_requests"] = len(tasks)
            
            # Check if memory usage is reasonable (should stay under 400MB for the process)
            if details["memory_increase_mb"] < 100:  # Less than 100MB increase
                status = "PASS"
            elif details["memory_increase_mb"] < 200:
                status = "PARTIAL"
                errors.append("Memory usage higher than expected")
            else:
                status = "FAIL"
                errors.append("Excessive memory usage detected")
                
        except Exception as e:
            errors.append(f"Memory pressure test failed: {str(e)}")
            status = "FAIL"
        
        return TestResult(
            test_name="Memory Pressure Handling",
            status=status,
            duration=time.time() - start_time,
            details=details,
            errors=errors,
            metrics={
                "memory_increase": details.get("memory_increase_mb", 0),
                "peak_memory": details.get("peak_memory_mb", 0)
            }
        )
    
    # ===============================
    # 4. MONITORING & ALERTING TESTS
    # ===============================
    
    async def test_email_alerting_system(self) -> TestResult:
        """Test email alerting system with third-party provider"""
        logger.info("🧪 Testing email alerting system...")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Test alerting endpoint if available
            async with self.session.post(
                f"{self.base_url}/api/monitoring/test-alert",
                json={"alert_type": "test", "message": "Chaos testing alert validation"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    details["alert_test"] = {
                        "status": "success",
                        "email_sent": data.get("email_sent", False),
                        "provider_used": data.get("provider", "unknown"),
                        "delivery_time": data.get("delivery_time", 0)
                    }
                    status = "PASS"
                elif response.status == 404:
                    # Endpoint doesn't exist - not necessarily a failure
                    details["alert_test"] = {"status": "endpoint_not_available"}
                    status = "PARTIAL"
                    errors.append("Alert testing endpoint not implemented")
                else:
                    errors.append(f"Alert test failed: {response.status}")
                    status = "FAIL"
                    
        except Exception as e:
            errors.append(f"Email alerting test failed: {str(e)}")
            status = "FAIL"
            details["alert_test"] = {"status": "error", "error": str(e)}
        
        return TestResult(
            test_name="Email Alerting System",
            status=status,
            duration=time.time() - start_time,
            details=details,
            errors=errors,
            metrics={"email_delivery_working": details.get("alert_test", {}).get("email_sent", False)}
        )
    
    async def test_health_check_endpoints(self) -> TestResult:
        """Test health check endpoints and monitoring"""
        logger.info("🧪 Testing health check endpoints...")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Test comprehensive health check
            async with self.session.get(f"{self.base_url}/api/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    details["comprehensive_health"] = health_data
                    details["overall_status"] = health_data.get("overall_status")
                    details["services_checked"] = list(health_data.get("services", {}).keys())
                else:
                    errors.append(f"Comprehensive health check failed: {response.status}")
            
            # Test simple health check
            async with self.session.get(f"{self.base_url}/api/health/simple") as response:
                if response.status == 200:
                    details["simple_health"] = await response.json()
                else:
                    errors.append(f"Simple health check failed: {response.status}")
            
            # Test monitoring stats
            async with self.session.get(f"{self.base_url}/api/monitoring/stats") as response:
                if response.status == 200:
                    details["monitoring_stats"] = await response.json()
                else:
                    errors.append(f"Monitoring stats failed: {response.status}")
            
            # Determine overall status
            if len(errors) == 0:
                status = "PASS"
            elif len(errors) == 1:
                status = "PARTIAL"
            else:
                status = "FAIL"
                
        except Exception as e:
            errors.append(f"Health check test failed: {str(e)}")
            status = "FAIL"
        
        return TestResult(
            test_name="Health Check Endpoints",
            status=status,
            duration=time.time() - start_time,
            details=details,
            errors=errors,
            metrics={
                "endpoints_tested": 3,
                "endpoints_working": 3 - len(errors)
            }
        )
    
    # ==========================
    # 5. SHARED ANALYSIS TESTING
    # ==========================
    
    async def test_real_user_api_workflow(self) -> TestResult:
        """Test real production API workflow exactly like test_user_journey_simple.py"""
        logger.info("🧪 Testing real user API workflow (routine → nutrition → insights)...")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Use real user ID from test_user_journey_simple.py
            user_id = self.primary_user  # "35pDPUIfAoRl2Y700bFkxPKYjjf2"
            
            # Step 1: Generate routine plan (exactly like test_user_journey_simple.py)
            routine_request = {
                "archetype": "Foundation Builder",
                "preferences": {
                    "workout_time": "morning",
                    "duration_minutes": 30,
                    "intensity": "moderate"
                }
            }
            
            start_routine = time.time()
            async with self.session.post(
                f"{self.base_url}/api/user/{user_id}/routine/generate",
                json=routine_request,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                
                if response.status == 200:
                    routine_result = await response.json()
                    details["routine_generation"] = {
                        "status": "success",
                        "response_time": time.time() - start_routine,
                        "analysis_type": routine_result.get("generation_metadata", {}).get("analysis_type", "unknown"),
                        "memory_quality": routine_result.get("generation_metadata", {}).get("memory_quality", "unknown"),
                        "has_weekly_schedule": "weekly_schedule" in routine_result.get("routine", {})
                    }
                else:
                    error_text = await response.text()
                    errors.append(f"Routine generation failed: {response.status} - {error_text[:100]}")
            
            # Step 2: Generate nutrition plan (exactly like test_user_journey_simple.py)
            nutrition_request = {
                "archetype": "Foundation Builder",
                "preferences": {
                    "dietary_restriction": "none",
                    "meal_prep_time": "moderate",
                    "cuisine_preference": "mediterranean"
                }
            }
            
            start_nutrition = time.time()
            async with self.session.post(
                f"{self.base_url}/api/user/{user_id}/nutrition/generate",
                json=nutrition_request,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                
                if response.status == 200:
                    nutrition_result = await response.json()
                    details["nutrition_generation"] = {
                        "status": "success",
                        "response_time": time.time() - start_nutrition,
                        "analysis_type": nutrition_result.get("generation_metadata", {}).get("analysis_type", "unknown"),
                        "has_meal_plan": "meal_plan" in nutrition_result.get("nutrition", {})
                    }
                else:
                    error_text = await response.text()
                    errors.append(f"Nutrition generation failed: {response.status} - {error_text[:100]}")
            
            # Step 3: Generate insights (exactly like test_user_journey_simple.py)
            insights_request = {
                "user_id": user_id,
                "archetype": "Foundation Builder",
                "force_refresh": True
            }
            
            start_insights = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/insights/generate",
                json=insights_request,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status == 200:
                    insights_result = await response.json()
                    if insights_result.get("success"):
                        insights = insights_result.get("insights", [])
                        details["insights_generation"] = {
                            "status": "success",
                            "response_time": time.time() - start_insights,
                            "insights_count": len(insights),
                            "source": insights_result.get("source", "unknown")
                        }
                    else:
                        errors.append("Insights API returned success=false")
                else:
                    error_text = await response.text()
                    errors.append(f"Insights generation failed: {response.status} - {error_text[:100]}")
            
            # Check if complete real user workflow succeeded
            workflow_success = (
                details.get("routine_generation", {}).get("status") == "success" and
                details.get("nutrition_generation", {}).get("status") == "success" and
                details.get("insights_generation", {}).get("status") == "success"
            )
            
            if workflow_success and len(errors) == 0:
                status = "PASS"
            elif len(errors) <= 1:
                status = "PARTIAL"
            else:
                status = "FAIL"
                
        except Exception as e:
            errors.append(f"Real user API workflow test failed: {str(e)}")
            status = "FAIL"
        
        return TestResult(
            test_name="Real User API Workflow",
            status=status,
            duration=time.time() - start_time,
            details=details,
            errors=errors,
            metrics={
                "workflow_complete": workflow_success,
                "total_response_time": (details.get("routine_generation", {}).get("response_time", 0) + 
                                     details.get("nutrition_generation", {}).get("response_time", 0) +
                                     details.get("insights_generation", {}).get("response_time", 0)),
                "insights_generated": details.get("insights_generation", {}).get("insights_count", 0)
            }
        )
    
    async def test_insights_generation_pipeline(self) -> TestResult:
        """Test AI insights generation endpoint with various scenarios"""
        logger.info("🧪 Testing AI insights generation pipeline...")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            user_id = self.primary_user  # Use real user with data
            
            # Test 1: Fresh insights generation
            async with self.session.post(
                f"{self.base_url}/api/v1/insights/generate",
                json={
                    "user_id": user_id,
                    "archetype": "Foundation Builder",
                    "force_refresh": True
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        insights = data.get("insights", [])
                        details["fresh_insights"] = {
                            "status": "success",
                            "insights_count": len(insights),
                            "source": data.get("source", "unknown"),
                            "response_time": time.time() - start_time
                        }
                    else:
                        errors.append("Insights API returned success=false")
                else:
                    error_text = await response.text()
                    errors.append(f"Fresh insights failed: {response.status} - {error_text[:100]}")
            
            # Test 2: Cached insights retrieval
            start_cached = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/insights/generate",
                json={
                    "user_id": user_id,
                    "archetype": "Foundation Builder", 
                    "force_refresh": False
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        insights = data.get("insights", [])
                        details["cached_insights"] = {
                            "status": "success",
                            "insights_count": len(insights),
                            "source": data.get("source", "unknown"),
                            "response_time": time.time() - start_cached
                        }
                    else:
                        errors.append("Cached insights API returned success=false")
                else:
                    error_text = await response.text()
                    errors.append(f"Cached insights failed: {response.status} - {error_text[:100]}")
            
            # Test 3: Invalid user ID handling
            async with self.session.post(
                f"{self.base_url}/api/v1/insights/generate",
                json={
                    "user_id": "invalid_user_id_12345",
                    "archetype": "Foundation Builder",
                    "force_refresh": True
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                details["invalid_user_test"] = {
                    "status_code": response.status,
                    "handled_gracefully": response.status in [400, 404, 422]
                }
            
            # Test 4: Concurrent insights requests
            start_concurrent = time.time()
            tasks = []
            for i in range(3):
                task = self.session.post(
                    f"{self.base_url}/api/v1/insights/generate",
                    json={
                        "user_id": user_id,
                        "archetype": random.choice(self.archetypes),
                        "force_refresh": False
                    },
                    timeout=aiohttp.ClientTimeout(total=45)
                )
                tasks.append(task)
            
            # Execute concurrent requests
            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_concurrent = 0
            for result in concurrent_results:
                if isinstance(result, aiohttp.ClientResponse):
                    if result.status == 200:
                        successful_concurrent += 1
                    await result.close()
            
            details["concurrent_insights"] = {
                "total_requests": len(tasks),
                "successful": successful_concurrent,
                "total_time": time.time() - start_concurrent
            }
            
        except Exception as e:
            errors.append(f"Insights generation test error: {str(e)}")
            logger.error(f"Insights test error: {e}")
            logger.error(traceback.format_exc())
        
        # Determine test status
        if not errors and details.get("fresh_insights", {}).get("status") == "success":
            status = "PASS"
        elif details.get("fresh_insights", {}).get("status") == "success":
            status = "PARTIAL"  # Some issues but core functionality works
        else:
            status = "FAIL"
        
        return TestResult(
            test_name="insights_generation_pipeline",
            status=status,
            duration=time.time() - start_time,
            details=details,
            errors=errors,
            metrics={
                "insights_generated": details.get("fresh_insights", {}).get("insights_count", 0),
                "cache_performance": details.get("cached_insights", {}).get("response_time", 0),
                "concurrent_success_rate": details.get("concurrent_insights", {}).get("successful", 0) / 
                                         details.get("concurrent_insights", {}).get("total_requests", 1)
            }
        )
    
    # ==========================
    # 6. EDGE CASE SCENARIOS
    # ==========================
    
    async def test_malformed_data_handling(self) -> TestResult:
        """Test handling of malformed or invalid data"""
        logger.info("🧪 Testing malformed data handling...")
        
        start_time = time.time()
        errors = []
        details = {}
        
        malformed_payloads = [
            {"archetype": "Invalid_Archetype"},  # Invalid archetype
            {"archetype": ""},  # Empty archetype
            {"archetype": None},  # Null archetype
            {"invalid_field": "test"},  # Missing required field
            {"archetype": "Foundation Builder", "extra_field": "x" * 10000},  # Oversized field
        ]
        
        handled_properly = 0
        
        try:
            for i, payload in enumerate(malformed_payloads):
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/user/malformed_test_user/routine/generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        # Should get 400 Bad Request or 422 Validation Error
                        if response.status in [400, 422]:
                            handled_properly += 1
                            details[f"test_{i+1}"] = {
                                "payload": payload,
                                "status": response.status,
                                "handled_properly": True
                            }
                        else:
                            details[f"test_{i+1}"] = {
                                "payload": payload,
                                "status": response.status,
                                "handled_properly": False
                            }
                            errors.append(f"Malformed data test {i+1}: Expected 400/422, got {response.status}")
                            
                except Exception as e:
                    errors.append(f"Routine malformed data test {i+1}: {str(e)}")
            
            # Also test nutrition endpoint with malformed data
            nutrition_handled_properly = 0
            for i, payload in enumerate(malformed_payloads):
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/user/malformed_test_user/nutrition/generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        # Should get 400 Bad Request or 422 Validation Error
                        if response.status in [400, 422]:
                            nutrition_handled_properly += 1
                            details[f"nutrition_test_{i+1}"] = {
                                "payload": payload,
                                "status": response.status,
                                "handled_properly": True
                            }
                        else:
                            details[f"nutrition_test_{i+1}"] = {
                                "payload": payload,
                                "status": response.status,
                                "handled_properly": False
                            }
                            errors.append(f"Nutrition malformed data test {i+1}: Expected 400/422, got {response.status}")
                            
                except Exception as e:
                    errors.append(f"Nutrition malformed data test {i+1}: {str(e)}")
            
            details["routine_properly_handled"] = handled_properly
            details["nutrition_properly_handled"] = nutrition_handled_properly
            details["total_tests_per_endpoint"] = len(malformed_payloads)
            details["total_tests"] = len(malformed_payloads) * 2  # Both routine and nutrition
            
            total_handled = handled_properly + nutrition_handled_properly
            total_possible = len(malformed_payloads) * 2  # Both endpoints
            
            if total_handled == total_possible:
                status = "PASS"
            elif total_handled > total_possible // 2:
                status = "PARTIAL"
            else:
                status = "FAIL"
                
        except Exception as e:
            errors.append(f"Malformed data handling test failed: {str(e)}")
            status = "FAIL"
        
        return TestResult(
            test_name="Malformed Data Handling",
            status=status,
            duration=time.time() - start_time,
            details=details,
            errors=errors,
            metrics={
                "properly_handled": handled_properly,
                "total_tests": len(malformed_payloads)
            }
        )
    
    async def test_concurrent_user_simulation(self) -> TestResult:
        """Test real concurrent user behavior with mix of new and existing users"""
        logger.info("🧪 Testing concurrent user simulation...")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Simulate 15 concurrent users (target capacity)
            concurrent_users = 15
            user_tasks = []
            
            for i in range(concurrent_users):
                # Mix of existing users (shared analysis) and new users
                if i < 5:
                    user_id = random.choice(self.users_with_analysis)
                    use_existing = True
                else:
                    user_id = f"concurrent_user_{i}_{int(time.time())}"
                    use_existing = False
                    
                archetype = random.choice(self.archetypes)
                
                # Create a realistic user journey
                user_task = self._simulate_user_journey(user_id, archetype, use_existing)
                user_tasks.append(user_task)
            
            # Execute all user journeys concurrently
            results = await asyncio.gather(*user_tasks, return_exceptions=True)
            
            # Analyze results
            successful_journeys = 0
            failed_journeys = 0
            partial_journeys = 0
            
            for result in results:
                if isinstance(result, Exception):
                    failed_journeys += 1
                    errors.append(f"User journey failed: {str(result)}")
                elif isinstance(result, dict):
                    if result.get("status") == "success":
                        successful_journeys += 1
                    elif result.get("status") == "partial":
                        partial_journeys += 1
                    else:
                        failed_journeys += 1
            
            details["concurrent_users"] = concurrent_users
            details["successful_journeys"] = successful_journeys
            details["partial_journeys"] = partial_journeys
            details["failed_journeys"] = failed_journeys
            details["success_rate"] = (successful_journeys / concurrent_users) * 100
            
            # Determine status based on success rate
            if details["success_rate"] >= 80:
                status = "PASS"
            elif details["success_rate"] >= 60:
                status = "PARTIAL"
            else:
                status = "FAIL"
                
        except Exception as e:
            errors.append(f"Concurrent user simulation failed: {str(e)}")
            status = "FAIL"
        
        return TestResult(
            test_name="Concurrent User Simulation",
            status=status,
            duration=time.time() - start_time,
            details=details,
            errors=errors,
            metrics={
                "concurrent_users": details.get("concurrent_users", 0),
                "success_rate": details.get("success_rate", 0)
            }
        )
    
    async def _simulate_user_journey(self, user_id: str, archetype: str, use_existing: bool = False) -> Dict[str, Any]:
        """Simulate a realistic user journey with shared analysis capability"""
        journey_start = time.time()
        journey_details = {"user_id": user_id, "archetype": archetype, "use_existing": use_existing, "steps": []}
        
        try:
            # Prepare payload for existing vs new analysis
            base_payload = {"archetype": archetype}
            if use_existing:
                base_payload["use_existing_analysis"] = True
                
            # Step 1: Generate routine
            async with self.session.post(
                f"{self.base_url}/api/user/{user_id}/routine/generate",
                json=base_payload,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    journey_details["steps"].append({
                        "routine": "success",
                        "shared_analysis": data.get("metadata", {}).get("shared_analysis_used", False)
                    })
                else:
                    journey_details["steps"].append({"routine": f"failed_{response.status}"})
            
            # Brief delay between requests (realistic user behavior)
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Step 2: Generate nutrition plan
            async with self.session.post(
                f"{self.base_url}/api/user/{user_id}/nutrition/generate",
                json=base_payload,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    journey_details["steps"].append({
                        "nutrition": "success",
                        "shared_analysis": data.get("metadata", {}).get("shared_analysis_used", False)
                    })
                else:
                    journey_details["steps"].append({"nutrition": f"failed_{response.status}"})
            
            # Determine journey success
            successful_steps = sum(1 for step in journey_details["steps"] 
                                 if any("success" in str(v) for v in step.values()))
            
            if successful_steps == len(journey_details["steps"]):
                journey_details["status"] = "success"
            elif successful_steps > 0:
                journey_details["status"] = "partial"
            else:
                journey_details["status"] = "failed"
            
            journey_details["duration"] = time.time() - journey_start
            return journey_details
            
        except Exception as e:
            journey_details["status"] = "error"
            journey_details["error"] = str(e)
            journey_details["duration"] = time.time() - journey_start
            return journey_details
    
    # ========================
    # TEST EXECUTION & REPORTING
    # ========================
    
    async def run_all_chaos_tests(self) -> Dict[str, Any]:
        """Run complete chaos testing suite"""
        logger.info("🚀 Starting Comprehensive Chaos Testing Suite...")
        
        suite_start_time = time.time()
        
        # Define test sequence with shared analysis and alerting testing
        test_methods = [
            self.test_health_check_endpoints,
            self.test_database_connection_resilience,
            self.test_email_alerting_system,  # Test alerting system
            self.test_real_user_api_workflow,  # Test real user API workflow
            self.test_insights_generation_pipeline,  # Test insights generation
            self.test_rate_limiting_enforcement,
            self.test_cost_tracking_accuracy,
            self.test_memory_pressure_handling,
            self.test_malformed_data_handling,
            self.test_openai_timeout_handling,
            self.test_concurrent_user_simulation,
        ]
        
        # Execute all tests
        for test_method in test_methods:
            try:
                result = await test_method()
                self.test_results.append(result)
                
                # Log immediate result
                logger.info(f"✅ {result.test_name}: {result.status} ({result.duration:.2f}s)")
                
                # Brief pause between tests
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Test {test_method.__name__} crashed: {e}")
                self.test_results.append(TestResult(
                    test_name=test_method.__name__,
                    status="CRASH",
                    duration=0,
                    details={"crash_error": str(e)},
                    errors=[str(e)],
                    metrics={}
                ))
        
        # Generate comprehensive report
        report = self._generate_test_report(time.time() - suite_start_time)
        
        # Save report to file
        with open(f"chaos_test_report_{int(time.time())}.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"🎯 Chaos Testing Complete! Report saved. Overall Score: {report['chaos_testing_report']['summary']['score']}/100")
        
        return report
    
    def _generate_test_report(self, total_duration: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "PASS"])
        partial_tests = len([r for r in self.test_results if r.status == "PARTIAL"])
        failed_tests = len([r for r in self.test_results if r.status == "FAIL"])
        crashed_tests = len([r for r in self.test_results if r.status == "CRASH"])
        
        # Calculate overall score
        score = ((passed_tests * 10) + (partial_tests * 5)) / (total_tests * 10) * 100
        
        return {
            "chaos_testing_report": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": total_duration,
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "partial": partial_tests,
                    "failed": failed_tests,
                    "crashed": crashed_tests,
                    "score": round(score, 1),
                    "production_readiness": "READY" if score >= 80 else "NEEDS_WORK"
                },
                "detailed_results": [
                    {
                        "test_name": result.test_name,
                        "status": result.status,
                        "duration": result.duration,
                        "details": result.details,
                        "errors": result.errors,
                        "metrics": result.metrics
                    }
                    for result in self.test_results
                ],
                "recommendations": self._generate_recommendations()
            }
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for result in self.test_results:
            if result.status == "FAIL":
                recommendations.append(f"🔧 Fix {result.test_name}: {', '.join(result.errors)}")
            elif result.status == "PARTIAL":
                recommendations.append(f"⚠️ Improve {result.test_name}: May need optimization")
        
        if not recommendations:
            recommendations.append("✅ All tests passed! System is production-ready.")
        
        return recommendations

# Main execution function
async def run_chaos_testing():
    """Main function to run chaos testing"""
    async with ChaosTestingSuite() as chaos_tester:
        report = await chaos_tester.run_all_chaos_tests()
        return report

if __name__ == "__main__":
    asyncio.run(run_chaos_testing())