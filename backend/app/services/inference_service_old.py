"""
Inference Service for Legal Argument Critic
============================================

Supports two backends:
1. LOCAL: Load fine-tuned model from local adapter files (uses GPU/CPU)
2. OLLAMA: Use Ollama API with custom GGUF model

Set INFERENCE_BACKEND in .env to choose: "local" or "ollama"

Author: LegalScoreModel Team
Date: January 2026
"""

import json
import re
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)


# ============================================
# Configuration
# ============================================

INFERENCE_BACKEND = os.getenv("INFERENCE_BACKEND", "local")  # "local" or "ollama"

# Local model paths
BASE_DIR = Path(__file__).parent.parent.parent
ADAPTER_PATH = BASE_DIR / "models" / "fine_tuned" / "adapter_model" / "qwen2.5-3b-legal-critic-adapter"
BASE_MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

# Ollama config
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "legal-critic")


class InferenceService:
    """
    Service for running inference with the fine-tuned legal argument critic model.
    
    Supports both local (transformers + PEFT) and Ollama backends.
    """
    
    def __init__(self):
        """Initialize the inference service based on configured backend."""
        logger.info("=" * 60)
        logger.info("Initializing Inference Service")
        logger.info("=" * 60)
        
        self.backend = INFERENCE_BACKEND
        self.is_ready = False
        self.model = None
        self.tokenizer = None
        self.device = None
        self.model_name = OLLAMA_MODEL if self.backend == "ollama" else str(ADAPTER_PATH)
        self.base_url = OLLAMA_BASE_URL
        
        logger.info(f"Backend: {self.backend}")
        
        try:
            if self.backend == "local":
                self._init_local()
            elif self.backend == "ollama":
                self._init_ollama()
            else:
                raise ValueError(f"Unknown backend: {self.backend}. Use 'local' or 'ollama'")
            
            self.is_ready = True
            logger.info("✓ Inference service ready")
        except Exception as e:
            logger.error(f"✗ Failed to initialize: {str(e)}")
            raise
    
    # ============================================
    # Local Backend (Transformers + PEFT)
    # ============================================
    
    def _init_local(self):
        """Initialize local inference with transformers + PEFT."""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel
        
        logger.info("Initializing LOCAL backend...")
        logger.info(f"Adapter path: {ADAPTER_PATH}")
        
        if not ADAPTER_PATH.exists():
            raise FileNotFoundError(f"Adapter not found at: {ADAPTER_PATH}")
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Device: {self.device}")
        
        # Load base model with quantization
        logger.info(f"Loading base model: {BASE_MODEL_NAME}")
        logger.info("This will download ~6GB on first run (cached afterwards)...")
        
        # Configure 4-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            BASE_MODEL_NAME,
            trust_remote_code=True
        )
        
        self.model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_NAME,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
            quantization_config=bnb_config
        )
        
        logger.info("✓ Base model loaded")
        
        # Load fine-tuned adapter
        logger.info(f"Loading fine-tuned adapter...")
        self.model = PeftModel.from_pretrained(
            self.model,
            str(ADAPTER_PATH)
        )
        self.model.eval()
        
        logger.info("✓ Fine-tuned adapter loaded")
        logger.info(f"✓ Local backend ready (device: {self.device})")
    
    def _generate_local(self, argument_text: str) -> str:
        """Generate response using local model."""
        import torch
        
        prompt = self._format_prompt(argument_text)
        
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=2048,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
        
        # Extract assistant response
        if "<|im_start|>assistant" in response:
            response = response.split("<|im_start|>assistant")[-1]
            if "<|im_end|>" in response:
                response = response.split("<|im_end|>")[0]
        
        return response.strip()
    
    # ============================================
    # Ollama Backend
    # ============================================
    
    def _init_ollama(self):
        """Initialize Ollama backend."""
        logger.info("Initializing OLLAMA backend...")
        logger.info(f"Ollama URL: {OLLAMA_BASE_URL}")
        logger.info(f"Model: {OLLAMA_MODEL}")
        
        # Verify connection
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info("✓ Connected to Ollama")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
                "Make sure Ollama is running: 'ollama serve'"
            )
        
        # Verify model exists
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        
        if not any(OLLAMA_MODEL in name for name in model_names):
            raise RuntimeError(
                f"Model '{OLLAMA_MODEL}' not found in Ollama. "
                f"Available: {model_names}. "
                f"Pull with: 'ollama pull {OLLAMA_MODEL}'"
            )
        
        logger.info(f"✓ Ollama backend ready (model: {OLLAMA_MODEL})")
    
    def _generate_ollama(self, argument_text: str) -> str:
        """Generate response using Ollama API."""
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": f"Critique this legal argument and respond with ONLY JSON:\n\n{argument_text}"}
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 2048
            }
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        
        return response.json().get("message", {}).get("content", "")
    
    # ============================================
    # Shared Methods
    # ============================================
    
    def _format_prompt(self, argument_text: str) -> str:
        """Format prompt for local model (Qwen2 chat format)."""
        system_prompt = self._build_system_prompt()
        
        return f"""<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
Critique this legal argument and respond with ONLY JSON:

{argument_text}<|im_end|>
<|im_start|>assistant
"""
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for legal argument critique."""
        return """You are an expert legal argument critic for Sri Lankan civil cases.

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

Scoring: 0=Missing, 1=Poor, 2=Below Average, 3=Average, 4=Good, 5=Excellent"""
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from model response."""
        cleaned = response_text.strip()
        
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
            logger.warning("Failed to extract JSON from response")
            return None
    
    def _validate_critique(self, critique: Dict[str, Any]) -> bool:
        """Validate critique structure."""
        if not all(k in critique for k in ["overall_score", "breakdown", "feedback"]):
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
        """Generate a critique for a legal argument."""
        if not argument_text or len(argument_text.strip()) < 10:
            raise ValueError("Argument text must be at least 10 characters long")
        
        logger.info(f"Generating critique ({len(argument_text)} chars) via {self.backend}")
        
        try:
            # Generate based on backend
            if self.backend == "local":
                response = self._generate_local(argument_text)
            else:
                response = self._generate_ollama(argument_text)
            
            # Parse response
            critique = self._extract_json_from_response(response)
            
            if critique is None:
                return {
                    "error": "Failed to parse model response as JSON",
                    "raw_response": response[:500],
                    "overall_score": 0,
                    "breakdown": [],
                    "feedback": ["The model response could not be parsed. Please try again."]
                }
            
            if not self._validate_critique(critique):
                critique["warning"] = "Critique may have incomplete structure"
            
            logger.info(f"✓ Critique generated (score: {critique.get('overall_score', 'N/A')})")
            return critique
            
        except Exception as e:
            logger.error(f"Error generating critique: {str(e)}")
            raise RuntimeError(f"Failed to generate critique: {str(e)}")


_inference_service: Optional[InferenceService] = None


def get_inference_service() -> InferenceService:
    """Get or create the global inference service instance."""
    global _inference_service
    
    if _inference_service is None:
        _inference_service = InferenceService()
    
    return _inference_service
