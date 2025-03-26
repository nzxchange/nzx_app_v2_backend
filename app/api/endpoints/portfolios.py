from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.core.auth import get_current_user
from app.core.db import supabase
from app.models.portfolio import Portfolio, PortfolioCreate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[Portfolio])
async def get_portfolios(current_user: str = Depends(get_current_user)):
    """Get all portfolios for the current user's organization"""
    try:
        # Get user's organization_id
        user = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        if not user.data or not user.data.get("organization_id"):
            return []

        # Get portfolios for the organization
        response = supabase.table("portfolios").select("*").eq("organization_id", user.data["organization_id"]).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting portfolios: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/", response_model=Portfolio)
async def create_portfolio(
    portfolio: PortfolioCreate,
    current_user: str = Depends(get_current_user)
):
    """Create a new portfolio"""
    try:
        # Get user's organization_id
        user = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        if not user.data or not user.data.get("organization_id"):
            raise HTTPException(status_code=400, detail="User must belong to an organization")

        # Create portfolio with organization_id
        portfolio_data = portfolio.dict()
        portfolio_data["organization_id"] = user.data["organization_id"]
        
        response = supabase.table("portfolios").insert(portfolio_data).execute()
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portfolio: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(portfolio_id: str, current_user: str = Depends(get_current_user)):
    """Get a specific portfolio"""
    try:
        response = supabase.table("portfolios").select("*").eq("id", portfolio_id).single().execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=404, detail="Portfolio not found") 