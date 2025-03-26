from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json

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

# Define a direct handler for Vercel without using Mangum
def handler(event, context):
    """Pure Python handler for Vercel serverless"""
    # Simple static path mapping
    path = event.get('path', '/')
    
    if path == '/':
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "NZX API is running", "version": "0.1.0"}),
            "headers": {"Content-Type": "application/json"}
        }
    elif path == '/api/health':
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "ok", "environment": os.environ.get("ENVIRONMENT", "production")}),
            "headers": {"Content-Type": "application/json"}
        }
    elif path == '/api/debug/env':
        return {
            "statusCode": 200,
            "body": json.dumps({
                "supabase_url_set": bool(os.environ.get("SUPABASE_URL")),
                "supabase_key_set": bool(os.environ.get("SUPABASE_KEY")),
                "env": os.environ.get("ENVIRONMENT", "production")
            }),
            "headers": {"Content-Type": "application/json"}
        }
    else:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Not found"}),
            "headers": {"Content-Type": "application/json"}
        } 