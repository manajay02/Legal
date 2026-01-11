# Argument Strength Score - Comprehensive Documentation

A sophisticated **AI-powered legal argument analysis component** that automatically evaluates legal arguments and provides detailed scoring based on an 8-category rubric. Built with FastAPI, OpenRouter LLM integration, and modern web technologies for Sri Lankan civil cases.

---

## Table of Contents


1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [Project Structure](#project-structure)
5. [Installation & Setup](#installation--setup)
6. [Usage Guide](#usage-guide)
7. [Technical Details](#technical-details)
8. [Model Information](#model-information)
9. [API Reference](#api-reference)
10. [Testing & Validation](#testing--validation)
11. [Contributing](#contributing)
12. [License](#license)

---

## Project Overview

The **Argument Strength Score** is an intelligent component designed to help legal professionals, law students, and organizations evaluate the quality and strength of legal arguments in civil cases within the Sri Lankan legal context.

### Problem Solved
- Manual evaluation of legal arguments is subjective and time-consuming
- Lack of standardized assessment frameworks for legal writing quality
- Legal professionals need quick, objective feedback on argument strength
- Law students require consistent guidance to improve legal writing skills
- Organizations need automated quality control for legal documentation

### Solution
A focused analysis component that:
- Automatically analyzes legal arguments using advanced LLM technology
- Provides objective scoring based on 8 comprehensive categories
- Generates detailed feedback with actionable improvement suggestions
- Supports text input for direct argument analysis
- Delivers real-time analysis with confidence-scored results
- Offers professional web interface for easy access

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  USER INTERFACE (Frontend)                  │
│              Modern Responsive Web Application              │
│                  (HTML5, CSS3, JavaScript)                  │
│                                                             │
│                ┌──────────────┐                            │
│                │  Text Input  │                            │
│                │   Interface  │                            │
│                └──────┬───────┘                            │
│                       │                                     │
│                       │                                     │
└────────────────────┼────────────────────────────────────────┘
                     │ HTTP/JSON REST API
┌────────────────────┼────────────────────────────────────────┐
│                    │   BACKEND API (FastAPI)                │
├────────────────────┼────────────────────────────────────────┤
│                    ▼                                        │
│          ┌─────────────────────┐                           │
│          │   API Endpoints     │                           │
│          │  /api/v1/analyze    │  ← Text Analysis         │
│          │  /api/v1/health     │  ← Health Check          │
│          └──────────┬──────────┘                           │
│                     │                                       │
│          ┌──────────▼──────────┐                           │
│          │  Inference Service  │  ← Main Orchestrator     │
│          │   (Core Engine)     │                           │
│          └──────────┬──────────┘                           │
│                     │                                       │
│     ┌───────────────┼───────────────┐                      │
│     │               │               │                      │
│ ┌───▼────┐    ┌────▼────┐    ┌────▼────┐                 │
│ │  LLM   │    │ Grading │    │  Model  │                 │
│ │Service │    │ Schema  │    │ Service │                 │
│ └────┬───┘    └─────────┘    └─────────┘                 │
│      │                                                     │
│      │                                                     │
│      ▼                                                     │
│ ┌──────────────────────────────┐                          │
│ │    OpenRouter API Gateway    │                          │
│ │  (LLM Model Aggregator)      │                          │
│ └──────────────┬───────────────┘                          │
│                │                                           │
│                ▼                                           │
│ ┌──────────────────────────────┐                          │
│ │  LLM Models Available:       │                          │
│ │  • Llama 3.1 8B (Free)       │                          │
│ │  • GPT-4 Turbo               │                          │
│ │  • Claude 3.5 Sonnet         │                          │
│ │  • Gemini Pro                │                          │
│ └──────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input (Text)
    ↓
[Frontend Validation]
    └─ Text: 50-10,000 characters
    ↓
[HTTP POST Request] → JSON payload to backend
    ↓
[FastAPI Endpoint Handler]
    └─ /api/v1/analyze (text analysis)
    ↓
[Inference Service] ← Main orchestrator
    ├─ Load grading schema (8 categories)
    ├─ Construct analysis prompt
    └─ Validate input
    ↓
[LLM Service]
    ├─ Format request for OpenRouter API
    ├─ Add API key and headers
    ├─ Set model parameters (temperature, max_tokens)
    └─ Handle retries and errors
    ↓
[OpenRouter API] → External LLM processing
    ├─ Route to selected model
    ├─ Generate structured analysis
    └─ Return JSON response
    ↓
[Response Processing]
    ├─ Parse LLM output
    ├─ Extract scores for 8 categories
    ├─ Calculate overall score
    ├─ Generate strength label
    └─ Format suggestions
    ↓
[JSON Response] → Return to frontend
    ├─ overall_score: int (0-100)
    ├─ strength: string
    ├─ categories: dict (8 categories)
    │   ├─ score: int
    │   ├─ rationale: string
    │   └─ suggestions: list
    └─ timestamp: datetime
    ↓
[Frontend Display]
    ├─ Animated score card
    ├─ Category breakdown cards
    ├─ Color-coded indicators
    └─ Improvement suggestions
```

---

##  Key Features

### 1. **Comprehensive 8-Category Analysis**

The system evaluates legal arguments across eight critical dimensions:

####  **Legal Basis & Citations** (0-100 points)
- Evaluation of statutory references
- Case law citation accuracy
- Constitutional grounding
- Legal authority relevance

####  **Logical Reasoning & Coherence** (0-100 points)
- Argument structure assessment
- Logical flow evaluation
- Internal consistency checking
- Premise-conclusion alignment

####  **Facts & Evidence Presentation** (0-100 points)
- Factual accuracy verification
- Evidence organization
- Relevance of presented facts
- Supporting documentation quality

####  **Clarity & Organization** (0-100 points)
- Writing clarity assessment
- Structural organization
- Paragraph coherence
- Readability scoring

####  **Case Law Application** (0-100 points)
- Precedent relevance
- Analogical reasoning strength
- Distinguishing arguments
- Judicial interpretation accuracy

####  **Statutory Interpretation** (0-100 points)
- Statutory construction methods
- Legislative intent analysis
- Textual interpretation accuracy
- Contextual understanding

####  **Counter-Argument Handling** (0-100 points)
- Anticipation of opposing views
- Rebuttal effectiveness
- Alternative perspectives consideration
- Weaknesses addressed

####  **Professional Tone** (0-100 points)
- Legal writing standards
- Formal language usage
- Objective presentation
- Respectful discourse

### 2. **Intelligent Scoring System**

```
Overall Score Calculation:
├─ Each category: 0-100 points
├─ Overall Score: Average of 8 categories
└─ Strength Classification:
    ├─ 90-100: "Exceptional" 
    ├─ 80-89:  "Strong" 
    ├─ 70-79:  "Good" 
    ├─ 60-69:  "Moderate" 
    ├─ 50-59:  "Weak" 
    └─ 0-49:   "Very Weak" 
```

### 3. **AI-Powered Analysis**

- **LLM Integration**: OpenRouter API with multiple model options
- **Structured Prompting**: Engineered prompts for consistent evaluation
- **JSON Response Format**: Standardized output for reliable parsing
- **Error Handling**: Robust fallback mechanisms
- **Retry Logic**: Automatic retry on API failures

### 4. **Text Input Interface**

#### Direct Text Analysis
- Clean, intuitive text input interface
- Real-time character counter (50-10,000 chars)
- Color-coded validation feedback
- Instant analysis on submit
- Paste-friendly textarea with smart formatting

### 5. **Professional Web Interface**

#### Modern Design
- Gradient purple theme
- Smooth animations and transitions
- Card-based layout
- Progress bars for scores
- Responsive design (mobile/tablet/desktop)

#### User Experience
- Clean, focused interface
- Real-time validation feedback
- Loading indicators during processing
- Clear error messages
- Accessible design (WCAG compliant)

#### Results Display
- Large animated score card with strength label
- Individual category cards with:
  - Score badges (color-coded)
  - Detailed rationales
  - Actionable suggestions
- Visual hierarchy for easy scanning
- Print-friendly layout

### 6. **API-First Architecture**

- **RESTful Design**: Clean, predictable endpoints
- **JSON Communication**: Standard data format
- **CORS Enabled**: Cross-origin resource sharing
- **Interactive Documentation**: Auto-generated Swagger UI
- **Versioned API**: `/api/v1/` namespace for future compatibility

---

##  Project Structure

```
Legal/
│
├── README.md                          # This comprehensive documentation
├── Legal.txt                          # Project notes and legal information
│
├── backend/                           # Backend API Application
│   │
│   ├── app/                          # Main application package
│   │   ├── __init__.py               # Package initializer
│   │   ├── main.py                   # FastAPI application entry point
│   │   │
│   │   ├── api/                      # API layer
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/            # API route handlers
│   │   │   └── v1/                   # API version 1 routes
│   │   │
│   │   ├── core/                     # Core configuration
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # Application settings
│   │   │   └── grading_schema.py     # 8-category rubric definition
│   │   │
│   │   ├── services/                 # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── inference_service.py  # Main analysis orchestrator
│   │   │   ├── llm_service.py        # OpenRouter API integration
│   │   │   └── model_service.py      # Model management utilities
│   │   │
│   │   ├── models/                   # Pydantic data models
│   │   │   └── __init__.py           # Request/response schemas
│   │   │
│   │   └── db/                       # Database (future implementation)
│   │
│   ├── data/                         # Data storage
│   │   ├── processed_text/           # Processed legal documents
│   │   │   ├── sc_appeal_10_and_11_2022.txt
│   │   │   ├── sc_appeal_105_2012.txt
│   │   │   └── ... (65+ documents)
│   │   ├── raw_data/                 # Original source documents
│   │   ├── metadata/                 # Document metadata
│   │   └── training_data/            # ML training datasets (future)
│   │
│   ├── models/                       # Model storage
│   │   ├── base/                     # Base models
│   │   └── fine_tuned/               # Fine-tuned models (future)
│   │
│   ├── scripts/                      # Utility scripts
│   │   ├── verify_setup.py           # Environment verification
│   │   ├── count_pdf_pages.py        # PDF analysis utility
│   │   └── convert_to_ollama.py      # Model conversion (future)
│   │
│   ├── tests/                        # Test suite
│   │   ├── test_api.py               # API endpoint tests
│   │   ├── test_api_v1.py            # API v1 tests
│   │   ├── test_full_pipeline.py     # Integration tests
│   │   └── test_openrouter.py        # LLM service tests
│   │
│   ├── logs/                         # Application logs
│   │   ├── api/                      # API access logs
│   │   ├── ocr/                      # OCR processing logs
│   │   └── training/                 # Training logs (future)
│   │
│   ├── training_pipeline/            # ML training pipeline (future)
│   │   ├── __init__.py
│   │   ├── 1_ocr_extraction.py       # Document extraction
│   │   ├── 2_dataset_generation.py   # Dataset creation
│   │   ├── 3_fine_tune_unsloth.py   # Model fine-tuning
│   │   └── utils/                    # Training utilities
│   │
│   ├── requirements.txt              # Python dependencies
│   ├── requirements-api.txt          # API-specific dependencies
│   ├── requirements-ml.txt           # ML-specific dependencies
│   ├── .env                          # Environment variables (create this!)
│   ├── .env.example                  # Environment template
│   ├── setup_env.ps1                 # Windows setup script
│   ├── README.md                     # Backend-specific documentation
│   ├── FRONTEND_GUIDE.md             # Frontend integration guide
│   ├── api_examples.py               # API usage examples
│   └── test_frontend.html            # Frontend test page
│
└── frontend/                         # Frontend Web Application
    │
    ├── index.html                    # Main application page
    ├── README.md                     # Frontend documentation
    │
    ├── css/                          # Stylesheets
    │   └── style.css                 # Main stylesheet (modern design)
    │
    ├── js/                           # JavaScript modules
    │   ├── config.js                 # Configuration (API URL, limits)
    │   ├── api.js                    # API service functions
    │   ├── ui.js                     # UI update functions
    │   └── app.js                    # Main application logic
    │
    └── assets/                       # Static assets
        └── (images, icons, fonts)
```

### File Descriptions

#### Backend Core Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app initialization, CORS config, route registration |
| `app/core/config.py` | Environment variables, API settings, logging config |
| `app/core/grading_schema.py` | 8-category rubric definitions and descriptions |
| `app/services/inference_service.py` | Main orchestrator for argument analysis |
| `app/services/llm_service.py` | OpenRouter API communication and error handling |
| `app/services/model_service.py` | Model loading and management utilities |

#### Frontend Core Files

| File | Purpose |
|------|---------|
| `index.html` | Main UI structure, forms, result containers |
| `css/style.css` | Complete styling, animations, responsive design |
| `js/config.js` | API endpoints, validation limits, configuration |
| `js/api.js` | HTTP request functions, error handling |
| `js/ui.js` | DOM manipulation, result rendering, animations |
| `js/app.js` | Event handlers, form validation, app initialization |

---

##  Installation & Setup

### Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** (Python 3.12 recommended)
  ```powershell
  python --version  # Should show 3.10 or higher
  ```

- **pip** (Python package manager)
  ```powershell
  pip --version  # Usually comes with Python
  ```

- **Modern web browser**
  - Chrome 90+
  - Firefox 88+
  - Edge 90+
  - Safari 14+

- **OpenRouter API Key** (FREE tier available)
  - Sign up at: https://openrouter.ai/
  - Free models available (Llama 3.1 8B)
  - No credit card required for free tier

- **Text Editor or IDE** (Recommended)
  - VS Code
  - PyCharm
  - Sublime Text

### Step-by-Step Installation

#### **Step 1: Navigate to Project Directory**

```powershell
# Open PowerShell and navigate to project folder
cd "d:\Y4S1\Research new\reserch component\Legal"

# Verify you're in the correct directory
ls
# You should see: backend/, frontend/, README.md, Legal.txt
```

#### **Step 2: Set Up Backend**

##### 2.1 Navigate to Backend Directory

```powershell
cd backend
```

##### 2.2 Create Virtual Environment

```powershell
# Create virtual environment named .venv
python -m venv .venv

# Verify creation
ls .venv
# You should see: Scripts/, Lib/, Include/
```

##### 2.3 Activate Virtual Environment

```powershell
# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Success: You should see (.venv) at the start of your prompt
# Example: (.venv) PS D:\Y4S1\Research new\reserch component\Legal\backend>
```

Troubleshooting Activation:

If you get an execution policy error:

```powershell
# Run this command to allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activation again
& .\.venv\Scripts\Activate.ps1
```

##### 2.4 Install Python Dependencies

```powershell
# CRITICAL: Make sure (.venv) is showing in your prompt!

# Install all required packages
pip install -r requirements.txt

# This will install:
# - fastapi: Web framework
# - uvicorn: ASGI server
# - pydantic: Data validation
# - python-multipart: File upload support
# - pypdf2: PDF processing
# - requests: HTTP client
# - python-dotenv: Environment variable management

# Installation takes 2-3 minutes
```

##### 2.5 Verify Installation

```powershell
# Check installed packages
pip list

# You should see:
# fastapi, uvicorn, pydantic, requests, pypdf2, etc.

# Quick verification
python -c "import fastapi; import uvicorn; print('All dependencies installed!')"
```

##### 2.6 Configure Environment Variables

**Step A: Get OpenRouter API Key**

1. Go to https://openrouter.ai/
2. Click "Sign Up" (free, no credit card needed)
3. After signing in, go to "Keys" section
4. Click "Create Key"
5. Copy your API key (starts with `sk-or-v1-...`)

**Step B: Create .env File**

```powershell
# Copy the example environment file
copy .env.example .env

# Or create manually
notepad .env
```

**Step C: Add Your Configuration**

```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here

# Model Selection (Free tier options)
MODEL_NAME=meta-llama/llama-3.1-8b-instruct:free

# Model Parameters
MAX_TOKENS=4000
TEMPERATURE=0.3

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Optional: Advanced Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
```

**Available Free Models:**
- `meta-llama/llama-3.1-8b-instruct:free` (Recommended)
- `google/gemini-flash-1.5` (Fast)
- `mistralai/mistral-7b-instruct:free`

##### 2.7 Test API Connection

```powershell
# Test OpenRouter API connection
python test_openrouter.py

# Success output:
# Testing OpenRouter API...
# Response received
# Model used: meta-llama/llama-3.1-8b-instruct:free
# Response preview: ...
```

##### 2.8 Start Backend Server

```powershell
# Development mode (auto-reload on file changes)
python -m uvicorn app.main:app --reload

# The server will start on: http://localhost:8000

# Success output:
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
# INFO:     Started server process
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

**Alternative: Production Mode**

```powershell
# Production mode (no auto-reload)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

##### 2.9 Verify Backend is Running

Open your browser and visit:

- **API Root**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

You should see the interactive API documentation!

#### **Step 3: Set Up Frontend**

Open a **new PowerShell window** (keep backend running in the first one).

##### Option 1: Direct Browser Opening (Simplest)

```powershell
# Navigate to frontend directory
cd "d:\Y4S1\Research new\reserch component\Legal\frontend"

# Open index.html in default browser
start index.html

# Or right-click index.html → "Open with" → Your browser
```

Advantages:
- No additional setup needed
- Instant access
- Works immediately

Note: This component focuses on direct text input for streamlined analysis.

##### Option 2: Live Server (VS Code) - Recommended for Development

```powershell
# If you have VS Code:

1. Open VS Code
2. Install "Live Server" extension:
   - Press Ctrl+Shift+X
   - Search "Live Server"
   - Click Install

3. Open frontend folder in VS Code:
   File → Open Folder → Select "frontend" folder

4. Right-click on index.html
5. Select "Open with Live Server"

# Browser opens automatically at: http://127.0.0.1:5500
```

Advantages:
- Auto-refresh on file changes
- Full CORS support
- Development-friendly
- Professional workflow

##### Option 3: Python HTTP Server

```powershell
# Navigate to frontend directory
cd "d:\Y4S1\Research new\reserch component\Legal\frontend"

# Start HTTP server on port 5500
python -m http.server 5500

# Success output:
# Serving HTTP on :: port 5500 (http://[::]:5500/) ...

# Open browser manually to: http://localhost:5500
```

Advantages:
- No additional software needed
- Full CORS support
- Works on any Python installation

#### **Step 4: Verify Complete Setup**

**Backend Checklist:**
- [ ] Virtual environment activated `(.venv)` visible
- [ ] Dependencies installed (`pip list` shows packages)
- [ ] `.env` file created with valid API key
- [ ] Server running on http://localhost:8000
- [ ] Swagger docs accessible at http://localhost:8000/docs

**Frontend Checklist:**
- [ ] Frontend accessible in browser
- [ ] Text input interface visible and functional
- [ ] Form validation working (try typing text)
- [ ] Character counter updating in real-time
- [ ] No console errors (press F12 to check)

**Integration Test:**
1. Open frontend in browser
2. Go to "Text Input" tab
3. Paste any legal text (50+ characters)
4. Click "Analyze Argument"
5. Results appear with scores and categories

---

##  Usage Guide

### For End Users (Web Interface)

#### **Scenario 1: Analyzing Text Directly**

**Step-by-Step:**

1. **Open the Application**
   - Navigate to http://localhost:5500 (or your frontend URL)

2. **View Text Input Interface**
   - The main text input area is displayed prominently

3. **Enter Legal Argument**
   ```
   Paste your legal argument text into the textarea.
   
   Example:
   "The defendant's actions constitute a clear breach of 
   contract under Section 73 of the Contracts Act. The 
   plaintiff has provided substantial evidence including 
   email correspondence and witness testimonies..."
   ```

4. **Validate Input**
   - Minimum: 50 characters
   - Maximum: 10,000 characters
   - Counter shows: "X / 10000 characters"
   - Green indicator: Valid
   - Red indicator: Invalid

5. **Submit for Analysis**
   - Click "Analyze Argument" button
   - Loading indicator appears
   - Wait 3-10 seconds for results

6. **View Results**
   - **Overall Score Card**: Large animated score display
   - **Strength Label**: Classification (Very Weak to Exceptional)
   - **Category Breakdown**: 8 detailed cards showing:
     - Individual scores (0-100)
     - Detailed rationales
     - Specific suggestions for improvement
   - **Visual Indicators**:
     - Green badges: High scores (80+)
     - Yellow badges: Medium scores (60-79)
     - Red badges: Low scores (<60)

7. **Take Action**
   - Read suggestions carefully
   - Note weak areas highlighted
   - Click "Analyze Another Argument" to continue

### For Developers (Programmatic API Usage)

#### **Python Example: Analyze Text**

```python
import requests

# API endpoint
API_URL = "http://localhost:8000/api/v1/analyze"

# Your legal argument
argument_text = """
The plaintiff has established all elements required for breach 
of contract: valid agreement, defendant's performance obligation, 
failure to perform, and resulting damages. According to Section 73 
of the Contracts Act, damages must be proven...
"""

# Make API request
response = requests.post(
    API_URL,
    json={"argument_text": argument_text}
)

# Parse response
if response.status_code == 200:
    result = response.json()
    
    print(f"Overall Score: {result['overall_score']}/100")
    print(f"Strength: {result['strength']}")
    print("\nCategory Breakdown:")
    
    for category, data in result['categories'].items():
        print(f"\n{category.upper()}")
        print(f"  Score: {data['score']}/100")
        print(f"  Rationale: {data['rationale'][:100]}...")
        print(f"  Suggestions: {len(data['suggestions'])} items")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```



#### **cURL Example: Analyze Text**

```bash
# Windows PowerShell
curl -X POST "http://localhost:8000/api/v1/analyze" `
     -H "Content-Type: application/json" `
     -d '{\"argument_text\": \"Your legal argument here...\"}'

# Linux/Mac
curl -X POST "http://localhost:8000/api/v1/analyze" \
     -H "Content-Type: application/json" \
     -d '{"argument_text": "Your legal argument here..."}'
```



#### **JavaScript/Fetch Example**

```javascript
// Analyze text
async function analyzeText(argumentText) {
    try {
        const response = await fetch('http://localhost:8000/api/v1/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                argument_text: argumentText
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Overall Score:', result.overall_score);
        console.log('Strength:', result.strength);
        
        // Process categories
        Object.entries(result.categories).forEach(([name, data]) => {
            console.log(`${name}: ${data.score}/100`);
        });
        
        return result;
    } catch (error) {
        console.error('Analysis failed:', error);
    }
}

// Usage
const text = "Your legal argument...";
analyzeText(text);
```

---

##  Technical Details

### Technology Stack

#### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.12+ | Core programming language |
| **FastAPI** | 0.109+ | Modern async web framework |
| **Uvicorn** | Latest | ASGI server for FastAPI |
| **Pydantic** | 2.0+ | Data validation and settings |
| **python-dotenv** | Latest | Environment variable management |
| **requests** | Latest | HTTP client for API calls |
| **PyPDF2** | Latest | PDF text extraction |
| **python-multipart** | Latest | File upload handling |

#### Frontend Technologies

| Technology | Purpose |
|------------|---------|
| **HTML5** | Semantic markup, modern features |
| **CSS3** | Styling, animations, gradients, flexbox/grid |
| **JavaScript (ES6+)** | Interactive functionality, async/await |
| **Fetch API** | HTTP requests to backend |
| **CSS Variables** | Dynamic theming |
| **CSS Grid/Flexbox** | Responsive layouts |

#### External Services

| Service | Purpose |
|---------|---------|
| **OpenRouter API** | LLM model aggregation and routing |
| **Multiple LLMs** | Llama 3.1, GPT-4, Claude 3.5, Gemini Pro |

### Core Processing Modules

#### **1. main.py** - Application Entry Point

```python
Purpose:
├─ Initialize FastAPI application
├─ Configure CORS (Cross-Origin Resource Sharing)
├─ Register API routes
├─ Set up middleware
├─ Configure static files
└─ Define startup/shutdown events

Key Features:
├─ Async support for concurrent requests
├─ Auto-generated API documentation
├─ Request validation
└─ Error handling middleware
```

#### **2. inference_service.py** - Analysis Orchestrator

```python
Purpose:
├─ Main coordinator for argument analysis
├─ Load grading schema
├─ Construct prompts for LLM
├─ Parse and validate responses
└─ Calculate overall scores

Functions:
├─ analyze_argument(text: str) -> dict
├─ parse_llm_response(response: str) -> dict
├─ calculate_overall_score(categories: dict) -> int
└─ determine_strength(score: int) -> str

Process Flow:
1. Receive argument text
2. Load 8-category rubric
3. Build structured prompt
4. Call LLM service
5. Parse JSON response
6. Validate category scores
7. Calculate overall score
8. Determine strength label
9. Return formatted results
```

#### **3. llm_service.py** - LLM Integration
