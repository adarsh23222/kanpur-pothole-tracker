"""
schemas/user.py — User Pydantic Schemas
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.CITIZEN
    area: Optional[str] = None
    username: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    """Login with username or email"""
    login: str      # username OR email
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    username: Optional[str]
    role: UserRole
    area: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: UserRole
    full_name: str
    username: Optional[str] = None


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[UserRole] = None
    email: Optional[str] = None


class UsernameCheck(BaseModel):
    username: str
    available: bool
    message: str
