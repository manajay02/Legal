"""
app.py  –  Flask REST API for Legal Case Similarity Search
-----------------------------------------------------------
Endpoints:
  GET  /                          Serves the frontend
  GET  /api/categories            List all categories + subcategories
  GET  /api/filenames             List filenames (filter by ?category=&subcategory=)
  POST /api/search                Find similar cases
  GET  /api/models                List trained models
  POST /api/add_case              Add a new case with classification
"""

import os
import io
import hashlib
import json
import numpy as np
import joblib
import pdfplumber
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from similarity_search import SimilarityEngine

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
MODELS_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
UPLOADS_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
DATASET_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dataset")
HASH_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content_hashes.json")
MONGO_TIMEOUT_MS = 2000  # 2 second timeout
os.makedirs(UPLOADS_DIR, exist_ok=True)


# ── Content Hash Cache for duplicate detection ────────────────────────────────
_hash_cache = {}  # {hash: {"filename": str, "category": str, "subcategory": str}}


def _load_hash_cache():
    """Load hash cache from file."""
    global _hash_cache
    if os.path.exists(HASH_CACHE_FILE):
        try:
            with open(HASH_CACHE_FILE, 'r', encoding='utf-8') as f:
                _hash_cache = json.load(f)
            print(f"[INFO] Loaded {len(_hash_cache)} content hashes from cache.")
        except Exception as e:
            print(f"[WARNING] Failed to load hash cache: {e}")
            _hash_cache = {}


def _save_hash_cache():
    """Save hash cache to file."""
    try:
        with open(HASH_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_hash_cache, f, indent=2)
    except Exception as e:
        print(f"[WARNING] Failed to save hash cache: {e}")


def _compute_text_hash(text: str) -> str:
    """Normalize and hash text content."""
    normalised = " ".join(text.split()).strip().lower()
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def _extract_pdf_text_from_path(pdf_path: str) -> str:
    """Extract text from a PDF file path."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"  [ERROR] Failed to read {pdf_path}: {e}")
    return text.strip()


def _build_hash_cache_from_dataset():
    """Build hash cache by scanning all PDFs in dataset folder."""
    global _hash_cache
    print("[INFO] Building content hash cache from dataset...")
    count = 0
    
    if not os.path.exists(DATASET_DIR):
        print(f"[WARNING] Dataset folder not found: {DATASET_DIR}")
        return
    
    for category in os.listdir(DATASET_DIR):
        cat_path = os.path.join(DATASET_DIR, category)
        if not os.path.isdir(cat_path):
            continue
        
        for subcategory in os.listdir(cat_path):
            sub_path = os.path.join(cat_path, subcategory)
            if not os.path.isdir(sub_path):
                continue
            
            pdfs = [f for f in os.listdir(sub_path) if f.lower().endswith('.pdf')]
            for pdf_name in pdfs:
                pdf_path = os.path.join(sub_path, pdf_name)
                text = _extract_pdf_text_from_path(pdf_path)
                if len(text) > 100:
                    text_hash = _compute_text_hash(text)
                    _hash_cache[text_hash] = {
                        "filename": pdf_name,
                        "category": category,
                        "subcategory": subcategory,
                        "path": pdf_path
                    }
                    count += 1
    
    _save_hash_cache()
    print(f"[INFO] Built hash cache with {count} documents.")


def check_duplicate(text: str) -> dict | None:
    """
    Check if text content already exists in the dataset.
    Returns the existing document info if duplicate, None otherwise.
    """
    text_hash = _compute_text_hash(text)
    return _hash_cache.get(text_hash)


# Load hash cache at startup (or build it if empty/missing)
_load_hash_cache()
if not _hash_cache:
    print("[INFO] Hash cache is empty. Building from dataset...")
    _build_hash_cache_from_dataset()

# ── Load classifiers once at startup ─────────────────────────────────────────
try:
    _cat_model = joblib.load(os.path.join(MODELS_DIR, "classifier_category.pkl"))
    _sub_model = joblib.load(os.path.join(MODELS_DIR, "classifier_subcategory.pkl"))
except FileNotFoundError as _e:
    print(f"[WARNING] Classifier models not found: {_e}")
    print("[WARNING] Run 'python train_classifier.py' first. /api/classify and /api/add_case will be unavailable.")
    _cat_model = None
    _sub_model = None

try:
    _legal_detector = joblib.load(os.path.join(MODELS_DIR, "legal_detector.pkl"))["pipeline"]
    print("[INFO] Legal document detector loaded.")
except FileNotFoundError:
    print("[WARNING] legal_detector.pkl not found. Run 'python train_legal_detector.py'.")
    _legal_detector = None


def extract_pdf_text(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text.strip()


def _softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()


# ── Legal-document gate: 5 universal words ───────────────────────────────────
# Every single Sri Lankan court document (across all 117 analysed cases)
# contains ALL of these 5 words. If any one is absent the document is not a
# Sri Lankan court case and is rejected immediately — no ML needed.
_REQUIRED_LEGAL_WORDS = ["court", "judge", "sri", "socialist", "republic"]
_LEGAL_CONFIDENCE_THRESHOLD = 0.50


def _compute_legal_confidence(text: str) -> float:
    """Check whether all 5 universal Sri Lankan court-document words are present.

    Returns:
        1.0  – all 5 words found  → proceed to classification
        0.0  – one or more words missing → reject as non-legal
    """
    if not text:
        return 0.0
    t = text.lower()
    missing = [w for w in _REQUIRED_LEGAL_WORDS if w not in t]
    if missing:
        return 0.0
    return 1.0


def classify_text(text: str) -> dict:
    if _cat_model is None or _sub_model is None:
        raise RuntimeError("Classifier models not loaded. Run 'python train_classifier.py' first.")
    cat_pred   = _cat_model["pipeline"].predict([text])[0]
    cat_label  = str(_cat_model["label_encoder"].inverse_transform([cat_pred])[0])
    raw_cat    = _cat_model["pipeline"].decision_function([text])[0]
    # Binary SVC returns a scalar; convert to 2-element array [neg, pos]
    if np.ndim(raw_cat) == 0:
        raw_cat = np.array([-float(raw_cat), float(raw_cat)])
    cat_conf  = _softmax(raw_cat)
    cat_probs = {str(cls): round(float(p), 4) for cls, p in zip(_cat_model["classes"], cat_conf)}

    sub_pred   = _sub_model["pipeline"].predict([text])[0]
    sub_label  = str(_sub_model["label_encoder"].inverse_transform([sub_pred])[0])
    raw_sub    = _sub_model["pipeline"].decision_function([text])[0]
    if np.ndim(raw_sub) == 0:
        raw_sub = np.array([-float(raw_sub), float(raw_sub)])
    sub_conf  = _softmax(raw_sub)
    sub_probs  = sorted(
        {str(cls): round(float(p), 4) for cls, p in zip(_sub_model["classes"], sub_conf)}.items(),
        key=lambda x: -x[1]
    )[:5]

    return {
        "category"            : cat_label,
        "subcategory"         : sub_label,
        "category_confidence" : cat_probs,
        "subcategory_top5"    : sub_probs,
    }

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)


# ── Serve frontend ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")
# ── GET /api/pdf/<filename> ────────────────────────────────────────────────
@app.route("/api/pdf/<path:filename>")
def get_pdf(filename):
    # 1. Check uploads folder first (newly added cases)
    upload_path = os.path.join(UPLOADS_DIR, filename)
    if os.path.isfile(upload_path):
        return send_from_directory(UPLOADS_DIR, filename)

    # 2. Search the dataset folder tree
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dataset")
    for root, dirs, files in os.walk(base_dir):
        if filename in files:
            return send_from_directory(root, filename)

    # 3. Fall back to MongoDB text for any file not found on disk (render as PDF-like HTML)
    if not _mongo_available:
        return jsonify({"error": "PDF not found."}), 404
    
    doc = _col.find_one({"filename": filename}, {"text": 1, "category": 1, "subcategory": 1, "_id": 0})
    if doc and doc.get("text"):
        import html as htmllib
        raw = doc["text"]
        cat = doc.get("category", "")
        sub = doc.get("subcategory", "")
        # Convert paragraphs: blank lines → paragraph breaks
        paragraphs = []
        for para in raw.split("\n\n"):
            lines = [htmllib.escape(l) for l in para.splitlines()]
            paragraphs.append("<br>".join(lines))
        body_html = "".join(f"<p>{p}</p>" for p in paragraphs if p.strip())
        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>{htmllib.escape(filename)}</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    html,body{{height:100%;background:#525659;font-family:Georgia,"Times New Roman",serif}}
    #toolbar{{
      position:fixed;top:0;left:0;right:0;height:48px;background:#323639;
      display:flex;align-items:center;gap:16px;padding:0 20px;z-index:100;
      color:#fff;font-family:Arial,sans-serif;font-size:13px;box-shadow:0 2px 6px rgba(0,0,0,.4)
    }}
    #toolbar .badge{{
      background:#4a90d9;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;letter-spacing:.5px
    }}
    #toolbar .title{{font-size:13px;opacity:.85;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:50vw}}
    #viewer{{padding:60px 0 40px;display:flex;flex-direction:column;align-items:center;gap:24px}}
    .page{{
      background:#fff;width:210mm;min-height:297mm;
      padding:25mm 25mm 25mm 30mm;
      box-shadow:0 4px 20px rgba(0,0,0,.5);
      position:relative;color:#111;line-height:1.85;font-size:13.5px;
      word-break:break-word;
    }}
    .page p{{margin-bottom:0.9em;text-align:justify}}
    .page p:empty{{display:none}}
    #print-btn{{
      background:#4a90d9;color:#fff;border:none;padding:8px 18px;
      border-radius:6px;cursor:pointer;font-size:13px;font-family:Arial,sans-serif
    }}
    #print-btn:hover{{background:#357abd}}
    @media print{{
      #toolbar{{display:none}}
      #viewer{{padding:0;background:#fff}}
      .page{{box-shadow:none;margin:0;width:100%;min-height:auto;padding:20mm}}
    }}
  </style>
</head>
<body>
  <div id="toolbar">
    <span>⚖️</span>
    <span class="title">{htmllib.escape(filename)}</span>
    <span class="badge">{htmllib.escape(cat)} › {htmllib.escape(sub)}</span>
    <span style="flex:1"></span>
    <button id="print-btn" onclick="window.print()">🖨 Print</button>
  </div>
  <div id="viewer">
    <div class="page">{body_html}</div>
  </div>
</body>
</html>"""
        from flask import Response
        return Response(page, mimetype="text/html")

    return jsonify({"error": "PDF not found."}), 404

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)

# ── Shared resources ──────────────────────────────────────────────────────────
_mongo_available = False
_client = None
_col = None

try:
    _client = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=MONGO_TIMEOUT_MS,
        connectTimeoutMS=MONGO_TIMEOUT_MS
    )
    _client.admin.command('ping')
    _col = _client["legal_cases_db"]["cases"]
    _mongo_available = True
    print("[INFO] MongoDB connected successfully (app.py).")
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"[WARNING] MongoDB not available (app.py): {e}")
    print("[WARNING] Some features will be limited.")

_engine = SimilarityEngine()


# ── GET /api/categories ───────────────────────────────────────────────────────
@app.route("/api/categories")
def get_categories():
    if not _mongo_available:
        # Scan dataset folder directly when MongoDB is unavailable
        result = {}
        if os.path.exists(DATASET_DIR):
            for category in os.listdir(DATASET_DIR):
                cat_path = os.path.join(DATASET_DIR, category)
                if not os.path.isdir(cat_path):
                    continue
                for subcategory in os.listdir(cat_path):
                    sub_path = os.path.join(cat_path, subcategory)
                    if not os.path.isdir(sub_path):
                        continue
                    # Count PDF files
                    pdf_count = len([f for f in os.listdir(sub_path) if f.lower().endswith('.pdf')])
                    if pdf_count > 0:
                        result.setdefault(category, []).append({"subcategory": subcategory, "count": pdf_count})
        return jsonify(result)
    
    pipeline = [
        {"$group": {
            "_id": {"category": "$category", "subcategory": "$subcategory"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.category": 1, "_id.subcategory": 1}}
    ]
    result: dict = {}
    for doc in _col.aggregate(pipeline):
        cat    = doc["_id"]["category"]
        subcat = doc["_id"]["subcategory"]
        result.setdefault(cat, []).append({"subcategory": subcat, "count": doc["count"]})
    return jsonify(result)


# ── GET /api/filenames ────────────────────────────────────────────────────────
@app.route("/api/filenames")
def get_filenames():
    if not _mongo_available:
        # List PDF files from dataset folder
        filt_cat = request.args.get("category")
        filt_sub = request.args.get("subcategory")
        files = []
        if os.path.exists(DATASET_DIR) and filt_cat and filt_sub:
            sub_path = os.path.join(DATASET_DIR, filt_cat, filt_sub)
            if os.path.isdir(sub_path):
                files = sorted([f for f in os.listdir(sub_path) if f.lower().endswith('.pdf')])
        return jsonify(files)
    
    filt = {}
    if cat := request.args.get("category"):
        filt["category"] = cat
    if sub := request.args.get("subcategory"):
        filt["subcategory"] = sub
    return jsonify(sorted(_col.distinct("filename", filt)))


# ── POST /api/search ──────────────────────────────────────────────────────────
@app.route("/api/search", methods=["POST"])
def search():
    data          = request.get_json(force=True)
    filename      = data.get("filename")    or None
    text          = data.get("text")        or None
    category      = data.get("category")   or None
    subcategory   = data.get("subcategory") or None
    global_search = bool(data.get("global_search", False))
    top_n         = int(data.get("top_n", 5))

    if not filename and not text:
        return jsonify({"error": "Provide 'filename' or 'text'."}), 400
    if not global_search and (not category or not subcategory):
        return jsonify({"error": "Provide 'category' and 'subcategory', or use global_search."}), 400

    try:
        results = _engine.find_similar(
            filename=filename, text=text,
            category=category, subcategory=subcategory,
            global_search=global_search, top_n=top_n,
        )
        return jsonify({"results": results})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500


# ── POST /api/classify ────────────────────────────────────────────────────────
@app.route("/api/classify", methods=["POST"])
def classify():
    """
    Accepts either:
      - multipart/form-data with a 'file' field (PDF)
      - application/json with a 'text' field
    Returns predicted category, subcategory, and confidence scores.
    """
    text = None

    if request.files.get("file"):
        f = request.files["file"]
        if not f.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported."}), 400
        try:
            text = extract_pdf_text(f.read())
        except Exception as e:
            return jsonify({"error": f"Failed to read PDF: {e}"}), 400
    else:
        data = request.get_json(force=True, silent=True) or {}
        text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "No readable text found in the document."}), 400

    legal_conf = _compute_legal_confidence(text)
    if legal_conf < _LEGAL_CONFIDENCE_THRESHOLD:
        t_lower = text.lower()
        missing = [w for w in _REQUIRED_LEGAL_WORDS if w not in t_lower]
        return jsonify({
            "error": (
                f"This is not a Sri Lankan legal document. "
                f"Required word(s) not found: {', '.join(missing)}. "
                f"Every court case must contain: {', '.join(_REQUIRED_LEGAL_WORDS)}."
            ),
            "missing_words": missing,
            "not_legal": True,
        }), 400

    try:
        result = classify_text(text)
        result["legal_confidence"] = round(legal_conf, 4)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Classification failed: {e}"}), 500


# ── GET /api/models ───────────────────────────────────────────────────────────
@app.route("/api/models")
def get_models():
    return jsonify(sorted(_engine.list_available_models()))


@app.route("/api/add_case", methods=["POST"])
def add_case():
    """
    Accepts either:
      - multipart/form-data with a 'file' field (PDF) and optional 'filename'
      - application/json with 'text' and optional 'filename'
    Classifies and stores the case. Works with MongoDB or file-based storage.
    """
    text = None
    filename = None
    file_bytes = None

    if request.files.get("file"):
        f = request.files["file"]
        filename = f.filename or None
        if not f.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported."}), 400
        try:
            file_bytes = f.read()
            text = extract_pdf_text(file_bytes)
        except Exception as e:
            return jsonify({"error": f"Failed to read PDF: {e}"}), 400
    else:
        data = request.get_json(force=True, silent=True) or {}
        text = (data.get("text") or "").strip()
        filename = data.get("filename") or None

    if not text:
        return jsonify({"error": "No readable text found."}), 400

    # ── Legal-document confidence gate ────────────────────────────────────────
    legal_conf = _compute_legal_confidence(text)
    if legal_conf < _LEGAL_CONFIDENCE_THRESHOLD:
        t_lower = text.lower()
        missing = [w for w in _REQUIRED_LEGAL_WORDS if w not in t_lower]
        return jsonify({
            "error": (
                f"This is not a Sri Lankan legal document. "
                f"Required word(s) not found: {', '.join(missing)}. "
                f"Every court case must contain: {', '.join(_REQUIRED_LEGAL_WORDS)}."
            ),
            "missing_words": missing,
            "not_legal": True,
        }), 400

    # ── Duplicate check using hash cache (works without MongoDB) ──
    text_hash = _compute_text_hash(text)
    
    # Check file-based hash cache first
    existing = _hash_cache.get(text_hash)
    if existing:
        return jsonify({
            "error": f"This document already exists in the database as '{existing['filename']}' in {existing['category']}/{existing['subcategory']}. Duplicate content is not allowed.",
            "duplicate": True,
            "existing_file": existing
        }), 409

    # Also check MongoDB if available
    if _mongo_available:
        mongo_existing = _col.find_one({
            "$or": [
                {"content_hash": text_hash},
                {"text": text}
            ]
        })
        if mongo_existing:
            if not mongo_existing.get("content_hash"):
                _col.update_one({"_id": mongo_existing["_id"]}, {"$set": {"content_hash": text_hash}})
            return jsonify({
                "error": "This document already exists in the database. Duplicate content is not allowed.",
                "duplicate": True
            }), 409

    # ── Classify the text ──
    try:
        result = classify_text(text)
    except Exception as e:
        return jsonify({"error": f"Classification failed: {e}"}), 500

    category = result["category"]
    subcategory = result["subcategory"]

    # ── Store the case ──
    if _mongo_available:
        # MongoDB storage
        try:
            doc = {
                "text": text,
                "category": category,
                "subcategory": subcategory,
                "filename": filename or f"case_{_col.count_documents({})+1}.txt",
                "content_hash": text_hash
            }
            _col.insert_one(doc)
            doc.pop("_id", None)
            
            # Also update hash cache
            _hash_cache[text_hash] = {
                "filename": doc["filename"],
                "category": category,
                "subcategory": subcategory
            }
            _save_hash_cache()
            
            return jsonify({"success": True, "case": doc, "classification": result})
        except Exception as e:
            return jsonify({"error": f"Failed to add case: {e}"}), 500
    else:
        # File-based storage (save to dataset folder)
        try:
            # Create category/subcategory folder if needed
            target_dir = os.path.join(DATASET_DIR, category, subcategory)
            os.makedirs(target_dir, exist_ok=True)
            
            # Generate unique filename
            if filename:
                base_name = filename
            else:
                existing_files = os.listdir(target_dir) if os.path.exists(target_dir) else []
                case_num = len([f for f in existing_files if f.lower().endswith('.pdf')]) + 1
                base_name = f"case_{case_num}.pdf"
            
            # Ensure unique filename
            target_path = os.path.join(target_dir, base_name)
            counter = 1
            while os.path.exists(target_path):
                name, ext = os.path.splitext(base_name)
                target_path = os.path.join(target_dir, f"{name}_{counter}{ext}")
                counter += 1
            
            final_filename = os.path.basename(target_path)
            
            # Save PDF file if we have bytes
            if file_bytes:
                with open(target_path, 'wb') as f:
                    f.write(file_bytes)
                
                # Also save to uploads for serving
                upload_path = os.path.join(UPLOADS_DIR, final_filename)
                with open(upload_path, 'wb') as f:
                    f.write(file_bytes)
            else:
                # Save as text file if no PDF bytes
                final_filename = final_filename.replace('.pdf', '.txt')
                target_path = target_path.replace('.pdf', '.txt')
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(text)
            
            # Update hash cache
            _hash_cache[text_hash] = {
                "filename": final_filename,
                "category": category,
                "subcategory": subcategory,
                "path": target_path
            }
            _save_hash_cache()
            
            doc = {
                "filename": final_filename,
                "category": category,
                "subcategory": subcategory,
                "path": target_path
            }
            
            return jsonify({
                "success": True,
                "case": doc,
                "classification": result,
                "message": f"Case saved to {category}/{subcategory}/{final_filename}"
            })
        except Exception as e:
            return jsonify({"error": f"Failed to save case to filesystem: {e}"}), 500


# ── API endpoint to rebuild hash cache ────────────────────────────────────────
@app.route("/api/rebuild_hash_cache", methods=["POST"])
def rebuild_hash_cache():
    """Rebuild the content hash cache from dataset folder."""
    try:
        _build_hash_cache_from_dataset()
        return jsonify({
            "success": True,
            "message": f"Hash cache rebuilt with {len(_hash_cache)} documents."
        })
    except Exception as e:
        return jsonify({"error": f"Failed to rebuild hash cache: {e}"}), 500


if __name__ == "__main__":
    print("API running at http://localhost:5000")
    app.run(debug=True, port=5000)
