import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

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
    confidence = probabilities[0][prediction].item() * 100
    
    # Store all probabilities for debugging
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