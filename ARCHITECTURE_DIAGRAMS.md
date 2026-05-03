# COMPLIANCE CHECKER - ARCHITECTURE & WORKFLOW DIAGRAMS

---

## System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                                │
│  (Vanilla JavaScript - index.html + app.js + style.css)             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Sidebar Navigation                                           │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │ • Similar Case Finder (backend-M)                           │   │
│  │ • Compliance Checker (backend-C) ← THIS COMPONENT          │   │
│  │ • Case Extractor (backend-N)                                │   │
│  │ • Argument Scorer (backend-N)                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Compliance Checker UI (3 Tabs)                              │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                               │   │
│  │  Tab 1: Check Document           Tab 2: History            │   │
│  │  ┌────────────────────┐          ┌────────────────────┐    │   │
│  │  │ File Upload/Paste  │          │ Analyses List      │    │   │
│  │  │ PDF/Text Toggle    │          │ Pagination         │    │   │
│  │  │ Drag & Drop Zone   │          │ Filters            │    │   │
│  │  │ [Analyze Button]   │          │ View Details       │    │   │
│  │  └────────────────────┘          └────────────────────┘    │   │
│  │                                                               │   │
│  │  Tab 3: Acts Library             Results Display           │   │
│  │  ┌────────────────────┐          ┌────────────────────┐    │   │
│  │  │ Search Box         │          │ Compliance Score % │    │   │
│  │  │ Category Filters   │          │ Domain Detected    │    │   │
│  │  │ Acts PDF List      │          │ ✓ Present Clauses │    │   │
│  │  │ Download Option    │          │ ❌ Missing Clauses│    │   │
│  │  └────────────────────┘          │ Statutory Citations│    │   │
│  │                                  │ [Export PDF]       │    │   │
│  │                                  └────────────────────┘    │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└──────────────────┬───────────────────────────────────────────────────┘
                   │ HTTP/JSON (CORS-enabled)
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND (backend-C)                        │
│              (Python 3.8+ | FastAPI | PyTorch)                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ API LAYER (api.py)                                           │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                               │   │
│  │  POST /check                → Text compliance check          │   │
│  │  POST /upload-pdf          → PDF upload & analysis           │   │
│  │  GET /history              → Paginated analysis history      │   │
│  │  GET /history/{id}         → Specific analysis record        │   │
│  │  GET /acts/list            → Available Acts PDFs             │   │
│  │  GET /acts/download/{fn}   → Download Act PDF               │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                   ▼                ▼                ▼               │
│  ┌─────────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │ REQUEST HANDLER      │  │ PDF EXTRACTOR  │  │ RESPONSE BUILDER
│  │ (Validation)         │  │ (PyMuPDF)      │  │ (JSON formatting)
│  └──────────┬───────────┘  └────────┬────────┘  └────────┬─────────┘
│             │                       │                    ▲
│             └───────────────────────┼────────────────────┘
│                                     │
│                                     ▼
│  ┌──────────────────────────────────────────────────────────┐
│  │ DOCUMENT VALIDATION & PROCESSING                         │
│  ├──────────────────────────────────────────────────────────┤
│  │                                                            │
│  │  1. Type Validation (validate_document_is_contract)      │
│  │     ├─ Detect: Contract vs. Judgment vs. Legislation     │
│  │     ├─ Keywords: Judgment (25), Contract (35)            │
│  │     ├─ Patterns: 8 regex patterns for court documents    │
│  │     └─ Result: Accept/Reject with reason                 │
│  │                                                            │
│  │  2. Text Extraction                                       │
│  │     ├─ If PDF: Extract text from all pages               │
│  │     ├─ If Text: Use as-is                                │
│  │     └─ Normalize: Remove extra whitespace                │
│  │                                                            │
│  │  3. Pass to Compliance Engine                            │
│  │     └─ Invoke check_compliance()                          │
│  │                                                            │
│  └──────────────────────────────────────────────────────────┘
│                             │
│                             ▼
│  ┌──────────────────────────────────────────────────────────┐
│  │ COMPLIANCE CHECKING ENGINE (compliance_checker_v2.py)    │
│  ├──────────────────────────────────────────────────────────┤
│  │                                                            │
│  │  PIPELINE:                                                │
│  │                                                            │
│  │  Step 1: DOMAIN DETECTION                                │
│  │  ├─ Keyword analysis (domain-specific keywords)           │
│  │  ├─ Match against 10 domains                              │
│  │  ├─ Calculate confidence                                  │
│  │  └─ Output: domain, domain_confidence                     │
│  │                                                            │
│  │  Step 2: CLAUSE EXTRACTION                                │
│  │  ├─ Split text into sentences                             │
│  │  ├─ Pattern matching (150+ patterns)                      │
│  │  ├─ Extract clause text & context                         │
│  │  └─ Output: clauses[] {text, category, raw_text}         │
│  │                                                            │
│  │  Step 3: CLAUSE CLASSIFICATION                            │
│  │  ├─ For each clause, classify category                    │
│  │  ├─ Look up statutory mapping                             │
│  │  ├─ Get Act, Section, Rule                                │
│  │  └─ Output: classified_clauses[]                          │
│  │                                                            │
│  │  Step 4: MANDATORY CLAUSE VALIDATION                      │
│  │  ├─ Get mandatory list for domain                         │
│  │  ├─ Check presence in classified_clauses                  │
│  │  ├─ Flag missing clauses                                  │
│  │  └─ Output: present_mandatory[], missing_mandatory[]      │
│  │                                                            │
│  │  Step 5: ML CONFIDENCE SCORING                            │
│  │  ├─ For each finding, invoke NLI model                    │
│  │  ├─ If unavailable, use rule-based fallback               │
│  │  ├─ Calibrate confidence scores                           │
│  │  └─ Output: confidence scores per finding                 │
│  │                                                            │
│  │  Step 6: REPORT GENERATION                                │
│  │  ├─ Aggregate all findings                                │
│  │  ├─ Calculate overall compliance score                    │
│  │  ├─ Generate detailed report                              │
│  │  └─ Output: {domain, clauses, scores, missing, present}  │
│  │                                                            │
│  └──────────────────────────────────────────────────────────┘
│     │       │              │              │
│     ▼       ▼              ▼              ▼
│  ┌────────────────────────────────────────────────────┐
│  │ SUPPORTING MODULES                                │
│  ├────────────────────────────────────────────────────┤
│  │                                                    │
│  │  predict.py                                       │
│  │  └─ NLI Model Inference                          │
│  │     ├─ Load fine-tuned transformer               │
│  │     ├─ Tokenize premise + hypothesis             │
│  │     ├─ Forward pass → logits                      │
│  │     ├─ Softmax → probabilities                    │
│  │     └─ Calibrate confidence                       │
│  │        └─ Sigmoid scaling + margin boost          │
│  │                                                    │
│  │  CATEGORY_LAW_MAPPING                            │
│  │  └─ 150+ categories → Act + Section + Rule       │
│  │     Sample: {                                     │
│  │       "salary": {                                 │
│  │         "act": "Wages Boards Ordinance",         │
│  │         "section": "17",                          │
│  │         "rule": "Wages must be paid monthly"     │
│  │       },                                          │
│  │       ...                                         │
│  │     }                                             │
│  │                                                    │
│  └────────────────────────────────────────────────────┘
│                     │
│                     ▼
│  ┌──────────────────────────────────────────────────────────┐
│  │ HISTORY MANAGEMENT & PERSISTENCE                         │
│  ├──────────────────────────────────────────────────────────┤
│  │                                                            │
│  │  _save_analysis()                                         │
│  │  ├─ Generate UUID for analysis_id                        │
│  │  ├─ Calculate compliance_score                           │
│  │  ├─ Serialize JSON fields                                │
│  │  ├─ INSERT into database                                 │
│  │  └─ COMMIT (atomic transaction)                          │
│  │                                                            │
│  │  _get_history()                                           │
│  │  ├─ SELECT from database                                 │
│  │  ├─ Order by analyzed_at DESC                            │
│  │  ├─ Apply pagination (LIMIT/OFFSET)                      │
│  │  └─ Return JSON response                                 │
│  │                                                            │
│  └──────────────────────────────────────────────────────────┘
│
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    DATA PERSISTENCE LAYER                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ SQLite Database (backend-C/data/compliance_history.db)      │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │                                                               │   │
│  │  TABLE: analyses                                             │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │ id (PK, UUID)                                       │    │   │
│  │  │ filename (TEXT)                                     │    │   │
│  │  │ document_type (TEXT) - "PDF"/"Text"               │    │   │
│  │  │ domain (TEXT) - "Employment"/"Rental"/etc.        │    │   │
│  │  │ analyzed_at (TEXT, ISO timestamp)                 │    │   │
│  │  │ compliance_score (REAL, 0-100)                    │    │   │
│  │  │ text_snippet (TEXT, 500 chars)                    │    │   │
│  │  │ clauses (TEXT/JSON, array)                        │    │   │
│  │  │ present_mandatory (TEXT/JSON, array)              │    │   │
│  │  │ missing_mandatory (TEXT/JSON, array)              │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │                                                               │   │
│  │  Features:                                                    │   │
│  │  ✓ ACID compliance (atomic transactions)                    │   │
│  │  ✓ Row factory (dict-like access)                           │   │
│  │  ✓ Full audit trail                                         │   │
│  │  ✓ Scalable (handles 1000+ records easily)                 │   │
│  │  ✓ No external dependencies                                 │   │
│  │                                                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Statutory Rules Database (data/statutes_structured/)        │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │                                                               │   │
│  │  statutes.json (150+ entries)                               │   │
│  │  └─ Clause categories → Acts + Sections + Rules             │   │
│  │                                                               │   │
│  │  acts_pdfs/ (directory)                                      │   │
│  │  └─ Statutory Acts PDFs for user reference                 │   │
│  │                                                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram (Single Analysis)

```
USER INPUT
    │
    ├─ Option A: Upload PDF File
    │  └─ File → multipart/form-data → POST /upload-pdf
    │
    └─ Option B: Paste Contract Text
       └─ Text → JSON → POST /check

         ▼
┌─────────────────────────┐
│ API Receives Request    │
└────────┬────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Parse & Validate Input         │
└────────┬───────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ Extract Text                         │
├──────────────────────────────────────┤
│ If PDF:                              │
│ • Open with PyMuPDF                  │
│ • Extract text from each page        │
│ • Concatenate                        │
│ If Text:                             │
│ • Use as-is                          │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ Validate Document Type              │
├──────────────────────────────────────┤
│ Is it a valid contract?              │
│ ├─ Count judgment keywords           │
│ ├─ Count contract keywords           │
│ ├─ Apply regex patterns              │
│ ├─ Score: judgment vs. contract      │
│ └─ Reject if not contract            │
└────────┬─────────────────────────────┘
         │
         ├─ REJECT ──→ Return error response
         │
         └─ ACCEPT ──┐
                     ▼
         ┌───────────────────────┐
         │ check_compliance()    │
         └───────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌──────────┐
│ DOMAIN  │  │ CLAUSE  │  │ CLASSIFY │
│DETECTION│  │EXTRACTION│  │ CLAUSES  │
└────┬────┘  └────┬────┘  └────┬─────┘
     │            │            │
     └────────────┼────────────┘
                  │
                  ▼
        ┌──────────────────────┐
        │ MANDATORY CLAUSE     │
        │ VALIDATION           │
        │                      │
        │ Get mandatory list   │
        │ Check presence       │
        │ Flag missing         │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ ML SCORING           │
        │ (NLI Inference)      │
        │                      │
        │ For each finding:    │
        │ • Input: premise +   │
        │   hypothesis         │
        │ • NLI model          │
        │ • Get probability    │
        │ • Fallback if needed │
        │ • Calibrate score    │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ REPORT GENERATION    │
        │                      │
        │ • Aggregate findings │
        │ • Calculate score    │
        │ • Format response    │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ SAVE TO HISTORY      │
        │                      │
        │ • Generate UUID      │
        │ • Serialize JSON     │
        │ • INSERT to DB       │
        │ • COMMIT             │
        └──────────┬───────────┘
                   │
                   ▼
      ┌─────────────────────────┐
      │ Return JSON Response    │
      │ {                       │
      │   domain: "Employment", │
      │   clauses: [...],       │
      │   present_mandatory: [ ], │
      │   missing_mandatory: [ ], │
      │   compliance_score: 85,  │
      │   analysis_id: "uuid"    │
      │ }                       │
      └─────────────────────────┘
                   │
                   ▼
         ┌──────────────────┐
         │ Frontend Renders │
         │ Results          │
         └──────────────────┘
```

---

## History Page Workflow

```
User: Click "Compliance" tab → "History"
         │
         ▼
┌──────────────────────────┐
│ Frontend Component Init  │
│ Load cmp-history tab     │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ JavaScript: loadCmpHistory()     │
└────────┬───────────────────────── ┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Fetch API: GET /history?limit=10&skip=0 │
└────────┬────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────────────────┐
│ Backend: get_history() endpoint                  │
├───────────────────────────────────────────────────┤
│ 1. Connect to SQLite                              │
│ 2. SELECT * FROM analyses                         │
│    ORDER BY analyzed_at DESC                      │
│    LIMIT 10 OFFSET 0                              │
│ 3. SELECT COUNT(*) for total                      │
│ 4. Convert rows to dicts                          │
│    (Parse JSON fields)                            │
│ 5. Return JSON:                                   │
│    {                                              │
│      "analyses": [ {...}, {...}, ... ],          │
│      "total": 47,                                 │
│      "limit": 10,                                 │
│      "skip": 0                                    │
│    }                                              │
└────────┬──────────────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────┐
│ Frontend: Render History List     │
├───────────────────────────────────┤
│                                   │
│ For each analysis in response:    │
│ ┌─────────────────────────────┐   │
│ │ Filename   | Domain | Score | Date     │
│ ├─────────────────────────────┤   │
│ │ contract.pdf | Employment | 85% | 2024-04-23 │
│ │ lease.pdf    | Rental      | 72% | 2024-04-22 │
│ │ ...                                  │
│ │ ...                                  │
│ │ ...                                  │
│ │ (10 records shown)                   │
│ └─────────────────────────────┘   │
│                                   │
│ Show: "Showing 1-10 of 47"        │
│ If total > 10:                    │
│   Show "Load More" button          │
│                                   │
│ Click row → View full analysis    │
│ Click "Load More" → Fetch next 10 │
│                                   │
└───────────────────────────────────┘
         │
         ├─ User clicks row
         │   │
         │   ▼
         │  GET /history/{analysis_id}
         │   │
         │   ▼
         │  Show modal with full analysis
         │
         └─ User clicks "Load More"
             │
             ▼
            GET /history?limit=10&skip=10
             │
             ▼
            Append 10 more records to list
             │
             ▼
            Update "Showing 1-20 of 47"
```

---

## Database Query Examples

### Insert Analysis
```sql
INSERT INTO analyses 
VALUES (
    'a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6',
    'employment_contract_v2.pdf',
    'PDF',
    'Employment',
    '2024-04-23T14:30:45.123456',
    85.5,
    'This Employment Agreement is entered into between...',
    '[{"text": "The employee is entitled to 14 days...", "category": "leave", "confidence": 0.92}]',
    '["salary", "leave", "epf", "etf"]',
    '["termination_notice", "gratuity_clause"]'
);
```

### Retrieve Recent Analyses
```sql
SELECT 
    id, 
    filename, 
    domain, 
    compliance_score, 
    analyzed_at
FROM analyses
ORDER BY analyzed_at DESC
LIMIT 10;
```

### Get Statistics by Domain
```sql
SELECT 
    domain,
    COUNT(*) as total,
    AVG(compliance_score) as avg_score,
    MAX(compliance_score) as best,
    MIN(compliance_score) as worst
FROM analyses
GROUP BY domain
ORDER BY avg_score DESC;
```

### Find Analyses with Low Compliance
```sql
SELECT 
    filename, 
    domain, 
    compliance_score,
    missing_mandatory,
    analyzed_at
FROM analyses
WHERE compliance_score < 70
ORDER BY compliance_score ASC;
```

---

## ML Confidence Scoring Pipeline

```
NLI Model Inference
    │
    Input: Premise (contract text) + Hypothesis (compliance rule)
    │
    Example:
    Premise: "The employee shall receive a monthly salary of LKR 50,000..."
    Hypothesis: "The contract complies with Wages Boards Ordinance §17"
    │
    ▼
┌─────────────────────────────────────┐
│ Tokenization                         │
│ [CLS] premise [SEP] hypothesis [EOS]│
└────────┬────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────────┐
│ Forward Pass through NLI Transformer      │
│                                           │
│ Input embeddings → Multi-head attention   │
│ → BERT encoders → Classification head     │
│                                           │
│ Output: logits [entail_logit, notent_logit]
└────────┬────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Softmax Activation                     │
│ Entailment prob: softmax[0]            │
│ Not Entailment prob: softmax[1]        │
│                                        │
│ Example: {entail: 0.92, notent: 0.08} │
└────────┬────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│ Confidence Calibration                                  │
│                                                          │
│ Step 1: Normalize                                       │
│   raw_conf = 92 (from softmax * 100)                   │
│   normalized = (92 - 50) / 50 = 0.84                   │
│                                                          │
│ Step 2: Apply sigmoid scaling                          │
│   sigmoid_input = (0.84 - 0.5) * 3.0 = 1.02           │
│   sigmoid_value = 1 / (1 + exp(-1.02)) = 0.735        │
│                                                          │
│ Step 3: Map to range                                    │
│   base = 70, ceiling = 98                              │
│   calibrated = 70 + (98-70) * 0.735 = 90.6            │
│                                                          │
│ Step 4: Apply margin bonus                             │
│   margin = 0.92 - 0.08 = 0.84 (>20%)                  │
│   final_conf = min(90.6 + 5, 98) = 95.6               │
│                                                          │
│ Result: 95.6% confidence                               │
│                                                          │
└────────┬─────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Return Calibrated Score            │
│ {                                  │
│   confidence: 95.6,                │
│   entailment: true,                │
│   raw_prob: 0.92                   │
│ }                                  │
└────────────────────────────────────┘
         │
         ▼
If NLI Unavailable → Use Fallback
    │
    ├─ Keyword overlap: 30 points
    ├─ Legal terminology: 20 points
    ├─ Semantic similarity: 25 points
    └─ Total: 70-85% range
```

---

## Integration with Other Modules

```
┌─────────────────────────────────────────────────────┐
│           Frontend (Unified UI)                     │
│  ┌──────┬──────────────┬──────────┬──────────────┐  │
│  │ Sim. │ COMPLIANCE   │ Extractor│ Argument     │  │
│  │      │ CHECKER ✓    │ Scorer   │ Scorer       │  │
│  └──────┼──────────────┼──────────┼──────────────┘  │
│         │              │          │                 │
└─────────┼──────────────┼──────────┼─────────────────┘
          │              │          │
          ▼              ▼          ▼
     ┌────────────┐ ┌─────────┐ ┌──────────┐
     │backend-M   │ │backend-C│ │backend-N │
     │(Similarity)│ │(OURS)   │ │(Other)   │
     │Port: 8001  │ │Port:8000│ │Port:8002 │
     └────────────┘ └─────────┘ └──────────┘
          │              │          │
          ├──────────────┼──────────┤
          │ Similar       │ Compliance│ Other
          │ Case Search   │ Checking  │ Services
          │ (Case law)    │ (Contracts)
          │               │
          └───────────────┴──────────

Data Flows:
- Compliance Checker: PDF → Extraction → Domain → Clauses → Scoring → History (SQLite)
- All results returned as JSON to frontend
- History persisted in SQLite database
- Cross-component communication via REST API
```

---

## Deployment Architecture

```
┌──────────────────────────────────────────────┐
│         Production Deployment                │
├──────────────────────────────────────────────┤
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ Load Balancer / Reverse Proxy          │  │
│  │ (Nginx)                                │  │
│  └─────────┬────────────────────────────┬─┘  │
│            │                            │    │
│     ┌──────▼────────┐         ┌────────▼──┐ │
│     │ FastAPI       │         │ FastAPI   │ │
│     │ Instance 1    │         │ Instance 2│ │
│     │ (Uvicorn)     │         │ (Uvicorn) │ │
│     └──────┬────────┘         └────────┬──┘ │
│            │                            │    │
│  ┌─────────┴────────────────────────────┴──┐ │
│  │      Shared SQLite Database              │ │
│  │  (compliance_history.db)                 │ │
│  │  - All instances can access              │ │
│  │  - ACID compliance                       │ │
│  │  - Auto-backup                           │ │
│  └──────────────────────────────────────────┘ │
│            │                                  │
│  ┌─────────▼──────────────────────────────┐  │
│  │      ML Model Cache                     │  │
│  │  - NLI transformer (shared)             │  │
│  │  - Loaded once per instance             │  │
│  │  - GPU accelerated (if available)       │  │
│  └─────────────────────────────────────────┘ │
│            │                                  │
│  ┌─────────▼──────────────────────────────┐  │
│  │      Data Storage                       │  │
│  │  - statutes.json (150+ mappings)       │  │
│  │  - acts_pdfs/ (statutory acts)         │  │
│  │  - Static files                        │  │
│  └─────────────────────────────────────────┘ │
│                                              │
│  Environment Variables:                      │
│  - DATABASE_URL                              │
│  - MODEL_PATH                                │
│  - DEBUG_MODE                                │
│  - CORS_ORIGINS                              │
│  - LOG_LEVEL                                 │
│                                              │
└──────────────────────────────────────────────┘
```

---

**End of Architecture Documentation**
