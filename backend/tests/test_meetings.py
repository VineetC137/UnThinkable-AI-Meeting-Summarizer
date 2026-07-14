"""
Tests for meeting endpoints.
"""

import io
import pytest


def test_create_meeting(client, auth_headers):
    file_content = b"fake audio data"
    file_io = io.BytesIO(file_content)
    
    response = client.post(
        "/api/v1/meetings/",
        headers=auth_headers,
        data={
            "title": "Weekly Sync",
            "description": "Weekly project alignment",
            "context": "Context information",
            "tags": '["project", "sync"]',
            "asr_provider": "whisper_cpp",
            "asr_model": "small",
            "llm_provider": "ollama",
            "llm_model": "llama2"
        },
        files={
            "audio_file": ("test.wav", file_io, "audio/wav")
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Weekly Sync"
    assert data["status"] == "pending"


def test_get_meetings(client, auth_headers):
    # Retrieve meeting list
    response = client.get("/api/v1/meetings/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "meetings" in data
    assert isinstance(data["meetings"], list)


def test_get_analytics(client, auth_headers):
    response = client.get("/api/v1/meetings/analytics/overview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_meetings" in data
    assert "total_duration_hours" in data
