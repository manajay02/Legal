# 🚀 How to Test Your New UI

## Starting the Flask Application

### Option 1: Using Terminal (Recommended)

1. Open a terminal and navigate to the project directory:
   ```powershell
   cd "d:\research comoponent\Legal\legal_nli_project"
   ```

2. Activate the virtual environment (if not already activated):
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. Run the Flask app:
   ```powershell
   python app.py
   ```

4. Open your browser and go to:
   ```
   http://localhost:5000
   ```

### Option 2: Using VS Code Run Configuration

1. Open the VS Code terminal (Ctrl + `)
2. Run: `python app.py`
3. Click the link or navigate to `http://localhost:5000`

---

## Testing the UI

### Upload Page Features to Test:

✅ **Visual Elements**
- [ ] Navbar appears at the top with branding
- [ ] Header displays properly with description
- [ ] Upload card is centered and styled nicely
- [ ] File input area has dashed border
- [ ] "Choose or Drag & Drop File" label is visible

✅ **Interactive Features**
- [ ] Hover over upload area - border color changes
- [ ] Click on upload area to open file browser
- [ ] Select a file - filename appears below
- [ ] Drag and drop a file - it gets selected
- [ ] Hover over "Analyze Document" button - color changes

✅ **Responsive Design**
- [ ] Test on mobile screen size (resize browser to ~375px width)
- [ ] Elements should stack and resize properly
- [ ] Text should remain readable

### Results Page Features to Test:

✅ **Visual Elements**
- [ ] Navbar visible with navigation
- [ ] Domain badge shows document type
- [ ] Results display in cards
- [ ] Color coding works (Red/Green/Yellow based on status)
- [ ] Status badges show correct icons

✅ **Result Card Content**
- [ ] Clause text displays in white box
- [ ] Confidence score shown with percentage
- [ ] Progress bar fills based on confidence
- [ ] Law reference displays
- [ ] Explanation text is readable
- [ ] Status badge shows correct color

✅ **Summary Section**
- [ ] Shows total clauses analyzed
- [ ] Shows count of compliant clauses
- [ ] Shows count of non-compliant clauses
- [ ] Shows count of clauses needing review
- [ ] Numbers are accurate

✅ **Navigation**
- [ ] "Analyze Another Document" button works
- [ ] Back link at top works
- [ ] Buttons have hover effects

### Browser Compatibility:

Test in:
- [ ] Chrome/Edge (Latest)
- [ ] Firefox
- [ ] Safari (if available)
- [ ] Mobile browser

### Performance:

- [ ] Page loads quickly
- [ ] No layout shifts
- [ ] Smooth animations
- [ ] Responsive to interactions

---

## Sample Test Document

To test the interface, use:
- Any PDF file with legal content
- Any .txt file with contract clauses
- Any .docx file with agreement text

---

## Troubleshooting

**Port 5000 already in use?**
```powershell
# Change port in app.py:
app.run(debug=True, port=5001)
```

**CSS not loading?**
- Make sure you're in the correct directory
- Check that `static/style.css` exists
- Refresh browser (Ctrl+Shift+Delete to clear cache)

**HTML rendering issues?**
- Check browser console for errors (F12)
- Verify all template syntax is correct
- Check that Flask is serving templates correctly

---

## 🎉 Success Indicators

✅ Clean, professional appearance
✅ Smooth animations and transitions
✅ Color-coded compliance status
✅ Easy navigation between pages
✅ Responsive on all screen sizes
✅ Clear information hierarchy
✅ Professional footer with security message

---

## Next Steps

After testing:
1. ✅ Deploy to production server
2. ✅ Set up SSL/HTTPS for security
3. ✅ Monitor user feedback
4. ✅ Consider additional features (export results, history, etc.)

Enjoy your new professional interface! 🚀
