"""
Celery tasks for meeting processing.
"""

import asyncio
from typing import List, Optional
from sqlalchemy.orm import Session
from celery import current_task

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.meeting_service import meeting_service
from app.repositories.meeting_repository import meeting_repository
from app.models.meeting import ProcessingStatus
from app.utils.prompt_templates import PromptTemplate

logger = get_logger(__name__)


def get_db_session() -> Session:
    """Get database session for Celery tasks."""
    return SessionLocal()


@celery_app.task(bind=True, name="process_meeting_full")
def process_meeting_full_task(
    self,
    meeting_id: int,
    include_speaker_diarization: bool = True,
    summary_types: Optional[List[str]] = None
):
    """
    Celery task for full meeting processing (transcription + summarization).
    """
    db = get_db_session()
    
    try:
        logger.info(f"Starting full processing task for meeting {meeting_id}")
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'starting', 'progress': 0}
        )
        
        # Convert summary types from strings to enums
        prompt_templates = None
        if summary_types:
            prompt_templates = []
            for summary_type in summary_types:
                try:
                    prompt_templates.append(PromptTemplate(summary_type))
                except ValueError:
                    logger.warning(f"Unknown summary type: {summary_type}")
        
        # Run the async processing function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                meeting_service.process_meeting_full_pipeline(
                    db=db,
                    meeting_id=meeting_id,
                    include_speaker_diarization=include_speaker_diarization,
                    summary_types=prompt_templates
                )
            )
            
            logger.info(f"Full processing completed for meeting {meeting_id}")
            
            return {
                'meeting_id': meeting_id,
                'status': 'completed',
                'result': {
                    'transcript_length': len(result.transcript or ''),
                    'confidence_score': result.confidence_score,
                    'num_speakers': result.num_speakers,
                    'has_summaries': bool(result.summaries),
                    'processing_time': (
                        result.processing_completed_at - result.processing_started_at
                    ).total_seconds() if result.processing_completed_at and result.processing_started_at else None
                }
            }
            
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Error in full processing task for meeting {meeting_id}: {e}")
        
        # Update meeting status to failed
        meeting_repository.update_status(
            db,
            meeting_id=meeting_id,
            status=ProcessingStatus.FAILED,
            error_message=str(e)
        )
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'meeting_id': meeting_id}
        )
        
        raise e
    
    finally:
        db.close()


@celery_app.task(bind=True, name="process_meeting_transcription")
def process_meeting_transcription_task(
    self,
    meeting_id: int,
    include_speaker_diarization: bool = False
):
    """
    Celery task for transcription-only processing.
    """
    db = get_db_session()
    
    try:
        logger.info(f"Starting transcription task for meeting {meeting_id}")
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'transcribing', 'progress': 0}
        )
        
        # Run the async processing function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                meeting_service.process_meeting_transcription_only(
                    db=db,
                    meeting_id=meeting_id,
                    include_speaker_diarization=include_speaker_diarization
                )
            )
            
            logger.info(f"Transcription completed for meeting {meeting_id}")
            
            return {
                'meeting_id': meeting_id,
                'status': 'completed',
                'result': {
                    'transcript_length': len(result.transcript or ''),
                    'confidence_score': result.confidence_score,
                    'language_detected': result.language_detected,
                    'num_speakers': result.num_speakers
                }
            }
            
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Error in transcription task for meeting {meeting_id}: {e}")
        
        # Update meeting status to failed
        meeting_repository.update_status(
            db,
            meeting_id=meeting_id,
            status=ProcessingStatus.FAILED,
            error_message=str(e)
        )
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'meeting_id': meeting_id}
        )
        
        raise e
    
    finally:
        db.close()


@celery_app.task(bind=True, name="reprocess_meeting_summaries")
def reprocess_meeting_summaries_task(
    self,
    meeting_id: int,
    summary_types: List[str],
    llm_provider: str,
    llm_model: str
):
    """
    Celery task for reprocessing meeting summaries with different models.
    """
    db = get_db_session()
    
    try:
        logger.info(f"Reprocessing summaries for meeting {meeting_id}")
        
        meeting = meeting_repository.get(db, meeting_id)
        if not meeting or not meeting.transcript:
            raise ValueError("Meeting not found or has no transcript")
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'summarizing', 'progress': 0}
        )
        
        # Convert summary types and providers
        from app.models.meeting import LLMProvider
        from app.services.summarization_service import summarization_service
        
        provider_enum = LLMProvider(llm_provider)
        prompt_templates = [PromptTemplate(st) for st in summary_types]
        
        # Run summarization
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            summaries_result = loop.run_until_complete(
                summarization_service.generate_structured_summaries(
                    transcript=meeting.transcript,
                    provider=provider_enum,
                    model_name=llm_model,
                    summary_types=prompt_templates,
                    context=meeting.context
                )
            )
            
            # Update meeting with new summaries
            meeting_repository.update_summaries(
                db,
                meeting_id=meeting_id,
                summaries={
                    'executive_summary': summaries_result.get('executive_summary'),
                    'detailed_summary': summaries_result.get('detailed_summary')
                },
                key_decisions=summaries_result.get('key_decisions', []),
                action_items=summaries_result.get('action_items', []),
                risks=summaries_result.get('risks', []),
                open_questions=summaries_result.get('open_questions', []),
                keywords=summaries_result.get('keywords', [])
            )
            
            logger.info(f"Summary reprocessing completed for meeting {meeting_id}")
            
            return {
                'meeting_id': meeting_id,
                'status': 'completed',
                'summary_types': summary_types,
                'provider': llm_provider,
                'model': llm_model
            }
            
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Error reprocessing summaries for meeting {meeting_id}: {e}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'meeting_id': meeting_id}
        )
        
        raise e
    
    finally:
        db.close()


@celery_app.task(name="cleanup_failed_meetings")
def cleanup_failed_meetings():
    """
    Periodic task to clean up failed meetings and temporary files.
    """
    db = get_db_session()
    
    try:
        logger.info("Starting cleanup of failed meetings")
        
        # Get meetings that have been in failed state for more than 24 hours
        from datetime import datetime, timedelta
        
        failed_meetings = meeting_repository.get_by_status(
            db, 
            status=ProcessingStatus.FAILED,
            limit=100
        )
        
        cleanup_count = 0
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        for meeting in failed_meetings:
            if meeting.updated_at < cutoff_time:
                # Optionally clean up files or reset status
                # For now, just log the failed meetings
                logger.warning(
                    f"Meeting {meeting.id} has been failed for over 24 hours: {meeting.error_message}"
                )
                cleanup_count += 1
        
        logger.info(f"Cleanup completed. Found {cleanup_count} long-failed meetings")
        
        return {
            'status': 'completed',
            'failed_meetings_found': cleanup_count,
            'cleanup_time': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        raise e
    
    finally:
        db.close()


@celery_app.task(name="generate_system_analytics")
def generate_system_analytics():
    """
    Periodic task to generate and cache system analytics.
    """
    db = get_db_session()
    
    try:
        logger.info("Generating system analytics")
        
        # Get overall system analytics
        analytics = meeting_repository.get_analytics(db)
        
        # Log key metrics
        logger.info(
            f"System metrics - Total meetings: {analytics.get('total_meetings', 0)}, "
            f"Total hours: {analytics.get('total_duration_hours', 0):.2f}, "
            f"Avg processing time: {analytics.get('avg_processing_time_seconds', 0):.2f}s"
        )
        
        return {
            'status': 'completed',
            'analytics': analytics,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        raise e
    
    finally:
        db.close()


@celery_app.task(bind=True, name="batch_process_meetings")
def batch_process_meetings_task(
    self,
    meeting_ids: List[int],
    processing_config: dict
):
    """
    Celery task for batch processing multiple meetings.
    """
    db = get_db_session()
    
    try:
        total_meetings = len(meeting_ids)
        completed_meetings = []
        failed_meetings = []
        
        logger.info(f"Starting batch processing for {total_meetings} meetings")
        
        for i, meeting_id in enumerate(meeting_ids):
            try:
                # Update progress
                progress = int((i / total_meetings) * 100)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': total_meetings,
                        'progress': progress,
                        'processing_meeting_id': meeting_id
                    }
                )
                
                # Process individual meeting
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(
                        meeting_service.process_meeting_full_pipeline(
                            db=db,
                            meeting_id=meeting_id,
                            include_speaker_diarization=processing_config.get('include_speaker_diarization', True)
                        )
                    )
                    
                    completed_meetings.append({
                        'meeting_id': meeting_id,
                        'status': 'completed',
                        'transcript_length': len(result.transcript or '')
                    })
                    
                finally:
                    loop.close()
                
            except Exception as e:
                logger.error(f"Failed to process meeting {meeting_id} in batch: {e}")
                failed_meetings.append({
                    'meeting_id': meeting_id,
                    'error': str(e)
                })
        
        logger.info(
            f"Batch processing completed. "
            f"Successful: {len(completed_meetings)}, Failed: {len(failed_meetings)}"
        )
        
        return {
            'status': 'completed',
            'total_meetings': total_meetings,
            'completed': completed_meetings,
            'failed': failed_meetings,
            'success_rate': len(completed_meetings) / total_meetings * 100
        }
    
    except Exception as e:
        logger.error(f"Error in batch processing task: {e}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        
        raise e
    
    finally:
        db.close()