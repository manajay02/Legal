# CivilModel Backend - Deployment Package

## 📦 What's Included

This zip contains the complete backend for the Civil Case Structure & Metadata Extractor.

### Structure
```
CivilModel_Backend.zip
└── backend/
    ├── app/                    # FastAPI application
    ├── data/                   # Data directories
    │   ├── uploads/            # (empty - for PDF uploads)
    │   ├── processed/          # (empty - for outputs)
    │   ├── training/           # (empty - for training data)
    │   └── sample_cases/       # (directory only, PDFs excluded)
    ├── scripts/                # Utility scripts
    │   ├── merge_adapter.py    # Merge LoRA for Ollama
    │   └── test_*.py           # Test scripts
    ├── tests/                  # Test suite
    ├── .env.example            # Environment template
    ├── .gitignore             # Git ignore rules
    ├── Modelfile              # Ollama model config
    ├── README.md              # Full documentation
    ├── requirements.txt       # Python dependencies
    └── test_api.ps1           # API test script
```

### What's NOT Included (Excluded for Size)
- ❌ `venv/` - Virtual environment (create fresh)
- ❌ `__pycache__/` - Python cache
- ❌ `.git/` - Git history
- ❌ Sample PDF files (too large)
- ❌ ML model files (download separately)

### What IS Included
- ✅ All source code
- ✅ Configuration templates
- ✅ Processed .txt files (OCR samples)
- ✅ Complete documentation
- ✅ Test scripts

---

## 🚀 Quick Start

### 1. Extract
```bash
unzip CivilModel_Backend.zip
cd backend
```

### 2. Setup Environment
```bash
# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure
```bash
# Copy environment template
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# Edit .env with your settings:
# - OPENROUTER_API_KEY (get from https://openrouter.ai/keys)
# OR
# - Configure Ollama for local model
```

### 4. Run
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/upload` | POST | Upload PDF |
| `/api/v1/process/{doc_id}` | POST | Process document |
| `/api/v1/documents/{doc_id}` | GET | Get full results |
| `/api/v1/documents/{doc_id}/metadata` | GET | Metadata only |
| `/api/v1/documents/{doc_id}/sections` | GET | Sections only |
| `/api/v1/documents-summary` | GET | List all docs |
| `/api/v1/health` | GET | Health check |

---

## 🔧 Two LLM Options

### Option A: OpenRouter (Easy - Recommended)
1. Get API key from https://openrouter.ai/keys
2. Set in `.env`:
   ```env
   LLM_PROVIDER=openrouter
   OPENROUTER_API_KEY=sk-or-v1-your-key
   ```
3. Done! (~$0.14 per 1M tokens)

### Option B: Ollama with Trained Model (Advanced)
1. Run: `python scripts/merge_adapter.py`
2. Run: `ollama create civilmodel-qwen3b -f Modelfile`
3. Run: `ollama serve` (keep running)
4. Set in `.env`:
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=civilmodel-qwen3b
   ```
5. Start backend in new terminal

---

## 📚 Full Documentation

See [README.md](README.md) for:
- Complete installation guide
- API usage examples
- Troubleshooting
- Frontend integration guide
- Training model details

---

## 🐛 Common Issues

**"Tesseract not found"**
- Install from: https://github.com/UB-Mannheim/tesseract/wiki
- Update `TESSERACT_PATH` in `.env`

**"OPENROUTER_API_KEY not set"**
- Get key from https://openrouter.ai/keys
- Add to `.env`

**"Cannot connect to Ollama"**
- Run `ollama serve` first
- Check `OLLAMA_BASE_URL` in `.env`

---

## 📊 Performance

- OCR: ~30 seconds (10-page PDF)
- LLM: ~20-30 seconds (OpenRouter)
- Total: ~1 minute per document

---

## 🤝 Support

For issues, check:
1. [README.md](README.md) - Full documentation
2. [API_TESTING.md](API_TESTING.md) - Testing guide
3. Logs at `logs/app.log`

---

**Version**: 1.0  
**Last Updated**: January 2026  
**Python**: 3.10+  
**License**: MIT
