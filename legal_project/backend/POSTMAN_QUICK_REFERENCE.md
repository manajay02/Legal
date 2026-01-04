# 🎯 Postman Quick Reference

## 📌 All Endpoints at a Glance

| # | Endpoint | Method | Purpose |
|---|----------|--------|---------|
| 1 | `/api/health` | GET | Check if server running |
| 2 | `/api/similar-cases/find` | POST | Find similar cases (YOUR ML) |
| 3 | `/api/similar-cases` | GET | List all cases |
| 4 | `/api/similar-cases/upload` | POST | Add new case to DB |
| 5 | `/api/cases/classify` | POST | Classify case type |
| 6 | `/api/cases/upload` | POST | Upload case file |
| 7 | `/api/compliance/audit` | POST | Audit compliance |
| 8 | `/api/documents/analyze` | POST | Analyze structure |
| 9 | `/api/arguments/analyze` | POST | Score argument |

---

## ⚡ Quick Start

1. Download Postman: https://www.postman.com/downloads/
2. Open Postman
3. Click **Import** → Select `Legal_Backend_API.postman_collection.json`
4. All endpoints appear in left sidebar
5. Click any endpoint and click **Send**

---

## 🧪 First Test (30 seconds)

```
1. Click: Health Check
2. Click: Send
3. See: "status": "Server is running" ✅
```

---

## 📝 Test Data (Copy & Paste)

### Employment Case:
```json
{
  "caseText": "Employment contract dispute regarding wrongful termination. Employee claims breach of contract.",
  "caseType": "Labour",
  "limit": 5
}
```

### Civil Case:
```json
{
  "caseText": "Commercial contract breach - supplier failed to deliver goods on agreed date.",
  "caseType": "Civil",
  "limit": 5
}
```

### Document for Audit:
```json
{
  "documentText": "Employment contract: 48 hours/week, LKR 50,000/month, 24-hour termination notice."
}
```

---

## 🎨 Response Colors

- 🟢 **200** (Green) = Success
- 🔵 **201** (Blue) = Created
- 🟠 **400** (Orange) = Bad Request
- 🔴 **500** (Red) = Server Error

---

## 💾 Save Your Work

After testing:
1. Right-click collection → Export
2. Save as: `my-test-results.json`
3. Share with team!

---

## ✅ Checklist

- [ ] Backend running (`npm run dev`)
- [ ] MongoDB connected
- [ ] Postman installed
- [ ] Collection imported
- [ ] Health check passes
- [ ] Can upload case
- [ ] Can find similar cases
- [ ] All 9 endpoints tested

---

**Backend URL:** http://localhost:5000
**Frontend URL:** http://localhost:3001
**Database:** MongoDB localhost:27017
