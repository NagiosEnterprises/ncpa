"""
Unified logging system for NCPA build framework.

Provides structured logging with multiple output formats and destinations.
"""

import logging
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, TextIO
from datetime import datetime


class LogLevel(Enum):
    """Logging levels enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class BuildFormatter(logging.Formatter):
    """Custom formatter for build logs with colored output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'RESET': '\033[0m'      # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors and sys.stderr.isatty()
        super().__init__()
    
    def format(self, record):
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Format level with optional color
        level = record.levelname
        if self.use_colors and level in self.COLORS:
            level = f"{self.COLORS[level]}{level}{self.COLORS['RESET']}"
        
        # Build log message
        if record.name == 'root':
            name = 'BUILD'
        else:
            name = record.name.upper()
            
        message = f"[{timestamp}] [{level:>7}] [{name:>12}] {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            message += '\n' + self.formatException(record.exc_info)
            
        return message


class Logger:
    """
    Unified logging system for NCPA builds
    
    Provides structured logging with file and console output, proper
    formatting, and integration with the build system's error handling.
    """
    
    def __init__(self, 
                 name: str = "ncpa_build",
                 level: LogLevel = LogLevel.INFO,
                 log_file: Optional[Path] = None,
                 console_output: bool = True,
                 use_colors: bool = True):
        """
        Initialize logger
        
        Args:
            name: Logger name
            level: Minimum logging level
            log_file: Optional file to write logs to
            console_output: Whether to output to console
            use_colors: Whether to use colored console output
        """
        self.name = name
        self.level = level
        self.log_file = log_file
        self.console_output = console_output
        self.use_colors = use_colors
        
        # Set up Python logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.value))
        
        # Clear any existing handlers
        self._logger.handlers.clear()
        
        # Set up console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(BuildFormatter(use_colors))
            self._logger.addHandler(console_handler)
        
        # Set up file handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setFormatter(BuildFormatter(use_colors=False))
            self._logger.addHandler(file_handler)
        
        # Track build progress
        self.start_time = datetime.now()
        self.step_count = 0
        
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._logger.debug(message, **kwargs)
        
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._logger.info(message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._logger.warning(message, **kwargs)
        
    def error(self, message: str, **kwargs):
        """Log error message"""
        self._logger.error(message, **kwargs)
        
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self._logger.exception(message, **kwargs)
        
    def step(self, message: str):
        """Log a build step with progress indication"""
        self.step_count += 1
        elapsed = datetime.now() - self.start_time
        elapsed_str = f"{elapsed.total_seconds():.1f}s"
        step_msg = f"[Step {self.step_count:2d}] [{elapsed_str:>6}] {message}"
        self.info(step_msg)
        
    def success(self, message: str):
        """Log success message with emphasis"""
        self.info(f"✓ {message}")
        
    def failure(self, message: str):
        """Log failure message with emphasis"""
        self.error(f"✗ {message}")
        
    def section(self, title: str):
        """Log a section header"""
        separator = "=" * min(60, len(title) + 20)
        self.info("")
        self.info(separator)
        self.info(f"  {title}")
        self.info(separator)
        
    def subsection(self, title: str):
        """Log a subsection header"""
        self.info(f"\n--- {title} ---")
        
    def create_child(self, name: str) -> 'Logger':
        """Create a child logger with a specific name"""
        child_name = f"{self.name}.{name}"
        return Logger(
            name=child_name,
            level=self.level,
            log_file=self.log_file,
            console_output=False,  # Avoid duplicate console output
            use_colors=self.use_colors
        )
        
    def set_level(self, level: LogLevel):
        """Change logging level"""
        self.level = level
        self._logger.setLevel(getattr(logging, level.value))
        
    def get_elapsed_time(self) -> float:
        """Get elapsed time since logger creation in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
