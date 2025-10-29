"""Ground Truth domain entities"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class GroundTruthValueType(Enum):
    """Types of ground truth values"""
    PRICE_RANGE = "PRICE_RANGE"
    CATEGORICAL = "CATEGORICAL"
    NUMERICAL = "NUMERICAL"
    TEXT = "TEXT"
    JSON = "JSON"
    LIST = "LIST"


@dataclass
class GroundTruthDomain:
    """
    Ground Truth Domain
    
    Represents a domain of ground truth data (e.g., taj_hotels_pricing).
    """
    name: str
    description: str
    value_type: GroundTruthValueType
    schema: Dict[str, Any]
    created_at: datetime
    created_by: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class GroundTruthEntry:
    """
    Ground Truth Entry
    
    Represents a single ground truth entry (e.g., Taj Mahal Palace pricing).
    """
    id: str
    domain: str
    key: str
    value: Dict[str, Any]
    value_type: GroundTruthValueType
    version: str
    valid_from: datetime
    valid_to: Optional[datetime]
    created_at: datetime
    created_by: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_current(self) -> bool:
        """Check if this is the current version"""
        return self.valid_to is None
    
    def is_valid_at(self, timestamp: datetime) -> bool:
        """Check if this entry is valid at a given timestamp"""
        if timestamp < self.valid_from:
            return False
        if self.valid_to and timestamp >= self.valid_to:
            return False
        return True
    
    def get_price_range(self) -> Optional[tuple]:
        """Get price range if this is a PRICE_RANGE entry"""
        if self.value_type != GroundTruthValueType.PRICE_RANGE:
            return None
        
        min_price = self.value.get("min_price")
        max_price = self.value.get("max_price")
        
        if min_price is not None and max_price is not None:
            return (min_price, max_price)
        
        return None

