# 📋 Frontend Developer Guide

## 🚀 Quick Start: Backend + Frontend Integration

### Step 1: Setup Backend API (5 minutes)

```powershell
# 1. Extract the project ZIP
# You'll get a 'backend' folder containing the API

# 2. Navigate to backend folder
cd backend

# 3. Create virtual environment
python -m venv .venv

# 4. Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 6. Get free API key from https://openrouter.ai/
#    - Sign in with Google/GitHub
#    - Go to "Keys" → "Create Key"
#    - Copy the key (starts with sk-or-v1-...)

# 7. Create .env file
Copy-Item .env.example .env
notepad .env

# Paste your API key:
# INFERENCE_BACKEND=openrouter
# OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE

# 8. Start the backend server
python -m uvicorn app.main:app --reload --port 8000

# ✅ Server running at http://localhost:8000
```

**Verify backend is working:**
- Open http://localhost:8000 → Should show API info
- Open http://localhost:8000/docs → Swagger UI

---

### Step 2: Setup Your Frontend

**Option A: React (Create React App)**
```bash
npx create-react-app legal-analyzer-frontend
cd legal-analyzer-frontend
npm start
# Frontend runs on http://localhost:3000
```

**Option B: React (Vite - Faster)**
```bash
npm create vite@latest legal-analyzer-frontend -- --template react
cd legal-analyzer-frontend
npm install
npm run dev
# Frontend runs on http://localhost:5173
```

**Option C: Plain HTML**
```bash
# Just create index.html and open in browser
# Use Live Server extension in VS Code
```

---

### Step 3: Connect Frontend to Backend

**Important: Both servers must run simultaneously!**

```
Terminal 1: Backend API (port 8000)
Terminal 2: Frontend (port 3000/5173)
```

**Test connection from browser console (F12):**
```javascript
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  .then(data => console.log(data));

// Should show: { status: "healthy", backend: "openrouter" }
```

**If CORS error:** Backend is already configured for localhost:3000 and localhost:5173. If using different port, edit `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:YOUR_PORT",  # Add your port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔌 API Endpoints

| Endpoint | Method | Purpose | Input |
|----------|--------|---------|-------|
| `/api/v1/analyze` | POST | Analyze text | `{ "text": "..." }` |
| `/api/v1/upload` | POST | Upload PDF/TXT | FormData with file |
| `/api/v1/health` | GET | Check status | None |

**Base URL:** `http://localhost:8000`

---

## 📦 JSON Response Structure

### Complete Response Object

```typescript
interface AnalysisResponse {
  overall_score: number;        // 0-100
  strength_label: string;       // "Very Weak" | "Weak" | "Moderate" | "Strong"
  breakdown: CategoryScore[];   // 8 categories
  feedback: string[];           // Array of suggestions
  
  // Only for /upload endpoint:
  filename?: string;
  file_type?: string;
  text_length?: number;
  extracted_text?: string;
}

interface CategoryScore {
  category: string;             // Category name
  weight: number;               // Weight percentage (5-20)
  rubric_score: number;         // 0-5 rating
  points: number;               // Weighted points
  rationale: string;            // AI explanation
}
```

---

## 🎯 Quick Code Snippets

### 1. Analyze Text (JavaScript)

```javascript
async function analyzeText(legalText) {
  const response = await fetch('http://localhost:8000/api/v1/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: legalText })
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return await response.json();
}

// Usage:
const result = await analyzeText('The appellant argues...');
console.log(`Score: ${result.overall_score}/100`);
```

---

### 2. Upload PDF (JavaScript)

```javascript
async function uploadPDF(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/api/v1/upload', {
    method: 'POST',
    body: formData  // Don't set Content-Type header!
  });
  
  return await response.json();
}

// Usage:
const fileInput = document.getElementById('pdfFile');
const result = await uploadPDF(fileInput.files[0]);
```

---

### 3. Display Score (React)

```jsx
function ScoreDisplay({ result }) {
  const getColor = (score) => {
    if (score >= 80) return '#4CAF50';  // Green
    if (score >= 60) return '#FF9800';  // Orange
    return '#F44336';                    // Red
  };
  
  return (
    <div>
      <h1 style={{ color: getColor(result.overall_score) }}>
        {result.overall_score}/100
      </h1>
      <p>{result.strength_label}</p>
      
      <div style={{ 
        width: '100%', 
        height: '30px', 
        background: '#eee' 
      }}>
        <div style={{
          width: `${result.overall_score}%`,
          height: '100%',
          background: getColor(result.overall_score),
          transition: 'width 0.5s ease'
        }} />
      </div>
    </div>
  );
}
```

---

### 4. Category Breakdown (React)

```jsx
function CategoryBreakdown({ breakdown }) {
  return (
    <div className="categories">
      {breakdown.map((cat, idx) => {
        const percentage = (cat.rubric_score / 5) * 100;
        
        return (
          <div key={idx} className="category">
            <div className="header">
              <span>{cat.category}</span>
              <span>{cat.rubric_score}/5</span>
            </div>
            
            {/* Progress bar */}
            <div className="progress-bar">
              <div 
                className="progress" 
                style={{ width: `${percentage}%` }}
              />
            </div>
            
            <p className="rationale">{cat.rationale}</p>
          </div>
        );
      })}
    </div>
  );
}
```

---

### 5. Weaknesses Detector

```javascript
function findWeaknesses(breakdown) {
  return breakdown
    .filter(cat => cat.rubric_score < 3)  // Score below 3/5
    .map(cat => ({
      name: cat.category,
      score: cat.rubric_score,
      issue: cat.rationale,
      severity: cat.rubric_score <= 1 ? 'critical' : 'moderate'
    }));
}

// Usage:
const weaknesses = findWeaknesses(result.breakdown);

if (weaknesses.length > 0) {
  console.log('⚠️ Areas needing attention:');
  weaknesses.forEach(w => {
    console.log(`- ${w.name}: ${w.issue}`);
  });
}
```

---

### 6. Feedback List (React)

```jsx
function FeedbackList({ feedback }) {
  return (
    <div className="feedback">
      <h3>💡 Improvement Suggestions</h3>
      <ul>
        {feedback.map((tip, idx) => (
          <li key={idx}>{tip}</li>
        ))}
      </ul>
    </div>
  );
}
```

---

### 7. Chart Data Preparation

```javascript
// For Chart.js or similar
function prepareChartData(breakdown) {
  return {
    labels: breakdown.map(cat => cat.category),
    datasets: [{
      label: 'Category Scores',
      data: breakdown.map(cat => cat.rubric_score),
      backgroundColor: breakdown.map(cat => 
        cat.rubric_score >= 4 ? '#4CAF50' :
        cat.rubric_score >= 3 ? '#FF9800' : '#F44336'
      )
    }]
  };
}

// Usage with Chart.js:
const chartData = prepareChartData(result.breakdown);
new Chart(ctx, {
  type: 'bar',
  data: chartData,
  options: {
    scales: {
      y: { max: 5 }  // Rubric score is 0-5
    }
  }
});
```

---

### 8. Save Results to File

```javascript
function downloadJSON(data, filename = 'analysis-result.json') {
  const blob = new Blob(
    [JSON.stringify(data, null, 2)], 
    { type: 'application/json' }
  );
  
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Usage:
downloadJSON(result, 'my-analysis.json');
```

---

### 9. Compare Before/After

```javascript
function compareAnalyses(before, after) {
  const improvement = after.overall_score - before.overall_score;
  
  const categoryChanges = before.breakdown.map((cat, idx) => {
    const afterCat = after.breakdown[idx];
    return {
      category: cat.category,
      before: cat.rubric_score,
      after: afterCat.rubric_score,
      change: afterCat.rubric_score - cat.rubric_score
    };
  });
  
  return {
    scoreImprovement: improvement,
    categoryChanges: categoryChanges.filter(c => c.change !== 0)
  };
}

// Usage:
const comparison = compareAnalyses(originalResult, revisedResult);
console.log(`Overall improvement: ${comparison.scoreImprovement} points`);
```

---

### 10. Error Handling

```javascript
async function safeAnalyze(text) {
  try {
    const response = await fetch('http://localhost:8000/api/v1/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `API error: ${response.status}`);
    }
    
    return await response.json();
    
  } catch (error) {
    if (error.message.includes('Failed to fetch')) {
      return {
        error: true,
        message: 'API is not running. Start server with: python -m uvicorn app.main:app --reload'
      };
    }
    
    return {
      error: true,
      message: error.message
    };
  }
}
```

---

## 🎨 CSS Styling Ideas

### Score Card

```css
.score-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  border-radius: 10px;
  text-align: center;
}

.score-card h1 {
  font-size: 4rem;
  margin: 0;
}

.score-card .strength {
  font-size: 1.5rem;
  opacity: 0.9;
}
```

### Category Progress Bar

```css
.category {
  margin: 1rem 0;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background: #eee;
  border-radius: 6px;
  overflow: hidden;
  margin: 0.5rem 0;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  transition: width 0.6s ease;
}
```

---

## 📊 Example: Complete Dashboard Component

```jsx
import React, { useState } from 'react';
import './Dashboard.css';

function LegalDashboard() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const analyze = async () => {
    if (text.length < 50) {
      setError('Text must be at least 50 characters');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      
      if (!res.ok) throw new Error('Analysis failed');
      
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="dashboard">
      <h1>Legal Argument Analyzer</h1>
      
      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder="Paste legal argument here (50-10000 chars)..."
        rows={10}
      />
      
      <button onClick={analyze} disabled={loading}>
        {loading ? 'Analyzing...' : 'Analyze'}
      </button>
      
      {error && <div className="error">{error}</div>}
      
      {result && (
        <div className="results">
          {/* Score */}
          <div className="score-card">
            <h1>{result.overall_score}/100</h1>
            <p>{result.strength_label}</p>
          </div>
          
          {/* Categories */}
          <div className="categories">
            <h2>Category Breakdown</h2>
            {result.breakdown.map((cat, i) => (
              <div key={i} className="category">
                <div className="cat-header">
                  <strong>{cat.category}</strong>
                  <span>{cat.rubric_score}/5</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress"
                    style={{ width: `${(cat.rubric_score / 5) * 100}%` }}
                  />
                </div>
                <p>{cat.rationale}</p>
              </div>
            ))}
          </div>
          
          {/* Feedback */}
          <div className="feedback">
            <h2>💡 Suggestions</h2>
            <ul>
              {result.feedback.map((tip, i) => (
                <li key={i}>{tip}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default LegalDashboard;
```

---

## ✅ Testing Checklist

- [ ] API returns status 200
- [ ] Response has all required fields
- [ ] `overall_score` is between 0-100
- [ ] `breakdown` has exactly 8 categories
- [ ] Each category has `rubric_score` 0-5
- [ ] `feedback` is a non-empty array
- [ ] Error handling works (try invalid text)
- [ ] Loading states display correctly
- [ ] Results update on new analysis

---

## 🚀 Performance Tips

1. **Debounce text input** - Don't analyze on every keystroke
2. **Cache results** - Store in localStorage for recent analyses
3. **Show loading state** - API takes 2-3 seconds
4. **Validate before sending** - Check text length (50-10000 chars)
5. **Handle errors gracefully** - Show user-friendly messages

---

## 📞 Need Help?

See [README.md](README.md) for full documentation and troubleshooting.

**Quick Debug:**
```javascript
// Test API is running:
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  .then(console.log);
```

Should return: `{ "status": "healthy", "backend": "openrouter" }`
