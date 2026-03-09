# 🎨 Legal Argument Critic - Frontend

Beautiful, modern frontend for the Legal Argument Critic API.

## 📁 Project Structure

```
frontend/
├── index.html          # Main HTML page
├── css/
│   └── style.css       # All styling
├── js/
│   ├── config.js       # API configuration
│   ├── api.js          # API service functions
│   ├── ui.js           # UI update functions
│   └── app.js          # Main application logic
└── assets/             # Images, icons (if needed)
```

## 🚀 How to Run

### Option 1: Open Directly in Browser

1. **Make sure the backend API is running** on `http://localhost:8000`
2. **Double-click** `index.html` or right-click → "Open with" → Your browser
3. Done! The UI will load and connect to your API

### Option 2: Using Live Server (Recommended for Development)

1. **Install Live Server** (VS Code extension):
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "Live Server"
   - Install it

2. **Start Live Server**:
   - Right-click on `index.html`
   - Select "Open with Live Server"
   - Browser will open automatically at `http://127.0.0.1:5500`

3. **Backend should be running** on `http://localhost:8000`

### Option 3: Using Python HTTP Server

```powershell
# Navigate to frontend folder
cd "d:\Y4S1\Research new\reserch component\Legal\frontend"

# Start simple HTTP server
python -m http.server 5500

# Open browser to: http://localhost:5500
```

## ✨ Features

### 📝 Text Analysis Tab
- Paste legal arguments directly (50-10,000 characters)
- Real-time character counter with validation
- Color-coded feedback (green = valid, red = invalid)
- Beautiful animations

### 📄 File Upload Tab
- Drag & drop support for PDF and TXT files
- File type and size validation (max 10MB)
- Visual feedback on file selection
- Hover effects and smooth transitions

### 📊 Results Display
- **Large score card** with animated progress bar
- **Strength label** (Very Weak/Weak/Moderate/Strong)
- **8 category cards** with individual scores and rationales
- **Suggestions** highlighted in yellow
- **Weak areas** highlighted in red
- **Smooth animations** on all elements

### 🎨 Design Features
- Modern gradient design (purple theme)
- Fully responsive (works on mobile, tablet, desktop)
- Smooth transitions and animations
- Hover effects on interactive elements
- Beautiful color scheme
- Professional typography

## 🔧 Configuration

Edit `js/config.js` to change settings:

```javascript
const CONFIG = {
    API_URL: 'http://localhost:8000',  // Change if API is on different URL
    ENDPOINTS: {
        ANALYZE: '/api/v1/analyze',
        UPLOAD: '/api/v1/upload',
        HEALTH: '/api/v1/health'
    },
    MAX_TEXT_LENGTH: 10000,
    MIN_TEXT_LENGTH: 50,
    MAX_FILE_SIZE: 10 * 1024 * 1024 // 10MB
};
```

## 🎯 Quick Test

1. **Start Backend API**:
   ```powershell
   cd "d:\Y4S1\Research new\reserch component\Legal\backend"
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
   .\.venv\Scripts\Activate.ps1
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Open Frontend**:
   - Double-click `index.html`
   - Check if status shows "✓ API Online" (green)

3. **Test with Sample Text**:
   ```
   The appellant challenges the District Court's decision on grounds of procedural irregularity. The lower court failed to consider Section 91 of the Civil Procedure Code which mandates proper notice to all parties. On July 15, 2023, the respondent filed an ex parte motion without providing adequate notice to the appellant as required under Section 91(1). This constitutes a fundamental breach of natural justice. The Court of Appeal in Silva v. Fernando [2019] 2 SLR 145 held that failure to provide notice renders proceedings void ab initio. We respectfully submit that the impugned order should be set aside and the matter remitted for proper hearing with notice.
   ```

4. **Click "Analyze Argument"** and wait for results!

## 🐛 Troubleshooting

### ❌ "API Offline" Status

**Problem**: Red status showing "API Offline"

**Solution**:
1. Make sure backend server is running on port 8000
2. Open browser to http://localhost:8000 - should see JSON response
3. Check browser console (F12) for CORS errors
4. Make sure backend has CORS enabled (it should by default)

### ❌ "Connection Refused" Error

**Problem**: Analysis fails with connection error

**Solution**:
1. Verify backend is running: http://localhost:8000/docs
2. Check firewall isn't blocking port 8000
3. Try using 127.0.0.1 instead of localhost in config.js

### ❌ File Upload Not Working

**Problem**: File upload button stays disabled

**Solution**:
1. Check file type is .pdf or .txt
2. Check file size is under 10MB
3. Try selecting file again
4. Check browser console (F12) for errors

### ❌ Results Not Displaying

**Problem**: Analysis completes but no results show

**Solution**:
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify API response format
4. Clear browser cache (Ctrl+Shift+Delete)

## 📱 Mobile Support

The UI is fully responsive and works on:
- ✅ Desktop (1200px+)
- ✅ Tablet (768px - 1199px)
- ✅ Mobile (320px - 767px)

## 🎨 Customization

### Change Color Theme

Edit `css/style.css`:

```css
/* Change gradient colors */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Change to different colors */
background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%); /* Blue */
background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); /* Pink */
background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); /* Cyan */
```

### Change Fonts

Edit `css/style.css`:

```css
body {
    font-family: 'Your Font', sans-serif;
}
```

## 🌐 Deployment

### Deploy to GitHub Pages

1. Create a GitHub repository
2. Push frontend folder
3. Enable GitHub Pages in repository settings
4. Update API_URL in config.js to your backend URL

### Deploy with Backend

Place frontend in backend's static folder and serve with FastAPI:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

## 📄 License

MIT License

## 👥 Support

If you encounter issues:
1. Check browser console (F12)
2. Check backend logs
3. Verify API is running
4. Review configuration in config.js

---

**Enjoy using Legal Argument Critic! 🏛️✨**
