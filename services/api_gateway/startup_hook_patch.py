"""
Patch for openai_main.py - Add Background Worker Startup
Add this to the initialize_agents() function after line 502
"""

# ADD THIS IMPORT at the top of openai_main.py (after other service imports)
"""
from services.background import get_job_queue
"""

# ADD THIS CODE inside initialize_agents() function after line 502:
"""
        # Initialize background job queue worker
        try:
            job_queue = get_job_queue()
            await job_queue.start()
            logger.info("[STARTUP] Background worker started successfully")
        except Exception as e:
            logger.error(f"[STARTUP] Failed to start background worker: {e}")
            # Non-critical - continue without background archival
"""

# ADD THIS CODE inside shutdown_agents() function after line 569:
"""
        # Stop background worker
        try:
            from services.background import get_job_queue
            job_queue = get_job_queue()
            await job_queue.stop()
            logger.info("[SHUTDOWN] Background worker stopped")
        except Exception as e:
            logger.error(f"[SHUTDOWN] Failed to stop background worker: {e}")
"""

# Full modified initialize_agents() function:
"""
@app.on_event("startup")
async def initialize_agents():
    global orchestrator, memory_agent, insights_agent, adaptation_agent

    try:
        # Initialize database connection pool first
        try:
            from shared_libs.database.connection_pool import db_pool
            await db_pool.initialize()
        except Exception as e:
            pass

        # Initialize agents
        from services.orchestrator.main import HolisticOrchestrator
        from services.agents.memory.main import HolisticMemoryAgent
        from services.agents.insights.main import HolisticInsightsAgent
        from services.agents.adaptation.main import HolisticAdaptationEngine

        orchestrator = HolisticOrchestrator()
        memory_agent = HolisticMemoryAgent()
        insights_agent = HolisticInsightsAgent()
        adaptation_agent = HolisticAdaptationEngine()

        # ✅ ADD THIS: Initialize background job queue worker
        try:
            from services.background import get_job_queue
            job_queue = get_job_queue()
            await job_queue.start()
            logger.info("[STARTUP] Background worker started successfully")
        except Exception as e:
            logger.error(f"[STARTUP] Failed to start background worker: {e}")
            # Non-critical - continue without background archival

        # Initialize monitoring system
        if MONITORING_AVAILABLE:
            try:
                app.state.start_time = time.time()
                asyncio.create_task(monitor_health_continuously())

                await alert_manager.send_alert(
                    AlertSeverity.INFO,
                    "HolisticOS System Started",
                    {
                        "version": "2.0.0",
                        "environment": os.getenv("ENVIRONMENT", "production"),
                        "agents_initialized": 4,
                        "monitoring_enabled": True,
                        "background_worker": True  # ✅ NEW: Indicate worker is running
                    },
                    service="system"
                )
            except Exception as e:
                pass

    except Exception as e:
        print(f"❌ Error initializing agents: {e}")
        if MONITORING_AVAILABLE:
            try:
                await alert_manager.send_alert(
                    AlertSeverity.CRITICAL,
                    "HolisticOS Startup Failed",
                    {
                        "error": str(e),
                        "startup_phase": "agent_initialization"
                    },
                    service="system"
                )
            except:
                pass
"""

# Full modified shutdown_agents() function:
"""
@app.on_event("shutdown")
async def shutdown_agents():
    try:
        print("🛑 Shutting down HolisticOS Multi-Agent System...")

        # Stop behavior analysis scheduler
        from services.scheduler.behavior_analysis_scheduler import stop_behavior_analysis_scheduler
        await stop_behavior_analysis_scheduler()

        # ✅ ADD THIS: Stop background worker
        try:
            from services.background import get_job_queue
            job_queue = get_job_queue()
            await job_queue.stop()
            logger.info("[SHUTDOWN] Background worker stopped")
        except Exception as e:
            logger.error(f"[SHUTDOWN] Failed to stop background worker: {e}")

        # Close database connection pool
        try:
            from shared_libs.database.connection_pool import db_pool
            await db_pool.close()
        except Exception as e:
            pass

    except Exception as e:
        print(f"❌ Error during shutdown: {e}")
"""
