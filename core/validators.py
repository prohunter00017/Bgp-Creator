#!/usr/bin/env python3
"""
Configuration validators for BGP Creator (ArcadeForge).

This module provides validation functions to ensure configuration integrity
and prevent common errors during site generation.
"""

import os
import re
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
                    except Exception as e:
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
                except:
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