import os
from supabase import create_client, Client
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def get_supabase_client():
    """Get Supabase client with error handling"""
    try:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials")
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
            
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        raise

# Initialize the client
try:
    supabase = get_supabase_client()
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Could not initialize Supabase: {str(e)}")
    raise

# Test the connection
if supabase:
    test_query = supabase.table("portfolios").select("count").execute()
    logger.info("Supabase connection test successful")
else:
    logger.warning("Supabase client not initialized, skipping connection test") 