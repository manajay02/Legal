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
import numpy as np
import joblib
import pdfplumber
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from similarity_search import SimilarityEngine

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
MODELS_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
UPLOADS_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ── Load classifiers once at startup ─────────────────────────────────────────
try:
    _cat_model = joblib.load(os.path.join(MODELS_DIR, "classifier_category.pkl"))
    _sub_model = joblib.load(os.path.join(MODELS_DIR, "classifier_subcategory.pkl"))
except FileNotFoundError as _e:
    print(f"[WARNING] Classifier models not found: {_e}")
    print("[WARNING] Run 'python train_classifier.py' first. /api/classify and /api/add_case will be unavailable.")
    _cat_model = None
    _sub_model = None


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
_client = MongoClient("mongodb://localhost:27017/")
_col    = _client["legal_cases_db"]["cases"]
_engine = SimilarityEngine()


# ── GET /api/categories ───────────────────────────────────────────────────────
@app.route("/api/categories")
def get_categories():
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

    try:
        result = classify_text(text)
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
    Classifies and stores in MongoDB.
    """
    text = None
    filename = None

    if request.files.get("file"):
        f = request.files["file"]
        filename = f.filename or None
        if not f.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported."}), 400
        try:
            file_bytes = f.read()
            text = extract_pdf_text(file_bytes)
            # Save the PDF to the uploads folder so it can be served later
            save_path = os.path.join(UPLOADS_DIR, f.filename)
            with open(save_path, "wb") as out:
                out.write(file_bytes)
        except Exception as e:
            return jsonify({"error": f"Failed to read PDF: {e}"}), 400
    else:
        data = request.get_json(force=True, silent=True) or {}
        text = (data.get("text") or "").strip()
        filename = data.get("filename") or None

    if not text:
        return jsonify({"error": "No readable text found."}), 400
    try:
        result = classify_text(text)
        doc = {
            "text": text,
            "category": result["category"],
            "subcategory": result["subcategory"],
            "filename": filename or f"case_{_col.count_documents({})+1}.txt"
        }
        _col.insert_one(doc)
        doc.pop("_id", None)  # remove non-serializable ObjectId added by pymongo
        return jsonify({"success": True, "case": doc, "classification": result})
    except Exception as e:
        return jsonify({"error": f"Failed to add case: {e}"}), 500


if __name__ == "__main__":
    print("API running at http://localhost:5000")
    app.run(debug=True, port=5000)
