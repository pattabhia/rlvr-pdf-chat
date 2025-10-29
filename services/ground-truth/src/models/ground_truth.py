"""SQLAlchemy models for ground truth"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..database.connection import Base


class Domain(Base):
    """Domain model"""
    __tablename__ = "domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String)
    value_type = Column(String(50), nullable=False)
    schema = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))
    extra_metadata = Column(JSON, default={})


class GroundTruthEntry(Base):
    """Ground truth entry model"""
    __tablename__ = "ground_truth_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String(100), ForeignKey("domains.name", ondelete="CASCADE"), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(JSON, nullable=False)
    value_type = Column(String(50), nullable=False)
    version = Column(String(50), nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))
    extra_metadata = Column(JSON, default={})
    
    __table_args__ = (
        Index('idx_gt_domain', 'domain'),
        Index('idx_gt_key', 'key'),
        Index('idx_gt_domain_key', 'domain', 'key'),
        Index('idx_gt_valid_from', 'valid_from'),
        Index('idx_gt_valid_to', 'valid_to'),
        Index('idx_gt_current', 'domain', 'key', postgresql_where=(valid_to == None)),
    )


class GroundTruthAlias(Base):
    """Ground truth alias model"""
    __tablename__ = "ground_truth_aliases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("ground_truth_entries.id", ondelete="CASCADE"), nullable=False)
    domain = Column(String(100), nullable=False)
    alias = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_aliases_domain', 'domain'),
        Index('idx_aliases_alias', 'alias'),
    )


class GroundTruthAuditLog(Base):
    """Ground truth audit log model"""
    __tablename__ = "ground_truth_audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("ground_truth_entries.id", ondelete="SET NULL"))
    action = Column(String(50), nullable=False)
    old_value = Column(JSON)
    new_value = Column(JSON)
    changed_by = Column(String(100))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    extra_metadata = Column(JSON, default={})
    
    __table_args__ = (
        Index('idx_audit_entry_id', 'entry_id'),
        Index('idx_audit_changed_at', 'changed_at'),
    )

