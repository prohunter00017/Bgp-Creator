#!/usr/bin/env python3
"""
Gaming Color Palettes for BGP Creator
Eye-friendly color schemes for gaming websites
"""

# Define 4 gaming-friendly color palettes
COLOR_PALETTES = {
    1: {
        "name": "Dark Ocean",
        "description": "Deep blue gaming theme with cyan accents",
        "colors": {
            # Backgrounds
            "--bg-primary": "#0a0f1c",
            "--bg-secondary": "#1a2332", 
            "--bg-surface": "#2d3748",
            "--bg-overlay": "rgba(10, 15, 28, 0.85)",
            
            # Text colors
            "--text-primary": "#ffffff",
            "--text-secondary": "#cbd5e0",
            "--text-muted": "#9ca3af",
            
            # Brand colors
            "--brand-primary": "#00d9ff",
            "--brand-hover": "#00b8e6",
            "--brand-active": "#0891b2",
            
            # Accent colors
            "--accent-green": "#34d399",
            "--accent-pink": "#f472b6", 
            "--accent-purple": "#a78bfa",
            "--accent-yellow": "#fbbf24",
            
            # Legacy support
            "--bg": "#0a0f1c",
            "--fg": "#ffffff",
            "--muted": "#9ca3af",
            "--brand": "#00d9ff",
            "--brand-2": "#00b8e6",
            "--surface": "#2d3748"
        }
    },
    
    2: {
        "name": "Neon Purple",
        "description": "Cyberpunk purple theme with electric accents",
        "colors": {
            # Backgrounds
            "--bg-primary": "#0f0a1a",
            "--bg-secondary": "#1a0f2e",
            "--bg-surface": "#2d1b3d",
            "--bg-overlay": "rgba(15, 10, 26, 0.85)",
            
            # Text colors
            "--text-primary": "#ffffff",
            "--text-secondary": "#e2d1f3",
            "--text-muted": "#a78bfa",
            
            # Brand colors
            "--brand-primary": "#a855f7",
            "--brand-hover": "#9333ea",
            "--brand-active": "#7c3aed",
            
            # Accent colors
            "--accent-green": "#10b981",
            "--accent-pink": "#ec4899",
            "--accent-purple": "#d946ef",
            "--accent-yellow": "#f59e0b",
            
            # Legacy support
            "--bg": "#0f0a1a",
            "--fg": "#ffffff", 
            "--muted": "#a78bfa",
            "--brand": "#a855f7",
            "--brand-2": "#9333ea",
            "--surface": "#2d1b3d"
        }
    },
    
    3: {
        "name": "Forest Green",
        "description": "Natural green gaming theme with earth tones",
        "colors": {
            # Backgrounds
            "--bg-primary": "#0f1a0a",
            "--bg-secondary": "#1a2e14",
            "--bg-surface": "#2d4a22",
            "--bg-overlay": "rgba(15, 26, 10, 0.85)",
            
            # Text colors
            "--text-primary": "#ffffff",
            "--text-secondary": "#d1f2d1",
            "--text-muted": "#86bc86",
            
            # Brand colors
            "--brand-primary": "#10b981",
            "--brand-hover": "#059669",
            "--brand-active": "#047857",
            
            # Accent colors
            "--accent-green": "#34d399",
            "--accent-pink": "#f87171",
            "--accent-purple": "#a78bfa",
            "--accent-yellow": "#fbbf24",
            
            # Legacy support
            "--bg": "#0f1a0a",
            "--fg": "#ffffff",
            "--muted": "#86bc86",
            "--brand": "#10b981",
            "--brand-2": "#059669",
            "--surface": "#2d4a22"
        }
    },
    
    4: {
        "name": "Fire Orange",
        "description": "Warm orange gaming theme with energy accents",
        "colors": {
            # Backgrounds
            "--bg-primary": "#1a0f0a",
            "--bg-secondary": "#2e1a14",
            "--bg-surface": "#4a2d22",
            "--bg-overlay": "rgba(26, 15, 10, 0.85)",
            
            # Text colors
            "--text-primary": "#ffffff", 
            "--text-secondary": "#f2d1d1",
            "--text-muted": "#bc8686",
            
            # Brand colors
            "--brand-primary": "#f97316",
            "--brand-hover": "#ea580c",
            "--brand-active": "#c2410c",
            
            # Accent colors
            "--accent-green": "#22c55e",
            "--accent-pink": "#f472b6",
            "--accent-purple": "#a78bfa", 
            "--accent-yellow": "#eab308",
            
            # Legacy support
            "--bg": "#1a0f0a",
            "--fg": "#ffffff",
            "--muted": "#bc8686",
            "--brand": "#f97316",
            "--brand-2": "#ea580c",
            "--surface": "#4a2d22"
        }
    }
}

def get_palette_colors(palette_number: int) -> dict:
    """
    Get color definitions for a specific palette number
    
    Args:
        palette_number: Palette number (1-4)
        
    Returns:
        Dictionary of CSS variable names and their color values
        
    Raises:
        ValueError: If palette number is not valid
    """
    if palette_number not in COLOR_PALETTES:
        raise ValueError(f"Invalid palette number: {palette_number}. Must be 1-4.")
    
    return COLOR_PALETTES[palette_number]["colors"]

def get_palette_info(palette_number: int) -> dict:
    """
    Get full palette information including name and description
    
    Args:
        palette_number: Palette number (1-4)
        
    Returns:
        Dictionary with name, description, and colors
    """
    if palette_number not in COLOR_PALETTES:
        raise ValueError(f"Invalid palette number: {palette_number}. Must be 1-4.")
    
    return COLOR_PALETTES[palette_number]

def list_all_palettes() -> dict:
    """
    Get all available color palettes
    
    Returns:
        Dictionary of all color palettes
    """
    return COLOR_PALETTES

def generate_css_variables(palette_number: int) -> str:
    """
    Generate CSS variables string for a specific palette
    
    Args:
        palette_number: Palette number (1-4)
        
    Returns:
        CSS string with variable definitions
    """
    colors = get_palette_colors(palette_number)
    css_vars = []
    
    for var_name, color_value in colors.items():
        css_vars.append(f"  {var_name}: {color_value};")
    
    return "\n".join(css_vars)