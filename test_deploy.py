from fastapi import FastAPI
from mangum import Mangum
import os
import sys
import traceback

app = FastAPI(title="NZX API Test")

@app.get("/")
async def root():
    try:
        # Get information about the environment
        python_version = sys.version
        env_vars = {k: v for k, v in os.environ.items()
                   if not any(secret in k.lower() for secret in 
                             ["key", "password", "secret", "token"])}
        
        return {
            "status": "ok",
            "message": "Minimal test deployment is running",
            "python_version": python_version,
            "env_keys": list(env_vars.keys()),
            "handler_type": str(type(handler))
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/api/version")
async def version():
    return {"version": "0.1.0", "environment": os.environ.get("ENVIRONMENT", "unknown")}

# Add better error handling for the Mangum handler
try:
    handler = Mangum(app, lifespan="off")  # Try disabling lifespan to reduce complexity
except Exception as e:
    print(f"Error initializing Mangum handler: {str(e)}")
    traceback.print_exc()
    
    # Provide a fallback handler
    def handler(event, context):
        return {
            "statusCode": 500,
            "body": '{"error": "Failed to initialize handler"}',
            "headers": {"Content-Type": "application/json"}
        } 