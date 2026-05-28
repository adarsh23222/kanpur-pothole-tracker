"""
models/audit_log.py — Audit Logs Table
-----------------------------------------
Yeh table system ka "Black Box" hai — har cheez record hoti hai.

PURPOSE (Requirement #2):
"Every status change logged in audit_logs"
- Jab bhi complaint ka status change ho → log entry
- Jab bhi assignment ho → log entry  
- Jab bhi reject ho → log entry with reason

WHY IS THIS IMPORTANT?
Real government systems mein accountability bahut important hai.
Agar koi complaint galat reject hui, audit trail se pata chalega
ki kisne, kab, aur kyun kiya.

EXAMPLE LOG ENTRIES:
1. Citizen → SUBMITTED complaint #5
2. Admin → ASSIGNED complaint #5 to inspector Rajesh
3. Inspector → INSPECTED complaint #5, uploaded proof
4. Admin → RESOLVED complaint #5

COLUMNS EXPLAINED:
- complaint_id: Kaunsi complaint ke baare mein
- changed_by: Kisne change kiya (FK → users)
- old_status / new_status: Status change record
- action: Free text — "COMPLAINT_SUBMITTED", "INSPECTOR_ASSIGNED", etc.
- notes: Additional context

Requirement #2 fulfill ho raha hai — every status change logged
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.complaint import ComplaintStatus


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Which complaint this log is about
    complaint_id = Column(Integer, ForeignKey("complaints.id"),
                          nullable=False, index=True)

    # Who made the change
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # What was the status before
    old_status = Column(Enum(ComplaintStatus), nullable=True)

    # What is the status after
    new_status = Column(Enum(ComplaintStatus), nullable=True)

    # Short action code — easy to filter/search
    # e.g., "COMPLAINT_SUBMITTED", "INSPECTOR_ASSIGNED", "PROOF_UPLOADED"
    action = Column(String(100), nullable=False)

    # Any additional notes/reason
    notes = Column(Text, nullable=True)

    # When did this happen
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    complaint = relationship("Complaint", back_populates="audit_logs")
    changed_by_user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog #{self.id} | {self.action} | complaint#{self.complaint_id}>"
