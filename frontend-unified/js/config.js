/* ── Global API configuration for all backends ─────────────────
   Adjust these BASE URLs if your backends run on different hosts/ports
   ─────────────────────────────────────────────────────────────── */

const CONFIG = {
  /* Flask backend — Auth + Case Similarity Search + Classifier */
  SEARCH_API: 'http://localhost:5000/api',

  /* FastAPI backend — Legal Argument Scoring (Nawanjana) */
  SCORER_API: 'http://127.0.0.1:8000',

  /* FastAPI backend — Civil Doc Extractor (Paramitha) */
  EXTRACTOR_API: 'http://127.0.0.1:8001',

  /* FastAPI backend — Compliance Auditor */
  COMPLIANCE_API: 'http://127.0.0.1:8002',

  /* Health-check paths per service */
  HEALTH: {
    search:     'http://localhost:5000/login.html',
    scorer:     'http://127.0.0.1:8000/api/v1/health',
    extractor:  'http://127.0.0.1:8001/api/v1/health',
    compliance: 'http://127.0.0.1:8002/',
  },

  /* Argument scorer limits */
  SCORER_MIN_CHARS: 50,
  SCORER_MAX_CHARS: 10000,
  SCORER_MAX_FILE:  10 * 1024 * 1024,  // 10 MB
};
