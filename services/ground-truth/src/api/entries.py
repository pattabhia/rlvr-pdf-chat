"""Ground truth entry management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from datetime import datetime
import jsonschema

from ..database.connection import get_db
from ..models.ground_truth import Domain, GroundTruthEntry, GroundTruthAlias, GroundTruthAuditLog
from ..schemas.ground_truth import (
    GroundTruthEntryCreate,
    GroundTruthEntryUpdate,
    GroundTruthEntryResponse,
    GroundTruthEntryListResponse,
    HistoryResponse,
    HistoryEntryResponse
)

router = APIRouter()


def normalize_key(db: Session, domain: str, key: str) -> str:
    """
    Normalize key by checking aliases
    
    If key is an alias, return the canonical key.
    Otherwise, return the key as-is.
    """
    alias = db.query(GroundTruthAlias).filter(
        and_(
            GroundTruthAlias.domain == domain,
            GroundTruthAlias.alias == key.lower()
        )
    ).first()
    
    if alias:
        # Get canonical key from entry
        entry = db.query(GroundTruthEntry).filter(
            GroundTruthEntry.id == alias.entry_id
        ).first()
        if entry:
            return entry.key
    
    return key.lower()


def validate_value_against_schema(value: dict, schema: dict) -> None:
    """
    Validate value against JSON schema
    
    Raises:
        HTTPException: If validation fails
    """
    try:
        jsonschema.validate(instance=value, schema=schema)
    except jsonschema.ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Value validation failed: {e.message}"
        )


@router.post("/{domain}", response_model=GroundTruthEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    domain: str,
    entry: GroundTruthEntryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new ground truth entry
    
    The value will be validated against the domain's schema.
    """
    # Get domain
    domain_obj = db.query(Domain).filter(Domain.name == domain).first()
    if not domain_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain}' not found"
        )
    
    # Validate value against schema
    validate_value_against_schema(entry.value, domain_obj.schema)
    
    # Check if entry already exists with this version
    existing = db.query(GroundTruthEntry).filter(
        and_(
            GroundTruthEntry.domain == domain,
            GroundTruthEntry.key == entry.key.lower(),
            GroundTruthEntry.version == entry.version
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Entry '{entry.key}' with version '{entry.version}' already exists"
        )
    
    # Create entry
    db_entry = GroundTruthEntry(
        domain=domain,
        key=entry.key.lower(),
        value=entry.value,
        value_type=domain_obj.value_type,
        version=entry.version,
        valid_from=entry.valid_from or datetime.utcnow(),
        created_by=entry.created_by,
        extra_metadata=entry.extra_metadata
    )
    
    db.add(db_entry)
    db.flush()  # Get ID without committing
    
    # Add aliases
    for alias in entry.aliases or []:
        db_alias = GroundTruthAlias(
            entry_id=db_entry.id,
            domain=domain,
            alias=alias.lower()
        )
        db.add(db_alias)
    
    # Add audit log
    audit = GroundTruthAuditLog(
        entry_id=db_entry.id,
        action="created",
        new_value=entry.value,
        changed_by=entry.created_by
    )
    db.add(audit)
    
    db.commit()
    db.refresh(db_entry)
    
    return GroundTruthEntryResponse(
        id=str(db_entry.id),
        domain=db_entry.domain,
        key=db_entry.key,
        value=db_entry.value,
        value_type=db_entry.value_type,
        version=db_entry.version,
        valid_from=db_entry.valid_from,
        valid_to=db_entry.valid_to,
        created_at=db_entry.created_at,
        created_by=db_entry.created_by,
        extra_metadata=db_entry.extra_metadata or {}
    )


@router.get("/{domain}/{key}", response_model=GroundTruthEntryResponse)
async def get_entry(
    domain: str,
    key: str,
    version: Optional[str] = None,
    as_of_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get a ground truth entry
    
    - If version specified: return that version
    - If as_of_date specified: return version valid at that date
    - Otherwise: return current version (valid_to IS NULL)
    """
    # Normalize key (handle aliases)
    normalized_key = normalize_key(db, domain, key)
    
    # Build query
    query = db.query(GroundTruthEntry).filter(
        and_(
            GroundTruthEntry.domain == domain,
            GroundTruthEntry.key == normalized_key
        )
    )
    
    if version:
        query = query.filter(GroundTruthEntry.version == version)
    elif as_of_date:
        query = query.filter(
            and_(
                GroundTruthEntry.valid_from <= as_of_date,
                or_(
                    GroundTruthEntry.valid_to.is_(None),
                    GroundTruthEntry.valid_to > as_of_date
                )
            )
        )
    else:
        # Get current version
        query = query.filter(GroundTruthEntry.valid_to.is_(None))
    
    entry = query.first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry '{key}' not found in domain '{domain}'"
        )
    
    return GroundTruthEntryResponse(
        id=str(entry.id),
        domain=entry.domain,
        key=entry.key,
        value=entry.value,
        value_type=entry.value_type,
        version=entry.version,
        valid_from=entry.valid_from,
        valid_to=entry.valid_to,
        created_at=entry.created_at,
        created_by=entry.created_by,
        extra_metadata=entry.extra_metadata or {}
    )


@router.get("/{domain}", response_model=GroundTruthEntryListResponse)
async def list_entries(
    domain: str,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    current_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    List all entries in a domain

    - current_only: If True, only return current versions (valid_to IS NULL)
    """
    query = db.query(GroundTruthEntry).filter(GroundTruthEntry.domain == domain)

    if current_only:
        query = query.filter(GroundTruthEntry.valid_to.is_(None))

    total = query.count()
    entries = query.offset(offset).limit(limit).all()

    return GroundTruthEntryListResponse(
        total=total,
        entries=[
            GroundTruthEntryResponse(
                id=str(e.id),
                domain=e.domain,
                key=e.key,
                value=e.value,
                value_type=e.value_type,
                version=e.version,
                valid_from=e.valid_from,
                valid_to=e.valid_to,
                created_at=e.created_at,
                created_by=e.created_by,
                extra_metadata=e.extra_metadata or {}
            )
            for e in entries
        ]
    )


@router.put("/{domain}/{key}", response_model=GroundTruthEntryResponse)
async def update_entry(
    domain: str,
    key: str,
    update: GroundTruthEntryUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a ground truth entry

    This creates a new version and marks the old version as expired.
    """
    # Get domain
    domain_obj = db.query(Domain).filter(Domain.name == domain).first()
    if not domain_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain}' not found"
        )

    # Validate value against schema
    validate_value_against_schema(update.value, domain_obj.schema)

    # Normalize key
    normalized_key = normalize_key(db, domain, key)

    # Get current version
    current = db.query(GroundTruthEntry).filter(
        and_(
            GroundTruthEntry.domain == domain,
            GroundTruthEntry.key == normalized_key,
            GroundTruthEntry.valid_to.is_(None)
        )
    ).first()

    if not current:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry '{key}' not found in domain '{domain}'"
        )

    # Mark current as expired
    current.valid_to = datetime.utcnow()

    # Create new version
    new_entry = GroundTruthEntry(
        domain=domain,
        key=normalized_key,
        value=update.value,
        value_type=domain_obj.value_type,
        version=update.version,
        valid_from=datetime.utcnow(),
        created_by=update.created_by,
        metadata={}
    )

    db.add(new_entry)
    db.flush()

    # Add audit log
    audit = GroundTruthAuditLog(
        entry_id=new_entry.id,
        action="updated",
        old_value=current.value,
        new_value=update.value,
        changed_by=update.created_by
    )
    db.add(audit)

    db.commit()
    db.refresh(new_entry)

    return GroundTruthEntryResponse(
        id=str(new_entry.id),
        domain=new_entry.domain,
        key=new_entry.key,
        value=new_entry.value,
        value_type=new_entry.value_type,
        version=new_entry.version,
        valid_from=new_entry.valid_from,
        valid_to=new_entry.valid_to,
        created_at=new_entry.created_at,
        created_by=new_entry.created_by,
        extra_metadata=new_entry.extra_metadata or {}
    )


@router.get("/{domain}/{key}/history", response_model=HistoryResponse)
async def get_entry_history(
    domain: str,
    key: str,
    db: Session = Depends(get_db)
):
    """
    Get all versions of a ground truth entry

    Returns history ordered by valid_from (newest first).
    """
    # Normalize key
    normalized_key = normalize_key(db, domain, key)

    entries = db.query(GroundTruthEntry).filter(
        and_(
            GroundTruthEntry.domain == domain,
            GroundTruthEntry.key == normalized_key
        )
    ).order_by(GroundTruthEntry.valid_from.desc()).all()

    if not entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry '{key}' not found in domain '{domain}'"
        )

    return HistoryResponse(
        domain=domain,
        key=normalized_key,
        versions=[
            HistoryEntryResponse(
                version=e.version,
                value=e.value,
                valid_from=e.valid_from,
                valid_to=e.valid_to,
                created_by=e.created_by
            )
            for e in entries
        ]
    )

