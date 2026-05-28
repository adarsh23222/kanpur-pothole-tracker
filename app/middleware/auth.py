"""
middleware/auth.py — JWT Authentication
-----------------------------------------
Yeh file JWT tokens create aur verify karti hai.

JWT (JSON Web Token) kya hota hai?
- Jab user login karta hai → server ek encrypted token deta hai
- Har protected request mein client yeh token bhejta hai
- Server token decode karke user ki identity verify karta hai

TOKEN STRUCTURE:
Header.Payload.Signature
- Header: Algorithm info
- Payload: user_id, role, email, expiry (yahi important hai)
- Signature: Server ka secret key se encrypt

EXAMPLE PAYLOAD:
{
  "user_id": 5,
  "role": "inspector",
  "email": "rajesh@kanpur.gov.in",
  "exp": 1700000000  ← expiry timestamp
}

Requirement #5 fulfill ho raha hai — JWT authentication
Requirement #1 fulfill ho raha hai — role JWT payload mein store hai
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenData

# bcrypt context — password hashing ke liye
# bcrypt automatically salt add karta hai (rainbow table attacks se bachata hai)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme — "Authorization: Bearer <token>" header expect karta hai
security = HTTPBearer()


# ---- PASSWORD FUNCTIONS ----

def hash_password(plain_password: str) -> str:
    """Plain text password ko bcrypt hash mein convert karo"""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Login ke time: user ka password check karo"""
    return pwd_context.verify(plain_password, hashed_password)


# ---- JWT FUNCTIONS ----

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    JWT token banao.
    
    data mein: user_id, role, email
    Token mein expiry add hoti hai automatically
    """
    to_encode = data.copy()

    # Expiry set karo
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    # Secret key se sign karo
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Token decode karo aur data extract karo.
    Agar token invalid/expired → HTTPException raise karo
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please login again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        email: str = payload.get("email")

        if user_id is None:
            raise credentials_exception

        return TokenData(user_id=user_id, role=role, email=email)

    except JWTError:
        raise credentials_exception


# ---- FASTAPI DEPENDENCIES ----

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI Dependency — har protected endpoint use karega.
    
    Kaise kaam karta hai:
    1. Request header se Bearer token lo
    2. Token decode karo
    3. Database se user load karo
    4. User return karo
    
    Use: current_user: User = Depends(get_current_user)
    """
    token_data = decode_token(credentials.credentials)

    user = db.query(User).filter(
        User.id == token_data.user_id,
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account deactivated"
        )

    return user
