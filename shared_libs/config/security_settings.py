"""
Production Security Settings
Centralized security configuration for CORS, headers, and validation
"""

import os
from typing import List, Dict, Any
from ..utils.environment_config import EnvironmentConfig


class SecuritySettings:
    """Centralized security configuration"""
    
    @staticmethod
    def get_allowed_origins() -> List[str]:
        """Get allowed CORS origins based on environment"""
        environment = EnvironmentConfig.get_environment()
        
        # Production origins - only specific domains allowed
        production_origins = [
            "https://bio-coach-hub.vercel.app",
            "https://admin-hos.onrender.com",
            "https://holisticos.tech",
            "https://www.holisticos.tech"
        ]
        
        # Development origins - local development servers
        development_origins = [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://localhost:5173",
            "http://localhost:8080"
        ]
        
        if environment == "production":
            return production_origins
        elif environment == "development":
            return development_origins + production_origins  # Allow testing prod URLs locally
        elif environment == "staging":
            return production_origins + [
                "https://staging.holisticos.tech",
                "http://localhost:3000"  # Allow local testing of staging
            ]
        else:
            return development_origins  # Fallback for unknown environments
    
    @staticmethod
    def get_allowed_methods() -> List[str]:
        """Get allowed HTTP methods"""
        return ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    
    @staticmethod
    def get_allowed_headers() -> List[str]:
        """Get allowed HTTP headers"""
        return [
            "Content-Type",
            "Authorization", 
            "Accept",
            "Origin",
            "X-Requested-With"
        ]
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get security headers to add to all responses"""
        return {
            # Prevent MIME sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # XSS protection (legacy but still good to have)
            "X-XSS-Protection": "1; mode=block",
            
            # HTTPS enforcement (only in production)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if EnvironmentConfig.is_production() else "",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    @staticmethod
    def is_cors_credentials_allowed() -> bool:
        """Whether to allow credentials in CORS requests"""
        # Allow credentials for authenticated requests
        return True
    
    @staticmethod
    def validate_cors_origin(origin: str) -> bool:
        """Validate if an origin is allowed"""
        allowed_origins = SecuritySettings.get_allowed_origins()
        return origin in allowed_origins
    
    @staticmethod
    def should_log_security_events() -> bool:
        """Whether to log security-related events"""
        return EnvironmentConfig.is_production() or EnvironmentConfig.is_staging()


# Convenience function for FastAPI CORS setup
def get_cors_config() -> Dict[str, Any]:
    """Get complete CORS configuration for FastAPI"""
    return {
        "allow_origins": SecuritySettings.get_allowed_origins(),
        "allow_credentials": SecuritySettings.is_cors_credentials_allowed(),
        "allow_methods": SecuritySettings.get_allowed_methods(),
        "allow_headers": SecuritySettings.get_allowed_headers()
    }