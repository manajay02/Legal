"""
FastAPI application entry point.
Civil Case Structure & Metadata Extractor API.
"""

import sys
import os

# Fix Windows pipe errors by redirecting print to stderr or suppressing
if sys.platform == 'win32':
    # Replace print with a safe version that catches pipe errors
    import builtins
    _original_print = builtins.print
    def _safe_print(*args, **kwargs):
        try:
            _original_print(*args, **kwargs)
        except OSError:
            pass  # Ignore broken pipe errors on Windows
    builtins.print = _safe_print

import pytesseract
import requests
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1.router import api_router
from app.core.config import settings

# Configure loguru to be safe on Windows
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.DEBUG else "INFO",
    catch=True  # Catch exceptions in logging
)
# Also log to file
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    catch=True
)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Extract and structure Sri Lankan Supreme Court civil case PDFs",
    debug=settings.DEBUG,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_V1_PREFIX
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Verifies that Tesseract and Ollama are accessible.
    """
    health_status = {
        "status": "healthy",
        "tesseract": "unknown",
        "ollama": "unknown"
    }
    
    # Check Tesseract
    try:
        tesseract_version = pytesseract.get_tesseract_version()
        health_status["tesseract"] = f"available (v{tesseract_version})"
    except Exception as e:
        health_status["tesseract"] = f"unavailable: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Ollama
    try:
        ollama_url = f"{settings.OLLAMA_BASE_URL}/api/tags"
        response = requests.get(ollama_url, timeout=5)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]
            
            if settings.OLLAMA_MODEL in model_names:
                health_status["ollama"] = f"available (model: {settings.OLLAMA_MODEL})"
            else:
                health_status["ollama"] = f"model '{settings.OLLAMA_MODEL}' not found"
                health_status["status"] = "degraded"
        else:
            health_status["ollama"] = f"HTTP {response.status_code}"
            health_status["status"] = "degraded"
    
    except requests.exceptions.RequestException as e:
        health_status["ollama"] = f"unreachable: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print(f"\n{'='*60}")
    print(f"🚀 {settings.PROJECT_NAME} Starting...")
    print(f"{'='*60}")
    print(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    print(f"Tesseract Language: {settings.TESSERACT_LANG}")
    
    # Show LLM configuration
    provider = settings.LLM_PROVIDER.lower()
    if provider == "openrouter":
        print(f"LLM Provider: OpenRouter (Cloud)")
        print(f"LLM Model: {settings.OPENROUTER_MODEL}")
    elif provider == "ollama":
        print(f"LLM Provider: Ollama (Local)")
        print(f"LLM Model: {settings.OLLAMA_MODEL}")
        print(f"Ollama URL: {settings.OLLAMA_BASE_URL}")
    
    print(f"Data Directory: {settings.DATA_DIR}")
    print(f"API Prefix: {settings.API_V1_PREFIX}")
    print(f"{'='*60}\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print(f"\n{'='*60}")
    print(f"🛑 {settings.PROJECT_NAME} Shutting down...")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
