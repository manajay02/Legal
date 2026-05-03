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
    
    # Master System Prompt — full structured legal extraction
    MASTER_SYSTEM_PROMPT = """You are an expert Sri Lankan paralegal AI. Extract structured legal data from the OCR text of a Supreme Court judgment and return ONLY a valid JSON object.

STRICT RULES:
1. Return ONLY the JSON object. No text, explanation, or markdown before or after it.
2. Do NOT invent data. Use null for any field that cannot be found in the document.
3. All list fields must be JSON arrays, even if only one item.
4. Confidence scores are integers 0-100 reflecting your certainty.
5. Dates may be YYYY-MM-DD, YYYY-MM, or YYYY — use whatever precision is available.
6. Section "text" fields must be concise summaries (3-6 sentences each), NOT verbatim copies of the text.

REQUIRED JSON FORMAT — fill EVERY field; null only if truly absent:
{
  "metadata": {
    "case_number": "SC Appeal No. X/YYYY",
    "court": "Supreme Court of Sri Lanka",
    "date": "YYYY-MM-DD",
    "year": 2012,
    "case_type": "Property Dispute | FR Application | Civil Appeal | Criminal Appeal | ...",
    "petitioners": ["Petitioner 1", "Petitioner 2"],
    "respondents": ["Respondent 1", "Respondent 2"],
    "parties": ["all petitioners and respondents combined"],
    "judges": ["Judge Name 1", "Judge Name 2"],
    "legal_provisions": ["Article 17 of the Constitution", "Section 66 of the Civil Procedure Code"],
    "page_count": null
  },
  "outcome": {
    "classification": "Allowed | Dismissed | Partially Allowed",
    "confidence": 88,
    "explanation": "The court allowed the appeal because ..."
  },
  "timeline": [
    {"event_name": "Case Filed", "date": "2012-03-15", "description": "Writ petition filed in the Court of Appeal", "event_type": "Filing"},
    {"event_name": "Supreme Court Hearing", "date": "2013", "description": "Leave to appeal granted", "event_type": "Hearing"},
    {"event_name": "Final Judgment", "date": "2014-07-22", "description": "Appeal allowed", "event_type": "Judgment"}
  ],
  "citations": [
    {"case_name": "Wijesinghe v. Attorney General", "year": "1998", "source": "1 SLR 100", "usage": "Precedent"},
    {"case_name": "Perera v. Perera", "year": "2001", "source": "NLR 245", "usage": "Reference"}
  ],
  "insights": {
    "key_legal_issues": ["Violation of fundamental rights", "Locus standi"],
    "reliefs_requested": "Writ of mandamus compelling respondent to ...",
    "reliefs_granted": "Appeal allowed, matter remanded to High Court",
    "state_involvement": true,
    "state_involvement_level": "High — multiple government departments named as respondents",
    "doctrines": ["Legitimate expectation", "Natural justice"],
    "risk_level": "High"
  },
  "confidence_scores": {
    "outcome": 90,
    "sections": 85,
    "citations": 78,
    "insights": 72
  },
  "sections": [
    {"title": "Header and Case Details", "text": "3-6 sentence summary of the header", "order_index": 1},
    {"title": "Case Overview / Background", "text": "3-6 sentence summary of the background", "order_index": 2},
    {"title": "Facts", "text": "3-6 sentence summary of key facts", "order_index": 3},
    {"title": "Legal Issues", "text": "3-6 sentence summary of legal issues", "order_index": 4},
    {"title": "Arguments", "text": "3-6 sentence summary of arguments", "order_index": 5},
    {"title": "Court Reasoning", "text": "3-6 sentence summary of court reasoning", "order_index": 6},
    {"title": "Decision and Orders", "text": "3-6 sentence summary of decision", "order_index": 7}
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

    def generate_response(self, prompt: str, max_retries: Optional[int] = None, max_tokens: int = 4096) -> str:
        """Generate a response from the LLM with retry logic."""
        max_retries = max_retries or self.settings.LLM_MAX_RETRIES
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Calling {self.provider.upper()} API (attempt {attempt}/{max_retries})...")
                
                if self.provider == "openrouter":
                    content = self._call_openrouter(prompt, max_tokens=max_tokens)
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

    def extract_document_data(self, ocr_text: str, max_text_length: int = None) -> str:
        """Extract full structured legal data (metadata, outcome, sections, timeline, citations, insights) from OCR text."""
        import re
        
        # Estimate max text length based on token limits
        # OpenRouter free tier: ~10k tokens, system prompt ~1500, output ~2500
        # So ~6000 tokens for document text, ~4 chars/token = 24000 chars
        # Use conservative estimate for free tier
        if max_text_length is None:
            max_text_length = 20000  # Safe limit for free tier (~5000 tokens)
        
        logger.info(f"Document text length: {len(ocr_text)} chars (limit: {max_text_length})")

        # Smart preprocessing: if the document has a very long party-address header section,
        # skip ahead to the actual judgment content to avoid wasting the context window.
        # Detect the "Before :" line (judges panel) as the start of judgment content.
        judgment_start_patterns = [
            r'Before\s*:\s*[A-Z]',
            r'BEFORE\s*:\s*[A-Z]',
            r'Argued on\s*:',
            r'ARGUED ON\s*:',
        ]
        judgment_start_idx = None
        for pattern in judgment_start_patterns:
            m = re.search(pattern, ocr_text)
            if m:
                # Only skip if this is far into the document (meaning a long header)
                if m.start() > len(ocr_text) * 0.3:
                    judgment_start_idx = m.start()
                    break

        if judgment_start_idx is not None:
            # Keep the first 2000 chars (case number / caption) + judgment content
            header_snippet = ocr_text[:2000]
            judgment_body = ocr_text[judgment_start_idx:]
            combined = header_snippet + "\n\n[... party address list omitted ...]\n\n" + judgment_body
            logger.info(f"Smart trim: header={judgment_start_idx} chars, body={len(judgment_body)} chars, combined={len(combined)} chars")
            ocr_text = combined

        # Truncate if still too long
        if len(ocr_text) > max_text_length:
            # For large documents, try to keep beginning and end (often most important)
            half_len = max_text_length // 2
            beginning = ocr_text[:half_len]
            ending = ocr_text[-half_len:]
            
            # Find sentence boundaries
            last_period_begin = beginning.rfind('.')
            first_period_end = ending.find('.')
            
            if last_period_begin > half_len * 0.7:
                beginning = beginning[:last_period_begin + 1]
            if first_period_end > 0 and first_period_end < half_len * 0.3:
                ending = ending[first_period_end + 1:]
            
            ocr_text = beginning + "\n\n[... middle section truncated due to length ...]\n\n" + ending
            logger.warning(f"⚠️ Text truncated to ~{len(ocr_text)} chars (keeping beginning and end)")

        prompt = f"""DOCUMENT OCR TEXT:

{ocr_text}

Extract ALL fields (metadata, outcome, timeline, citations, insights, confidence_scores, sections) from the above judgment. Return ONLY valid JSON matching the required format. Keep section "text" values as concise summaries (3-6 sentences), not verbatim copies."""

        return self.generate_response(prompt, max_tokens=2000)
