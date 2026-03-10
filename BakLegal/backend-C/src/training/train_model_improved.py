import pandas as pd
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# Load train and test data
train_df = pd.read_csv("data/training_pairs/train.csv")
test_df = pd.read_csv("data/training_pairs/test.csv")

# Convert to HuggingFace Dataset
train_dataset = Dataset.from_pandas(train_df)
test_dataset = Dataset.from_pandas(test_df)

# Load Legal-BERT
model_name = "nlpaueb/legal-bert-base-uncased"

tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize_function(example):
    return tokenizer(
        example["Premise"],
        example["Hypothesis"],
        padding="max_length",
        truncation=True,
        max_length=256  # Slightly shorter for efficiency
    )

train_dataset = train_dataset.map(tokenize_function, batched=True)
test_dataset = test_dataset.map(tokenize_function, batched=True)

train_dataset = train_dataset.rename_column("Label", "labels")
test_dataset = test_dataset.rename_column("Label", "labels")

train_dataset.set_format(
    type="torch",
    columns=["input_ids", "attention_mask", "labels"]
)

test_dataset.set_format(
    type="torch",
    columns=["input_ids", "attention_mask", "labels"]
)


# Load model (2 classes)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=2
)

# Metrics function
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average='binary'
    )
    acc = accuracy_score(labels, predictions)
    return {
        "accuracy": acc,
        "f1": f1,
        "precision": precision,
        "recall": recall
    }

# IMPROVED TRAINING ARGUMENTS
training_args = TrainingArguments(
    output_dir="./models/legal_nli_model_v2",  # Save to new location
    evaluation_strategy="epoch",
    save_strategy="epoch",
    logging_dir="./logs_v2",
    
    # Lower learning rate for better fine-tuning
    learning_rate=5e-6,
    
    # Smaller batch with gradient accumulation = effective batch 16
    per_device_train_batch_size=4,
    per_device_eval_batch_size=8,
    gradient_accumulation_steps=4,
    
    # More epochs for small dataset
    num_train_epochs=15,
    
    # Warmup helps stabilize training
    warmup_ratio=0.1,
    
    # Regularization
    weight_decay=0.01,
    
    # Best model selection
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    greater_is_better=True,
    
    # Seed for reproducibility
    seed=42,
    
    # Logging
    logging_steps=10,
)

# Early stopping to prevent overfitting
early_stopping = EarlyStoppingCallback(
    early_stopping_patience=5,
    early_stopping_threshold=0.001
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics,
    callbacks=[early_stopping]
)

print("Starting improved training...")
trainer.train()

# Evaluate final model
print("\nFinal Evaluation:")
results = trainer.evaluate()
print(f"Accuracy: {results['eval_accuracy']*100:.2f}%")
print(f"F1 Score: {results['eval_f1']*100:.2f}%")

# Save final model to v2 location (does not overwrite original)
model.save_pretrained("./models/legal_nli_model_v2")
tokenizer.save_pretrained("./models/legal_nli_model_v2")

print("\nTraining completed! Model saved to ./models/legal_nli_model_v2")
print("Your original model in ./models/legal_nli_model is untouched.")
print("\nIf accuracy is good, you can replace the original model by running:")
print("  Copy-Item -Path './models/legal_nli_model_v2/*' -Destination './models/legal_nli_model/' -Recurse -Force")
