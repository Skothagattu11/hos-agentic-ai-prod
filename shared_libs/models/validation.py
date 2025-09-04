"""
Input Validation and Sanitization for HolisticOS API
Simple, effective validation without breaking existing functionality
"""

import html
import re
from typing import Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date


class SecureUserRequest(BaseModel):
    """Base class for user-related API requests with security validation"""
    
    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        """Sanitize all string inputs to prevent XSS"""
        if isinstance(v, str):
            # Basic HTML escaping
            sanitized = html.escape(v.strip())
            # Remove potentially dangerous characters for SQL safety
            sanitized = re.sub(r'[<>"\';\\]', '', sanitized)
            return sanitized[:1000]  # Limit string length
        return v


class SecureUserIdMixin:
    """Mixin for validating user IDs"""
    
    @validator('user_id', pre=True)
    def validate_user_id(cls, v):
        if not v:
            raise ValueError("User ID is required")
        
        # Sanitize and validate user ID format
        user_id = str(v).strip()
        
        # Allow alphanumeric, hyphens, and underscores (Firebase UID format)
        if not re.match(r'^[a-zA-Z0-9_-]{1,128}$', user_id):
            raise ValueError("Invalid user ID format")
            
        return user_id


class SecureDateRequest(SecureUserRequest):
    """Request with date validation"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    
    @validator('date', pre=True)
    def validate_date(cls, v):
        if isinstance(v, str):
            # Validate date format: YYYY-MM-DD
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
                raise ValueError("Date must be in YYYY-MM-DD format")
            
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError("Invalid date")
        return v


class SecureAnalysisRequest(SecureUserRequest):
    """Validation for analysis requests"""
    user_id: str = Field(..., min_length=1, max_length=128)
    archetype: Optional[str] = Field(None, max_length=50)
    
    @validator('archetype')
    def validate_archetype(cls, v):
        if v:
            valid_archetypes = [
                'Foundation Builder',
                'Transformation Seeker', 
                'Systematic Improver',
                'Peak Performer',
                'Resilience Rebuilder',
                'Connected Explorer'
            ]
            if v not in valid_archetypes:
                raise ValueError(f"Invalid archetype. Must be one of: {', '.join(valid_archetypes)}")
        return v


class SecureFeedbackRequest(SecureUserRequest):
    """Validation for feedback requests"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=500)
    
    @validator('feedback')
    def validate_feedback(cls, v):
        if v:
            # Additional sanitization for user feedback
            sanitized = html.escape(v.strip())
            # Remove excessive whitespace
            sanitized = re.sub(r'\s+', ' ', sanitized)
            return sanitized[:500]
        return v


def sanitize_input(value: Any, max_length: int = 1000) -> Any:
    """
    General purpose input sanitization function
    
    Args:
        value: Input value to sanitize
        max_length: Maximum allowed length for strings
        
    Returns:
        Sanitized value
    """
    if isinstance(value, str):
        # HTML escape
        sanitized = html.escape(value.strip())
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';\\]', '', sanitized)
        
        # Limit length
        return sanitized[:max_length]
    
    elif isinstance(value, dict):
        # Recursively sanitize dictionary values
        return {k: sanitize_input(v, max_length) for k, v in value.items()}
    
    elif isinstance(value, list):
        # Recursively sanitize list items
        return [sanitize_input(item, max_length) for item in value]
    
    return value


def validate_user_id(user_id: str) -> str:
    """
    Validate and sanitize user ID
    
    Args:
        user_id: User ID to validate
        
    Returns:
        Validated user ID
        
    Raises:
        ValueError: If user ID is invalid
    """
    if not user_id:
        raise ValueError("User ID is required")
    
    user_id = str(user_id).strip()
    
    # Allow Firebase UID format: alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]{1,128}$', user_id):
        raise ValueError("Invalid user ID format")
    
    return user_id


def validate_date_string(date_str: str) -> str:
    """
    Validate date string format
    
    Args:
        date_str: Date string to validate
        
    Returns:
        Validated date string
        
    Raises:
        ValueError: If date is invalid
    """
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        raise ValueError("Date must be in YYYY-MM-DD format")
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        raise ValueError("Invalid date")


# Security middleware helper
class InputSecurityChecker:
    """Helper class for additional security checks"""
    
    @staticmethod
    def check_sql_injection_patterns(text: str) -> bool:
        """Check for common SQL injection patterns"""
        sql_patterns = [
            r'(union|select|insert|update|delete|drop|create|alter)\s+',
            r'(\-\-|\#|\/\*)',
            r'(\bor\b|\band\b)\s*\d+\s*=\s*\d+',
            r'\'.*\'',
            r'\".*\"',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text.lower()):
                return True
        return False
    
    @staticmethod
    def check_xss_patterns(text: str) -> bool:
        """Check for common XSS patterns"""
        xss_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed',
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, text.lower()):
                return True
        return False
    
    @staticmethod
    def is_safe_input(text: str) -> bool:
        """Check if input is safe from common attacks"""
        if not isinstance(text, str):
            return True
        
        return not (
            InputSecurityChecker.check_sql_injection_patterns(text) or
            InputSecurityChecker.check_xss_patterns(text)
        )