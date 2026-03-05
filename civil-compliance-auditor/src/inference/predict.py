import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ==============================
# Load trained model once
# ==============================

model_path = "models/legal_nli_model"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

model.eval()  # Set to evaluation mode


# ==============================
# Prediction Function
# ==============================

def predict(premise, hypothesis):
    """
    Performs NLI prediction between legal rule (premise)
    and contract clause (hypothesis).

    Returns:
        {
            "status": "🟢 Compliant" or "🔴 Violation",
            "confidence": float (0-100),
            "label_id": int
        }
    """

    inputs = tokenizer(
        premise,
        hypothesis,
        return_tensors="pt",
        truncation=True,
        padding=True
    )

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    probabilities = F.softmax(logits, dim=1)

    prediction = torch.argmax(probabilities, dim=1).item()
    confidence = probabilities[0][prediction].item() * 100

    # ==============================
    # IMPORTANT LABEL MAPPING
    # ==============================
    # Based on training data analysis:
    # 0 = Entailment (Compliant)
    # 1 = Contradiction (Violation)

    if prediction == 0:
        return {
            "status": "🟢 Compliant",
            "confidence": round(confidence, 2),
            "label_id": prediction
        }

    elif prediction == 1:
        return {
            "status": "🔴 Violation",
            "confidence": round(confidence, 2),
            "label_id": prediction
        }