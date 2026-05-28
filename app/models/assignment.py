"""
models/assignment.py — Assignments Table
------------------------------------------
Yeh table Admin aur Inspector ke beech ka bridge hai.

PURPOSE:
- Admin kisi complaint ko kisi inspector ko assign karta hai
- Ek complaint ko ek time pe ek hi inspector handle karta hai
- Auto-assign logic: nearest inspector dhundhna

WHY SEPARATE TABLE (not just a column in complaints)?
- Future mein re-assignment track kar sakte hain
- Inspector ki workload dekh sakte hain
- Assignment ka history rakh sakte hain

COLUMNS EXPLAINED:
- complaint_id: Kaunsi complaint (FK → complaints)
- inspector_id: Kisko assign ki (FK → users where role=inspector)
- assigned_by: Kisme ne assign kiya (FK → users where role=admin)
- assigned_at: Kab assign kiya
- visit_scheduled_at: Inspector kab visit karega
- visit_completed_at: Kab visit complete hui

Requirement #1 fulfill ho raha hai — Admin assign karta hai, Inspector handle karta hai
Requirement #2 fulfill ho raha hai — 4th important table, complex relationship
"""
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)

    # Which complaint is assigned
    complaint_id = Column(Integer, ForeignKey("complaints.id"),
                          nullable=False, unique=True)  # unique=True: ek complaint ek assignment

    # Which inspector got assigned
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Which admin assigned it
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timeline
    assigned_at = Column(DateTime, default=datetime.utcnow)
    visit_scheduled_at = Column(DateTime, nullable=True)   # Admin sets this
    visit_completed_at = Column(DateTime, nullable=True)   # Inspector updates this

    # Admin's note to inspector — "Rush karo, main road hai"
    admin_notes = Column(Text, nullable=True)

    # Relationships
    complaint = relationship("Complaint", back_populates="assignment")
    inspector = relationship("User", back_populates="assignments",
                             foreign_keys=[inspector_id])
    admin = relationship("User", foreign_keys=[assigned_by])

    def __repr__(self):
        return f"<Assignment complaint#{self.complaint_id} → inspector#{self.inspector_id}>"
