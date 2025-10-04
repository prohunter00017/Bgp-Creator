#!/usr/bin/env python3
"""
CSS Processor for Color Palette System
Handles injecting color palettes into CSS templates
"""

import os
import re
from .color_palettes import get_palette_colors, get_palette_info

def process_css_with_palette(css_content: str, palette_number: int) -> str:
    """
    Process CSS content and inject color palette variables
    
    Args:
        css_content: Original CSS content as string
        palette_number: Color palette number (1-4)
        
    Returns:
        Processed CSS content with palette colors injected
    """
    # Get the colors for the selected palette
    palette_colors = get_palette_colors(palette_number)
    palette_info = get_palette_info(palette_number)
    
    # Create the color variables section
    color_variables = []
    color_variables.append(f"  /* {palette_info['name']} Palette - {palette_info['description']} */")
    
    for var_name, color_value in palette_colors.items():
        color_variables.append(f"  {var_name}: {color_value};")
    
    color_variables_section = "\n".join(color_variables)
    
    # Pattern to match the color system section in CSS
    color_section_pattern = r'(/\* Color System \*/.*?)(?=/\* [^C]|\n  /\* [A-Z])'
    
    # Replace the color system section with our palette colors
    new_css = re.sub(
        color_section_pattern,
        f"/* Color System */\n{color_variables_section}\n\n  ",
        css_content,
        flags=re.DOTALL
    )
    
    # If the pattern didn't match, try to replace just the :root section
    if new_css == css_content:
        # Alternative approach: replace content within :root {...}
        root_pattern = r'(:root\s*{)(.*?)(})'
        
        def replace_root_content(match):
            root_start = match.group(1)
            root_end = match.group(3)
            
            # Extract non-color content (spacing, typography, etc.)
            original_content = match.group(2)
            
            # Keep sections that are not color-related
            sections_to_keep = []
            for line in original_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('/*') and not line.startswith('--bg') and not line.startswith('--text') and not line.startswith('--brand') and not line.startswith('--accent'):
                    # Keep non-color variables
                    if '--' in line and not any(color_var in line for color_var in ['bg', 'text', 'brand', 'accent']):
                        sections_to_keep.append(f"  {line}")
                elif line.startswith('/*') and 'Color System' not in line:
                    sections_to_keep.append(f"  {line}")
            
            # Build new content
            new_content = [
                "",
                color_variables_section,
                "",
                "\n".join(sections_to_keep) if sections_to_keep else "",
                ""
            ]
            
            return root_start + "\n".join(new_content) + root_end
        
        new_css = re.sub(root_pattern, replace_root_content, css_content, flags=re.DOTALL)
    
    return new_css

def generate_css_for_site(template_css_path: str, output_css_path: str, palette_number: int) -> bool:
    """
    Generate site-specific CSS file with selected color palette
    
    Args:
        template_css_path: Path to the template CSS file
        output_css_path: Path where the processed CSS should be saved
        palette_number: Color palette number (1-4)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read the template CSS
        with open(template_css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Process the CSS with the selected palette
        processed_css = process_css_with_palette(css_content, palette_number)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_css_path), exist_ok=True)
        
        # Write the processed CSS
        with open(output_css_path, 'w', encoding='utf-8') as f:
            f.write(processed_css)
        
        return True
    
    except FileNotFoundError as e:
        print(f"❌ CSS template file not found: {template_css_path} - {e}")
        return False
    except PermissionError as e:
        print(f"❌ Permission denied writing CSS: {output_css_path} - {e}")
        return False
    except OSError as e:
        print(f"❌ File system error processing CSS: {e}")
        return False
    except UnicodeDecodeError as e:
        print(f"❌ Invalid encoding in CSS file: {e}")
        return False
    except ValueError as e:
        print(f"❌ Invalid palette number or CSS format: {e}")
        return False