"""
Meeting-related Pydantic schemas.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.meeting import ProcessingStatus, ASRProvider, LLMProvider


class MeetingBase(BaseModel):
    """Base meeting schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    context: Optional[str] = None
    tags: Optional[List[str]] = None


class MeetingCreate(MeetingBase):
    """Schema for creating a new meeting."""
    asr_provider: ASRProvider = ASRProvider.WHISPER_CPP
    asr_model: str = "small"
    llm_provider: LLMProvider = LLMProvider.OLLAMA
    llm_model: str = "llama2"


class MeetingUpdate(BaseModel):
    """Schema for updating meeting information."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    context: Optional[str] = None
    tags: Optional[List[str]] = None


class SpeakerSegment(BaseModel):
    """Schema for speaker segment information."""
    speaker_id: str
    speaker_label: Optional[str] = None
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float] = None


class ActionItem(BaseModel):
    """Schema for action item information."""
    id: str
    description: str
    owner: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "open"


class KeyDecision(BaseModel):
    """Schema for key decision information."""
    id: str
    description: str
    decision_maker: Optional[str] = None
    rationale: Optional[str] = None
    timestamp: Optional[datetime] = None


class Risk(BaseModel):
    """Schema for risk information."""
    id: str
    description: str
    impact: Optional[str] = "medium"
    probability: Optional[str] = "medium"
    mitigation: Optional[str] = None


class OpenQuestion(BaseModel):
    """Schema for open question information."""
    id: str
    question: str
    context: Optional[str] = None
    assigned_to: Optional[str] = None


class MeetingSummaries(BaseModel):
    """Schema for different types of meeting summaries."""
    executive_summary: Optional[str] = None
    detailed_summary: Optional[str] = None
    key_points: Optional[List[str]] = None


class MeetingProcessingConfig(BaseModel):
    """Schema for meeting processing configuration."""
    asr_provider: ASRProvider
    asr_model: str
    llm_provider: LLMProvider
    llm_model: str
    include_speaker_diarization: bool = True
    summary_types: List[str] = ["executive", "detailed", "key_points"]


class MeetingInDB(MeetingBase):
    """Schema for meeting data from database."""
    id: int
    original_filename: str
    file_path: str
    file_size: int
    duration: Optional[float] = None
    
    # Processing information
    asr_provider: ASRProvider
    asr_model: str
    llm_provider: LLMProvider
    llm_model: str
    status: ProcessingStatus
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Results
    transcript: Optional[str] = None
    confidence_score: Optional[float] = None
    language_detected: Optional[str] = None
    speaker_segments: Optional[List[Dict[str, Any]]] = None
    num_speakers: Optional[int] = None
    summaries: Optional[Dict[str, Any]] = None
    key_decisions: Optional[List[Dict[str, Any]]] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    risks: Optional[List[Dict[str, Any]]] = None
    open_questions: Optional[List[Dict[str, Any]]] = None
    keywords: Optional[List[str]] = None
    
    # Metadata
    owner_id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class Meeting(MeetingInDB):
    """Public meeting schema."""
    pass


class MeetingList(BaseModel):
    """Schema for paginated meeting list."""
    meetings: List[Meeting]
    total: int
    page: int
    per_page: int
    pages: int


class MeetingAnalytics(BaseModel):
    """Schema for meeting analytics."""
    total_meetings: int
    total_duration_hours: float
    avg_processing_time_seconds: float
    status_breakdown: Dict[str, int]
    provider_usage: Dict[str, Dict[str, int]]
    recent_activity: List[Dict[str, Any]]


class ExportFormat(BaseModel):
    """Schema for export format options."""
    format: str = Field(..., pattern="^(pdf|docx|markdown|json)$")
    include_transcript: bool = True
    include_summary: bool = True
    include_action_items: bool = True
    include_key_decisions: bool = True
    include_speaker_segments: bool = False


class MeetingSearch(BaseModel):
    """Schema for meeting search parameters."""
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[ProcessingStatus] = None
    asr_provider: Optional[ASRProvider] = None
    llm_provider: Optional[LLMProvider] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)