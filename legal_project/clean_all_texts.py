import os
from preprocess_text import preprocess_legal_text

INPUT_DIR = "extracted_text"
OUTPUT_DIR = "clean_text"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for file in os.listdir(INPUT_DIR):
    with open(os.path.join(INPUT_DIR, file), "r", encoding="utf-8") as f:
        raw = f.read()

    clean = preprocess_legal_text(raw)

    with open(os.path.join(OUTPUT_DIR, file), "w", encoding="utf-8") as f:
        f.write(clean)

print("✅ All texts cleaned")
