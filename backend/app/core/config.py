"""
Configuration Settings
======================

Centralized configuration management using Pydantic Settings.

Author: LegalScoreModel Team
Date: January 2026
"""

import os
from typing import Optional
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application configuration settings.
    """
    
    # ============================================
    # API Configuration
    # ============================================
    
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_RELOAD: bool = Field(default=True, env="API_RELOAD")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    API_TITLE: str = "Legal Argument Critic API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Civil Case Legal Argument Scoring System for Sri Lanka"
    
    # ============================================
    # Google AI Configuration (Teacher Model)
    # ============================================
    
    GOOGLE_API_KEY: Optional[str] = Field(
        default=None,
        env="GOOGLE_API_KEY",
        description="Google AI Studio API key for Gemini models"
    )
    
    GEMINI_MODEL_NAME: str = Field(
        default="gemini-2.5-flash",
        env="GEMINI_MODEL_NAME",
        description="Gemini model to use for training data generation"
    )
    
    GEMINI_TEMPERATURE: float = Field(
        default=0.7,
        env="GEMINI_TEMPERATURE",
        description="Temperature for Gemini generation (0.0-1.0)"
    )
    
    GEMINI_MAX_TOKENS: int = Field(
        default=2048,
        env="GEMINI_MAX_TOKENS",
        description="Maximum tokens for Gemini responses"
    )
    
    # ============================================
    # Tesseract OCR Configuration
    # ============================================
    
    TESSERACT_CMD: Optional[str] = Field(
        default=r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        env="TESSERACT_CMD",
        description="Path to Tesseract executable"
    )
    
    OCR_LANGUAGE: str = Field(
        default="sin+eng",
        env="OCR_LANGUAGE",
        description="OCR language codes (Sinhala + English)"
    )
    
    OCR_DPI: int = Field(
        default=300,
        env="OCR_DPI",
        description="DPI for PDF to image conversion"
    )
    
    # ============================================
    # Database Configuration
    # ============================================
    
    DATABASE_URL: str = Field(
        default="sqlite:///./legal_score.db",
        env="DATABASE_URL",
        description="Database connection URL"
    )
    
    # ============================================
    # Logging Configuration
    # ============================================
    
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    LOG_DIR: Path = Field(
        default=Path("logs"),
        env="LOG_DIR",
        description="Directory for log files"
    )
    
    # ============================================
    # Model Paths
    # ============================================
    
    BASE_MODEL_PATH: Path = Field(
        default=Path("models/base"),
        env="BASE_MODEL_PATH",
        description="Path to base model cache"
    )
    
    FINE_TUNED_MODEL_PATH: Path = Field(
        default=Path("models/fine_tuned/adapter_model"),
        env="FINE_TUNED_MODEL_PATH",
        description="Path to fine-tuned LoRA adapter"
    )
    
    # ============================================
    # CORS Configuration
    # ============================================
    
    CORS_ORIGINS: list = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
settings = Settings()
