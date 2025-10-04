#!/usr/bin/env python3
"""
Game content management module
Handles scanning, processing, and generating game-related content
with comprehensive security validation and sanitization
"""

import os
import re
import json
import html
import hashlib
import random
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from urllib.parse import urlparse
from .performance_logger import log_info, log_warn, log_error, log_success


class GameManager:
    """Manages game content scanning and processing with image validation"""
    
    def __init__(self, content_dir: str, site_url: str):
        self.content_dir = content_dir
        self.site_url = site_url
        self.missing_images = []  # Track missing images that cause games to be skipped
        self.image_fallbacks = {}  # Track fallback images used
        # Get the static directory path
        self.static_dir = Path(content_dir).parent / "static"
    
    def scan_games_content(self, default_embed_url: str = "about:blank", 
                          default_hero_image: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scan content_html/games/*.html and extract metadata.
        
        Args:
            default_embed_url: Default embed URL for games without one specified
            default_hero_image: Default hero image for games without one specified
            
        Returns:
            List of game dictionaries with metadata
        """
        games_dir = os.path.join(self.content_dir, "games")
        games = []
        
        if not os.path.isdir(games_dir):
            return games
            
        for fname in sorted(os.listdir(games_dir)):
            if not fname.lower().endswith(".html"):
                continue
                
            slug = os.path.splitext(fname)[0]
            path = os.path.join(games_dir, fname)
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    raw = f.read()
                
                # Extract title from first <h1> if present
                title = self._extract_title(raw, slug)
                
                # Parse optional meta comments
                embed_url = self._extract_embed_url(raw) or default_embed_url
                hero_image = self._extract_hero_image(raw) or default_hero_image
                
                # Parse JSON metadata block
                meta = self._extract_metadata(raw, fname)
                
                # Check if images exist - skip game if required images are missing
                hero_image_raw = meta.get("hero") or hero_image
                logo_image_raw = meta.get("logo")
                
                # Validate hero image (required)
                if hero_image_raw:
                    hero_valid = self._check_image_exists(hero_image_raw)
                    if not hero_valid:
                        log_warn("GameManager", f"Skipping game '{slug}' - missing hero image: {hero_image_raw}")
                        continue
                
                # Validate logo image if specified
                if logo_image_raw:
                    logo_valid = self._check_image_exists(logo_image_raw)
                    if not logo_valid:
                        log_warn("GameManager", f"Skipping game '{slug}' - missing logo image: {logo_image_raw}")
                        continue
                
                # Update meta with validated images
                if hero_image_raw:
                    meta["hero"] = hero_image_raw
                if logo_image_raw:
                    meta["logo"] = logo_image_raw
                
                games.append({
                    "slug": slug,
                    "title": meta.get("title") or title,
                    "content_html": raw,
                    "embed_url": meta.get("embed") or embed_url,
                    "hero_image": meta.get("hero") or hero_image_raw,
                    "description": meta.get("description"),
                    "meta": meta
                })
                
            except (OSError, IOError) as e:
                # File access errors (permissions, disk issues)
                log_warn("GameManager", f"Could not read game file {fname}: {e}")
            except UnicodeDecodeError as e:
                # File encoding issues
                log_warn("GameManager", f"Invalid encoding in game file {fname}: {e}")
            except Exception as e:
                # Catch any other parsing errors but log them specifically
                log_warn("GameManager", f"Failed parsing game file {fname}: {type(e).__name__}: {e}")
        
        log_info("GameManager", "Game Scan Summary:", "📊")
        log_info("GameManager", f"Total games found: {len(os.listdir(games_dir)) if os.path.isdir(games_dir) else 0}", "•")
        log_info("GameManager", f"Games with valid images: {len(games)}", "•")
        log_info("GameManager", f"Games skipped (missing images): {len(self.missing_images)}", "•")
                
        return games
    
    def _sanitize_game_metadata(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize game metadata to prevent XSS and injection attacks.
        
        Args:
            meta: Raw metadata dictionary
            
        Returns:
            Sanitized metadata dictionary
        """
        sanitized = {}
        
        for key, value in meta.items():
            if isinstance(value, str):
                # Escape HTML for text fields to prevent XSS
                if key in ['title', 'description', 'developer', 'publisher']:
                    sanitized[key] = html.escape(value, quote=True)
                # Validate URLs
                elif key in ['embed', 'link', 'website']:
                    if self._validate_game_url(value):
                        sanitized[key] = value
                    else:
                        log_warn("GameManager", f"Invalid URL in metadata: {key}={value}")
                # Validate image paths
                elif key in ['hero', 'logo', 'thumbnail', 'icon']:
                    if self._validate_image_path(value):
                        sanitized[key] = value
                    else:
                        log_warn("GameManager", f"Invalid image path in metadata: {key}={value}")
                else:
                    # For other string fields, basic sanitization
                    sanitized[key] = html.escape(value, quote=True)
            else:
                # Keep non-string values as is (numbers, booleans, etc.)
                sanitized[key] = value
        
        return sanitized
    
    def _validate_game_url(self, url: str) -> bool:
        """Validate a game URL to prevent XSS and ensure it's safe.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is safe, False otherwise
        """
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            # Check for dangerous schemes
            dangerous_schemes = ['javascript', 'data', 'vbscript', 'file']
            if parsed.scheme and parsed.scheme.lower() in dangerous_schemes:
                return False
            
            # Allow about:blank for iframe placeholder
            if url == "about:blank":
                return True
            
            # For other URLs, require http or https
            if parsed.scheme and parsed.scheme.lower() not in ['http', 'https', '']:
                return False
            
            # Check for XSS patterns in the URL
            xss_patterns = ['<script', 'javascript:', 'on\\w+\\s*=', '\\x00']
            for pattern in xss_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return False
            
            return True
            
        except (ValueError, AttributeError):
            return False
    
    def _validate_image_path(self, path: str) -> bool:
        """Validate an image path to ensure it's safe.
        
        Args:
            path: Image path to validate
            
        Returns:
            True if path is safe, False otherwise
        """
        if not path:
            return False
        
        # Check for path traversal attempts
        if '..' in path or path.startswith('/') or path.startswith('~'):
            return False
        
        # Check for null bytes
        if '\\x00' in path or '\0' in path:
            return False
        
        # Validate file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico']
        path_lower = path.lower()
        if not any(path_lower.endswith(ext) for ext in allowed_extensions):
            return False
        
        return True
    
    def _extract_title(self, html_content: str, fallback_slug: str) -> str:
        """Extract title from HTML content or generate from slug (with sanitization)"""
        m = re.search(r"<h1[^>]*>(.*?)</h1>", html_content, flags=re.IGNORECASE|re.DOTALL)
        if m:
            # Remove HTML tags and sanitize
            title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if title:
                # Escape HTML to prevent XSS
                return html.escape(title, quote=True)
        
        # Sanitize the fallback slug-based title
        title = fallback_slug.replace('-', ' ').replace('_', ' ').title()
        return html.escape(title, quote=True)
    
    def _extract_embed_url(self, html_content: str) -> Optional[str]:
        """Extract and validate embed URL from HTML comment"""
        m = re.search(r"<!--\s*embed:\s*(.*?)\s*-->", html_content, flags=re.IGNORECASE)
        if m:
            url = m.group(1).strip()
            # Validate the URL before returning
            if self._validate_game_url(url):
                return url
            else:
                log_warn("GameManager", f"Invalid embed URL found: {url}")
        return None
    
    def _extract_hero_image(self, html_content: str) -> Optional[str]:
        """Extract and validate hero image from HTML comment"""
        m = re.search(r"<!--\s*hero:\s*(.*?)\s*-->", html_content, flags=re.IGNORECASE)
        if m:
            image_path = m.group(1).strip()
            # Validate the image path before returning
            if self._validate_image_path(image_path):
                return image_path
            else:
                log_warn("GameManager", f"Invalid hero image path: {image_path}")
        return None
    
    def _extract_metadata(self, html_content: str, filename: str) -> Dict[str, Any]:
        """Extract and sanitize JSON metadata from HTML comment"""
        try:
            m = re.search(r"<!--\s*meta:\s*(\{[\s\S]*?\})\s*-->", html_content, flags=re.IGNORECASE)
            if m:
                raw_meta = json.loads(m.group(1))
                # Sanitize the metadata before returning
                return self._sanitize_game_metadata(raw_meta)
        except json.JSONDecodeError as e:
            # Specifically handle JSON parsing errors with detailed context
            log_warn("GameManager", f"Invalid JSON syntax in {filename} metadata: {e}")
        except (ValueError, TypeError) as e:
            # Handle JSON structure issues (wrong types, etc.)
            log_warn("GameManager", f"Invalid meta data structure in {filename}: {e}")
        return {}
    
    def generate_game_rating(self, game_slug: str, custom_rating: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate deterministic rating for a game based on its slug.
        
        Args:
            game_slug: The game's slug for deterministic generation
            custom_rating: Optional custom rating to use instead
            
        Returns:
            Dictionary with ratingValue and ratingCount
        """
        if custom_rating:
            return custom_rating
            
        try:
            h = int(hashlib.sha256(game_slug.encode('utf-8')).hexdigest()[:8], 16)
        except (ValueError, UnicodeEncodeError) as e:
            # Handle encoding errors or conversion errors gracefully
            # Fallback to simple checksum if hashing fails
            h = sum(ord(c) for c in game_slug)
        
        # Rating between 3.0 and 4.9
        rating_value = round(3.0 + ((h % 200) / 100.0), 1)
        if rating_value > 5.0:
            rating_value = 5.0
            
        # Rating count between 250 and 5250
        rating_count = 250 + (h % 5001)
        
        return {
            "ratingValue": rating_value,
            "ratingCount": rating_count
        }
    
    def get_random_games_for_widget(self, games: List[Dict], exclude_slug: Optional[str] = None, 
                                   max_games: int = 12) -> List[Dict[str, str]]:
        """
        Get a random selection of games for the widget.
        
        Args:
            games: List of all games
            exclude_slug: Game slug to exclude (current game page)
            max_games: Maximum number of games to return
            
        Returns:
            List of games formatted for the widget
        """
        if not games or not isinstance(games, list):
            return []
        
        # Filter out current game and ensure valid games
        available_games = [
            g for g in games 
            if isinstance(g, dict) and g.get("slug") and g.get("title")
        ]
        
        if exclude_slug:
            available_games = [g for g in available_games if g["slug"] != exclude_slug]
        
        if not available_games:
            return []
        
        # Select random games
        try:
            random_games = random.sample(available_games, min(max_games, len(available_games)))
        except (ValueError, TypeError):
            random_games = available_games[:max_games]
        
        # Format for widget
        result = []
        for g in random_games:
            if not g.get('slug') or not g.get('title'):
                continue
                
            # Get logo path
            logo = g.get('meta', {}).get('logo')
            if logo:
                image_path = f"/assets/images/{logo[4:]}" if logo.startswith('img/') else f"/assets/images/{logo}"
            else:
                hero = g.get('hero_image', 'placeholder.webp')
                image_path = f"/assets/images/{hero}"
            
            result.append({
                "title": g.get("title", "Untitled Game"),
                "url": f"/games/{g.get('slug')}/",
                "image": image_path
            })
        
        return result
    
    def _check_image_exists(self, image_path: str) -> bool:
        """
        Check if an image file exists in the static directory.
        
        Args:
            image_path: The image path to check
            
        Returns:
            True if image exists, False otherwise
        """
        if not image_path:
            return False
        
        # Clean up the image path
        if image_path.startswith('img/'):
            image_filename = image_path[4:]
        else:
            image_filename = os.path.basename(image_path)
        
        # Check if the image exists in static/img
        image_file = self.static_dir / "img" / image_filename
        
        if not image_file.exists():
            # Track missing image for reporting
            self.missing_images.append(image_filename)
            return False
        
        return True
    
    def get_all_games_for_widget(self, games: List[Dict], exclude_slug: Optional[str] = None,
                                max_games: int = 60) -> List[Dict[str, str]]:
        """
        Get all games for the icon widget.
        
        Args:
            games: List of all games
            exclude_slug: Game slug to exclude (current game page)
            max_games: Maximum number of games to return
            
        Returns:
            List of games formatted for the widget
        """
        if not games or not isinstance(games, list):
            return []
        
        # Filter and validate games
        available_games = [
            g for g in games 
            if isinstance(g, dict) and g.get("slug") and g.get("title")
        ]
        
        if exclude_slug:
            available_games = [g for g in available_games if g["slug"] != exclude_slug]
        
        # Format for widget
        result = []
        for g in available_games[:max_games]:
            if not g.get('slug') or not g.get('title'):
                continue
                
            # Get logo path
            logo = g.get('meta', {}).get('logo')
            if logo:
                image_path = f"/assets/images/{logo[4:]}" if logo.startswith('img/') else f"/assets/images/{logo}"
            else:
                hero = g.get('hero_image', 'gamelogo.webp')
                image_path = f"/assets/images/{hero[4:]}" if hero.startswith('img/') else f"/assets/images/{hero}"
            
            result.append({
                "title": g.get("title", "Untitled Game"),
                "url": f"/games/{g.get('slug')}/",
                "image": image_path
            })
        
        return result
    
    def _report_missing_images(self) -> None:
        """Report all missing images found during scanning."""
        log_warn("GameManager", f"Found {len(self.missing_images)} missing images:", "⚠️")
        
        # Group by game for cleaner output
        games_with_missing = {}
        for item in self.missing_images:
            game = item["game"]
            if game not in games_with_missing:
                games_with_missing[game] = []
            games_with_missing[game].append(item)
        
        for game, issues in games_with_missing.items():
            log_info("GameManager", f"Game: {game}", "📎")
            for issue in issues:
                log_error("GameManager", f"Missing {issue['type']}: {issue['missing_file']}", "❌")
                if issue['game'] in self.image_fallbacks:
                    fallback_info = self.image_fallbacks.get(f"{game}_{issue['type']}")
                    if fallback_info:
                        log_success("GameManager", f"Using fallback: {fallback_info['fallback']}", "✅")
        
        log_info("GameManager", "Image Validation Summary:", "📊")
        log_info("GameManager", f"Total missing: {len(self.missing_images)}", "•")
        log_info("GameManager", f"Fallbacks used: {len(self.image_fallbacks)}", "•")
        log_info("GameManager", f"Affected games: {len(games_with_missing)}", "•")