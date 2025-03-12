#!/usr/bin/env python
"""
Simple script to run the FastAPI server with the appropriate environment settings.
Usage:
  python start.py [--env ENV]
"""
import os
import sys
import argparse
from dotenv import load_dotenv
import uvicorn

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start the NZX API server")
    parser.add_argument("--env", choices=["development", "production"], default="development",
                      help="Environment to run in (default: development)")
    args = parser.parse_args()
    
    # Load appropriate .env file
    env_file = f".env.{args.env}" if os.path.exists(f".env.{args.env}") else ".env"
    load_dotenv(env_file)
    print(f"Starting server with configuration from {env_file}")
    
    # Set the host and port
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    
    # Show debug info
    print(f"⚙️ Environment: {os.environ.get('ENVIRONMENT', 'not set')}")
    print(f"🔒 SUPABASE_URL: {'is set' if os.environ.get('SUPABASE_URL') else 'not set'}")
    print(f"🚪 CORS origins: {os.environ.get('CORS_ORIGINS', 'not set')}")
    
    # Run the development server
    print(f"🚀 Starting server at http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    main()