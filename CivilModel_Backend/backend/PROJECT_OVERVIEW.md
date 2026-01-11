# Civil Case Extractor - Project Structure Overview

## 📁 Directory Structure

```
CivilModel/
│
├── app/                                    # Main application package
│   ├── __init__.py
│   ├── main.py                            # FastAPI entry point (TO BE CREATED)
│   │
│   ├── api/                               # API layer
│   │   ├── __init__.py
│   │   └── v1/                            # API version 1
│   │       ├── __init__.py
│   │       ├── router.py                  # Main API router (TO BE CREATED)
│   │       └── endpoints/                 # API endpoints (TO BE CREATED)
│   │           ├── __init__.py
│   │           ├── upload.py              # POST /upload - Upload PDF
│   │           ├── process.py             # POST /process/{id} - Process document
│   │           └── retrieve.py            # GET /documents/{id} - Get results
│   │
│   ├── core/                              # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py                      # Settings from .env (TO BE CREATED)
│   │   ├── logging.py                     # Logging setup (TO BE CREATED)
│   │   └── dependencies.py                # FastAPI dependencies (TO BE CREATED)
│   │
│   ├── services/                          # Business logic layer
│   │   ├── __init__.py
│   │   ├── ocr_service.py                 # ⭐ Tesseract integration (PRIORITY)
│   │   ├── llm_service.py                 # ⭐ Ollama/Qwen interface (PRIORITY)
│   │   ├── parser_service.py              # JSON structure validation (TO BE CREATED)
│   │   ├── document_service.py            # Orchestrates entire pipeline (TO BE CREATED)
│   │   └── storage_service.py             # Database/file storage (TO BE CREATED)
│   │
│   ├── models/                            # Database models
│   │   ├── __init__.py
│   │   └── database.py                    # SQLAlchemy models (TO BE CREATED)
│   │
│   ├── schemas/                           # Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── document.py                    # Document schemas (TO BE CREATED)
│   │   ├── section.py                     # Section schemas (TO BE CREATED)
│   │   ├── clause.py                      # Clause schemas (TO BE CREATED)
│   │   └── metadata.py                    # Metadata schemas (TO BE CREATED)
│   │
│   └── db/                                # Database management
│       ├── __init__.py
│       └── session.py                     # DB session handling (TO BE CREATED)
│
├── scripts/                               # Utility scripts
│   ├── prepare_training_data.py           # Convert PDFs → JSONL (TO BE CREATED)
│   ├── test_ocr.py                        # Test Tesseract setup (TO BE CREATED)
│   └── test_ollama.py                     # Test Ollama connection (TO BE CREATED)
│
├── tests/                                 # Test suite
│   ├── __init__.py
│   ├── test_ocr_service.py                # OCR unit tests (TO BE CREATED)
│   ├── test_llm_service.py                # LLM unit tests (TO BE CREATED)
│   └── test_api.py                        # API integration tests (TO BE CREATED)
│
├── data/                                  # Data storage
│   ├── sample_cases/                      # 📄 Place 4 sample PDFs here
│   │   └── README.md
│   ├── uploads/                           # User uploads (gitignored)
│   │   └── .gitkeep
│   ├── processed/                         # Processed JSON outputs (gitignored)
│   │   └── .gitkeep
│   └── training/                          # Training data JSONL (gitignored)
│       └── .gitkeep
│
├── .env.example                           # ✅ Environment template (CREATED)
├── .gitignore                             # ✅ Git ignore patterns (CREATED)
├── README.md                              # ✅ Full documentation (CREATED)
├── requirements.txt                       # ✅ Python dependencies (CREATED)
└── CivilAssignment.pdf                    # Assignment requirements
```

## 🎯 Next Steps - Implementation Priority

### Phase 1: Core Services (Your Approval Required)
1. **app/core/config.py** - Load environment variables
2. **app/services/ocr_service.py** - Tesseract wrapper (eng+sin support)
3. **app/services/llm_service.py** - Ollama client for Qwen2.5
4. **app/main.py** - FastAPI application entry point

### Phase 2: Data Schemas
5. **app/schemas/document.py** - Document structure validation
6. **app/schemas/section.py** - Section schemas
7. **app/schemas/clause.py** - Clause schemas
8. **app/schemas/metadata.py** - Metadata extraction

### Phase 3: API Endpoints
9. **app/api/v1/endpoints/upload.py** - File upload handler
10. **app/api/v1/endpoints/process.py** - Document processing
11. **app/api/v1/endpoints/retrieve.py** - Retrieve results

### Phase 4: Database & Storage
12. **app/models/database.py** - SQLAlchemy models
13. **app/db/session.py** - Database session
14. **app/services/storage_service.py** - Store/retrieve data

### Phase 5: Orchestration
15. **app/services/document_service.py** - Pipeline orchestration
16. **app/services/parser_service.py** - JSON validation

### Phase 6: Testing & Scripts
17. **scripts/test_ocr.py** - Verify Tesseract
18. **scripts/test_ollama.py** - Verify Ollama
19. **scripts/prepare_training_data.py** - Training data prep
20. **tests/** - Unit and integration tests

## 🔧 Technology Decisions

### Why These Choices?

| Technology | Reason |
|------------|--------|
| **FastAPI** | Async performance, auto-generated docs, Pydantic integration |
| **Pydantic v2** | Strict type validation, JSON schema generation, fast |
| **Tesseract 5** | Open-source, Sinhala support, proven for legal docs |
| **Ollama + Qwen2.5** | Free local inference, no API costs, fine-tunable |
| **SQLite** | Zero-config, embedded, easy migration to PostgreSQL |
| **Unsloth (future)** | 2x faster fine-tuning, works on free Colab T4 |

## 🔍 Key Architecture Patterns

### 1. Service Layer Pattern
- **Services** contain all business logic
- **Endpoints** are thin wrappers calling services
- Makes testing and reuse easier

### 2. Dependency Injection
- FastAPI's `Depends()` for services
- Easy to mock for testing

### 3. Pydantic Validation
- All inputs/outputs validated
- Automatic 422 errors on bad data
- Type safety throughout

### 4. Async/Await
- Non-blocking I/O for file operations
- Concurrent page processing
- Better resource utilization

## 📊 Expected JSON Output Structure

```json
{
  "document_id": "uuid-v4",
  "filename": "SC_2023_123.pdf",
  "processed_at": "2026-01-05T10:30:00Z",
  "metadata": {
    "case_number": "SC/123/2023",
    "court": "Supreme Court of Sri Lanka",
    "judges": ["Judge A", "Judge B"],
    "parties": {
      "petitioners": ["Party A"],
      "respondents": ["Party B"]
    },
    "date": "2023-12-15",
    "language": "mixed_en_sin"
  },
  "sections": [
    {
      "id": "section_1",
      "title": "Introduction",
      "page_range": [1, 2],
      "clauses": [
        {
          "id": "clause_1_1",
          "number": "1",
          "text": "This matter concerns...",
          "page": 1,
          "footnotes": [
            {
              "id": "footnote_1",
              "number": "1",
              "text": "See Law X, Section Y"
            }
          ]
        }
      ]
    }
  ]
}
```

## 🚨 Important Constraints

1. **NO Knowledge Graph** - That's another team. Focus on extraction only.
2. **Sinhala Support** - Must handle mixed English/Sinhala text correctly.
3. **Local Only** - All processing local (Tesseract + Ollama).
4. **Validation** - Strict Pydantic schemas for all data.
5. **Modularity** - Each service independent and testable.

## ✅ What's Done

- ✅ Folder structure created
- ✅ README.md with full documentation
- ✅ requirements.txt with all dependencies
- ✅ .env.example with configuration template
- ✅ .gitignore properly configured
- ✅ Package structure (__init__.py files)

## ⏳ Waiting for Your Approval

**Ready to proceed with Phase 1 implementation:**
1. Core configuration (config.py)
2. OCR service (ocr_service.py)
3. LLM service (llm_service.py)
4. FastAPI entry point (main.py)

Please confirm to proceed with code implementation! 🚀
