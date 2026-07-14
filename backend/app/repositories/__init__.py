"""
Repository imports for easier access.
"""

from app.repositories.base_repository import BaseRepository
from app.repositories.user_repository import UserRepository, user_repository
from app.repositories.meeting_repository import MeetingRepository, meeting_repository

__all__ = [
    "BaseRepository",
    "UserRepository", 
    "user_repository",
    "MeetingRepository", 
    "meeting_repository"
]