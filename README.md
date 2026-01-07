# Legal Case Classification & Similarity System

A machine learning-powered legal document analysis system that classifies legal cases into categories and finds similar cases using NLP techniques.

## 📋 Overview

This project provides tools for:
- **PDF Text Extraction** - Extract text from legal PDFs (including scanned documents via OCR)
- **Text Preprocessing** - Clean and normalize legal text using NLP techniques
- **Case Classification** - Classify legal cases into predefined categories using ML
- **Similar Case Search** - Find similar cases using TF-IDF vectorization and cosine similarity

## 🏗️ Project Structure

```
legal_project/
├── extract_text_pdf.py      # Extract text from a single PDF
├── extract_all_pdfs.py      # Batch extract text from all PDFs (with OCR support)
├── preprocess_text.py       # Text cleaning and normalization utilities
├── clean_all_texts.py       # Batch preprocess all extracted texts
├── train_classifier.py      # Train the legal case classifier
├── predict_case.py          # Predict category for a new case
├── build_case_index.py      # Build similarity search index
├── find_similar_cases.py    # Find similar cases to a query
├── test_case.txt            # Sample test case for prediction
├── requirements.txt         # Python dependencies
├── dataset/                 # Training data organized by category
│   ├── asset/
│   ├── civil/
│   ├── contemptofcourt/
│   ├── criminal/
│   ├── drug/
│   ├── environmental/
│   ├── family/
│   ├── financial/
│   ├── labour/
│   ├── sexualcases/
│   ├── sports/
│   ├── tax/
│   └── terrorism/
├── raw_pdfs/                # Input PDF files
├── extracted_text/          # Extracted text from PDFs
├── clean_text/              # Preprocessed clean text
└── processed_text/          # Additional processed text
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Tesseract OCR (for scanned PDFs)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Legal.git
   cd Legal/legal_project
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Tesseract OCR** (for scanned PDF support)
   - Windows: Download from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt install tesseract-ocr`
   - macOS: `brew install tesseract`

4. **Download NLTK resources** (auto-downloaded on first run)
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
   ```

## 📖 Usage

### 1. Extract Text from PDFs

**Single PDF:**
```bash
python extract_text_pdf.py
```

**Batch extraction (all PDFs in `raw_pdfs/`):**
```bash
python extract_all_pdfs.py
```

### 2. Preprocess Text

Clean and normalize all extracted texts:
```bash
python clean_all_texts.py
```

### 3. Train the Classifier

Train the legal case classifier on your dataset:
```bash
python train_classifier.py
```

This will generate:
- `legal_classifier.pkl` - Trained model
- `tfidf_vectorizer.pkl` - TF-IDF vectorizer

### 4. Predict Case Category

Place your case text in `test_case.txt` and run:
```bash
python predict_case.py
```

### 5. Find Similar Cases

First, build the case index:
```bash
python build_case_index.py
```

Then find similar cases:
```bash
python find_similar_cases.py
```

## 🏷️ Supported Legal Categories

| Category | Description |
|----------|-------------|
| Asset | Property and asset-related cases |
| Civil | Civil law cases |
| Contempt of Court | Court contempt cases |
| Criminal | Criminal law cases |
| Drug | Drug-related offenses |
| Environmental | Environmental law cases |
| Family | Family law matters |
| Financial | Financial crimes and disputes |
| Labour | Employment and labor law |
| Sexual Cases | Sexual offense cases |
| Sports | Sports law cases |
| Tax | Tax-related cases |
| Terrorism | Terrorism-related cases |

## 🔧 Technical Details

### Text Preprocessing Pipeline
1. Remove page numbers and extra whitespace
2. Convert to lowercase
3. Remove special characters
4. Tokenize text
5. Remove stopwords (preserving legal terms like "shall", "may", "court")
6. Lemmatize words

### Machine Learning
- **Vectorization:** TF-IDF with bigrams (max 6000 features)
- **Classifier:** Logistic Regression
- **Similarity:** Cosine similarity on TF-IDF vectors

## 📦 Dependencies

- `Flask` - Web framework
- `pdfminer.six` - PDF text extraction
- `scikit-learn` - Machine learning
- `joblib` - Model serialization
- `nltk` - Natural language processing
- `pytesseract` - OCR support
- `PyMuPDF` - PDF processing
- `Pillow` - Image processing

## 👤 Author

**IT22361868**

## 📄 License

This project is for educational purposes.
