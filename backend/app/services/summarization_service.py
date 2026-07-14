"""
Summarization service supporting multiple LLM providers.
Preserves Ollama integration and adds OpenAI, Gemini, and Claude.
"""

import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import httpx
import asyncio

from app.core.config import settings
from app.core.logging import get_logger
from app.models.meeting import LLMProvider
from app.utils.prompt_templates import PromptTemplateManager, PromptTemplate

logger = get_logger(__name__)


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate response from LLM."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        pass


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider - preserves original functionality with improvements.
    """
    
    def __init__(self):
        self.logger = logger
        self.base_url = settings.OLLAMA_SERVER_URL
    
    async def generate_response(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate response using Ollama API with streaming support."""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": temperature
                }
            }
            
            if max_tokens:
                data["options"]["num_predict"] = max_tokens
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=data,
                    headers=headers
                ) as response:
                    
                    if response.status_code != 200:
                        raise Exception(f"Ollama API error: {response.status_code}")
                    
                    full_response = ""
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                json_line = json.loads(line)
                                chunk = json_line.get("response", "")
                                full_response += chunk
                                
                                if json_line.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
                    
                    return full_response.strip()
                    
        except Exception as e:
            self.logger.error(f"Ollama generation error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Ollama models from API."""
        try:
            import requests  # Use sync requests for model discovery
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            
            if response.status_code == 200:
                models = response.json()["models"]
                return [model["name"] for model in models]
            else:
                self.logger.warning(f"Failed to get Ollama models: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting Ollama models: {e}")
            return []


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self):
        self.logger = logger
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
    
    async def generate_response(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate response using OpenAI API."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "stream": False
            }
            
            if max_tokens:
                data["max_tokens"] = max_tokens
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
            
            if response.status_code != 200:
                error_detail = response.json().get("error", {}).get("message", response.text)
                raise Exception(f"OpenAI API error: {response.status_code} - {error_detail}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            self.logger.error(f"OpenAI generation error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models."""
        return [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""
    
    def __init__(self):
        self.logger = logger
        self.api_key = settings.GOOGLE_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def generate_response(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate response using Google Gemini API."""
        if not self.api_key:
            raise ValueError("Google API key not configured")
        
        try:
            url = f"{self.base_url}/models/{model_name}:generateContent?key={self.api_key}"
            
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "candidateCount": 1
                }
            }
            
            if max_tokens:
                data["generationConfig"]["maxOutputTokens"] = max_tokens
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                error_detail = response.json().get("error", {}).get("message", response.text)
                raise Exception(f"Gemini API error: {response.status_code} - {error_detail}")
            
            result = response.json()
            
            # Extract text from Gemini response format
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"].strip()
            
            raise Exception("Invalid response format from Gemini API")
            
        except Exception as e:
            self.logger.error(f"Gemini generation error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Gemini models."""
        return [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self):
        self.logger = logger
        self.api_key = settings.ANTHROPIC_API_KEY
        self.base_url = "https://api.anthropic.com/v1"
    
    async def generate_response(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate response using Anthropic Claude API."""
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")
        
        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens or 4000
            }
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=data
                )
            
            if response.status_code != 200:
                error_detail = response.json().get("error", {}).get("message", response.text)
                raise Exception(f"Claude API error: {response.status_code} - {error_detail}")
            
            result = response.json()
            
            # Extract text from Claude response format
            if "content" in result and len(result["content"]) > 0:
                content = result["content"][0]
                if content["type"] == "text":
                    return content["text"].strip()
            
            raise Exception("Invalid response format from Claude API")
            
        except Exception as e:
            self.logger.error(f"Claude generation error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Claude models."""
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]


class SummarizationService:
    """
    Main summarization service that manages multiple LLM providers.
    """
    
    def __init__(self):
        self.logger = logger
        self.prompt_manager = PromptTemplateManager()
        self.providers = {
            LLMProvider.OLLAMA: OllamaProvider(),
            LLMProvider.OPENAI: OpenAIProvider(),
            LLMProvider.GEMINI: GeminiProvider(),
            LLMProvider.CLAUDE: ClaudeProvider(),
        }
    
    async def generate_summary(
        self,
        transcript: str,
        provider: LLMProvider,
        model_name: str,
        summary_type: PromptTemplate,
        context: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        Generate a specific type of summary using the specified provider.
        """
        if provider not in self.providers:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        self.logger.info(
            f"Generating {summary_type.value} with {provider.value} using model {model_name}"
        )
        
        # Get the appropriate prompt
        prompt = self.prompt_manager.get_prompt(summary_type, transcript, context)
        
        # Get provider instance
        llm_provider = self.providers[provider]
        
        # Validate model availability
        available_models = llm_provider.get_available_models()
        if model_name not in available_models:
            raise ValueError(
                f"Model {model_name} not available for {provider.value}. "
                f"Available models: {available_models}"
            )
        
        try:
            # Generate response
            response = await llm_provider.generate_response(
                prompt=prompt,
                model_name=model_name,
                temperature=temperature,
                max_tokens=4000 if summary_type != PromptTemplate.DETAILED_SUMMARY else 8000
            )
            
            self.logger.info(f"Summary generation completed with {provider.value}")
            return response
            
        except Exception as e:
            self.logger.error(f"Summary generation failed with {provider.value}: {e}")
            raise
    
    async def generate_comprehensive_analysis(
        self,
        transcript: str,
        provider: LLMProvider,
        model_name: str,
        context: Optional[str] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate comprehensive meeting analysis with all summary types.
        """
        self.logger.info(f"Starting comprehensive analysis with {provider.value}")
        
        # Use the comprehensive analysis prompt
        prompt = self.prompt_manager.get_comprehensive_analysis_prompt(transcript, context)
        
        # Get provider instance
        if provider not in self.providers:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        llm_provider = self.providers[provider]
        
        try:
            # Generate comprehensive response
            response = await llm_provider.generate_response(
                prompt=prompt,
                model_name=model_name,
                temperature=temperature,
                max_tokens=12000  # Larger limit for comprehensive analysis
            )
            
            # Try to parse as JSON
            try:
                result = json.loads(response)
                self.logger.info("Comprehensive analysis completed successfully")
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, return as text summary
                self.logger.warning("JSON parsing failed, returning as text summary")
                return {
                    "executive_summary": response,
                    "detailed_summary": response,
                    "key_decisions": [],
                    "action_items": [],
                    "risks": [],
                    "open_questions": [],
                    "keywords": []
                }
                
        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed with {provider.value}: {e}")
            raise
    
    async def generate_structured_summaries(
        self,
        transcript: str,
        provider: LLMProvider,
        model_name: str,
        summary_types: List[PromptTemplate],
        context: Optional[str] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate multiple types of summaries concurrently.
        """
        self.logger.info(f"Generating {len(summary_types)} summary types with {provider.value}")
        
        # Create tasks for concurrent generation
        tasks = []
        for summary_type in summary_types:
            task = self.generate_summary(
                transcript=transcript,
                provider=provider,
                model_name=model_name,
                summary_type=summary_type,
                context=context,
                temperature=temperature
            )
            tasks.append((summary_type, task))
        
        # Execute tasks concurrently
        results = {}
        for summary_type, task in tasks:
            try:
                result = await task
                
                # For structured outputs, try to parse as JSON
                if summary_type in [
                    PromptTemplate.KEY_DECISIONS,
                    PromptTemplate.ACTION_ITEMS,
                    PromptTemplate.RISKS,
                    PromptTemplate.OPEN_QUESTIONS,
                    PromptTemplate.KEYWORDS
                ]:
                    try:
                        parsed_result = json.loads(result)
                        results[summary_type.value] = parsed_result
                    except json.JSONDecodeError:
                        self.logger.warning(f"Failed to parse JSON for {summary_type.value}")
                        results[summary_type.value] = result
                else:
                    results[summary_type.value] = result
                    
            except Exception as e:
                self.logger.error(f"Failed to generate {summary_type.value}: {e}")
                results[summary_type.value] = None
        
        return results
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available LLM providers."""
        available = []
        
        for provider in LLMProvider:
            try:
                # Check if provider is properly configured
                if provider == LLMProvider.OPENAI and not settings.OPENAI_API_KEY:
                    continue
                elif provider == LLMProvider.GEMINI and not settings.GOOGLE_API_KEY:
                    continue
                elif provider == LLMProvider.CLAUDE and not settings.ANTHROPIC_API_KEY:
                    continue
                
                available.append(provider)
            except Exception:
                continue
        
        return available
    
    def get_available_models(self, provider: LLMProvider) -> List[str]:
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
        
        for provider in LLMProvider:
            info[provider.value] = {
                'available': provider in self.get_available_providers(),
                'models': self.get_available_models(provider),
                'description': self._get_provider_description(provider)
            }
        
        return info
    
    def _get_provider_description(self, provider: LLMProvider) -> str:
        """Get description for a provider."""
        descriptions = {
            LLMProvider.OLLAMA: "Local Ollama server - Free, private, customizable",
            LLMProvider.OPENAI: "OpenAI GPT models - High quality, requires API key",
            LLMProvider.GEMINI: "Google Gemini - Advanced reasoning, requires API key",
            LLMProvider.CLAUDE: "Anthropic Claude - Excellent analysis, requires API key"
        }
        return descriptions.get(provider, "Unknown provider")


# Create global service instance
summarization_service = SummarizationService()