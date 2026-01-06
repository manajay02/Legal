"""
Legal Argument Critic API
==========================

FastAPI application for scoring and critiquing legal arguments
using a fine-tuned Qwen2.5-3B-Instruct model.

Author: LegalScoreModel Team
Date: January 2026
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.api.v1 import analyze
from app.services.inference_service import get_inference_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Loads the model on startup and cleans up on shutdown.
    """
    # Startup: Load the fine-tuned model
    print("=" * 60)
    print("Starting Legal Argument Critic API")
    print("=" * 60)
    
    try:
        # Initialize the inference service (loads the model)
        inference_service = get_inference_service()
        print("✓ Model loaded and ready for inference")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        print("⚠ API will start but /analyze endpoint will fail")
    
    yield
    
    # Shutdown
    print("\nShutting down...")


# Create FastAPI app
app = FastAPI(
    title="Legal Argument Critic API",
    description="AI-powered legal argument scoring system for Sri Lankan civil cases",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    analyze.router,
    prefix="/api/v1",
    tags=["Analysis"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Legal Argument Critic API",
        "version": "1.0.0",
        "description": "AI-powered legal argument scoring system for Sri Lankan civil cases",
        "endpoints": {
            "analyze": "POST /api/v1/analyze - Analyze text directly",
            "upload": "POST /api/v1/upload - Upload PDF/TXT file for analysis",
            "health": "GET /api/v1/health - Check service health",
            "docs": "GET /docs - Interactive API documentation"
        }
    }


@app.get("/health")
async def health():
    """Basic application health check."""
    return {
        "status": "ok",
        "message": "API is running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
