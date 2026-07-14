"""
Schema imports for easier access.
"""

from app.schemas.auth import (
    UserBase, UserCreate, UserUpdate, UserInDB, User, UserLogin,
    Token, TokenData, RefreshToken, PasswordReset, PasswordResetConfirm
)
from app.schemas.meeting import (
    MeetingBase, MeetingCreate, MeetingUpdate, MeetingInDB, Meeting,
    MeetingList, MeetingAnalytics, ExportFormat, MeetingSearch,
    SpeakerSegment, ActionItem, KeyDecision, Risk, OpenQuestion,
    MeetingSummaries, MeetingProcessingConfig
)

__all__ = [
    # Auth schemas
    "UserBase", "UserCreate", "UserUpdate", "UserInDB", "User", "UserLogin",
    "Token", "TokenData", "RefreshToken", "PasswordReset", "PasswordResetConfirm",
    
    # Meeting schemas
    "MeetingBase", "MeetingCreate", "MeetingUpdate", "MeetingInDB", "Meeting",
    "MeetingList", "MeetingAnalytics", "ExportFormat", "MeetingSearch",
    "SpeakerSegment", "ActionItem", "KeyDecision", "Risk", "OpenQuestion",
    "MeetingSummaries", "MeetingProcessingConfig"
]