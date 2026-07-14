"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    UserCreate, UserLogin, UserUpdate, User, Token, RefreshToken,
    PasswordReset, PasswordResetConfirm
)
from app.services.auth_service import auth_service
from app.api.dependencies import get_current_active_user
from app.models.user import User as UserModel

router = APIRouter()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    """
    result = auth_service.register_user(db, user_data)
    
    return {
        "message": "User registered successfully",
        "user": User.model_validate(result['user']),
        "access_token": result['tokens']['access_token'],
        "refresh_token": result['tokens']['refresh_token'],
        "token_type": result['tokens']['token_type']
    }


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access tokens.
    """
    result = auth_service.authenticate_user(db, credentials)
    
    return Token(
        access_token=result['tokens']['access_token'],
        refresh_token=result['tokens']['refresh_token'],
        token_type=result['tokens']['token_type']
    )


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_data: RefreshToken,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    tokens = auth_service.refresh_token(db, refresh_data.refresh_token)
    
    return Token(
        access_token=tokens['access_token'],
        refresh_token=tokens['refresh_token'],
        token_type=tokens['token_type']
    )


@router.get("/me", response_model=User)
def get_current_user_info(
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get current user information.
    """
    return User.model_validate(current_user)


@router.put("/me", response_model=User)
def update_profile(
    update_data: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    """
    updated_user = auth_service.update_user_profile(
        db, 
        current_user.id, 
        update_data
    )
    return User.model_validate(updated_user)


@router.post("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    """
    success = auth_service.change_password(
        db,
        current_user.id,
        current_password,
        new_password
    )
    
    return {"message": "Password changed successfully"}


@router.get("/stats")
def get_user_stats(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user statistics and activity summary.
    """
    stats = auth_service.get_user_stats(db, current_user.id)
    return stats


@router.post("/logout")
def logout():
    """
    Logout user (client-side token invalidation).
    """
    return {"message": "Logged out successfully"}


@router.delete("/deactivate")
def deactivate_account(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate current user account.
    """
    success = auth_service.deactivate_user(db, current_user.id)
    return {"message": "Account deactivated successfully"}


# Password reset endpoints (for future implementation)
@router.post("/password-reset")
def request_password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Request password reset (sends email with reset token).
    """
    # TODO: Implement email sending functionality
    return {"message": "Password reset instructions sent to email"}


@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset with token.
    """
    # TODO: Implement password reset confirmation
    return {"message": "Password reset successfully"}