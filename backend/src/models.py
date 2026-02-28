from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)

    fields = relationship("Field", back_populates="owner")


class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), index=True)
    location = Column(String(255))
    size = Column(Float)

    crop_type = Column(String(100), nullable=True)  # crop name
    soil_type = Column(String(100), nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="fields")