# Quick Start Guide - Phase 2 & 3 Complete

## ✅ What Was Created

### Schemas (Pydantic Models)
- ✅ `app/schemas/metadata.py` - CaseMetadata with validation
- ✅ `app/schemas/clause.py` - Clause schema
- ✅ `app/schemas/section.py` - Section with clauses
- ✅ `app/schemas/document.py` - Complete document response

### Services
- ✅ `app/services/parser_service.py` - LLM JSON extraction with regex for Qwen 1.5B

### Database
- ✅ `app/db/session.py` - Thread-safe in-memory database

### API Endpoints
- ✅ `app/api/v1/endpoints/upload.py` - POST /upload
- ✅ `app/api/v1/endpoints/process.py` - POST /process/{doc_id}
- ✅ `app/api/v1/endpoints/retrieve.py` - GET /documents/{doc_id}
- ✅ `app/api/v1/router.py` - Combined API router

### Updated Files
- ✅ `app/main.py` - Integrated API router
- ✅ `app/core/config.py` - Added get_settings()
- ✅ `requirements.txt` - Added requests library

### Test Scripts
- ✅ `scripts/test_api.py` - Complete API integration test

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
uvicorn app.main:app --reload
```

You should see:
```
============================================================
🚀 Civil Case Structure & Metadata Extractor Starting...
============================================================
Environment: PRODUCTION
Tesseract Language: eng+sin
Ollama Host: http://localhost:11434
Ollama Model: qwen2.5:1.5b-instruct
Data Directory: D:\CivilModel\data
API Prefix: /api/v1
============================================================
```

### 3. Test the API

**Option A: Interactive Swagger UI**
Visit: http://localhost:8000/docs

**Option B: Run Test Script**
```bash
# In a new terminal
python scripts/test_api.py
```

**Option C: Manual cURL Commands**
```bash
# Health check
curl http://localhost:8000/health

# Upload a PDF
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@data/sample_cases/sc_appeal_105_2012.pdf"

# Response: {"document_id": "doc_abc123", ...}

# Start processing
curl -X POST "http://localhost:8000/api/v1/process/doc_abc123"

# Check status (wait ~30 seconds for processing)
curl "http://localhost:8000/api/v1/documents/doc_abc123"

# List all documents
curl "http://localhost:8000/api/v1/documents"
```

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (Tesseract + Ollama) |
| GET | `/` | Root info |
| POST | `/api/v1/upload` | Upload PDF file |
| POST | `/api/v1/process/{doc_id}` | Start background processing |
| GET | `/api/v1/documents/{doc_id}` | Get processed document |
| GET | `/api/v1/documents` | List all documents |

---

## 🔄 Processing Pipeline

When you call `/process/{doc_id}`, the system runs this pipeline in the background:

```
1. OCR Extraction (pytesseract)
   ├─ Convert PDF → Images
   ├─ Extract text (eng+sin)
   └─ Clean artifacts

2. LLM Analysis (Qwen 2.5:1.5b)
   ├─ Send OCR text with structured prompt
   ├─ Request JSON output
   └─ Retry up to 3 times if timeout

3. JSON Parsing (ParserService)
   ├─ Extract JSON from LLM response (regex)
   ├─ Fix common formatting issues
   └─ Validate with Pydantic schemas

4. Database Update
   ├─ Save metadata
   ├─ Save sections/clauses
   └─ Set status to "completed"
```

---

## 📝 Example Response

```json
{
  "id": "doc_a1b2c3d4e5f6",
  "filename": "sc_appeal_105_2012.pdf",
  "status": "completed",
  "created_at": "2026-01-05T10:30:00",
  "processed_at": "2026-01-05T10:31:45",
  "metadata": {
    "case_number": "SC Appeal No. 105/2012",
    "court": "Supreme Court of the Democratic Socialist Republic of Sri Lanka",
    "date": "2011-11-08",
    "parties": [
      "Hitihamy Mudiyanselage Tilakaratna Banda",
      "Hitihamy Mudiyanselage Punchiralage Ran Banda"
    ],
    "judges": [],
    "case_type": "Civil Appeal"
  },
  "sections": [],
  "raw_text": "IN THE SUPREME COURT OF...",
  "error_message": null,
  "page_count": null
}
```

---

## 🐛 Troubleshooting

**Issue: "Tesseract not found"**
- Make sure Tesseract is installed and in PATH
- Test: `tesseract --version`

**Issue: "Ollama unreachable"**
- Make sure Ollama is running: `ollama serve`
- Test: `ollama list`
- Ensure model is pulled: `ollama pull qwen2.5:1.5b-instruct`

**Issue: "Processing takes too long"**
- First page processing: ~10-15 seconds
- Full document (10 pages): ~1-2 minutes
- Check terminal for progress logs

**Issue: "Invalid JSON in LLM output"**
- The 1.5B model sometimes adds extra text
- ParserService uses regex to extract JSON
- Check logs to see what the LLM returned

---

## 📦 Next Steps

**Immediate Testing:**
1. Start the API: `uvicorn app.main:app --reload`
2. Open http://localhost:8000/docs
3. Upload a sample PDF via Swagger UI
4. Monitor terminal for processing logs

**Production Enhancements (Future):**
- [ ] Add SQLite persistence (replace in-memory DB)
- [ ] Add authentication/authorization
- [ ] Implement rate limiting
- [ ] Add document deletion endpoint
- [ ] Export to structured JSON files
- [ ] Add WebSocket for real-time status updates

---

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Health check returns "healthy" for both Tesseract and Ollama
- ✅ Upload returns a document_id
- ✅ Process starts without errors
- ✅ Retrieve shows status changing: uploaded → processing → completed
- ✅ Metadata is extracted correctly from the PDF

Happy testing! 🚀
