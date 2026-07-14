"""
Main meeting service that orchestrates transcription, summarization, and speaker diarization.
"""

import os
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import shutil

from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import get_logger
from app.models.meeting import Meeting, ProcessingStatus, ASRProvider, LLMProvider
from app.schemas.meeting import MeetingCreate, MeetingProcessingConfig
from app.repositories.meeting_repository import meeting_repository
from app.services.transcription_service import transcription_service
from app.services.summarization_service import summarization_service
from app.services.speaker_diarization_service import speaker_diarization_service
from app.utils.prompt_templates import PromptTemplate
from app.utils.audio_processor import audio_processor

logger = get_logger(__name__)


class MeetingService:
    """
    Main service for meeting processing workflow.
    """
    
    def __init__(self):
        self.logger = logger
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    def save_uploaded_file(self, file_content: bytes, filename: str, user_id: int) -> str:
        """Save uploaded audio file and return the file path."""
        try:
            # Generate unique filename to avoid conflicts
            file_extension = Path(filename).suffix
            unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
            file_path = self.upload_dir / unique_filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            self.logger.info(f"File saved: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Error saving uploaded file: {e}")
            raise
    
    def create_meeting(
        self, 
        db: Session, 
        meeting_data: MeetingCreate,
        file_content: bytes,
        filename: str,
        user_id: int
    ) -> Meeting:
        """Create a new meeting record with uploaded file."""
        try:
            # Save the uploaded file
            file_path = self.save_uploaded_file(file_content, filename, user_id)
            
            # Get file size and audio info
            file_size = os.path.getsize(file_path)
            audio_info = audio_processor.get_audio_info(file_path)
            
            # Create meeting record
            meeting = Meeting(
                title=meeting_data.title,
                description=meeting_data.description,
                context=meeting_data.context,
                tags=meeting_data.tags or [],
                original_filename=filename,
                file_path=file_path,
                file_size=file_size,
                duration=audio_info.get('duration'),
                asr_provider=meeting_data.asr_provider,
                asr_model=meeting_data.asr_model,
                llm_provider=meeting_data.llm_provider,
                llm_model=meeting_data.llm_model,
                status=ProcessingStatus.PENDING,
                owner_id=user_id
            )
            
            # Save to database
            created_meeting = meeting_repository.create(db, obj_in=meeting)
            
            self.logger.info(f"Meeting created: {created_meeting.id}")
            return created_meeting
            
        except Exception as e:
            self.logger.error(f"Error creating meeting: {e}")
            raise
    
    async def process_meeting_full_pipeline(
        self, 
        db: Session, 
        meeting_id: int,
        include_speaker_diarization: bool = True,
        summary_types: Optional[List[PromptTemplate]] = None
    ) -> Meeting:
        """
        Process meeting through the complete AI pipeline:
        1. Transcription
        2. Speaker diarization (optional)
        3. Summarization
        """
        try:
            # Get meeting record
            meeting = meeting_repository.get(db, meeting_id)
            if not meeting:
                raise ValueError(f"Meeting {meeting_id} not found")
            
            self.logger.info(f"Starting full pipeline processing for meeting {meeting_id}")
            
            # Update status to transcribing
            meeting_repository.update_status(
                db, 
                meeting_id=meeting_id, 
                status=ProcessingStatus.TRANSCRIBING
            )
            
            # Step 1: Transcription
            transcription_result = await transcription_service.transcribe(
                audio_path=meeting.file_path,
                provider=meeting.asr_provider,
                model_name=meeting.asr_model,
                language=None  # Auto-detect
            )
            
            transcript = transcription_result['transcript']
            confidence = transcription_result.get('confidence', 0.0)
            language = transcription_result.get('language', 'auto')
            transcript_segments = transcription_result.get('segments', [])
            
            # Update meeting with transcript
            meeting_repository.update_transcript(
                db,
                meeting_id=meeting_id,
                transcript=transcript,
                confidence_score=confidence,
                language_detected=language
            )
            
            self.logger.info(f"Transcription completed for meeting {meeting_id}")
            
            # Step 2: Speaker Diarization (if requested and available)
            speaker_segments = None
            num_speakers = None
            
            if include_speaker_diarization and speaker_diarization_service.is_available():
                try:
                    self.logger.info(f"Starting speaker diarization for meeting {meeting_id}")
                    
                    if transcript_segments:
                        # Align with transcript segments
                        diarization_result = await speaker_diarization_service.diarize_and_align_with_transcript(
                            audio_path=meeting.file_path,
                            transcript_segments=transcript_segments
                        )
                        
                        if diarization_result['success']:
                            speaker_segments = diarization_result['aligned_segments']
                            num_speakers = diarization_result['num_speakers']
                            
                            # Update transcript with speaker information
                            transcript_with_speakers = speaker_diarization_service.format_transcript_with_speakers(
                                diarization_result['aligned_segments'],
                                include_timestamps=False
                            )
                            
                            if transcript_with_speakers:
                                transcript = transcript_with_speakers
                    else:
                        # Basic diarization without transcript alignment
                        diarization_result = await speaker_diarization_service.diarize_audio(
                            meeting.file_path
                        )
                        
                        if diarization_result['success']:
                            speaker_segments = diarization_result['segments']
                            num_speakers = diarization_result['num_speakers']
                    
                    self.logger.info(f"Speaker diarization completed for meeting {meeting_id}")
                    
                except Exception as e:
                    self.logger.warning(f"Speaker diarization failed for meeting {meeting_id}: {e}")
                    # Continue without speaker diarization
            
            # Update meeting with speaker information
            if speaker_segments:
                meeting_repository.update_transcript(
                    db,
                    meeting_id=meeting_id,
                    transcript=transcript,
                    confidence_score=confidence,
                    language_detected=language,
                    speaker_segments=speaker_segments,
                    num_speakers=num_speakers
                )
            
            # Step 3: Summarization
            meeting_repository.update_status(
                db,
                meeting_id=meeting_id,
                status=ProcessingStatus.SUMMARIZING
            )
            
            # Define default summary types if not provided
            if not summary_types:
                summary_types = [
                    PromptTemplate.EXECUTIVE_SUMMARY,
                    PromptTemplate.DETAILED_SUMMARY,
                    PromptTemplate.KEY_DECISIONS,
                    PromptTemplate.ACTION_ITEMS,
                    PromptTemplate.RISKS,
                    PromptTemplate.OPEN_QUESTIONS,
                    PromptTemplate.KEYWORDS
                ]
            
            # Generate comprehensive analysis
            self.logger.info(f"Starting summarization for meeting {meeting_id}")
            
            summaries_result = await summarization_service.generate_comprehensive_analysis(
                transcript=transcript,
                provider=meeting.llm_provider,
                model_name=meeting.llm_model,
                context=meeting.context
            )
            
            # Extract structured data from summaries
            summaries = {
                'executive_summary': summaries_result.get('executive_summary'),
                'detailed_summary': summaries_result.get('detailed_summary')
            }
            
            key_decisions = summaries_result.get('key_decisions', [])
            action_items = summaries_result.get('action_items', [])
            risks = summaries_result.get('risks', [])
            open_questions = summaries_result.get('open_questions', [])
            keywords = summaries_result.get('keywords', [])
            
            # Update meeting with summaries
            meeting_repository.update_summaries(
                db,
                meeting_id=meeting_id,
                summaries=summaries,
                key_decisions=key_decisions,
                action_items=action_items,
                risks=risks,
                open_questions=open_questions,
                keywords=keywords
            )
            
            # Mark as completed
            meeting_repository.update_status(
                db,
                meeting_id=meeting_id,
                status=ProcessingStatus.COMPLETED
            )
            
            self.logger.info(f"Full pipeline processing completed for meeting {meeting_id}")
            
            # Return updated meeting
            return meeting_repository.get(db, meeting_id)
            
        except Exception as e:
            self.logger.error(f"Error processing meeting {meeting_id}: {e}")
            
            # Mark as failed
            meeting_repository.update_status(
                db,
                meeting_id=meeting_id,
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
            
            raise
    
    async def process_meeting_transcription_only(
        self, 
        db: Session, 
        meeting_id: int,
        include_speaker_diarization: bool = False
    ) -> Meeting:
        """Process meeting for transcription only."""
        try:
            meeting = meeting_repository.get(db, meeting_id)
            if not meeting:
                raise ValueError(f"Meeting {meeting_id} not found")
            
            self.logger.info(f"Starting transcription-only processing for meeting {meeting_id}")
            
            # Update status
            meeting_repository.update_status(
                db, 
                meeting_id=meeting_id, 
                status=ProcessingStatus.TRANSCRIBING
            )
            
            # Transcribe
            transcription_result = await transcription_service.transcribe(
                audio_path=meeting.file_path,
                provider=meeting.asr_provider,
                model_name=meeting.asr_model,
                language=None
            )
            
            transcript = transcription_result['transcript']
            
            # Speaker diarization if requested
            if include_speaker_diarization and speaker_diarization_service.is_available():
                try:
                    transcript_segments = transcription_result.get('segments', [])
                    if transcript_segments:
                        diarization_result = await speaker_diarization_service.diarize_and_align_with_transcript(
                            audio_path=meeting.file_path,
                            transcript_segments=transcript_segments
                        )
                        
                        if diarization_result['success']:
                            transcript_with_speakers = speaker_diarization_service.format_transcript_with_speakers(
                                diarization_result['aligned_segments']
                            )
                            if transcript_with_speakers:
                                transcript = transcript_with_speakers
                except Exception as e:
                    self.logger.warning(f"Speaker diarization failed: {e}")
            
            # Update meeting
            meeting_repository.update_transcript(
                db,
                meeting_id=meeting_id,
                transcript=transcript,
                confidence_score=transcription_result.get('confidence', 0.0),
                language_detected=transcription_result.get('language', 'auto')
            )
            
            # Mark as completed
            meeting_repository.update_status(
                db,
                meeting_id=meeting_id,
                status=ProcessingStatus.COMPLETED
            )
            
            return meeting_repository.get(db, meeting_id)
            
        except Exception as e:
            self.logger.error(f"Error in transcription-only processing: {e}")
            meeting_repository.update_status(
                db,
                meeting_id=meeting_id,
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
            raise
    
    def delete_meeting(self, db: Session, meeting_id: int, user_id: int) -> bool:
        """Delete a meeting and its associated files."""
        try:
            meeting = meeting_repository.get(db, meeting_id)
            if not meeting:
                return False
            
            # Check ownership
            if meeting.owner_id != user_id:
                raise PermissionError("Not authorized to delete this meeting")
            
            # Delete physical file
            if os.path.exists(meeting.file_path):
                os.remove(meeting.file_path)
                self.logger.info(f"Deleted file: {meeting.file_path}")
            
            # Soft delete from database
            meeting_repository.delete(db, id=meeting_id)
            
            self.logger.info(f"Meeting {meeting_id} deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting meeting {meeting_id}: {e}")
            raise
    
    def get_processing_status(self, db: Session, meeting_id: int) -> Dict[str, Any]:
        """Get detailed processing status for a meeting."""
        try:
            meeting = meeting_repository.get(db, meeting_id)
            if not meeting:
                raise ValueError(f"Meeting {meeting_id} not found")
            
            # Calculate processing time
            processing_time = None
            if meeting.processing_started_at and meeting.processing_completed_at:
                diff = meeting.processing_completed_at - meeting.processing_started_at
                processing_time = diff.total_seconds()
            
            return {
                'meeting_id': meeting.id,
                'status': meeting.status.value,
                'processing_started_at': meeting.processing_started_at.isoformat() if meeting.processing_started_at else None,
                'processing_completed_at': meeting.processing_completed_at.isoformat() if meeting.processing_completed_at else None,
                'processing_time_seconds': processing_time,
                'error_message': meeting.error_message,
                'has_transcript': bool(meeting.transcript),
                'has_speaker_segments': bool(meeting.speaker_segments),
                'has_summaries': bool(meeting.summaries),
                'confidence_score': meeting.confidence_score,
                'language_detected': meeting.language_detected,
                'num_speakers': meeting.num_speakers
            }
            
        except Exception as e:
            self.logger.error(f"Error getting processing status for meeting {meeting_id}: {e}")
            raise
    
    def get_ai_provider_status(self) -> Dict[str, Any]:
        """Get status of all AI providers."""
        try:
            return {
                'transcription_providers': transcription_service.get_provider_info(),
                'summarization_providers': summarization_service.get_provider_info(),
                'speaker_diarization_available': speaker_diarization_service.is_available()
            }
        except Exception as e:
            self.logger.error(f"Error getting AI provider status: {e}")
            return {}


# Create global service instance
meeting_service = MeetingService()