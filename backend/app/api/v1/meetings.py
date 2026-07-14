"""
Meeting management API endpoints.
"""

import os
from typing import List, Optional
from fastapi import (
    APIRouter, Depends, HTTPException, status, UploadFile, File, 
    Form, BackgroundTasks, Response, Query
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.core.database import get_db
from app.core.config import settings
from app.schemas.meeting import (
    Meeting, MeetingCreate, MeetingUpdate, MeetingList, 
    MeetingAnalytics, ExportFormat, MeetingSearch
)
from app.models.meeting import ProcessingStatus, ASRProvider, LLMProvider
from app.models.user import User as UserModel
from app.services.meeting_service import meeting_service
from app.services.export_service import export_service
from app.repositories.meeting_repository import meeting_repository
from app.api.dependencies import get_current_active_user, CommonQueryParams
from app.utils.prompt_templates import PromptTemplate
from app.tasks.meeting_tasks import process_meeting_full_task, process_meeting_transcription_task

router = APIRouter()


@router.post("/", response_model=Meeting, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string of tags
    asr_provider: ASRProvider = Form(ASRProvider.WHISPER_CPP),
    asr_model: str = Form("small"),
    llm_provider: LLMProvider = Form(LLMProvider.OLLAMA),
    llm_model: str = Form("llama2"),
    audio_file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new meeting with audio file upload.
    """
    # Validate file size
    if audio_file.size and audio_file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Validate file format
    file_extension = os.path.splitext(audio_file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Allowed formats: {settings.ALLOWED_AUDIO_FORMATS}"
        )
    
    # Parse tags
    import json
    parsed_tags = []
    if tags:
        try:
            parsed_tags = json.loads(tags)
        except json.JSONDecodeError:
            parsed_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    # Create meeting data object
    meeting_data = MeetingCreate(
        title=title,
        description=description,
        context=context,
        tags=parsed_tags,
        asr_provider=asr_provider,
        asr_model=asr_model,
        llm_provider=llm_provider,
        llm_model=llm_model
    )
    
    # Read file content
    file_content = await audio_file.read()
    
    # Create meeting
    meeting = meeting_service.create_meeting(
        db=db,
        meeting_data=meeting_data,
        file_content=file_content,
        filename=audio_file.filename,
        user_id=current_user.id
    )
    
    return Meeting.model_validate(meeting)


@router.post("/{meeting_id}/process")
async def process_meeting(
    meeting_id: int,
    include_speaker_diarization: bool = Query(True),
    transcription_only: bool = Query(False),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start processing meeting audio (transcription and summarization).
    """
    # Get meeting and verify ownership
    meeting = meeting_repository.get(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if meeting.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to process this meeting"
        )
    
    if meeting.status != ProcessingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Meeting is already {meeting.status.value}"
        )
    
    # Add processing task to Celery
    if transcription_only:
        process_meeting_transcription_task.delay(
            meeting_id, include_speaker_diarization
        )
    else:
        process_meeting_full_task.delay(
            meeting_id, include_speaker_diarization
        )
    
    return {"message": "Meeting processing started", "meeting_id": meeting_id}


@router.get("/", response_model=MeetingList)
def get_meetings(
    pagination: CommonQueryParams = Depends(CommonQueryParams),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's meetings with pagination.
    """
    meetings = meeting_repository.get_by_owner(
        db,
        owner_id=current_user.id,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    total = meeting_repository.count_by_owner(db, owner_id=current_user.id)
    
    return MeetingList(
        meetings=[Meeting.model_validate(meeting) for meeting in meetings],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=(total + pagination.per_page - 1) // pagination.per_page
    )


@router.post("/search", response_model=MeetingList)
def search_meetings(
    search_params: MeetingSearch,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search meetings with filters.
    """
    meetings = meeting_repository.search(
        db,
        query=search_params.query,
        owner_id=current_user.id,
        tags=search_params.tags,
        status=search_params.status,
        asr_provider=search_params.asr_provider,
        llm_provider=search_params.llm_provider,
        date_from=search_params.date_from,
        date_to=search_params.date_to,
        skip=(search_params.page - 1) * search_params.per_page,
        limit=search_params.per_page
    )
    
    total = meeting_repository.count_search(
        db,
        query=search_params.query,
        owner_id=current_user.id,
        tags=search_params.tags,
        status=search_params.status,
        asr_provider=search_params.asr_provider,
        llm_provider=search_params.llm_provider,
        date_from=search_params.date_from,
        date_to=search_params.date_to
    )
    
    return MeetingList(
        meetings=[Meeting.model_validate(meeting) for meeting in meetings],
        total=total,
        page=search_params.page,
        per_page=search_params.per_page,
        pages=(total + search_params.per_page - 1) // search_params.per_page
    )


@router.get("/{meeting_id}", response_model=Meeting)
def get_meeting(
    meeting_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get specific meeting details.
    """
    meeting = meeting_repository.get(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if meeting.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this meeting"
        )
    
    return Meeting.model_validate(meeting)


@router.put("/{meeting_id}", response_model=Meeting)
def update_meeting(
    meeting_id: int,
    update_data: MeetingUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update meeting information (metadata only).
    """
    meeting = meeting_repository.get(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if meeting.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this meeting"
        )
    
    updated_meeting = meeting_repository.update(
        db, 
        db_obj=meeting, 
        obj_in=update_data
    )
    
    return Meeting.model_validate(updated_meeting)


@router.delete("/{meeting_id}")
def delete_meeting(
    meeting_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete meeting and associated files.
    """
    success = meeting_service.delete_meeting(db, meeting_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    return {"message": "Meeting deleted successfully"}


@router.get("/{meeting_id}/status")
def get_processing_status(
    meeting_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get meeting processing status.
    """
    meeting = meeting_repository.get(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if meeting.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this meeting"
        )
    
    status_info = meeting_service.get_processing_status(db, meeting_id)
    return status_info


@router.post("/{meeting_id}/export")
def export_meeting(
    meeting_id: int,
    export_options: ExportFormat,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export meeting in specified format.
    """
    meeting = meeting_repository.get(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if meeting.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export this meeting"
        )
    
    if meeting.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting processing not completed"
        )
    
    # Generate export
    content, content_type = export_service.export_meeting(
        meeting=meeting,
        format_type=export_options.format,
        include_transcript=export_options.include_transcript,
        include_summary=export_options.include_summary,
        include_action_items=export_options.include_action_items,
        include_key_decisions=export_options.include_key_decisions,
        include_speaker_segments=export_options.include_speaker_segments
    )
    
    # Generate filename
    safe_title = "".join(c for c in meeting.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_title}_{meeting_id}.{export_options.format}"
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/{meeting_id}/email")
async def email_meeting_summary(
    meeting_id: int,
    email: Optional[str] = Query(None, description="Recipient email address. Defaults to current user's email."),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Email the meeting summary to the specified email address or current user's email.
    """
    meeting = meeting_repository.get(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if meeting.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to email this meeting"
        )
        
    if meeting.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting processing not completed yet"
        )
        
    recipient = email or current_user.email
    
    # Trigger Celery task
    from app.tasks.notification_tasks import send_meeting_summary_email_task
    send_meeting_summary_email_task.delay(meeting_id, recipient)
    
    return {"message": f"Email task queued to be sent to {recipient}"}


@router.get("/analytics/overview", response_model=MeetingAnalytics)
def get_analytics(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's meeting analytics.
    """
    analytics = meeting_repository.get_analytics(db, owner_id=current_user.id)
    return MeetingAnalytics(**analytics)


# Admin endpoints (for future implementation)
@router.get("/admin/all", response_model=MeetingList)
def get_all_meetings_admin(
    pagination: CommonQueryParams = Depends(CommonQueryParams),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to get all meetings.
    """
    from app.services.auth_service import auth_service
    from app.models.user import UserRole
    
    auth_service.require_role(current_user, UserRole.ADMIN)
    
    meetings = meeting_repository.get_multi(
        db,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    total = meeting_repository.count(db)
    
    return MeetingList(
        meetings=[Meeting.model_validate(meeting) for meeting in meetings],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=(total + pagination.per_page - 1) // pagination.per_page
    )