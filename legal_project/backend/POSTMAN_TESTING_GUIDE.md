# 🚀 Testing Backend with Postman

## 📥 Import Collection

### Step 1: Download Postman
- Download: https://www.postman.com/downloads/
- Install and launch Postman

### Step 2: Import Collection
1. Click **Import** button (top-left)
2. Choose **File** tab
3. Select: `Legal_Backend_API.postman_collection.json`
4. Click **Import**

✅ All 9 API endpoints are now ready to test!

---

## ✅ Test Endpoints (In Order)

### 1️⃣ Health Check
**Endpoint:** `GET http://localhost:5000/api/health`

- Click **Send**
- You should see `"status": "Server is running"`
- ✅ Confirms backend is running

**Response:**
```json
{
  "status": "Server is running",
  "timestamp": "2024-01-04T10:00:00.000Z",
  "environment": "development"
}
```

---

### 2️⃣ Find Similar Cases (YOUR ML COMPONENT)
**Endpoint:** `POST http://localhost:5000/api/similar-cases/find`

- Pre-filled body with employment dispute case
- Click **Send**
- Backend searches database for similar cases

**Request Body:**
```json
{
  "caseText": "Employment contract dispute...",
  "caseType": "Labour",
  "limit": 5
}
```

**Response (when database has data):**
```json
{
  "found": 5,
  "highestMatch": 92.5,
  "averageMatch": 85.3,
  "results": [
    {
      "caseId": "case_001",
      "title": "Smith v. Jones",
      "similarityScore": 92.5,
      "relevantPoints": ["Breach of contract", ...],
      "matchType": "Exact Match"
    }
  ]
}
```

---

### 3️⃣ Upload New Case
**Endpoint:** `POST http://localhost:5000/api/similar-cases/upload`

- Fill in case details:
  - Title, text, type, court, year
- Click **Send**
- Case is saved to MongoDB database

**Request Body:**
```json
{
  "caseText": "Full case text...",
  "title": "Smith v. Jones",
  "caseType": "Labour",
  "court": "District Court",
  "year": 2023
}
```

**Response:**
```json
{
  "message": "Case uploaded successfully",
  "caseId": "507f1f77bcf86cd799439011",
  "case": {
    "_id": "507f1f77bcf86cd799439011",
    "caseId": "case_1704355200000",
    "title": "Smith v. Jones",
    ...
  }
}
```

---

### 4️⃣ Get All Cases
**Endpoint:** `GET http://localhost:5000/api/similar-cases?page=1&limit=10`

- Lists all cases in database
- Supports pagination and filtering
- Click **Send**

**Response:**
```json
{
  "total": 5,
  "page": 1,
  "pages": 1,
  "results": [
    {
      "_id": "...",
      "title": "Case Title",
      "caseType": "Labour",
      "year": 2023
    }
  ]
}
```

---

### 5️⃣ Classify Case
**Endpoint:** `POST http://localhost:5000/api/cases/classify`

- Analyzes case text and determines type
- Returns classification with confidence

**Request Body:**
```json
{
  "caseText": "Contract dispute case..."
}
```

**Response:**
```json
{
  "caseType": "Civil",
  "confidence": 0.92,
  "tags": ["contract", "dispute", "damages"]
}
```

---

### 6️⃣ Audit Document (Compliance)
**Endpoint:** `POST http://localhost:5000/api/compliance/audit`

- Checks document against Sri Lankan laws
- Returns compliance score

**Request Body:**
```json
{
  "documentText": "Employment contract: 48 hours/week, LKR 50,000/month..."
}
```

**Response:**
```json
{
  "complianceScore": 78,
  "violations": 5,
  "status": "REVIEW_NEEDED",
  "criticalIssues": 2,
  "warnings": 3
}
```

---

### 7️⃣ Analyze Document Structure
**Endpoint:** `POST http://localhost:5000/api/documents/analyze`

- Analyzes document structure
- Returns sections, clauses, references

**Request Body:**
```json
{
  "documentText": "Section 1: Intro. Section 2: Terms..."
}
```

**Response:**
```json
{
  "sections": 7,
  "clauses": 38,
  "crossReferences": 12,
  "ambiguousSections": 2
}
```

---

### 8️⃣ Analyze Argument Strength
**Endpoint:** `POST http://localhost:5000/api/arguments/analyze`

- Scores argument strength
- Returns detailed scoring breakdown

**Request Body:**
```json
{
  "argumentText": "The defendant breached the contract..."
}
```

**Response:**
```json
{
  "overallScore": 72,
  "criteria": {
    "factualSupport": 75,
    "legalPrecedent": 68,
    "counterarguments": 65,
    "evidence": 78
  },
  "weaknesses": [],
  "improvements": []
}
```

---

## 🧪 Testing Workflow

**Recommended order:**

1. ✅ **Health Check** - Verify server is running
2. ✅ **Upload Case** - Add sample data to database (do this 2-3 times)
3. ✅ **Get All Cases** - See uploaded cases
4. ✅ **Find Similar Cases** - Search for similar ones
5. ✅ **Classify Case** - Test classification
6. ✅ **Audit Document** - Test compliance
7. ✅ **Analyze Document** - Test structure analysis
8. ✅ **Analyze Argument** - Test argument scoring

---

## 🔍 Troubleshooting

### "Cannot GET /api/health"
❌ **Problem:** Backend not running
✅ **Solution:** Run `npm run dev` in backend folder

### "ECONNREFUSED 127.0.0.1:5000"
❌ **Problem:** Backend not listening on port 5000
✅ **Solution:** 
- Kill any process on port 5000
- Restart backend server

### "Bad Gateway" or timeout
❌ **Problem:** Request taking too long
✅ **Solution:** 
- Check MongoDB is running
- Check backend logs for errors

### Empty results for "Find Similar Cases"
❌ **Problem:** No cases in database yet
✅ **Solution:** 
- Use "Upload Case" endpoint first
- Add 2-3 sample cases
- Then search

---

## 📊 Expected Test Results

After uploading 3 cases with similar themes:

```
Upload Case 1: "Smith v. Jones - Employment Dispute"
Upload Case 2: "ABC Corp v. XYZ - Contract Breach"  
Upload Case 3: "Employee Rights - Labour Dispute"

Then search for:
"Employment contract dispute regarding termination"

Expected: Find Cases 1 & 3 with high similarity scores
```

---

## 💡 Pro Tips

1. **Save requests** - Right-click endpoint, select "Save"
2. **Use Variables** - Set `{{url}}` = `http://localhost:5000`
3. **Test Collections** - Run all at once with "Collection Runner"
4. **View history** - All past requests saved automatically
5. **Export results** - Share findings with team

---

## 🔗 Backend Status

Current status: **✅ Running on http://localhost:5000**

MongoDB: **✅ Connected to local database**

All endpoints: **✅ Ready for testing**

**Start testing now!** 🎉
