import os
from supabase import create_client, Client
import logging
from dotenv import load_dotenv
import time
import httpx

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def create_supabase_client(retries=3, delay=1):
    """Create Supabase client with retries"""
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Missing Supabase credentials in environment variables")
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
        )

    for attempt in range(retries):
        try:
            client = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Test the connection
            if os.getenv("ENVIRONMENT") == "development":
                client.table("profiles").select("count").execute()
            logger.info("Supabase client initialized successfully")
            return client
        except httpx.ConnectError as e:
            if attempt == retries - 1:  # Last attempt
                logger.error(f"Failed to connect to Supabase after {retries} attempts")
                raise
            logger.warning(f"Connection attempt {attempt + 1} failed, retrying...")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise

# Initialize the client
try:
    supabase = create_supabase_client()
except Exception as e:
    logger.error(f"Could not initialize Supabase: {str(e)}")
    # In production, we might want to handle this more gracefully
    if os.getenv("ENVIRONMENT") == "development":
        raise
    else:
        # In production, we'll initialize with None and handle errors at the endpoint level
        supabase = None