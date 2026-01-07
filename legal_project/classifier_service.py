#!/usr/bin/env python3
"""
ML Classification Service for Legal Cases
Integrates with the trained scikit-learn classifier
"""

import joblib
import os
import sys
import json
from pathlib import Path

# Get the model directory
MODEL_DIR = Path(__file__).parent

# Load trained models
try:
    classifier = joblib.load(MODEL_DIR / 'legal_classifier.pkl')
    vectorizer = joblib.load(MODEL_DIR / 'tfidf_vectorizer.pkl')
    case_labels = joblib.load(MODEL_DIR / 'case_labels.pkl')
except Exception as e:
    print(f"❌ Error loading models: {e}")
    classifier = None
    vectorizer = None
    case_labels = None

def classify_legal_case(text):
    """
    Classify if text is a legal case and predict its category
    
    Args:
        text (str): The text content to classify
        
    Returns:
        dict: {
            'is_legal_case': bool,
            'confidence': float (0-1),
            'case_type': str,
            'all_predictions': dict
        }
    """
    if not classifier or not vectorizer:
        return {
            'is_legal_case': False,
            'confidence': 0,
            'case_type': 'unknown',
            'error': 'Models not loaded'
        }
    
    try:
        # Check minimum text length
        if len(text.strip()) < 100:
            return {
                'is_legal_case': False,
                'confidence': 0.1,
                'case_type': 'too_short',
                'all_predictions': {}
            }
        
        # Vectorize the text
        text_vector = vectorizer.transform([text])
        
        # Get prediction probabilities
        probabilities = classifier.predict_proba(text_vector)[0]
        predicted_class_idx = classifier.predict(text_vector)[0]
        predicted_class = classifier.classes_[predicted_class_idx]
        confidence = float(probabilities[predicted_class_idx])
        
        # Create prediction dictionary for all classes
        all_predictions = {}
        for idx, class_name in enumerate(classifier.classes_):
            all_predictions[class_name] = float(probabilities[idx])
        
        # A legal case should have reasonable confidence
        # If any prediction > 0.25, treat as legal case (since all trained data is legal)
        is_legal = confidence > 0.25 or max(probabilities) > 0.35
        
        return {
            'is_legal_case': is_legal,
            'confidence': confidence,
            'case_type': predicted_class,
            'all_predictions': all_predictions,
            'method': 'ml'
        }
        
    except Exception as e:
        print(f"❌ Classification error: {e}", file=sys.stderr)
        return {
            'is_legal_case': False,
            'confidence': 0,
            'case_type': 'error',
            'error': str(e)
        }

if __name__ == '__main__':
    # Get text from command line argument
    if len(sys.argv) > 1:
        text = sys.argv[1]
    else:
        # Test the classifier
        text = "IN THE COURT OF APPEAL OF THE DEMOCRATIC SOCIALIST REPUBLIC OF SRI LANKA In the matter of an application for bail in terms of the Section 83 of the Poisons, Opium and Dangerous Drugs Ordinance as amended by the Act No.41 of 2022. Court of Appeal The Officer-in-Charge Application No. Police Station, Katana. COMPLAINANT Vs."
    
    result = classify_legal_case(text)
    # Output as JSON for Node.js to parse
    print(json.dumps(result))

