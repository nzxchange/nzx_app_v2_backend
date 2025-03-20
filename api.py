from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app - keeping it minimal for serverless
app = FastAPI(title="NZX API")

# Configure CORS with permissive settings for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint for health checks"""
    return {
        "message": "NZX API is running",
        "version": "0.1.0",
        "env": os.environ.get("ENVIRONMENT", "production")
    }

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok", 
        "environment": os.environ.get("ENVIRONMENT", "production")
    }

@app.get("/api/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables (use with caution)"""
    return {
        "supabase_url_set": bool(os.environ.get("SUPABASE_URL")),
        "supabase_key_set": bool(os.environ.get("SUPABASE_KEY")),
        "env": os.environ.get("ENVIRONMENT", "production")
    }

# Create handler for Vercel serverless
handler = Mangum(app) 