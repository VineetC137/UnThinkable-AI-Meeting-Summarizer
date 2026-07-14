"""
API dependencies for authentication, database, and common functionality.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import credentials_exception
from app.models.user import User, UserRole
from app.services.auth_service import auth_service

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    """
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(db, token)
        return user
    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (additional check for is_active).
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with admin role.
    """
    auth_service.require_role(current_user, UserRole.ADMIN)
    return current_user


# Optional authentication (for public endpoints that can work with or without auth)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token is provided, otherwise return None.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(db, token)
        return user
    except Exception:
        return None


class CommonQueryParams:
    """
    Common query parameters for pagination and filtering.
    """
    def __init__(
        self,
        page: int = 1,
        per_page: int = 20,
        skip: Optional[int] = None,
        limit: Optional[int] = None
    ):
        # Support both page/per_page and skip/limit patterns
        if skip is not None or limit is not None:
            self.skip = skip or 0
            self.limit = min(limit or 100, 100)  # Max 100 items per request
        else:
            page = max(1, page)  # Ensure page is at least 1
            per_page = min(max(1, per_page), 100)  # Between 1 and 100
            self.skip = (page - 1) * per_page
            self.limit = per_page
            
        self.page = page if 'page' in locals() else (self.skip // self.limit) + 1
        self.per_page = self.limit


def get_pagination_params() -> CommonQueryParams:
    """Dependency for pagination parameters."""
    return CommonQueryParams