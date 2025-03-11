from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class UserRole(str, Enum):
    owner = "owner"
    tenant = "tenant"
    operator = "operator"
    consultant = "consultant"

class AssetType(str, Enum):
    office = "office"
    retail = "retail"
    industrial = "industrial"
    residential = "residential"
    mixed_use = "mixed_use"
    commercial = "commercial"

class Organization(BaseModel):
    id: Optional[str] = None
    name: str
    registration_number: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Portfolio(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    organization_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Asset(BaseModel):
    id: Optional[str] = None
    portfolio_id: str
    name: str
    asset_type: AssetType
    address: str
    total_area: float
    year_built: Optional[int] = None
    energy_rating: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    organization_id: Optional[str] = None

class AssetTenant(BaseModel):
    id: Optional[str] = None
    asset_id: str
    tenant_id: str
    floor_number: Optional[int] = None
    area_occupied: float
    lease_start_date: date
    lease_end_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AssetDocument(BaseModel):
    id: Optional[str] = None
    asset_id: str
    document_type: str
    document_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None