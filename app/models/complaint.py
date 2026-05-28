"""
models/complaint.py — Complaints Table
----------------------------------------
Yeh project ka CORE table hai. Har pothole complaint yahan store hoti hai.

STATUS WORKFLOW (Requirement #2):
SUBMITTED → ASSIGNED → INSPECTED → RESOLVED
                                 ↘ REJECTED

Status kab change hota hai:
- SUBMITTED: Citizen ne complaint daali
- ASSIGNED:  Admin ne inspector assign kiya
- INSPECTED: Inspector ne site visit kar li aur proof upload ki
- RESOLVED:  Admin ne complaint close ki (road theek ho gayi)
- REJECTED:  Admin ne reject ki (duplicate/invalid complaint)

COLUMNS EXPLAINED:
- citizen_id: Kisne complaint daali (FK → users)
- area: Kanpur ka kaunsa area (e.g., "Rawatpur", "Vijay Nagar")
- latitude/longitude: GPS coordinates for map view
- description: Pothole ka detailed description
- severity: LOW/MEDIUM/HIGH — kitna bada gadd hai
- photo_url: Complaint ki photo URL
- status: Current status (workflow upar dekho)
- resolved_at: Kab resolve hua — average resolution time calculate karne ke liye

Requirement #2 fulfill ho raha hai — complex status workflow
Requirement #3 fulfill ho raha hai — area, severity, resolved_at analytics ke liye
Requirement #4 fulfill ho raha hai — real Kanpur locations
"""
import enum
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Float, Text,
                         DateTime, Enum, ForeignKey)
from sqlalchemy.orm import relationship
from app.database import Base


class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    ASSIGNED = "ASSIGNED"
    INSPECTED = "INSPECTED"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class Severity(str, enum.Enum):
    LOW = "LOW"       # Chhota gadd — slow down karna padta hai
    MEDIUM = "MEDIUM" # Bada gadd — tyre damage possible
    HIGH = "HIGH"     # Bahut bada — accident risk


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    # Kisne report kiya — FK to users table
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Location details — Kanpur ke real areas
    area = Column(String(100), nullable=False, index=True)  # For area-wise analytics
    street_address = Column(String(255), nullable=False)
    landmark = Column(String(200), nullable=True)  # e.g., "ABC School ke paas"

    # GPS coordinates — future map feature ke liye
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Complaint details
    description = Column(Text, nullable=False)
    severity = Column(Enum(Severity), nullable=False, default=Severity.MEDIUM)
    photo_url = Column(String(500), nullable=True)  # Citizen uploaded photo

    # Inspector ke liye fields
    inspector_notes = Column(Text, nullable=True)  # Inspector ki visit notes
    proof_photo_url = Column(String(500), nullable=True)  # Inspector ka proof

    # Status workflow
    status = Column(
        Enum(ComplaintStatus),
        nullable=False,
        default=ComplaintStatus.SUBMITTED,
        index=True  # Status pe queries fast hongi
    )

    # Timestamps — analytics ke liye bahut important
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)  # For avg resolution time

    # Relationships
    citizen = relationship("User", back_populates="complaints",
                           foreign_keys=[citizen_id])
    assignment = relationship("Assignment", back_populates="complaint",
                              uselist=False)  # One-to-One
    audit_logs = relationship("AuditLog", back_populates="complaint")

    def __repr__(self):
        return f"<Complaint #{self.id} | {self.area} | {self.status}>"
