from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import verify_admin_api_key
from app.schemas.psf import PSFCreate, PSFUpdate, PSFResponse
from app.services.psf_service import PSFService

router = APIRouter(prefix="/psf", tags=["PSF Data Management"])

@router.post("", response_model=PSFResponse, status_code=status.HTTP_201_CREATED, summary="Create PSF Record")
def create_psf_record(
    psf_in: PSFCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """Create a new PSF performance status record."""
    return PSFService.create_psf(db, psf_in)

@router.get("", response_model=List[PSFResponse], summary="List & Filter PSF Records")
def list_psf_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, COMPLETED, etc.)"),
    q: Optional[str] = Query(None, description="Search query string for title/description"),
    start_date: Optional[datetime] = Query(None, description="Filter records created on or after start_date"),
    end_date: Optional[datetime] = Query(None, description="Filter records created on or before end_date"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """List, search, and filter PSF records by category, status, search query, or date range."""
    return PSFService.list_psf(
        db,
        skip=skip,
        limit=limit,
        category=category,
        status=status,
        search_query=q,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/{id}", response_model=PSFResponse, summary="Get PSF Record Details")
def get_psf_record(
    id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """Get PSF record details by ID."""
    record = PSFService.get_psf(db, id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"PSF record '{id}' not found")
    return record

@router.patch("/{id}", response_model=PSFResponse, summary="Update PSF Record")
def update_psf_record(
    id: str,
    psf_in: PSFUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """Update an existing PSF record."""
    record = PSFService.update_psf(db, id, psf_in)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"PSF record '{id}' not found")
    return record

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete PSF Record")
def delete_psf_record(
    id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """Delete a PSF record by ID."""
    success = PSFService.delete_psf(db, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"PSF record '{id}' not found")
