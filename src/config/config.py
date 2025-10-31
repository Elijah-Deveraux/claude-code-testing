"""
Application configuration management using Pydantic Settings.

This module provides centralized configuration management for the PDF Summarizer
application, loading settings from environment variables and .env file.
"""

from typing import List, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables or .env file.
    """

    # Google AI API Configuration
    google_api_key: str = Field(..., description="Google AI API key")

    # LLM Configuration
    llm_provider: Literal["gemini", "ollama"] = Field(
        default="gemini",
        description="LLM provider to use"
    )
    gemini_model: str = Field(
        default="gemini-1.5-flash",
        description="Gemini model name"
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    ollama_model: str = Field(
        default="llama3.2",
        description="Ollama model name"
    )

    # Embedding Configuration
    embedding_model: str = Field(
        default="models/text-embedding-004",
        description="Google embedding model"
    )
    embedding_dimension: int = Field(
        default=768,
        description="Embedding vector dimension"
    )

    # Vector Database Configuration
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_collection_name: str = Field(
        default="pdf_documents",
        description="Qdrant collection name"
    )
    qdrant_distance_metric: str = Field(
        default="cosine",
        description="Distance metric for vector similarity"
    )

    # Text Chunking Configuration
    chunk_size: int = Field(
        default=1000,
        description="Text chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks in characters"
    )

    # Retrieval Configuration
    top_k_chunks: int = Field(
        default=5,
        description="Number of chunks to retrieve"
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_key: str = Field(..., description="API key for authentication")
    api_rate_limit: int = Field(
        default=100,
        description="Rate limit (requests per minute)"
    )

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/app.log", description="Log file path")
    log_max_bytes: int = Field(
        default=10485760,
        description="Max log file size in bytes"
    )
    log_backup_count: int = Field(
        default=5,
        description="Number of backup log files"
    )

    # Frontend Configuration
    streamlit_server_port: int = Field(
        default=8501,
        description="Streamlit server port"
    )
    streamlit_server_address: str = Field(
        default="localhost",
        description="Streamlit server address"
    )

    # Summary Configuration
    brief_summary_sentences: int = Field(
        default=5,
        description="Number of sentences in brief summary"
    )
    detailed_summary_min_words: int = Field(
        default=300,
        description="Minimum words in detailed summary"
    )
    detailed_summary_max_words: int = Field(
        default=500,
        description="Maximum words in detailed summary"
    )

    # Token Tracking
    max_context_tokens: int = Field(
        default=4000,
        description="Maximum context tokens"
    )
    token_tracking_enabled: bool = Field(
        default=True,
        description="Enable token tracking"
    )

    # Cache Configuration
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )

    # Database Retry Configuration
    db_max_retries: int = Field(
        default=3,
        description="Maximum database retry attempts"
    )
    db_retry_delay: int = Field(
        default=1,
        description="Delay between retries in seconds"
    )

    # File Upload Configuration
    max_upload_size_mb: int = Field(
        default=50,
        description="Maximum file upload size in MB"
    )
    allowed_extensions: List[str] = Field(
        default=[".pdf"],
        description="Allowed file extensions"
    )

    # Development/Production Mode
    environment: Literal["development", "production"] = Field(
        default="development",
        description="Environment mode"
    )
    debug: bool = Field(default=True, description="Debug mode")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

