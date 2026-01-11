# 🏛️ Legal Argument Critic API

> **AI-powered legal argument analysis and scoring system for Sri Lankan civil cases**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)

Submit legal arguments and receive:
- ✅ **Automated scoring** (0-100) based on 8-category rubric
- 📊 **Detailed breakdown** with per-category scores and rationale  
- 💡 **Improvement suggestions** with actionable feedback

---

## 🔑 Key Concept: API-First Architecture

**❗ IMPORTANT FOR FRONTEND DEVELOPERS:**

- **No JSON files are saved to disk**
- All responses are returned **directly via HTTP API**
- Your frontend makes HTTP requests and receives JSON responses
- Perfect for building web apps, mobile apps, or desktop clients

**Example Flow:**
```
Frontend → POST /api/v1/analyze → Backend processes → JSON response → Display results
```

No intermediate files. No file system. Pure API communication.

---

## 📋 Quick Start (Step-by-Step)

### 1. Extract Project Files

```powershell
# Extract the ZIP file you received
# You'll get a 'backend' folder containing the API

# Navigate to backend folder
cd backend

# Verify extraction
ls  # Should see: app/, data/, models/, scripts/, .env.example, README.md
```

### 2. Setup Python Virtual Environment

```powershell
# IMPORTANT: Make sure you're in the backend directory
cd backend

# Check Python version (must be 3.10+)
python --version  # Should show: Python 3.12.x or 3.11.x or 3.10.x

# Create virtual environment
python -m venv .venv

# Verify .venv folder created
ls .venv  # Should see: Scripts/, Lib/, Include/

# Activate virtual environment (CRITICAL STEP)
& .\.venv\Scripts\Activate.ps1

# ✅ You should see (.venv) at the start of your terminal prompt
# Example: (.venv) PS D:\LegalScoreModel>
```

**⚠️ Troubleshooting Activation:**
```powershell
# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activation again:
& .\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
# MAKE SURE (.venv) is showing in your prompt!
# If not, go back to step 2

# Install all required packages
pip install -r requirements.txt

# This will take 2-3 minutes. You should see:
# - fastapi, uvicorn, pydantic, requests installing
# - pypdf, python-multipart for file uploads

# Verify installation
pip list  # Should show fastapi, uvicorn, etc.
```

### 4. Configure API Backend (IMPORTANT!)

**Step 4.1: Get Free API Key**

1. Go to https://openrouter.ai/
2. Click "Sign In" (top right)
3. Sign up with Google/GitHub (free account)
4. Go to "Keys" section
5. Click "Create Key"
6. Copy the key (starts with `sk-or-v1-...`)

**Step 4.2: Create Configuration File**

```powershell
# Copy the example file
Copy-Item .env.example .env

# Open .env in notepad
notepad .env
```

**Step 4.3: Paste Your API Key**

Edit the `.env` file:

```env
# Backend: "openrouter", "gemini", or "ollama"
INFERENCE_BACKEND=openrouter

# OpenRouter (Recommended - Free DeepSeek)
OPENROUTER_API_KEY=sk-or-v1-YOUR_ACTUAL_KEY_HERE  # ⬅️ PASTE HERE
OPENROUTER_MODEL=deepseek/deepseek-chat
OPENROUTER_TEMPERATURE=0.7
OPENROUTER_MAX_TOKENS=2048
```

**Save and close notepad.**

**Step 4.4: Verify Configuration**

```powershell
# Check .env file exists
ls .env  # Should show the file

# Verify content (should show your API key)
cat .env
```

### 5. Start the API Server

```powershell
# MAKE SURE:
# 1. (.venv) is active in your prompt
# 2. You're in D:\LegalScoreModel directory
# 3. .env file has your API key

# Start server
python -m uvicorn app.main:app --reload --port 8000

# ✅ You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete.
```

**Keep this terminal window OPEN!** The server must run continuously.

**Step 5.1: Verify Server is Running**

Open browser and go to: http://localhost:8000

You should see:
```json
{
  "message": "Legal Argument Critic API",
  "version": "1.0.0",
  "endpoints": {
    "analyze": "POST /api/v1/analyze",
    "upload": "POST /api/v1/upload",
    "health": "GET /api/v1/health"
  }
}
```

**Step 5.2: Test Interactive Docs**

Go to: http://localhost:8000/docs

You should see Swagger UI with all endpoints listed.

### 6. Run Tests (Verify Everything Works)

**Open a NEW PowerShell window** (keep server running in the first window):

```powershell
# Navigate to project
cd D:\LegalScoreModel

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Run comprehensive test
python test_full_pipeline.py

# ✅ Expected output:
# TEST 1: Health Check ✅
# TEST 2: Text Analysis ✅
# TEST 3: PDF Upload ✅
# TEST 4: JSON Format ✅
# 
# All tests passed!
```

**If all tests pass, your API is working correctly!** 🎉

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API info |
| `POST` | `/api/v1/analyze` | Analyze text |
| `POST` | `/api/v1/upload` | Upload PDF/TXT |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/docs` | Swagger docs |

---

## 🔌 Frontend Integration Guide

### ⚠️ IMPORTANT: No JSON Files Are Saved!

**The API returns JSON responses directly via HTTP.**  
**No files are created on disk.**

Your frontend should:
1. **Call the API** via HTTP POST request
2. **Receive JSON response** in real-time
3. **Parse and display** the data

---

### POST /api/v1/analyze

**Endpoint:** `http://localhost:8000/api/v1/analyze`

**Request:**
```json
{
  "text": "The appellant challenges the District Court's decision on grounds of procedural irregularity. The lower court failed to consider Section 91 of the Civil Procedure Code..."
}
```

**Response Structure (Complete):**
```json
{
  "overall_score": 75,
  "strength_label": "Moderate",
  "breakdown": [
    {
      "category": "Issue & Claim Clarity",
      "weight": 10,
      "rubric_score": 4,
      "points": 8.0,
      "rationale": "The legal issue is clearly stated with specific reference to procedural grounds."
    },
    {
      "category": "Facts & Chronology",
      "weight": 15,
      "rubric_score": 3,
      "points": 9.0,
      "rationale": "Timeline is present but lacks some material details."
    },
    {
      "category": "Legal Basis",
      "weight": 20,
      "rubric_score": 4,
      "points": 16.0,
      "rationale": "References Section 91 CPC but could cite more case law."
    },
    {
      "category": "Evidence & Support",
      "weight": 15,
      "rubric_score": 3,
      "points": 9.0,
      "rationale": "Some documentary evidence mentioned but not detailed."
    },
    {
      "category": "Reasoning & Logic",
      "weight": 15,
      "rubric_score": 4,
      "points": 12.0,
      "rationale": "Logical flow is coherent with clear argumentation."
    },
    {
      "category": "Counterarguments",
      "weight": 10,
      "rubric_score": 3,
      "points": 6.0,
      "rationale": "Acknowledges opposing view but doesn't fully address it."
    },
    {
      "category": "Remedies",
      "weight": 10,
      "rubric_score": 4,
      "points": 8.0,
      "rationale": "Relief sought is clear and appropriate."
    },
    {
      "category": "Structure",
      "weight": 5,
      "rubric_score": 4,
      "points": 4.0,
      "rationale": "Well-organized with professional tone."
    }
  ],
  "feedback": [
    "Add more case law citations to strengthen legal basis",
    "Address potential counterarguments about alternative interpretations",
    "Include more specific details about evidence"
  ]
}
```

### 📊 How to Use JSON in Frontend

**1. Overall Score (0-100):**
```javascript
const score = result.overall_score;  // 75
const percentage = `${score}%`;      // "75%"
```

**2. Strength Label:**
```javascript
const strength = result.strength_label;  // "Moderate"
// Possible values: "Very Weak", "Weak", "Moderate", "Strong"
```

**3. Category Breakdown (for charts/graphs):**
```javascript
result.breakdown.forEach(category => {
  const name = category.category;          // "Issue & Claim Clarity"
  const score = category.rubric_score;     // 4 (out of 5)
  const percentage = (score / 5) * 100;    // 80%
  const explanation = category.rationale;   // "The legal issue is..."
  
  // Display in your UI
  displayCategoryBar(name, percentage, explanation);
});
```

**4. Weaknesses (low-scoring categories):**
```javascript
const weaknesses = result.breakdown
  .filter(cat => cat.rubric_score < 3)  // Score below 3/5
  .map(cat => ({
    category: cat.category,
    score: cat.rubric_score,
    issue: cat.rationale
  }));

// Example output:
// [
//   { category: "Facts & Chronology", score: 2, issue: "Timeline unclear" }
// ]
```

**5. Suggestions for Improvement:**
```javascript
const suggestions = result.feedback;  // Array of strings

suggestions.forEach((suggestion, index) => {
  console.log(`${index + 1}. ${suggestion}`);
});

// Output:
// 1. Add more case law citations to strengthen legal basis
// 2. Address potential counterarguments about alternative interpretations
// 3. Include more specific details about evidence
```

### POST /api/v1/upload

**Endpoint:** `http://localhost:8000/api/v1/upload`

**Accepts:** PDF or TXT files (max 10MB)

**Request (JavaScript):**
```javascript
const formData = new FormData();
formData.append('file', file);  // file from <input type="file">

const response = await fetch('http://localhost:8000/api/v1/upload', {
  method: 'POST',
  body: formData  // No Content-Type header needed
});

const result = await response.json();
```

**Response:** Same as `/analyze` PLUS:
```json
{
  "overall_score": 85,
  "strength_label": "Strong",
  "breakdown": [ /* 8 categories */ ],
  "feedback": [ /* suggestions */ ],
  
  // Extra fields for file uploads:
  "filename": "appeal_case_2023.pdf",
  "file_type": "pdf",
  "text_length": 8543,
  "extracted_text": "The appellant submits..."  // First 10,000 chars
}
```

**Frontend Example:**
```jsx
function FileUpload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  
  const handleUpload = async () => {
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await fetch('http://localhost:8000/api/v1/upload', {
      method: 'POST',
      body: formData
    });
    
    const data = await res.json();
    setResult(data);
    
    // Access file info
    console.log('Uploaded:', data.filename);
    console.log('Score:', data.overall_score);
  };
  
  return (
    <div>
      <input type="file" onChange={e => setFile(e.target.files[0])} />
      <button onClick={handleUpload}>Analyze PDF</button>
      {result && <ScoreDisplay data={result} />}
    </div>
  );
}

---

## 🎨 Frontend Integration

### JavaScript Example

```javascript
// Analyze text
async function analyzeText(text) {
  const res = await fetch('http://localhost:8000/api/v1/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  return await res.json();
}

// Upload file
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('http://localhost:8000/api/v1/upload', {
    method: 'POST',
    body: formData
  });
  return await res.json();
}
```

### Complete React Component Example

```jsx
import React, { useState } from 'react';

function LegalAnalyzer() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const analyze = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('API Error:', error);
      alert('Analysis failed. Make sure API is running on port 8000');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="analyzer">
      <h1>Legal Argument Analyzer</h1>
      
      {/* Input */}
      <textarea 
        value={text} 
        onChange={e => setText(e.target.value)}
        placeholder="Paste your legal argument here (50-10000 characters)..."
        rows={10}
        style={{ width: '100%' }}
      />
      
      <button onClick={analyze} disabled={loading || text.length < 50}>
        {loading ? 'Analyzing...' : 'Analyze Argument'}
      </button>
      
      {/* Results */}
      {result && (
        <div className="results">
          {/* Overall Score */}
          <div className="score-card">
            <h2>Overall Score: {result.overall_score}/100</h2>
            <p className="strength">{result.strength_label}</p>
            
            {/* Progress bar */}
            <div style={{ 
              width: '100%', 
              height: '30px', 
              background: '#eee',
              borderRadius: '5px'
            }}>
              <div style={{
                width: `${result.overall_score}%`,
                height: '100%',
                background: result.overall_score >= 80 ? 'green' : 
                           result.overall_score >= 60 ? 'orange' : 'red',
                borderRadius: '5px',
                transition: 'width 0.5s'
              }}></div>
            </div>
          </div>
          
          {/* Category Breakdown */}
          <div className="breakdown">
            <h3>Category Analysis</h3>
            {result.breakdown.map((category, i) => (
              <div key={i} className="category">
                <div className="category-header">
                  <strong>{category.category}</strong>
                  <span>{category.rubric_score}/5 ({category.points.toFixed(1)} points)</span>
                </div>
                
                {/* Category progress bar */}
                <div style={{ 
                  width: '100%', 
                  height: '10px', 
                  background: '#eee',
                  margin: '5px 0'
                }}>
                  <div style={{
                    width: `${(category.rubric_score / 5) * 100}%`,
                    height: '100%',
                    background: '#4CAF50'
                  }}></div>
                </div>
                
                <p className="rationale">{category.rationale}</p>
              </div>
            ))}
          </div>
          
          {/* Improvement Suggestions */}
          <div className="feedback">
            <h3>💡 Suggestions for Improvement</h3>
            <ul>
              {result.feedback.map((suggestion, i) => (
                <li key={i}>{suggestion}</li>
              ))}
            </ul>
          </div>
          
          {/* Weaknesses */}
          <div className="weaknesses">
            <h3>⚠️ Areas Needing Attention</h3>
            <ul>
              {result.breakdown
                .filter(cat => cat.rubric_score < 3)
                .map((cat, i) => (
                  <li key={i}>
                    <strong>{cat.category}:</strong> {cat.rationale}
                  </li>
                ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
```

### CORS Configuration

Update `app/main.py` for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## ⚙️ Backend Options

### Option 1: OpenRouter (Recommended)

Free with DeepSeek V3 - no rate limits.

```env
INFERENCE_BACKEND=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=deepseek/deepseek-chat
```

**Get API key:** https://openrouter.ai/

### Option 2: Google Gemini

```env
INFERENCE_BACKEND=gemini
GOOGLE_API_KEY=AIzaSyxxxxxx
GEMINI_MODEL_NAME=gemini-1.5-flash
```

**Get API key:** https://aistudio.google.com/

### Option 3: Local Fine-Tuned Model (Ollama)

**Requires:** NVIDIA GPU with 8GB+ VRAM

```env
INFERENCE_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=legal-critic
OLLAMA_MODELS=D:\LegalScoreModel\.ollama\models
```

**Setup:**
1. Install [Ollama](https://ollama.ai/)
2. Merge adapter:
   ```powershell
   python scripts/merge_and_convert_ollama.py
   ```
3. Start Ollama:
   ```powershell
   $env:OLLAMA_MODELS = "D:\LegalScoreModel\.ollama\models"
   ollama serve
   ```

---

## 📁 Project Structure

```
LegalScoreModel/
├── app/
│   ├── main.py                       # FastAPI app
│   ├── api/v1/analyze.py             # API endpoints
│   └── services/
│       └── inference_service.py      # Multi-backend support
│
├── scripts/
│   └── merge_and_convert_ollama.py   # Convert adapter → Ollama
│
├── training_pipeline/                # ML Training
│   ├── 1_ocr_extraction.py
│   ├── 2_dataset_generation.py
│   └── 3_fine_tune_unsloth.py
│
├── data/
│   ├── raw_pdfs/                     # 80 legal PDFs
│   └── training_data/
│
├── models/fine_tuned/
│   └── adapter_model/                # LoRA adapter (117MB)
│
├── .env                              # Configuration
├── test_full_pipeline.py             # E2E test
└── api_examples.py                   # Integration examples
```

---

## 🔧 Training Pipeline

**Model:** Qwen2.5-3B-Instruct + LoRA fine-tuning  
**Dataset:** 81 Sri Lankan legal examples  
**Training:** Kaggle GPU, 5 epochs, 17 minutes  
**Loss:** 0.8068

To retrain:
1. Upload `training_pipeline/3_fine_tune_unsloth.py` to Kaggle
2. Enable GPU
3. Download adapter from `/kaggle/working/`

---

## 🐛 Troubleshooting

### "Where are the JSON files saved?"

**They aren't!** The API returns JSON responses via HTTP, not files.

```javascript
// ✅ Correct: Get JSON from API response
const response = await fetch('/api/v1/analyze', { method: 'POST', ... });
const jsonData = await response.json();  // This is your JSON

// ❌ Wrong: Looking for files on disk
// There are no .json files created
```

If you need to save responses:
```javascript
// Frontend saves to localStorage
localStorage.setItem('lastResult', JSON.stringify(jsonData));

// Or download as file
const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'analysis-result.json';
a.click();
```

### API Won't Start

```powershell
# Check port 8000
netstat -ano | findstr 8000

# Kill process
Stop-Process -Id <PID> -Force

# Restart
python -m uvicorn app.main:app --reload
```

### Module Not Found

```powershell
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### CORS Errors (Frontend Can't Connect)

**Symptoms:**
- Browser console shows: "Access-Control-Allow-Origin" error
- Fetch requests fail with CORS error

**Solution:**

The API already has CORS enabled for `http://localhost:3000` (React default).

If your frontend runs on a different port:

Edit `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React
        "http://localhost:5173",   # Vite
        "http://localhost:8080",   # Vue
        "http://127.0.0.1:5500",  # Live Server
        # Add your frontend URL here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then restart the server.

### "Connection Refused" Errors

```powershell
# Make sure API is running
# Open http://localhost:8000 in browser
# Should see: {"message": "Legal Argument Critic API", ...}

# If not, start server:
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Gets Empty Response

```javascript
// ❌ Wrong: Missing await
const response = fetch('/api/v1/analyze', { ... });
const data = response.json();  // This is a Promise, not data!

// ✅ Correct: Use await
const response = await fetch('/api/v1/analyze', { ... });
const data = await response.json();  // Now this is actual data
```

### Rate Limits (Gemini)

Switch to OpenRouter:
```env
INFERENCE_BACKEND=openrouter
```

### Slow Inference (Ollama on CPU)

Use cloud backend:
```env
INFERENCE_BACKEND=openrouter
```

### PDF Upload Fails

```powershell
pip install pypdf python-multipart
```

### Ollama Model Not Found

```powershell
# Set env variable
$env:OLLAMA_MODELS = "D:\LegalScoreModel\.ollama\models"

# List models
ollama list

# If missing, run conversion
python scripts/merge_and_convert_ollama.py
```

---

## 📊 Scoring Rubric

| Category | Weight | Description |
|----------|--------|-------------|
| Issue & Claim Clarity | 10% | Legal claim, parties, relief |
| Facts & Chronology | 15% | Timeline, material facts |
| Legal Basis | 20% | Statutes, case law, elements |
| Evidence & Support | 15% | Documentary proof |
| Reasoning & Logic | 15% | Logical flow |
| Counterarguments | 10% | Address opposing views |
| Remedies | 10% | Relief sought, quantification |
| Structure | 5% | Organization, professionalism |

**Strength Labels:**
- 0-39: Very Weak
- 40-59: Weak
- 60-79: Moderate
- 80-100: Strong

---

## 📝 Development

### Run Tests
```powershell
python test_full_pipeline.py
```

### Run Specific Test
```powershell
python api_examples.py
```

### View Logs
```powershell
# Check logs/ directory
Get-Content logs/app.log
```

---

## 📄 License

MIT License

---

## 👥 Contributors

LegalScoreModel Team - January 2026
