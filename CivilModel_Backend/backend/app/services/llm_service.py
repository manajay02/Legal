"""
LLM service with multiple provider support.
Providers:
  - OpenRouter (cloud API - recommended for easy setup)
  - Ollama (local - for running trained model on GPU)
"""

import json
import time
from typing import Optional

import requests
from loguru import logger

from app.core.config import get_settings

settings = get_settings()


class LLMService:
    """Service for LLM inference with multiple provider support."""
    
    # Master System Prompt (same as used in training)
    MASTER_SYSTEM_PROMPT = """You are an expert Sri Lankan paralegal. Extract metadata and content from the OCR text of a Supreme Court judgment and return ONLY a valid JSON object.

RULES:
1. Return ONLY the JSON object. No explanatory text before or after.
2. Do NOT invent data. Use null for missing fields.
3. parties and judges must be flat lists of strings.
4. Divide content into logical sections.

Required JSON format:
{
  "metadata": {
    "case_number": "SC Appeal No. X/YYYY",
    "court": "Supreme Court of Sri Lanka",
    "date": "YYYY-MM-DD",
    "parties": ["Party 1", "Party 2"],
    "judges": ["Judge 1", "Judge 2"],
    "case_type": "Appeal"
  },
  "sections": [
    {"title": "Header and Case Details", "content": "..."},
    {"title": "Judgment and Legal Analysis", "content": "..."},
    {"title": "Conclusion and Order", "content": "..."}
  ]
}"""

    def __init__(self):
        """Initialize the LLM service based on configured provider."""
        self.settings = settings
        self.provider = self.settings.LLM_PROVIDER.lower()
        
        if self.provider == "openrouter":
            # OpenRouter API (cloud - easy setup)
            self.api_url = "https://openrouter.ai/api/v1/chat/completions"
            self.api_key = self.settings.OPENROUTER_API_KEY
            self.model = self.settings.OPENROUTER_MODEL
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "CivilCaseExtractor"
            }
            if not self.api_key:
                logger.warning("⚠️ OPENROUTER_API_KEY not set!")
                
        elif self.provider == "ollama":
            # Ollama API (local - for trained model)
            self.api_url = f"{self.settings.OLLAMA_BASE_URL}/api/chat"
            self.api_key = None  # No auth needed for local
            self.model = self.settings.OLLAMA_MODEL
            self.headers = {"Content-Type": "application/json"}
            logger.info(f"🦙 Using Ollama at {self.settings.OLLAMA_BASE_URL}")
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}. Use 'openrouter' or 'ollama'")
        
        logger.info(f"🤖 LLM Service initialized")
        logger.info(f"   Provider: {self.provider.upper()}")
        logger.info(f"   Model: {self.model}")

    def _call_openrouter(self, prompt: str, max_tokens: int = 2048) -> str:
        """Call OpenRouter API."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.MASTER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload,
            timeout=self.settings.LLM_TIMEOUT
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error ({response.status_code}): {response.text[:500]}")
        
        result = response.json()
        choices = result.get("choices", [])
        if not choices:
            raise Exception(f"No choices in response: {result}")
        
        return choices[0].get("message", {}).get("content", "").strip()

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama API."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.MASTER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }
        
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload,
            timeout=self.settings.LLM_TIMEOUT
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error ({response.status_code}): {response.text[:500]}")
        
        result = response.json()
        return result.get("message", {}).get("content", "").strip()

    def generate_response(self, prompt: str, max_retries: Optional[int] = None) -> str:
        """Generate a response from the LLM with retry logic."""
        max_retries = max_retries or self.settings.LLM_MAX_RETRIES
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Calling {self.provider.upper()} API (attempt {attempt}/{max_retries})...")
                
                if self.provider == "openrouter":
                    content = self._call_openrouter(prompt)
                elif self.provider == "ollama":
                    content = self._call_ollama(prompt)
                else:
                    raise Exception(f"Unknown provider: {self.provider}")
                
                if not content:
                    raise Exception("Empty response from model")
                
                logger.success(f"✅ Response received ({len(content)} chars)")
                return content
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️ Timeout (attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                raise Exception(f"Timeout after {max_retries} attempts")
                
            except requests.exceptions.ConnectionError as e:
                if self.provider == "ollama":
                    logger.error("❌ Cannot connect to Ollama. Is it running?")
                    logger.error("   Start with: ollama serve")
                raise Exception(f"Connection error: {e}")
                
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                raise
        
        raise Exception(f"Failed after {max_retries} attempts")

    def extract_document_data(self, ocr_text: str, max_text_length: int = 15000) -> str:
        """Extract structured data from OCR text."""
        # Truncate if too long (DeepSeek supports large context)
        if len(ocr_text) > max_text_length:
            truncated = ocr_text[:max_text_length]
            last_period = truncated.rfind('.')
            if last_period > max_text_length * 0.7:
                truncated = truncated[:last_period + 1]
            ocr_text = truncated
            logger.warning(f"⚠️ Text truncated to ~{max_text_length} chars")
        
        prompt = f"""DOCUMENT OCR TEXT:

{ocr_text}

Extract all metadata and sections from the above document. Return ONLY valid JSON."""
        
        return self.generate_response(prompt)
