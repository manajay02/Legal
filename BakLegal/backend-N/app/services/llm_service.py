"""
LLM Service for Google Gemini Integration
==========================================

This service handles communication with Google's Gemini API for
training data generation using the teacher-student approach.

Teacher Model: Gemini 2.5 Flash (free tier, high quality)
Student Model: Qwen2-1.5B-Instruct (target for fine-tuning)

"""

import json
import logging
import time
import re
from typing import Dict, Any, Optional

from app.core.config import settings


logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service class for interacting with Google Gemini API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Initialize the Gemini service.
        
        Args:
            api_key: Google AI API key (from Google AI Studio)
            model_name: Name of the Gemini model to use
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
        """
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError(
                "Google API key is required. Set GOOGLE_API_KEY in .env file or "
                "get your key from https://makersuite.google.com/app/apikey"
            )

        try:
            from google import genai
            from google.genai.types import GenerateContentConfig as _GCC  # noqa: F401
        except ImportError:
            raise ImportError(
                "google-genai package is required for Gemini. "
                "Run: pip install google-genai"
            )

        # Initialize the client
        self.client = genai.Client(api_key=self.api_key)
        self._genai = genai
        
        logger.info(f"Gemini service initialized (model: {self.model_name})")
    
    
    def get_analysis_from_gemini(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retry_attempts: int = 3
    ) -> str:
        """
        Send a prompt to Gemini and return the text response.
        
        Args:
            prompt: The input prompt for Gemini
            temperature: Override default temperature (optional)
            max_tokens: Override default max tokens (optional)
            retry_attempts: Number of retry attempts on failure
            
        Returns:
            Generated text response from Gemini
            
        Raises:
            Exception: If all retry attempts fail
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        from google.genai.types import GenerateContentConfig
        config = GenerateContentConfig(
            temperature=temp,
            max_output_tokens=max_tok,
            top_p=0.95,
            top_k=40
        )
        
        logger.debug(f"Sending prompt to Gemini (length: {len(prompt)} chars)")
        
        for attempt in range(1, retry_attempts + 1):
            try:
                # Generate response
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                
                # Extract text from response
                if response.text:
                    logger.info(
                        f"✓ Received response from Gemini "
                        f"({len(response.text)} chars)"
                    )
                    return response.text.strip()
                else:
                    logger.warning("Empty response from Gemini")
                    if attempt < retry_attempts:
                        logger.info(f"Retrying... (attempt {attempt + 1}/{retry_attempts})")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise ValueError("Gemini returned empty response")
                
            except Exception as e:
                error_str = str(e)
                logger.error(f"Gemini API error (attempt {attempt}/{retry_attempts}): {error_str}")
                
                # Check for rate limit error and extract retry delay
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    # Extract retry delay from error message if available
                    import re
                    retry_match = re.search(r'retry in (\d+(?:\.\d+)?)s', error_str)
                    if retry_match:
                        wait_time = int(float(retry_match.group(1))) + 5  # Add buffer
                        logger.info(f"Rate limited. Waiting {wait_time} seconds as requested by API...")
                    else:
                        wait_time = 60  # Default to 60 seconds for rate limits
                        logger.info(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif attempt < retry_attempts:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    raise
        
        raise Exception("Failed to get response from Gemini after all retries")
    
    
    def get_json_from_gemini(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retry_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Send a prompt to Gemini and parse the response as JSON.
        
        Uses a lower temperature for JSON generation and includes automatic
        retries with stricter prompting if JSON parsing fails.
        
        Args:
            prompt: The input prompt for Gemini
            temperature: Override default temperature (optional)
            max_tokens: Override default max tokens (optional)
            retry_attempts: Number of retry attempts on failure
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            json.JSONDecodeError: If response cannot be parsed as JSON after all retries
            Exception: If API call fails
        """
        # Use lower temperature for structured output
        json_temp = temperature if temperature is not None else 0.2
        
        for attempt in range(1, retry_attempts + 1):
            try:
                # Add stricter instructions on retry attempts
                current_prompt = prompt
                if attempt > 1:
                    current_prompt = (
                        "CRITICAL: Your response MUST be valid JSON only. "
                        "No markdown, no explanation, no code fences. "
                        "Ensure all strings are properly escaped.\n\n"
                        + prompt
                    )
                
                response_text = self.get_analysis_from_gemini(
                    prompt=current_prompt,
                    temperature=json_temp,
                    max_tokens=max_tokens,
                    retry_attempts=1  # Don't retry at this level
                )
                
                # Clean up the response
                response_text = self._extract_json_from_text(response_text)
                
                # Try to parse
                parsed_json = json.loads(response_text)
                logger.debug("✓ Successfully parsed JSON response")
                return parsed_json
                
            except json.JSONDecodeError as e:
                logger.warning(
                    f"JSON parse error (attempt {attempt}/{retry_attempts}): {str(e)}"
                )
                logger.debug(f"Problematic JSON: {response_text[:500]}...")
                
                if attempt < retry_attempts:
                    logger.info(f"Retrying with stricter prompt...")
                    time.sleep(2)
                else:
                    logger.error("All JSON parsing attempts failed")
                    logger.error(f"Final raw response: {response_text}")
                    raise
        
        raise json.JSONDecodeError("Failed to parse JSON after all retries", "", 0)
    
    
    def _extract_json_from_text(self, text: str) -> str:
        """
        Extract JSON from text that may contain markdown code blocks or other formatting.
        
        Args:
            text: Raw text response
            
        Returns:
            Cleaned JSON string
        """
        text = text.strip()
        
        # Remove markdown code fences
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        # Try to find JSON object boundaries if text contains extra content
        # Look for outermost curly braces
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            text = text[first_brace:last_brace + 1]
        
        return text
    
    
    def check_health(self) -> bool:
        """
        Check if Gemini API is accessible and working.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try listing models to verify API key
            models = self.client.models.list()
            logger.info("✓ Gemini API is healthy and accessible")
            return True
        except Exception as e:
            logger.error(f"✗ Gemini health check failed: {str(e)}")
            return False


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """
    Get or create the Gemini service singleton.
    
    Returns:
        GeminiService instance
    """
    global _gemini_service
    
    if _gemini_service is None:
        _gemini_service = GeminiService(
            api_key=settings.GOOGLE_API_KEY,
            model_name=settings.GEMINI_MODEL_NAME,
            temperature=settings.GEMINI_TEMPERATURE,
            max_tokens=settings.GEMINI_MAX_TOKENS
        )
    
    return _gemini_service


def get_analysis_from_gemini(prompt: str) -> str:
    """
    Convenience function to get a text response from Gemini.
    
    Args:
        prompt: Input prompt
        
    Returns:
        Generated text response
    """
    service = get_gemini_service()
    return service.get_analysis_from_gemini(prompt)


# ============================================
# DeepSeek Service
# ============================================

class DeepSeekService:
    """
    Service class for interacting with the DeepSeek API.
    DeepSeek uses an OpenAI-compatible REST API.
    """

    BASE_URL = "https://api.deepseek.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError(
                "DeepSeek API key is required. Set DEEPSEEK_API_KEY in .env file. "
                "Get your key from https://platform.deepseek.com/"
            )

        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.BASE_URL,
            )
        except ImportError:
            raise ImportError(
                "openai package is required for DeepSeek. "
                "Run: pip install openai"
            )

        logger.info(f"DeepSeek service initialized (model: {self.model_name})")

    def get_analysis_from_deepseek(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retry_attempts: int = 3,
    ) -> str:
        """Send a prompt to DeepSeek and return the text response."""
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        for attempt in range(1, retry_attempts + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temp,
                    max_tokens=max_tok,
                )
                text = response.choices[0].message.content
                if text:
                    logger.info(f"✓ Received response from DeepSeek ({len(text)} chars)")
                    return text.strip()
                logger.warning("Empty response from DeepSeek")
                if attempt < retry_attempts:
                    time.sleep(2 ** attempt)
                    continue
                raise ValueError("DeepSeek returned empty response")

            except Exception as e:
                error_str = str(e)
                logger.error(f"DeepSeek API error (attempt {attempt}/{retry_attempts}): {error_str}")
                if "429" in error_str or "rate" in error_str.lower():
                    wait_time = 60
                    logger.info(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif attempt < retry_attempts:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

        raise Exception("Failed to get response from DeepSeek after all retries")

    def get_json_from_deepseek(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retry_attempts: int = 3,
    ) -> Dict[str, Any]:
        """Send a prompt to DeepSeek and parse the response as JSON."""
        json_temp = temperature if temperature is not None else 0.2

        for attempt in range(1, retry_attempts + 1):
            try:
                current_prompt = prompt
                if attempt > 1:
                    current_prompt = (
                        "CRITICAL: Your response MUST be valid JSON only. "
                        "No markdown, no explanation, no code fences. "
                        "Ensure all strings are properly escaped.\n\n"
                        + prompt
                    )

                response_text = self.get_analysis_from_deepseek(
                    prompt=current_prompt,
                    temperature=json_temp,
                    max_tokens=max_tokens,
                    retry_attempts=1,
                )

                response_text = self._extract_json_from_text(response_text)
                parsed_json = json.loads(response_text)
                logger.debug("✓ Successfully parsed JSON response from DeepSeek")
                return parsed_json

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error (attempt {attempt}/{retry_attempts}): {str(e)}")
                if attempt < retry_attempts:
                    logger.info("Retrying with stricter prompt...")
                    time.sleep(2)
                else:
                    logger.error("All JSON parsing attempts failed")
                    raise

        raise json.JSONDecodeError("Failed to parse JSON after all retries", "", 0)

    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON from text that may contain markdown code blocks."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            text = text[first_brace:last_brace + 1]
        return text

    # Drop-in aliases — same interface as OpenRouterService / GeminiService
    def get_analysis_from_gemini(self, *args, **kwargs) -> str:
        return self.get_analysis_from_deepseek(*args, **kwargs)

    def get_json_from_gemini(self, *args, **kwargs) -> Dict[str, Any]:
        return self.get_json_from_deepseek(*args, **kwargs)

    def check_health(self) -> bool:
        """Check if DeepSeek API is accessible."""
        try:
            self.get_analysis_from_deepseek("Say OK", max_tokens=5, retry_attempts=1)
            logger.info("✓ DeepSeek API is healthy and accessible")
            return True
        except Exception as e:
            logger.error(f"✗ DeepSeek health check failed: {str(e)}")
            return False


# Singleton instance
_deepseek_service: Optional[DeepSeekService] = None


def get_deepseek_service() -> DeepSeekService:
    """Get or create the DeepSeek service singleton."""
    global _deepseek_service
    if _deepseek_service is None:
        _deepseek_service = DeepSeekService(
            api_key=settings.DEEPSEEK_API_KEY,
            model_name=settings.DEEPSEEK_MODEL_NAME,
            temperature=settings.DEEPSEEK_TEMPERATURE,
            max_tokens=settings.DEEPSEEK_MAX_TOKENS,
        )
    return _deepseek_service


# ============================================
# OpenRouter Service
# ============================================

class OpenRouterService:
    """
    Service for OpenRouter API (OpenAI-compatible).
    Supports free models like deepseek/deepseek-chat with no rate limits.
    Drop-in replacement for GeminiService — same method names.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "deepseek/deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY in .env file. "
                "Get your key from https://openrouter.ai/"
            )

        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.BASE_URL,
                default_headers={
                    "HTTP-Referer": "https://github.com/legal-score-model",
                    "X-Title": "Legal Argument Critic",
                },
            )
        except ImportError:
            raise ImportError(
                "openai package is required for OpenRouter. Run: pip install openai"
            )

        logger.info(f"OpenRouter service initialized (model: {self.model_name})")

    def get_analysis_from_gemini(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retry_attempts: int = 3,
    ) -> str:
        """Send a prompt to OpenRouter and return the text response."""
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        for attempt in range(1, retry_attempts + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temp,
                    max_tokens=max_tok,
                )
                text = response.choices[0].message.content
                if text:
                    logger.info(f"✓ Received response from OpenRouter ({len(text)} chars)")
                    return text.strip()
                logger.warning("Empty response from OpenRouter")
                if attempt < retry_attempts:
                    time.sleep(2 ** attempt)
                    continue
                raise ValueError("OpenRouter returned empty response")

            except Exception as e:
                error_str = str(e)
                logger.error(f"OpenRouter API error (attempt {attempt}/{retry_attempts}): {error_str}")
                if "429" in error_str or "rate" in error_str.lower():
                    logger.info("Rate limited. Waiting 30 seconds...")
                    time.sleep(30)
                elif attempt < retry_attempts:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

        raise Exception("Failed to get response from OpenRouter after all retries")

    def get_json_from_gemini(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retry_attempts: int = 3,
    ) -> Dict[str, Any]:
        """Send a prompt to OpenRouter and parse the response as JSON."""
        json_temp = temperature if temperature is not None else 0.2

        for attempt in range(1, retry_attempts + 1):
            try:
                current_prompt = prompt
                if attempt > 1:
                    current_prompt = (
                        "CRITICAL: Your response MUST be valid JSON only. "
                        "No markdown, no explanation, no code fences.\n\n" + prompt
                    )
                response_text = self.get_analysis_from_gemini(
                    prompt=current_prompt,
                    temperature=json_temp,
                    max_tokens=max_tokens,
                    retry_attempts=1,
                )
                response_text = self._extract_json_from_text(response_text)
                parsed_json = json.loads(response_text)
                logger.debug("✓ Successfully parsed JSON response from OpenRouter")
                return parsed_json

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error (attempt {attempt}/{retry_attempts}): {str(e)}")
                if attempt < retry_attempts:
                    time.sleep(2)
                else:
                    raise

        raise json.JSONDecodeError("Failed to parse JSON after all retries", "", 0)

    def _extract_json_from_text(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            text = text[first_brace:last_brace + 1]
        return text

    def check_health(self) -> bool:
        """Check if OpenRouter API is accessible."""
        try:
            self.get_analysis_from_gemini("Say OK", max_tokens=5, retry_attempts=1)
            logger.info("✓ OpenRouter API is healthy and accessible")
            return True
        except Exception as e:
            logger.error(f"✗ OpenRouter health check failed: {str(e)}")
            return False


# Singleton instance
_openrouter_service: Optional[OpenRouterService] = None


def get_openrouter_service() -> OpenRouterService:
    """Get or create the OpenRouter service singleton."""
    global _openrouter_service
    if _openrouter_service is None:
        _openrouter_service = OpenRouterService(
            api_key=settings.OPENROUTER_API_KEY,
            model_name=settings.OPENROUTER_MODEL,
            temperature=settings.OPENROUTER_TEMPERATURE,
            max_tokens=settings.OPENROUTER_MAX_TOKENS,
        )
    return _openrouter_service
