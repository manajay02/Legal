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


CLAIM_SUPPORT_SYSTEM_PROMPT = """You are a legal argument grounding assistant for Sri Lankan civil cases.

You will receive:
  (A) SOURCE_EXCERPTS — labelled excerpt tuples from a source judgment or evidence set.
      Labels take the form "Para N:", "Excerpt N:", "E1:", "E2:", etc.
  (B) ARGUMENT_CATEGORIES — the scored categories from a legal argument evaluation.

Your task for EACH category:
1. Identify 2–4 distinct atomic CLAIMS made or implied in that category's argument_quote and rationale.
2. For each claim, find the best matching excerpt in SOURCE_EXCERPTS and write a single bullet:
       "<label> → <one sentence from that excerpt that supports or contradicts the claim>"
   Use the EXACT label as it appears in SOURCE_EXCERPTS (e.g. "Para 10", "Excerpt 3", "E2").
   If NO excerpt matches a claim, record that claim in "not_referenced".
3. Count total_claims and supported_claims (those that matched an excerpt).
4. Compute support_ratio_percent = round(supported_claims / total_claims * 100) clamped to [0,100].
5. Assign support_ratio_label: "High" (≥75%), "Moderate" (40–74%), "Low" (<40%).

IMPORTANT RULES:
- The label in each bullet MUST be one that actually appears in SOURCE_EXCERPTS — never invent labels.
- Bullets must quote a real phrase from that excerpt; do not paraphrase beyond 15 words.
- If SOURCE_EXCERPTS is empty or irrelevant to a category, all claims go to "not_referenced".
- Output STRICTLY valid JSON, no markdown, no extra commentary.
- Skip categories that are purely about formatting or document structure (e.g. "Structure & Professionalism") — omit them from the output or return empty bullets.

OUTPUT FORMAT (repeat for each applicable category):
{
  "claim_support": [
    {
      "category": "<exact category name>",
      "bullets": ["Para 10 → <phrase>", "Excerpt 3 → <phrase>"],
      "total_claims": <int>,
      "supported_claims": <int>,
      "support_ratio_percent": <0-100>,
      "support_ratio_label": "High|Moderate|Low",
      "not_referenced": ["<unsupported claim text>"]
    }
  ]
}"""


class GeminiBackend:
    """Gemini 2.5 Pro backend for inference."""
    
    def __init__(self):
        """Initialize Gemini backend."""
        logger.info("Initializing Gemini Backend...")
        
        if not GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY not set in .env")
        
        self.api_key = GOOGLE_API_KEY
        self.model = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-lite")
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        self.last_request_time = 0
        # gemini-2.0-flash-lite: 30 RPM free tier → 2s interval is safe
        # gemini-2.5-pro: 2 RPM → needs 35s; kept as fallback
        self.min_request_interval = 2 if "flash" in self.model else 35
        
        logger.info(f"Gemini backend ready (model: {self.model}, interval: {self.min_request_interval}s)")
    
    def _rate_limit(self):
        """Enforce rate limiting to avoid 429 errors.

        IMPORTANT: We only advance last_request_time after a successful API
        response (see _call_api). This avoids long sleeps when requests fail
        and the app immediately falls back.
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            wait_time = self.min_request_interval - elapsed
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
    
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
                "maxOutputTokens": 4096,
            },
        }
        headers = {"Content-Type": "application/json"}
        url = f"{self.api_url}?key={self.api_key}"
        for attempt in range(3):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=120)
                if response.status_code == 429:
                    # Quota exhausted — don't wait; raise immediately so the
                    # caller can fall through to the fallback backend.
                    raise RuntimeError("Gemini API quota exceeded (429). Switch INFERENCE_BACKEND to openrouter.")
                response.raise_for_status()
                data = response.json()
                # Mark successful request for rate limiting.
                self.last_request_time = time.time()
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
    
    def _post(self, messages: list, max_tokens: int = None, temperature: float = None) -> str:
        """Make a chat completion request, falling back to user-merged prompt if system role unsupported."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else float(os.getenv("OPENROUTER_TEMPERATURE", "0.7")),
            "max_tokens": max_tokens if max_tokens is not None else int(os.getenv("OPENROUTER_MAX_TOKENS", "2048")),
        }
        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=120)
        except requests.exceptions.Timeout:
            raise RuntimeError("OpenRouter API timeout")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenRouter API error: {e}")

        if response.status_code == 400 and "developer instruction" in response.text.lower():
            # Model does not support system role — merge system+user into single user message
            merged_user = ""
            for msg in messages:
                if msg["role"] == "system":
                    merged_user += msg["content"] + "\n\n"
                else:
                    merged_user += msg["content"]
            payload["messages"] = [{"role": "user", "content": merged_user.strip()}]
            try:
                response = requests.post(self.base_url, json=payload, headers=headers, timeout=120)
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"OpenRouter API error: {e}")

        if response.status_code == 429:
            raise RuntimeError(f"OpenRouter rate limited (429): {response.text[:200]}")

        if response.status_code != 200:
            raise RuntimeError(f"OpenRouter API error: {response.status_code} - {response.text[:300]}")

        content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            raise RuntimeError("Empty response from OpenRouter API")
        return content

    def generate(self, argument_text: str) -> str:
        """Generate response using OpenRouter API."""
        user_prompt = f"Critique this legal argument:\n\n{argument_text}"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        return self._post(messages)


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

            if isinstance(critique, dict):
                _wt_dbg = str(critique.get("warning") or "")
                _bd_dbg = critique.get("breakdown") if isinstance(critique.get("breakdown"), list) else []
                _r0_dbg = str(((_bd_dbg[0] if _bd_dbg else {}) or {}).get("rationale") or "")
                logger.info(f"[debug] parsed warning={_wt_dbg[:80]!r} r0={_r0_dbg[:60]!r}")

            # Some upstream paths can return a fully-structured *template* JSON
            # with generic rationales (same across inputs) along with a warning
            # like "AI service unavailable...". Prefer our rule-based fallback
            # which ties rationales to the user's text and avoids repetition.
            if isinstance(critique, dict):
                wt = str(critique.get("warning") or "")
                breakdown = critique.get("breakdown") if isinstance(critique.get("breakdown"), list) else []
                r0 = str((breakdown[0] if breakdown else {}).get("rationale") or "")
                if (
                    "ai service unavailable" in wt.lower()
                    and "[rule_fallback_v2]" not in wt
                    and not r0.lower().startswith("your text says:")
                ):
                    critique = self._get_fallback_critique(argument_text)
            
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

            # If the configured backend fails (common: Gemini quota / network),
            # try OpenRouter as a secondary backend when it is configured.
            if self.backend_name != "openrouter" and OPENROUTER_API_KEY:
                try:
                    logger.warning("Primary backend failed; attempting OpenRouter fallback backend...")
                    alt_backend = OpenRouterBackend()
                    alt_content = alt_backend.generate(argument_text)
                    alt_critique = self._extract_json(alt_content)
                    if alt_critique is not None and self._validate_critique(alt_critique):
                        alt_critique = self._enrich_breakdown(alt_critique, argument_text)
                        alt_critique["warning"] = (
                            "Primary backend failed; used OpenRouter fallback backend for this response."
                        )
                        logger.info(
                            f"✓ Critique generated via OpenRouter fallback (score: {alt_critique.get('overall_score', 'N/A')})"
                        )
                        return alt_critique
                    logger.warning("OpenRouter fallback returned invalid structure; using template fallback.")
                except Exception as alt_e:
                    logger.warning(f"OpenRouter fallback backend failed: {alt_e}")

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
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT_GROUNDED},
                    {"role": "user",   "content": user_prompt},
                ]
                content = self.backend._post(messages, temperature=0.4)

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

            # Same as non-grounded: if we got a template JSON with an
            # AI-unavailable warning and generic rationales, replace it with
            # the rule-based fallback so outputs vary by input.
            if isinstance(critique, dict):
                wt = str(critique.get("warning") or "")
                breakdown = critique.get("breakdown") if isinstance(critique.get("breakdown"), list) else []
                r0 = str((breakdown[0] if breakdown else {}).get("rationale") or "")
                if (
                    "ai service unavailable" in wt.lower()
                    and "[rule_fallback_v2]" not in wt
                    and not r0.lower().startswith("your text says:")
                ):
                    critique = self._get_fallback_critique(argument_text)
            if critique is None:
                fallback = self._get_fallback_critique(argument_text)
                # Even in fallback mode, keep the UX consistent: inject at least
                # one [E#] citation per category when evidence_pack is present
                # so the frontend can show the supporting excerpts.
                try:
                    fallback = self._inject_missing_citations(fallback, evidence_pack)
                except Exception as _e:
                    logger.debug(f"[citation-inject] Skipped for fallback critique: {_e}")
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

            # Secondary attempt: OpenRouter grounded path (if configured)
            if self.backend_name != "openrouter" and OPENROUTER_API_KEY:
                try:
                    logger.warning("Primary grounded backend failed; attempting OpenRouter grounded fallback...")
                    alt_or = OpenRouterBackend()
                    # Rebuild the same user prompt used in the main path.
                    user_prompt = (
                        "=== SOURCE_JUDGMENT ===\n"
                        "The following numbered excerpts are the source judgment / supporting documents.\n"
                        "For each category you MUST quote the exact sentence(s) from these excerpts\n"
                        "that support or contradict the argument, citing [E#].\n"
                        "If no relevant extract exists, write: 'No supporting extract found in the judgment for this claim.'\n\n"
                        f"{evidence_pack}\n\n"
                        "=== ARGUMENT_TEXT ===\n"
                        f"{argument_text}\n\n"
                        "SCORING REMINDER:\n"
                        "- Every rationale MUST cite at least one [E#] from SOURCE_JUDGMENT above.\n"
                        "- Every rationale MUST quote a specific phrase from ARGUMENT_TEXT in 'argument_quote'.\n"
                        "- Every rationale MUST quote a specific phrase from SOURCE_JUDGMENT in 'judgment_quote'.\n"
                        "- Do NOT repeat the same reasoning across different categories.\n"
                        "- Do NOT use vague phrases without textual proof."
                    )
                    content = alt_or._post(
                        [{"role": "system", "content": SYSTEM_PROMPT_GROUNDED}, {"role": "user", "content": user_prompt}],
                        temperature=0.4,
                    )
                    alt_critique = self._extract_json(content)
                    if alt_critique is not None and self._validate_critique(alt_critique):
                        alt_critique = self._inject_missing_citations(alt_critique, evidence_pack)
                        alt_critique = self._enrich_breakdown(alt_critique, argument_text)
                        alt_critique["warning"] = (
                            "Primary backend failed; used OpenRouter grounded fallback backend for this response."
                        )
                        return alt_critique
                    logger.warning("OpenRouter grounded fallback returned invalid structure; using template fallback.")
                except Exception as alt_e:
                    logger.warning(f"OpenRouter grounded fallback failed: {alt_e}")

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

        warning_text = str(critique.get("warning") or "")
        # Some fallback paths still return a fully structured response with
        # template rationales that look identical across different inputs.
        # When we detect that mode, force argument-specific rationales tied to
        # the extracted argument_quote.
        force_argument_specific_rationales = "ai service unavailable" in warning_text.lower()
        if force_argument_specific_rationales:
            logger.info("[enrich] Detected AI-unavailable mode; forcing argument-specific rationales.")

        def _norm_ws(s: str) -> str:
            return _re.sub(r"\s+", " ", (s or "").strip())

        def _norm_for_match(s: str) -> str:
            # Aggressive normalization for substring checks.
            s = _norm_ws(s).lower()
            # Replace curly quotes etc.
            s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
            return s

        normalized_argument = _norm_for_match(argument_text)

        # Lightweight feature detection (mirrors the rule-based fallback)
        tl = (argument_text or "").lower()
        has_parties = any(k in tl for k in ("appellant", "respondent", "plaintiff", "defendant", "petitioner"))
        has_relief = any(k in tl for k in ("prayer", "relief", "seek", "seeks", "request", "asks", "declare", "declaration", "injunction", "ejectment", "damages", "costs"))
        has_dates = bool(_re.search(r"\b(19\d{2}|20\d{2})\b|\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", argument_text or ""))
        has_statute = bool(_re.search(r"\b(section|s\.|article|act|ordinance|law)\b", tl))
        has_evidence = any(k in tl for k in ("evidence", "exhibit", "document", "deed", "agreement", "survey", "plan", "witness", "affidavit", "receipt", "letter"))
        has_reasoning = any(k in tl for k in ("therefore", "thus", "because", "hence", "accordingly", "as a result"))
        has_counter = any(k in tl for k in ("however", "but", "defence", "defense", "counter", "respondent may", "the defendant may", "anticipated"))
        has_amounts = bool(_re.search(r"\b(lkr|rs\.?|rupees|usd|\d{1,3}(,\d{3})+)\b", tl))

        def _missing_and_action(category_name: str) -> tuple[str, str]:
            c = (category_name or "").lower()
            if "issue" in c or "claim" in c:
                missing = []
                if not has_parties:
                    missing.append("parties")
                if not has_relief:
                    missing.append("exact relief/prayer")
                missing_txt = " and ".join(missing) if missing else "key details"
                action = "State the parties and the exact relief sought in the first 1-2 lines."
                return missing_txt, action
            if "fact" in c or "chron" in c:
                missing_txt = "specific dates or a clear timeline" if not has_dates else "a cleaner chronological order"
                action = "List key events in date order (each sentence starts with a date/time)."
                return missing_txt, action
            if "legal" in c or "element" in c or "basis" in c:
                missing_txt = "statute/section citations" if not has_statute else "element-by-element application"
                action = "Cite the exact law (Act + Section) and apply each legal element to your facts."
                return missing_txt, action
            if "evidence" in c or "support" in c:
                missing_txt = "named documents/exhibits" if not has_evidence else "specific exhibit details (title/date)"
                action = "Name each document (e.g., deed number/date) and say what fact it proves."
                return missing_txt, action
            if "reason" in c or "logic" in c:
                missing_txt = "clear fact→law→conclusion links" if not has_reasoning else "tighter step-by-step logic"
                action = "Add explicit connectors: 'Because X, under Section Y, therefore Z follows.'"
                return missing_txt, action
            if "counter" in c or "rebut" in c:
                missing_txt = "any anticipated defence and rebuttal" if not has_counter else "stronger rebuttal detail"
                action = "Write 1 paragraph: 'Opponent may argue __; reply __' with a reason and citation."
                return missing_txt, action
            if "remed" in c or "quant" in c:
                missing_txt = "a precise remedy (and amount/calculation if money)" if not has_amounts else "a clearer calculation basis"
                action = "State the exact order you want (and exact amount + how calculated if damages)."
                return missing_txt, action
            missing_txt = "clear headings/numbered paragraphs"
            action = "Use headings (Facts/Issues/Law/Relief) and numbered paragraphs for easy reference."
            return missing_txt, action

        # ── Build sentence list — try punctuation split, then newline, then words ──
        raw_sentences = _re.split(r'(?<=[.!?])\s+|\n{1,}', argument_text.strip())
        arg_sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 12]
        # Last resort: chunk into ~80-char pieces so we always have something to quote
        if not arg_sentences:
            words = argument_text.split()
            arg_sentences = [" ".join(words[i:i+15]) for i in range(0, len(words), 15) if words[i:i+15]]
        if not arg_sentences:
            arg_sentences = [argument_text[:200]] if argument_text.strip() else ["(no argument text provided)"]

        # Precompute word sets for each sentence for faster matching.
        sent_word_sets = [set(_re.findall(r"[a-z]{4,}", s.lower())) for s in arg_sentences]

        # Category keyword hints to pick more relevant, distinct sentences.
        category_hints = {
            "issue": {"issue", "claim", "relief", "prayer", "appellant", "respondent", "plaintiff", "defendant", "seek", "asks"},
            "facts": {"on", "in", "dated", "date", "year", "month", "timeline", "chronology", "when", "then", "after", "before"},
            "legal": {"act", "section", "article", "law", "statute", "ordinance", "code", "case", "authority", "under"},
            "evidence": {"evidence", "exhibit", "document", "deed", "agreement", "receipt", "letter", "witness", "affidavit", "plan", "survey"},
            "reasoning": {"therefore", "thus", "because", "hence", "so", "means", "shows", "proves", "conclude"},
            "counter": {"however", "but", "defence", "defense", "counter", "respondent may", "likely", "anticipate", "rebut"},
            "remedy": {"damages", "injunction", "ejectment", "declaration", "costs", "interest", "relief", "order", "remove"},
            "structure": {"heading", "paragraph", "numbered", "section", "format", "tone", "clarity"},
        }

        def _hint_key(category_name: str) -> str:
            c = (category_name or "").lower()
            if "issue" in c or "claim" in c:
                return "issue"
            if "fact" in c or "chron" in c:
                return "facts"
            if "legal" in c or "element" in c or "basis" in c:
                return "legal"
            if "evidence" in c or "support" in c:
                return "evidence"
            if "reason" in c or "logic" in c:
                return "reasoning"
            if "counter" in c or "rebut" in c:
                return "counter"
            if "remed" in c or "quant" in c:
                return "remedy"
            return "structure"

        def _is_placeholder_quote(q: str) -> bool:
            ql = (q or "").strip().lower()
            if not ql:
                return True
            # Common placeholder patterns when the model echoes the instructions.
            return any(tok in ql for tok in (
                "<required",
                "verbatim sentence",
                "argument_text",
                "copy-paste",
                "most relevant sentence",
            ))

        def _quote_looks_sourced_from_argument(q: str) -> bool:
            qn = _norm_for_match(q)
            if len(qn) < 12:
                return False
            if qn in normalized_argument:
                return True
            # Allow truncated quotes: match the first ~60 chars.
            head = qn[:60].strip()
            return len(head) >= 20 and head in normalized_argument

        def best_arg_sentence_for(query_text: str, category_name: str, used: set[int]) -> str:
            """Pick the best sentence from the user's argument for this category.

            Prefers unused sentences to avoid showing the same quote across categories.
            """
            query_words = set(_re.findall(r"[a-z]{4,}", (query_text or "").lower()))
            hint = category_hints.get(_hint_key(category_name), set())
            best_idx = 0
            best_score = -1
            for idx, words in enumerate(sent_word_sets):
                overlap = len(query_words & words)
                hint_overlap = len(hint & words)
                # Prefer unused sentences.
                reuse_penalty = 0 if idx not in used else 2
                score = overlap + (2 * hint_overlap) - reuse_penalty
                if score > best_score:
                    best_score = score
                    best_idx = idx
            used.add(best_idx)
            return arg_sentences[best_idx][:250]

        def best_arg_sentence(rationale: str) -> str:
            """Return the argument sentence with highest word overlap to the rationale."""
            words = set(_re.findall(r'[a-z]{4,}', (rationale or "").lower()))
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

        # Track duplicates so we can re-pick quotes per category.
        existing_quotes = [str((it or {}).get("argument_quote", "") or "").strip() for it in critique.get("breakdown", []) or []]
        quote_counts: Dict[str, int] = {}
        for q in existing_quotes:
            if q:
                quote_counts[q] = quote_counts.get(q, 0) + 1

        used_sentence_indexes: set[int] = set()
        for item in critique.get("breakdown", []):
            rationale = item.get("rationale", "") or ""
            cat = item.get("category", "this category")

            current_quote = str(item.get("argument_quote", "") or "").strip()
            needs_requote = (
                _is_placeholder_quote(current_quote)
                or not _quote_looks_sourced_from_argument(current_quote)
                or (len(arg_sentences) >= 2 and current_quote and quote_counts.get(current_quote, 0) >= 2)
            )

            # argument_quote — always fill if empty
            if not current_quote or needs_requote:
                query_text = f"{cat} {rationale} "
                # Include strengths/gaps if present for more signal.
                strengths = item.get("strengths") or []
                gaps = item.get("gaps") or []
                if isinstance(strengths, list):
                    query_text += " ".join(str(s) for s in strengths if str(s).strip()) + " "
                if isinstance(gaps, list):
                    query_text += " ".join(str(g) for g in gaps if str(g).strip()) + " "
                item["argument_quote"] = best_arg_sentence_for(query_text, cat, used_sentence_indexes)
                enriched += 1

            # rationale — in fallback/template mode, rewrite to be argument-specific
            if force_argument_specific_rationales:
                existing_rationale = str(item.get("rationale") or "").strip()
                if not existing_rationale.lower().startswith("your text says:"):
                    quote = str(item.get("argument_quote") or "").strip() or best_arg_sentence_for(cat, cat, used_sentence_indexes)
                    missing_txt, action = _missing_and_action(cat)
                    item["rationale"] = (
                        f"Your text says: \"{quote}\". This is the part most relevant to {cat} and it affected your score here. "
                        f"You lost points because the argument is missing {missing_txt} in this category. "
                        f"To score higher, do this: {action}"
                    )
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

        # Citation injection disabled — [E#] references are not shown in the UI.

        return critique

    # ------------------------------------------------------------------
    # Claim-support mapping — second LLM call per grounded analysis
    # ------------------------------------------------------------------

    def compute_claim_support(
        self,
        breakdown: list,
        para_index_text: str,
        source_title: str = "Source Judgment",
    ) -> Dict[str, Any]:
        """Map each category's claims to numbered paragraphs via an LLM call.

        Args:
            breakdown: The ``breakdown`` list from the critique dict (8 items).
            para_index_text: Pre-formatted string of "Para N: <excerpt>\\n" lines.
            source_title: Label for the source document shown in the prompt.

        Returns:
            A dict keyed by category name, each value a dict with keys:
            ``bullets``, ``total_claims``, ``supported_claims``,
            ``support_ratio_percent``, ``support_ratio_label``, ``not_referenced``.
        """
        if not breakdown or not para_index_text.strip():
            return {}

        # Build compact category summaries (avoid sending huge text to the LLM)
        cat_summaries = []
        for item in breakdown:
            cat = item.get("category", "Unknown")
            score = item.get("rubric_score", "?")
            weight = item.get("weight", "?")
            aq = (item.get("argument_quote") or "")[:300]
            rat = (item.get("rationale") or "")[:400]
            cat_summaries.append(
                f"Category: {cat} [Score {score}/5, Weight {weight}]\n"
                f"  argument_quote: {aq}\n"
                f"  rationale: {rat}"
            )

        user_prompt = (
            f"=== SOURCE_EXCERPTS FROM: {source_title} ===\n"
            f"{para_index_text}\n\n"
            "=== ARGUMENT CATEGORIES ===\n"
            + "\n\n".join(cat_summaries)
            + "\n\nNow produce the claim_support JSON for the applicable categories listed above."
        )

        try:
            if self.backend_name == "gemini":
                raw = self.backend._call_api(
                    CLAIM_SUPPORT_SYSTEM_PROMPT, user_prompt, temperature=0.1
                )
            elif self.backend_name == "openrouter":
                messages = [
                    {"role": "system", "content": CLAIM_SUPPORT_SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ]
                raw = self.backend._post(messages, temperature=0.1)
            elif self.backend_name == "ollama":
                import requests as _req
                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": CLAIM_SUPPORT_SYSTEM_PROMPT},
                        {"role": "user",   "content": user_prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 2048},
                }
                resp = _req.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=600)
                resp.raise_for_status()
                raw = resp.json().get("message", {}).get("content", "")
            else:
                logger.warning(f"[claim-support] Unknown backend {self.backend_name}")
                return {}

            parsed = self._extract_json(raw)
            if not isinstance(parsed, dict):
                logger.warning("[claim-support] LLM returned non-dict JSON; skipping claim map.")
                return {}

            items = parsed.get("claim_support", [])
            if not isinstance(items, list):
                return {}

            result: Dict[str, Any] = {}
            for entry in items:
                cat_name = entry.get("category", "")
                if not cat_name:
                    continue
                result[cat_name] = {
                    "bullets":               entry.get("bullets") or [],
                    "total_claims":          int(entry.get("total_claims") or 0),
                    "supported_claims":      int(entry.get("supported_claims") or 0),
                    "support_ratio_percent": int(entry.get("support_ratio_percent") or 0),
                    "support_ratio_label":   entry.get("support_ratio_label") or "Low",
                    "not_referenced":        entry.get("not_referenced") or [],
                }
            logger.info(f"[claim-support] Mapped {len(result)} categories via LLM.")
            return result

        except Exception as exc:
            logger.warning(f"[claim-support] Failed ({exc}); returning empty map.")
            return {}

    def _get_fallback_critique(self, argument_text: str) -> Dict[str, Any]:
        """Generate a fallback critique when AI inference fails.

        IMPORTANT: This path must still generate *argument-specific* rationales.
        The previous version used fixed template rationales that appeared the
        same for all inputs, which confused users.
        """
        import re as _re

        text = (argument_text or "").strip()
        word_count = len(text.split())

        # ── Sentence extraction (for argument_quote) ─────────────────────────
        raw_sentences = _re.split(r'(?<=[.!?])\s+|\n{1,}', text)
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 12]
        if not sentences:
            words = text.split()
            sentences = [" ".join(words[i:i+15]) for i in range(0, len(words), 15) if words[i:i+15]]
        if not sentences:
            sentences = [text[:200]] if text else ["(no argument text provided)"]

        def _pick_sentence(hints: set[str]) -> str:
            best = sentences[0]
            best_score = -1
            for s in sentences:
                w = set(_re.findall(r"[a-z]{4,}", s.lower()))
                score = len(w & hints)
                if score > best_score:
                    best_score = score
                    best = s
            return best[:250]

        # ── Feature detection (varies by input) ─────────────────────────────
        tl = text.lower()
        has_parties = any(k in tl for k in ("appellant", "respondent", "plaintiff", "defendant", "petitioner"))
        has_relief = any(k in tl for k in ("prayer", "relief", "seek", "seeks", "request", "asks", "declare", "declaration", "injunction", "ejectment", "damages", "costs"))
        has_dates = bool(_re.search(r"\b(19\d{2}|20\d{2})\b|\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", text))
        has_statute = bool(_re.search(r"\b(section|s\.|article|act|ordinance|law)\b", tl))
        has_case_cites = bool(_re.search(r"\bv\.?\b|\bvs\.?\b|\bsc\b|\bca\b|\b[12]\d{3}\b", tl))
        has_evidence = any(k in tl for k in ("evidence", "exhibit", "document", "deed", "agreement", "survey", "plan", "witness", "affidavit", "receipt", "letter"))
        has_reasoning = any(k in tl for k in ("therefore", "thus", "because", "hence", "accordingly", "as a result"))
        has_counter = any(k in tl for k in ("however", "but", "defence", "defense", "counter", "respondent may", "the defendant may", "anticipated"))
        has_amounts = bool(_re.search(r"\b(lkr|rs\.?|rupees|usd|\d{1,3}(,\d{3})+)\b", tl))
        has_numbered_structure = bool(_re.search(r"^\s*\d+\.|\n\s*\d+\.", text))

        # ── Category config ─────────────────────────────────────────────────
        categories = [
            ("Issue & Claim Clarity", 10, {"issue", "claim", "relief", "prayer", "seek", "appellant", "respondent", "plaintiff", "defendant"}),
            ("Facts & Chronology", 15, {"dated", "on", "in", "after", "before", "then", "timeline", "chronology"}),
            ("Legal Basis / Elements", 20, {"section", "act", "article", "law", "elements", "under"}),
            ("Evidence & Support", 15, {"evidence", "exhibit", "document", "deed", "survey", "plan", "witness"}),
            ("Reasoning & Logic", 15, {"therefore", "because", "thus", "hence", "so"}),
            ("Counterarguments & Rebuttal", 10, {"however", "but", "defence", "defense", "counter", "rebut"}),
            ("Remedies & Quantification", 10, {"damages", "injunction", "ejectment", "declaration", "costs", "interest"}),
            ("Structure, Style & Professionalism", 5, {"facts", "issues", "submissions", "prayer", "heading", "paragraph"}),
        ]

        def _clamp(n: int, lo: int = 0, hi: int = 5) -> int:
            return max(lo, min(hi, int(n)))

        breakdown = []
        for cat_name, weight, hints in categories:
            quote = _pick_sentence(hints)

            # Heuristic rubric score per category (0-5) derived from features.
            if "Issue" in cat_name:
                score = 2 + int(has_parties) + int(has_relief)
                missing = []
                if not has_parties:
                    missing.append("parties")
                if not has_relief:
                    missing.append("exact relief/prayer")
                missing_txt = " and ".join(missing) if missing else "key details"
                action = "State the parties and the exact relief sought in the first 1-2 lines."
            elif "Facts" in cat_name:
                score = 2 + int(has_dates) + int(word_count >= 80)
                missing_txt = "specific dates or a clear timeline" if not has_dates else "a cleaner chronological order"
                action = "List key events in date order (each sentence starts with a date/time)."
            elif "Legal Basis" in cat_name:
                score = 1 + int(has_statute) + int(has_case_cites) + int(word_count >= 80)
                missing_txt = "statute/section citations" if not has_statute else "element-by-element application"
                action = "Cite the exact law (Act + Section) and apply each legal element to your facts."
            elif "Evidence" in cat_name:
                score = 1 + int(has_evidence) + int(word_count >= 80) + int(has_dates)
                missing_txt = "named documents/exhibits" if not has_evidence else "specific exhibit details (title/date)"
                action = "Name each document (e.g., deed number/date) and say what fact it proves."
            elif "Reasoning" in cat_name:
                score = 2 + int(has_reasoning) + int(word_count >= 80)
                missing_txt = "clear fact→law→conclusion links" if not has_reasoning else "tighter step-by-step logic"
                action = "Add explicit connectors: 'Because X, under Section Y, therefore Z follows.'"
            elif "Counter" in cat_name:
                score = 1 + int(has_counter) + int(word_count >= 80)
                missing_txt = "any anticipated defence and rebuttal" if not has_counter else "stronger rebuttal detail"
                action = "Write 1 paragraph: 'Opponent may argue __; reply __' with a reason and citation."
            elif "Remedies" in cat_name:
                score = 2 + int(has_relief) + int(has_amounts)
                missing_txt = "a precise remedy (and amount/calculation if money)" if not has_amounts else "a clearer calculation basis"
                action = "State the exact order you want (and exact amount + how calculated if damages)."
            else:  # Structure/style
                score = 2 + int(has_numbered_structure) + int(word_count >= 80)
                missing_txt = "clear headings/numbered paragraphs" if not has_numbered_structure else "cleaner sectioning"
                action = "Use headings (Facts/Issues/Law/Relief) and numbered paragraphs for easy reference."

            rubric_score = _clamp(score)
            points = round((rubric_score / 5.0) * weight, 1)

            # Build strengths/gaps from detected features so they vary by input.
            strengths = []
            gaps = []

            if "Issue" in cat_name:
                if has_parties:
                    strengths.append("Parties are identified.")
                if has_relief:
                    strengths.append("Relief requested is indicated.")
                if not has_parties:
                    gaps.append("Missing: who the parties are (appellant/respondent or plaintiff/defendant).")
                if not has_relief:
                    gaps.append("Missing: the exact relief/prayer (e.g., declaration, injunction, damages).")
            elif "Facts" in cat_name:
                if has_dates:
                    strengths.append("At least one date/time marker is included.")
                if word_count >= 80:
                    strengths.append("There is enough factual detail to follow the dispute.")
                if not has_dates:
                    gaps.append("Missing: specific dates for the key events.")
                gaps.append("Improve: present facts strictly in chronological order.")
            elif "Legal Basis" in cat_name:
                if has_statute:
                    strengths.append("Legal terminology suggests an attempt to ground the claim in law.")
                if has_case_cites:
                    strengths.append("Some citation-style markers appear.")
                if not has_statute:
                    gaps.append("Missing: statute name + section/article number for each legal proposition.")
                gaps.append("Missing: apply each legal element to a specific fact.")
            elif "Evidence" in cat_name:
                if has_evidence:
                    strengths.append("Mentions evidence/documents to support facts.")
                if not has_evidence:
                    gaps.append("Missing: specific documents/exhibits/witness references.")
                gaps.append("Improve: link each document to the fact it proves.")
            elif "Reasoning" in cat_name:
                if has_reasoning:
                    strengths.append("Uses reasoning connectors (e.g., therefore/because).")
                if not has_reasoning:
                    gaps.append("Missing: explicit reasoning steps (facts → rule → conclusion).")
                gaps.append("Improve: avoid jumping from facts directly to conclusions.")
            elif "Counter" in cat_name:
                if has_counter:
                    strengths.append("Acknowledges a possible opposing point.")
                else:
                    gaps.append("Missing: anticipate the opponent's strongest defence.")
                gaps.append("Missing: a clear rebuttal explaining why that defence fails.")
            elif "Remedies" in cat_name:
                if has_relief:
                    strengths.append("Mentions a form of relief/remedy.")
                if has_amounts:
                    strengths.append("Includes (or hints at) quantification.")
                if not has_amounts:
                    gaps.append("Missing: exact amount and how it is calculated (if claiming money).")
                gaps.append("Improve: list each remedy separately in a Prayer/Relief section.")
            else:
                if has_numbered_structure:
                    strengths.append("Uses numbered structure in parts of the text.")
                gaps.append("Improve: add headings (Facts / Issues / Law / Relief) for readability.")
                if not has_numbered_structure:
                    gaps.append("Missing: numbered paragraphs for court-friendly referencing.")

            # Ensure 1-3 items each
            strengths = [s for s in strengths if s][:3] or ["Some relevant content is present."]
            gaps = [g for g in gaps if g][:3]
            if rubric_score == 5:
                gaps = []
            elif not gaps:
                gaps = [f"Add more specific detail for {cat_name}."]

            # 3-sentence rationale tied to the actual quote + detected gaps.
            rationale = (
                f"Your text says: \"{quote}\". This is the part most relevant to {cat_name} and it helped your score here. "
                f"You lost points because the argument is missing {missing_txt} in this category. "
                f"To score higher, do this: {action}"
            )

            breakdown.append({
                "category": cat_name,
                "weight": weight,
                "rubric_score": rubric_score,
                "points": points,
                "argument_quote": quote,
                "judgment_quote": "",
                "rationale": rationale,
                "strengths": strengths,
                "gaps": gaps,
            })

        overall_score = int(round(sum(float(it.get("points") or 0.0) for it in breakdown)))
        feedback = [
            "Add a clear opening sentence stating parties, claim, and relief.",
            "Add dates and list facts in chronological order.",
            "Cite the specific law/section and link evidence to each key fact.",
        ]

        critique = {
            "overall_score": _clamp(overall_score, 0, 100),
            "breakdown": breakdown,
            "feedback": feedback,
            "warning": "AI service unavailable - using rule-based fallback analysis (rationales are generated from your typed text). [rule_fallback_v2]",
        }

        return critique


# Singleton instance
_inference_service: Optional[InferenceService] = None


def get_inference_service() -> InferenceService:
    """Get or create the inference service singleton."""
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService()
    return _inference_service
