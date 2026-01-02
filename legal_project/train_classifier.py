import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

DATASET_DIR = "dataset"

texts = []
labels = []

# Load dataset
for label in os.listdir(DATASET_DIR):
    label_path = os.path.join(DATASET_DIR, label)

    if not os.path.isdir(label_path):
        continue

    for file in os.listdir(label_path):
        file_path = os.path.join(label_path, file)
        with open(file_path, "r", encoding="utf-8") as f:
            texts.append(f.read())
            labels.append(label)

print("Samples:", len(texts))
print("Labels:", set(labels))

# Vectorize text (NO pretrained embeddings)
vectorizer = TfidfVectorizer(
    max_features=6000,
    ngram_range=(1, 2),
    min_df=2
)

X = vectorizer.fit_transform(texts)

# Train/Test split
X_train, X_test, y_train, y_test = train_test_split(
    X, labels, test_size=0.2, random_state=42
)

# Train classifier
model = LogisticRegression(max_iter=2000)

model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("\n📊 Classification Report:\n")
print(classification_report(y_test, y_pred))

# Save model
joblib.dump(model, "legal_classifier.pkl")
joblib.dump(vectorizer, "tfidf_vectorizer.pkl")

print("✅ Legal classifier trained and saved successfully")
