"""
Enhanced logging utilities with timestamp support and file logging
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class EnhancedLogger:
    """Enhanced logging with timestamp support and file logging to experiment directories"""
    
    def __init__(self):
        self.loggers = {}
        self.file_handlers = {}
    
    def setup_logging(self, output_dir: Optional[str] = None, 
                     log_level: int = logging.INFO) -> None:
        """
        Setup enhanced logging with timestamp format and optional file logging
        
        Args:
            output_dir: Directory to save log files (if None, only console logging)
            log_level: Logging level (default: INFO)
        """
        # Remove any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create formatter with timestamp
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        
        root_logger.addHandler(console_handler)
        root_logger.setLevel(log_level)
        
        # File handler if output directory is provided
        if output_dir:
            self._setup_file_logging(output_dir, formatter, log_level)
    
    def _setup_file_logging(self, output_dir: str, formatter: logging.Formatter, 
                           log_level: int) -> None:
        """Setup file logging to experiment directory"""
        log_dir = Path(output_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"generation_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        
        # Store reference to file handler
        self.file_handlers[str(log_dir)] = file_handler
        
        logging.info(f"Log file created: {log_file}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]
    
    def close_file_handlers(self) -> None:
        """Close all file handlers"""
        for handler in self.file_handlers.values():
            handler.close()
        self.file_handlers.clear()


# Global logger instance
_logger_instance = EnhancedLogger()


def setup_logging(output_dir: Optional[str] = None, log_level: int = logging.INFO) -> None:
    """Setup enhanced logging system"""
    _logger_instance.setup_logging(output_dir, log_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with enhanced formatting"""
    return _logger_instance.get_logger(name)


def close_logging() -> None:
    """Close all logging handlers"""
    _logger_instance.close_file_handlers()


def log_generation_stats(start_time: datetime, total_functions: int, 
                        successful: int, failed: int) -> None:
    """Log generation statistics with timing information"""
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger = get_logger(__name__)
    
    logger.info("=== Generation Statistics ===")
    logger.info(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Total Functions: {total_functions}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {(successful/total_functions*100):.1f}%")
    
    if duration > 0:
        rate = total_functions / duration
        logger.info(f"Generation Rate: {rate:.2f} functions/second")
    
    logger.info("============================")