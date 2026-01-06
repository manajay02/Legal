import os
import joblib
import numpy as np

# Load vectorizer
vectorizer = joblib.load("tfidf_vectorizer.pkl")

DATASET_DIR = "dataset"

case_texts = []
case_labels = []
case_names = []

for label in os.listdir(DATASET_DIR):
    label_path = os.path.join(DATASET_DIR, label)

    if not os.path.isdir(label_path):
        continue

    for file in os.listdir(label_path):
        with open(os.path.join(label_path, file), "r", encoding="utf-8") as f:
            case_texts.append(f.read())
            case_labels.append(label)
            case_names.append(file)

# Vectorize all cases
case_vectors = vectorizer.transform(case_texts)

# Save everything
joblib.dump(case_vectors, "case_vectors.pkl")
joblib.dump(case_labels, "case_labels.pkl")
joblib.dump(case_names, "case_names.pkl")

print("✅ Case similarity index built")
print("Total cases indexed:", len(case_names))
