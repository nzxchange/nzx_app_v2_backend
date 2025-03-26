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
    commercial = "commercial"
    residential = "residential"
    industrial = "industrial"
    retail = "retail"
    office = "office"
    mixed_use = "mixed_use"

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

class AssetBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    asset_type: AssetType
    portfolio_id: str
    floor_area: Optional[float] = None
    occupancy_rate: Optional[float] = None

class AssetCreate(AssetBase):
    pass

class Asset(AssetBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

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