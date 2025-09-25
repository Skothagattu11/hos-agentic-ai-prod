"""
Environment-aware logging utility
Provides detailed logging for development, minimal for production
"""
import os
import logging

# Check environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT in ["production", "prod"]
IS_DEVELOPMENT = ENVIRONMENT in ["development", "dev"]

class EnvironmentLogger:
    """Environment-aware logger that adjusts verbosity based on environment"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name

    def debug_dev(self, message: str, *args, **kwargs):
        """Debug logging only in development environment"""
        if IS_DEVELOPMENT:
            print(f"🔧 [DEV_{self.name.upper()}] {message}")
            self.logger.debug(message, *args, **kwargs)

    def info_dev(self, message: str, *args, **kwargs):
        """Info logging only in development environment"""
        if IS_DEVELOPMENT:
            print(f"ℹ️ [DEV_{self.name.upper()}] {message}")
            self.logger.info(message, *args, **kwargs)

    def warn_always(self, message: str, *args, **kwargs):
        """Warning logging in all environments"""
        self.logger.warning(message, *args, **kwargs)

    def error_always(self, message: str, *args, **kwargs):
        """Error logging in all environments"""
        self.logger.error(message, *args, **kwargs)

    def critical_always(self, message: str, *args, **kwargs):
        """Critical logging in all environments"""
        self.logger.critical(message, *args, **kwargs)

def get_env_logger(name: str) -> EnvironmentLogger:
    """Get environment-aware logger for a module"""
    return EnvironmentLogger(name)

# Helper functions for quick access
def log_dev(message: str, category: str = "SYSTEM"):
    """Quick development-only logging"""
    if IS_DEVELOPMENT:
        print(f"🛠️ [DEV_{category}] {message}")

def log_prod(message: str, level: str = "INFO"):
    """Production logging (errors/warnings only)"""
    if IS_PRODUCTION:
        logger = logging.getLogger("production")
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "CRITICAL":
            logger.critical(message)