"""
schemas/complaint.py — Complaint & Assignment Schemas
-------------------------------------------------------
Yeh file complaints, assignments, aur analytics ke
saare input/output schemas define karti hai.

Requirement #5 fulfill ho raha hai — Pydantic schemas for all request/response
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.complaint import ComplaintStatus, Severity


# ============================================================
# COMPLAINT SCHEMAS
# ============================================================

class ComplaintCreate(BaseModel):
    """Citizen complaint file karne ke liye"""
    area: str
    street_address: str
    landmark: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: str
    severity: Severity = Severity.MEDIUM
    photo_url: Optional[str] = None

    @field_validator("description")
    @classmethod
    def description_min_length(cls, v):
        if len(v) < 20:
            raise ValueError("Description kam se kam 20 characters ka hona chahiye")
        return v


class ComplaintUpdate(BaseModel):
    """Inspector site visit ke baad update karta hai"""
    inspector_notes: Optional[str] = None
    proof_photo_url: Optional[str] = None


class ComplaintStatusUpdate(BaseModel):
    """Admin status change karta hai"""
    status: ComplaintStatus
    notes: Optional[str] = None  # Rejection reason etc.


class AssignmentInfo(BaseModel):
    """Complaint response mein assignment details"""
    id: int
    inspector_id: int
    inspector_name: Optional[str] = None
    assigned_at: datetime
    visit_scheduled_at: Optional[datetime] = None
    visit_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComplaintResponse(BaseModel):
    """Complaint API response"""
    id: int
    citizen_id: int
    citizen_name: Optional[str] = None
    area: str
    street_address: str
    landmark: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    description: str
    severity: Severity
    photo_url: Optional[str]
    inspector_notes: Optional[str]
    proof_photo_url: Optional[str]
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    assignment: Optional[AssignmentInfo] = None

    class Config:
        from_attributes = True


# ============================================================
# ASSIGNMENT SCHEMAS
# ============================================================

class AssignmentCreate(BaseModel):
    """Admin inspector assign karne ke liye"""
    complaint_id: int
    inspector_id: int
    visit_scheduled_at: Optional[datetime] = None
    admin_notes: Optional[str] = None


class AssignmentResponse(BaseModel):
    id: int
    complaint_id: int
    inspector_id: int
    assigned_by: int
    assigned_at: datetime
    visit_scheduled_at: Optional[datetime]
    visit_completed_at: Optional[datetime]
    admin_notes: Optional[str]

    class Config:
        from_attributes = True


# ============================================================
# ANALYTICS SCHEMAS (Requirement #3)
# ============================================================

class AreaWiseCount(BaseModel):
    """Requirement #3: Area-wise pending complaints"""
    area: str
    pending_count: int
    total_count: int


class InspectorWiseResolved(BaseModel):
    """Requirement #3: Inspector-wise resolved complaints"""
    inspector_id: int
    inspector_name: str
    resolved_count: int
    inspected_count: int


class MonthlyTrend(BaseModel):
    """Requirement #3: Monthly complaint trend"""
    month: str         # e.g., "2024-01"
    month_name: str    # e.g., "January 2024"
    complaint_count: int
    resolved_count: int


class AnalyticsDashboard(BaseModel):
    """Admin dashboard ka full analytics response"""
    total_complaints: int
    pending_complaints: int
    resolved_complaints: int
    rejected_complaints: int
    avg_resolution_days: float
    area_wise: List[AreaWiseCount]
    inspector_wise: List[InspectorWiseResolved]
    monthly_trend: List[MonthlyTrend]


# ============================================================
# AUDIT LOG SCHEMA
# ============================================================

class AuditLogResponse(BaseModel):
    id: int
    complaint_id: int
    changed_by: int
    changer_name: Optional[str] = None
    old_status: Optional[ComplaintStatus]
    new_status: Optional[ComplaintStatus]
    action: str
    notes: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True
