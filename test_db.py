import os
from dotenv import load_dotenv
from supabase import create_client
import json

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase = create_client(supabase_url, supabase_key)

def print_response(response):
    """Pretty print a Supabase response"""
    if hasattr(response, 'data'):
        print(f"Data: {json.dumps(response.data, indent=2)}")
    if hasattr(response, 'error'):
        print(f"Error: {response.error}")

# Test functions
def test_organizations():
    print("\n=== Testing organizations table ===")
    try:
        response = supabase.table("organizations").select("*").limit(5).execute()
        print(f"Success! Found {len(response.data)} organizations")
        print_response(response)
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_portfolios():
    print("\n=== Testing portfolios table ===")
    try:
        response = supabase.table("portfolios").select("*").limit(5).execute()
        print(f"Success! Found {len(response.data)} portfolios")
        print_response(response)
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_assets():
    print("\n=== Testing assets table ===")
    try:
        response = supabase.table("assets").select("*").limit(5).execute()
        print(f"Success! Found {len(response.data)} assets")
        print_response(response)
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_policies():
    print("\n=== Testing RLS policies ===")
    try:
        # Since we can't directly query pg_policies, let's check if we can access the tables
        print("Testing access to tables with current policies...")
        test_organizations()
        test_portfolios()
        test_assets()
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

# Run tests
if __name__ == "__main__":
    print("Testing Supabase connection...")
    test_organizations()
    test_portfolios()
    test_assets()
    test_policies()
    print("Tests completed.") 