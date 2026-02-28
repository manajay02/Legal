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
SYSTEM_PROMPT = """You are a forensic legal argument evaluator for Sri Lankan civil cases.

You will receive a legal argument (ARGUMENT_TEXT). Score it across 8 categories.

=== FORENSIC EVALUATION RULES (MANDATORY) ===
For EVERY category you MUST:
  1. State the rubric score (0–5) and points calculation.
  2. Quote the EXACT sentence(s) from ARGUMENT_TEXT that justify the score —
     place this verbatim phrase in "argument_quote".
     If no relevant sentence exists, set "argument_quote" to empty string and
     reflect that absence in the gap bullets.
  3. In the "rationale" field write EXACTLY 3 sentences:
     Sentence 1 — What the argument DOES in this category (cite argument_quote).
     Sentence 2 — SPECIFICALLY what is missing, wrong, or weak that caused the
                  score to be X and not higher (name the exact gap).
     Sentence 3 — The CONCRETE action that would raise the score to a 4 or 5
                  (e.g. "To score 4/5 the argument must cite the relevant statute
                  by name and provide its section number").
     NEVER use vague phrases like "could be more polished" or "adequate support".
     NEVER write a one-sentence rationale.
  4. "strengths": 1–3 specific bullets of what the argument does well HERE.
  5. "gaps": 1–3 specific bullets of what is missing or weak HERE.
     Each gap must name the SPECIFIC element that is absent, not just say "lacks detail".
     Empty array only when rubric_score = 5.
  6. Each category MUST analyze a DIFFERENT legal dimension.
     Do NOT repeat the same reasoning across categories.

=== OUTPUT FORMAT (strict JSON only, no markdown, no extra text) ===
Every single breakdown object MUST have non-empty argument_quote, rationale,
strengths, and gaps (except judgment_quote which stays empty string here).
Do NOT leave any field as an empty string or empty array except judgment_quote.

{
    "overall_score": <integer 0-100>,
    "breakdown": [
        {
            "category": "Issue & Claim Clarity",
            "weight": 10,
            "rubric_score": <0-5>,
            "points": <weight*rubric_score/5 rounded 1dp>,
            "argument_quote": "<REQUIRED: verbatim sentence copied from ARGUMENT_TEXT most relevant to this category>",
            "judgment_quote": "",
            "rationale": "<REQUIRED 3 sentences: S1=what argument does here. S2=exactly what is wrong/missing that cost points. S3=concrete action to reach 4/5.>",
            "strengths": ["<REQUIRED: 1-3 specific bullets — what is done well>"],
            "gaps": ["<REQUIRED: 1-3 specific bullets — name the exact missing element>"]
        },
        {
            "category": "Facts & Chronology",
            "weight": 15, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "",
            "rationale": "<REQUIRED 3 sentences>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Legal Basis",
            "weight": 20, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "",
            "rationale": "<REQUIRED 3 sentences>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Evidence & Support",
            "weight": 15, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "",
            "rationale": "<REQUIRED 3 sentences>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Reasoning & Logic",
            "weight": 15, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "",
            "rationale": "<REQUIRED 3 sentences>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Counterarguments",
            "weight": 10, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument, or empty if completely absent>",
            "judgment_quote": "",
            "rationale": "<REQUIRED 3 sentences>",
            "strengths": ["<specific strength or 'None identified'>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Remedies & Quantification",
            "weight": 10, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "",
            "rationale": "<REQUIRED 3 sentences>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Structure & Professionalism",
            "weight": 5, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "",
            "rationale": "<REQUIRED 3 sentences>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        }
    ],
    "feedback": ["<actionable suggestion 1>", "<actionable suggestion 2>", "<actionable suggestion 3>"]
}

Scoring: 0=Missing, 1=Poor, 2=Below Average, 3=Average, 4=Good, 5=Excellent
overall_score = sum of all points.

CRITICAL REMINDER: A response where any rationale is one sentence, or any
argument_quote/strengths/gaps is empty (except as noted above), is INVALID
and will be rejected. Every field must be substantively filled.

IMPORTANT: Respond with ONLY the JSON object, no additional text."""


SYSTEM_PROMPT_GROUNDED = """You are a forensic legal argument evaluator for Sri Lankan civil cases.

You will receive:
  (1) SOURCE_JUDGMENT — numbered excerpts [E1], [E2] … from uploaded case documents / prior judgments.
  (2) ARGUMENT_TEXT — the legal argument to be scored.

=== FORENSIC EVALUATION RULES (ALL MANDATORY) ===
For EVERY category you MUST:

  1. ARGUMENT QUOTE — Copy the EXACT sentence(s) from ARGUMENT_TEXT that are most relevant
     to this category into "argument_quote".
     If the argument says nothing relevant to this category, set "argument_quote" to ""
     and note the absence in gaps.

  2. JUDGMENT QUOTE — Copy the EXACT sentence from SOURCE_JUDGMENT (one of the [E#] excerpts)
     that best supports or contradicts what the argument says into "judgment_quote".
     • You MUST also cite that excerpt's ID (e.g. [E2]) inside "rationale".
     • If NO excerpt is relevant, write exactly:
       "No supporting extract found in the source judgment for this claim."
     NEVER invent text that is not in the excerpts.

  3. RATIONALE — Write EXACTLY 3 sentences:
     Sentence 1 — What the argument DOES in this category (reference argument_quote
                  and cite [E#] where relevant).
     Sentence 2 — SPECIFICALLY what is missing or wrong that caused the score to be
                  X and NOT higher — name the exact gap and cite the [E#] excerpt
                  that shows what was expected.
     Sentence 3 — The CONCRETE action that would raise the score to 4 or 5
                  (e.g. "To score 4/5 the argument must cite the partition statute
                  by name and reproduce the boundary description from [E2]").
     NEVER write a one-sentence rationale.
     NEVER use vague phrases like "could be more polished" or "adequate support".
     EVERY rationale MUST contain at least one [E#] citation.
     For categories where the evaluated aspect is purely about the argument's own
     writing (e.g. Structure & Professionalism), cite the closest [E#] that shows
     how a properly structured legal submission looks in comparison.

  4. STRENGTHS — 1–3 specific bullets about what is done WELL in this category.

  5. GAPS — 1–3 specific bullets of what is MISSING or WEAK in this category.
     Empty array only when rubric_score = 5.

  6. Each category MUST analyze a DIFFERENT legal dimension.
     Do NOT reuse the same reasoning, quote, or evidence ID across multiple categories.

=== OUTPUT FORMAT (strict JSON only — no markdown fences, no extra text) ===
Every single breakdown object MUST have non-empty argument_quote, judgment_quote,
rationale, strengths, and gaps. Do NOT leave any field empty.

{
    "overall_score": <integer 0-100>,
    "breakdown": [
        {
            "category": "Issue & Claim Clarity",
            "weight": 10,
            "rubric_score": <0-5>,
            "points": <weight * rubric_score / 5, rounded to 1 decimal>,
            "argument_quote": "<REQUIRED: verbatim sentence copied from ARGUMENT_TEXT most relevant here>",
            "judgment_quote": "<REQUIRED: verbatim sentence from a [E#] excerpt, or exactly: 'No supporting extract found in the source judgment for this claim.'>",
            "rationale": "<REQUIRED 3 sentences: S1=what argument does here citing argument_quote + [E#]. S2=exactly what is wrong/missing and cite [E#] showing what was expected. S3=concrete action to reach 4/5.>",
            "strengths": ["<REQUIRED: 1-3 specific bullets>"],
            "gaps": ["<REQUIRED: 1-3 specific bullets naming the exact missing element>"]
        },
        {
            "category": "Facts & Chronology",
            "weight": 15, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "<REQUIRED verbatim from [E#] or no-extract message>",
            "rationale": "<REQUIRED 3 sentences citing [E#]>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Legal Basis",
            "weight": 20, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "<REQUIRED verbatim from [E#] or no-extract message>",
            "rationale": "<REQUIRED 3 sentences citing [E#]>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Evidence & Support",
            "weight": 15, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "<REQUIRED verbatim from [E#] or no-extract message>",
            "rationale": "<REQUIRED 3 sentences citing [E#]>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Reasoning & Logic",
            "weight": 15, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "<REQUIRED verbatim from [E#] or no-extract message>",
            "rationale": "<REQUIRED 3 sentences citing [E#]>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Counterarguments",
            "weight": 10, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence, or empty string if topic entirely absent>",
            "judgment_quote": "<REQUIRED verbatim from [E#] or no-extract message>",
            "rationale": "<REQUIRED 3 sentences citing [E#]>",
            "strengths": ["<specific strength or 'None identified'>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Remedies & Quantification",
            "weight": 10, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "<REQUIRED verbatim from [E#] or no-extract message>",
            "rationale": "<REQUIRED 3 sentences citing [E#]>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        },
        {
            "category": "Structure & Professionalism",
            "weight": 5, "rubric_score": <0-5>, "points": <calc>,
            "argument_quote": "<REQUIRED verbatim sentence from argument>",
            "judgment_quote": "<REQUIRED verbatim from [E#] or no-extract message>",
            "rationale": "<REQUIRED 3 sentences citing [E#]>",
            "strengths": ["<specific strength>"], "gaps": ["<specific gap>"]
        }
    ],
    "feedback": ["<actionable suggestion 1>", "<actionable suggestion 2>", "<actionable suggestion 3>"]
}

Scoring: 0=Missing, 1=Poor, 2=Below Average, 3=Average, 4=Good, 5=Excellent
overall_score = sum of all points (0-100).

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
    
    def _call_api(self, system_instruction: str, user_text: str,
                   temperature: float = 0.7) -> str:
        """Low-level Gemini API call supporting an explicit system instruction."""
        self._rate_limit()
        payload = {
            # systemInstruction is the correct Gemini field for a persistent
            # instruction that the model must follow throughout the conversation.
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": user_text}]}
            ],
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.9,
                "maxOutputTokens": 8192,
            },
        }
        headers = {"Content-Type": "application/json"}
        url = f"{self.api_url}?key={self.api_key}"
        for attempt in range(3):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=120)
                if response.status_code == 429:
                    wait = (attempt + 1) * 60
                    logger.warning(f"Rate limited (429). Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                data = response.json()
                return (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
            except requests.exceptions.Timeout:
                logger.error(f"Timeout on attempt {attempt + 1}")
                if attempt == 2:
                    raise RuntimeError("Gemini API timeout after 3 attempts")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt == 2:
                    raise RuntimeError(f"Gemini API error: {str(e)}")
        raise RuntimeError("Failed to get response from Gemini")

    def generate(self, argument_text: str) -> str:
        """Generate a basic (non-grounded) critique using Gemini API."""
        user_text = (
            "=== ARGUMENT_TEXT ===\n"
            f"{argument_text}\n\n"
            "MANDATORY OUTPUT REMINDER:\n"
            "For EVERY category in breakdown you MUST fill:\n"
            "  - argument_quote: copy-paste the most relevant sentence from ARGUMENT_TEXT above\n"
            "  - rationale: exactly 3 sentences (what argument does, what is missing/wrong, what action raises to 4/5)\n"
            "  - strengths: list of 1-3 specific bullets (what was done well)\n"
            "  - gaps: list of 1-3 specific bullets (exact missing elements)\n"
            "Any category with empty argument_quote, empty strengths, or empty gaps is INVALID."
        )
        return self._call_api(SYSTEM_PROMPT, user_text, temperature=0.2)

    def generate_grounded(self, user_text: str) -> str:
        """Generate a grounded critique (evidence citations required) using Gemini API."""
        return self._call_api(SYSTEM_PROMPT_GROUNDED, user_text, temperature=0.2)


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
    
    def generate(self, argument_text: str) -> str:
        """Generate response using OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        user_prompt = f"Critique this legal argument:\n\n{argument_text}"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
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
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"OpenRouter API error ({response.status_code}): {error_detail}")
                raise RuntimeError(f"OpenRouter API error: {response.status_code} - {error_detail}")
            
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not content:
                logger.error(f"Empty response from OpenRouter: {data}")
                raise RuntimeError("Empty response from OpenRouter API")
            
            return content
            
        except requests.exceptions.Timeout:
            logger.error("OpenRouter API timeout")
            raise RuntimeError("OpenRouter API timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter request error: {str(e)}")
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
                logger.warning(f"Failed to parse model response (len={len(content)}). First 500 chars: {content[:500]!r}")
                return self._get_fallback_critique(argument_text)
            
            if not self._validate_critique(critique):
                critique["warning"] = "Critique may have incomplete structure"
            
            # Fill any empty fields the model skipped
            critique = self._enrich_breakdown(critique, argument_text)
            
            logger.info(f"✓ Critique generated (score: {critique.get('overall_score', 'N/A')})")
            return critique
            
        except Exception as e:
            logger.error(f"Error generating critique: {str(e)}")
            return self._get_fallback_critique(argument_text)

    def generate_grounded_critique(self, argument_text: str, evidence_pack: str) -> Dict[str, Any]:
        """Generate a grounded critique using provided evidence excerpts.

        The evidence_pack is appended to the user prompt; the model is instructed
        to cite evidence ids like [E1] in rationales.
        """
        if not argument_text or len(argument_text.strip()) < 10:
            raise ValueError("Argument text must be at least 10 characters long")

        logger.info(
            f"Generating GROUNDED critique ({len(argument_text)} chars, evidence {len(evidence_pack)} chars) via {self.backend_name}"
        )

        try:
            # ── Build user prompt ────────────────────────────────────────────
            # Re-number the evidence pack lines for extra clarity and add a
            # reinforcement reminder right before the argument text.
            user_prompt = (
                "=== SOURCE_JUDGMENT ===\n"
                "The following numbered excerpts are the source judgment / supporting documents.\n"
                "For each category you MUST quote the exact sentence(s) from these excerpts\n"
                "that support or contradict the argument, citing [E#].\n"
                "If no relevant extract exists, write: \'No supporting extract found in the judgment for this claim.\'\n\n"
                f"{evidence_pack}\n\n"
                "=== ARGUMENT_TEXT ===\n"
                f"{argument_text}\n\n"
                "SCORING REMINDER:\n"
                "- Every rationale MUST cite at least one [E#] from SOURCE_JUDGMENT above.\n"
                "- Every rationale MUST quote a specific phrase from ARGUMENT_TEXT in \'argument_quote\'.\n"
                "- Every rationale MUST quote a specific phrase from SOURCE_JUDGMENT in \'judgment_quote\'.\n"
                "- Do NOT repeat the same reasoning across different categories.\n"
                "- Do NOT use vague phrases without textual proof."
            )

            # ── Dispatch to correct backend ──────────────────────────────────
            if self.backend_name == "gemini":
                # Use the dedicated grounded method that sends systemInstruction
                # via the proper Gemini API field (not concatenated text).
                content = self.backend.generate_grounded(user_prompt)

            elif self.backend_name == "openrouter":
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT_GROUNDED},
                        {"role": "user",   "content": user_prompt},
                    ],
                    "temperature": float(os.getenv("OPENROUTER_TEMPERATURE", "0.4")),
                    "max_tokens": int(os.getenv("OPENROUTER_MAX_TOKENS", "2048")),
                }
                resp = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload, headers=headers, timeout=120,
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"OpenRouter API error: {resp.status_code} - {resp.text}")
                content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")

            elif self.backend_name == "ollama":
                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT_GROUNDED},
                        {"role": "user",   "content": user_prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.4, "top_p": 0.9, "num_predict": 2048},
                }
                resp = requests.post(
                    f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=600,
                )
                resp.raise_for_status()
                content = resp.json().get("message", {}).get("content", "")

            else:
                raise RuntimeError(f"Unknown backend: {self.backend_name}")

            # Log raw response for debugging citation issues
            logger.debug(f"[GROUNDED RAW RESPONSE snippet]: {content[:400]!r}")

            critique = self._extract_json(content)
            if critique is None:
                fallback = self._get_fallback_critique(argument_text)
                fallback["warning"] = (
                    "Failed to parse grounded model response; using fallback critique without evidence citations."
                )
                return fallback

            if not self._validate_critique(critique):
                critique["warning"] = "Critique may have incomplete structure (grounded mode)"

            # ── Post-process: guarantee every rationale has at least one [E#] ──
            critique = self._inject_missing_citations(critique, evidence_pack)

            # Fill any empty fields the model skipped
            critique = self._enrich_breakdown(critique, argument_text)

            return critique

        except Exception as e:
            logger.error(f"Error generating grounded critique: {str(e)}")
            fallback = self._get_fallback_critique(argument_text)
            fallback["warning"] = (
                "AI service unavailable in grounded mode - using basic analysis without evidence citations."
            )
            return fallback

    # ------------------------------------------------------------------
    # Breakdown enrichment — fills empty fields the model may have skipped
    # ------------------------------------------------------------------

    def _enrich_breakdown(self, critique: Dict[str, Any], argument_text: str) -> Dict[str, Any]:
        """Post-process: for any category where argument_quote / strengths / gaps
        are missing or empty, derive them programmatically from the rationale
        text and the argument text so the frontend always has content to show."""
        import re as _re

        # ── Build sentence list — try punctuation split, then newline, then words ──
        raw_sentences = _re.split(r'(?<=[.!?])\s+|\n{1,}', argument_text.strip())
        arg_sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 12]
        # Last resort: chunk into ~80-char pieces so we always have something to quote
        if not arg_sentences:
            words = argument_text.split()
            arg_sentences = [" ".join(words[i:i+15]) for i in range(0, len(words), 15) if words[i:i+15]]
        if not arg_sentences:
            arg_sentences = [argument_text[:200]] if argument_text.strip() else ["(no argument text provided)"]

        def best_arg_sentence(rationale: str) -> str:
            """Return the argument sentence with highest word overlap to the rationale."""
            words = set(_re.findall(r'[a-z]{4,}', rationale.lower()))
            if not words:
                return arg_sentences[0]
            best, best_score = arg_sentences[0], -1
            for s in arg_sentences:
                s_words = set(_re.findall(r'[a-z]{4,}', s.lower()))
                score = len(words & s_words)
                if score > best_score:
                    best_score, best = score, s
            # Trim to reasonable quote length
            return best[:250]

        def split_rationale(rationale: str) -> list:
            """Split rationale into sentences, falling back to period-separated chunks."""
            parts = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', rationale) if s.strip()]
            if len(parts) < 2:
                # Try splitting at '. ' even without trailing space
                parts = [s.strip() for s in rationale.split('. ') if s.strip()]
            return parts

        def extract_strengths(rationale: str, category: str) -> list:
            """Extract positive part of rationale as a strength bullet."""
            parts = split_rationale(rationale)
            # Look for the sentence that starts with a positive/descriptive phrase
            pos_keywords = ['state', 'mention', 'include', 'address', 'identify',
                            'present', 'provide', 'contain', 'refer', 'note']
            for p in parts:
                if any(p.lower().startswith(k) or f' {k}' in p.lower() for k in pos_keywords):
                    return [p[:220]]
            # Default: first sentence = describes what IS there
            return [(parts[0] if parts else f"The {category} aspect is addressed.")[:220]]

        def extract_gaps(rationale: str, category: str) -> list:
            """Extract what-is-missing and how-to-fix sentences as gap bullets."""
            parts = split_rationale(rationale)
            gaps_out = []
            gap_keywords = ['missing', 'without', 'not', 'lack', 'absent', 'fail',
                            'no ', 'does not', 'does not', 'insufficient', 'unclear', 'vague']
            fix_keywords = ['to reach', 'to score', 'must', 'should', 'would', 'add', 'include',
                            'provide', 'cite', 'state', 'specify']
            for p in parts:
                pl = p.lower()
                if any(k in pl for k in gap_keywords) and len(gaps_out) < 2:
                    gaps_out.append(p[:220])
                elif any(k in pl for k in fix_keywords) and len(gaps_out) < 2:
                    gaps_out.append(p[:220])
            if not gaps_out and len(parts) >= 2:
                gaps_out = [p[:220] for p in parts[1:3]]
            if not gaps_out:
                gaps_out = [f"The {category} section needs more specific detail and citation."]
            return gaps_out[:2]

        enriched = 0
        for item in critique.get("breakdown", []):
            rationale = item.get("rationale", "") or ""
            cat = item.get("category", "this category")

            # argument_quote — always fill if empty
            if not str(item.get("argument_quote", "")).strip():
                item["argument_quote"] = best_arg_sentence(rationale)
                enriched += 1

            # strengths
            existing_strengths = item.get("strengths", [])
            if not isinstance(existing_strengths, list) or not any(str(s).strip() for s in existing_strengths):
                item["strengths"] = extract_strengths(rationale, cat)
                enriched += 1

            # gaps
            existing_gaps = item.get("gaps", [])
            if not isinstance(existing_gaps, list) or not any(str(g).strip() for g in existing_gaps):
                item["gaps"] = extract_gaps(rationale, cat)
                enriched += 1

        if enriched:
            logger.info(f"[enrich] Auto-filled {enriched} empty field(s) across breakdown categories.")

        return critique

    # ------------------------------------------------------------------
    # Citation injection helper
    # ------------------------------------------------------------------

    def _inject_missing_citations(self, critique: Dict[str, Any], evidence_pack: str) -> Dict[str, Any]:
        """Post-process the model response.

        Any breakdown rationale that contains no [E#] tag gets the most
        textually-relevant evidence ID appended automatically, so the
        frontend can always show evidence in the accordion.
        """
        import re as _re

        # ── 1. Parse evidence pack into {id: text} ─────────────────────
        # Evidence pack lines look like:
        #   [E1] source=uploaded_doc title=... score=0.121\n<excerpt>\n
        ev_map: Dict[str, str] = {}
        current_id: str | None = None
        current_lines: list[str] = []

        for line in evidence_pack.splitlines():
            header = _re.match(r'^\[(E\d+)\]', line)
            if header:
                if current_id:
                    ev_map[current_id] = " ".join(current_lines).lower()
                current_id = header.group(1)
                # strip the header prefix; keep rest of line as first content
                rest = line[header.end():].strip()
                current_lines = [rest] if rest else []
            else:
                if current_id:
                    current_lines.append(line.strip())

        if current_id:
            ev_map[current_id] = " ".join(current_lines).lower()

        if not ev_map:
            return critique   # no evidence to cite, nothing to do

        ev_ids = list(ev_map.keys())   # ordered list, e.g. ['E1','E2','E3']

        # ── 2. Best-match function ──────────────────────────────────────
        def best_ev_id_for(rationale_text: str) -> str:
            """Return the evidence ID whose excerpt has the most word overlap
            with the rationale text (simple bag-of-words)."""
            words = set(_re.findall(r'[a-z]{4,}', rationale_text.lower()))
            best_id, best_score = ev_ids[0], -1
            for eid, ev_text in ev_map.items():
                ev_words = set(_re.findall(r'[a-z]{4,}', ev_text))
                score = len(words & ev_words)
                if score > best_score:
                    best_score, best_id = score, eid
            return best_id

        # ── 3. Inject into any uncited rationale ───────────────────────
        citation_re = _re.compile(r'\[E\d+\]', _re.IGNORECASE)
        injected = 0
        for item in critique.get("breakdown", []):
            rationale = item.get("rationale", "")
            if not citation_re.search(rationale):
                eid = best_ev_id_for(rationale)
                item["rationale"] = (
                    rationale.rstrip()
                    + f" (See [{eid}] for the most relevant supporting excerpt.)"
                )
                injected += 1

        if injected:
            logger.info(f"[citation-inject] Injected citations into {injected} rationale(s).")

        return critique

    def _get_fallback_critique(self, argument_text: str) -> Dict[str, Any]:
        """Generate a basic fallback critique when API fails.
        Runs _enrich_breakdown so the frontend always has argument_quote/strengths/gaps."""
        word_count = len(argument_text.split())
        has_citations = bool(re.search(r'\d{4}|Act|Section|Article', argument_text))
        has_facts = bool(re.search(r'fact|evidence|witness|document', argument_text, re.IGNORECASE))

        base_score = 50
        if word_count > 100: base_score += 10
        if has_citations: base_score += 10
        if has_facts: base_score += 5

        critique = {
            "overall_score": min(base_score, 75),
            "breakdown": [
                {
                    "category": "Issue & Claim Clarity", "weight": 10, "rubric_score": 3, "points": 6.0,
                    "argument_quote": "", "judgment_quote": "",
                    "rationale": "The legal issue is introduced but the specific claim is not stated with enough precision for a court to act on it. The argument does not name the exact legal right being asserted or the specific relief being sought, which costs points under this criterion. To reach 4/5 the argument must open with a single sentence that names the cause of action, the parties, and the specific legal right violated.",
                    "strengths": ["A legal topic is identified and the general subject matter is clear."],
                    "gaps": ["The specific cause of action (e.g. breach of contract, negligence) is not named explicitly.", "The prayer or relief sought is not stated in the opening section."]
                },
                {
                    "category": "Facts & Chronology", "weight": 15, "rubric_score": 3, "points": 9.0,
                    "argument_quote": "", "judgment_quote": "",
                    "rationale": "Some factual background is present but the events are not arranged in a clear dated sequence. The absence of a numbered chronology makes it difficult for the reader to follow the timeline of events, which reduces the score. To reach 4/5 each factual paragraph must begin with a date or period (e.g. 'On 12 March 2019…') and facts must be listed in chronological order.",
                    "strengths": ["Key facts relevant to the dispute are mentioned."],
                    "gaps": ["Events are not presented in dated chronological order.", "Missing: specific dates for each key event."]
                },
                {
                    "category": "Legal Basis", "weight": 20, "rubric_score": 3, "points": 12.0,
                    "argument_quote": "", "judgment_quote": "",
                    "rationale": "Legal principles are referenced in general terms but no statute is cited by its short title, year, and section number. Without a specific statutory or case-law citation the court cannot verify the legal basis, which keeps the score at 3/5. To reach 4/5 each legal proposition must be followed by a citation in the form 'Section X of Act No. Y of YYYY' or 'Name v Name [YEAR] X SC Y'.",
                    "strengths": ["The argument attempts to ground the claim in law rather than mere assertion."],
                    "gaps": ["No statute cited by name, year, and section number.", "No case law cited to support the legal propositions."]
                },
                {
                    "category": "Evidence & Support", "weight": 15, "rubric_score": 3, "points": 9.0,
                    "argument_quote": "", "judgment_quote": "",
                    "rationale": "The argument refers to evidence but does not exhibit or describe specific documents by name. Saying 'there is evidence' without naming the document, document number, or date gives the reader no way to locate or verify it. To reach 4/5 each piece of evidence must be referred to as a named exhibit (e.g. 'P1 — Survey Plan No. 123 dated 2018') with its relevance explained.",
                    "strengths": ["The argument acknowledges that evidence exists to support the claim."],
                    "gaps": ["No documents are referred to by exhibit number or document description.", "The probative value of each piece of evidence is not explained."]
                },
                {
                    "category": "Reasoning & Logic", "weight": 15, "rubric_score": 3, "points": 9.0,
                    "argument_quote": "", "judgment_quote": "",
                    "rationale": "A logical sequence is attempted but the argument jumps between facts and conclusions without showing the inferential steps. The reader must infer the connection between the facts and the legal consequence, which should be made explicit. To reach 4/5 each factual paragraph must be followed by a sentence that states 'Therefore, under Section X, the [party] is entitled to…'.",
                    "strengths": ["The overall argument moves from facts toward a conclusion."],
                    "gaps": ["Inferential steps between facts and legal conclusions are not spelled out.", "The argument does not apply legal elements to specific facts one by one."]
                },
                {
                    "category": "Counterarguments", "weight": 10, "rubric_score": 2, "points": 4.0,
                    "argument_quote": "", "judgment_quote": "",
                    "rationale": "The argument does not address any opposing argument the defendant is likely to raise. In adversarial proceedings, failing to anticipate the other side's strongest point leaves the argument vulnerable to being dismissed. To reach 4/5 the argument must identify at least one likely defence (e.g. 'The defendant may argue that the limitation period has expired') and rebut it.",
                    "strengths": ["The argument presents a clear petitioner's position."],
                    "gaps": ["No anticipated defence or counter-argument is identified.", "No rebuttal section is present."]
                },
                {
                    "category": "Remedies & Quantification", "weight": 10, "rubric_score": 3, "points": 6.0,
                    "argument_quote": "", "judgment_quote": "",
                    "rationale": "A remedy is mentioned but it is not quantified with a specific amount or calculation. Courts require a precise sum or a defined act to grant relief, so an unquantified remedy weakens the prayer. To reach 4/5 the prayer must state the exact sum sought (e.g. 'LKR 2,500,000 as general damages') or the specific act required (e.g. 'delivery of vacant possession within 30 days').",
                    "strengths": ["The type of remedy sought (damages / declaration / injunction) is indicated."],
                    "gaps": ["The monetary amount is not specified or calculated.", "The basis of calculation (e.g. market value, loss of income) is not stated."]
                },
                {
                    "category": "Structure & Professionalism", "weight": 5, "rubric_score": 3, "points": 3.0,
                    "argument_quote": "", "judgment_quote": "",
                    "rationale": "The submission is written in prose but lacks the numbered-paragraph format expected in Sri Lankan civil pleadings. Without numbered paragraphs opposing counsel and the court cannot refer to specific passages precisely, which reduces the professionalism score. To reach 4/5 the entire submission must use numbered paragraphs, a bold heading for each section, and a separate signed prayer at the end.",
                    "strengths": ["The language is generally professional and avoids colloquial expressions."],
                    "gaps": ["Paragraphs are not numbered, making cross-reference difficult.", "No separate 'Prayer for Relief' section appears at the end of the submission."]
                }
            ],
            "feedback": [
                "Open each legal claim with the exact statute and section number that creates the right (e.g. 'Under Section 5 of the Partition Law No. 21 of 1977…').",
                "Number every paragraph and add a bold heading for each section (Facts, Legal Basis, Reliefs Sought).",
                "Add a final 'Prayer' section listing each remedy with a precise monetary amount or defined act."
            ],
            "warning": "AI service unavailable — using structured template analysis. Configure valid API keys in .env for full AI critique."
        }
        # Enrich argument_quotes from the actual argument text
        return self._enrich_breakdown(critique, argument_text)


# Singleton instance
_inference_service: Optional[InferenceService] = None


def get_inference_service() -> InferenceService:
    """Get or create the inference service singleton."""
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService()
    return _inference_service
