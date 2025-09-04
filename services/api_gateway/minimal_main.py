#!/usr/bin/env python3
"""
Minimal FastAPI server to test OpenAPI schema generation
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

# Create minimal FastAPI app
app = FastAPI(
    title="HolisticOS Minimal API", 
    version="1.0.0",
    description="Minimal version for OpenAPI debugging"
)

# Basic Pydantic model
class HealthResponse(BaseModel):
    status: str
    message: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "HolisticOS Minimal API", "status": "running"}

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", message="Service is running")

@app.get("/debug/openapi")
async def debug_openapi_generation():
    """Debug endpoint to test OpenAPI schema generation"""
    try:
        schema = app.openapi()
        return {
            "status": "success",
            "message": "OpenAPI schema generated successfully",
            "path_count": len(schema.get("paths", {})),
            "component_count": len(schema.get("components", {}).get("schemas", {}))
        }
    except Exception as e:
        import traceback
        return {
            "status": "error", 
            "message": f"OpenAPI generation failed: {str(e)}",
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)