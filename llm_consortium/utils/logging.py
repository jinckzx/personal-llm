import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

def configure_logging(
    name: str = "llm_consortium",
    log_dir: str = "logs",
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure and return a logger with both file and console handlers.
    
    Args:
        name (str): Logger name.
        log_dir (str): Directory to store log files.
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        max_bytes (int): Max log file size before rotation.
        backup_count (int): Number of backup logs to keep.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Determine logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate log handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Log format
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
    formatter = logging.Formatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")
    
    # File handler with rotation
    log_file = os.path.join(log_dir, "consortium.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name (str, optional): Logger name. Defaults to "llm_consortium".
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name or "llm_consortium")

# Initialize and configure the default logger when the module is imported
logger = configure_logging()
