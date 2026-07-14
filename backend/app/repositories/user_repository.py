"""
User repository for user-specific database operations.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserCreate, UserUpdate
from app.repositories.base_repository import BaseRepository
from app.core.security import create_password_hash


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Repository for User model with specific user operations.
    """
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(
            User.email == email,
            User.is_active == True
        ).first()
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(
            User.username == username,
            User.is_active == True
        ).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create a new user with hashed password."""
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            full_name=obj_in.full_name,
            hashed_password=create_password_hash(obj_in.password),
            role=obj_in.role
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        """Update user with optional password hashing."""
        update_data = obj_in.dict(exclude_unset=True)
        
        # Hash password if provided
        if "password" in update_data:
            update_data["hashed_password"] = create_password_hash(update_data["password"])
            del update_data["password"]
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def verify_user(self, db: Session, *, user_id: int) -> Optional[User]:
        """Mark user as verified."""
        user = self.get(db, user_id)
        if user:
            user.is_verified = True
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        from app.core.security import verify_password
        
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def update_last_login(self, db: Session, *, user_id: int) -> Optional[User]:
        """Update user's last login timestamp."""
        from datetime import datetime
        
        user = self.get(db, user_id)
        if user:
            user.last_login = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    def is_email_taken(self, db: Session, *, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if email is already taken by another user."""
        query = db.query(User).filter(User.email == email, User.is_active == True)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None
    
    def is_username_taken(self, db: Session, *, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if username is already taken by another user."""
        query = db.query(User).filter(User.username == username, User.is_active == True)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None


# Create repository instance
user_repository = UserRepository()