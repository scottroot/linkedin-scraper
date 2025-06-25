import logging
import os
from datetime import datetime
from functools import wraps
import inspect

# Configure logging format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure file handler
log_file = os.path.join(logs_dir, f'linkedin_scraper_{datetime.now().strftime("%Y%m%d")}.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Configure console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))


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

        # Only add handlers if they haven't been added already
        if not self._logger.handlers:
            self._logger.setLevel(LOG_LEVEL)
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