"""
Celery application configuration for background task processing.
"""

from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "meeting_summarizer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.meeting_tasks",
        "app.tasks.notification_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Time zone
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'app.tasks.meeting_tasks.*': {'queue': 'meeting_processing'},
        'app.tasks.notification_tasks.*': {'queue': 'notifications'},
    },
    
    # Task execution
    task_always_eager=False,  # Set to True for synchronous execution in tests
    task_eager_propagates=True,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Beat schedule (for periodic tasks)
    beat_schedule={
        'cleanup-failed-meetings': {
            'task': 'app.tasks.meeting_tasks.cleanup_failed_meetings',
            'schedule': 3600.0,  # Run every hour
        },
        'generate-analytics': {
            'task': 'app.tasks.meeting_tasks.generate_system_analytics',
            'schedule': 86400.0,  # Run daily
        },
    },
)


# Celery signals
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
    return "Celery is working!"


# Export celery app
__all__ = ["celery_app"]