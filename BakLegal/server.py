"""
BakLegal Unified Server
=======================
Serves the frontend + all 4 backends on a single port (8000).

Routes:
  /                        → frontend static files
  /similarity/api/...      → backend-M  (Similar Case Finder — Flask)
  /compliance/...          → backend-C  (Compliance Checker  — FastAPI)
  /extractor/...           → backend-P  (Case Extractor      — FastAPI)
  /argument/...            → backend-N  (Argument Scorer     — FastAPI)

Run:
  python server.py
  → http://localhost:8000
"""

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.absolute()

# ─────────────────────────────────────────────────────────────────────────────
# 1. backend-N  (Argument Scorer — FastAPI)
#    Loaded FIRST because it also uses an "app/" package (same as backend-P).
#    After importing, we clear "app.*" from sys.modules so backend-P can load
#    its own fresh "app" package without collision.
# ─────────────────────────────────────────────────────────────────────────────
_bn = str((ROOT / "backend-N").resolve())
if _bn not in sys.path:
    sys.path.insert(0, _bn)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(ROOT / "backend-N" / ".env", override=True)

from app.main import app as _argument_app  # noqa: E402  ← backend-N's app

# Clear backend-N's "app.*" so backend-P can register its own "app" package
for _k in list(sys.modules.keys()):
    if _k == "app" or _k.startswith("app."):
        del sys.modules[_k]
if _bn in sys.path:
    sys.path.remove(_bn)

# ─────────────────────────────────────────────────────────────────────────────
# 2. backend-P  (Case Extractor — FastAPI)
#    Its top-level package is "app/" — import BEFORE backend-M's "app.py" file
# ─────────────────────────────────────────────────────────────────────────────
_bp = str(ROOT / "backend-P")
if _bp not in sys.path:
    sys.path.insert(0, _bp)

load_dotenv(ROOT / "backend-P" / ".env", override=True)

from app.main import app as _extractor_app  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# 3. backend-C  (Compliance Checker — FastAPI)
#    Top-level package is "src/"
# ─────────────────────────────────────────────────────────────────────────────
_bc = str(ROOT / "backend-C")
if _bc not in sys.path:
    sys.path.insert(0, _bc)

from src.api import app as _compliance_app  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# 4. backend-M  (Similar Case Finder — Flask)
#    Loaded via importlib to avoid "app" package-name conflict with backend-P
# ─────────────────────────────────────────────────────────────────────────────
_bm = str(ROOT / "backend-M")
if _bm not in sys.path:
    sys.path.insert(0, _bm)   # required so Flask app can import similarity_search

_spec = importlib.util.spec_from_file_location(
    "_baklegal_flask_app",
    ROOT / "backend-M" / "app.py",
    submodule_search_locations=[_bm],
)
_flask_mod = importlib.util.module_from_spec(_spec)
sys.modules["_baklegal_flask_app"] = _flask_mod
_spec.loader.exec_module(_flask_mod)
_flask_app = _flask_mod.app

# ─────────────────────────────────────────────────────────────────────────────
# 5. Build main FastAPI app and mount sub-apps
# ─────────────────────────────────────────────────────────────────────────────
from fastapi import FastAPI                         # noqa: E402
from fastapi.staticfiles import StaticFiles         # noqa: E402
from starlette.middleware.wsgi import WSGIMiddleware  # noqa: E402

main_app = FastAPI(title="BakLegal Unified API", docs_url=None, redoc_url=None)

# Mounts are matched in ORDER — specific prefixes first, static catch-all last
main_app.mount("/similarity", WSGIMiddleware(_flask_app))
main_app.mount("/compliance",  _compliance_app)
main_app.mount("/extractor",   _extractor_app)
main_app.mount("/argument",    _argument_app)

# Serve the frontend (catch-all — must be registered last)
main_app.mount(
    "/",
    StaticFiles(directory=str(ROOT / "frontend"), html=True),
    name="static",
)

# ─────────────────────────────────────────────────────────────────────────────
# 6. Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("  BakLegal Unified Server")
    print("=" * 60)
    print("  Frontend      → http://localhost:8000")
    print("  Similarity    → http://localhost:8000/similarity/api")
    print("  Compliance    → http://localhost:8000/compliance")
    print("  Extractor     → http://localhost:8000/extractor/api/v1")
    print("  Argument      → http://localhost:8000/argument/api/v1")
    print("=" * 60 + "\n")
    uvicorn.run(main_app, host="0.0.0.0", port=8000, reload=False)
