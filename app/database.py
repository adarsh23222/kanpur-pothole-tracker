"""
database.py — Database Connection Setup
-----------------------------------------
Yeh file PostgreSQL se connection banati hai SQLAlchemy ke through.

KEY CONCEPTS:
- engine: Database ka actual connection object
- SessionLocal: Har HTTP request ke liye ek fresh DB session
- Base: Sabhi SQLAlchemy models yahan se inherit karenge
- get_db(): FastAPI dependency — request aate hi session kholo,
            response jaate hi band karo (finally block se)

Requirement #5 (Backend Heavy) fulfill ho raha hai —
PostgreSQL + SQLAlchemy ORM proper setup.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings


# Engine banao — yeh actual PostgreSQL connection manage karta hai
# pool_pre_ping=True means: connection alive hai ya nahi check karo
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # True karo agar SQL queries console mein dekhni ho
)

# Session factory — har request ke liye naya session
SessionLocal = sessionmaker(
    autocommit=False,   # Manual commit karna padega
    autoflush=False,    # Explicit flush karna padega
    bind=engine
)

# Base class — sabhi models yahan se inherit karenge
Base = declarative_base()


def get_db():
    """
    FastAPI Dependency Injection function.
    
    Kaise kaam karta hai:
    1. Request aati hai → naya DB session khulta hai
    2. Request ke baad → finally block mein session band hota hai
    3. yield se FastAPI samajhta hai ki yeh ek generator hai
    
    Use: def some_endpoint(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
