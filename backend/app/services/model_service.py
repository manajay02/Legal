"""
Fine-tuned Model Inference Service
===================================

Loads and runs inference with the fine-tuned Qwen2.5-3B-Instruct model
for legal argument critique.
"""

import json
import torch
from typing import Dict, Any, Optional
from pathlib import Path


class ModelService:
    """Service for loading and running inference with fine-tuned model."""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.max_seq_length = 2048
        self.model_loaded = False
    
    def load_model(self, model_path: str = "models/fine_tuned/qwen2.5-3b-legal-critic-adapter"):
        """
        Load the fine-tuned model adapter.
        
        Args:
            model_path: Path to the fine-tuned adapter directory
        """
        try:
            # Try Unsloth first (if available)
            try:
                from unsloth import FastLanguageModel
                
                print(f"Loading fine-tuned model with Unsloth from: {model_path}")
                
                self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                    model_name=model_path,
                    max_seq_length=self.max_seq_length,
                    dtype=None,
                    load_in_4bit=True,
                )
                
                FastLanguageModel.for_inference(self.model)
                print("✓ Model loaded with Unsloth")
                
            except ImportError:
                # Fallback to standard transformers + PEFT
                print(f"Unsloth not available, using transformers + PEFT")
                print(f"Loading base model: Qwen/Qwen2.5-3B-Instruct")
                
                from transformers import AutoModelForCausalLM, AutoTokenizer
                from peft import PeftModel
                
                # Load base model
                base_model = AutoModelForCausalLM.from_pretrained(
                    "Qwen/Qwen2.5-3B-Instruct",
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
                
                # Load adapter
                print(f"Loading fine-tuned adapter from: {model_path}")
                self.model = PeftModel.from_pretrained(base_model, model_path)
                
                # Load tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=True
                )
                
                # Set to eval mode
                self.model.eval()
                print("✓ Model loaded with transformers + PEFT")
            
            self.model_loaded = True
            print("✓ Model ready for inference")
            
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            raise
    
    def critique_argument(self, legal_argument: str) -> Dict[str, Any]:
        """
        Generate a critique for a legal argument using the fine-tuned model.
        
        Args:
            legal_argument: The legal argument text to critique
            
        Returns:
            Dictionary containing the critique (overall_score, breakdown, feedback)
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Format the prompt using the same template as training
        system_prompt = """You are an expert legal argument critic for Sri Lankan civil cases. 
Analyze the provided legal argument and return a JSON critique with:
1. overall_score (0-100)
2. breakdown (8 categories with weight, rubric_score 0-5, points, rationale)
3. feedback (3 improvement suggestions)

Categories: Issue & Claim Clarity (10), Facts & Chronology (15), Legal Basis (20), 
Evidence & Support (15), Reasoning & Logic (15), Counterarguments (10), 
Remedies & Quantification (10), Structure & Professionalism (5)"""
        
        prompt = f"""<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
Critique this legal argument:

{legal_argument}<|im_end|>
<|im_start|>assistant
"""
        
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_seq_length
        ).to(self.model.device)
        
        # Generate response
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=2048,  # Allow long critiques
                temperature=0.7,  # Balanced creativity
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        
        # Decode response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract assistant's response (after the prompt)
        assistant_response = response.split("<|im_start|>assistant")[-1].strip()
        
        # Parse JSON response
        try:
            critique = json.loads(assistant_response)
            return critique
        except json.JSONDecodeError:
            # If model didn't return valid JSON, try to extract it
            import re
            json_match = re.search(r'\{.*\}', assistant_response, re.DOTALL)
            if json_match:
                try:
                    critique = json.loads(json_match.group(0))
                    return critique
                except:
                    pass
            
            # Fallback: return raw response
            return {
                "error": "Failed to parse JSON response",
                "raw_response": assistant_response,
                "overall_score": 0,
                "breakdown": [],
                "feedback": []
            }


# Global model service instance
model_service = ModelService()


def get_model_service() -> ModelService:
    """Get the global model service instance."""
    return model_service
