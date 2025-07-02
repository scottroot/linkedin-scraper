import logging
import os
from datetime import datetime
from functools import wraps
import inspect

# Configure logging format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def get_log_level():
    """Get the current log level based on DEBUG environment variable"""
    if os.getenv('DEBUG', '').lower() in ('true', '1', 'yes', 'on'):
        return logging.DEBUG
    else:
        return logging.INFO

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Global variable to store the current session log file
_current_session_log_file = None

def get_session_log_file():
    """Get the current session log file path"""
    global _current_session_log_file
    if _current_session_log_file is None:
        # Create a unique log file for this session with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _current_session_log_file = os.path.join(logs_dir, f'linkedin_scraper_{timestamp}.log')
    return _current_session_log_file

def reset_session_log_file():
    """Reset the session log file to create a new one for the next run"""
    global _current_session_log_file
    _current_session_log_file = None

    # Clear all existing loggers to force them to recreate with new handlers
    for logger_name in logging.root.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()

def get_handlers():
    """Get configured handlers with current log level"""
    log_level = get_log_level()

    # Configure file handler with session-specific filename
    log_file = get_session_log_file()
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    return file_handler, console_handler


class Logger:
    """
    A wrapper class for Python's logging module that provides a simple interface
    with automatic module name detection and consistent formatting.
    """

    def __init__(self, name=None):
        """
        Initialize a logger instance.

        Args:
            name: Optional logger name. If None, uses the calling module's name.
        """
        if name is None:
            # Get the calling module's name by looking at the frame that called get_logger
            frame = inspect.currentframe()
            # Go up the call stack to find the frame that called get_logger
            while frame:
                frame = frame.f_back
                if frame and frame.f_globals.get('__name__') != 'app.logger':
                    name = frame.f_globals.get('__name__', 'unknown')
                    break
            if not name:
                name = 'unknown'

        self._logger = logging.getLogger(name)

        # Clear existing handlers to ensure we get fresh ones for the new session
        self._logger.handlers.clear()

        # Set up handlers for this logger
        self._logger.setLevel(get_log_level())
        file_handler, console_handler = get_handlers()
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

    def info(self, message):
        """Log an info message."""
        self._logger.info(message)

    def warning(self, message):
        """Log a warning message."""
        self._logger.warning(message)

    def error(self, message):
        """Log an error message."""
        self._logger.error(message)

    def debug(self, message):
        """Log a debug message."""
        self._logger.debug(message)

    def critical(self, message):
        """Log a critical message."""
        self._logger.critical(message)


def get_logger(name=None):
    """
    Get a Logger instance with the specified name.
    If no name is provided, uses the calling module's name.

    Returns:
        Logger: A Logger instance
    """
    return Logger(name)

def refresh_logger_levels():
    """
    Refresh the log level for all existing loggers based on current DEBUG environment variable.
    This should be called after changing the DEBUG environment variable.
    """
    new_level = get_log_level()

    # Get all existing loggers
    for logger_name in logging.root.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.setLevel(new_level)

        # Update handlers for this logger
        for handler in logger.handlers:
            handler.setLevel(new_level)


def log_function_call(func):
    """
    Decorator to log function entry and exit with function name and file.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        func_name = func.__name__
        module_name = func.__module__

        logger.info(f"Entering {module_name}.{func_name}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Exiting {module_name}.{func_name}")
            return result
        except Exception as e:
            logger.error(f"Error in {module_name}.{func_name}: {e}")
            raise

    return wrapper


def log_method_call(method):
    """
    Decorator to log method entry and exit with class and method name.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        logger = get_logger()
        class_name = self.__class__.__name__
        method_name = method.__name__
        module_name = self.__class__.__module__

        logger.info(f"Entering {module_name}.{class_name}.{method_name}")
        try:
            result = method(self, *args, **kwargs)
            logger.info(f"Exiting {module_name}.{class_name}.{method_name}")
            return result
        except Exception as e:
            logger.error(f"Error in {module_name}.{class_name}.{method_name}: {e}")
            raise

    return wrapper

# Convenience functions for common log levels
def info(message, name=None):
    """Log an info message."""
    get_logger(name).info(message)

def warning(message, name=None):
    """Log a warning message."""
    get_logger(name).warning(message)

def error(message, name=None):
    """Log an error message."""
    get_logger(name).error(message)

def debug(message, name=None):
    """Log a debug message."""
    get_logger(name).debug(message)

def critical(message, name=None):
    """Log a critical message."""
    get_logger(name).critical(message)