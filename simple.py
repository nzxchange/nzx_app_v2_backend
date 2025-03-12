import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Load environment variables
if os.path.exists(".env"):
    print("Loading .env file")
    from dotenv import load_dotenv
    load_dotenv()
    
app = FastAPI(title="NZX API - Simple Version")

# Configure CORS with explicit values (not from env vars)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "NZX API is running in simple mode"}

@app.get("/api/health")
async def health_check():
    # Return basic environment info for debugging
    return {
        "status": "ok",
        "message": "API is running in simple mode"
    }

# For Vercel deployment
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 