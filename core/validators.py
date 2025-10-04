#!/usr/bin/env python3
"""
Configuration validators for BGP Creator (ArcadeForge).

This module provides validation functions to ensure configuration integrity,
prevent common errors during site generation, and implement comprehensive
security measures against injection attacks and path traversal.
"""

import os
import re
import html
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


class ConfigValidator:
    """Validates site configuration to ensure all required fields are present and valid."""
    
    def __init__(self):
        """Initialize the configuration validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_site_config(self, config: Any) -> Tuple[bool, List[str], List[str]]:
        """Validate a complete site configuration.
        
        Args:
            config: The site configuration object or module to validate
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Validate required fields
        self._validate_required_fields(config)
        
        # Validate URLs
        self._validate_urls(config)
        
        # Validate email addresses
        self._validate_emails(config)
        
        # Validate ad configuration if present
        if hasattr(config, 'ADS_ENABLED') and config.ADS_ENABLED:
            self._validate_ad_config(config)
        
        # Validate social media links if present
        if hasattr(config, 'SOCIAL_MEDIA'):
            self._validate_social_media(config)
        
        # Validate rating configuration if present
        if hasattr(config, 'APP_RATING'):
            self._validate_app_rating(config)
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_required_fields(self, config: Any) -> None:
        """Check that all required fields are present."""
        required_fields = [
            'SITE_NAME',
            'SITE_URL', 
            'SITE_DOMAIN',
            'GAME_EMBED_URL'
        ]
        
        for field in required_fields:
            if not hasattr(config, field):
                self.errors.append(f"Required field '{field}' is missing from configuration")
            elif not getattr(config, field):
                self.errors.append(f"Required field '{field}' is empty")
    
    def _validate_urls(self, config: Any) -> None:
        """Validate that URLs are properly formatted."""
        url_fields = ['SITE_URL', 'GAME_EMBED_URL']
        
        for field in url_fields:
            if hasattr(config, field):
                url = getattr(config, field)
                if url:
                    try:
                        parsed = urlparse(url)
                        if not parsed.scheme:
                            self.errors.append(f"{field}: URL must include http:// or https:// scheme")
                        if not parsed.netloc:
                            self.errors.append(f"{field}: Invalid URL format")
                    except (ValueError, TypeError) as e:
                        self.errors.append(f"{field}: Invalid URL - {str(e)}")
    
    def _validate_emails(self, config: Any) -> None:
        """Validate email addresses."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if hasattr(config, 'CONTACT_EMAIL'):
            email = getattr(config, 'CONTACT_EMAIL')
            if email and not re.match(email_pattern, email):
                self.errors.append(f"Invalid email address: {email}")
    
    def _validate_ad_config(self, config: Any) -> None:
        """Validate advertisement configuration."""
        if not hasattr(config, 'AD_NETWORKS'):
            self.warnings.append("ADS_ENABLED is True but AD_NETWORKS is not configured")
            return
        
        ad_networks = getattr(config, 'AD_NETWORKS', {})
        active_networks = [k for k, v in ad_networks.items() 
                          if isinstance(v, dict) and v.get('enabled')]
        
        if not active_networks:
            self.warnings.append("ADS_ENABLED is True but no ad networks are enabled")
        
        # Validate AdSense configuration if enabled
        if 'google_adsense' in active_networks:
            adsense = ad_networks.get('google_adsense', {})
            if not adsense.get('publisher_id'):
                self.errors.append("Google AdSense enabled but publisher_id is missing")
    
    def _validate_social_media(self, config: Any) -> None:
        """Validate social media links."""
        social = getattr(config, 'SOCIAL_MEDIA', {})
        
        for platform, url in social.items():
            if url:
                try:
                    parsed = urlparse(url)
                    if not parsed.scheme:
                        self.warnings.append(f"Social media URL for {platform} should include http:// or https://")
                except (ValueError, AttributeError):
                    self.warnings.append(f"Invalid URL for social media platform: {platform}")
    
    def _validate_app_rating(self, config: Any) -> None:
        """Validate app rating configuration."""
        rating = getattr(config, 'APP_RATING', {})
        
        if rating:
            # Validate rating value is within range
            try:
                rating_value = float(rating.get('rating_value', 0))
                if rating_value < 1 or rating_value > 5:
                    self.warnings.append("APP_RATING.rating_value should be between 1 and 5")
            except (ValueError, TypeError):
                self.errors.append("APP_RATING.rating_value must be a number")
            
            # Validate rating count is positive
            try:
                rating_count = int(rating.get('rating_count', 0))
                if rating_count < 0:
                    self.warnings.append("APP_RATING.rating_count should be positive")
            except (ValueError, TypeError):
                self.errors.append("APP_RATING.rating_count must be a number")


def validate_file_paths(paths: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Validate that required file paths exist.
    
    Args:
        paths: Dictionary of path names to actual paths
        
    Returns:
        Tuple of (all_exist, missing_paths)
    """
    missing = []
    
    for name, path in paths.items():
        if not os.path.exists(path):
            missing.append(f"{name}: {path}")
    
    return len(missing) == 0, missing


def validate_domain_name(domain: str) -> bool:
    """Validate that a domain name is properly formatted.
    
    Args:
        domain: Domain name to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Basic domain validation pattern
    pattern = r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$'
    return bool(re.match(pattern, domain.lower()))


def validate_safe_path(path: str, base_dir: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Validate a file path to prevent directory traversal attacks.
    
    Args:
        path: The path to validate
        base_dir: Optional base directory to ensure path stays within
        
    Returns:
        Tuple of (is_safe, error_message)
    """
    if not path:
        return False, "Path cannot be empty"
    
    # Convert to Path object for better handling
    try:
        path_obj = Path(path)
        
        # Check for path traversal attempts
        if '..' in path_obj.parts:
            return False, "Path traversal detected: '..' not allowed"
        
        # Check for absolute paths when not expected
        if path_obj.is_absolute() and base_dir:
            return False, "Absolute paths not allowed when base directory is specified"
        
        # Normalize and resolve the path
        if base_dir:
            base_path = Path(base_dir).resolve()
            full_path = (base_path / path).resolve()
            
            # Ensure the resolved path is within base directory
            try:
                full_path.relative_to(base_path)
            except ValueError:
                return False, f"Path escapes base directory: {path}"
        
        # Check for suspicious patterns
        path_str = str(path_obj)
        suspicious_patterns = [
            r'\0',  # Null bytes
            r'\.\./',  # Path traversal
            r'\.\.\\',  # Windows path traversal
            r'^~',  # Home directory expansion
            r'^\$',  # Environment variable
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, path_str):
                return False, f"Suspicious pattern detected in path: {pattern}"
        
        return True, None
        
    except (ValueError, OSError, TypeError) as e:
        return False, f"Invalid path: {str(e)}"


def sanitize_html_content(content: str, allow_basic_tags: bool = False) -> str:
    """Sanitize user-provided content to prevent XSS attacks.
    
    Args:
        content: The content to sanitize
        allow_basic_tags: Whether to allow basic formatting tags (b, i, em, strong)
        
    Returns:
        Sanitized content safe for HTML output
    """
    if not content:
        return ""
    
    # First, escape all HTML special characters
    sanitized = html.escape(content, quote=True)
    
    # Optionally restore basic formatting tags if allowed
    if allow_basic_tags:
        allowed_tags = ['b', 'i', 'em', 'strong', 'u']
        for tag in allowed_tags:
            # Restore opening tags
            sanitized = sanitized.replace(f'&lt;{tag}&gt;', f'<{tag}>')
            # Restore closing tags
            sanitized = sanitized.replace(f'&lt;/{tag}&gt;', f'</{tag}>')
    
    return sanitized


def validate_url_strict(url: str, allowed_schemes: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """Strictly validate URLs to prevent XSS and other attacks.
    
    Args:
        url: The URL to validate
        allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"
    
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if not parsed.scheme:
            return False, "URL must include a scheme (http:// or https://)"
        
        if parsed.scheme.lower() not in allowed_schemes:
            return False, f"URL scheme '{parsed.scheme}' not allowed. Allowed schemes: {', '.join(allowed_schemes)}"
        
        # Check for javascript: and data: URLs
        if parsed.scheme.lower() in ['javascript', 'data', 'vbscript', 'file']:
            return False, f"Potentially dangerous URL scheme: {parsed.scheme}"
        
        # Check netloc (domain)
        if not parsed.netloc:
            return False, "URL must include a domain"
        
        # Check for suspicious patterns in URL
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',  # Event handlers like onclick=
            r'\0',  # Null bytes
            r'%00',  # URL-encoded null
            r'%3Cscript',  # URL-encoded <script
        ]
        
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, url_lower, re.IGNORECASE):
                return False, f"Suspicious pattern detected in URL"
        
        return True, None
        
    except (ValueError, TypeError, AttributeError) as e:
        return False, f"Invalid URL format: {str(e)}"


def validate_image_path(image_path: str, base_dir: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Validate image file paths with additional security checks.
    
    Args:
        image_path: The image path to validate
        base_dir: Optional base directory for the images
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # First, perform general path validation
    is_safe, error = validate_safe_path(image_path, base_dir)
    if not is_safe:
        return False, error
    
    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.bmp']
    path_obj = Path(image_path)
    
    if path_obj.suffix.lower() not in allowed_extensions:
        return False, f"Invalid image extension: {path_obj.suffix}. Allowed: {', '.join(allowed_extensions)}"
    
    # Check for double extensions (potential attack vector)
    if len(path_obj.suffixes) > 1:
        return False, "Multiple file extensions not allowed for security reasons"
    
    return True, None


def sanitize_filename(filename: str, allow_subdirs: bool = False) -> str:
    """Sanitize a filename to make it safe for file operations.
    
    Args:
        filename: The filename to sanitize
        allow_subdirs: Whether to allow subdirectories in the path
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return ""
    
    # Remove null bytes
    filename = filename.replace('\0', '')
    
    # Handle subdirectories if allowed
    if allow_subdirs:
        # Split path and sanitize each part
        parts = filename.replace('\\', '/').split('/')
        sanitized_parts = []
        for part in parts:
            if part and part not in ['.', '..']:
                # Remove dangerous characters from each part
                part = re.sub(r'[<>:"|?*]', '', part)
                part = part.strip('. ')
                if part:
                    sanitized_parts.append(part)
        return '/'.join(sanitized_parts) if sanitized_parts else ""
    else:
        # Remove all path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        return filename


def validate_config(config: Any) -> Tuple[bool, List[str], List[str]]:
    """Enhanced configuration validation with security checks.
    
    This is the main validation function that performs comprehensive
    validation including security checks on all configuration values.
    
    Args:
        config: The configuration object or module to validate
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = ConfigValidator()
    is_valid, errors, warnings = validator.validate_site_config(config)
    
    # Additional security validations
    security_errors = []
    security_warnings = []
    
    # Validate and sanitize text fields for XSS
    text_fields = ['SITE_NAME', 'SITE_TITLE', 'SITE_DESCRIPTION', 'SITE_TAGLINE']
    for field in text_fields:
        if hasattr(config, field):
            value = getattr(config, field)
            if value and isinstance(value, str):
                # Check for potential XSS patterns
                if re.search(r'<script|javascript:|on\w+\s*=', value, re.IGNORECASE):
                    security_errors.append(f"{field} contains potentially dangerous HTML/JavaScript")
                
                # Sanitize and store back (for reference, actual sanitization happens during rendering)
                sanitized = sanitize_html_content(value, allow_basic_tags=True)
                if sanitized != value:
                    security_warnings.append(f"{field} contains HTML that will be escaped for security")
    
    # Validate file paths if specified
    if hasattr(config, 'CUSTOM_LOGO_PATH'):
        logo_path = getattr(config, 'CUSTOM_LOGO_PATH')
        if logo_path:
            is_valid_path, error = validate_image_path(logo_path)
            if not is_valid_path:
                security_errors.append(f"CUSTOM_LOGO_PATH: {error}")
    
    # Validate output directory if specified
    if hasattr(config, 'OUTPUT_DIR'):
        output_dir = getattr(config, 'OUTPUT_DIR')
        if output_dir:
            is_safe, error = validate_safe_path(output_dir)
            if not is_safe:
                security_errors.append(f"OUTPUT_DIR: {error}")
    
    # Combine errors and warnings
    errors.extend(security_errors)
    warnings.extend(security_warnings)
    
    return len(errors) == 0, errors, warnings


# Rate limiting documentation
"""
RATE LIMITING CONSIDERATIONS:

Rate limiting should be implemented at the following points to prevent abuse:

1. Web Server Level (Recommended):
   - Implement at nginx/Apache level using modules like mod_ratelimit
   - Or use a reverse proxy like Cloudflare with rate limiting rules
   
2. Application Entry Points:
   - main.py: When processing generation requests
     Example: Use a simple in-memory counter with timestamps
     ```python
     from collections import deque
     from time import time
     
     request_timestamps = deque(maxlen=100)
     MAX_REQUESTS_PER_MINUTE = 10
     
     def check_rate_limit():
         now = time()
         request_timestamps.append(now)
         recent_requests = sum(1 for t in request_timestamps if now - t < 60)
         return recent_requests <= MAX_REQUESTS_PER_MINUTE
     ```
   
3. File Upload/Processing:
   - Limit the number of sites that can be processed per hour
   - Limit the size of uploaded content files
   - Implement cooldown periods between generation requests

4. API Endpoints (if exposed):
   - Use decorators to limit requests per IP
   - Implement token bucket algorithm for more sophisticated limiting
   
5. Resource-Intensive Operations:
   - Image processing: Limit concurrent image optimization operations
   - Site crawling: Implement delays between page fetches
   - Build cache operations: Limit cache rebuilds per time period

Note: The actual implementation depends on the deployment environment.
For production use, consider using established libraries like:
- Flask-Limiter (if using Flask)
- django-ratelimit (if using Django)  
- redis-py with Redis for distributed rate limiting
"""