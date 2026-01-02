from pdfminer.high_level import extract_text

text = extract_text("sample.pdf")
print(text[:1000])  # preview
