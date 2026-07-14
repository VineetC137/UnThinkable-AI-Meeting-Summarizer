"""
Meeting repository for meeting-specific database operations.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from datetime import datetime
from app.models.meeting import Meeting, ProcessingStatus
from app.schemas.meeting import MeetingCreate, MeetingUpdate
from app.repositories.base_repository import BaseRepository


class MeetingRepository(BaseRepository[Meeting, MeetingCreate, MeetingUpdate]):
    """
    Repository for Meeting model with specific meeting operations.
    """
    
    def __init__(self):
        super().__init__(Meeting)
    
    def get_by_owner(
        self, 
        db: Session, 
        *, 
        owner_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Meeting]:
        """Get meetings by owner with pagination."""
        return db.query(Meeting).filter(
            Meeting.owner_id == owner_id,
            Meeting.is_active == True
        ).order_by(Meeting.created_at.desc()).offset(skip).limit(limit).all()
    
    def count_by_owner(self, db: Session, *, owner_id: int) -> int:
        """Count meetings by owner."""
        return db.query(Meeting).filter(
            Meeting.owner_id == owner_id,
            Meeting.is_active == True
        ).count()
    
    def search(
        self, 
        db: Session, 
        *,
        query: Optional[str] = None,
        owner_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        status: Optional[ProcessingStatus] = None,
        asr_provider: Optional[str] = None,
        llm_provider: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """Search meetings with multiple filters."""
        db_query = db.query(Meeting).filter(Meeting.is_active == True)
        
        # Filter by owner
        if owner_id:
            db_query = db_query.filter(Meeting.owner_id == owner_id)
        
        # Text search in title, description, and transcript
        if query:
            search_filter = or_(
                Meeting.title.ilike(f"%{query}%"),
                Meeting.description.ilike(f"%{query}%"),
                Meeting.transcript.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_filter)
        
        # Filter by tags (if any of the provided tags match)
        if tags:
            tag_filters = []
            for tag in tags:
                tag_filters.append(Meeting.tags.op('@>')([tag]))
            if tag_filters:
                db_query = db_query.filter(or_(*tag_filters))
        
        # Filter by status
        if status:
            db_query = db_query.filter(Meeting.status == status)
        
        # Filter by ASR provider
        if asr_provider:
            db_query = db_query.filter(Meeting.asr_provider == asr_provider)
        
        # Filter by LLM provider
        if llm_provider:
            db_query = db_query.filter(Meeting.llm_provider == llm_provider)
        
        # Filter by date range
        if date_from:
            db_query = db_query.filter(Meeting.created_at >= date_from)
        if date_to:
            db_query = db_query.filter(Meeting.created_at <= date_to)
        
        return db_query.order_by(Meeting.created_at.desc()).offset(skip).limit(limit).all()
    
    def count_search(
        self, 
        db: Session, 
        *,
        query: Optional[str] = None,
        owner_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        status: Optional[ProcessingStatus] = None,
        asr_provider: Optional[str] = None,
        llm_provider: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> int:
        """Count search results with multiple filters."""
        db_query = db.query(Meeting).filter(Meeting.is_active == True)
        
        # Apply same filters as search method
        if owner_id:
            db_query = db_query.filter(Meeting.owner_id == owner_id)
        
        if query:
            search_filter = or_(
                Meeting.title.ilike(f"%{query}%"),
                Meeting.description.ilike(f"%{query}%"),
                Meeting.transcript.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_filter)
        
        if tags:
            tag_filters = []
            for tag in tags:
                tag_filters.append(Meeting.tags.op('@>')([tag]))
            if tag_filters:
                db_query = db_query.filter(or_(*tag_filters))
        
        if status:
            db_query = db_query.filter(Meeting.status == status)
        
        if asr_provider:
            db_query = db_query.filter(Meeting.asr_provider == asr_provider)
        
        if llm_provider:
            db_query = db_query.filter(Meeting.llm_provider == llm_provider)
        
        if date_from:
            db_query = db_query.filter(Meeting.created_at >= date_from)
        if date_to:
            db_query = db_query.filter(Meeting.created_at <= date_to)
        
        return db_query.count()
    
    def get_by_status(
        self, 
        db: Session, 
        *, 
        status: ProcessingStatus,
        limit: int = 100
    ) -> List[Meeting]:
        """Get meetings by processing status."""
        return db.query(Meeting).filter(
            Meeting.status == status,
            Meeting.is_active == True
        ).order_by(Meeting.created_at).limit(limit).all()
    
    def update_status(
        self, 
        db: Session, 
        *, 
        meeting_id: int, 
        status: ProcessingStatus,
        error_message: Optional[str] = None
    ) -> Optional[Meeting]:
        """Update meeting processing status."""
        meeting = self.get(db, meeting_id)
        if meeting:
            meeting.status = status
            if error_message:
                meeting.error_message = error_message
            
            # Set timestamps based on status
            if status == ProcessingStatus.TRANSCRIBING:
                meeting.processing_started_at = datetime.utcnow()
            elif status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                meeting.processing_completed_at = datetime.utcnow()
            
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
        return meeting
    
    def update_transcript(
        self, 
        db: Session, 
        *, 
        meeting_id: int, 
        transcript: str,
        confidence_score: Optional[float] = None,
        language_detected: Optional[str] = None,
        speaker_segments: Optional[List[Dict]] = None,
        num_speakers: Optional[int] = None
    ) -> Optional[Meeting]:
        """Update meeting transcript and related data."""
        meeting = self.get(db, meeting_id)
        if meeting:
            meeting.transcript = transcript
            meeting.confidence_score = confidence_score
            meeting.language_detected = language_detected
            meeting.speaker_segments = speaker_segments
            meeting.num_speakers = num_speakers
            
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
        return meeting
    
    def update_summaries(
        self, 
        db: Session, 
        *, 
        meeting_id: int, 
        summaries: Optional[Dict] = None,
        key_decisions: Optional[List[Dict]] = None,
        action_items: Optional[List[Dict]] = None,
        risks: Optional[List[Dict]] = None,
        open_questions: Optional[List[Dict]] = None,
        keywords: Optional[List[str]] = None
    ) -> Optional[Meeting]:
        """Update meeting summaries and analysis."""
        meeting = self.get(db, meeting_id)
        if meeting:
            if summaries is not None:
                meeting.summaries = summaries
            if key_decisions is not None:
                meeting.key_decisions = key_decisions
            if action_items is not None:
                meeting.action_items = action_items
            if risks is not None:
                meeting.risks = risks
            if open_questions is not None:
                meeting.open_questions = open_questions
            if keywords is not None:
                meeting.keywords = keywords
            
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
        return meeting
    
    def get_analytics(self, db: Session, *, owner_id: Optional[int] = None) -> Dict[str, Any]:
        """Get meeting analytics."""
        base_query = db.query(Meeting).filter(Meeting.is_active == True)
        
        if owner_id:
            base_query = base_query.filter(Meeting.owner_id == owner_id)
        
        # Total meetings
        total_meetings = base_query.count()
        
        # Total duration
        total_duration = base_query.with_entities(func.sum(Meeting.duration)).scalar() or 0
        
        # Average processing time for completed meetings
        completed_meetings = base_query.filter(
            Meeting.status == ProcessingStatus.COMPLETED,
            Meeting.processing_started_at.isnot(None),
            Meeting.processing_completed_at.isnot(None)
        )
        
        avg_processing_time = 0
        if completed_meetings.count() > 0:
            processing_times = []
            for meeting in completed_meetings:
                if meeting.processing_started_at and meeting.processing_completed_at:
                    diff = meeting.processing_completed_at - meeting.processing_started_at
                    processing_times.append(diff.total_seconds())
            
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)
        
        # Status breakdown
        status_breakdown = {}
        for status in ProcessingStatus:
            count = base_query.filter(Meeting.status == status).count()
            status_breakdown[status.value] = count
        
        # Provider usage
        asr_providers = db.query(Meeting.asr_provider, func.count(Meeting.id)).filter(
            Meeting.is_active == True
        ).group_by(Meeting.asr_provider).all()
        
        llm_providers = db.query(Meeting.llm_provider, func.count(Meeting.id)).filter(
            Meeting.is_active == True
        ).group_by(Meeting.llm_provider).all()
        
        provider_usage = {
            "asr": {str(provider): count for provider, count in asr_providers},
            "llm": {str(provider): count for provider, count in llm_providers}
        }
        
        # Recent activity (last 10 meetings)
        recent_meetings = base_query.order_by(Meeting.created_at.desc()).limit(10).all()
        recent_activity = []
        for meeting in recent_meetings:
            recent_activity.append({
                "id": meeting.id,
                "title": meeting.title,
                "status": meeting.status.value,
                "created_at": meeting.created_at.isoformat(),
                "duration": meeting.duration
            })
        
        return {
            "total_meetings": total_meetings,
            "total_duration_hours": total_duration / 3600 if total_duration else 0,
            "avg_processing_time_seconds": avg_processing_time,
            "status_breakdown": status_breakdown,
            "provider_usage": provider_usage,
            "recent_activity": recent_activity
        }


# Create repository instance
meeting_repository = MeetingRepository()