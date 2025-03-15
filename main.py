from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os
import logging
from app.api.api import api_router
from mangum import Mangum
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NetZeroXchange API",
    description="API for NetZeroXchange platform",
    version="0.1.0",
)

# Configure CORS - use explicit values for Vercel
origins = [
    "http://localhost:3000",
    "https://app.netzeroxchange.com",
    # Add other allowed origins here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# Basic health check that doesn't require auth
@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": os.environ.get("ENVIRONMENT", "production")
    }

# Exception handler for cleaner errors
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

@app.middleware("http")
async def check_supabase_client(request: Request, call_next):
    try:
        from app.core.db import supabase
        if not supabase:
            raise HTTPException(status_code=500, detail="Database client not initialized")
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Middleware error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Create handler for Vercel
handler = Mangum(app)

# Only run the server directly when not on Vercel
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)