"""
Logging configuration for PDF Summarizer application.

This module sets up comprehensive logging with multiple handlers:
- Console handler for INFO and above
- File handler for all levels
- JSON formatting for structured logging
- Rotating file handler to manage log file size
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from pythonjsonlogger import jsonlogger


class LoggingConfig:
    """
    Configure application-wide logging with console and file handlers.

    Attributes:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """

    def __init__(
        self,
        log_level: str = "INFO",
        log_file: str = "logs/app.log",
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
    ) -> None:
        """
        Initialize logging configuration.

        Args:
            log_level: Logging level (default: INFO)
            log_file: Path to log file (default: logs/app.log)
            max_bytes: Maximum log file size in bytes (default: 10MB)
            backup_count: Number of backup files to keep (default: 5)
        """
        self.log_level = getattr(logging, log_level.upper())
        self.log_file = log_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        # Create logs directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

    def setup_logging(self) -> logging.Logger:
        """
        Set up application logging with console and file handlers.

        Returns:
            Configured root logger instance
        """
        # Get root logger
        logger = logging.getLogger()
        logger.setLevel(self.log_level)

        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()

        # Console handler - human-readable format
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler - JSON format for structured logging
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        json_formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)

        logger.info("Logging configuration initialized")
        return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Name of the logger (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    return logging.getLogger(name)


def configure_logging_from_env() -> logging.Logger:
    """
    Configure logging using environment variables.

    Environment variables:
        LOG_LEVEL: Logging level (default: INFO)
        LOG_FILE: Path to log file (default: logs/app.log)
        LOG_MAX_BYTES: Max file size (default: 10485760)
        LOG_BACKUP_COUNT: Number of backups (default: 5)

    Returns:
        Configured root logger instance
    """
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "logs/app.log")
    max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    config = LoggingConfig(
        log_level=log_level,
        log_file=log_file,
        max_bytes=max_bytes,
        backup_count=backup_count
    )

    return config.setup_logging()
