"""
models/__init__.py
-------------------
Yeh file sabhi models ko ek jagah import karti hai.

WHY NEEDED:
Alembic (migration tool) ko poore app ke models pata hone chahiye
tabhi woh automatically database tables create kar sakta hai.
Agar yahan import na karo, Alembic kuch models miss kar sakta hai.
"""
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintStatus, Severity
from app.models.assignment import Assignment
from app.models.audit_log import AuditLog

__all__ = [
    "User", "UserRole",
    "Complaint", "ComplaintStatus", "Severity",
    "Assignment",
    "AuditLog"
]
