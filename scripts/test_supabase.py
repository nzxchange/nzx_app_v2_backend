import os
from dotenv import load_dotenv
from supabase import create_client
import sys
import httpx

def test_supabase_connection():
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        print(f"SUPABASE_URL: {'✓' if url else '✗'}")
        print(f"SUPABASE_KEY: {'✓' if key else '✗'}")
        return False
    
    print(f"Testing connection to: {url}")
    
    try:
        # Try to create client
        supabase = create_client(url, key)
        
        # Test a simple query
        response = supabase.table("profiles").select("count").execute()
        
        print("✅ Successfully connected to Supabase!")
        print(f"Response data: {response.data}")
        return True
        
    except httpx.ConnectError as e:
        print("❌ Connection Error:")
        print("  - Could not connect to Supabase")
        print("  - Check your internet connection")
        print("  - Check if the Supabase URL is correct")
        print(f"  - Error: {str(e)}")
        return False
        
    except Exception as e:
        print("❌ Error:")
        print(f"  {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Supabase connection...")
    success = test_supabase_connection()
    sys.exit(0 if success else 1)