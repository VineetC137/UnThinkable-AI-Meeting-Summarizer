"""
Transcription service supporting multiple ASR providers.
Preserves Whisper.cpp integration and adds OpenAI Whisper and Faster-Whisper.
"""

import os
import tempfile
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
from pathlib import Path
import asyncio
import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.meeting import ASRProvider
from app.utils.audio_processor import audio_processor

logger = get_logger(__name__)


class BaseASRProvider(ABC):
    """Base class for ASR providers."""
    
    @abstractmethod
    async def transcribe(
        self, 
        audio_path: str, 
        model_name: str,
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio file.
        
        Returns:
            {
                'transcript': str,
                'confidence': float,
                'language': str,
                'segments': List[Dict] (optional)
            }
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        pass


class WhisperCppProvider(BaseASRProvider):
    """
    Whisper.cpp provider - preserves original functionality.
    """
    
    def __init__(self):
        self.logger = logger
    
    async def transcribe(
        self, 
        audio_path: str, 
        model_name: str = "small",
        language: Optional[str] = None
    ) -> Dict:
        """Transcribe using Whisper.cpp."""
        try:
            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            transcript, success, confidence, segments = await loop.run_in_executor(
                None,
                audio_processor.transcribe_with_whisper_cpp,
                audio_path,
                model_name,
                language
            )
            
            if not success:
                raise Exception("Whisper.cpp transcription failed")
            
            return {
                'transcript': transcript,
                'confidence': confidence or 0.0,
                'language': language or 'auto',
                'segments': segments
            }
            
        except Exception as e:
            self.logger.error(f"Whisper.cpp transcription error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Whisper.cpp models."""
        return audio_processor.get_available_whisper_models()


class OpenAIWhisperProvider(BaseASRProvider):
    """
    OpenAI Whisper API provider.
    """
    
    def __init__(self):
        self.logger = logger
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
    
    async def transcribe(
        self, 
        audio_path: str, 
        model_name: str = "whisper-1",
        language: Optional[str] = None
    ) -> Dict:
        """Transcribe using OpenAI Whisper API."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        try:
            # Preprocess audio for optimal API performance
            processed_audio, success = audio_processor.preprocess_audio_file(audio_path)
            if not success:
                processed_audio = audio_path
            
            # Prepare request
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Read audio file
            with open(processed_audio, 'rb') as audio_file:
                files = {
                    'file': (Path(audio_path).name, audio_file, 'audio/wav'),
                    'model': (None, model_name),
                    'response_format': (None, 'verbose_json'),
                }
                
                if language:
                    files['language'] = (None, language)
                
                async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout
                    response = await client.post(
                        f"{self.base_url}/audio/transcriptions",
                        headers=headers,
                        files=files
                    )
            
            # Clean up processed file if it was temporary
            if processed_audio != audio_path:
                audio_processor.cleanup_temp_file(processed_audio)
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Extract segments if available
            segments = []
            if 'segments' in result:
                for segment in result['segments']:
                    segments.append({
                        'start': segment.get('start', 0),
                        'end': segment.get('end', 0),
                        'text': segment.get('text', ''),
                        'confidence': segment.get('avg_logprob', 0)
                    })
            
            return {
                'transcript': result.get('text', ''),
                'confidence': 0.9,  # OpenAI doesn't provide overall confidence, assume high
                'language': result.get('language', 'auto'),
                'segments': segments
            }
            
        except Exception as e:
            self.logger.error(f"OpenAI Whisper transcription error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI Whisper models."""
        return ["whisper-1"]  # OpenAI only has one Whisper model


class FasterWhisperProvider(BaseASRProvider):
    """
    Faster-Whisper provider for local GPU-accelerated transcription.
    """
    
    def __init__(self):
        self.logger = logger
        self.models = {}  # Cache loaded models
    
    async def transcribe(
        self, 
        audio_path: str, 
        model_name: str = "small",
        language: Optional[str] = None
    ) -> Dict:
        """Transcribe using Faster-Whisper."""
        try:
            import torch
            from faster_whisper import WhisperModel
            
            # Load model if not cached
            if model_name not in self.models:
                self.logger.info(f"Loading Faster-Whisper model: {model_name}")
                
                # Determine device
                device = "cuda" if torch.cuda.is_available() else "cpu"
                compute_type = "float16" if device == "cuda" else "int8"
                
                # Load model in thread pool
                loop = asyncio.get_event_loop()
                model = await loop.run_in_executor(
                    None,
                    lambda: WhisperModel(
                        model_name, 
                        device=device, 
                        compute_type=compute_type
                    )
                )
                self.models[model_name] = model
            
            model = self.models[model_name]
            
            # Preprocess audio
            processed_audio, success = audio_processor.preprocess_audio_file(audio_path)
            if not success:
                processed_audio = audio_path
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None,
                lambda: model.transcribe(
                    processed_audio,
                    language=language,
                    beam_size=5,
                    best_of=5,
                    temperature=0.0,
                    condition_on_previous_text=False
                )
            )
            
            # Convert segments to list and extract transcript
            segments_list = list(segments)
            transcript = " ".join([segment.text for segment in segments_list])
            
            # Calculate average confidence
            confidences = [segment.avg_logprob for segment in segments_list if hasattr(segment, 'avg_logprob')]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Convert segments to our format
            formatted_segments = []
            for segment in segments_list:
                formatted_segments.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text,
                    'confidence': getattr(segment, 'avg_logprob', 0)
                })
            
            # Clean up processed file if it was temporary
            if processed_audio != audio_path:
                audio_processor.cleanup_temp_file(processed_audio)
            
            return {
                'transcript': transcript.strip(),
                'confidence': max(0.0, min(1.0, (avg_confidence + 5) / 5)),  # Normalize logprob to 0-1
                'language': info.language if hasattr(info, 'language') else (language or 'auto'),
                'segments': formatted_segments
            }
            
        except Exception as e:
            self.logger.error(f"Faster-Whisper transcription error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Faster-Whisper models."""
        return ["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3"]


class TranscriptionService:
    """
    Main transcription service that manages multiple ASR providers.
    """
    
    def __init__(self):
        self.logger = logger
        self.providers = {
            ASRProvider.WHISPER_CPP: WhisperCppProvider(),
            ASRProvider.OPENAI_WHISPER: OpenAIWhisperProvider(),
            ASRProvider.FASTER_WHISPER: FasterWhisperProvider(),
        }
    
    async def transcribe(
        self,
        audio_path: str,
        provider: ASRProvider,
        model_name: str,
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio using specified provider and model.
        
        Returns:
            {
                'transcript': str,
                'confidence': float,
                'language': str,
                'segments': List[Dict],
                'provider': str,
                'model': str
            }
        """
        if provider not in self.providers:
            raise ValueError(f"Unsupported ASR provider: {provider}")
        
        self.logger.info(f"Starting transcription with {provider.value} using model {model_name}")
        
        # Validate audio file
        if not audio_processor.validate_audio_file(audio_path):
            raise ValueError("Invalid or unsupported audio file format")
        
        # Get provider instance
        asr_provider = self.providers[provider]
        
        # Validate model availability
        available_models = asr_provider.get_available_models()
        if model_name not in available_models:
            raise ValueError(
                f"Model {model_name} not available for {provider.value}. "
                f"Available models: {available_models}"
            )
        
        try:
            # Perform transcription
            result = await asr_provider.transcribe(audio_path, model_name, language)
            
            # Add provider and model info to result
            result['provider'] = provider.value
            result['model'] = model_name
            
            self.logger.info(
                f"Transcription completed successfully with {provider.value}. "
                f"Transcript length: {len(result['transcript'])} characters"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Transcription failed with {provider.value}: {e}")
            raise
    
    def get_available_providers(self) -> List[ASRProvider]:
        """Get list of available ASR providers."""
        available = []
        
        for provider in ASRProvider:
            try:
                # Check if provider is properly configured
                if provider == ASRProvider.OPENAI_WHISPER:
                    if settings.OPENAI_API_KEY:
                        available.append(provider)
                else:
                    available.append(provider)
            except Exception:
                continue
        
        return available
    
    def get_available_models(self, provider: ASRProvider) -> List[str]:
        """Get available models for a specific provider."""
        if provider not in self.providers:
            return []
        
        try:
            return self.providers[provider].get_available_models()
        except Exception as e:
            self.logger.error(f"Error getting models for {provider.value}: {e}")
            return []
    
    def get_provider_info(self) -> Dict[str, Dict]:
        """Get information about all providers."""
        info = {}
        
        for provider in ASRProvider:
            info[provider.value] = {
                'available': provider in self.get_available_providers(),
                'models': self.get_available_models(provider),
                'description': self._get_provider_description(provider)
            }
        
        return info
    
    def _get_provider_description(self, provider: ASRProvider) -> str:
        """Get description for a provider."""
        descriptions = {
            ASRProvider.WHISPER_CPP: "Local Whisper.cpp implementation - Fast, no API costs",
            ASRProvider.OPENAI_WHISPER: "OpenAI Whisper API - High accuracy, requires API key",
            ASRProvider.FASTER_WHISPER: "GPU-accelerated local Whisper - Best of both worlds"
        }
        return descriptions.get(provider, "Unknown provider")


# Create global service instance
transcription_service = TranscriptionService()