from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings
import logging
import time
import os
import uvicorn
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set up
    print(f"Starting application with CORS origins: {settings.CORS_ORIGINS}")
    yield
    # Clean up

app = FastAPI(
    title="NZX API",
    description="API for NetZeroXchange platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=[m.strip() for m in settings.CORS_METHODS.split(",")],
    allow_headers=[h.strip() for h in settings.CORS_HEADERS.split(",")],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint for testing"""
    print("Root endpoint called")
    return {
        "status": "ok",
        "message": "API is running",
        "timestamp": time.time()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT
    }

@app.get("/routes")
async def list_routes():
    """List all registered routes"""
    route_list = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        route_list.append(f"{route.path} - {methods}")
    return {"routes": route_list}

@app.get("/debug/simple")
async def debug_simple():
    print("Simple debug endpoint called")
    return {"status": "ok", "timestamp": time.time()}

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", settings.PORT))
    print(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port)