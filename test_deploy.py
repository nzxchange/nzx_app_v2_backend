from fastapi import FastAPI
from mangum import Mangum
import os

app = FastAPI(title="NZX API Test")

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Minimal test deployment is running"
    }

@app.get("/api/version")
async def version():
    return {"version": "0.1.0", "environment": os.environ.get("ENVIRONMENT", "unknown")}

# For Vercel serverless function
handler = Mangum(app) 