"""
routers/analytics.py — Analytics & Reporting
----------------------------------------------
Requirement #3 DIRECTLY fulfill ho raha hai yahan.

ENDPOINTS:
GET /analytics/dashboard         — Full admin dashboard
GET /analytics/area-wise         — Area-wise pending count
GET /analytics/inspector-wise    — Inspector performance
GET /analytics/monthly-trend     — Month-by-month trend
GET /analytics/resolution-time   — Average resolution time
GET /analytics/export-csv        — CSV export (Requirement #3)

Requirement #3 fulfill ho raha hai —
- Area-wise pending complaints count ✓
- Inspector-wise resolved complaints ✓
- Monthly complaint trend ✓
- Average resolution time ✓
- CSV export of all complaints ✓

Requirement #1 fulfill ho raha hai — Sirf Admin access kar sakta hai
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from typing import List
from datetime import datetime
import pandas as pd
import io

from app.database import get_db
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintStatus
from app.models.assignment import Assignment
from app.schemas.complaint import (
    AnalyticsDashboard, AreaWiseCount,
    InspectorWiseResolved, MonthlyTrend
)
from app.middleware.rbac import admin_only

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboard)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)  # SIRF ADMIN!
):
    """
    Admin ka full analytics dashboard.
    Ek API call mein saara data.
    Requirement #3 ka main endpoint.
    """

    # ---- OVERALL COUNTS ----
    total = db.query(func.count(Complaint.id)).scalar()
    pending = db.query(func.count(Complaint.id)).filter(
        Complaint.status.in_([ComplaintStatus.SUBMITTED, ComplaintStatus.ASSIGNED, ComplaintStatus.INSPECTED])
    ).scalar()
    resolved = db.query(func.count(Complaint.id)).filter(
        Complaint.status == ComplaintStatus.RESOLVED
    ).scalar()
    rejected = db.query(func.count(Complaint.id)).filter(
        Complaint.status == ComplaintStatus.REJECTED
    ).scalar()

    # ---- AVERAGE RESOLUTION TIME (Requirement #3) ----
    # resolved_at - created_at = kitne din lage
    resolved_complaints = db.query(
        Complaint.created_at,
        Complaint.resolved_at
    ).filter(
        Complaint.status == ComplaintStatus.RESOLVED,
        Complaint.resolved_at.isnot(None)
    ).all()

    if resolved_complaints:
        total_days = sum(
            (r.resolved_at - r.created_at).days
            for r in resolved_complaints
        )
        avg_days = round(total_days / len(resolved_complaints), 1)
    else:
        avg_days = 0.0

    # ---- AREA-WISE (Requirement #3) ----
    area_data = db.query(
        Complaint.area,
        func.count(Complaint.id).label("total_count"),
        func.sum(
            case(
                (Complaint.status.in_([
                    ComplaintStatus.SUBMITTED,
                    ComplaintStatus.ASSIGNED,
                    ComplaintStatus.INSPECTED
                ]), 1),
                else_=0
            )
        ).label("pending_count")
    ).group_by(Complaint.area).order_by(
        func.count(Complaint.id).desc()
    ).all()

    area_wise = [
        AreaWiseCount(
            area=row.area,
            total_count=row.total_count,
            pending_count=row.pending_count or 0
        )
        for row in area_data
    ]

    # ---- INSPECTOR-WISE (Requirement #3) ----
    inspector_data = db.query(
        User.id,
        User.full_name,
        func.count(Assignment.id).label("total_assigned"),
        func.sum(
            case(
                (Complaint.status == ComplaintStatus.RESOLVED, 1),
                else_=0
            )
        ).label("resolved_count"),
        func.sum(
            case(
                (Complaint.status.in_([
                    ComplaintStatus.INSPECTED,
                    ComplaintStatus.RESOLVED
                ]), 1),
                else_=0
            )
        ).label("inspected_count")
    ).join(
        Assignment, Assignment.inspector_id == User.id
    ).join(
        Complaint, Complaint.id == Assignment.complaint_id
    ).filter(
        User.role == UserRole.INSPECTOR
    ).group_by(User.id, User.full_name).all()

    inspector_wise = [
        InspectorWiseResolved(
            inspector_id=row.id,
            inspector_name=row.full_name,
            resolved_count=row.resolved_count or 0,
            inspected_count=row.inspected_count or 0
        )
        for row in inspector_data
    ]

    # ---- MONTHLY TREND (Requirement #3) ----
    monthly_data = db.query(
        extract("year", Complaint.created_at).label("year"),
        extract("month", Complaint.created_at).label("month"),
        func.count(Complaint.id).label("complaint_count"),
        func.sum(
            case(
                (Complaint.status == ComplaintStatus.RESOLVED, 1),
                else_=0
            )
        ).label("resolved_count")
    ).group_by("year", "month").order_by("year", "month").all()

    MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    monthly_trend = [
        MonthlyTrend(
            month=f"{int(row.year)}-{int(row.month):02d}",
            month_name=f"{MONTHS[int(row.month)]} {int(row.year)}",
            complaint_count=row.complaint_count,
            resolved_count=row.resolved_count or 0
        )
        for row in monthly_data
    ]

    return AnalyticsDashboard(
        total_complaints=total,
        pending_complaints=pending,
        resolved_complaints=resolved,
        rejected_complaints=rejected,
        avg_resolution_days=avg_days,
        area_wise=area_wise,
        inspector_wise=inspector_wise,
        monthly_trend=monthly_trend
    )


@router.get("/area-wise", response_model=List[AreaWiseCount])
def area_wise_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    """Area-wise complaint count — Requirement #3"""
    data = db.query(
        Complaint.area,
        func.count(Complaint.id).label("total_count"),
        func.sum(
            case(
                (Complaint.status.in_([
                    ComplaintStatus.SUBMITTED,
                    ComplaintStatus.ASSIGNED,
                    ComplaintStatus.INSPECTED
                ]), 1),
                else_=0
            )
        ).label("pending_count")
    ).group_by(Complaint.area).order_by(func.count(Complaint.id).desc()).all()

    return [
        AreaWiseCount(area=r.area, total_count=r.total_count, pending_count=r.pending_count or 0)
        for r in data
    ]


@router.get("/inspector-wise", response_model=List[InspectorWiseResolved])
def inspector_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    """Inspector-wise resolved count — Requirement #3"""
    data = db.query(
        User.id,
        User.full_name,
        func.sum(
            case((Complaint.status == ComplaintStatus.RESOLVED, 1), else_=0)
        ).label("resolved_count"),
        func.sum(
            case(
                (Complaint.status.in_([ComplaintStatus.INSPECTED, ComplaintStatus.RESOLVED]), 1),
                else_=0
            )
        ).label("inspected_count")
    ).join(Assignment, Assignment.inspector_id == User.id
    ).join(Complaint, Complaint.id == Assignment.complaint_id
    ).filter(User.role == UserRole.INSPECTOR
    ).group_by(User.id, User.full_name).all()

    return [
        InspectorWiseResolved(
            inspector_id=r.id,
            inspector_name=r.full_name,
            resolved_count=r.resolved_count or 0,
            inspected_count=r.inspected_count or 0
        )
        for r in data
    ]


@router.get("/export-csv")
def export_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)  # SIRF ADMIN!
):
    """
    CSV Export — Requirement #3: "CSV export of all complaints"
    
    Pandas se DataFrame banao aur CSV mein convert karo.
    StreamingResponse se browser mein file download hogi.
    """
    complaints = db.query(
        Complaint.id,
        Complaint.area,
        Complaint.street_address,
        Complaint.landmark,
        Complaint.description,
        Complaint.severity,
        Complaint.status,
        Complaint.created_at,
        Complaint.resolved_at,
        User.full_name.label("citizen_name"),
        User.email.label("citizen_email")
    ).join(User, User.id == Complaint.citizen_id).all()

    if not complaints:
        raise HTTPException(status_code=404, detail="Koi complaint nahi mili")

    # Pandas DataFrame banao
    data = [{
        "Complaint ID": c.id,
        "Area": c.area,
        "Street Address": c.street_address,
        "Landmark": c.landmark or "",
        "Description": c.description,
        "Severity": c.severity,
        "Status": c.status,
        "Citizen Name": c.citizen_name,
        "Citizen Email": c.citizen_email,
        "Filed On": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "",
        "Resolved On": c.resolved_at.strftime("%Y-%m-%d %H:%M") if c.resolved_at else "Pending"
    } for c in complaints]

    df = pd.DataFrame(data)

    # CSV string banao
    output = io.StringIO()
    df.to_csv(output, index=False, encoding="utf-8-sig")  # utf-8-sig for Excel compatibility
    output.seek(0)

    filename = f"kanpur_pothole_complaints_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
