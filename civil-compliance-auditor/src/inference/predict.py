import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load trained model
model_path = "models/legal_nli_model"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

def predict(premise, hypothesis):
    inputs = tokenizer(
        premise,
        hypothesis,
        return_tensors="pt",
        truncation=True,
        padding=True
    )

    with torch.no_grad():
        outputs = model(**inputs)

    prediction = torch.argmax(outputs.logits).item()

    if prediction == 0:
        return "🟢 Compliant"
    elif prediction == 1:
        return "🔴 Violation"