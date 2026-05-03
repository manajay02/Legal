"""
Configuration Settings
======================

Centralized configuration management using Pydantic Settings.

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
    # Inference Backend Selection
    # ============================================

    INFERENCE_BACKEND: str = Field(
        default="gemini",
        env="INFERENCE_BACKEND",
        description="Inference backend: openrouter, gemini, or ollama"
    )

    # ============================================
    # OpenRouter Configuration
    # ============================================

    OPENROUTER_API_KEY: Optional[str] = Field(
        default=None,
        env="OPENROUTER_API_KEY",
        description="OpenRouter API key"
    )

    OPENROUTER_MODEL: str = Field(
        default="deepseek/deepseek-chat",
        env="OPENROUTER_MODEL",
        description="OpenRouter model identifier"
    )

    OPENROUTER_TEMPERATURE: float = Field(
        default=0.7,
        env="OPENROUTER_TEMPERATURE",
        description="Temperature for OpenRouter generation"
    )

    OPENROUTER_MAX_TOKENS: int = Field(
        default=2048,
        env="OPENROUTER_MAX_TOKENS",
        description="Maximum tokens for OpenRouter responses"
    )

    # ============================================
    # Ollama Configuration
    # ============================================

    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        env="OLLAMA_BASE_URL",
        description="Ollama server base URL"
    )

    OLLAMA_MODEL: str = Field(
        default="legal-critic",
        env="OLLAMA_MODEL",
        description="Ollama model name"
    )

    OLLAMA_MODELS: Optional[str] = Field(
        default=None,
        env="OLLAMA_MODELS",
        description="Path to Ollama models directory"
    )

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
    # DeepSeek Configuration (Teacher Model alternative)
    # ============================================

    DEEPSEEK_API_KEY: Optional[str] = Field(
        default=None,
        env="DEEPSEEK_API_KEY",
        description="DeepSeek API key from platform.deepseek.com"
    )

    DEEPSEEK_MODEL_NAME: str = Field(
        default="deepseek-chat",
        env="DEEPSEEK_MODEL_NAME",
        description="DeepSeek model to use (deepseek-chat or deepseek-reasoner)"
    )

    DEEPSEEK_TEMPERATURE: float = Field(
        default=0.7,
        env="DEEPSEEK_TEMPERATURE",
        description="Temperature for DeepSeek generation (0.0-1.0)"
    )

    DEEPSEEK_MAX_TOKENS: int = Field(
        default=4096,
        env="DEEPSEEK_MAX_TOKENS",
        description="Maximum tokens for DeepSeek responses"
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
        extra = "ignore"


# Singleton instance
settings = Settings()
