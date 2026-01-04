# Legal Backend - Setup Guide

## 📁 Backend Structure

```
backend/
├── server.js                 # Main Express server
├── package.json             # Dependencies
├── .env                     # Environment variables
├── models/
│   └── Case.js             # MongoDB Case schema
├── routes/
│   ├── caseRoutes.js       # General case endpoints
│   ├── similarCasesRoutes.js  # Similar cases finder
│   ├── complianceRoutes.js    # Compliance auditor
│   ├── documentRoutes.js      # Document analyzer
│   └── argumentRoutes.js      # Argument analyzer
└── middleware/              # (To be added)
```

## 🚀 Quick Start

### Step 1: Install MongoDB
Download and install MongoDB Community Edition:
- **Windows**: https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/
- **Mac**: `brew tap mongodb/brew && brew install mongodb-community`
- **Linux**: Follow official MongoDB docs

### Step 2: Install Dependencies
```bash
cd backend
npm install
```

### Step 3: Configure Environment
Edit `.env`:
```
MONGODB_URI=mongodb://localhost:27017/legal-database
PORT=5000
NODE_ENV=development
JWT_SECRET=your_jwt_secret_key
FRONTEND_URL=http://localhost:3001
```

### Step 4: Start MongoDB
**Windows (Command Prompt as Admin):**
```bash
mongod
```

**Mac/Linux:**
```bash
brew services start mongodb-community
```

### Step 5: Start Backend Server
```bash
npm run dev
```

Expected output:
```
✅ MongoDB connected successfully
🚀 Backend server running on http://localhost:5000
```

## 📚 API Endpoints

### Similar Cases Finder
```
POST /api/similar-cases/find
- Body: { caseText, caseType, limit }
- Returns: Similar cases with similarity scores

GET /api/similar-cases
- Query: caseType, page, limit
- Returns: Paginated cases list

POST /api/similar-cases/upload
- Body: { caseText, title, caseType, court, year }
- Returns: Saved case with ID
```

### Case Management
```
POST /api/cases/classify
- Body: { caseText }
- Returns: Case classification

POST /api/cases/upload
- Body: { caseFile }
- Returns: Uploaded case info
```

### Compliance Audit
```
POST /api/compliance/audit
- Body: { documentText }
- Returns: Compliance score & violations
```

### Document Analysis
```
POST /api/documents/analyze
- Body: { documentText }
- Returns: Document structure analysis
```

### Argument Analysis
```
POST /api/arguments/analyze
- Body: { argumentText }
- Returns: Argument strength score
```

## 🗄️ Database Schema

### Case Collection
```javascript
{
  caseId: String,           // Unique identifier
  title: String,            // Case title
  caseType: String,         // Civil, Criminal, Labour, etc.
  court: String,            // Court name
  year: Number,             // Year decided
  outcome: String,          // Won, Lost, Settled, etc.
  summary: String,          // Case summary
  fullText: String,         // Complete case text
  relevantLaws: [String],   // Applicable laws
  citedCases: [String],     // Referenced cases
  keyPoints: [String],      // Important points
  tags: [String],           // Search tags
  uploadedAt: Date,         // Upload timestamp
  updatedAt: Date           // Last update
}
```

## ✅ Health Check
```
GET http://localhost:5000/api/health

Response:
{
  "status": "Server is running",
  "timestamp": "2024-01-03T10:00:00.000Z",
  "environment": "development"
}
```

## 🔄 Database Operations

### Insert Sample Data (MongoDB Shell)
```javascript
db.cases.insertOne({
  caseId: "case_001",
  title: "Smith v. Jones",
  caseType: "Civil",
  court: "District Court",
  year: 2023,
  outcome: "Won",
  summary: "Contract dispute over service delivery",
  fullText: "Full case text here...",
  relevantLaws: ["Contract Act", "Sale of Goods Act"],
  citedCases: ["Case A v Case B"],
  keyPoints: ["Breach of contract", "Damages awarded"],
  uploadedAt: new Date()
})
```

### Query Examples
```javascript
// Find all civil cases
db.cases.find({ caseType: "Civil" })

// Text search
db.cases.find({ $text: { $search: "contract" } })

// Find by year
db.cases.find({ year: { $gte: 2020 } })
```

## 🐛 Troubleshooting

### MongoDB Won't Connect
- Ensure MongoDB service is running: `mongod`
- Check connection string in .env
- Verify port 27017 is accessible

### Port 5000 Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -i :5000
kill -9 <PID>
```

### API Returns 500 Error
- Check server logs for error message
- Ensure MongoDB is connected
- Verify request body format

## 📝 Next Steps

1. **Add Authentication**: JWT middleware for protected routes
2. **File Upload**: Multer integration for PDF uploads
3. **ML Integration**: Connect trained model for classification
4. **Database Seeding**: Add sample cases to database
5. **Error Handling**: Comprehensive error middleware
6. **Validation**: Input validation for all endpoints

## 🔗 Frontend Integration

Frontend is already configured to use this backend at `http://localhost:5000` via the proxy in `package.json`

To test: Visit http://localhost:3001 - All API calls will forward to backend.
