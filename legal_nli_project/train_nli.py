import pandas as pd
import numpy as np
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)
from sklearn.preprocessing import LabelEncoder
import torch

# =========================
# STEP 1 — Load datasets
# =========================
train_df = pd.read_csv("train_dataset.csv")
val_df = pd.read_csv("validation_dataset.csv")

# =========================
# STEP 2 — Clean labels
# =========================
# Fix casing issues like ENTAILMENt
train_df["Label"] = train_df["Label"].str.upper().str.strip()
val_df["Label"] = val_df["Label"].str.upper().str.strip()

# =========================
# STEP 3 — Encode labels
# =========================
label_encoder = LabelEncoder()
train_df["label"] = label_encoder.fit_transform(train_df["Label"])
val_df["label"] = label_encoder.transform(val_df["Label"])

print("Labels:", list(label_encoder.classes_))

num_labels = len(label_encoder.classes_)

# =========================
# STEP 4 — Convert to HuggingFace Dataset
# =========================
train_dataset = Dataset.from_pandas(
    train_df[["Premise", "Hypothesis", "label"]]
)
val_dataset = Dataset.from_pandas(
    val_df[["Premise", "Hypothesis", "label"]]
)

# =========================
# STEP 5 — Load tokenizer & model
# =========================
model_name = "roberta-base"   # later you can switch to legal-bert

tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=num_labels
)

# =========================
# STEP 6 — Tokenization function
# =========================
def tokenize_function(example):
    return tokenizer(
        example["Premise"],
        example["Hypothesis"],
        truncation=True,
        padding="max_length",
        max_length=256
    )

train_dataset = train_dataset.map(tokenize_function, batched=True)
val_dataset = val_dataset.map(tokenize_function, batched=True)

# =========================
# STEP 7 — Training arguments (UPDATED)
# =========================
training_args = TrainingArguments(
    output_dir="./results",
    eval_strategy="epoch",          # ✅ FIXED
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=50,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    report_to="none"
)

# =========================
# STEP 8 — Trainer
# =========================
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer
)

# =========================
# STEP 9 — Train model
# =========================
trainer.train()

# =========================
# STEP 10 — Save model
# =========================
trainer.save_model("legal_nli_model")
tokenizer.save_pretrained("legal_nli_model")

print("✅ Training complete. Model saved to 'legal_nli_model/'")
