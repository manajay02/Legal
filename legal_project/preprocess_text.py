import re
import nltk
from pathlib import Path
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


def ensure_nltk_resources():
    resources = ['punkt', 'stopwords', 'wordnet', 'omw-1.4']
    project_root = Path(__file__).resolve().parents[1]
    venv_dir = project_root / '.venv'
    dest = venv_dir / 'nltk_data' if venv_dir.exists() else project_root / 'nltk_data'
    dest.mkdir(parents=True, exist_ok=True)

    # Make sure NLTK searches this path
    if str(dest) not in nltk.data.path:
        nltk.data.path.append(str(dest))

    for res in resources:
        try:
            nltk.data.find(res)
        except LookupError:
            print(f"NLTK resource '{res}' not found — downloading to {dest}...")
            try:
                nltk.download(res, download_dir=str(dest), quiet=True)
            except Exception as e:
                print(f"Failed to download {res}: {e}")
                print(f"Please run: python -c \"import nltk; nltk.download('{res}')\"")


# Ensure required NLTK data is available before using tokenizers/lemmatizer
ensure_nltk_resources()

# Load stopwords
stop_words = set(stopwords.words('english'))

# Keep important legal words
legal_keep = {'shall', 'may', 'court', 'plaintiff', 'defendant'}
stop_words = stop_words - legal_keep

lemmatizer = WordNetLemmatizer()


def clean_legal_noise(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'Page \d+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text


def preprocess_legal_text(text):
    text = clean_legal_noise(text)
    text = normalize_text(text)

    words = word_tokenize(text)
    words = [w for w in words if w not in stop_words and len(w) > 2]
    words = [lemmatizer.lemmatize(w) for w in words]

    return " ".join(words)


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    input_path = base_dir / "extracted_text" / "sample.txt"
    output_dir = base_dir / "processed_text"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "sample_clean.txt"

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    clean_text = preprocess_legal_text(raw_text)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(clean_text)

    print("Preprocessing completed successfully.")
