from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import engine, Base
from app.routers import auth, complaints, assignments, analytics
from app.routers import upload

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="🚧 Kanpur Pothole Tracker API",
    description="""
Kanpur Nagar Nigam — Pothole Complaint Management System

### Roles
- **Citizen**: File complaints, track own complaints
- **Inspector**: View assigned complaints, update site visits
- **Admin**: Full access, assign inspectors, analytics, reports

### Status Workflow
`SUBMITTED` → `ASSIGNED` → `INSPECTED` → `RESOLVED` / `REJECTED`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(assignments.router)
app.include_router(analytics.router)
app.include_router(upload.router)


@app.get("/", tags=["Health"])
def root():
    return JSONResponse({
        "project": "Kanpur Pothole Tracker",
        "status":  "running",
        "version": "1.0.0",
        "docs":    "/docs"
    })


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
