"""
Grading Schema Definition
==========================

Defines the rubric for scoring legal arguments across 8 categories.

Author: LegalScoreModel Team
Date: January 2026
"""

from typing import Dict, List
from pydantic import BaseModel


class RubricLevel(BaseModel):
    """Definition for a single rubric score level."""
    score: int
    description: str


class GradingCategory(BaseModel):
    """Definition for a grading category."""
    name: str
    weight: int
    description: str
    rubric_levels: Dict[int, str]
    
    def calculate_points(self, rubric_score: int) -> float:
        """
        Calculate points for this category based on rubric score.
        
        Args:
            rubric_score: Score from 0-5
            
        Returns:
            Points earned (0 to weight)
        """
        if not 0 <= rubric_score <= 5:
            raise ValueError(f"Rubric score must be 0-5, got {rubric_score}")
        
        return (rubric_score / 5.0) * self.weight


# ============================================
# Grading Schema Configuration
# ============================================

GRADING_SCHEMA = {
    "issue_claim_clarity": GradingCategory(
        name="Issue & Claim Clarity",
        weight=10,
        description="Is the legal claim clearly stated? Parties, relief sought, dispute framed",
        rubric_levels={
            0: "No identifiable claim or issue",
            1: "Vague or contradictory claim; unclear parties or relief",
            2: "Basic claim stated but missing key elements (parties, relief, or issue)",
            3: "Claim stated with most elements present; minor ambiguities",
            4: "Clear and complete claim with all elements well-articulated",
            5: "Exceptional clarity; precise framing of issue, parties, and relief"
        }
    ),
    
    "facts_chronology": GradingCategory(
        name="Facts & Chronology",
        weight=15,
        description="Specificity, completeness, timeline, material facts vs irrelevant narrative",
        rubric_levels={
            0: "No factual basis provided",
            1: "Extremely vague or generic facts; no timeline",
            2: "Some facts present but incomplete; missing dates or key events",
            3: "Adequate factual narrative with basic chronology; some gaps",
            4: "Comprehensive facts with clear timeline; well-organized",
            5: "Detailed, specific facts with complete chronology; distinguishes material from immaterial"
        }
    ),
    
    "legal_basis_elements": GradingCategory(
        name="Legal Basis / Elements",
        weight=20,
        description="Correct cause of action; elements listed and applied to facts",
        rubric_levels={
            0: "No legal basis or cause of action identified",
            1: "Mentions law vaguely; no element-by-element analysis",
            2: "Identifies cause of action but fails to map elements to facts",
            3: "Lists elements and attempts application; some gaps in analysis",
            4: "Strong element-by-element analysis with good fact-to-law mapping",
            5: "Comprehensive legal analysis; all elements clearly mapped to facts with citations"
        }
    ),
    
    "evidence_support": GradingCategory(
        name="Evidence & Support",
        weight=15,
        description="References to documents, witness statements, admissions; factual assertions supported",
        rubric_levels={
            0: "No evidence or supporting documentation mentioned",
            1: "Bare assertions without any evidentiary support",
            2: "Minimal references to evidence; mostly unsupported claims",
            3: "Some evidence cited but incomplete; key assertions lack support",
            4: "Good evidentiary support; most claims backed by documents or testimony",
            5: "Comprehensive evidence; all material facts supported by specific references"
        }
    ),
    
    "reasoning_logic": GradingCategory(
        name="Reasoning & Logic",
        weight=15,
        description="Clear link: facts → rule → conclusion; no contradictions; avoids speculation",
        rubric_levels={
            0: "No logical structure or reasoning present",
            1: "Illogical or contradictory reasoning; major logical leaps",
            2: "Weak reasoning with gaps; some contradictions or speculation",
            3: "Adequate logical flow; minor gaps in reasoning",
            4: "Strong logical structure; clear fact-to-conclusion pathway",
            5: "Exceptional reasoning; flawless logical progression with no contradictions"
        }
    ),
    
    "counterarguments_rebuttal": GradingCategory(
        name="Counterarguments & Rebuttal",
        weight=10,
        description="Anticipates opposing points and answers them",
        rubric_levels={
            0: "No acknowledgment of opposing arguments",
            1: "Briefly mentions opposition but provides no rebuttal",
            2: "Weak rebuttal; fails to address key counterarguments",
            3: "Addresses some counterarguments adequately",
            4: "Strong rebuttal to most anticipated defenses",
            5: "Comprehensive pre-emption and rebuttal of all likely counterarguments"
        }
    ),
    
    "remedies_quantification": GradingCategory(
        name="Remedies & Quantification",
        weight=10,
        description="Remedies are appropriate; damages calculation explained if relevant",
        rubric_levels={
            0: "No remedy or relief specified",
            1: "Vague or inappropriate remedy requested",
            2: "Remedy stated but without justification or calculation",
            3: "Appropriate remedy with basic justification",
            4: "Well-justified remedy with clear calculation (if applicable)",
            5: "Comprehensive remedy analysis with detailed quantification and legal basis"
        }
    ),
    
    "structure_professionalism": GradingCategory(
        name="Structure, Style & Professionalism",
        weight=5,
        description="Readability, headings, concise, legally appropriate tone",
        rubric_levels={
            0: "Incomprehensible or extremely unprofessional",
            1: "Poor structure; informal or inappropriate tone",
            2: "Basic structure but lacks organization; some tone issues",
            3: "Adequate structure and tone; readable",
            4: "Well-structured with professional tone; good use of headings",
            5: "Exemplary structure, style, and professionalism; highly polished"
        }
    )
}


def get_total_possible_score() -> int:
    """
    Calculate the total possible score across all categories.
    
    Returns:
        Total weight (should be 100)
    """
    return sum(category.weight for category in GRADING_SCHEMA.values())


def get_category_names() -> List[str]:
    """
    Get list of all category names.
    
    Returns:
        List of category display names
    """
    return [category.name for category in GRADING_SCHEMA.values()]


# Validate that weights sum to 100
assert get_total_possible_score() == 100, "Category weights must sum to 100"
