"""
models/user.py — Users Table with Username Support
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    CITIZEN   = "citizen"
    INSPECTOR = "inspector"
    ADMIN     = "admin"


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    full_name       = Column(String(100), nullable=False)
    email           = Column(String(150), unique=True, index=True, nullable=False)
    username        = Column(String(50),  unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(Enum(UserRole), nullable=False, default=UserRole.CITIZEN)
    area            = Column(String(100), nullable=True)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    complaints  = relationship("Complaint",  back_populates="citizen",
                               foreign_keys="Complaint.citizen_id")
    assignments = relationship("Assignment", back_populates="inspector",
                               foreign_keys="Assignment.inspector_id")
    audit_logs  = relationship("AuditLog",   back_populates="changed_by_user")

    def __repr__(self):
        return f"<User {self.username or self.email} ({self.role})>"
