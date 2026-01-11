"""
Configuration management using pydantic-settings.
Loads environment variables and defines application settings.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Project directories
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    
    # Data directories
    DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    SAMPLE_CASES_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "sample_cases")
    UPLOADS_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "uploads")
    PROCESSED_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "processed")
    TRAINING_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "training")
    
    # Tesseract configuration
    TESSERACT_CMD: Optional[str] = Field(
        default=None,
        description="Path to tesseract executable. If None, will use system PATH."
    )
    TESSERACT_LANG: str = Field(
        default="eng+sin",
        description="Languages for OCR (e.g., 'eng+sin' for English and Sinhala)"
    )
    TESSERACT_DPI: int = Field(
        default=300,
        description="DPI for PDF to image conversion"
    )
    
    # LLM Provider: 'openrouter' (cloud API) or 'ollama' (local with trained model)
    LLM_PROVIDER: str = Field(
        default="openrouter",
        description="LLM provider: 'openrouter' (cloud) or 'ollama' (local GPU)"
    )
    
    # OpenRouter configuration (cloud API - recommended for easy setup)
    OPENROUTER_API_KEY: str = Field(
        default="",
        description="OpenRouter API key from openrouter.ai"
    )
    OPENROUTER_MODEL: str = Field(
        default="deepseek/deepseek-chat",
        description="OpenRouter model (deepseek/deepseek-chat is powerful and cheap)"
    )
    
    # Ollama configuration (local - for running trained model on GPU)
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    OLLAMA_MODEL: str = Field(
        default="civilmodel-qwen3b",
        description="Ollama model name (after importing merged model)"
    )
    
    # Common LLM settings
    LLM_TIMEOUT: int = Field(
        default=60,
        description="Timeout in seconds for LLM requests"
    )
    LLM_MAX_RETRIES: int = Field(
        default=3,
        description="Maximum retries"
    )
    
    # API configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Civil Case Structure & Metadata Extractor"
    DEBUG: bool = Field(default=False)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("DATA_DIR", "SAMPLE_CASES_DIR", "UPLOADS_DIR", "PROCESSED_DIR", "TRAINING_DIR")
    @classmethod
    def ensure_directory_exists(cls, v: Path) -> Path:
        """Ensure data directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    def get_tesseract_cmd(self) -> Optional[str]:
        """Get Tesseract command path."""
        if self.TESSERACT_CMD:
            return str(self.TESSERACT_CMD)
        return None  # Will use pytesseract default (system PATH)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Returns:
        Settings instance
    """
    return settings
