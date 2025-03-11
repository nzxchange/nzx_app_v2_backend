from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from app.core.db import supabase
import json
import base64
import os
import jwt
from jwt.exceptions import PyJWTError

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Get the JWT secret from environment variables or use a default for development
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "your-supabase-jwt-secret")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    logger.info(f"Authenticating user with token: {credentials.credentials[:10]}...")
    try:
        token = credentials.credentials
        
        # Try to verify the token with PyJWT first
        try:
            # Decode the token with the JWT secret
            payload = jwt.decode(
                token, 
                JWT_SECRET, 
                algorithms=["HS256"]
            )
            
            if 'sub' in payload:
                user_id = payload['sub']
                logger.info(f"User authenticated via JWT decode: {user_id}")
                return user_id
            
            logger.warning(f"JWT does not contain 'sub' claim: {payload}")
            
        except PyJWTError as jwt_error:
            logger.warning(f"JWT decode failed, trying Supabase auth: {str(jwt_error)}")
        
        # If JWT decode fails, try Supabase auth
        try:
            response = supabase.auth.get_user(token)
            user = response.user
            
            if not user:
                raise Exception("User not found in token")
                
            logger.info(f"User authenticated via Supabase: {user.id}")
            return user.id
            
        except Exception as auth_error:
            logger.warning(f"Supabase auth failed, trying manual decode: {str(auth_error)}")
            
            # Try to decode the JWT manually as a last resort
            try:
                # Split the token into parts
                parts = token.split('.')
                if len(parts) != 3:
                    raise Exception("Invalid JWT format")
                
                # Decode the payload (middle part)
                payload_b64 = parts[1]
                # Add padding if needed
                payload_b64 += '=' * (4 - len(payload_b64) % 4) if len(payload_b64) % 4 != 0 else ''
                
                try:
                    payload_bytes = base64.b64decode(payload_b64)
                    payload = json.loads(payload_bytes.decode('utf-8'))
                    
                    if 'sub' in payload:
                        user_id = payload['sub']
                        logger.info(f"User authenticated via manual JWT decode: {user_id}")
                        return user_id
                    
                    logger.warning(f"JWT does not contain 'sub' claim: {payload}")
                    raise HTTPException(status_code=401, detail="Invalid token format")
                    
                except Exception as decode_error:
                    logger.error(f"Error decoding JWT payload: {str(decode_error)}")
                    raise HTTPException(status_code=401, detail=f"Token decode error: {str(decode_error)}")
            
            except Exception as jwt_error:
                logger.error(f"All authentication methods failed: {str(jwt_error)}")
                raise HTTPException(status_code=401, detail=f"Authentication failed: {str(jwt_error)}")
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}") 