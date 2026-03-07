"""
Service for parsing and cleaning LLM responses.
Enhanced with robust JSON extraction for unreliable model outputs.
"""

import json
import re
from typing import Any, Dict, Optional

from pydantic import ValidationError

from app.schemas import CaseMetadata


class ParserService:
    """Service for parsing LLM outputs and extracting structured data."""
    
    def __init__(self):
        """Initialize the parser service."""
        print("ParserService initialized")
    
    def clean_llm_json(self, llm_output: str) -> Dict[str, Any]:
        """
        Extract valid JSON from LLM output with enhanced error handling.
        
        This method handles multiple common LLM response patterns:
        1. Pure JSON response
        2. JSON wrapped in markdown code blocks (```json ... ```)
        3. JSON with explanatory text before/after
        4. Malformed JSON with common syntax errors
        
        Args:
            llm_output: Raw text output from LLM
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            ValueError: If no valid JSON found in output
        """
        if not llm_output or not llm_output.strip():
            raise ValueError("LLM output is empty")
        
        # Log the raw output for debugging
        print(f"Raw LLM output ({len(llm_output)} chars): {llm_output[:500]}...")
        
        original_output = llm_output
        
        # Step 1: Remove markdown code blocks if present
        code_block_pattern = r'```(?:json)?\s*(.*?)\s*```'
        code_blocks = re.findall(code_block_pattern, llm_output, re.DOTALL)
        
        if code_blocks:
            print(f"Found {len(code_blocks)} code block(s)")
            for block in code_blocks:
                if '{' in block or '[' in block:
                    llm_output = block
                    print("Extracted JSON from markdown code block")
                    break
        
        # Step 2: Try to find JSON object or array using multiple strategies
        json_patterns = [
            (r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', 'object'),
            (r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]', 'array'),
        ]
        
        extracted_json = None
        
        for pattern, json_type in json_patterns:
            matches = list(re.finditer(pattern, llm_output, re.DOTALL))
            
            if matches:
                matches.sort(key=lambda m: len(m.group(0)), reverse=True)
                
                for match in matches:
                    candidate = match.group(0)
                    
                    if json_type == 'object':
                        if candidate.count('{') == candidate.count('}'):
                            extracted_json = candidate
                            print(f"Found balanced JSON {json_type}")
                            break
                    else:
                        if candidate.count('[') == candidate.count(']'):
                            extracted_json = candidate
                            print(f"Found balanced JSON {json_type}")
                            break
                
                if extracted_json:
                    break
        
        if not extracted_json:
            # Strategy 2: Find first '{' and last '}'
            first_brace = llm_output.find('{')
            last_brace = llm_output.rfind('}')
            
            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                extracted_json = llm_output[first_brace:last_brace + 1]
                print("Extracted JSON using first/last brace positions")
            else:
                first_bracket = llm_output.find('[')
                last_bracket = llm_output.rfind(']')
                
                if first_bracket != -1 and last_bracket != -1 and first_bracket < last_bracket:
                    extracted_json = llm_output[first_bracket:last_bracket + 1]
                    print("Extracted JSON array using first/last bracket positions")
        
        if not extracted_json:
            print(f"No JSON structure found in output:\n{original_output[:1000]}")
            raise ValueError("No valid JSON object or array found in LLM output")
        
        print(f"Extracted JSON string ({len(extracted_json)} chars): {extracted_json[:300]}...")
        
        # Step 3: Attempt to parse the JSON
        try:
            parsed_json = json.loads(extracted_json)
            print(f"✓ Successfully parsed JSON ({type(parsed_json).__name__})")
            
            if isinstance(parsed_json, dict):
                print(f"  Top-level keys: {list(parsed_json.keys())}")
            elif isinstance(parsed_json, list):
                print(f"  Array length: {len(parsed_json)}")
            
            return parsed_json
        
        except json.JSONDecodeError as e:
            print(f"Initial JSON parse failed: {e}")
            print(f"Failed at position {e.pos}: ...{extracted_json[max(0, e.pos-50):e.pos+50]}...")
            
            # Step 4: Try to fix common JSON issues
            fixed_json = self._fix_common_json_issues(extracted_json)
            
            if fixed_json != extracted_json:
                try:
                    parsed_json = json.loads(fixed_json)
                    print("✓ Successfully parsed JSON after auto-fix")
                    return parsed_json
                except json.JSONDecodeError as e2:
                    print(f"JSON still invalid after fixes: {e2}")
            
            # Step 5: Last resort - try partial extraction
            print("Attempting partial JSON extraction...")
            partial_json = self._extract_partial_json(extracted_json)
            if partial_json:
                print("✓ Extracted partial JSON")
                return partial_json
            
            raise ValueError(f"Invalid JSON in LLM output: {str(e)}\nExtracted: {extracted_json[:500]}")
    
    def _extract_partial_json(self, json_str: str) -> Optional[Dict[str, Any]]:
        """Try to extract partial valid JSON if full parsing fails."""
        # Try to extract metadata
        metadata_match = re.search(r'"metadata"\s*:\s*(\{[^}]+\})', json_str)
        if metadata_match:
            try:
                metadata_obj = json.loads(metadata_match.group(1))
                print("Extracted metadata from partial JSON")
                return {"metadata": metadata_obj}
            except json.JSONDecodeError:
                pass
        
        # Try to extract sections
        sections_match = re.search(r'"sections"\s*:\s*(\[[^\]]+\])', json_str)
        if sections_match:
            try:
                sections_arr = json.loads(sections_match.group(1))
                print("Extracted sections from partial JSON")
                return {"sections": sections_arr}
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _fix_common_json_issues(self, json_str: str) -> str:
        """Attempt to fix common JSON formatting issues."""
        print("Applying JSON fixes...")
        
        # Remove trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # Remove control characters
        json_str = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', json_str)
        
        # Replace single quotes with double quotes if no double quotes present
        if '"' not in json_str and "'" in json_str:
            json_str = json_str.replace("'", '"')
            print("Replaced single quotes with double quotes")
        
        # Remove BOM
        json_str = json_str.replace('\ufeff', '')
        
        return json_str
    
    def extract_metadata(self, llm_json: Dict[str, Any]) -> Optional[CaseMetadata]:
        """
        Extract and validate case metadata from parsed JSON.
        
        Args:
            llm_json: Parsed JSON dictionary from LLM
            
        Returns:
            Validated CaseMetadata object or None if validation fails
        """
        try:
            # Look for metadata in common locations
            metadata_dict = llm_json.get('metadata', llm_json)
            
            # Validate using Pydantic
            metadata = CaseMetadata(**metadata_dict)
            print(f"Successfully extracted metadata: {metadata.case_number}")
            return metadata
        
        except ValidationError as e:
            print(f"Metadata validation failed: {e}")
            print(f"Attempted to parse: {metadata_dict}")
            return None
        
        except Exception as e:
            print(f"Unexpected error extracting metadata: {e}")
            return None
    
    def create_extraction_prompt(self, text: str, max_tokens: int = 2000) -> str:
        """
        Create a structured prompt for the 1.5B model to extract information.
        
        This prompt is specifically designed for smaller models that need
        clear instructions and examples.
        
        Args:
            text: OCR text to analyze
            max_tokens: Maximum tokens to include from text
            
        Returns:
            Formatted prompt string
        """
        # Truncate text if too long (approximate token count)
        if len(text) > max_tokens * 4:  # Rough estimate: 1 token ≈ 4 chars
            text = text[:max_tokens * 4] + "..."
            print(f"Text truncated to ~{max_tokens} tokens")
        
        prompt = f"""You are a legal document analyzer. Extract information from this Sri Lankan court case document and return ONLY a valid JSON object.

IMPORTANT: Return ONLY the JSON object, no explanatory text before or after.

Extract these fields:
1. case_number: The case number/identifier (e.g., "SC Appeal No. 105/2012")
2. court: The court name (e.g., "Supreme Court of Sri Lanka")
3. date: Date in YYYY-MM-DD format (if found)
4. parties: Array of party names (plaintiffs, defendants, appellants, respondents)
5. judges: Array of judge names
6. case_type: Type of case (e.g., "Civil Appeal", "Criminal")

Document text:
{text}

Return JSON in this exact format:
{{
  "case_number": "SC Appeal No. XXX/YYYY",
  "court": "Court name here",
  "date": "YYYY-MM-DD",
  "parties": ["Party 1", "Party 2"],
  "judges": ["Judge 1"],
  "case_type": "Case type"
}}

JSON:"""
        
        return prompt
