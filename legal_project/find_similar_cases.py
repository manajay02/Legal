import joblib
from sklearn.metrics.pairwise import cosine_similarity

# Load everything
vectorizer = joblib.load("tfidf_vectorizer.pkl")
case_vectors = joblib.load("case_vectors.pkl")
case_labels = joblib.load("case_labels.pkl")
case_names = joblib.load("case_names.pkl")

# Read new case
with open("test_case.txt", "r", encoding="utf-8") as f:
    new_case = f.read()

# Vectorize new case
new_vector = vectorizer.transform([new_case])

# Compute similarity
similarities = cosine_similarity(new_vector, case_vectors)[0]

# Get top 5 similar cases
top_indices = similarities.argsort()[-5:][::-1]

print("\n🔍 Top Similar Cases:\n")

for idx in top_indices:
    print(f"Case: {case_names[idx]}")
    print(f"Category: {case_labels[idx]}")
    print(f"Similarity Score: {similarities[idx]:.2f}")
    print("-" * 40)
