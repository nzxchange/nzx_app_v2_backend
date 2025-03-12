from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import logging
from app.core.config import settings
from app.api.api import api_router
from mangum import Mangum

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="NetZeroXchange API",
        description="API for NetZeroXchange platform",
        version="0.1.0",
    )
    
    # Include API router
    app.include_router(api_router, prefix="/api")
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),  # Use the safe method
        allow_credentials=True,
        allow_methods=["*"] if settings.CORS_METHODS == ["*"] else settings.CORS_METHODS,
        allow_headers=["*"] if settings.CORS_HEADERS == ["*"] else settings.CORS_HEADERS,
    )
    
    # Add a simple health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Simple health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.ENVIRONMENT
        }
    
    # Add a debug endpoint for CORS configuration
    @app.get("/api/debug/cors")
    async def debug_cors_settings():
        """Debug endpoint to show CORS settings"""
        return {
            "raw_cors_origins": settings.CORS_ORIGINS,
            "parsed_cors_origins": settings.get_cors_origins(),
            "allow_origins_type": type(settings.get_cors_origins()).__name__,
            "cors_methods": settings.CORS_METHODS,
            "cors_headers": settings.CORS_HEADERS,
            "environment": settings.ENVIRONMENT
        }
    
    return app

app = create_application()

# AWS Lambda handler
handler = Mangum(app, lifespan="off")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)