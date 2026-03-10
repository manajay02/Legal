import os
import csv
import sys

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    os.system(f"{sys.executable} -m pip install pdfplumber")
    import pdfplumber

DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dataset")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "legal_cases.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"  [ERROR] Could not read {pdf_path}: {e}")
    return text.strip()


def build_dataset():
    rows = []
    total = 0
    errors = 0

    print(f"Scanning dataset directory: {DATASET_DIR}\n")

    for category in sorted(os.listdir(DATASET_DIR)):
        category_path = os.path.join(DATASET_DIR, category)
        if not os.path.isdir(category_path):
            continue

        for subcategory in sorted(os.listdir(category_path)):
            subcategory_path = os.path.join(category_path, subcategory)
            if not os.path.isdir(subcategory_path):
                continue

            pdf_files = [f for f in os.listdir(subcategory_path) if f.lower().endswith(".pdf")]
            print(f"[{category}] {subcategory}: {len(pdf_files)} files")

            for pdf_file in pdf_files:
                pdf_path = os.path.join(subcategory_path, pdf_file)
                text = extract_text_from_pdf(pdf_path)
                total += 1

                if not text:
                    errors += 1

                rows.append({
                    "filename": pdf_file,
                    "category": category,
                    "subcategory": subcategory,
                    "text": text
                })

    print(f"\nWriting {len(rows)} records to {OUTPUT_FILE} ...")
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["filename", "category", "subcategory", "text"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone! Dataset saved to: {OUTPUT_FILE}")
    print(f"  Total files processed : {total}")
    print(f"  Files with no text    : {errors}")


if __name__ == "__main__":
    build_dataset()
