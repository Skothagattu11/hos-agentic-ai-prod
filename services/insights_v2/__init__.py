"""
HolisticOS Insights System V2 - Standalone Implementation

This module provides a clean, standalone implementation of the insights system
following the architecture defined in INSIGHTS_IMPLEMENTATION_PLAN.md.

Phase 1 (Weeks 1-3): Daily Insights MVP
- Sprint 1.1: Data Pipeline & Baseline Service
- Sprint 1.2: AI Insights Generation Engine
- Sprint 1.3: API Endpoints & Background Jobs

Data Architecture:
- Health Data: Direct Sahha API calls (primary) + Supabase (fallback)
- Behavioral Data: Supabase only (plan_items, user_check_ins, analysis_results)
- Baselines: Calculated from Supabase 30-day window, cached in Redis
"""

__version__ = "2.0.0"
__phase__ = "Phase 1 - Daily Insights MVP"
