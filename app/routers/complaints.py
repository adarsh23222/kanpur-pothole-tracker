"""
routers/complaints.py — Complaint Management
----------------------------------------------
Yeh project ka sabse important router hai.

ENDPOINTS:
POST   /complaints/           — Citizen: nayi complaint daalo
GET    /complaints/           — All complaints (role-based filter)
GET    /complaints/{id}       — Single complaint detail
PUT    /complaints/{id}/status     — Admin: status change
PUT    /complaints/{id}/inspect    — Inspector: visit update + proof upload
GET    /complaints/{id}/audit-log  — Complaint ka audit trail

RBAC ENFORCEMENT (Requirement #1):
- Citizen: sirf apni complaints dekh sakta hai
- Inspector: sirf assigned complaints dekh sakta hai
- Admin: saari complaints dekh sakta hai

STATUS WORKFLOW (Requirement #2):
SUBMITTED → ASSIGNED (admin ke through assignments router)
ASSIGNED  → INSPECTED (inspector PUT /inspect)
INSPECTED → RESOLVED or REJECTED (admin PUT /status)

AUDIT LOG (Requirement #2):
Har status change pe audit_logs mein entry hoti hai.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintStatus
from app.models.audit_log import AuditLog
from app.schemas.complaint import (
    ComplaintCreate, ComplaintResponse,
    ComplaintUpdate, ComplaintStatusUpdate,
    AuditLogResponse
)
from app.middleware.rbac import (
    any_authenticated_user, citizen_only,
    inspector_or_admin, admin_only
)

router = APIRouter(prefix="/complaints", tags=["Complaints"])


def create_audit_log(
    db: Session,
    complaint_id: int,
    changed_by: int,
    action: str,
    old_status=None,
    new_status=None,
    notes: str = None
):
    """
    Helper function — har status change pe audit log banao.
    Requirement #2: "Every status change logged in audit_logs"
    """
    log = AuditLog(
        complaint_id=complaint_id,
        changed_by=changed_by,
        action=action,
        old_status=old_status,
        new_status=new_status,
        notes=notes
    )
    db.add(log)
    # Note: Caller commit karega


@router.post("/", response_model=ComplaintResponse, status_code=201)
def create_complaint(
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(citizen_only)  # SIRF CITIZEN!
):
    """
    Nayi complaint file karo.
    Requirement #1: Sirf Citizens complaint file kar sakte hain
    Requirement #4: Real Kanpur location names
    """
    new_complaint = Complaint(
        citizen_id=current_user.id,
        area=complaint_data.area,
        street_address=complaint_data.street_address,
        landmark=complaint_data.landmark,
        latitude=complaint_data.latitude,
        longitude=complaint_data.longitude,
        description=complaint_data.description,
        severity=complaint_data.severity,
        photo_url=complaint_data.photo_url,
        status=ComplaintStatus.SUBMITTED
    )

    db.add(new_complaint)
    db.flush()  # ID generate karo commit se pehle

    # Audit log — Complaint submitted
    create_audit_log(
        db=db,
        complaint_id=new_complaint.id,
        changed_by=current_user.id,
        action="COMPLAINT_SUBMITTED",
        new_status=ComplaintStatus.SUBMITTED,
        notes=f"Complaint filed by {current_user.full_name}"
    )

    db.commit()
    db.refresh(new_complaint)
    return new_complaint


@router.get("/", response_model=List[ComplaintResponse])
def get_complaints(
    area: Optional[str] = Query(None, description="Filter by area"),
    status_filter: Optional[ComplaintStatus] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(any_authenticated_user)
):
    """
    Complaints list — ROLE-BASED FILTERING (Requirement #1):
    - Citizen: sirf apni complaints
    - Inspector: sirf assigned complaints
    - Admin: saari complaints
    """
    query = db.query(Complaint).options(
        joinedload(Complaint.assignment),
        joinedload(Complaint.citizen)
    )

    # RBAC filtering — yahan role check hota hai
    if current_user.role == UserRole.CITIZEN:
        # Citizen sirf apni complaints dekhe
        query = query.filter(Complaint.citizen_id == current_user.id)

    elif current_user.role == UserRole.INSPECTOR:
        # Inspector sirf assigned complaints dekhe
        from app.models.assignment import Assignment
        query = query.join(Assignment).filter(
            Assignment.inspector_id == current_user.id
        )

    # Admin: koi filter nahi — saari complaints

    # Additional filters (optional query params)
    if area:
        query = query.filter(Complaint.area.ilike(f"%{area}%"))
    if status_filter:
        query = query.filter(Complaint.status == status_filter)

    complaints = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()

    # Response mein citizen name add karo
    result = []
    for c in complaints:
        c_dict = ComplaintResponse.model_validate(c)
        c_dict.citizen_name = c.citizen.full_name if c.citizen else None
        if c.assignment and c.assignment.inspector:
            c_dict.assignment.inspector_name = c.assignment.inspector.full_name
        result.append(c_dict)

    return result


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint_detail(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(any_authenticated_user)
):
    """Single complaint ki detail"""
    complaint = db.query(Complaint).options(
        joinedload(Complaint.assignment),
        joinedload(Complaint.citizen)
    ).filter(Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint nahi mili")

    # Access control
    if current_user.role == UserRole.CITIZEN and complaint.citizen_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Aap sirf apni complaints dekh sakte hain"
        )

    result = ComplaintResponse.model_validate(complaint)
    result.citizen_name = complaint.citizen.full_name if complaint.citizen else None
    return result


@router.put("/{complaint_id}/inspect", response_model=ComplaintResponse)
def inspector_update(
    complaint_id: int,
    update_data: ComplaintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(any_authenticated_user)
):
    """
    Inspector site visit ke baad update karta hai.
    Requirement #1: Sirf assigned Inspector yeh kar sakta hai
    Status change: ASSIGNED → INSPECTED
    """
    if current_user.role != UserRole.INSPECTOR:
        raise HTTPException(status_code=403, detail="Sirf inspector yeh action kar sakta hai")

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint nahi mili")

    # Check ki yeh complaint is inspector ko assigned hai
    from app.models.assignment import Assignment
    assignment = db.query(Assignment).filter(
        Assignment.complaint_id == complaint_id,
        Assignment.inspector_id == current_user.id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=403,
            detail="Yeh complaint aapko assign nahi ki gayi"
        )

    if complaint.status != ComplaintStatus.ASSIGNED:
        raise HTTPException(
            status_code=400,
            detail=f"ASSIGNED status wali complaints hi inspect ki ja sakti hain. Current: {complaint.status}"
        )

    old_status = complaint.status

    # Update complaint
    if update_data.inspector_notes:
        complaint.inspector_notes = update_data.inspector_notes
    if update_data.proof_photo_url:
        complaint.proof_photo_url = update_data.proof_photo_url

    # Status: ASSIGNED → INSPECTED
    complaint.status = ComplaintStatus.INSPECTED

    # Assignment update
    assignment.visit_completed_at = datetime.utcnow()

    # AUDIT LOG (Requirement #2)
    create_audit_log(
        db=db,
        complaint_id=complaint_id,
        changed_by=current_user.id,
        action="SITE_INSPECTED",
        old_status=old_status,
        new_status=ComplaintStatus.INSPECTED,
        notes=f"Inspector {current_user.full_name} ne site visit complete ki"
    )

    db.commit()
    db.refresh(complaint)
    return complaint


@router.put("/{complaint_id}/status", response_model=ComplaintResponse)
def update_status(
    complaint_id: int,
    status_data: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)  # SIRF ADMIN!
):
    """
    Admin complaint ka status change karta hai.
    Requirement #1: Sirf Admin
    Requirement #2: Status workflow + audit log
    
    Valid transitions:
    INSPECTED → RESOLVED
    INSPECTED → REJECTED
    SUBMITTED → REJECTED (directly reject bhi ho sakta hai)
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint nahi mili")

    old_status = complaint.status
    new_status = status_data.status

    # Valid transition check
    VALID_TRANSITIONS = {
        ComplaintStatus.SUBMITTED: [ComplaintStatus.REJECTED],
        ComplaintStatus.ASSIGNED: [ComplaintStatus.REJECTED],
        ComplaintStatus.INSPECTED: [ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED],
    }

    allowed = VALID_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"'{old_status}' se '{new_status}' transition allowed nahi. Allowed: {[s.value for s in allowed]}"
        )

    complaint.status = new_status

    # Resolve time record karo (Requirement #3: avg resolution time)
    if new_status == ComplaintStatus.RESOLVED:
        complaint.resolved_at = datetime.utcnow()

    # AUDIT LOG (Requirement #2)
    action = "COMPLAINT_RESOLVED" if new_status == ComplaintStatus.RESOLVED else "COMPLAINT_REJECTED"
    create_audit_log(
        db=db,
        complaint_id=complaint_id,
        changed_by=current_user.id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        notes=status_data.notes
    )

    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("/{complaint_id}/audit-log", response_model=List[AuditLogResponse])
def get_audit_log(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(inspector_or_admin)
):
    """
    Complaint ka pura audit trail dekho.
    Requirement #2: Every status change logged
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint nahi mili")

    logs = db.query(AuditLog).options(
        joinedload(AuditLog.changed_by_user)
    ).filter(
        AuditLog.complaint_id == complaint_id
    ).order_by(AuditLog.timestamp).all()

    result = []
    for log in logs:
        log_resp = AuditLogResponse.model_validate(log)
        log_resp.changer_name = log.changed_by_user.full_name if log.changed_by_user else None
        result.append(log_resp)

    return result
