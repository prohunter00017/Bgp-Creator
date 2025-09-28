#!/usr/bin/env python3
"""
Game content management module
Handles scanning, processing, and generating game-related content
"""

import os
import re
import json
import hashlib
import random
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path


class GameManager:
    """Manages game content scanning and processing with image validation"""
    
    def __init__(self, content_dir: str, site_url: str):
        self.content_dir = content_dir
        self.site_url = site_url
        self.missing_images = []  # Track missing images that cause games to be skipped
        # Get the static directory path
        self.static_dir = Path(content_dir).parent / "static"
    
    def scan_games_content(self, default_embed_url: str = "about:blank", 
                          default_hero_image: str = None) -> List[Dict[str, Any]]:
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
                        print(f"  ⚠️  Skipping game '{slug}' - missing hero image: {hero_image_raw}")
                        continue
                
                # Validate logo image if specified
                if logo_image_raw:
                    logo_valid = self._check_image_exists(logo_image_raw)
                    if not logo_valid:
                        print(f"  ⚠️  Skipping game '{slug}' - missing logo image: {logo_image_raw}")
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
                
            except Exception as e:
                print(f"⚠️  Failed parsing game file {fname}: {e}")
        
        print(f"\n📊 Game Scan Summary:")
        print(f"  • Total games found: {len(os.listdir(games_dir)) if os.path.isdir(games_dir) else 0}")
        print(f"  • Games with valid images: {len(games)}")
        print(f"  • Games skipped (missing images): {len(self.missing_images)}")
                
        return games
    
    def _extract_title(self, html_content: str, fallback_slug: str) -> str:
        """Extract title from HTML content or generate from slug"""
        m = re.search(r"<h1[^>]*>(.*?)</h1>", html_content, flags=re.IGNORECASE|re.DOTALL)
        if m:
            title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if title:
                return title
        return fallback_slug.replace('-', ' ').replace('_', ' ').title()
    
    def _extract_embed_url(self, html_content: str) -> Optional[str]:
        """Extract embed URL from HTML comment"""
        m = re.search(r"<!--\s*embed:\s*(.*?)\s*-->", html_content, flags=re.IGNORECASE)
        return m.group(1).strip() if m else None
    
    def _extract_hero_image(self, html_content: str) -> Optional[str]:
        """Extract hero image from HTML comment"""
        m = re.search(r"<!--\s*hero:\s*(.*?)\s*-->", html_content, flags=re.IGNORECASE)
        return m.group(1).strip() if m else None
    
    def _extract_metadata(self, html_content: str, filename: str) -> Dict[str, Any]:
        """Extract JSON metadata from HTML comment"""
        try:
            m = re.search(r"<!--\s*meta:\s*(\{[\s\S]*?\})\s*-->", html_content, flags=re.IGNORECASE)
            if m:
                return json.loads(m.group(1))
        except Exception as e:
            print(f"⚠️  Ignoring invalid meta JSON in {filename}: {e}")
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
        except Exception:
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
        print(f"\n⚠️  Found {len(self.missing_images)} missing images:")
        
        # Group by game for cleaner output
        games_with_missing = {}
        for item in self.missing_images:
            game = item["game"]
            if game not in games_with_missing:
                games_with_missing[game] = []
            games_with_missing[game].append(item)
        
        for game, issues in games_with_missing.items():
            print(f"  📎 Game: {game}")
            for issue in issues:
                print(f"    ❌ Missing {issue['type']}: {issue['missing_file']}")
                if issue['game'] in self.image_fallbacks:
                    fallback_info = self.image_fallbacks.get(f"{game}_{issue['type']}")
                    if fallback_info:
                        print(f"    ✅ Using fallback: {fallback_info['fallback']}")
        
        print(f"\n📊 Image Validation Summary:")
        print(f"  • Total missing: {len(self.missing_images)}")
        print(f"  • Fallbacks used: {len(self.image_fallbacks)}")
        print(f"  • Affected games: {len(games_with_missing)}")