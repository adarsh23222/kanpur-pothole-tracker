"""
routers/assignments.py — Assignment Management
------------------------------------------------
Admin Inspector ko complaints assign karta hai yahan.

ENDPOINTS:
POST /assignments/              — Admin: manually assign
POST /assignments/auto-assign/{id} — Admin: auto-assign nearest inspector
GET  /assignments/my-work       — Inspector: apna assigned work dekho
GET  /assignments/              — Admin: saari assignments dekho

AUTO-ASSIGN LOGIC (Requirement #2):
Nearest Inspector = Jo inspector complaint ke same area mein kaam karta hai.
Agar same area inspector nahi mila → workload kam wala inspector assign karo.

Requirement #1 fulfill ho raha hai — Admin assigns, Inspector views own work
Requirement #2 fulfill ho raha hai — Auto-assign logic, audit logging
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintStatus
from app.models.assignment import Assignment
from app.models.audit_log import AuditLog
from app.schemas.complaint import AssignmentCreate, AssignmentResponse
from app.middleware.rbac import admin_only, inspector_only, any_authenticated_user

router = APIRouter(prefix="/assignments", tags=["Assignments"])


def log_assignment(db, complaint_id, changed_by, inspector_id, notes=None):
    """Assignment ke liye audit log"""
    log = AuditLog(
        complaint_id=complaint_id,
        changed_by=changed_by,
        action="INSPECTOR_ASSIGNED",
        old_status=ComplaintStatus.SUBMITTED,
        new_status=ComplaintStatus.ASSIGNED,
        notes=notes or f"Inspector ID {inspector_id} ko assign kiya"
    )
    db.add(log)


@router.post("/", response_model=AssignmentResponse, status_code=201)
def assign_inspector(
    assign_data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)  # SIRF ADMIN!
):
    """
    Admin manually inspector assign karta hai.
    Requirement #1: Sirf Admin assign kar sakta hai
    """
    # Complaint exist karta hai?
    complaint = db.query(Complaint).filter(
        Complaint.id == assign_data.complaint_id
    ).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint nahi mili")

    # Sirf SUBMITTED complaints assign ho sakti hain
    if complaint.status != ComplaintStatus.SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail=f"Sirf SUBMITTED complaints assign ho sakti hain. Current status: {complaint.status}"
        )

    # Already assigned?
    existing = db.query(Assignment).filter(
        Assignment.complaint_id == assign_data.complaint_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Yeh complaint pehle se assign hai"
        )

    # Inspector exist karta hai aur active hai?
    inspector = db.query(User).filter(
        User.id == assign_data.inspector_id,
        User.role == UserRole.INSPECTOR,
        User.is_active == True
    ).first()
    if not inspector:
        raise HTTPException(
            status_code=404,
            detail="Inspector nahi mila ya inactive hai"
        )

    # Assignment banao
    assignment = Assignment(
        complaint_id=assign_data.complaint_id,
        inspector_id=assign_data.inspector_id,
        assigned_by=current_user.id,
        visit_scheduled_at=assign_data.visit_scheduled_at,
        admin_notes=assign_data.admin_notes
    )
    db.add(assignment)

    # Complaint ka status update karo
    complaint.status = ComplaintStatus.ASSIGNED

    # AUDIT LOG (Requirement #2)
    log_assignment(
        db=db,
        complaint_id=complaint.id,
        changed_by=current_user.id,
        inspector_id=inspector.id,
        notes=f"Admin {current_user.full_name} ne {inspector.full_name} ko assign kiya"
    )

    db.commit()
    db.refresh(assignment)
    return assignment


@router.post("/auto-assign/{complaint_id}", response_model=AssignmentResponse)
def auto_assign_inspector(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)  # SIRF ADMIN!
):
    """
    AUTO-ASSIGN LOGIC (Requirement #2):
    
    Step 1: Complaint ka area dekho
    Step 2: Same area mein inspector dhundho
    Step 3: Agar mila → assign karo
    Step 4: Nahi mila → sabse kam assignments wala inspector assign karo
    
    Yeh "nearest inspector" logic hai — area-based proximity.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint nahi mili")

    if complaint.status != ComplaintStatus.SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail=f"Sirf SUBMITTED complaints auto-assign ho sakti hain"
        )

    existing = db.query(Assignment).filter(
        Assignment.complaint_id == complaint_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Pehle se assigned hai")

    # ---- AUTO-ASSIGN ALGORITHM ----

    # Step 1: Same area ka active inspector dhundho
    # Inspector ka 'area' field complaint ke 'area' se match karo
    area_inspector = db.query(User).filter(
        User.role == UserRole.INSPECTOR,
        User.is_active == True,
        User.area.ilike(f"%{complaint.area}%")  # Case-insensitive match
    ).first()

    selected_inspector = area_inspector

    if not selected_inspector:
        # Step 2: Koi same-area inspector nahi mila
        # Sabse kam active assignments wala inspector select karo (load balancing)
        inspector_load = db.query(
            User.id,
            func.count(Assignment.id).label("active_count")
        ).outerjoin(
            Assignment,
            (Assignment.inspector_id == User.id) &
            (Assignment.visit_completed_at.is_(None))  # Active assignments only
        ).filter(
            User.role == UserRole.INSPECTOR,
            User.is_active == True
        ).group_by(User.id).order_by("active_count").first()

        if not inspector_load:
            raise HTTPException(
                status_code=404,
                detail="Koi active inspector available nahi hai"
            )

        selected_inspector = db.query(User).filter(
            User.id == inspector_load.id
        ).first()

    # Assignment create karo
    assignment = Assignment(
        complaint_id=complaint_id,
        inspector_id=selected_inspector.id,
        assigned_by=current_user.id,
        admin_notes=f"Auto-assigned based on area: {complaint.area}"
    )
    db.add(assignment)

    complaint.status = ComplaintStatus.ASSIGNED

    log_assignment(
        db=db,
        complaint_id=complaint_id,
        changed_by=current_user.id,
        inspector_id=selected_inspector.id,
        notes=f"Auto-assigned: {selected_inspector.full_name} (area: {selected_inspector.area})"
    )

    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/my-work", response_model=List[dict])
def get_my_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(inspector_only)  # SIRF INSPECTOR!
):
    """
    Inspector ka apna work queue.
    Requirement #1: Inspector sirf apna assigned work dekhe
    """
    assignments = db.query(Assignment).options(
        joinedload(Assignment.complaint)
    ).filter(
        Assignment.inspector_id == current_user.id
    ).all()

    result = []
    for a in assignments:
        result.append({
            "assignment_id": a.id,
            "complaint_id": a.complaint_id,
            "area": a.complaint.area if a.complaint else None,
            "street_address": a.complaint.street_address if a.complaint else None,
            "severity": a.complaint.severity if a.complaint else None,
            "status": a.complaint.status if a.complaint else None,
            "description": a.complaint.description if a.complaint else None,
            "assigned_at": a.assigned_at,
            "visit_scheduled_at": a.visit_scheduled_at,
            "visit_completed_at": a.visit_completed_at,
            "admin_notes": a.admin_notes
        })
    return result


@router.get("/", response_model=List[AssignmentResponse])
def get_all_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)  # SIRF ADMIN!
):
    """Admin saari assignments dekhe"""
    assignments = db.query(Assignment).order_by(
        Assignment.assigned_at.desc()
    ).all()
    return assignments
