import joblib

# Load trained model and vectorizer
model = joblib.load("legal_classifier.pkl")
vectorizer = joblib.load("tfidf_vectorizer.pkl")

# Read test case text
with open("test_case.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Transform and predict
X = vectorizer.transform([text])
prediction = model.predict(X)

print("🔍 Predicted legal category:", prediction[0])
