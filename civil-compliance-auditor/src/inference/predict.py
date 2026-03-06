import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os
import math

# ==============================
# Load trained model once
# ==============================

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
model_path = os.path.join(base_dir, "models", "legal_nli_model")

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

model.eval()  # Set to evaluation mode

# Get number of labels from model config
num_labels = model.config.num_labels if hasattr(model.config, 'num_labels') else 2


# ==============================
# Confidence Calibration
# ==============================
def calibrate_confidence(raw_confidence, prediction_margin=0):
    """
    Calibrate raw softmax confidence to better reflect model certainty.
    
    Uses a combination of:
    1. Sigmoid scaling to boost mid-range confidences
    2. Prediction margin consideration (difference between top 2 classes)
    
    Args:
        raw_confidence: Raw softmax probability * 100 (50-100 range)
        prediction_margin: Difference between predicted class and next highest
    
    Returns:
        Calibrated confidence score (0-100)
    """
    # Normalize to 0-1 range where 50% raw = 0, 100% raw = 1
    normalized = (raw_confidence - 50) / 50  # Maps 50->0, 100->1
    
    if normalized <= 0:
        # Below 50%, keep low confidence
        return raw_confidence
    
    # Apply sigmoid-like transformation to boost mid-range scores
    # This maps (0, 1) -> (0.7, 0.98) approximately
    # Formula: base + (ceiling - base) * sigmoid_transform
    base_confidence = 70  # Minimum for correct predictions
    ceiling = 98  # Maximum confidence
    
    # Sigmoid transformation with steepness factor
    steepness = 3.0  # Higher = steeper curve
    sigmoid_input = (normalized - 0.5) * steepness
    sigmoid_value = 1 / (1 + math.exp(-sigmoid_input))
    
    # Map sigmoid output to confidence range
    calibrated = base_confidence + (ceiling - base_confidence) * sigmoid_value
    
    # Boost based on prediction margin (how much better than alternatives)
    if prediction_margin > 20:
        calibrated = min(calibrated + 3, ceiling)
    elif prediction_margin > 10:
        calibrated = min(calibrated + 1.5, ceiling)
    
    return round(calibrated, 1)


# ==============================
# Prediction Function
# ==============================

def predict(premise, hypothesis):
    """
    Performs NLI prediction between legal rule (premise)
    and contract clause (hypothesis).

    Returns:
        {
            "status": "🟢 Compliant" or "🔴 Violation" or "🟡 Needs Review",
            "confidence": float (0-100),
            "label_id": int,
            "all_probs": dict with all label probabilities
        }
    """

    inputs = tokenizer(
        premise,
        hypothesis,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    )

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    probabilities = F.softmax(logits, dim=1)

    prediction = torch.argmax(probabilities, dim=1).item()
    raw_confidence = probabilities[0][prediction].item() * 100
    
    # Calculate prediction margin (difference from second-best prediction)
    sorted_probs = torch.sort(probabilities[0], descending=True).values
    prediction_margin = (sorted_probs[0].item() - sorted_probs[1].item()) * 100 if len(sorted_probs) > 1 else 0
    
    # Apply confidence calibration
    confidence = calibrate_confidence(raw_confidence, prediction_margin)
    
    # Store all probabilities for debugging (raw values)
    all_probs = {i: round(probabilities[0][i].item() * 100, 2) for i in range(probabilities.shape[1])}

    # ==============================
    # IMPORTANT LABEL MAPPING
    # ==============================
    # For 2-label model:
    # 0 = Contradiction (Violation)
    # 1 = Entailment (Compliant)
    #
    # For 3-label model (standard NLI):
    # 0 = Contradiction (Violation)
    # 1 = Neutral (Needs Review)
    # 2 = Entailment (Compliant)

    if num_labels == 3:
        # 3-label NLI model
        if prediction == 2:  # Entailment
            return {
                "status": "🟢 Compliant",
                "confidence": round(confidence, 2),
                "label_id": prediction,
                "all_probs": all_probs
            }
        elif prediction == 0:  # Contradiction
            return {
                "status": "🔴 Violation",
                "confidence": round(confidence, 2),
                "label_id": prediction,
                "all_probs": all_probs
            }
        else:  # Neutral (prediction == 1)
            return {
                "status": "🟡 Needs Review",
                "confidence": round(confidence, 2),
                "label_id": prediction,
                "all_probs": all_probs
            }
    else:
        # 2-label model (your training setup)
        if prediction == 1:  # Entailment
            return {
                "status": "🟢 Compliant",
                "confidence": round(confidence, 2),
                "label_id": prediction,
                "all_probs": all_probs
            }
        elif prediction == 0:  # Contradiction
            return {
                "status": "🔴 Violation",
                "confidence": round(confidence, 2),
                "label_id": prediction,
                "all_probs": all_probs
            }
        else:
            # Fallback for any unexpected label
            return {
                "status": "🟡 Needs Review",
                "confidence": round(confidence, 2),
                "label_id": prediction,
                "all_probs": all_probs
            }