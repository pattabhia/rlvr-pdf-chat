"""Domain management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import jsonschema

from ..database.connection import get_db
from ..models.ground_truth import Domain
from ..schemas.ground_truth import DomainCreate, DomainResponse

router = APIRouter()


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(
    domain: DomainCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new domain
    
    A domain represents a category of ground truth data (e.g., 'taj_hotels_pricing').
    Each domain has a schema that validates entries.
    """
    # Check if domain already exists
    existing = db.query(Domain).filter(Domain.name == domain.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Domain '{domain.name}' already exists"
        )
    
    # Validate JSON schema
    try:
        jsonschema.Draft7Validator.check_schema(domain.schema)
    except jsonschema.SchemaError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON schema: {str(e)}"
        )
    
    # Create domain
    db_domain = Domain(
        name=domain.name,
        description=domain.description,
        value_type=domain.value_type.value,
        schema=domain.schema,
        created_by=domain.created_by,
        extra_metadata=domain.extra_metadata
    )
    
    db.add(db_domain)
    db.commit()
    db.refresh(db_domain)
    
    return DomainResponse(
        id=str(db_domain.id),
        name=db_domain.name,
        description=db_domain.description,
        value_type=db_domain.value_type,
        schema=db_domain.schema,
        created_at=db_domain.created_at,
        created_by=db_domain.created_by,
        extra_metadata=db_domain.extra_metadata or {}
    )


@router.get("", response_model=List[DomainResponse])
async def list_domains(db: Session = Depends(get_db)):
    """
    List all domains
    
    Returns all registered ground truth domains.
    """
    domains = db.query(Domain).all()
    
    return [
        DomainResponse(
            id=str(d.id),
            name=d.name,
            description=d.description,
            value_type=d.value_type,
            schema=d.schema,
            created_at=d.created_at,
            created_by=d.created_by,
            extra_metadata=d.extra_metadata or {}
        )
        for d in domains
    ]


@router.get("/{domain_name}", response_model=DomainResponse)
async def get_domain(
    domain_name: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific domain
    
    Returns domain details including schema.
    """
    domain = db.query(Domain).filter(Domain.name == domain_name).first()
    
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain_name}' not found"
        )
    
    return DomainResponse(
        id=str(domain.id),
        name=domain.name,
        description=domain.description,
        value_type=domain.value_type,
        schema=domain.schema,
        created_at=domain.created_at,
        created_by=domain.created_by,
        extra_metadata=domain.extra_metadata or {}
    )


@router.delete("/{domain_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_name: str,
    db: Session = Depends(get_db)
):
    """
    Delete a domain
    
    WARNING: This will also delete all ground truth entries in this domain!
    """
    domain = db.query(Domain).filter(Domain.name == domain_name).first()
    
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain_name}' not found"
        )
    
    db.delete(domain)
    db.commit()
    
    return None

