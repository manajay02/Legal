from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

MODEL_PATH = "legal_nli_model"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

label_map = {0: "CONTRADICTION", 1: "ENTAILMENT"}

def predict_nli(premise, hypothesis):
    inputs = tokenizer(
        premise,
        hypothesis,
        return_tensors="pt",
        truncation=True,
        padding=True
    )

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits.squeeze(0)
    probs = F.softmax(logits, dim=-1)
    pred_id = int(torch.argmax(probs).item())
    confidence = float(probs[pred_id].item())
    label = label_map[pred_id]
    return label, confidence


if __name__ == "__main__":
    premise = "Employees are entitled to maternity leave under Sri Lankan law."
    hypothesis = "No maternity leave shall be granted to employees."
    label, conf = predict_nli(premise, hypothesis)
    print("Prediction:", label, "Confidence:", round(conf, 3))