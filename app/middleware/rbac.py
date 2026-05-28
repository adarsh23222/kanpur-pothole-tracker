"""
middleware/rbac.py — Role-Based Access Control
------------------------------------------------
Yeh file RBAC implement karti hai — "Role Decorator on every protected endpoint"

HOW RBAC WORKS HERE:
- require_roles() ek factory function hai
- Yeh ek FastAPI dependency return karta hai
- Dependency check karta hai ki current user ka role allowed hai ya nahi

EXAMPLE USE:
@router.get("/admin-only")
def admin_endpoint(user = Depends(require_roles(UserRole.ADMIN))):
    ...

@router.get("/inspector-or-admin")  
def shared_endpoint(user = Depends(require_roles(UserRole.INSPECTOR, UserRole.ADMIN))):
    ...

Requirement #1 (RBAC) DIRECTLY fulfill ho raha hai yahan!
Teen roles, alag-alag endpoints pe alag-alag access.
"""
from fastapi import Depends, HTTPException, status
from app.models.user import User, UserRole
from app.middleware.auth import get_current_user


def require_roles(*allowed_roles: UserRole):
    """
    Role check karne wala dependency factory.
    
    *allowed_roles: Kitne bhi roles pass karo
    Returns: FastAPI dependency function
    
    Agar user ka role allowed_roles mein nahi hai →
    403 Forbidden error
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied! "
                    f"Aapka role '{current_user.role}' is endpoint ke liye allowed nahi. "
                    f"Required roles: {[r.value for r in allowed_roles]}"
                )
            )
        return current_user

    return role_checker


# ---- SHORTCUT DEPENDENCIES ----
# Yeh shortcuts endpoints mein directly use karo — code cleaner lagta hai

def citizen_only(current_user: User = Depends(require_roles(UserRole.CITIZEN))):
    """Sirf Citizens access kar sakte hain"""
    return current_user


def inspector_only(current_user: User = Depends(require_roles(UserRole.INSPECTOR))):
    """Sirf Inspectors access kar sakte hain"""
    return current_user


def admin_only(current_user: User = Depends(require_roles(UserRole.ADMIN))):
    """Sirf Admins access kar sakte hain"""
    return current_user


def inspector_or_admin(
    current_user: User = Depends(require_roles(UserRole.INSPECTOR, UserRole.ADMIN))
):
    """Inspector ya Admin — dono access kar sakte hain"""
    return current_user


def any_authenticated_user(current_user: User = Depends(get_current_user)):
    """Koi bhi logged-in user — bas authentication chahiye"""
    return current_user
