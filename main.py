from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from supabase import create_client, Client
from pydantic import BaseModel
from dotenv import load_dotenv
import signal
import sys
import logging
import json
from bill_reader import BillReader
import uuid
from app.api.endpoints import assets
from app.api.api import api_router
from app.models.asset import AssetType
import jwt
from jwt.exceptions import PyJWTError
from app.core.config import settings
from mangum import Mangum
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add a signal handler to properly handle Ctrl+C
def signal_handler(sig, frame):
    logger.info("Shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Load environment variables from .env file
load_dotenv()

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For simplicity, replace with your frontend URL in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app

app = create_application()

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting application in {settings.ENVIRONMENT} mode")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")

# Get environment variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Validate environment variables
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

# Modify the Supabase client initialization
try:
    logger.info(f"Initializing Supabase client with URL: {supabase_url}")
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Supabase client: {str(e)}")
    # Don't raise an error here, just log it and continue
    # We'll create a placeholder client that will be properly initialized later
    supabase = None

# Add a middleware to check Supabase connection on each request
@app.middleware("http")
async def check_supabase_connection(request, call_next):
    global supabase
    if supabase is None:
        try:
            supabase = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully in middleware")
        except Exception as e:
            logger.error(f"Still unable to initialize Supabase client: {str(e)}")
    
    response = await call_next(request)
    return response

# Debug endpoint to check if Supabase is connected
@app.get("/api/debug/env", include_in_schema=False)
async def debug_env():
    try:
        # Try a simple query to verify connection
        test_query = supabase.table("profiles").select("count", count="exact").limit(1).execute()
        connection_status = "connected" if test_query else "error"
    except Exception as e:
        connection_status = f"error: {str(e)}"
    
    return {
        "supabase_url": supabase_url is not None,
        "supabase_key": supabase_key is not None,
        "connection_status": connection_status
    }

# Pydantic models for request/response
class Profile(BaseModel):
    company_name: str
    role: str

class Document(BaseModel):
    filename: str
    file_type: str
    file_size: int

class Project(BaseModel):
    name: str
    description: Optional[str]
    location: Optional[str]
    project_type: str
    price_per_credit: float
    available_credits: int
    total_emissions_reduction: Optional[float]
    image_url: Optional[str]

class Credit(BaseModel):
    project_id: str
    quantity: int
    price_per_credit: float

class Notification(BaseModel):
    title: str
    message: str
    type: str

class Asset(BaseModel):
    portfolio_id: str
    name: str
    asset_type: str
    address: str
    total_area: float
    year_built: Optional[int]
    energy_rating: Optional[str]

class Organization(BaseModel):
    name: str
    registration_number: Optional[str]
    address: Optional[str]

class AssetDocument(BaseModel):
    asset_id: str
    document_type: str
    document_id: Optional[str] = None

class EnergyConsumptionData(BaseModel):
    asset_id: str
    period_start: str
    period_end: str
    consumption_kwh: float
    cost: float
    provider: Optional[str] = None
    meter_readings: Optional[Dict[str, Any]] = None

class EnergyInsight(BaseModel):
    asset_id: str
    insight_type: str
    description: str
    recommendation: Optional[str] = None
    potential_savings: Optional[float] = None
    created_at: str

# Security scheme
security = HTTPBearer()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        
        # Verify token with Supabase
        response = supabase.auth.get_user(token)
        user = response.user
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        return user.id
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

# Test endpoint
@app.get("/api/test")
async def test_api():
    return {"status": "ok", "message": "API is working"}

# Profile endpoints
@app.get("/api/profile")
async def get_profile(current_user: str = Depends(get_current_user)):
    try:
        profile_response = supabase.table("profiles").select("*").eq("id", current_user).single().execute()
        
        if not profile_response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        return profile_response.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/profile")
async def update_profile(profile: Profile, current_user: str = Depends(get_current_user)):
    try:
        response = supabase.table("profiles").update({
            "company_name": profile.company_name,
            "role": profile.role,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", current_user).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Document endpoints
@app.get("/api/documents")
async def get_documents(current_user: str = Depends(get_current_user)):
    try:
        # Get the user's organization
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            raise HTTPException(status_code=400, detail="User does not belong to an organization")
            
        org_id = profile_response.data["organization_id"]
        
        # Get documents for the user's organization
        documents_response = supabase.table("documents").select("""
            *,
            assets:asset_id (id, name, portfolio_id),
            asset_documents!inner (document_type, upload_date)
        """).eq("assets.portfolios.organization_id", org_id).execute()
        
        return documents_response.data or []
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/documents")
async def create_document(
    file: UploadFile = File(...),
    asset_id: str = Form(...),
    document_type: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    try:
        # Verify user has access to the asset
        asset_response = supabase.table("assets").select("portfolio_id").eq("id", asset_id).single().execute()
        
        if not asset_response.data:
            raise HTTPException(status_code=404, detail="Asset not found")
            
        portfolio_id = asset_response.data["portfolio_id"]
        
        # Check if user has access to this portfolio
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            raise HTTPException(status_code=403, detail="User does not belong to an organization")
            
        portfolio_response = supabase.table("portfolios").select("id").eq("id", portfolio_id).eq("organization_id", profile_response.data["organization_id"]).execute()
        
        if not portfolio_response.data or len(portfolio_response.data) == 0:
            raise HTTPException(status_code=403, detail="Not authorized to upload documents to this asset")
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        storage_path = f"documents/{unique_filename}"
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Upload to Supabase storage
        storage_response = supabase.storage.from_("documents").upload(
            storage_path,
            file_content
        )
        
        # Create document record
        document_response = supabase.table("documents").insert({
            "filename": file.filename,
            "file_type": file.content_type,
            "file_size": file_size,
            "storage_path": storage_path,
            "asset_id": asset_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        
        if not document_response.data or len(document_response.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create document record")
            
        document_id = document_response.data[0]["id"]
        
        # Create asset_document link
        asset_document_response = supabase.table("asset_documents").insert({
            "asset_id": asset_id,
            "document_id": document_id,
            "document_type": document_type,
            "upload_date": datetime.utcnow().isoformat()
        }).execute()
        
        return document_response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Project endpoints
@app.get("/api/projects")
async def get_projects(current_user: str = Depends(get_current_user)):
    try:
        response = supabase.table("projects").select("*").eq("status", "active").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Credits endpoints
@app.get("/api/credits")
async def get_credits(current_user: str = Depends(get_current_user)):
    try:
        response = supabase.table("credits").select("*").eq("user_id", current_user).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/credits/purchase")
async def purchase_credits(credit: Credit, current_user: str = Depends(get_current_user)):
    try:
        # Calculate total amount
        total_amount = credit.quantity * credit.price_per_credit
        
        response = supabase.table("credits").insert({
            "user_id": current_user,
            "project_id": credit.project_id,
            "quantity": credit.quantity,
            "price_per_credit": credit.price_per_credit,
            "total_amount": total_amount,
            "transaction_type": "purchase"
        }).execute()
        
        # Create notification for purchase
        supabase.table("notifications").insert({
            "user_id": current_user,
            "title": "Credit Purchase Successful",
            "message": f"Successfully purchased {credit.quantity} credits",
            "type": "purchase"
        }).execute()
        
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Notifications endpoints
@app.get("/api/notifications")
async def get_notifications(current_user: str = Depends(get_current_user)):
    try:
        response = supabase.table("notifications").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: str = Depends(get_current_user)):
    try:
        response = supabase.table("notifications").update({
            "read": True
        }).eq("id", notification_id).eq("user_id", current_user).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Asset document endpoints
@app.get("/api/assets/{asset_id}/documents")
async def get_asset_documents(asset_id: str, current_user: str = Depends(get_current_user)):
    try:
        # Verify user has access to the asset
        asset = supabase.table("assets").select("portfolio_id").eq("id", asset_id).single().execute()
        
        if not asset.data:
            raise HTTPException(status_code=404, detail="Asset not found")
            
        portfolio = supabase.table("portfolios").select("organization_id").eq("id", asset.data["portfolio_id"]).single().execute()
        
        if not portfolio.data:
            raise HTTPException(status_code=404, detail="Portfolio not found")
            
        # Get user's organization
        profile = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile.data or profile.data.get("organization_id") != portfolio.data.get("organization_id"):
            raise HTTPException(status_code=403, detail="Not authorized to view documents for this asset")
        
        # Get the documents
        response = supabase.table("asset_documents").select("*, document:document_id(*)").eq("asset_id", asset_id).execute()
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/assets/{asset_id}/documents")
async def link_asset_document(
    asset_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    try:
        # Verify user has access to the asset
        asset_response = supabase.table("assets").select("portfolio_id").eq("id", asset_id).single().execute()
        
        if not asset_response.data:
            raise HTTPException(status_code=404, detail="Asset not found")
            
        portfolio_id = asset_response.data["portfolio_id"]
        
        # Check if user has access to this portfolio
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            raise HTTPException(status_code=403, detail="User does not belong to an organization")
            
        portfolio_response = supabase.table("portfolios").select("id").eq("id", portfolio_id).eq("organization_id", profile_response.data["organization_id"]).execute()
        
        if not portfolio_response.data or len(portfolio_response.data) == 0:
            raise HTTPException(status_code=403, detail="Not authorized to upload documents to this asset")
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        storage_path = f"documents/{unique_filename}"
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Upload to Supabase storage
        storage_response = supabase.storage.from_("documents").upload(
            storage_path,
            file_content
        )
        
        # Create document record
        document_response = supabase.table("documents").insert({
            "filename": file.filename,
            "file_type": file.content_type,
            "file_size": file_size,
            "storage_path": storage_path,
            "asset_id": asset_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        
        if not document_response.data or len(document_response.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create document record")
            
        document_id = document_response.data[0]["id"]
        
        # Create asset_document link
        asset_document_response = supabase.table("asset_documents").insert({
            "asset_id": asset_id,
            "document_id": document_id,
            "document_type": document_type,
            "upload_date": datetime.utcnow().isoformat()
        }).execute()
        
        return {
            "asset_id": asset_id,
            "document_id": document_id,
            "document_type": document_type,
            "filename": file.filename,
            "file_type": file.content_type,
            "file_size": file_size,
            "storage_path": storage_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking asset document: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Portfolio endpoints
@app.get("/api/portfolios")
async def get_portfolios(current_user: str = Depends(get_current_user)):
    try:
        # Get the user's organization from their profile
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            return []
            
        # Get portfolios for the user's organization
        response = supabase.table("portfolios").select("*").eq("organization_id", profile_response.data["organization_id"]).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/portfolios")
async def create_portfolio(portfolio_data: BaseModel, current_user: str = Depends(get_current_user)):
    try:
        # Get the user's organization from their profile
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            # User doesn't have an organization yet, create one
            org_response = supabase.table("organizations").insert({
                "name": f"{current_user}'s Organization",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            
            # Update user's profile with the new organization
            supabase.table("profiles").update({
                "organization_id": org_response.data[0]["id"],
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", current_user).execute()
            
            organization_id = org_response.data[0]["id"]
        else:
            organization_id = profile_response.data["organization_id"]
        
        # Create the portfolio
        portfolio_response = supabase.table("portfolios").insert({
            "organization_id": organization_id,
            "name": portfolio_data.name if hasattr(portfolio_data, "name") else "New Portfolio",
            "description": portfolio_data.description if hasattr(portfolio_data, "description") else None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        
        return portfolio_response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Organization endpoints
@app.get("/api/organizations")
async def get_organizations(current_user: str = Depends(get_current_user)):
    try:
        # Get the user's organization from their profile
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            return []
            
        # Get the organization details
        response = supabase.table("organizations").select("*").eq("id", profile_response.data["organization_id"]).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/organizations")
async def create_organization(organization: Organization, current_user: str = Depends(get_current_user)):
    try:
        # Create the organization
        org_response = supabase.table("organizations").insert({
            "name": organization.name,
            "registration_number": organization.registration_number,
            "address": organization.address,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        
        # Update the user's profile with the new organization
        supabase.table("profiles").update({
            "organization_id": org_response.data[0]["id"],
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", current_user).execute()
        
        return org_response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/assets")
async def create_asset(asset: Asset, current_user: str = Depends(get_current_user)):
    try:
        # Get the user's organization from their profile
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            raise HTTPException(status_code=400, detail="User does not belong to an organization")
            
        # Verify user has access to the portfolio
        portfolio_response = supabase.table("portfolios").select("id").eq("id", asset.portfolio_id).eq("organization_id", profile_response.data["organization_id"]).execute()
        
        if not portfolio_response.data or len(portfolio_response.data) == 0:
            raise HTTPException(status_code=403, detail="Not authorized to create assets in this portfolio")
        
        # Create the asset
        response = supabase.table("assets").insert({
            "portfolio_id": asset.portfolio_id,
            "name": asset.name,
            "asset_type": asset.asset_type,
            "address": asset.address,
            "total_area": asset.total_area,
            "year_built": asset.year_built,
            "energy_rating": asset.energy_rating,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create asset")
            
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating asset: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/assets")
async def get_assets(current_user: str = Depends(get_current_user)):
    try:
        # Get the user's organization
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            raise HTTPException(status_code=400, detail="User does not belong to an organization")
            
        org_id = profile_response.data["organization_id"]
        
        # Get assets for the user's organization
        assets_response = supabase.table("assets").select("""
            *,
            portfolios:portfolio_id (id, name, organization_id)
        """).eq("portfolios.organization_id", org_id).execute()
        
        return assets_response.data or []
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assets: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Initialize bill reader
bill_reader = BillReader()

# Background task for processing energy bills
async def process_energy_bill(document_id: str, storage_path: str, background_tasks: BackgroundTasks):
    try:
        # Get document details
        doc_response = supabase.table("documents").select("*").eq("id", document_id).single().execute()
        
        if not doc_response.data:
            logger.error(f"Document not found: {document_id}")
            return
            
        document = doc_response.data
        
        # Download file from storage
        file_data = supabase.storage.from_("assets").download(storage_path)
        
        # Save to temporary file
        temp_file_path = f"/tmp/{os.path.basename(storage_path)}"
        with open(temp_file_path, 'wb') as f:
            f.write(file_data)
        
        # Process the bill
        bill_data = await bill_reader.process_bill(temp_file_path, document["file_type"])
        
        # Remove temporary file
        os.remove(temp_file_path)
        
        # Store the extracted data
        if bill_data["status"] == "success":
            # Create energy consumption record
            consumption_data = bill_data["data"]
            
            energy_data = {
                "asset_id": document["asset_id"],
                "period_start": consumption_data.get("billing_period", {}).get("start"),
                "period_end": consumption_data.get("billing_period", {}).get("end"),
                "consumption_kwh": consumption_data.get("consumption", {}).get("value"),
                "cost": consumption_data.get("total_amount"),
                "provider": consumption_data.get("provider"),
                "meter_readings": consumption_data.get("meter_readings"),
                "document_id": document_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("energy_consumption").insert(energy_data).execute()
            
            # Generate insights based on the new data
            background_tasks.add_task(generate_energy_insights, document["asset_id"])
            
        # Update document processing status
        supabase.table("documents").update({
            "processing_status": bill_data["status"],
            "processing_result": json.dumps(bill_data),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", document_id).execute()
        
    except Exception as e:
        logger.error(f"Error processing energy bill: {str(e)}")
        # Update document with error status
        supabase.table("documents").update({
            "processing_status": "error",
            "processing_result": json.dumps({"error": str(e)}),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", document_id).execute()

# Function to generate energy insights
async def generate_energy_insights(asset_id: str):
    try:
        # Get all energy consumption data for this asset
        consumption_response = supabase.table("energy_consumption").select("*").eq("asset_id", asset_id).order("period_end", {"ascending": False}).execute()
        
        if not consumption_response.data or len(consumption_response.data) < 2:
            # Not enough data for meaningful insights
            return
            
        consumption_data = consumption_response.data
        
        # Example insight: Consumption trend
        latest = consumption_data[0]
        previous = consumption_data[1]
        
        if latest["consumption_kwh"] > previous["consumption_kwh"] * 1.1:  # 10% increase
            insight = {
                "asset_id": asset_id,
                "insight_type": "consumption_increase",
                "description": f"Energy consumption increased by {((latest['consumption_kwh'] / previous['consumption_kwh']) - 1) * 100:.1f}% compared to the previous period.",
                "recommendation": "Consider reviewing energy usage patterns and identifying potential causes for the increase.",
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("energy_insights").insert(insight).execute()
            
        # Example insight: Cost efficiency
        if latest["consumption_kwh"] > 0 and previous["consumption_kwh"] > 0:
            latest_unit_cost = latest["cost"] / latest["consumption_kwh"]
            previous_unit_cost = previous["cost"] / previous["consumption_kwh"]
            
            if latest_unit_cost > previous_unit_cost * 1.05:  # 5% increase
                insight = {
                    "asset_id": asset_id,
                    "insight_type": "unit_cost_increase",
                    "description": f"Energy unit cost increased by {((latest_unit_cost / previous_unit_cost) - 1) * 100:.1f}% compared to the previous period.",
                    "recommendation": "Consider reviewing your energy tariff or switching providers.",
                    "potential_savings": (latest_unit_cost - previous_unit_cost) * latest["consumption_kwh"],
                    "created_at": datetime.utcnow().isoformat()
                }
                
                supabase.table("energy_insights").insert(insight).execute()
                
    except Exception as e:
        logger.error(f"Error generating energy insights: {str(e)}")

# Endpoint to get energy insights for an asset
@app.get("/api/assets/{asset_id}/energy/insights", response_model=List[EnergyInsight])
async def get_energy_insights(asset_id: str, current_user: str = Depends(get_current_user)):
    try:
        # Verify user has access to the asset
        asset_response = supabase.table("assets").select("portfolio_id").eq("id", asset_id).single().execute()
        
        if not asset_response.data:
            raise HTTPException(status_code=404, detail="Asset not found")
            
        portfolio_id = asset_response.data["portfolio_id"]
        
        # Check if user has access to this portfolio
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            raise HTTPException(status_code=403, detail="User does not belong to an organization")
            
        portfolio_response = supabase.table("portfolios").select("id").eq("id", portfolio_id).eq("organization_id", profile_response.data["organization_id"]).execute()
        
        if not portfolio_response.data or len(portfolio_response.data) == 0:
            raise HTTPException(status_code=403, detail="Not authorized to access this asset")
        
        # Get insights
        insights_response = supabase.table("energy_insights").select("*").eq("asset_id", asset_id).order("created_at", {"ascending": False}).execute()
        
        return insights_response.data or []
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint to get energy consumption data for an asset
@app.get("/api/assets/{asset_id}/energy/consumption")
async def get_energy_consumption(asset_id: str, current_user: str = Depends(get_current_user)):
    try:
        # Verify user has access to the asset
        asset_response = supabase.table("assets").select("portfolio_id").eq("id", asset_id).single().execute()
        
        if not asset_response.data:
            raise HTTPException(status_code=404, detail="Asset not found")
            
        portfolio_id = asset_response.data["portfolio_id"]
        
        # Check if user has access to this portfolio
        profile_response = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if not profile_response.data or not profile_response.data.get("organization_id"):
            raise HTTPException(status_code=403, detail="User does not belong to an organization")
            
        portfolio_response = supabase.table("portfolios").select("id").eq("id", portfolio_id).eq("organization_id", profile_response.data["organization_id"]).execute()
        
        if not portfolio_response.data or len(portfolio_response.data) == 0:
            raise HTTPException(status_code=403, detail="Not authorized to access this asset")
        
        # Get consumption data
        consumption_response = supabase.table("energy_consumption").select("*").eq("asset_id", asset_id).order("period_end", {"ascending": False}).execute()
        
        return consumption_response.data or []
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/debug/frontend", include_in_schema=False)
async def debug_frontend():
    """Endpoint for frontend to check if API is accessible"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "API is accessible from frontend"
    }

@app.get("/api/debug/cors", include_in_schema=False)
async def debug_cors():
    """Endpoint to test CORS configuration"""
    return {
        "status": "ok",
        "cors": "working",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise

@app.get("/api/debug/new-asset-page")
async def debug_new_asset_page():
    """Endpoint to debug the new asset page"""
    return {
        "status": "ok",
        "message": "New asset page API is accessible",
        "asset_types": [asset_type.value for asset_type in AssetType],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/debug/routes")
async def debug_routes():
    """Return all available routes for debugging"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": route.methods if hasattr(route, "methods") else None
        })
    return {"routes": routes}

@app.get("/api/debug/auth")
async def debug_auth(current_user: str = Depends(get_current_user)):
    """Test endpoint to verify authentication is working"""
    return {
        "authenticated": True,
        "user_id": current_user,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/debug/supabase")
async def debug_supabase():
    """Test endpoint to verify Supabase connection"""
    try:
        # Check if supabase is properly initialized
        if not hasattr(supabase, 'table'):
            return {
                "status": "error",
                "message": "Supabase client not properly initialized",
                "supabase_url_set": bool(supabase_url),
                "supabase_key_set": bool(supabase_key)
            }
            
        # Try a simple query
        response = supabase.table("profiles").select("count", count="exact").limit(1).execute()
        
        return {
            "status": "ok",
            "message": "Supabase connection working",
            "response": response,
            "supabase_url": supabase_url[:10] + "..." if supabase_url else None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "supabase_url_set": bool(supabase_url),
            "supabase_key_set": bool(supabase_key)
        }

@app.get("/api/debug/schema")
async def debug_schema():
    """Test endpoint to check database schema"""
    try:
        # Check portfolios table schema
        portfolios_schema = supabase.table("portfolios").select("*").limit(1).execute()
        
        # Check if there are any portfolios
        portfolios_count = supabase.table("portfolios").select("count", count="exact").execute()
        
        # Get column names from the first portfolio (if any)
        column_names = []
        if portfolios_schema.data and len(portfolios_schema.data) > 0:
            column_names = list(portfolios_schema.data[0].keys())
        
        return {
            "status": "ok",
            "portfolios_count": portfolios_count.count if hasattr(portfolios_count, 'count') else 0,
            "column_names": column_names,
            "sample_data": portfolios_schema.data
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/debug/hardcoded-portfolios")
async def hardcoded_portfolios():
    """Debug endpoint that returns hardcoded portfolio data without authentication"""
    from datetime import datetime
    
    # Return hardcoded data
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
    
    return hardcoded_portfolios

@app.get("/api/debug/asset-types")
async def debug_asset_types():
    """Debug endpoint that returns asset types without authentication"""
    try:
        # Return the enum values directly
        types = [asset_type.value for asset_type in AssetType]
        return types
    except Exception as e:
        return {"error": str(e)}

# Create handler for Vercel serverless function
try:
    handler = Mangum(app)
except Exception as e:
    print(f"Error initializing Mangum handler: {str(e)}")
    traceback.print_exc()
    
    # Create a simple handler that returns the error
    def handler(event, context):
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Server initialization failed",
                "details": str(e),
                "traceback": traceback.format_exc()
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }

if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        sys.exit(0)