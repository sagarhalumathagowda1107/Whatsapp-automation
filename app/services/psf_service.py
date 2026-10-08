from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.db.models.psf import PSFRecord
from app.schemas.psf import PSFCreate, PSFUpdate

class PSFService:

    @staticmethod
    def create_psf(db: Session, psf_in: PSFCreate) -> PSFRecord:
        db_obj = PSFRecord(
            title=psf_in.title,
            description=psf_in.description,
            category=psf_in.category,
            value=psf_in.value,
            status=psf_in.status
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_psf(db: Session, psf_id: str) -> Optional[PSFRecord]:
        return db.scalar(select(PSFRecord).where(PSFRecord.id == psf_id))

    @staticmethod
    def update_psf(db: Session, psf_id: str, psf_in: PSFUpdate) -> Optional[PSFRecord]:
        db_obj = PSFService.get_psf(db, psf_id)
        if not db_obj:
            return None
            
        update_data = psf_in.model_dump(exclude_unset=True)
        for field, val in update_data.items():
            setattr(db_obj, field, val)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete_psf(db: Session, psf_id: str) -> bool:
        db_obj = PSFService.get_psf(db, psf_id)
        if not db_obj:
            return False
        db.delete(db_obj)
        db.commit()
        return True

    @staticmethod
    def list_psf(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PSFRecord]:
        stmt = select(PSFRecord)
        
        if category:
            stmt = stmt.where(PSFRecord.category == category)
        if status:
            stmt = stmt.where(PSFRecord.status == status)
        if search_query:
            pattern = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    PSFRecord.title.ilike(pattern),
                    PSFRecord.description.ilike(pattern),
                    PSFRecord.category.ilike(pattern)
                )
            )
        if start_date:
            stmt = stmt.where(PSFRecord.created_at >= start_date)
        if end_date:
            stmt = stmt.where(PSFRecord.created_at <= end_date)

        stmt = stmt.order_by(PSFRecord.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())
