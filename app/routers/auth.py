"""
routers/auth.py — Authentication Endpoints with Username Support
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (UserCreate, UserLogin, UserResponse,
                               Token, UsernameCheck)
from app.middleware.auth import (hash_password, verify_password,
                                 create_access_token, get_current_user)
from app.middleware.rbac import admin_only, any_authenticated_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


def generate_unique_username(base: str, db: Session) -> str:
    """Generate a unique username from full name"""
    # Clean: lowercase, remove spaces, keep alphanumeric
    base = "".join(c for c in base.lower() if c.isalnum())[:15]
    username = base
    counter  = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base}{counter}"
        counter += 1
    return username


@router.get("/check-username/{username}", response_model=UsernameCheck)
def check_username(username: str, db: Session = Depends(get_db)):
    """
    Check if a username is available — called live during signup.
    """
    # Validate format
    if len(username) < 3:
        return UsernameCheck(username=username, available=False,
                             message="Username must be at least 3 characters")
    if not username.replace("_","").replace(".","").isalnum():
        return UsernameCheck(username=username, available=False,
                             message="Only letters, numbers, _ and . allowed")

    exists = db.query(User).filter(User.username == username.lower()).first()
    return UsernameCheck(
        username=username,
        available=not exists,
        message="Available" if not exists else "Username already taken"
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""

    # Email duplicate check
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400,
                            detail="An account with this email already exists")

    # Username handling
    if user_data.username:
        uname = user_data.username.lower()
        if db.query(User).filter(User.username == uname).first():
            raise HTTPException(status_code=400,
                                detail="This username is already taken")
    else:
        # Auto-generate from full name
        uname = generate_unique_username(user_data.full_name, db)

    # Inspector area check
    if user_data.role == UserRole.INSPECTOR and not user_data.area:
        raise HTTPException(status_code=400,
                            detail="Area is required for inspector accounts")

    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        username=uname,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        area=user_data.area
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login with username OR email.
    The 'login' field accepts both.
    """
    login_val = user_data.login.strip().lower()

    # Find by username OR email
    user = db.query(User).filter(
        or_(User.username == login_val, User.email == login_val),
        User.is_active == True
    ).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your username and password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(data={
        "user_id": user.id,
        "role":    user.role.value,
        "email":   user.email
    })

    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        role=user.role,
        full_name=user.full_name,
        username=user.username
    )


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(any_authenticated_user)):
    return current_user


@router.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db),
                  current_user: User = Depends(admin_only)):
    return db.query(User).all()


@router.get("/inspectors", response_model=List[UserResponse])
def get_all_inspectors(db: Session = Depends(get_db),
                       current_user: User = Depends(admin_only)):
    return db.query(User).filter(
        User.role == UserRole.INSPECTOR,
        User.is_active == True
    ).all()
