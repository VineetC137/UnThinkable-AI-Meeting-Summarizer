"""
Authentication service for user management and JWT token handling.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import (
    verify_password, create_token_pair, verify_token,
    TOKEN_TYPE_ACCESS, TOKEN_TYPE_REFRESH,
    credentials_exception, inactive_user_exception
)
from app.core.logging import get_logger
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserUpdate, UserLogin
from app.repositories.user_repository import user_repository

logger = get_logger(__name__)


class AuthService:
    """
    Service for authentication and user management.
    """
    
    def __init__(self):
        self.logger = logger
    
    def register_user(self, db: Session, user_data: UserCreate) -> Dict[str, Any]:
        """
        Register a new user.
        
        Returns:
            {
                'user': User,
                'tokens': Dict[str, str]
            }
        """
        try:
            # Check if email already exists
            if user_repository.is_email_taken(db, email=user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Check if username already exists
            if user_repository.is_username_taken(db, username=user_data.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            
            # Create user
            user = user_repository.create(db, obj_in=user_data)
            
            # Generate tokens
            tokens = create_token_pair(user.id)
            
            # Update last login
            user_repository.update_last_login(db, user_id=user.id)
            
            self.logger.info(f"User registered successfully: {user.email}")
            
            return {
                'user': user,
                'tokens': tokens
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error registering user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during registration"
            )
    
    def authenticate_user(self, db: Session, credentials: UserLogin) -> Dict[str, Any]:
        """
        Authenticate user and return tokens.
        
        Returns:
            {
                'user': User,
                'tokens': Dict[str, str]
            }
        """
        try:
            # Authenticate user
            user = user_repository.authenticate(
                db, 
                email=credentials.email, 
                password=credentials.password
            )
            
            if not user:
                self.logger.warning(f"Failed login attempt for email: {credentials.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            if not user.is_active:
                raise inactive_user_exception
            
            # Generate tokens
            tokens = create_token_pair(user.id)
            
            # Update last login
            user_repository.update_last_login(db, user_id=user.id)
            
            self.logger.info(f"User authenticated successfully: {user.email}")
            
            return {
                'user': user,
                'tokens': tokens
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error authenticating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during authentication"
            )
    
    def refresh_token(self, db: Session, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using refresh token.
        
        Returns:
            New token pair
        """
        try:
            # Verify refresh token
            user_id = verify_token(refresh_token, TOKEN_TYPE_REFRESH)
            if not user_id:
                raise credentials_exception
            
            # Get user
            user = user_repository.get(db, int(user_id))
            if not user:
                raise credentials_exception
            
            if not user.is_active:
                raise inactive_user_exception
            
            # Generate new token pair
            tokens = create_token_pair(user.id)
            
            self.logger.info(f"Token refreshed for user: {user.email}")
            
            return tokens
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error refreshing token: {e}")
            raise credentials_exception
    
    def get_current_user(self, db: Session, token: str) -> User:
        """
        Get current user from access token.
        """
        try:
            # Verify access token
            user_id = verify_token(token, TOKEN_TYPE_ACCESS)
            if not user_id:
                raise credentials_exception
            
            # Get user
            user = user_repository.get(db, int(user_id))
            if not user:
                raise credentials_exception
            
            if not user.is_active:
                raise inactive_user_exception
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting current user: {e}")
            raise credentials_exception
    
    def update_user_profile(
        self, 
        db: Session, 
        user_id: int, 
        update_data: UserUpdate
    ) -> User:
        """Update user profile information."""
        try:
            user = user_repository.get(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check email uniqueness if being updated
            if update_data.email and update_data.email != user.email:
                if user_repository.is_email_taken(db, email=update_data.email, exclude_user_id=user_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
            
            # Check username uniqueness if being updated
            if update_data.username and update_data.username != user.username:
                if user_repository.is_username_taken(db, username=update_data.username, exclude_user_id=user_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already taken"
                    )
            
            # Update user
            updated_user = user_repository.update(db, db_obj=user, obj_in=update_data)
            
            self.logger.info(f"User profile updated: {updated_user.email}")
            
            return updated_user
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error updating user profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during profile update"
            )
    
    def change_password(
        self, 
        db: Session, 
        user_id: int, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """Change user password."""
        try:
            user = user_repository.get(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not verify_password(current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Update password
            update_data = UserUpdate(password=new_password)
            user_repository.update(db, db_obj=user, obj_in=update_data)
            
            self.logger.info(f"Password changed for user: {user.email}")
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error changing password: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during password change"
            )
    
    def deactivate_user(self, db: Session, user_id: int) -> bool:
        """Deactivate user account."""
        try:
            user = user_repository.get(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Deactivate user
            update_data = UserUpdate()
            user.is_active = False
            user_repository.update(db, db_obj=user, obj_in=update_data)
            
            self.logger.info(f"User deactivated: {user.email}")
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error deactivating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during user deactivation"
            )
    
    def get_user_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get user statistics."""
        try:
            user = user_repository.get(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get meeting statistics
            from app.repositories.meeting_repository import meeting_repository
            
            total_meetings = meeting_repository.count_by_owner(db, owner_id=user_id)
            analytics = meeting_repository.get_analytics(db, owner_id=user_id)
            
            return {
                'user_info': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.full_name,
                    'role': user.role.value,
                    'is_verified': user.is_verified,
                    'member_since': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                },
                'meeting_stats': {
                    'total_meetings': total_meetings,
                    'total_duration_hours': analytics.get('total_duration_hours', 0),
                    'avg_processing_time_seconds': analytics.get('avg_processing_time_seconds', 0),
                    'status_breakdown': analytics.get('status_breakdown', {}),
                    'recent_activity': analytics.get('recent_activity', [])
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting user stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error getting user statistics"
            )
    
    def check_user_permissions(
        self, 
        user: User, 
        required_role: UserRole = UserRole.USER
    ) -> bool:
        """Check if user has required permissions."""
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.USER: 2,
            UserRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def require_role(self, user: User, required_role: UserRole):
        """Require specific role or raise permission exception."""
        if not self.check_user_permissions(user, required_role):
            from app.core.security import permission_exception
            raise permission_exception


# Create global service instance
auth_service = AuthService()