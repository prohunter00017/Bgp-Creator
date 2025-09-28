#!/usr/bin/env python3
"""
Page building module
Handles HTML page generation and template rendering
"""

import os
import re
from typing import Dict, List, Any, Optional, Tuple
from jinja2 import Environment, Template
from .url_utils import URLBuilder
from .performance_logger import (
    logger, time_operation, log_info, log_success, log_warn, log_error,
    log_phase_start, log_phase_complete, update_stats
)


class PageBuilder:
    """Handles page generation and template rendering"""
    
    def __init__(self, env: Environment, output_dir: str, site_url: Optional[str] = None):
        self.env = env
        self.output_dir = output_dir
        self.url_builder = URLBuilder(site_url) if site_url else None
    
    def generate_page(self, template_name: str, context: Dict[str, Any], 
                     output_path: str, subdir: Optional[str] = None) -> None:
        """
        Generate a single page from template.
        
        Args:
            template_name: Name of the template file
            context: Template context dictionary
            output_path: Output file path
            subdir: Optional subdirectory for organization
        """
        with time_operation("page_generation", {"template": template_name, "page": output_path}):
            try:
                template = self.env.get_template(template_name)
                html_content = template.render(**context)
                
                # Ensure output directory exists
                if subdir:
                    full_dir = os.path.join(self.output_dir, subdir)
                    os.makedirs(full_dir, exist_ok=True)
                    full_path = os.path.join(full_dir, output_path)
                else:
                    full_path = os.path.join(self.output_dir, output_path)
                
                # Resolve asset links in all pages
                html_content = self.resolve_asset_links(html_content)
                
                # Write with atomic operation
                temp_file = f"{full_path}.tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                os.rename(temp_file, full_path)
                
                display_path = f"{subdir}/{output_path}" if subdir else output_path
                log_success("PageBuilder", f"Generated page: {display_path}", "📄")
                update_stats("page_generation", files_processed=1)
                
            except (OSError, IOError) as e:
                log_error("PageBuilder", f"File system error generating page {output_path}: {e}", "⚠️")
                update_stats("page_generation", files_error=1)
                raise
            except Exception as e:
                log_error("PageBuilder", f"Template error generating page {output_path}: {e}", "⚠️")
                update_stats("page_generation", files_error=1)
                raise
    
    def generate_game_page(self, game: Dict[str, Any], template: Template,
                          context_base: Dict[str, Any], games_list: List[Dict],
                          breadcrumbs: List[Dict], subdir: str = "games") -> None:
        """
        Generate a single game page.
        
        Args:
            game: Game data dictionary
            template: Jinja2 template object
            context_base: Base context dictionary
            games_list: List of all games for sidebar
            breadcrumbs: Breadcrumb navigation data
            subdir: Output subdirectory
        """
        try:
            page_key = game["slug"]
            
            # Build complete context
            context = {
                **context_base,
                "page_title": game["title"],
                "page_description": game.get("description", ""),
                "canonical_url": self.url_builder.get_canonical_url(f"{subdir}/{page_key}") if self.url_builder else f"{context_base['site_url']}{subdir}/{page_key}/",
                "current_page": page_key,
                "breadcrumbs": breadcrumbs,
                "game_name": game["title"],
                "game_embed": {"url": game["embed_url"]},
                "game_url": game["embed_url"],
                "hero_image": game["hero_image"],
                "custom_html_content": game["content_html"],
                "games": games_list,
                "sidebar_title": "More Games",
                # Add ad placement configuration
                "ads_enabled": context_base.get("ads_enabled", False),
                "ad_networks": context_base.get("ad_networks", {}),
                "ad_sizes": context_base.get("ad_sizes", {})
            }
            
            # Render template
            html_content = template.render(**context)
            
            # Resolve asset links in rendered content
            html_content = self.resolve_asset_links(html_content)
            
            # Get clean URL output path for game page
            full_output_path, _ = self.get_page_output_path(page_key, is_game_page=True)
            
            # Ensure output directory exists for clean URLs
            os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
            
            # Write file to clean URL structure
            temp_file = f"{full_output_path}.tmp"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            os.rename(temp_file, full_output_path)
            
            # Display relative path for logging
            rel_path = os.path.relpath(full_output_path, self.output_dir)
            log_success("PageBuilder", f"Generated game page: {rel_path}", "📄")
            update_stats("page_generation", files_processed=1)
            
        except (OSError, IOError) as e:
            log_error("PageBuilder", f"File system error generating game page {game.get('slug')}: {e}", "⚠️")
            update_stats("page_generation", files_error=1)
        except Exception as e:
            log_error("PageBuilder", f"Template error generating game page {game.get('slug')}: {e}", "⚠️")
            update_stats("page_generation", files_error=1)
    
    def generate_games_listing(self, games: List[Dict], context_base: Dict[str, Any]) -> None:
        """
        Generate the games listing page.
        
        Args:
            games: List of all games
            context_base: Base context dictionary
        """
        try:
            # Try to get the games list template, fallback to page template
            template = None
            for template_name in ["games_list.html", "page.html"]:
                try:
                    template = self.env.get_template(template_name)
                    break
                except Exception:
                    continue
            
            if not template:
                log_warn("PageBuilder", "No suitable template found for games listing", "⚠️")
                return
            
            breadcrumbs = [
                {"title": "Home", "url": "/"},
                {"title": "Games", "url": None}
            ]
            
            context = {
                **context_base,
                "page_title": "Games",
                "page_description": "Browse all games.",
                "canonical_url": self.url_builder.get_canonical_url("games") if self.url_builder else f"{context_base['site_url']}games/",
                "current_page": "games",
                "breadcrumbs": breadcrumbs,
                "games": [{
                    "title": g["title"],
                    "url": f"/games/{g['slug']}/",
                    "image": self._format_image_path(g.get("meta", {}).get("logo") or g["hero_image"])
                } for g in games],
                "sidebar_title": "More Games"
            }
            
            html_content = template.render(**context)
            
            output_file = os.path.join(self.output_dir, "games", "index.html")
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            temp_file = f"{output_file}.tmp"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            os.rename(temp_file, output_file)
            
            log_success("PageBuilder", "Generated games/index.html listing", "📄")
            update_stats("page_generation", files_processed=1)
            
            # Clean up legacy games.html file to prevent duplicate content
            legacy_games_file = os.path.join(self.output_dir, "games.html")
            if os.path.exists(legacy_games_file):
                os.remove(legacy_games_file)
                log_info("PageBuilder", "Cleaned up legacy file: games.html", "🧹")
            
        except (OSError, IOError) as e:
            log_error("PageBuilder", f"File system error generating games listing: {e}", "⚠️")
            update_stats("page_generation", files_error=1)
        except Exception as e:
            log_error("PageBuilder", f"Template error generating games listing: {e}", "⚠️")
            update_stats("page_generation", files_error=1)
    
    def get_page_output_path(self, page_key: str, is_game_page: bool = False) -> Tuple[str, Optional[str]]:
        """
        Get the output path for a page with clean URL structure (directories with index.html).
        
        Args:
            page_key: The page identifier
            is_game_page: Whether this is a game page
            
        Returns:
            Tuple of (full_output_path, subdirectory)
        """
        if is_game_page:
            subdir = "games"
            # Create games/game-name/index.html for clean URLs
            output_file = os.path.join(self.output_dir, subdir, page_key, "index.html")
            return output_file, subdir
        elif page_key == "index":
            return os.path.join(self.output_dir, "index.html"), None
        elif page_key in ["about-us", "contact"]:
            # Create clean URLs: /about-us/ and /contact/
            output_file = os.path.join(self.output_dir, page_key, "index.html")
            return output_file, None
        elif page_key in ["privacy-policy", "terms-of-service", "cookies-policy", "dmca", "parents-information"]:
            # Create clean URLs: /privacy-policy/, /terms-of-service/, etc.
            output_file = os.path.join(self.output_dir, page_key, "index.html")
            return output_file, None
        elif page_key == "games":
            # Create clean URL: /games/
            output_file = os.path.join(self.output_dir, "games", "index.html")
            return output_file, None
        else:
            # For any other pages, create clean URLs
            output_file = os.path.join(self.output_dir, page_key, "index.html")
            return output_file, None
    
    def _format_image_path(self, image_path: str) -> str:
        """
        Format image path to use correct asset directory.
        
        Args:
            image_path: Original image path
            
        Returns:
            Properly formatted image path
        """
        if not image_path:
            return "/assets/images/gamelogo.webp"
            
        # Use URLBuilder's normalize_asset_path if available
        if self.url_builder:
            return self.url_builder.normalize_asset_path(image_path)
        
        # Fallback to original logic
        if image_path.startswith('img/'):
            return f"/assets/images/{image_path[4:]}"
        elif image_path.startswith('/img/'):
            return f"/assets/images/{image_path[5:]}"
        elif image_path.startswith('/assets/'):
            return image_path
        else:
            return f"/assets/images/{image_path}"
    
    def generate_page_direct(self, template_name: str, context: Dict[str, Any], full_output_path: str) -> None:
        """
        Generate a page directly to a specified full path (for clean URLs).
        
        Args:
            template_name: Name of the template file
            context: Template context dictionary  
            full_output_path: Complete path where the file should be written
        """
        with time_operation("page_generation", {"template": template_name, "page": full_output_path}):
            try:
                template = self.env.get_template(template_name)
                html_content = template.render(**context)
                
                # Resolve asset links in all pages
                html_content = self.resolve_asset_links(html_content)
                
                # Write with atomic operation
                temp_file = f"{full_output_path}.tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                os.rename(temp_file, full_output_path)
                
                # Display relative path for logging
                rel_path = os.path.relpath(full_output_path, self.output_dir)
                log_success("PageBuilder", f"Generated page: {rel_path}", "📄")
                update_stats("page_generation", files_processed=1)
                
            except (OSError, IOError) as e:
                log_error("PageBuilder", f"File system error generating page {full_output_path}: {e}", "⚠️")
                update_stats("page_generation", files_error=1)
                raise
            except Exception as e:
                log_error("PageBuilder", f"Template error generating page {full_output_path}: {e}", "⚠️")
                update_stats("page_generation", files_error=1)
                raise

    def generate_error_pages(self, base_context: Dict[str, Any]):
        """
        Generate static error pages (404.html, offline.html) for production hosting.
        These are crucial for proper PWA functionality and error handling.
        
        Args:
            base_context: Base context dictionary with all site configuration
        """
        from datetime import datetime
        log_info("PageBuilder", "Generating error and offline pages...", "🚨")
        
        # Generate 404 error page - merge base context with error-specific values
        error_context = {**base_context}
        error_context.update({
            'page_title': '404 - Page Not Found',
            'page_description': 'The page you are looking for cannot be found.',
            'current_page': '404',
            'content': '<p>The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.</p>',
            'canonical_url': self.url_builder.get_canonical_url("404.html") if self.url_builder else f"{base_context.get('site_url', '/')}404.html",
            'seo_context': {
                'robots': 'noindex, nofollow',
                'type': 'error'
            }
        })
        
        # Generate 404.html in root for standard hosting
        self.generate_page_direct('error.html', error_context, os.path.join(self.output_dir, '404.html'))
        
        # Generate offline page for PWA - merge base context with offline-specific values
        offline_context = {**base_context}
        offline_context.update({
            'page_title': 'You are Offline',
            'page_description': 'Please check your internet connection and try again.',
            'current_page': 'offline',
            'content': '<p>It looks like you have lost your internet connection. Please check your connection and try again.</p>',
            'canonical_url': self.url_builder.get_canonical_url("offline.html") if self.url_builder else f"{base_context.get('site_url', '/')}offline.html",
            'seo_context': {
                'robots': 'noindex, nofollow',
                'type': 'offline'
            }
        })
        
        # Generate offline.html for PWA service worker
        self.generate_page_direct('offline.html', offline_context, os.path.join(self.output_dir, 'offline.html'))
        
        # Also generate in offline directory for clean URL access
        offline_dir = os.path.join(self.output_dir, 'offline')
        os.makedirs(offline_dir, exist_ok=True)
        self.generate_page_direct('offline.html', offline_context, os.path.join(offline_dir, 'index.html'))
        
        log_success("PageBuilder", "Generated error pages: 404.html, offline.html", "✅")
    
    def resolve_asset_links(self, html_content: str) -> str:
        """
        Resolve asset links in HTML content using optimized regex patterns.
        
        Args:
            html_content: HTML content with asset references
            
        Returns:
            HTML with resolved asset links
        """
        # Compile regex patterns for better performance (cached)
        if not hasattr(self, '_asset_patterns'):
            self._asset_patterns = [
                (re.compile(r'(src|href)="img/', re.IGNORECASE), r'\1="/assets/images/'),
                (re.compile(r'(src|href)="css/', re.IGNORECASE), r'\1="/assets/css/'),
                (re.compile(r'(src|href)="js/', re.IGNORECASE), r'\1="/assets/js/'),
                (re.compile(r'url\("?img/', re.IGNORECASE), 'url("/assets/images/'),
                (re.compile(r'url\("?css/', re.IGNORECASE), 'url("/assets/css/'),
                (re.compile(r'url\("?js/', re.IGNORECASE), 'url("/assets/js/'),
            ]
        
        # Apply compiled patterns for better performance
        for pattern, replacement in self._asset_patterns:
            html_content = pattern.sub(replacement, html_content)
        
        return html_content