from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import logging
import os
import time
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple FastAPI app specifically for Vercel deployment
app = FastAPI(title="NZX API")

# Configure CORS with explicit values for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted by Vercel's own CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data for basic endpoints
ASSET_TYPES = ["BUILDING", "LAND", "INDUSTRIAL", "RETAIL", "OFFICE", "WAREHOUSE", "OTHER"]

SAMPLE_PORTFOLIOS = [
    {"id": "1", "name": "Demo Portfolio", "description": "Demo portfolio for testing", "organization_id": "org1"},
    {"id": "2", "name": "Test Portfolio", "description": "Another test portfolio", "organization_id": "org1"}
]

# Basic endpoints that don't require database access
@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/api/health")
async def health():
    return {
        "status": "ok", 
        "timestamp": time.time(),
        "environment": os.environ.get("VERCEL_ENV", "production")
    }

@app.get("/api/asset-types")
async def asset_types():
    return ASSET_TYPES

@app.get("/api/portfolios")
async def portfolios():
    return SAMPLE_PORTFOLIOS

# Vercel serverless handler
def handler(event, context):
    path = event.get('path', '/')
    
    # Basic routing
    if path == '/' or path == '/api/health':
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "ok", "message": "API is running"}),
            "headers": {"Content-Type": "application/json"}
        }
    elif path == '/api/asset-types':
        return {
            "statusCode": 200,
            "body": json.dumps(ASSET_TYPES),
            "headers": {"Content-Type": "application/json"}
        }
    elif path == '/api/portfolios':
        return {
            "statusCode": 200,
            "body": json.dumps(SAMPLE_PORTFOLIOS),
            "headers": {"Content-Type": "application/json"}
        }
    else:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Not found"}),
            "headers": {"Content-Type": "application/json"}
        }

# Create the handler for Vercel
handler = Mangum(app) 