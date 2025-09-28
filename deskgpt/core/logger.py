"""
Logging configuration for DeskGPT
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler
from rich.console import Console

from ..config.config import config


def setup_logging(
    level: Optional[str] = None, 
    log_file: Optional[str] = None
) -> logging.Logger:
    """Set up logging configuration with Rich formatting"""
    
    # Determine log level
    log_level = level or config.logging.level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create console for rich output
    console = Console()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create Rich console handler
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True
    )
    console_handler.setLevel(numeric_level)
    
    # Create formatter
    console_format = "%(message)s"
    console_handler.setFormatter(logging.Formatter(console_format))
    
    # Add console handler
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(numeric_level)
        
        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file_handler.setFormatter(logging.Formatter(file_format))
        
        root_logger.addHandler(file_handler)
    
    # Get application logger
    app_logger = logging.getLogger("deskgpt")
    app_logger.setLevel(numeric_level)
    
    return app_logger


class TaskLogger:
    """Specialized logger for tracking task execution"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_task_start(self, task_id: str, prompt: str) -> None:
        """Log task start"""
        self.logger.info(f"Task {task_id} started: '{prompt}'")
    
    def log_task_complete(self, task_id: str, success: bool, duration: float) -> None:
        """Log task completion"""
        status = "completed" if success else "failed"
        self.logger.info(f"Task {task_id} {status} in {duration:.2f}s")
    
    def log_action(self, action: str, details: Optional[dict] = None) -> None:
        """Log action execution"""
        if details:
            self.logger.debug(f"Action: {action} - {details}")
        else:
            self.logger.debug(f"Action: {action}")
    
    def log_error(self, context: str, error: Exception) -> None:
        """Log error with context"""
        self.logger.error(f"Error in {context}: {error}", exc_info=True)


# Initialize default logger
logger = setup_logging()
task_logger = TaskLogger(logger)