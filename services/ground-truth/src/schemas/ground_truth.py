"""Pydantic schemas for API requests/responses"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class GroundTruthValueType(str, Enum):
    """Ground truth value types"""
    PRICE_RANGE = "PRICE_RANGE"
    CATEGORICAL = "CATEGORICAL"
    NUMERICAL = "NUMERICAL"
    TEXT = "TEXT"
    JSON = "JSON"
    LIST = "LIST"


# ============================================================================
# Domain Schemas
# ============================================================================

class DomainCreate(BaseModel):
    """Schema for creating a domain"""
    name: str = Field(..., max_length=100, description="Domain name (e.g., 'taj_hotels_pricing')")
    description: Optional[str] = Field(None, description="Domain description")
    value_type: GroundTruthValueType = Field(..., description="Type of values in this domain")
    schema: Dict[str, Any] = Field(..., description="JSON Schema for validation")
    created_by: Optional[str] = Field(None, description="Creator email/username")
    extra_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DomainResponse(BaseModel):
    """Schema for domain response"""
    id: str
    name: str
    description: Optional[str]
    value_type: str
    schema: Dict[str, Any]
    created_at: datetime
    created_by: Optional[str]
    extra_metadata: Dict[str, Any]

    class Config:
        from_attributes = True


# ============================================================================
# Ground Truth Entry Schemas
# ============================================================================

class GroundTruthEntryCreate(BaseModel):
    """Schema for creating a ground truth entry"""
    key: str = Field(..., max_length=255, description="Entry key (e.g., 'taj_mahal_palace')")
    value: Dict[str, Any] = Field(..., description="Entry value (validated against domain schema)")
    version: str = Field(..., max_length=50, description="Version identifier")
    valid_from: Optional[datetime] = Field(None, description="Valid from timestamp")
    aliases: Optional[List[str]] = Field(default_factory=list, description="Aliases for this entry")
    created_by: Optional[str] = Field(None, description="Creator email/username")
    extra_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GroundTruthEntryUpdate(BaseModel):
    """Schema for updating a ground truth entry"""
    value: Dict[str, Any] = Field(..., description="New value")
    version: str = Field(..., max_length=50, description="New version identifier")
    created_by: Optional[str] = Field(None, description="Updater email/username")


class GroundTruthEntryResponse(BaseModel):
    """Schema for ground truth entry response"""
    id: str
    domain: str
    key: str
    value: Dict[str, Any]
    value_type: str
    version: str
    valid_from: datetime
    valid_to: Optional[datetime]
    created_at: datetime
    created_by: Optional[str]
    extra_metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class GroundTruthEntryListResponse(BaseModel):
    """Schema for list of ground truth entries"""
    total: int
    entries: List[GroundTruthEntryResponse]


# ============================================================================
# Alias Schemas
# ============================================================================

class AliasCreate(BaseModel):
    """Schema for creating an alias"""
    alias: str = Field(..., max_length=255, description="Alias text")


class AliasResponse(BaseModel):
    """Schema for alias response"""
    id: str
    entry_id: str
    domain: str
    alias: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Audit Log Schemas
# ============================================================================

class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    id: str
    entry_id: Optional[str]
    action: str
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    changed_by: Optional[str]
    changed_at: datetime
    extra_metadata: Dict[str, Any]

    class Config:
        from_attributes = True


# ============================================================================
# History Schemas
# ============================================================================

class HistoryEntryResponse(BaseModel):
    """Schema for history entry"""
    version: str
    value: Dict[str, Any]
    valid_from: datetime
    valid_to: Optional[datetime]
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    """Schema for history response"""
    domain: str
    key: str
    versions: List[HistoryEntryResponse]

