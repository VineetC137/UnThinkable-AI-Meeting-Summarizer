"""
Unit tests for transcription, summarization, and speaker diarization services using mocks.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.transcription_service import transcription_service
from app.services.summarization_service import summarization_service
from app.models.meeting import ASRProvider, LLMProvider
from app.utils.prompt_templates import PromptTemplate


@pytest.mark.asyncio
async def test_transcription_service_mock_openai():
    """Test OpenAI Whisper transcription with mock API response."""
    import tempfile
    import os
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={
        "text": "Hello this is a mocked transcript",
        "language": "en",
        "segments": [{"start": 0.0, "end": 2.0, "text": "Hello this is a mocked transcript", "avg_logprob": -0.1}]
    })

    # Create a temporary file to act as the audio file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(b"fake wav data")
        temp_path = tmp.name

    try:
        transcription_service.providers[ASRProvider.OPENAI_WHISPER].api_key = "fake-key"
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
             patch("app.utils.audio_processor.audio_processor.validate_audio_file", return_value=True):
            
            mock_post.return_value = mock_response
            
            result = await transcription_service.transcribe(
                audio_path=temp_path,
                provider=ASRProvider.OPENAI_WHISPER,
                model_name="whisper-1"
            )
            
            assert result["transcript"] == "Hello this is a mocked transcript"
            assert result["language"] == "en"
            assert len(result["segments"]) == 1
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pytest.mark.asyncio
async def test_summarization_service_mock_openai():
    """Test OpenAI GPT summarization with mock API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={
        "choices": [
            {
                "message": {
                    "content": "This is a mocked executive summary"
                }
            }
        ]
    })

    summarization_service.providers[LLMProvider.OPENAI].api_key = "fake-key"
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        
        mock_post.return_value = mock_response
        
        result = await summarization_service.generate_summary(
            transcript="Mock transcript content",
            provider=LLMProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            summary_type=PromptTemplate.EXECUTIVE_SUMMARY
        )
        
        assert result == "This is a mocked executive summary"
