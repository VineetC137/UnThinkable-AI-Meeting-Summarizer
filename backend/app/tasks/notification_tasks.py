"""
Celery tasks for sending notifications (e.g., email summaries).
"""

import asyncio
from sqlalchemy.orm import Session
from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.repositories.meeting_repository import meeting_repository
from app.services.notification_service import notification_service

logger = get_logger(__name__)


def get_db_session() -> Session:
    """Get database session for Celery tasks."""
    return SessionLocal()


@celery_app.task(name="send_meeting_summary_email")
def send_meeting_summary_email_task(meeting_id: int, recipient_email: str):
    """
    Celery task to send a meeting summary email in the background.
    """
    db = get_db_session()
    try:
        logger.info(f"Starting Celery task to email summary of meeting {meeting_id} to {recipient_email}")
        meeting = meeting_repository.get(db, meeting_id)
        if not meeting:
            logger.error(f"Meeting {meeting_id} not found in database. Cannot email summary.")
            return False
            
        # Run async mail function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(
                notification_service.send_meeting_summary_email(meeting, recipient_email)
            )
            return success
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error executing email task for meeting {meeting_id}: {e}")
        raise e
    finally:
        db.close()
