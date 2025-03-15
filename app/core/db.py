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

logger.info(f"Initializing Supabase with URL: {supabase_url[:10] if supabase_url else 'Not set'}...")

# Initialize Supabase client
try:
    if not supabase_url or not supabase_key:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not set")
        supabase = None
    else:
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized")
except Exception as e:
    logger.error(f"Error initializing Supabase client: {str(e)}")
    supabase = None

# Test the connection
if supabase:
    test_query = supabase.table("portfolios").select("count").execute()
    logger.info("Supabase connection test successful")
else:
    logger.warning("Supabase client not initialized, skipping connection test") 