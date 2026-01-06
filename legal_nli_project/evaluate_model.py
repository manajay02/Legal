import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import accuracy_score, classification_report

# --------------------------------------------------
# Load trained model
# --------------------------------------------------

MODEL_PATH = "legal_nli_model"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

model.eval()

LABEL_MAP = {
    0: "CONTRADICTION",
    1: "ENTAILMENT"
}

REVERSE_LABEL_MAP = {
    "CONTRADICTION": 0,
    "ENTAILMENT": 1
}

# --------------------------------------------------
# Load test dataset
# --------------------------------------------------

df = pd.read_csv("test_dataset.csv")

premises = df["Premise"].tolist()
hypotheses = df["Hypothesis"].tolist()
true_labels = df["Label"].map(REVERSE_LABEL_MAP).tolist()


# --------------------------------------------------
# Prediction loop
# --------------------------------------------------

predicted_labels = []

for premise, hypothesis in zip(premises, hypotheses):
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

    prediction = torch.argmax(outputs.logits, dim=1).item()
    predicted_labels.append(prediction)

# --------------------------------------------------
# Evaluation metrics
# --------------------------------------------------

accuracy = accuracy_score(true_labels, predicted_labels)

print("\n✅ MODEL EVALUATION RESULTS\n")
print(f"Accuracy: {accuracy:.4f}\n")

print("📊 Classification Report:")
print(
    classification_report(
        true_labels,
        predicted_labels,
        target_names=["CONTRADICTION", "ENTAILMENT"]
    )
)
