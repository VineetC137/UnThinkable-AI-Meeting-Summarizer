"""
Validation utilities for API inputs and data processing.
"""

import re
from typing import List, Optional, Dict, Any
from pydantic import validator, ValidationError

from app.core.logging import get_logger

logger = get_logger(__name__)


class ValidationUtils:
    """Utility class for common validations."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format."""
        # Username should be 3-30 characters, alphanumeric plus underscore
        pattern = r'^[a-zA-Z0-9_]{3,30}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength."""
        result = {
            'valid': True,
            'errors': [],
            'score': 0,
            'suggestions': []
        }
        
        # Check length
        if len(password) < 8:
            result['valid'] = False
            result['errors'].append("Password must be at least 8 characters long")
        else:
            result['score'] += 1
        
        # Check for uppercase
        if not re.search(r'[A-Z]', password):
            result['suggestions'].append("Add uppercase letters")
        else:
            result['score'] += 1
        
        # Check for lowercase
        if not re.search(r'[a-z]', password):
            result['suggestions'].append("Add lowercase letters")
        else:
            result['score'] += 1
        
        # Check for numbers
        if not re.search(r'\d', password):
            result['suggestions'].append("Add numbers")
        else:
            result['score'] += 1
        
        # Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['suggestions'].append("Add special characters")
        else:
            result['score'] += 1
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', 'qwerty', 'abc123', 'password123',
            'admin', 'letmein', 'welcome', '12345678'
        ]
        if password.lower() in weak_passwords:
            result['valid'] = False
            result['errors'].append("Password is too common")
            result['score'] = 0
        
        return result
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """Validate file extension."""
        if not filename:
            return False
        
        extension = filename.lower().split('.')[-1]
        return f".{extension}" in [ext.lower() for ext in allowed_extensions]
    
    @staticmethod
    def validate_meeting_title(title: str) -> bool:
        """Validate meeting title."""
        if not title or not title.strip():
            return False
        
        # Title should be 1-255 characters
        if len(title.strip()) > 255:
            return False
        
        # No special characters that could cause issues
        forbidden_chars = ['<', '>', '"', "'", '&', '\0', '\n', '\r', '\t']
        return not any(char in title for char in forbidden_chars)
    
    @staticmethod
    def validate_tags(tags: List[str]) -> bool:
        """Validate meeting tags."""
        if not isinstance(tags, list):
            return False
        
        # Max 10 tags
        if len(tags) > 10:
            return False
        
        # Each tag should be 1-50 characters
        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                return False
            if len(tag.strip()) > 50:
                return False
        
        return True
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Sanitize search query to prevent injection."""
        if not query:
            return ""
        
        # Remove potentially dangerous characters
        query = re.sub(r'[<>"\'\(\);]', '', query)
        
        # Limit length
        return query[:200]
    
    @staticmethod
    def validate_pagination_params(page: int, per_page: int) -> Dict[str, Any]:
        """Validate pagination parameters."""
        result = {'valid': True, 'errors': []}
        
        if page < 1:
            result['valid'] = False
            result['errors'].append("Page must be >= 1")
        
        if per_page < 1 or per_page > 100:
            result['valid'] = False
            result['errors'].append("Per page must be between 1 and 100")
        
        return result
    
    @staticmethod
    def validate_json_field(data: Any, max_size_kb: int = 100) -> bool:
        """Validate JSON field size and structure."""
        try:
            import json
            import sys
            
            # Check if data can be serialized
            json_str = json.dumps(data)
            
            # Check size
            size_kb = sys.getsizeof(json_str) / 1024
            if size_kb > max_size_kb:
                return False
            
            return True
        except (TypeError, ValueError, OverflowError):
            return False
    
    @staticmethod
    def validate_model_name(model_name: str, provider: str) -> bool:
        """Validate model name for specific provider."""
        if not model_name or not model_name.strip():
            return False
        
        # Basic alphanumeric check with some allowed special characters
        pattern = r'^[a-zA-Z0-9\-_.]+$'
        if not re.match(pattern, model_name):
            return False
        
        # Length check
        if len(model_name) > 100:
            return False
        
        return True
    
    @staticmethod
    def validate_context_text(text: str) -> bool:
        """Validate context text field."""
        if not text:
            return True  # Optional field
        
        # Max 2000 characters
        if len(text) > 2000:
            return False
        
        # No null bytes or control characters
        if '\0' in text:
            return False
        
        return True


# Example custom Pydantic validators
def validate_strong_password(password: str) -> str:
    """Pydantic validator for strong passwords."""
    validation_result = ValidationUtils.validate_password_strength(password)
    if not validation_result['valid']:
        raise ValueError(f"Password validation failed: {', '.join(validation_result['errors'])}")
    return password


def validate_meeting_tags(tags: List[str]) -> List[str]:
    """Pydantic validator for meeting tags."""
    if not ValidationUtils.validate_tags(tags):
        raise ValueError("Invalid tags format or content")
    return [tag.strip() for tag in tags]


def validate_safe_filename(filename: str) -> str:
    """Pydantic validator for safe filenames."""
    if not filename:
        raise ValueError("Filename is required")
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValueError("Invalid filename")
    
    return filename


# Global validator instance
validators = ValidationUtils()