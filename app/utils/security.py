"""
Security utilities for the healthcare chatbot.
"""

import os
import re
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, List
from flask import request, jsonify, current_app, g
from flask_login import current_user
from cryptography.fernet import Fernet
import jwt
import bleach

# Configure logging
logger = logging.getLogger(__name__)

class SecurityManager:
    """Centralized security management for the application."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self._encryption_key)
        
        # Rate limiting configuration
        self.rate_limits = {
            'login_attempts': 5,
            'password_reset': 3,
            'api_calls': 100,
            'chat_messages': 50
        }
        
        # Security headers
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': self._get_csp_header(),
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data."""
        key_file = 'encryption.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            logger.info("Created new encryption key")
            return key
    
    def _get_csp_header(self) -> str:
        """Generate Content Security Policy header."""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdnjs.cloudflare.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.openai.com; "
            "frame-ancestors 'none';"
        )
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like medical history."""
        if not data:
            return data
        
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise SecurityException("Failed to encrypt sensitive data")
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not encrypted_data:
            return encrypted_data
        
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise SecurityException("Failed to decrypt sensitive data")
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """Hash password with salt using PBKDF2."""
        if not salt:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 with SHA-256
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return key.hex(), salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash."""
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return secrets.compare_digest(key.hex(), hashed_password)
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        return secrets.token_urlsafe(length)
    
    def create_jwt_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT token for API authentication."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            'user_id': user_id,
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None

# Global security manager instance
security_manager = SecurityManager()

class SecurityException(Exception):
    """Custom exception for security-related errors."""
    pass

def sanitize_input(input_data: str, allowed_tags: List[str] = None) -> str:
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        input_data: Raw input string
        allowed_tags: List of allowed HTML tags
        
    Returns:
        Sanitized string
    """
    if not input_data:
        return input_data
    
    # Default allowed tags for medical text
    if allowed_tags is None:
        allowed_tags = ['b', 'i', 'em', 'strong', 'p', 'br']
    
    # Sanitize HTML
    sanitized = bleach.clean(
        input_data,
        tags=allowed_tags,
        attributes={},
        strip=True
    )
    
    # Additional sanitization for medical context
    sanitized = re.sub(r'<script.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()

def validate_symptom_input(input_text: str) -> bool:
    """
    Validate symptom input for safety and relevance.
    
    Args:
        input_text: User input describing symptoms
        
    Returns:
        Boolean indicating if input is valid
    """
    if not input_text or len(input_text.strip()) == 0:
        return False
    
    # Check length constraints
    if len(input_text) > 2000:  # Reasonable limit for symptom description
        return False
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'<script',
        r'javascript:',
        r'data:text/html',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*='
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, input_text, re.IGNORECASE):
            logger.warning(f"Suspicious pattern detected in input: {pattern}")
            return False
    
    return True

def require_api_key(f):
    """
    Decorator to require API key authentication.
    
    Expected header: X-API-Key: your-api-key
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'error': 'Missing API key',
                'message': 'X-API-Key header is required'
            }), 401
        
        # Validate API key
        valid_api_keys = current_app.config.get('VALID_API_KEYS', [])
        if api_key not in valid_api_keys:
            logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_permission(permission: str):
    """
    Decorator to require specific user permission.
    
    Args:
        permission: Required permission string
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource'
                }), 401
            
            # Check user permissions (implement based on your user model)
            if not hasattr(current_user, 'has_permission') or not current_user.has_permission(permission):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'Permission {permission} is required'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def log_api_access(f):
    """
    Decorator to log API access for security monitoring.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Log request details
        access_info = {
            'endpoint': request.endpoint,
            'method': request.method,
            'ip_address': request.remote_addr,
            'user_agent': request.user_agent.string,
            'user_id': str(current_user.id) if current_user.is_authenticated else None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store in request context for later use
        g.access_info = access_info
        
        try:
            result = f(*args, **kwargs)
            access_info['status'] = 'success'
            return result
        except Exception as e:
            access_info['status'] = 'error'
            access_info['error'] = str(e)
            raise
        finally:
            # Log to security monitoring system
            logger.info(f"API Access: {access_info}")
    
    return decorated_function

def detect_suspicious_activity(user_id: str, activity_type: str) -> bool:
    """
    Detect suspicious user activity patterns.
    
    Args:
        user_id: User identifier
        activity_type: Type of activity (login, api_call, etc.)
        
    Returns:
        Boolean indicating if activity is suspicious
    """
    # This is a simplified implementation
    # In production, you'd use Redis or database to track activity
    
    current_time = datetime.utcnow()
    time_window = timedelta(minutes=5)
    
    # Example: Check for too many rapid requests
    if activity_type == 'api_call':
        # In a real implementation, you'd check against stored timestamps
        return False  # Placeholder
    
    return False

def apply_security_headers(response):
    """
    Apply security headers to response.
    
    Args:
        response: Flask response object
        
    Returns:
        Response with security headers applied
    """
    for header, value in security_manager.security_headers.items():
        response.headers[header] = value
    
    return response

def validate_file_upload(file, allowed_extensions: set = None, max_size: int = None) -> bool:
    """
    Validate uploaded file for security.
    
    Args:
        file: Uploaded file object
        allowed_extensions: Set of allowed file extensions
        max_size: Maximum file size in bytes
        
    Returns:
        Boolean indicating if file is safe
    """
    if not file:
        return False
    
    # Check file extension
    if allowed_extensions:
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return False
    
    # Check file size
    if max_size:
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning
        if size > max_size:
            return False
    
    # Check for malicious content (basic)
    content_preview = file.read(1024)  # Read first 1KB
    file.seek(0)  # Reset
    
    # Look for suspicious patterns
    suspicious_patterns = [
        b'<script',
        b'javascript:',
        b'<?php',
        b'<%',
        b'exec(',
        b'system(',
        b'shell_exec'
    ]
    
    for pattern in suspicious_patterns:
        if pattern in content_preview:
            logger.warning(f"Suspicious pattern found in uploaded file: {pattern}")
            return False
    
    return True

def generate_csrf_token() -> str:
    """Generate CSRF token for form protection."""
    return security_manager.generate_secure_token(32)

def verify_csrf_token(token: str, stored_token: str) -> bool:
    """Verify CSRF token."""
    return secrets.compare_digest(token, stored_token)

def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging/display.
    
    Args:
        data: Sensitive data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to keep visible
        
    Returns:
        Masked string
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ''
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)

def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength and return detailed feedback.
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'is_valid': True,
        'score': 0,
        'issues': [],
        'suggestions': []
    }
    
    # Length check
    if len(password) < 8:
        result['is_valid'] = False
        result['issues'].append('Password must be at least 8 characters long')
        result['suggestions'].append('Use a longer password')
    else:
        result['score'] += 1
    
    # Character variety checks
    if not re.search(r'[a-z]', password):
        result['issues'].append('Password must contain lowercase letters')
        result['suggestions'].append('Add lowercase letters')
    else:
        result['score'] += 1
    
    if not re.search(r'[A-Z]', password):
        result['issues'].append('Password must contain uppercase letters')
        result['suggestions'].append('Add uppercase letters')
    else:
        result['score'] += 1
    
    if not re.search(r'\d', password):
        result['issues'].append('Password must contain numbers')
        result['suggestions'].append('Add numbers')
    else:
        result['score'] += 1
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['issues'].append('Password must contain special characters')
        result['suggestions'].append('Add special characters (!@#$%^&*)')
    else:
        result['score'] += 1
    
    # Common password check
    common_passwords = [
        'password', '123456', 'password123', 'admin', 'letmein',
        'welcome', 'monkey', '1234567890', 'qwerty', 'abc123'
    ]
    
    if password.lower() in common_passwords:
        result['is_valid'] = False
        result['issues'].append('Password is too common')
        result['suggestions'].append('Use a unique password')
        result['score'] = 0
    
    # Final validation
    if len(result['issues']) > 0:
        result['is_valid'] = False
    
    return result

class RateLimiter:
    """Simple in-memory rate limiter for demonstration."""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, identifier: str, limit: int, window: int = 3600) -> bool:
        """
        Check if request is allowed under rate limit.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Boolean indicating if request is allowed
        """
        current_time = datetime.utcnow()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        cutoff_time = current_time - timedelta(seconds=window)
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= limit:
            return False
        
        # Add current request
        self.requests[identifier].append(current_time)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()
