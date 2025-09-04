"""
Environment-specific configuration helper
Handles different settings for development vs production environments
"""

import os
import logging
import re
from typing import Dict, Any, Optional, List
from ..exceptions.holisticos_exceptions import ConfigurationException

class EnvironmentConfig:
    """
    Centralized environment configuration management
    """
    
    @staticmethod
    def get_environment() -> str:
        """Get current environment (development/production/staging)"""
        return os.getenv("ENVIRONMENT", "development").lower()
    
    @staticmethod
    def is_development() -> bool:
        """Check if running in development mode"""
        return EnvironmentConfig.get_environment() == "development"
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production mode"""
        return EnvironmentConfig.get_environment() == "production"
    
    @staticmethod
    def is_staging() -> bool:
        """Check if running in staging mode"""
        return EnvironmentConfig.get_environment() == "staging"
    
    @staticmethod
    def should_use_connection_pool() -> bool:
        """
        Determine if database connection pool should be used
        
        Returns:
            True if connection pool should be used, False for fallback
        """
        environment = EnvironmentConfig.get_environment()
        
        # Always use connection pool in production
        if environment == "production":
            return True
        
        # In development, check for compatible DATABASE_URL
        if environment == "development":
            database_url = os.getenv("DATABASE_URL", "")
            
            # No DATABASE_URL = use fallback
            if not database_url:
                return False
            
            # IPv6 URLs don't work in WSL2 development
            if "db.ijcckqnqruwvqqbkiubb.supabase.co" in database_url:
                return False
            
            # Pooler URLs should work
            if "pooler.supabase.com" in database_url:
                return True
            
            return False
        
        # Default for other environments (staging, etc.)
        return True
    
    @staticmethod
    def get_database_config() -> Dict[str, Any]:
        """
        Get database configuration based on environment
        
        Returns:
            Dictionary with database configuration settings
        """
        environment = EnvironmentConfig.get_environment()
        
        base_config = {
            "min_size": 2,
            "max_size": 8,
            "max_queries": 1000,
            "max_inactive_connection_lifetime": 300,
            "command_timeout": 30
        }
        
        # Adjust for environment
        if environment == "production":
            base_config.update({
                "min_size": 5,
                "max_size": 20,
                "max_queries": 5000,
                "command_timeout": 60
            })
        elif environment == "development":
            base_config.update({
                "min_size": 1,
                "max_size": 5,
                "max_queries": 500,
                "command_timeout": 30
            })
        
        return base_config
    
    @staticmethod
    def get_log_level() -> str:
        """Get appropriate log level for environment"""
        environment = EnvironmentConfig.get_environment()
        
        if environment == "production":
            return os.getenv("LOG_LEVEL", "WARNING")
        elif environment == "development":
            return os.getenv("LOG_LEVEL", "INFO")
        else:
            return os.getenv("LOG_LEVEL", "INFO")
    
    @staticmethod
    def should_enable_debug_endpoints() -> bool:
        """Check if debug endpoints should be enabled"""
        return EnvironmentConfig.get_environment() != "production"
    
    @staticmethod
    def get_timeout_config() -> Dict[str, int]:
        """Get timeout configurations based on environment"""
        environment = EnvironmentConfig.get_environment()
        
        if environment == "production":
            return {
                "openai_request": 60,
                "database_query": 30,
                "behavior_analysis": 180,
                "routine_generation": 120,
                "nutrition_generation": 120
            }
        else:
            return {
                "openai_request": 30,
                "database_query": 30,
                "behavior_analysis": 120,
                "routine_generation": 60,
                "nutrition_generation": 60
            }