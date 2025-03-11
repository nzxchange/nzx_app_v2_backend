import os
from supabase import create_client, Client
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Get environment variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

logger.info(f"Initializing Supabase with URL: {supabase_url[:10]}...")

# Initialize Supabase client
try:
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
    supabase = create_client(supabase_url, supabase_key)
    
    # Test the connection
    test_query = supabase.table("portfolios").select("count").execute()
    logger.info("Supabase connection test successful")
    
except Exception as e:
    logger.error(f"Error initializing Supabase client: {str(e)}")
    raise RuntimeError(f"Supabase client not initialized properly. Error: {str(e)}") 