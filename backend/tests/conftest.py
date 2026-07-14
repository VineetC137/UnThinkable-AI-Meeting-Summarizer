"""
Pytest configuration and fixtures.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables for testing database before any imports
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["ASYNC_DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from app.core.config import settings
# Override settings for tests before importing main/database engines
settings.DATABASE_URL = "sqlite:///./test.db"
settings.ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
settings.DEBUG = True

from app.main import app
from app.core.database import Base, get_db, engine, SessionLocal
from app.services.auth_service import auth_service
from app.schemas.auth import UserCreate


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Get a database session for test operations."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Get FastAPI TestClient with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a default test user."""
    user_in = UserCreate(
        email="test@example.com",
        username="testuser",
        password="Password123!",
        full_name="Test User"
    )
    result = auth_service.register_user(db_session, user_in)
    return result["user"]


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """Get authorization headers for the default test user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "Password123!"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Mock Celery tasks to run synchronously in tests
@pytest.fixture(autouse=True)
def mock_celery(monkeypatch):
    """Mock Celery task .delay() to execute synchronously or mock delay behaviour."""
    from app.tasks.meeting_tasks import (
        process_meeting_full_task,
        process_meeting_transcription_task
    )
    from app.tasks.notification_tasks import send_meeting_summary_email_task
    
    # We mock delay to immediately run the task function synchronously
    def mock_delay_full(meeting_id, include_speaker_diarization=True):
        # run task directly by calling it (mocking celery eager mode)
        try:
            process_meeting_full_task(meeting_id, include_speaker_diarization)
        except Exception:
            pass
            
    def mock_delay_trans(meeting_id, include_speaker_diarization=False):
        try:
            process_meeting_transcription_task(meeting_id, include_speaker_diarization)
        except Exception:
            pass
            
    def mock_delay_email(meeting_id, recipient):
        try:
            send_meeting_summary_email_task(meeting_id, recipient)
        except Exception:
            pass
            
    monkeypatch.setattr(process_meeting_full_task, "delay", mock_delay_full)
    monkeypatch.setattr(process_meeting_transcription_task, "delay", mock_delay_trans)
    monkeypatch.setattr(send_meeting_summary_email_task, "delay", mock_delay_email)
