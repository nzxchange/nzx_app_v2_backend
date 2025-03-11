from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.db import supabase
import logging
import os
import time
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    redirect_url: str

class MagicLinkRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    token: str
    password: str

class ProfileCreateRequest(BaseModel):
    user_id: str
    email: EmailStr
    company_name: str

@router.post("/signin")
async def sign_in(request: SignInRequest):
    """Sign in with email and password"""
    try:
        logger.info(f"Sign in attempt for email: {request.email}")
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not response.user:
            logger.warning(f"Sign in failed for email: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        logger.info(f"Sign in successful for user: {response.user.id}")
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email
            }
        }
    except Exception as e:
        logger.error(f"Sign in error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/signup")
async def sign_up(request: SignUpRequest):
    """Sign up with email and password"""
    try:
        logger.info(f"Sign up attempt for email: {request.email}")
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password
        })
        
        if response.error:
            logger.error(f"Sign up error: {response.error.message}")
            raise HTTPException(status_code=400, detail=response.error.message)
        
        if not response.user:
            logger.warning(f"Sign up failed for email: {request.email}")
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        # Retry logic for creating user profile
        for attempt in range(3):
            profile_data = {
                "id": response.user.id,
                "company_name": request.name or "Default Company",
                "role": "user",  # Default role
                "created_at": "now()",
                "updated_at": "now()",
                "organization_id": None,  # Adjust as needed
                "email": request.email
            }
            logger.info(f"Attempt {attempt + 1}: Inserting profile data: {profile_data}")
            profile_response = supabase.table("profiles").insert(profile_data).execute()
            
            if not profile_response.error:
                logger.info(f"Profile created successfully for user: {response.user.id}")
                break
            
            logger.error(f"Profile creation error: {profile_response.error.message}")
            if attempt < 2:
                logger.info("Retrying profile creation...")
                time.sleep(3)  # 3-second delay
            else:
                raise HTTPException(status_code=400, detail="Failed to create profile after multiple attempts")
        
        return {
            "message": "User created successfully. Please check your email for verification.",
            "user": {
                "id": response.user.id,
                "email": response.user.email
            }
        }
    except Exception as e:
        logger.error(f"Sign up error: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail="An error occurred during sign up"
        )

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Send a password reset email"""
    try:
        logger.info(f"Password reset request for email: {request.email}")
        
        # Use Supabase to send a password reset email
        response = supabase.auth.reset_password_for_email(
            request.email,
            options={"redirect_to": f"{request.redirect_url}/auth/reset-password-confirm"}
        )
        
        if response.error:
            logger.error(f"Error in sending reset email: {response.error.message}")
            raise HTTPException(status_code=400, detail=response.error.message)
        
        logger.info("Password reset email sent successfully")
        return {"success": True, "message": "Password reset email sent"}
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update-password")
async def update_password(request: UpdatePasswordRequest):
    """Update user password with reset token"""
    try:
        logger.info(f"Updating password with token: {request.token}")
        
        # Use Supabase to update the password
        response = supabase.auth.api.update_user(
            request.token,
            {"password": request.password}
        )
        
        if response.error:
            logger.error(f"Error updating password: {response.error.message}")
            raise HTTPException(status_code=400, detail=response.error.message)
        
        logger.info("Password updated successfully")
        return {"success": True, "message": "Password updated successfully"}
    except Exception as e:
        logger.error(f"Error updating password: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/debug-token")
async def debug_token(token: str):
    """Debug endpoint to check token validity"""
    try:
        import jwt
        import base64
        import json
        
        # Try to decode the token without verification
        parts = token.split('.')
        if len(parts) != 3:
            return {"valid": False, "error": "Invalid JWT format"}
        
        # Decode header and payload
        header_b64 = parts[0]
        payload_b64 = parts[1]
        
        # Add padding if needed
        header_b64 += '=' * (4 - len(header_b64) % 4) if len(header_b64) % 4 != 0 else ''
        payload_b64 += '=' * (4 - len(payload_b64) % 4) if len(payload_b64) % 4 != 0 else ''
        
        header = json.loads(base64.b64decode(header_b64).decode('utf-8'))
        payload = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
        
        # Try to verify with Supabase
        try:
            user = supabase.auth.get_user(token)
            supabase_valid = True
        except Exception as e:
            supabase_valid = False
            supabase_error = str(e)
        
        return {
            "valid": True,
            "header": header,
            "payload": payload,
            "supabase_valid": supabase_valid,
            "supabase_error": supabase_error if not supabase_valid else None
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}

@router.post("/magic-link")
async def magic_link(request: MagicLinkRequest):
    """Send magic link for passwordless login"""
    try:
        logger.info(f"Magic link request for email: {request.email}")
        response = supabase.auth.sign_in_with_otp({
            "email": request.email
        })
        logger.info(f"Magic link email sent to: {request.email}")
        return {"message": "Magic link email sent"}
    except Exception as e:
        logger.error(f"Magic link error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/debug-jwt")
async def debug_jwt():
    """Debug endpoint to check JWT configuration"""
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "not-set")
    jwt_secret_masked = jwt_secret[:5] + "..." + jwt_secret[-5:] if len(jwt_secret) > 10 else "too-short"
    
    return {
        "jwt_secret_set": jwt_secret != "not-set",
        "jwt_secret_preview": jwt_secret_masked,
        "jwt_secret_length": len(jwt_secret),
        "environment": {
            "SUPABASE_URL": os.getenv("SUPABASE_URL", "not-set")[:10] + "...",
            "FRONTEND_URL": os.getenv("FRONTEND_URL", "not-set"),
        }
    }

@router.post("/create-profile")
async def create_profile(request: ProfileCreateRequest):
    """Create a profile for a newly registered user"""
    try:
        logger.info(f"Creating profile for user ID: {request.user_id}")
        
        profile_data = {
            "id": request.user_id,
            "email": request.email,
            "company_name": request.company_name,
            "role": "user",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        profile_response = supabase.table("profiles").insert(profile_data).execute()
        
        if profile_response.error:
            logger.error(f"Profile creation error: {profile_response.error.message}")
            raise HTTPException(status_code=400, detail=profile_response.error.message)
        
        logger.info(f"Profile created successfully for user: {request.user_id}")
        return {"success": True, "message": "Profile created successfully"}
    except Exception as e:
        logger.error(f"Error creating profile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 