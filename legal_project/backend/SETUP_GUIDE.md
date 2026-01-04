# ✅ Complete Backend Setup Guide

## 📊 Development Order (Best Practice)

**Backend First → Database Connection → Data Integration**

This is what I've created for you:

1. ✅ **Backend Structure** (Express.js server) - DONE
2. ✅ **Database Models** (MongoDB schemas) - DONE  
3. ✅ **API Routes** (All endpoints) - DONE
4. 🔜 **MongoDB Setup** (Local or Cloud)

---

## 🚀 Installation Steps (Windows)

### Step 1: Install MongoDB Community Edition
1. Download: https://www.mongodb.com/try/download/community
2. Run the installer
3. Choose "Install as a Service" (recommended)
4. Click "Install"
5. **Verify installation**: Open Command Prompt and run:
   ```bash
   mongod --version
   ```
   You should see the version number

### Step 2: Start MongoDB Service
**Option A: Auto-start (if installed as service)**
- MongoDB starts automatically when Windows boots

**Option B: Manual start**
- Open Command Prompt as **Administrator**
- Run: `mongod`
- You should see: `waiting for connections on port 27017`
- Keep this window open!

### Step 3: Setup Backend

**Navigate to backend folder:**
```bash
cd c:\Users\Maneth\Documents\GitHub\Legal\legal_project\backend
```

**Option A: Quick Setup (Recommended for Windows)**
```bash
setup.bat
```
This will automatically:
- Install npm dependencies
- Create .env file
- Show you next steps

**Option B: Manual Setup**
```bash
# Install dependencies
npm install

# Create .env (copy from template if not exists)
# Check .env file has correct MongoDB URI

# Start server
npm run dev
```

### Step 4: Verify Backend is Running
Visit: http://localhost:5000/api/health

You should see:
```json
{
  "status": "Server is running",
  "timestamp": "2024-01-03T10:00:00.000Z",
  "environment": "development"
}
```

---

## 📁 Backend Structure Explained

```
backend/
├── server.js                      # Main server (Express + MongoDB)
├── package.json                   # Dependencies
├── .env                          # Configuration
├── BACKEND_README.md             # API documentation
│
├── models/
│   └── Case.js                   # Database schema for cases
│
└── routes/
    ├── similarCasesRoutes.js     # Your ML model endpoint
    ├── caseRoutes.js             # General case operations
    ├── complianceRoutes.js        # Compliance auditor
    ├── documentRoutes.js          # Document analyzer
    └── argumentRoutes.js          # Argument analyzer
```

---

## 🗄️ Database Structure

### MongoDB Collection: `cases`

Each case stored with:
- `caseId` - Unique identifier
- `title` - Case name
- `caseType` - Civil, Criminal, Labour, etc.
- `court` - Court name
- `year` - Year decided
- `summary` - Quick summary
- `fullText` - Complete text (for ML)
- `relevantLaws` - Applicable laws
- `keyPoints` - Important points
- `uploadedAt` - When added

---

## 🤖 Similar Cases Component Integration

Your frontend at `http://localhost:3001` will now:

1. **Upload Case PDF** → Sends to `POST /api/similar-cases/upload`
2. **Find Similar Cases** → Sends to `POST /api/similar-cases/find`
3. **Get Results** → Receives ranked cases with similarity scores

### API Endpoint for Similar Cases:

```
POST http://localhost:5000/api/similar-cases/find
Content-Type: application/json

{
  "caseText": "Employment contract dispute...",
  "caseType": "Labour",
  "limit": 5
}

Response:
{
  "found": 5,
  "highestMatch": 92.5,
  "averageMatch": 85.3,
  "results": [
    {
      "_id": "...",
      "caseId": "case_001",
      "title": "Smith v. Jones",
      "similarityScore": 92.5,
      "relevantPoints": ["Breach of contract", ...],
      "matchType": "Exact Match"
    },
    ...
  ]
}
```

---

## ✨ Next: Adding Sample Data to Database

### Option 1: Using MongoDB Compass (GUI)
1. Download: https://www.mongodb.com/products/tools/compass
2. Connect to: `mongodb://localhost:27017`
3. Create database: `legal-database`
4. Create collection: `cases`
5. Insert sample documents manually

### Option 2: Using MongoDB Shell
Open Command Prompt and run:
```bash
mongosh
```

Then insert data:
```javascript
use legal-database

db.cases.insertMany([
  {
    caseId: "case_001",
    title: "Smith v. Jones - Employment Dispute",
    caseType: "Labour",
    court: "District Court",
    year: 2023,
    outcome: "Won",
    summary: "Employment contract dispute regarding termination",
    fullText: "Full case details here...",
    relevantLaws: ["Industrial Disputes Act"],
    citedCases: [],
    keyPoints: ["Unfair dismissal", "Compensation awarded"],
    uploadedAt: new Date()
  },
  {
    caseId: "case_002",
    title: "ABC Corp v. XYZ Ltd - Contract Breach",
    caseType: "Civil",
    court: "High Court",
    year: 2023,
    outcome: "Settled",
    summary: "Contract breach case",
    fullText: "Full case details here...",
    relevantLaws: ["Contract Act"],
    citedCases: [],
    keyPoints: ["Breach of contract", "Damages"],
    uploadedAt: new Date()
  }
])

// Verify inserted
db.cases.find().pretty()
```

---

## 🔄 How Everything Works Together

```
┌─────────────────────────────────────────────────────┐
│         Your React Frontend (port 3001)              │
│  • Similar Cases Component                           │
│  • Compliance Auditor                                │
│  • Document Analyzer                                 │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP Requests
                   ↓
┌─────────────────────────────────────────────────────┐
│        Backend Express Server (port 5000)            │
│  • /api/similar-cases/find ← Your ML endpoint        │
│  • /api/compliance/audit                             │
│  • /api/documents/analyze                            │
└──────────────────┬──────────────────────────────────┘
                   │ CRUD Operations
                   ↓
┌─────────────────────────────────────────────────────┐
│     MongoDB Database (port 27017)                    │
│  • cases collection (stores all legal cases)         │
│  • Indexed for fast search                           │
└─────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Commands

```bash
# Start MongoDB (Windows - Admin Command Prompt)
mongod

# Start MongoDB shell (new window)
mongosh

# Start backend server
npm run dev

# Install new packages
npm install <package-name>

# Check if backend is running
curl http://localhost:5000/api/health

# View running processes
netstat -ano
```

---

## 🐛 Troubleshooting

### MongoDB Won't Connect
```
❌ Error: connect ECONNREFUSED 127.0.0.1:27017

✅ Solution:
1. Open Command Prompt as Administrator
2. Run: mongod
3. Keep window open
4. Restart backend: npm run dev
```

### "Port 5000 Already in Use"
```
❌ Error: listen EADDRINUSE: address already in use :::5000

✅ Solution:
1. Find process: netstat -ano | findstr :5000
2. Kill it: taskkill /PID <PID> /F
3. Restart: npm run dev
```

### Cannot Find Database After Restart
```
✅ MongoDB data is saved in:
Windows: C:\Program Files\MongoDB\Server\<version>\data

Your data persists even after restart
```

---

## 📈 Production Checklist

Before deploying to production:

- [ ] Change `JWT_SECRET` in .env
- [ ] Use MongoDB Atlas (cloud) instead of local
- [ ] Set `NODE_ENV=production`
- [ ] Add proper error handling
- [ ] Add authentication to routes
- [ ] Add rate limiting
- [ ] Test all API endpoints
- [ ] Add HTTPS/SSL certificate
- [ ] Setup proper CORS
- [ ] Add input validation
- [ ] Setup monitoring/logging

---

## 📞 Support

If you need help:
1. Check BACKEND_README.md for API details
2. Check server.js logs for errors
3. Verify MongoDB is running
4. Check .env configuration
5. Test with curl or Postman

---

**You're all set! Your backend is ready to work with your Similar Cases component.** 🎉
