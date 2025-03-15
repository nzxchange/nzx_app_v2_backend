from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from app.core.db import supabase
import os

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simplified auth handler that works with Supabase tokens"""
    logger.info(f"Authenticating user with token: {credentials.credentials[:10]}...")
    
    try:
        token = credentials.credentials
        
        # Use Supabase's built-in authentication
        response = supabase.auth.get_user(token)
        
        if not response.user:
            logger.error("User not found in token")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
            
        logger.info(f"User authenticated: {response.user.id}")
        return response.user.id
            
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed") 