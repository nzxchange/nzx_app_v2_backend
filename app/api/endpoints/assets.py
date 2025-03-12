from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.models.asset import (
    Organization,
    Portfolio,
    Asset,
    AssetTenant,
    AssetDocument,
    AssetType
)
from app.core.auth import get_current_user
from app.core.db import supabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Add the missing model definition
class OrganizationCreate(BaseModel):
    name: str
    registration_number: Optional[str] = None
    address: Optional[str] = None

@router.get("/organizations", response_model=List[Organization])
async def get_organizations(current_user: str = Depends(get_current_user)):
    try:
        response = supabase.table("organizations").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/organizations", response_model=Organization)
async def create_organization(org: OrganizationCreate, current_user: str = Depends(get_current_user)):
    try:
        response = supabase.table("organizations").insert({
            **org.dict(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/portfolios", response_model=List[Portfolio])
async def get_portfolios(current_user: str = Depends(get_current_user)):
    """Get all portfolios for the current user's organization"""
    logger.info(f"Get portfolios request from user: {current_user}")
    
    try:
        # First, check if the user exists in the profiles table
        logger.info(f"Checking if user {current_user} exists in profiles")
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        logger.info(f"Profile response: {profile_response}")
        
        if not profile_response.data:
            logger.warning(f"No profile found for user {current_user}")
            return []
            
        org_id = profile_response.data.get("organization_id")
        if not org_id:
            logger.warning(f"No organization_id found for user {current_user}")
            return []
            
        # Get portfolios for the organization
        logger.info(f"Fetching portfolios for organization: {org_id}")
        portfolios_response = supabase.table("portfolios").select("*").eq("organization_id", org_id).execute()
        
        logger.info(f"Found {len(portfolios_response.data)} portfolios")
        return portfolios_response.data
        
    except Exception as e:
        logger.error(f"Error in get_portfolios: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/portfolios", response_model=Portfolio)
async def create_portfolio(portfolio: Portfolio, current_user: str = Depends(get_current_user)):
    """Create a new portfolio for the current user's organization"""
    logger.info(f"Create portfolio request from user: {current_user}")
    
    try:
        # First, check if the user exists in the profiles table
        logger.info(f"Checking if user {current_user} exists in profiles")
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        logger.info(f"Profile response: {profile_response}")
        
        # If user doesn't have a profile, create one with a default organization
        if not profile_response.data:
            logger.info(f"No profile found for user {current_user}, creating one")
            
            # Create a default organization
            org_data = {
                "name": f"Organization for {current_user}",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            org_response = supabase.table("organizations").insert(org_data).execute()
            
            if not org_response.data or len(org_response.data) == 0:
                logger.error("Failed to create organization")
                raise HTTPException(status_code=500, detail="Failed to create organization")
                
            org_id = org_response.data[0]["id"]
            logger.info(f"Created organization with ID: {org_id}")
            
            # Create a profile for the user
            profile_data = {
                "id": current_user,
                "organization_id": org_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            profile_response = supabase.table("profiles").insert(profile_data).execute()
            
            if not profile_response.data or len(profile_response.data) == 0:
                logger.error("Failed to create profile")
                raise HTTPException(status_code=500, detail="Failed to create profile")
                
            logger.info(f"Created profile for user {current_user}")
            
        else:
            # Get the organization ID from the profile
            org_id = profile_response.data.get("organization_id")
            
            # If user doesn't have an organization, create one
            if not org_id:
                logger.info(f"No organization found for user {current_user}, creating one")
                
                # Create a default organization
                org_data = {
                    "name": f"Organization for {current_user}",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                org_response = supabase.table("organizations").insert(org_data).execute()
                
                if not org_response.data or len(org_response.data) == 0:
                    logger.error("Failed to create organization")
                    raise HTTPException(status_code=500, detail="Failed to create organization")
                    
                org_id = org_response.data[0]["id"]
                logger.info(f"Created organization with ID: {org_id}")
                
                # Update the user's profile with the organization ID
                profile_update = supabase.table("profiles").update({
                    "organization_id": org_id,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", current_user).execute()
                
                logger.info(f"Updated profile with organization ID: {profile_update}")
        
        # Now create the portfolio
        portfolio_data = {
            "name": portfolio.name,
            "description": portfolio.description,
            "organization_id": org_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Creating portfolio: {portfolio_data}")
        
        portfolio_response = supabase.table("portfolios").insert(portfolio_data).select().execute()
        
        if not portfolio_response.data or len(portfolio_response.data) == 0:
            logger.error("Failed to create portfolio")
            raise HTTPException(status_code=500, detail="Failed to create portfolio")
            
        logger.info(f"Created portfolio: {portfolio_response.data[0]}")
        return portfolio_response.data[0]
        
    except Exception as error:
        logger.error(f"Error in create_portfolio: {str(error)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(error))

@router.get("/", response_model=List[Asset])
async def get_assets(current_user: str = Depends(get_current_user)):
    try:
        # Get the user's organization
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            return []
            
        # Get assets for the user's organization
        assets_response = supabase.table("assets").select("*").eq("organization_id", profile_response.data["organization_id"]).execute()
        
        return assets_response.data or []
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/assets", response_model=Asset)
async def create_asset(asset: Asset, current_user: str = Depends(get_current_user)):
    """Create a new asset"""
    logger.info(f"Create asset request from user: {current_user}")
    
    try:
        # Validate asset type
        if asset.asset_type not in [t.value for t in AssetType]:
            logger.error(f"Invalid asset type: {asset.asset_type}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid asset type. Must be one of: {', '.join([t.value for t in AssetType])}"
            )
            
        # Get the user's organization
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            raise HTTPException(status_code=400, detail="User has no organization")
            
        org_id = profile_response.data["organization_id"]
        
        # Create the asset with organization_id
        asset_data = {
            **asset.dict(exclude={'id'}),
            "organization_id": org_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Creating asset with data: {asset_data}")
        response = supabase.table("assets").insert(asset_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create asset")
            
        return response.data[0]
        
    except Exception as e:
        logger.error(f"Error in create_asset: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/assets/{asset_id}/tenants", response_model=AssetTenant)
async def assign_tenant(
    asset_id: str,
    tenant: AssetTenant,
    current_user: str = Depends(get_current_user)
):
    try:
        response = supabase.table("asset_tenants").insert({
            **tenant.dict(),
            "asset_id": asset_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/assets/{asset_id}/documents")
async def upload_document(
    asset_id: str,
    document_type: str,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    try:
        # First, create a document record
        doc_response = supabase.table("documents").insert({
            "user_id": current_user,
            "filename": file.filename,
            "file_type": file.content_type,
            "file_size": 0  # Will be updated after upload
        }).execute()
        
        document_id = doc_response.data[0]["id"]
        
        # Create asset document link
        asset_doc_response = supabase.table("asset_documents").insert({
            "asset_id": asset_id,
            "document_id": document_id,
            "document_type": document_type,
            "upload_date": datetime.utcnow().isoformat()
        }).execute()
        
        # Handle file upload to Supabase storage
        file_content = await file.read()
        storage_path = f"documents/{asset_id}/{document_id}/{file.filename}"
        
        supabase.storage.from_("documents").upload(
            storage_path,
            file_content
        )
        
        return asset_doc_response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/types", response_model=List[str])
async def get_asset_types():
    logger.info("Get asset types request received")
    types = [asset_type.value for asset_type in AssetType]
    logger.info(f"Returning asset types: {types}")
    return types

@router.get("/debug-portfolios", response_model=List[Portfolio])
async def debug_portfolios(current_user: str = Depends(get_current_user)):
    """Debug endpoint that returns hardcoded portfolio data"""
    logger.info(f"Debug portfolios request from user: {current_user}")
    
    # Return hardcoded data that matches the Portfolio model
    hardcoded_portfolios = [
        {
            "id": "1",
            "name": "Test Portfolio 1",
            "description": "This is a test portfolio",
            "organization_id": "org123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "2",
            "name": "Test Portfolio 2",
            "description": "Another test portfolio",
            "organization_id": "org123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    logger.info(f"Returning hardcoded portfolios: {hardcoded_portfolios}")
    return hardcoded_portfolios

@router.get("/simple-portfolios")
async def get_simple_portfolios(current_user: str = Depends(get_current_user)):
    """Simple endpoint that returns hardcoded portfolios without model validation"""
    logger.info(f"Simple portfolios request from user: {current_user}")
    
    # Return hardcoded data
    return [
        {
            "id": "1",
            "name": "Portfolio 1"
        },
        {
            "id": "2",
            "name": "Portfolio 2"
        }
    ]

@router.get("/simple-types")
async def get_simple_asset_types():
    """Simple endpoint that returns asset types without model validation"""
    logger.info("Simple asset types request received")
    
    return ["office", "retail", "industrial", "residential", "mixed_use", "commercial"]

@router.get("/direct-portfolios")
async def get_direct_portfolios(current_user: str = Depends(get_current_user)):
    """Emergency endpoint that uses direct SQL to get portfolios"""
    logger.info(f"Direct portfolios request from user: {current_user}")
    
    try:
        # Get all portfolios in the system - for debugging only
        query = "SELECT * FROM portfolios LIMIT 10"
        response = supabase.rpc('execute_sql', {'query': query}).execute()
        
        logger.info(f"Direct portfolios query response: {response}")
        
        return {
            "success": True,
            "data": response.data,
            "user_id": current_user
        }
    except Exception as error:
        logger.error(f"Error in direct portfolios query: {str(error)}")
        return {
            "success": False,
            "error": str(error),
            "user_id": current_user
        }

@router.get("/debug-user-profile")
async def debug_user_profile(current_user: str = Depends(get_current_user)):
    """Debug endpoint to check user profile and organization"""
    logger.info(f"Debug user profile request from user: {current_user}")
    
    try:
        # Get the user's profile
        profile_response = supabase.table("profiles").select("*").eq("id", current_user).single().execute()
        
        # Get the user's organization if available
        org_id = None
        org_data = None
        if profile_response.data and profile_response.data.get("organization_id"):
            org_id = profile_response.data["organization_id"]
            org_response = supabase.table("organizations").select("*").eq("id", org_id).single().execute()
            org_data = org_response.data
            
        # Get portfolios for the organization if available
        portfolios_data = []
        if org_id:
            portfolios_response = supabase.table("portfolios").select("*").eq("organization_id", org_id).execute()
            portfolios_data = portfolios_response.data
            
        return {
            "user_id": current_user,
            "profile": profile_response.data,
            "organization": org_data,
            "portfolios": portfolios_data,
            "portfolios_count": len(portfolios_data) if portfolios_data else 0
        }
    except Exception as error:
        logger.error(f"Error in debug_user_profile: {str(error)}", exc_info=True)
        return {
            "error": str(error),
            "user_id": current_user
        }
