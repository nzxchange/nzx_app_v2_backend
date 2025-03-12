import os
from fastapi import FastAPI
from mangum import Mangum
import json

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Debug API is running"}

@app.get("/debug/environment")
async def get_environment():
    # Return sanitized environment variables (exclude secrets)
    env_vars = {k: v for k, v in os.environ.items() 
                if not any(secret in k.lower() for secret in 
                          ["key", "password", "secret", "token"])}
    return {"environment": env_vars}

@app.get("/debug/test")
async def test():
    return {"status": "ok"}

handler = Mangum(app) 