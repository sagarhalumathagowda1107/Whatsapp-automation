from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models.recipient import Recipient
from app.schemas.recipient import RecipientCreate, RecipientUpdate

class RecipientService:

    @staticmethod
    def create_recipient(db: Session, recipient_in: RecipientCreate) -> Recipient:
        existing = db.scalar(select(Recipient).where(Recipient.phone_number == recipient_in.phone_number))
        if existing:
            raise ValueError(f"Recipient with phone number {recipient_in.phone_number} already exists")

        db_obj = Recipient(
            name=recipient_in.name,
            phone_number=recipient_in.phone_number,
            active=recipient_in.active
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_recipient(db: Session, recipient_id: str) -> Optional[Recipient]:
        return db.scalar(select(Recipient).where(Recipient.id == recipient_id))

    @staticmethod
    def get_recipient_by_phone(db: Session, phone_number: str) -> Optional[Recipient]:
        return db.scalar(select(Recipient).where(Recipient.phone_number == phone_number))

    @staticmethod
    def update_recipient(db: Session, recipient_id: str, recipient_in: RecipientUpdate) -> Optional[Recipient]:
        db_obj = RecipientService.get_recipient(db, recipient_id)
        if not db_obj:
            return None

        update_data = recipient_in.model_dump(exclude_unset=True)
        if "phone_number" in update_data and update_data["phone_number"] != db_obj.phone_number:
            existing = RecipientService.get_recipient_by_phone(db, update_data["phone_number"])
            if existing:
                raise ValueError(f"Phone number {update_data['phone_number']} is already assigned to another recipient")

        for field, val in update_data.items():
            setattr(db_obj, field, val)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete_recipient(db: Session, recipient_id: str) -> bool:
        db_obj = RecipientService.get_recipient(db, recipient_id)
        if not db_obj:
            return False
        db.delete(db_obj)
        db.commit()
        return True

    @staticmethod
    def list_recipients(db: Session, active_only: bool = False, skip: int = 0, limit: int = 100) -> List[Recipient]:
        stmt = select(Recipient)
        if active_only:
            stmt = stmt.where(Recipient.active == True)
        stmt = stmt.order_by(Recipient.name.asc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())
