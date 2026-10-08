from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import verify_admin_api_key
from app.schemas.recipient import RecipientCreate, RecipientUpdate, RecipientResponse
from app.services.recipient_service import RecipientService

router = APIRouter(prefix="/recipients", tags=["Recipient Management"])

@router.post("", response_model=RecipientResponse, status_code=status.HTTP_201_CREATED, summary="Create Recipient")
def create_recipient(
    recipient_in: RecipientCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """Register a new WhatsApp recipient."""
    try:
        return RecipientService.create_recipient(db, recipient_in)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

@router.get("", response_model=List[RecipientResponse], summary="List Recipients")
def list_recipients(
    active_only: bool = Query(False, description="Return only active recipients"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """List all registered report recipients."""
    return RecipientService.list_recipients(db, active_only=active_only, skip=skip, limit=limit)

@router.get("/{id}", response_model=RecipientResponse, summary="Get Recipient Details")
def get_recipient(
    id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """Retrieve recipient details by ID."""
    recipient = RecipientService.get_recipient(db, id)
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recipient '{id}' not found")
    return recipient

@router.patch("/{id}", response_model=RecipientResponse, summary="Update Recipient")
def update_recipient(
    id: str,
    recipient_in: RecipientUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """Update recipient details or active status."""
    try:
        recipient = RecipientService.update_recipient(db, id, recipient_in)
        if not recipient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recipient '{id}' not found")
        return recipient
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Recipient")
def delete_recipient(
    id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """Delete a recipient by ID."""
    success = RecipientService.delete_recipient(db, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recipient '{id}' not found")
