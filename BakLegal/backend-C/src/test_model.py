from inference.predict import predict

premise = "Employees are entitled to maternity leave."
hypothesis = "No maternity leave shall be granted."

result = predict(premise, hypothesis)

print("Prediction:", result)