"""
train_classifier.py
--------------------
Trains text classification models to predict the category and subcategory
of an unseen legal document.

Models saved to backend/models/:
  classifier_category.pkl    →  predicts  Civil | Criminal
  classifier_subcategory.pkl →  predicts  Administrative | Murder | ...

Algorithm: TF-IDF (unigrams+bigrams) + LinearSVC (fast, accurate for text)
"""

import os
import joblib
import numpy as np
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

# ── Config ────────────────────────────────────────────────────────────────────
MONGO_URI  = "mongodb://localhost:27017/"
DB_NAME    = "legal_cases_db"
COLLECTION = "cases"
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def load_data():
    print("Loading data from MongoDB...")
    client = MongoClient(MONGO_URI)
    col    = client[DB_NAME][COLLECTION]
    docs   = list(col.find({}, {"text": 1, "category": 1, "subcategory": 1, "_id": 0}))
    client.close()

    texts       = [d.get("text", "") for d in docs]
    categories  = [d["category"]    for d in docs]
    subcategories = [d["subcategory"] for d in docs]

    print(f"  Loaded {len(texts)} documents.")
    return texts, categories, subcategories


def train_pipeline(texts, labels, label_name: str) -> dict:
    """Train a TF-IDF + LinearSVC pipeline and return the artefact dict."""

    # Encode string labels → integers
    le = LabelEncoder()
    y  = le.fit_transform(labels)

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=30_000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
            analyzer="word",
            token_pattern=r"(?u)\b\w+\b",
            min_df=1,
        )),
        ("clf", LinearSVC(
            C=1.0,
            max_iter=2000,
            class_weight="balanced",   # handles imbalanced subcategories
        )),
    ])

    # Cross-validation (use min folds to handle small classes)
    n_classes  = len(le.classes_)
    min_count  = min(np.bincount(y))
    n_splits   = min(5, min_count)

    if n_splits >= 2:
        cv     = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        scores = cross_val_score(pipe, texts, y, cv=cv, scoring="accuracy")
        print(f"  [{label_name}] CV accuracy: {scores.mean():.3f} ± {scores.std():.3f}  (folds={n_splits})")
    else:
        print(f"  [{label_name}] Skipping CV — too few samples per class.")

    # Fit on full dataset
    pipe.fit(texts, y)

    return {
        "pipeline"      : pipe,
        "label_encoder" : le,
        "classes"       : list(le.classes_),
        "label_name"    : label_name,
    }


def train_all():
    texts, categories, subcategories = load_data()

    # ── Category classifier ───────────────────────────────────────────────────
    print("\nTraining CATEGORY classifier (Civil / Criminal)...")
    cat_artefact = train_pipeline(texts, categories, "category")
    path = os.path.join(MODELS_DIR, "classifier_category.pkl")
    joblib.dump(cat_artefact, path, compress=3)
    print(f"  Saved → {path}")
    print(f"  Classes: {cat_artefact['classes']}")

    # ── Subcategory classifier ────────────────────────────────────────────────
    print("\nTraining SUBCATEGORY classifier (28 classes)...")
    sub_artefact = train_pipeline(texts, subcategories, "subcategory")
    path = os.path.join(MODELS_DIR, "classifier_subcategory.pkl")
    joblib.dump(sub_artefact, path, compress=3)
    print(f"  Saved → {path}")
    print(f"  Classes ({len(sub_artefact['classes'])}): {sub_artefact['classes']}")

    # ── Full report on training data ──────────────────────────────────────────
    print("\n── Category report (train set) ──")
    y_cat_true = cat_artefact["label_encoder"].transform(categories)
    y_cat_pred = cat_artefact["pipeline"].predict(
        cat_artefact["pipeline"].named_steps["tfidf"].transform(texts)
        if False else texts   # use pipeline.predict directly
    )
    y_cat_pred = cat_artefact["pipeline"].predict(texts)
    print(classification_report(y_cat_true, y_cat_pred,
                                target_names=cat_artefact["classes"], zero_division=0))

    print("\n── Subcategory report (train set) ──")
    y_sub_true = sub_artefact["label_encoder"].transform(subcategories)
    y_sub_pred = sub_artefact["pipeline"].predict(texts)
    print(classification_report(y_sub_true, y_sub_pred,
                                target_names=sub_artefact["classes"], zero_division=0))

    print("\nAll classifiers saved to:", MODELS_DIR)


if __name__ == "__main__":
    train_all()
