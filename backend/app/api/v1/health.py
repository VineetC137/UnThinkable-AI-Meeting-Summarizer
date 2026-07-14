"""
Health check and system status API endpoints.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.services.meeting_service import meeting_service
from app.services.transcription_service import transcription_service
from app.services.summarization_service import summarization_service
from app.services.speaker_diarization_service import speaker_diarization_service

router = APIRouter()


@router.get("/")
def health_check():
    """
    Basic health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "Meeting Summarizer API",
        "version": settings.APP_VERSION
    }


@router.get("/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with system status.
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Get AI provider status
    ai_status = meeting_service.get_ai_provider_status()
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "Meeting Summarizer API",
        "version": settings.APP_VERSION,
        "components": {
            "database": db_status,
            "ai_providers": ai_status
        },
        "config": {
            "upload_dir": settings.UPLOAD_DIR,
            "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
            "allowed_formats": settings.ALLOWED_AUDIO_FORMATS,
            "cors_origins": settings.BACKEND_CORS_ORIGINS
        }
    }


@router.get("/providers")
def get_provider_status():
    """
    Get AI provider availability and configuration.
    """
    return {
        "transcription": transcription_service.get_provider_info(),
        "summarization": summarization_service.get_provider_info(),
        "speaker_diarization": {
            "available": speaker_diarization_service.is_available(),
            "description": "Speaker diarization using pyannote.audio"
        }
    }


@router.get("/metrics")
def get_basic_metrics(db: Session = Depends(get_db)):
    """
    Get basic system metrics.
    """
    try:
        from app.repositories.meeting_repository import meeting_repository
        from app.repositories.user_repository import user_repository
        
        # Get basic counts
        total_meetings = meeting_repository.count(db)
        total_users = user_repository.count(db)
        
        # Get processing status breakdown
        analytics = meeting_repository.get_analytics(db)
        
        return {
            "totals": {
                "meetings": total_meetings,
                "users": total_users,
                "total_audio_hours": analytics.get("total_duration_hours", 0)
            },
            "processing": {
                "status_breakdown": analytics.get("status_breakdown", {}),
                "avg_processing_time_seconds": analytics.get("avg_processing_time_seconds", 0)
            },
            "providers": {
                "asr_usage": analytics.get("provider_usage", {}).get("asr", {}),
                "llm_usage": analytics.get("provider_usage", {}).get("llm", {})
            }
        }
        
    except Exception as e:
        return {
            "error": f"Failed to get metrics: {str(e)}",
            "totals": {"meetings": 0, "users": 0},
            "processing": {"status_breakdown": {}, "avg_processing_time_seconds": 0},
            "providers": {"asr_usage": {}, "llm_usage": {}}
        }


@router.get("/version")
def get_version_info():
    """
    Get version and build information.
    """
    return {
        "version": settings.APP_VERSION,
        "name": settings.APP_NAME,
        "api_version": settings.API_V1_STR,
        "debug": settings.DEBUG
    }