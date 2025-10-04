#!/usr/bin/env python3
"""
Site-specific settings loader for multi-site architecture.

This module provides secure loading of site configurations with validation
to prevent path traversal attacks and ensure safe site name handling.
Enhanced security features include comprehensive path validation and
protection against various injection attacks.
"""

import os
import importlib.util
import re
from pathlib import Path
from typing import Optional, Any, Dict, Tuple


def get_project_root() -> Path:
    """Get the project root directory (cross-platform)"""
    return Path(__file__).parent.parent.resolve()


def abs_path(*parts) -> Path:
    """Create absolute path from project root (cross-platform)"""
    return (get_project_root() / Path(*parts)).resolve()


def validate_site_name(site: str) -> bool:
    """Validate site name contains only safe characters and prevent path traversal.
    
    Args:
        site: The site name to validate (e.g., 'example.com')
        
    Returns:
        True if the site name is valid and safe, False otherwise
        
    Security Features:
        - Prevents path traversal attacks (e.g., '../', '..\\') 
        - Blocks invalid domain characters
        - Ensures cross-platform compatibility
        - Validates against malicious patterns
        - Enforces RFC domain name standards
    """
    if not site:
        return False
    
    # Length check to prevent overflow attacks
    if len(site) > 253:  # Max domain length per RFC
        return False
    
    # Basic character validation: only alphanumeric, dots, and hyphens (lowercase)
    pattern = r'^[a-z0-9.-]+$'
    if not re.match(pattern, site.lower()):
        return False
    
    # Security: Prevent path traversal attacks
    if '..' in site or site.startswith('.') or site.endswith('.') or site.startswith('-') or site.endswith('-'):
        return False
    
    # Prevent empty labels in domain (e.g., "domain..com")
    if '..' in site or '--' in site:
        return False
    
    # Check for null bytes and other dangerous characters
    dangerous_chars = ['\0', '\n', '\r', '\t', '%00', '../', '..\\', '~', '$', '%', '&', '*', '|', ';', '<', '>', '(', ')', '[', ']', '{', '}', '`', '"', "'"]
    for char in dangerous_chars:
        if char in site:
            return False
    
    # Validate each domain label
    labels = site.split('.')
    for label in labels:
        # Each label must be 1-63 characters
        if not label or len(label) > 63:
            return False
        # Label cannot start/end with hyphen
        if label.startswith('-') or label.endswith('-'):
            return False
        # Check for only valid characters in each label
        if not re.match(r'^[a-z0-9-]+$', label):
            return False
    
    # Cross-platform path traversal protection: use Path and commonpath
    try:
        sites_dir = abs_path("sites")
        site_path = sites_dir / site
        
        # Resolve and normalize paths
        sites_dir_resolved = sites_dir.resolve()
        site_path_resolved = site_path.resolve()
        
        # Use os.path.commonpath for cross-platform security check
        try:
            common = Path(os.path.commonpath([str(sites_dir_resolved), str(site_path_resolved)]))
            if common != sites_dir_resolved:
                return False
        except (ValueError, OSError):
            # Paths are on different drives (Windows) or invalid
            return False
            
    except (ValueError, OSError, AttributeError):
        return False
    
    return True


def load_site_settings(site: Optional[str] = None):
    """
    Load site-specific settings with fallback to core/settings.py
    
    Args:
        site: Domain name (e.g., 'slitheriofree.net') or None for legacy mode
        
    Returns:
        Settings module object
    """
    # Validate site name if provided
    if site and not validate_site_name(site):
        raise ValueError(f"Invalid site name: {site}. Only alphanumeric, dots, and hyphens allowed.")
    
    # Get project root (cross-platform)
    project_root = get_project_root()
    
    # Try to load site-specific settings first
    if site:
        site_settings_path = abs_path("sites", site, "settings.py")
        
        if site_settings_path.exists():
            try:
                # Load site-specific settings module
                spec = importlib.util.spec_from_file_location(
                    f"site_settings_{site.replace('.', '_').replace('-', '_')}", 
                    str(site_settings_path)
                )
                if spec and spec.loader:
                    site_settings = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(site_settings)
                    print(f"✅ Loaded site-specific settings for {site}")
                    return site_settings
            except Exception as e:
                print(f"⚠️  Warning: Could not load site settings for {site}: {e}")
                print("   Falling back to core/settings.py")
    
    # Fallback to core/settings.py (current behavior)
    try:
        from . import settings as core_settings
        if site:
            print(f"📋 Using core/settings.py for {site} (fallback)")
        else:
            print("📋 Using core/settings.py (legacy mode)")
        return core_settings
    except ImportError as e:
        raise ImportError(f"Could not load settings: {e}")


def validate_file_path_security(file_path: str, base_dir: str) -> Tuple[bool, Optional[str]]:
    """Validate that a file path is safe and within expected directories.
    
    Args:
        file_path: The file path to validate
        base_dir: The base directory that the file must be within
        
    Returns:
        Tuple of (is_safe, error_message)
    """
    try:
        # Convert to Path objects and resolve
        file_path_obj = Path(file_path).resolve()
        base_dir_obj = Path(base_dir).resolve()
        
        # Check if file path is within base directory
        try:
            file_path_obj.relative_to(base_dir_obj)
        except ValueError:
            return False, f"Path escapes base directory: {file_path}"
        
        # Check for suspicious patterns
        path_str = str(file_path)
        if any(pattern in path_str for pattern in ['..', '\0', '%00', '~/', '$']):
            return False, f"Suspicious pattern detected in path"
        
        return True, None
        
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


def sanitize_path_component(component: str) -> str:
    """Sanitize a single path component to remove dangerous characters.
    
    Args:
        component: Path component to sanitize
        
    Returns:
        Sanitized path component
    """
    # Remove null bytes and control characters
    component = re.sub(r'[\0\n\r\t]', '', component)
    # Remove path traversal sequences
    component = component.replace('..', '')
    # Remove leading/trailing whitespace and dots
    component = component.strip('. \t')
    return component


def get_site_paths(site: Optional[str] = None) -> dict:
    """
    Get site-specific directory paths with security validation
    
    Args:
        site: Domain name or None for legacy mode
        
    Returns:
        Dictionary with content_dir, static_dir, and site_root paths
    """
    project_root = get_project_root()
    
    # Additional validation if site is provided
    if site and not validate_site_name(site):
        raise ValueError(f"Invalid site name: {site}")
    
    if site:
        # Multi-site mode: use sites/<domain>/ structure (cross-platform)
        site_root = abs_path("sites", site)
        content_dir = site_root / "content_html"
        static_dir = site_root / "static"
        
        # Validate that paths are within project root
        for path_name, path in [("site_root", site_root), ("content_dir", content_dir), ("static_dir", static_dir)]:
            is_safe, error = validate_file_path_security(str(path), str(project_root))
            if not is_safe:
                raise ValueError(f"Security validation failed for {path_name}: {error}")
        
        # Fallback to legacy paths if site-specific don't exist
        if not content_dir.exists():
            content_dir = abs_path("content_html")
            print(f"⚠️  Using fallback content_dir for {site}")
            
        if not static_dir.exists():
            static_dir = abs_path("static")
            print(f"⚠️  Using fallback static_dir for {site}")
    else:
        # Legacy mode: use original structure (cross-platform)
        site_root = project_root
        content_dir = abs_path("content_html")
        static_dir = abs_path("static")
    
    return {
        "site_root": str(site_root),
        "content_dir": str(content_dir),
        "static_dir": str(static_dir),
        "project_root": str(project_root)
    }


def get_site_output_dir(site: Optional[str] = None, custom_output: Optional[str] = None) -> str:
    """
    Get output directory for site with security validation (cross-platform)
    
    Args:
        site: Domain name or None for legacy mode
        custom_output: Custom output directory override
        
    Returns:
        Output directory path
        
    Raises:
        ValueError: If paths fail security validation
    """
    # Validate site name if provided
    if site and not validate_site_name(site):
        raise ValueError(f"Invalid site name: {site}")
    
    if custom_output:
        # Sanitize and validate custom output path
        custom_output = sanitize_path_component(custom_output)
        output_path = Path(custom_output).resolve()
        
        # Ensure it's not trying to write to system directories
        system_dirs = ['/etc', '/usr', '/bin', '/sbin', '/boot', '/proc', '/sys', 
                      'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)']
        output_str = str(output_path)
        for sys_dir in system_dirs:
            if output_str.startswith(sys_dir):
                raise ValueError(f"Cannot write to system directory: {output_str}")
        
        return str(output_path)
    
    if site:
        # Validate site name before using it in path
        if not validate_site_name(site):
            raise ValueError(f"Invalid site name for output directory: {site}")
        return str(abs_path("output", site))
    else:
        return str(abs_path("output"))


def list_available_sites() -> list:
    """
    List all available sites in the sites/ directory (cross-platform)
    
    Returns:
        List of site domain names
    """
    sites_dir = abs_path("sites")
    
    if not sites_dir.exists():
        return []
    
    sites = []
    for item in sites_dir.iterdir():
        if item.is_dir() and validate_site_name(item.name):
            sites.append(item.name)
    
    return sorted(sites)