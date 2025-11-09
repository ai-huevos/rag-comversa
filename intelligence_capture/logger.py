#!/usr/bin/env python3
"""
Structured Logging Framework for Knowledge Graph Consolidation

Provides centralized logging configuration with:
- Rotating file handlers (10MB max, 5 backups)
- Color-coded console output
- Structured log format with timestamps
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)

Usage:
    from intelligence_capture.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("Entity consolidated successfully")
    logger.warning("Low confidence score detected")
    logger.error("API call failed")
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

# Try to import colorlog for colored console output
try:
    import colorlog
    HAVE_COLORLOG = True
except ImportError:
    HAVE_COLORLOG = False


# Global logger registry to avoid duplicate handlers
_loggers = {}


def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger with structured logging configuration
    
    Args:
        name: Logger name (typically __name__ of the module)
        log_level: Optional log level override (DEBUG, INFO, WARNING, ERROR)
                  Defaults to INFO
    
    Returns:
        Configured logger instance
    """
    # Return existing logger if already configured
    if name in _loggers:
        return _loggers[name]
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Set log level
    level = getattr(logging, log_level.upper()) if log_level else logging.INFO
    logger.setLevel(level)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    # Only add handlers if logger doesn't have any
    if not logger.handlers:
        # Add file handler
        file_handler = _create_file_handler()
        logger.addHandler(file_handler)
        
        # Add console handler
        console_handler = _create_console_handler()
        logger.addHandler(console_handler)
    
    # Register logger
    _loggers[name] = logger
    
    return logger


def _create_file_handler() -> logging.Handler:
    """
    Create rotating file handler for logs
    
    Returns:
        Configured rotating file handler
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create rotating file handler
    # 10MB max size, 5 backup files
    handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "consolidation.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Set format
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    return handler


def _create_console_handler() -> logging.Handler:
    """
    Create console handler with color-coded output
    
    Returns:
        Configured console handler
    """
    handler = logging.StreamHandler()
    
    # Use colorlog if available, otherwise standard formatter
    if HAVE_COLORLOG:
        formatter = colorlog.ColoredFormatter(
            fmt='%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    
    return handler


def configure_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Configure global logging settings
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional custom log file path
    """
    # Set root logger level
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    # If custom log file specified, update file handler
    if log_file:
        # Remove existing file handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                root_logger.removeHandler(handler)
        
        # Add new file handler
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        root_logger.addHandler(handler)


# Example usage
if __name__ == "__main__":
    # Test logging at different levels
    logger = get_logger(__name__)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("\nLog file created at: logs/consolidation.log")
