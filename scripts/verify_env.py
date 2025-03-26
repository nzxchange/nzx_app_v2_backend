import os
from dotenv import load_dotenv
from supabase import create_client

def verify_environment():
    # Load environment variables
    load_dotenv()
    
    # Required variables
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "ENVIRONMENT",
        "PORT"
    ]
    
    # Check for missing variables
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        return False
    
    # Test Supabase connection
    try:
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        test = supabase.table("profiles").select("count").execute()
        print("✅ Supabase connection successful")
        return True
    except Exception as e:
        print("❌ Supabase connection failed:")
        print(f"  Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Verifying environment setup...")
    if verify_environment():
        print("✅ All checks passed!")
    else:
        print("❌ Environment verification failed") 