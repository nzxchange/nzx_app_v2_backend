import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env.development if it exists, fall back to .env
if os.path.exists(".env.development"):
    load_dotenv(".env.development")
    print("Loaded environment from .env.development")
else:
    load_dotenv()
    print("Loaded environment from .env")

if __name__ == "__main__":
    print("Starting local development server...")
    # Verify environment variables are loaded
    print(f"Environment: {os.environ.get('ENVIRONMENT', 'not set')}")
    print(f"SUPABASE_URL: {'is set' if os.environ.get('SUPABASE_URL') else 'not set'}")
    print(f"SUPABASE_KEY: {'is set' if os.environ.get('SUPABASE_KEY') else 'not set'}")
    
    # Run the development server with hot reload
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 