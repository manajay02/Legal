"""
Inference Service for Legal Argument Critic
============================================

Supports dual backends:
- Gemini 2.5 Pro (API-based, works on any machine)
- Ollama (local, requires GPU for fine-tuned model)

Set INFERENCE_BACKEND in .env to switch between them.

Author: LegalScoreModel Team
Date: January 2026
"""

import json
import re
import logging
import os
import time
from typing import Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)


# Configuration from environment
INFERENCE_BACKEND = os.getenv("INFERENCE_BACKEND", "gemini").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "legal-critic")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")


# System prompt for legal argument critique
SYSTEM_PROMPT = """You are an expert legal argument critic for Sri Lankan civil cases.

Analyze the legal argument and respond with ONLY valid JSON in this exact format:
{
    "overall_score": <0-100>,
    "breakdown": [
        {"category": "Issue & Claim Clarity", "weight": 10, "rubric_score": <0-5>, "points": <weight*score/5>, "rationale": "<explanation>"},
        {"category": "Facts & Chronology", "weight": 15, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"},
        {"category": "Legal Basis", "weight": 20, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"},
        {"category": "Evidence & Support", "weight": 15, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"},
        {"category": "Reasoning & Logic", "weight": 15, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"},
        {"category": "Counterarguments", "weight": 10, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"},
        {"category": "Remedies & Quantification", "weight": 10, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"},
        {"category": "Structure & Professionalism", "weight": 5, "rubric_score": <0-5>, "points": <calculated>, "rationale": "<explanation>"}
    ],
    "feedback": ["<suggestion 1>", "<suggestion 2>", "<suggestion 3>"]
}

Scoring: 0=Missing, 1=Poor, 2=Below Average, 3=Average, 4=Good, 5=Excellent

IMPORTANT: Respond with ONLY the JSON object, no additional text."""


class GeminiBackend:
    """Gemini 2.5 Pro backend for inference."""
    
    def __init__(self):
        """Initialize Gemini backend."""
        logger.info("Initializing Gemini Backend...")
        
        if not GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY not set in .env")
        
        self.api_key = GOOGLE_API_KEY
        self.model = "gemini-2.5-pro"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        self.last_request_time = 0
        self.min_request_interval = 35  # 35 seconds between requests (2 RPM limit)
        
        logger.info(f"✓ Gemini backend ready (model: {self.model})")
    
    def _rate_limit(self):
        """Enforce rate limiting to avoid 429 errors."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            wait_time = self.min_request_interval - elapsed
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def generate(self, argument_text: str) -> str:
        """Generate critique using Gemini API."""
        self._rate_limit()
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_PROMPT}\n\nCritique this legal argument:\n\n{argument_text}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "maxOutputTokens": 2048
            }
        }
        
        headers = {"Content-Type": "application/json"}
        url = f"{self.api_url}?key={self.api_key}"
        
        for attempt in range(3):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=120)
                
                if response.status_code == 429:
                    wait = (attempt + 1) * 60  # Exponential backoff
                    logger.warning(f"Rate limited (429). Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                
                response.raise_for_status()
                
                data = response.json()
                content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return content
                
            except requests.exceptions.Timeout:
                logger.error(f"Timeout on attempt {attempt + 1}")
                if attempt == 2:
                    raise RuntimeError("Gemini API timeout after 3 attempts")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt == 2:
                    raise RuntimeError(f"Gemini API error: {str(e)}")
        
        raise RuntimeError("Failed to get response from Gemini")


class OpenRouterBackend:
    """OpenRouter backend for API inference with DeepSeek."""
    
    def __init__(self):
        """Initialize OpenRouter backend."""
        logger.info("Initializing OpenRouter Backend...")
        
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set in .env")
        
        self.api_key = OPENROUTER_API_KEY
        self.model = OPENROUTER_MODEL
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        logger.info(f"✓ OpenRouter backend ready (model: {self.model})")
    
    def generate(self, prompt: str) -> str:
        """Generate response using OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": float(os.getenv("OPENROUTER_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("OPENROUTER_MAX_TOKENS", "2048"))
        }
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=120
            )
            response.raise_for_status()
            
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content
            
        except requests.exceptions.Timeout:
            raise RuntimeError("OpenRouter API timeout")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenRouter API error: {str(e)}")


class OllamaBackend:
    """Ollama backend for local inference."""
    
    def __init__(self):
        """Initialize Ollama backend."""
        logger.info("Initializing Ollama Backend...")
        
        self.base_url = OLLAMA_BASE_URL
        self.model_name = OLLAMA_MODEL
        
        self._verify_connection()
        self._verify_model()
        
        logger.info(f"✓ Ollama backend ready (model: {self.model_name})")
    
    def _verify_connection(self):
        """Verify Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running: 'ollama serve'"
            )
    
    def _verify_model(self):
        """Verify the model is available in Ollama."""
        response = requests.get(f"{self.base_url}/api/tags", timeout=5)
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        
        model_found = any(self.model_name in name for name in model_names)
        
        if not model_found:
            raise RuntimeError(
                f"Model '{self.model_name}' not found in Ollama.\n"
                f"Available models: {model_names}"
            )
    
    def generate(self, argument_text: str) -> str:
        """Generate critique using Ollama."""
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Critique this legal argument:\n\n{argument_text}"}
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 2048
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=600
        )
        response.raise_for_status()
        
        return response.json().get("message", {}).get("content", "")


class InferenceService:
    """
    Unified inference service supporting multiple backends.
    
    Switch between backends by setting INFERENCE_BACKEND in .env:
    - "gemini": Use Gemini 2.5 Pro API (works everywhere)
    - "ollama": Use local Ollama with fine-tuned model (requires GPU)
    """
    
    def __init__(self):
        """Initialize the inference service with configured backend."""
        logger.info("=" * 60)
        logger.info("Initializing Inference Service")
        logger.info(f"Backend: {INFERENCE_BACKEND}")
        logger.info("=" * 60)
        
        self.backend_name = INFERENCE_BACKEND
        self.is_ready = False
        
        try:
            if INFERENCE_BACKEND == "openrouter":
                self.backend = OpenRouterBackend()
                self.device = "cloud"
            elif INFERENCE_BACKEND == "gemini":
                self.backend = GeminiBackend()
                self.device = "cloud"
            elif INFERENCE_BACKEND == "ollama":
                self.backend = OllamaBackend()
                self.device = "local"
            else:
                raise ValueError(f"Unknown backend: {INFERENCE_BACKEND}. Use 'openrouter', 'gemini', or 'ollama'")
            
            self.is_ready = True
            logger.info("✓ Model loaded and ready for inference")
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize: {str(e)}")
            raise
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from model response."""
        cleaned = text.strip()
        
        # Remove markdown fences
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        # Try direct parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try regex extraction
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            return None
    
    def _validate_critique(self, critique: Dict[str, Any]) -> bool:
        """Validate critique structure."""
        required = ["overall_score", "breakdown", "feedback"]
        if not all(k in critique for k in required):
            return False
        
        score = critique.get("overall_score")
        if not isinstance(score, (int, float)) or not (0 <= score <= 100):
            return False
        
        breakdown = critique.get("breakdown")
        if not isinstance(breakdown, list) or len(breakdown) != 8:
            return False
        
        feedback = critique.get("feedback")
        if not isinstance(feedback, list) or len(feedback) < 1:
            return False
        
        return True
    
    def generate_critique(self, argument_text: str) -> Dict[str, Any]:
        """
        Generate a critique for a legal argument.
        
        Args:
            argument_text: The legal argument to critique
            
        Returns:
            Dict with overall_score, breakdown, and feedback
        """
        if not argument_text or len(argument_text.strip()) < 10:
            raise ValueError("Argument text must be at least 10 characters long")
        
        logger.info(f"Generating critique ({len(argument_text)} chars) via {self.backend_name}")
        
        try:
            content = self.backend.generate(argument_text)
            critique = self._extract_json(content)
            
            if critique is None:
                return {
                    "error": "Failed to parse JSON from model response",
                    "raw_response": content[:500],
                    "overall_score": 0,
                    "breakdown": [],
                    "feedback": ["Model response could not be parsed. Please try again."]
                }
            
            if not self._validate_critique(critique):
                critique["warning"] = "Critique may have incomplete structure"
            
            logger.info(f"✓ Critique generated (score: {critique.get('overall_score', 'N/A')})")
            return critique
            
        except Exception as e:
            raise RuntimeError(str(e))


# Singleton instance
_inference_service: Optional[InferenceService] = None


def get_inference_service() -> InferenceService:
    """Get or create the inference service singleton."""
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService()
    return _inference_service
