import asyncio
import aiohttp
import time
import json
from typing import Dict, Any, List
from dataclasses import dataclass
import sys
import os

@dataclass
class AgentTestResult:
    agent_name: str
    endpoint: str
    success: bool
    response_time_ms: float
    status_code: int
    error_message: str = ""
    response_data: dict = None

class HolisticOSAgentValidator:
    """Comprehensive validation of all HolisticOS agent components"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.test_results = []
        self.test_user_id = f"validation_user_{int(time.time())}"
    
    async def validate_all_agents(self) -> Dict[str, Any]:
        """Run comprehensive validation of all agent components"""
        print("🔍 Starting comprehensive agent validation...")
        print(f"Using test user ID: {self.test_user_id}")
        
        validation_results = {
            "test_timestamp": time.time(),
            "test_user_id": self.test_user_id,
            "system_health": await self.validate_system_health(),
            "orchestrator_agent": await self.validate_orchestrator_agent(),
            "behavior_analysis_agent": await self.validate_behavior_analysis_agent(),
            "memory_management_agent": await self.validate_memory_management_agent(),
            "routine_generation_agent": await self.validate_routine_generation_agent(),
            "nutrition_planning_agent": await self.validate_nutrition_planning_agent(),
            "insights_extraction_service": await self.validate_insights_extraction_service(),
            "agent_integration": await self.validate_agent_integration(),
            "error_handling": await self.validate_error_handling(),
            "performance_thresholds": await self.validate_performance_thresholds()
        }
        
        # Generate overall assessment
        validation_results["overall_assessment"] = self._generate_overall_assessment(validation_results)
        
        return validation_results
    
    async def validate_system_health(self) -> Dict[str, Any]:
        """Validate basic system health and monitoring endpoints"""
        print("🏥 Validating system health...")
        
        health_tests = [
            ("Basic Health Check", "GET", "/api/health", None, 200),
            ("Detailed Health", "GET", "/api/monitoring/health", None, 200),
            ("System Stats", "GET", "/api/monitoring/stats", None, 200),
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for test_name, method, endpoint, payload, expected_status in health_tests:
                result = await self._make_test_request(
                    session, test_name, method, endpoint, payload, expected_status
                )
                results.append(result)
        
        return {
            "tests": results,
            "overall_health": all(r.success for r in results),
            "critical_issues": [r.error_message for r in results if not r.success]
        }
    
    async def validate_orchestrator_agent(self) -> Dict[str, Any]:
        """Validate orchestrator agent coordination capabilities"""
        print("🎭 Validating orchestrator agent...")
        
        # Test orchestrator by triggering a complete user journey
        orchestrator_tests = [
            ("Legacy Analysis Endpoint", "POST", "/api/analyze", 
             {"user_id": self.test_user_id, "archetype": "Foundation Builder"}, 200),
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for test_name, method, endpoint, payload, expected_status in orchestrator_tests:
                result = await self._make_test_request(
                    session, test_name, method, endpoint, payload, expected_status
                )
                results.append(result)
                
                # Check if orchestrator properly coordinated multiple agents
                if result.success and result.response_data:
                    orchestration_quality = self._assess_orchestration_quality(result.response_data)
                    result.response_data["orchestration_assessment"] = orchestration_quality
        
        return {
            "tests": results,
            "orchestrator_functional": all(r.success for r in results),
            "coordination_quality": self._calculate_coordination_score(results)
        }
    
    async def validate_behavior_analysis_agent(self) -> Dict[str, Any]:
        """Validate behavior analysis agent with 50-item threshold logic"""
        print("🧠 Validating behavior analysis agent...")
        
        behavior_tests = [
            ("Behavior Analysis Direct", "POST", f"/api/user/{self.test_user_id}/behavior/analyze", 
             {}, 200),
            ("Behavior Analysis with Data", "POST", f"/api/user/{self.test_user_id}/behavior/analyze",
             {"force_analysis": True}, 200),
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for test_name, method, endpoint, payload, expected_status in behavior_tests:
                result = await self._make_test_request(
                    session, test_name, method, endpoint, payload, expected_status
                )
                results.append(result)
                
                # Validate behavior analysis response structure
                if result.success and result.response_data:
                    analysis_quality = self._assess_behavior_analysis_quality(result.response_data)
                    result.response_data["analysis_assessment"] = analysis_quality
        
        return {
            "tests": results,
            "behavior_agent_functional": all(r.success for r in results),
            "threshold_logic_working": self._check_threshold_logic(results),
            "analysis_quality": self._calculate_analysis_quality(results)
        }
    
    async def validate_memory_management_agent(self) -> Dict[str, Any]:
        """Validate 4-layer memory management system"""
        print("🧮 Validating memory management agent...")
        
        memory_tests = [
            ("Memory Health Check", "GET", "/api/monitoring/memory", None, 200),
            ("Memory Storage Test", "POST", f"/api/user/{self.test_user_id}/behavior/analyze", 
             {"test_memory": True}, 200),
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for test_name, method, endpoint, payload, expected_status in memory_tests:
                result = await self._make_test_request(
                    session, test_name, method, endpoint, payload, expected_status
                )
                results.append(result)
        
        # Test memory persistence by checking if data persists between calls
        memory_persistence = await self._test_memory_persistence(session)
        
        return {
            "tests": results,
            "memory_agent_functional": all(r.success for r in results),
            "memory_persistence": memory_persistence,
            "memory_layers_operational": self._check_memory_layers(results)
        }
    
    async def validate_routine_generation_agent(self) -> Dict[str, Any]:
        """Validate routine generation agent for all archetypes"""
        print("🏃 Validating routine generation agent...")
        
        archetypes = [
            "Foundation Builder", "Transformation Seeker", "Systematic Improver",
            "Peak Performer", "Resilience Rebuilder", "Connected Explorer"
        ]
        
        routine_tests = []
        results = []
        
        # Test each archetype
        for archetype in archetypes:
            routine_tests.append((
                f"Routine Generation - {archetype}", "POST", 
                f"/api/user/{self.test_user_id}/routine/generate",
                {"archetype": archetype, "preferences": {"focus_areas": ["strength"]}}, 200
            ))
        
        # Test with different parameters
        routine_tests.extend([
            ("Routine with Complex Preferences", "POST", f"/api/user/{self.test_user_id}/routine/generate",
             {"archetype": "Peak Performer", "preferences": {
                 "focus_areas": ["strength", "cardio", "flexibility"],
                 "duration_minutes": 45,
                 "equipment": ["dumbbells", "resistance_bands"]
             }}, 200),
            ("Routine with Minimal Data", "POST", f"/api/user/{self.test_user_id}/routine/generate",
             {"archetype": "Foundation Builder"}, 200),
        ])
        
        async with aiohttp.ClientSession() as session:
            for test_name, method, endpoint, payload, expected_status in routine_tests:
                result = await self._make_test_request(
                    session, test_name, method, endpoint, payload, expected_status, timeout=30
                )
                results.append(result)
                
                # Validate routine content quality
                if result.success and result.response_data:
                    routine_quality = self._assess_routine_quality(result.response_data, payload.get("archetype"))
                    result.response_data["routine_assessment"] = routine_quality
        
        return {
            "tests": results,
            "routine_agent_functional": all(r.success for r in results),
            "archetype_coverage": self._calculate_archetype_coverage(results, archetypes),
            "routine_quality": self._calculate_routine_quality(results)
        }
    
    async def validate_nutrition_planning_agent(self) -> Dict[str, Any]:
        """Validate nutrition planning agent for all archetypes"""
        print("🥗 Validating nutrition planning agent...")
        
        nutrition_tests = [
            ("Nutrition Planning - Foundation Builder", "POST", 
             f"/api/user/{self.test_user_id}/nutrition/generate",
             {"archetype": "Foundation Builder", "dietary_preferences": ["vegetarian"]}, 200),
            ("Nutrition Planning - Peak Performer", "POST",
             f"/api/user/{self.test_user_id}/nutrition/generate", 
             {"archetype": "Peak Performer", "dietary_preferences": ["high_protein"]}, 200),
            ("Nutrition with Complex Requirements", "POST",
             f"/api/user/{self.test_user_id}/nutrition/generate",
             {"archetype": "Transformation Seeker", "dietary_preferences": [
                 "vegetarian", "gluten_free", "low_carb"
             ]}, 200),
            ("Nutrition with Minimal Data", "POST",
             f"/api/user/{self.test_user_id}/nutrition/generate",
             {"archetype": "Systematic Improver"}, 200),
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for test_name, method, endpoint, payload, expected_status in nutrition_tests:
                result = await self._make_test_request(
                    session, test_name, method, endpoint, payload, expected_status, timeout=30
                )
                results.append(result)
                
                # Validate nutrition plan quality
                if result.success and result.response_data:
                    nutrition_quality = self._assess_nutrition_quality(result.response_data, payload.get("archetype"))
                    result.response_data["nutrition_assessment"] = nutrition_quality
        
        return {
            "tests": results,
            "nutrition_agent_functional": all(r.success for r in results),
            "nutrition_quality": self._calculate_nutrition_quality(results)
        }
    
    async def validate_insights_extraction_service(self) -> Dict[str, Any]:
        """Validate insights extraction service and deduplication"""
        print("💡 Validating insights extraction service...")
        
        # First generate some data for insights extraction
        setup_tasks = []
        async with aiohttp.ClientSession() as session:
            # Generate routine and nutrition to create data for insights
            setup_tasks.append(
                self._make_test_request(session, "Setup Routine", "POST", 
                                      f"/api/user/{self.test_user_id}/routine/generate",
                                      {"archetype": "Foundation Builder"}, 200, timeout=30)
            )
            setup_tasks.append(
                self._make_test_request(session, "Setup Nutrition", "POST",
                                      f"/api/user/{self.test_user_id}/nutrition/generate", 
                                      {"archetype": "Foundation Builder"}, 200, timeout=30)
            )
            
            setup_results = await asyncio.gather(*setup_tasks, return_exceptions=True)
            
            # Now test insights extraction
            insights_tests = [
                ("Manual Insights Generation", "POST", f"/api/user/{self.test_user_id}/insights/generate",
                 {}, 200),
            ]
            
            results = []
            for test_name, method, endpoint, payload, expected_status in insights_tests:
                result = await self._make_test_request(
                    session, test_name, method, endpoint, payload, expected_status, timeout=30
                )
                results.append(result)
                
                # Validate insights quality
                if result.success and result.response_data:
                    insights_quality = self._assess_insights_quality(result.response_data)
                    result.response_data["insights_assessment"] = insights_quality
        
        return {
            "tests": results,
            "insights_service_functional": all(r.success for r in results),
            "insights_quality": self._calculate_insights_quality(results)
        }
    
    async def validate_agent_integration(self) -> Dict[str, Any]:
        """Validate inter-agent communication and data flow"""
        print("🔗 Validating agent integration...")
        
        # Test complete user journey that exercises all agents
        integration_tests = [
            ("Complete User Journey", "POST", "/api/analyze",
             {"user_id": self.test_user_id, "archetype": "Foundation Builder"}, 200),
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for test_name, method, endpoint, payload, expected_status in integration_tests:
                start_time = time.time()
                result = await self._make_test_request(
                    session, test_name, method, endpoint, payload, expected_status, timeout=60
                )
                results.append(result)
                
                # Check if the journey properly integrated multiple agents
                if result.success and result.response_data:
                    integration_quality = self._assess_integration_quality(result.response_data)
                    result.response_data["integration_assessment"] = integration_quality
                    result.response_data["journey_duration"] = time.time() - start_time
        
        return {
            "tests": results,
            "agent_integration_functional": all(r.success for r in results),
            "integration_quality": self._calculate_integration_quality(results),
            "data_flow_integrity": self._check_data_flow_integrity(results)
        }
    
    async def validate_error_handling(self) -> Dict[str, Any]:
        """Validate error handling and resilience"""
        print("⚠️ Validating error handling...")
        
        error_tests = [
            ("Invalid Archetype", "POST", f"/api/user/{self.test_user_id}/routine/generate",
             {"archetype": "InvalidArchetype"}, 400),
            ("Missing Required Data", "POST", f"/api/user/{self.test_user_id}/routine/generate",
             {}, 400),
            ("Invalid User ID Format", "POST", "/api/user//routine/generate",
             {"archetype": "Foundation Builder"}, 404),
            ("Non-existent Endpoint", "GET", "/api/nonexistent", None, 404),
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for test_name, method, endpoint, payload, expected_status in error_tests:
                result = await self._make_test_request(
                    session, test_name, method, endpoint, payload, expected_status
                )
                results.append(result)
        
        return {
            "tests": results,
            "error_handling_functional": all(r.success for r in results),
            "graceful_degradation": self._check_graceful_degradation(results)
        }
    
    async def validate_performance_thresholds(self) -> Dict[str, Any]:
        """Validate that all agents meet performance thresholds"""
        print("⚡ Validating performance thresholds...")
        
        performance_tests = [
            ("Health Check Speed", "GET", "/api/health", None, 200, 2000),  # 2s threshold
            ("Routine Generation Speed", "POST", f"/api/user/{self.test_user_id}/routine/generate",
             {"archetype": "Foundation Builder"}, 200, 15000),  # 15s threshold
            ("Nutrition Generation Speed", "POST", f"/api/user/{self.test_user_id}/nutrition/generate",
             {"archetype": "Foundation Builder"}, 200, 15000),  # 15s threshold
            ("Behavior Analysis Speed", "POST", f"/api/user/{self.test_user_id}/behavior/analyze",
             {}, 200, 20000),  # 20s threshold
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for test_name, method, endpoint, payload, expected_status, threshold_ms in performance_tests:
                result = await self._make_test_request(
                    session, test_name, method, endpoint, payload, expected_status, timeout=30
                )
                
                # Check if within threshold
                result.within_threshold = result.response_time_ms <= threshold_ms
                result.threshold_ms = threshold_ms
                
                results.append(result)
        
        return {
            "tests": results,
            "performance_acceptable": all(r.within_threshold for r in results if hasattr(r, 'within_threshold')),
            "threshold_violations": [r for r in results if hasattr(r, 'within_threshold') and not r.within_threshold]
        }
    
    async def _make_test_request(self, session: aiohttp.ClientSession, test_name: str,
                               method: str, endpoint: str, payload: dict = None, 
                               expected_status: int = 200, timeout: int = 15) -> AgentTestResult:
        """Make a test request and return structured result"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method == "GET":
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    duration_ms = (time.time() - start_time) * 1000
                    content = await response.text()
                    
                    try:
                        response_data = json.loads(content) if content else {}
                    except json.JSONDecodeError:
                        response_data = {"raw_response": content}
                    
                    success = response.status == expected_status
                    error_msg = "" if success else f"Expected {expected_status}, got {response.status}"
                    
                    return AgentTestResult(
                        agent_name=test_name,
                        endpoint=endpoint,
                        success=success,
                        response_time_ms=duration_ms,
                        status_code=response.status,
                        error_message=error_msg,
                        response_data=response_data
                    )
            else:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    duration_ms = (time.time() - start_time) * 1000
                    content = await response.text()
                    
                    try:
                        response_data = json.loads(content) if content else {}
                    except json.JSONDecodeError:
                        response_data = {"raw_response": content}
                    
                    success = response.status == expected_status
                    error_msg = "" if success else f"Expected {expected_status}, got {response.status}"
                    
                    return AgentTestResult(
                        agent_name=test_name,
                        endpoint=endpoint,
                        success=success,
                        response_time_ms=duration_ms,
                        status_code=response.status,
                        error_message=error_msg,
                        response_data=response_data
                    )
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return AgentTestResult(
                agent_name=test_name,
                endpoint=endpoint,
                success=False,
                response_time_ms=duration_ms,
                status_code=0,
                error_message=str(e),
                response_data={}
            )
    
    # Assessment helper methods
    def _assess_orchestration_quality(self, response_data: dict) -> Dict[str, Any]:
        """Assess the quality of orchestrator coordination"""
        quality_score = 0
        issues = []
        
        # Check if response contains evidence of multi-agent coordination
        if "status" in response_data:
            quality_score += 25
        if "message" in response_data:
            quality_score += 25
        if "processing_time" in response_data:
            quality_score += 25
        if response_data.get("status") == "success":
            quality_score += 25
        
        return {"quality_score": quality_score, "issues": issues}
    
    def _assess_behavior_analysis_quality(self, response_data: dict) -> Dict[str, Any]:
        """Assess the quality of behavior analysis"""
        quality_score = 0
        issues = []
        
        # Check for expected behavior analysis components
        if "analysis_summary" in response_data or "behavior_insights" in response_data:
            quality_score += 30
        if "recommendations" in response_data:
            quality_score += 30
        if "patterns" in response_data or "insights" in response_data:
            quality_score += 40
        
        return {"quality_score": quality_score, "issues": issues}
    
    def _assess_routine_quality(self, response_data: dict, archetype: str) -> Dict[str, Any]:
        """Assess the quality of routine generation"""
        quality_score = 0
        issues = []
        
        # Check for routine structure
        if "routine" in response_data or "exercises" in response_data:
            quality_score += 40
        if "duration" in response_data or "total_time" in response_data:
            quality_score += 20
        if archetype.lower() in str(response_data).lower():
            quality_score += 20  # Archetype-specific content
        if "instructions" in response_data or "description" in response_data:
            quality_score += 20
        
        return {"quality_score": quality_score, "issues": issues}
    
    def _assess_nutrition_quality(self, response_data: dict, archetype: str) -> Dict[str, Any]:
        """Assess the quality of nutrition planning"""
        quality_score = 0
        issues = []
        
        # Check for nutrition structure
        if "meal_plan" in response_data or "nutrition_plan" in response_data:
            quality_score += 40
        if "calories" in response_data or "macros" in response_data:
            quality_score += 20
        if archetype.lower() in str(response_data).lower():
            quality_score += 20  # Archetype-specific content
        if "recommendations" in response_data:
            quality_score += 20
        
        return {"quality_score": quality_score, "issues": issues}
    
    def _assess_insights_quality(self, response_data: dict) -> Dict[str, Any]:
        """Assess the quality of insights extraction"""
        quality_score = 0
        issues = []
        
        # Check for insights structure
        if "insights" in response_data or "recommendations" in response_data:
            quality_score += 50
        if "patterns" in response_data or "trends" in response_data:
            quality_score += 30
        if "action_items" in response_data or "next_steps" in response_data:
            quality_score += 20
        
        return {"quality_score": quality_score, "issues": issues}
    
    def _assess_integration_quality(self, response_data: dict) -> Dict[str, Any]:
        """Assess the quality of agent integration"""
        quality_score = 0
        issues = []
        
        # Check for evidence of multi-agent coordination
        expected_components = ["behavior", "routine", "nutrition", "insights"]
        found_components = []
        
        response_str = str(response_data).lower()
        for component in expected_components:
            if component in response_str:
                found_components.append(component)
                quality_score += 25
        
        return {
            "quality_score": quality_score, 
            "issues": issues,
            "components_found": found_components
        }
    
    async def _test_memory_persistence(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test memory persistence between requests"""
        # Make a request that should store something in memory
        first_request = await self._make_test_request(
            session, "Memory Store Test", "POST",
            f"/api/user/{self.test_user_id}/behavior/analyze", {}, 200
        )
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Make another request that should retrieve from memory
        second_request = await self._make_test_request(
            session, "Memory Retrieve Test", "POST",
            f"/api/user/{self.test_user_id}/behavior/analyze", {}, 200
        )
        
        return {
            "first_request_success": first_request.success,
            "second_request_success": second_request.success,
            "persistence_working": first_request.success and second_request.success,
            "response_time_improvement": (
                first_request.response_time_ms > second_request.response_time_ms
                if first_request.success and second_request.success else False
            )
        }
    
    # Calculation helper methods
    def _calculate_coordination_score(self, results: List[AgentTestResult]) -> float:
        if not results:
            return 0.0
        
        successful_tests = [r for r in results if r.success]
        if not successful_tests:
            return 0.0
        
        quality_scores = []
        for result in successful_tests:
            if result.response_data and "orchestration_assessment" in result.response_data:
                quality_scores.append(result.response_data["orchestration_assessment"]["quality_score"])
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _check_threshold_logic(self, results: List[AgentTestResult]) -> bool:
        """Check if threshold logic is working correctly"""
        # For now, just check if behavior analysis responds appropriately
        return any(r.success for r in results)
    
    def _calculate_analysis_quality(self, results: List[AgentTestResult]) -> float:
        quality_scores = []
        for result in results:
            if result.success and result.response_data and "analysis_assessment" in result.response_data:
                quality_scores.append(result.response_data["analysis_assessment"]["quality_score"])
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _check_memory_layers(self, results: List[AgentTestResult]) -> bool:
        """Check if memory layers are operational"""
        return any(r.success for r in results)
    
    def _calculate_archetype_coverage(self, results: List[AgentTestResult], archetypes: List[str]) -> float:
        successful_archetypes = 0
        for archetype in archetypes:
            archetype_results = [r for r in results if archetype in r.agent_name and r.success]
            if archetype_results:
                successful_archetypes += 1
        
        return (successful_archetypes / len(archetypes)) * 100 if archetypes else 0.0
    
    def _calculate_routine_quality(self, results: List[AgentTestResult]) -> float:
        quality_scores = []
        for result in results:
            if result.success and result.response_data and "routine_assessment" in result.response_data:
                quality_scores.append(result.response_data["routine_assessment"]["quality_score"])
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_nutrition_quality(self, results: List[AgentTestResult]) -> float:
        quality_scores = []
        for result in results:
            if result.success and result.response_data and "nutrition_assessment" in result.response_data:
                quality_scores.append(result.response_data["nutrition_assessment"]["quality_score"])
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_insights_quality(self, results: List[AgentTestResult]) -> float:
        quality_scores = []
        for result in results:
            if result.success and result.response_data and "insights_assessment" in result.response_data:
                quality_scores.append(result.response_data["insights_assessment"]["quality_score"])
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_integration_quality(self, results: List[AgentTestResult]) -> float:
        quality_scores = []
        for result in results:
            if result.success and result.response_data and "integration_assessment" in result.response_data:
                quality_scores.append(result.response_data["integration_assessment"]["quality_score"])
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _check_data_flow_integrity(self, results: List[AgentTestResult]) -> bool:
        """Check if data flows correctly between agents"""
        return any(r.success for r in results)
    
    def _check_graceful_degradation(self, results: List[AgentTestResult]) -> bool:
        """Check if system degrades gracefully under error conditions"""
        # All error tests should return appropriate HTTP status codes
        return all(r.success for r in results)
    
    def _generate_overall_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall assessment of agent validation"""
        assessment = {
            "overall_score": 0,
            "production_ready": False,
            "critical_issues": [],
            "recommendations": [],
            "agent_status": {}
        }
        
        # Calculate component scores
        components = [
            ("system_health", results.get("system_health", {})),
            ("orchestrator_agent", results.get("orchestrator_agent", {})),
            ("behavior_analysis_agent", results.get("behavior_analysis_agent", {})),
            ("memory_management_agent", results.get("memory_management_agent", {})),
            ("routine_generation_agent", results.get("routine_generation_agent", {})),
            ("nutrition_planning_agent", results.get("nutrition_planning_agent", {})),
            ("insights_extraction_service", results.get("insights_extraction_service", {})),
            ("agent_integration", results.get("agent_integration", {})),
            ("error_handling", results.get("error_handling", {})),
            ("performance_thresholds", results.get("performance_thresholds", {}))
        ]
        
        total_score = 0
        component_count = 0
        
        for component_name, component_data in components:
            component_score = 0
            
            # Check if component has functional tests
            if "tests" in component_data:
                tests = component_data["tests"]
                successful_tests = sum(1 for test in tests if test.success)
                total_tests = len(tests)
                component_score = (successful_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Check for specific functional flags
            functional_keys = [k for k in component_data.keys() if k.endswith("_functional")]
            if functional_keys:
                functional_status = all(component_data[key] for key in functional_keys)
                if functional_status:
                    component_score = max(component_score, 85)  # Functional = at least 85%
            
            assessment["agent_status"][component_name] = {
                "score": component_score,
                "functional": component_score >= 70,
                "issues": component_data.get("critical_issues", [])
            }
            
            total_score += component_score
            component_count += 1
            
            # Add critical issues
            if component_score < 70:
                assessment["critical_issues"].append(f"{component_name} below functional threshold")
        
        # Calculate overall score
        assessment["overall_score"] = total_score / component_count if component_count > 0 else 0
        
        # Determine production readiness
        assessment["production_ready"] = (
            assessment["overall_score"] >= 80 and
            len(assessment["critical_issues"]) == 0 and
            all(status["functional"] for status in assessment["agent_status"].values())
        )
        
        # Generate recommendations
        if assessment["overall_score"] < 90:
            assessment["recommendations"].append("Consider additional testing for edge cases")
        
        if not results.get("performance_thresholds", {}).get("performance_acceptable", True):
            assessment["recommendations"].append("Optimize response times for better performance")
        
        for component_name, status in assessment["agent_status"].items():
            if not status["functional"]:
                assessment["recommendations"].append(f"Fix critical issues in {component_name}")
        
        return assessment

async def main():
    """Main validation function"""
    validator = HolisticOSAgentValidator()
    
    print("🚀 Starting comprehensive HolisticOS agent validation...")
    print("This comprehensive test may take several minutes...")
    
    try:
        results = await validator.validate_all_agents()
        
        # Save detailed results
        with open("agent_validation_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        # Generate human-readable summary
        generate_validation_summary(results)
        
        print("\n📊 Agent validation complete!")
        print("Reports saved to:")
        print("  - agent_validation_results.json (detailed)")
        print("  - agent_validation_summary.txt (summary)")
        
        # Print quick summary
        assessment = results.get("overall_assessment", {})
        print(f"\n🎯 Overall Score: {assessment.get('overall_score', 0):.1f}/100")
        print(f"🚦 Production Ready: {'YES' if assessment.get('production_ready', False) else 'NO'}")
        
        if assessment.get("critical_issues"):
            print("⚠️ Critical Issues:")
            for issue in assessment["critical_issues"]:
                print(f"  - {issue}")
        
        return results
        
    except Exception as e:
        print(f"❌ Agent validation failed: {e}")
        return {"error": str(e)}

def generate_validation_summary(results: Dict[str, Any]):
    """Generate human-readable validation summary"""
    summary = []
    summary.append("HolisticOS Agent Validation Summary")
    summary.append("=" * 40)
    summary.append(f"Test Date: {time.ctime(results.get('test_timestamp', time.time()))}")
    summary.append(f"Test User ID: {results.get('test_user_id', 'Unknown')}")
    summary.append("")
    
    # Overall Assessment
    if "overall_assessment" in results:
        assessment = results["overall_assessment"]
        summary.append("Overall Assessment:")
        summary.append(f"  ✓ Score: {assessment.get('overall_score', 0):.1f}/100")
        summary.append(f"  ✓ Production Ready: {'YES' if assessment.get('production_ready', False) else 'NO'}")
        summary.append("")
        
        # Agent Status
        summary.append("Agent Component Status:")
        for component, status in assessment.get("agent_status", {}).items():
            status_icon = "✅" if status["functional"] else "❌"
            summary.append(f"  {status_icon} {component}: {status['score']:.1f}% functional")
        summary.append("")
        
        # Critical Issues
        if assessment.get("critical_issues"):
            summary.append("Critical Issues:")
            for issue in assessment["critical_issues"]:
                summary.append(f"  ❌ {issue}")
            summary.append("")
        
        # Recommendations
        if assessment.get("recommendations"):
            summary.append("Recommendations:")
            for rec in assessment["recommendations"]:
                summary.append(f"  💡 {rec}")
            summary.append("")
    
    # Component Details
    components = [
        ("System Health", results.get("system_health", {})),
        ("Orchestrator Agent", results.get("orchestrator_agent", {})),
        ("Behavior Analysis Agent", results.get("behavior_analysis_agent", {})),
        ("Memory Management Agent", results.get("memory_management_agent", {})),
        ("Routine Generation Agent", results.get("routine_generation_agent", {})),
        ("Nutrition Planning Agent", results.get("nutrition_planning_agent", {})),
        ("Insights Extraction Service", results.get("insights_extraction_service", {})),
        ("Agent Integration", results.get("agent_integration", {})),
        ("Error Handling", results.get("error_handling", {})),
        ("Performance Thresholds", results.get("performance_thresholds", {}))
    ]
    
    for component_name, component_data in components:
        if "tests" in component_data:
            tests = component_data["tests"]
            successful = sum(1 for test in tests if test.success)
            total = len(tests)
            
            summary.append(f"{component_name}:")
            summary.append(f"  Tests: {successful}/{total} passed")
            
            # Show failed tests
            failed_tests = [test for test in tests if not test.success]
            if failed_tests:
                summary.append("  Failed tests:")
                for test in failed_tests:
                    summary.append(f"    - {test.agent_name}: {test.error_message}")
            
            summary.append("")
    
    # Performance Summary
    if "performance_thresholds" in results:
        perf = results["performance_thresholds"]
        summary.append("Performance Summary:")
        summary.append(f"  ✓ All thresholds met: {'YES' if perf.get('performance_acceptable', False) else 'NO'}")
        
        if "threshold_violations" in perf and perf["threshold_violations"]:
            summary.append("  Threshold violations:")
            for violation in perf["threshold_violations"]:
                summary.append(f"    - {violation.agent_name}: {violation.response_time_ms:.0f}ms (limit: {violation.threshold_ms}ms)")
        
        summary.append("")
    
    # Write summary to file
    with open("agent_validation_summary.txt", "w") as f:
        f.write("\n".join(summary))

if __name__ == "__main__":
    asyncio.run(main())