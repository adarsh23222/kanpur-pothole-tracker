# 🚧 Kanpur Pothole Tracker
### Civic Complaint Management System — BCA Final Year Project

> **Developed by:** [Your Name] | BCA Final Year  
> **College:** [Your College Name]  
> **Tech Stack:** FastAPI + PostgreSQL + SQLAlchemy + JWT

---

## 📋 Project Overview

Kanpur Nagar Nigam ke liye ek pothole complaint management system jisme:
- **Citizens** sadak ke gaddho ki complaint file kar sakte hain
- **Inspectors** assigned complaints ki site visit kar ke verify karte hain  
- **Admins** complaints manage karte hain, analytics dekhte hain, CSV export karte hain

---

## ⚙️ SETUP GUIDE (Step by Step)

### Step 1: Prerequisites Install Karo
```bash
# Python 3.11+ required
python --version

# PostgreSQL install aur start karo
# Windows: pgAdmin use karo
# Ubuntu: sudo apt install postgresql
```

### Step 2: Project Clone / Extract Karo
```bash
cd kanpur_pothole_tracker
```

### Step 3: Virtual Environment Banao
```bash
# Virtual environment create karo
python -m venv venv

# Activate karo
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 4: Dependencies Install Karo
```bash
pip install -r requirements.txt
```

### Step 5: PostgreSQL Database Banao
```sql
-- pgAdmin ya psql mein yeh run karo:
CREATE DATABASE kanpur_pothole_db;
```

### Step 6: .env File Configure Karo
```bash
# .env file mein apna PostgreSQL password daalo:
DATABASE_URL=postgresql://postgres:YOURPASSWORD@localhost:5432/kanpur_pothole_db
```

### Step 7: Database Seed Karo (Tables + Data)
```bash
python -m app.seed.seed_data
```
Expected output:
```
✅ 9 users created
✅ 27 complaints created  
✅ 5 RESOLVED, 5 INSPECTED, 8 ASSIGNED
```

### Step 8: Server Start Karo
```bash
uvicorn app.main:app --reload --port 8000
```

### Step 9: Swagger UI Open Karo
```
http://localhost:8000/docs
```

---

## 🔑 Login Credentials (After Seeding)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@kanpurnagarnigam.in | admin123 |
| Inspector | rajesh.inspector@kanpur.gov.in | inspector123 |
| Inspector | sunil.inspector@kanpur.gov.in | inspector123 |
| Inspector | meena.inspector@kanpur.gov.in | inspector123 |
| Citizen | priya.singh@gmail.com | citizen123 |
| Citizen | ramesh.mishra@yahoo.com | citizen123 |

---

## 📡 API Endpoints

### 🔐 Authentication (`/auth`)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/auth/register` | Public | New user register |
| POST | `/auth/login` | Public | Login → JWT token |
| GET | `/auth/me` | All | Apni profile |
| GET | `/auth/users` | Admin | All users |
| GET | `/auth/inspectors` | Admin | All inspectors |

### 📋 Complaints (`/complaints`)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/complaints/` | Citizen | File complaint |
| GET | `/complaints/` | All* | List (role-filtered) |
| GET | `/complaints/{id}` | All* | Detail |
| PUT | `/complaints/{id}/inspect` | Inspector | Update visit |
| PUT | `/complaints/{id}/status` | Admin | Change status |
| GET | `/complaints/{id}/audit-log` | Insp+Admin | Audit trail |

### 📌 Assignments (`/assignments`)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/assignments/` | Admin | Manual assign |
| POST | `/assignments/auto-assign/{id}` | Admin | Auto assign |
| GET | `/assignments/my-work` | Inspector | My queue |
| GET | `/assignments/` | Admin | All assignments |

### 📊 Analytics (`/analytics`)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/analytics/dashboard` | Admin | Full dashboard |
| GET | `/analytics/area-wise` | Admin | Area stats |
| GET | `/analytics/inspector-wise` | Admin | Inspector stats |
| GET | `/analytics/export-csv` | Admin | Download CSV |

---

## 🔄 Status Workflow

```
SUBMITTED  →  ASSIGNED  →  INSPECTED  →  RESOLVED
    ↓              ↓             ↓
  (Admin        (Admin        (Admin
  rejects)      rejects)      rejects)
    ↓              ↓             ↓
  REJECTED      REJECTED      REJECTED
```

---

## 5️⃣ How 5 Requirements Are Fulfilled

| Requirement | Implementation |
|-------------|---------------|
| **RBAC** | `middleware/rbac.py` — `require_roles()` decorator har endpoint pe |
| **Complex DB** | 4 tables + status workflow + audit logs + auto-assign |
| **Analytics** | `/analytics/dashboard` — area, inspector, monthly, CSV |
| **Real World** | 27 Kanpur complaints, GT Road, Vijay Nagar, Rawatpur etc. |
| **Backend Heavy** | FastAPI + PostgreSQL + SQLAlchemy + Alembic + JWT + Pydantic |

---

## 🏗️ Project Structure

```
kanpur_pothole_tracker/
├── app/
│   ├── main.py              ← FastAPI entry point
│   ├── config.py            ← Settings from .env
│   ├── database.py          ← DB connection + session
│   ├── models/
│   │   ├── user.py          ← Users table (RBAC roles)
│   │   ├── complaint.py     ← Complaints table (workflow)
│   │   ├── assignment.py    ← Assignments table
│   │   └── audit_log.py     ← Audit trail table
│   ├── schemas/
│   │   ├── user.py          ← User Pydantic schemas
│   │   └── complaint.py     ← Complaint/Analytics schemas
│   ├── middleware/
│   │   ├── auth.py          ← JWT create/verify
│   │   └── rbac.py          ← Role decorators
│   ├── routers/
│   │   ├── auth.py          ← Login/Register endpoints
│   │   ├── complaints.py    ← Complaint CRUD
│   │   ├── assignments.py   ← Assignment management
│   │   └── analytics.py     ← Dashboard + CSV export
│   └── seed/
│       └── seed_data.py     ← 27 Kanpur complaints
├── alembic/                 ← DB migrations
├── requirements.txt
└── .env
```
