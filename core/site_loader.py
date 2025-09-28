#!/usr/bin/env python3
"""
Site-specific settings loader for multi-site architecture.

This module provides secure loading of site configurations with validation
to prevent path traversal attacks and ensure safe site name handling.
"""

import os
import sys
import importlib.util
import re
from pathlib import Path
from typing import Optional, Any, Dict


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
    """
    if not site:
        return False
    
    # Basic character validation: only alphanumeric, dots, and hyphens
    pattern = r'^[a-z0-9.-]+$'
    if not re.match(pattern, site.lower()):
        return False
    
    # Security: Prevent path traversal attacks
    if '..' in site or site.startswith('.') or site.endswith('.') or site.startswith('-') or site.endswith('-'):
        return False
    
    # Prevent empty labels in domain (e.g., "domain..com")
    if '..' in site or '--' in site:
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
            
    except Exception:
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


def get_site_paths(site: Optional[str] = None) -> dict:
    """
    Get site-specific directory paths
    
    Args:
        site: Domain name or None for legacy mode
        
    Returns:
        Dictionary with content_dir, static_dir, and site_root paths
    """
    project_root = get_project_root()
    
    if site:
        # Multi-site mode: use sites/<domain>/ structure (cross-platform)
        site_root = abs_path("sites", site)
        content_dir = site_root / "content_html"
        static_dir = site_root / "static"
        
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
    Get output directory for site (cross-platform)
    
    Args:
        site: Domain name or None for legacy mode
        custom_output: Custom output directory override
        
    Returns:
        Output directory path
    """
    if custom_output:
        return str(Path(custom_output).resolve())
    
    if site:
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