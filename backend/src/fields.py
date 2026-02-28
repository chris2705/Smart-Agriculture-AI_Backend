from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from . import models, database, auth

router = APIRouter(prefix="/fields", tags=["fields"])

# --- Schemas ---
class FieldBase(BaseModel):
    name: str
    location: str
    size: float
    crop_type: Optional[str] = None
    soil_type: Optional[str] = None

class FieldCreate(FieldBase):
    pass

class FieldResponse(FieldBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

# --- Routes ---

@router.post("/", response_model=FieldResponse)
def create_field(field: FieldCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_field = models.Field(**field.dict(), owner_id=current_user.id)
    db.add(db_field)
    db.commit()
    db.refresh(db_field)
    return db_field

@router.get("/", response_model=List[FieldResponse])
def read_fields(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Field).filter(models.Field.owner_id == current_user.id).all()

@router.delete("/{field_id}")
def delete_field(field_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    field = db.query(models.Field).filter(models.Field.id == field_id, models.Field.owner_id == current_user.id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    
    db.delete(field)
    db.commit()
    return {"status": "success", "message": "Field deleted"}
