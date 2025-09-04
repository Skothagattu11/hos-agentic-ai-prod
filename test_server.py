#!/usr/bin/env python3
"""
Test server to verify time_blocks JOIN is working
"""
import os
import sys
from fastapi import FastAPI, HTTPException
import uvicorn
from typing import Optional

# Add project path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    from supabase import create_client, Client
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        sys.exit(1)
        
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Supabase client initialized")
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Setup error: {e}")
    sys.exit(1)

app = FastAPI(title="Time Blocks Test Server")

@app.get("/api/calendar/available-items/{profile_id}")
async def get_available_plan_items(
    profile_id: str,
    date: Optional[str] = None,
    include_calendar_status: bool = True
):
    """Test endpoint with CORRECTED JOIN syntax"""
    try:
        # Use the CORRECTED JOIN syntax with specific constraint name
        query = supabase.table("plan_items")\
            .select("""
                *,
                time_blocks!fk_plan_items_time_block_id (
                    id,
                    block_title,
                    time_range,
                    purpose,
                    why_it_matters,
                    connection_to_insights,
                    health_data_integration
                )
            """)\
            .eq("profile_id", profile_id)
        
        result = query.order("scheduled_time").execute()
        
        return {
            "success": True,
            "date": date or "2025-09-03",
            "total_items": len(result.data) if result.data else 0,
            "plan_items": result.data or [],
            "server_version": "UPDATED with fk_plan_items_time_block_id constraint"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available plan items: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Test server with corrected JOIN syntax"}

if __name__ == "__main__":
    print("🚀 Starting Test Server with Corrected JOIN Syntax")
    print("   http://localhost:8002/api/calendar/available-items/{profile_id}")
    print("   http://localhost:8002/docs")
    print("=" * 50)
    
    uvicorn.run(
        "test_server:app",
        host="0.0.0.0",
        port=8002,
        reload=False
    )