import os
from pdfminer.high_level import extract_text
from PIL import Image
import pytesseract
import fitz  # PyMuPDF

INPUT_DIR = "raw_pdfs"
OUTPUT_DIR = "extracted_text"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for pdf_file in os.listdir(INPUT_DIR):
    if not pdf_file.endswith(".pdf"):
        continue

    pdf_path = os.path.join(INPUT_DIR, pdf_file)
    output_txt = os.path.join(OUTPUT_DIR, pdf_file.replace(".pdf", ".txt"))

    text = extract_text(pdf_path)

    if text.strip():
        # Text-based PDF
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✔ Text extracted: {pdf_file}")
    else:
        # Scanned PDF → OCR
        doc = fitz.open(pdf_path)
        ocr_text = ""

        for page in doc:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_text += pytesseract.image_to_string(img)

        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(ocr_text)

        print(f"✔ OCR applied: {pdf_file}")

print("✅ All PDFs processed")
