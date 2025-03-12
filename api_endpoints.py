from fastapi import FastAPI
import json

app = FastAPI()

# Sample data
ASSET_TYPES = ["BUILDING", "LAND", "INDUSTRIAL", "RETAIL", "OFFICE", "WAREHOUSE", "OTHER"]

SAMPLE_PORTFOLIOS = [
    {"id": "1", "name": "Demo Portfolio", "description": "Demo portfolio for testing", "organization_id": "org1"},
    {"id": "2", "name": "Test Portfolio", "description": "Another test portfolio", "organization_id": "org1"}
]

# Endpoints
@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/api/health")
async def health():
    return {"status": "ok"}

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