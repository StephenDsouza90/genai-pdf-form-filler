from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from database import Base


class FormSession(Base):
    __tablename__ = "form_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    output_path = Column(String, nullable=True)
    total_fields = Column(Integer, default=0)
    filled_fields = Column(Integer, default=0)
    status = Column(String, default="active")  # active, completed, expired
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FormField(Base):
    __tablename__ = "form_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    field_name = Column(String, nullable=False)
    field_type = Column(String, nullable=False)
    value = Column(Text, nullable=True)
    is_filled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())