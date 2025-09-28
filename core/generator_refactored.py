#!/usr/bin/env python3
"""
Refactored Site Generator - Clean Architecture
Main orchestrator that uses specialized modules for different responsibilities
"""

import os
import shutil
from datetime import datetime
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape, ChoiceLoader
except ImportError as e:
    raise ImportError("Jinja2 is required. Install with: pip install Jinja2") from e

from .site_loader import load_site_settings, get_site_paths, get_site_output_dir
from .config import SiteConfig
from .game_manager import GameManager
from .page_builder import PageBuilder
from .seo_manager import SEOManager
from .asset_manager import AssetManager
from .optimizer import ImageOptimizer
from .build_cache import BuildCache
from .site_crawler import SiteCrawler
from .performance_logger import (
    logger, time_operation, log_info, log_success, log_warn, log_error,
    log_phase_start, log_phase_complete, update_stats, print_build_summary
)


class SiteGenerator:
    """Main site generator orchestrating all components"""
    
    def __init__(self, template_dir="templates", output_dir=None, site_url=None, language=None, site=None, force=False):
        """Initialize the site generator with all necessary components"""
        
        # Store site parameter for multi-site support
        self.site = site
        self.force = force
        
        # Load site-specific settings and paths
        self.site_settings = load_site_settings(site)
        self.site_paths = get_site_paths(site)
        
        # Set up directories
        project_root = self.site_paths["project_root"]
        self.template_dir = template_dir if os.path.isabs(template_dir) else os.path.join(project_root, template_dir)
        self.output_dir = get_site_output_dir(site, output_dir)
        self.content_dir = self.site_paths["content_dir"]
        self.static_dir = self.site_paths["static_dir"]
        
        # Language configuration (simplified to English)
        self.language = "en-US"
        
        # Override site_url from settings if not provided
        if not site_url and hasattr(self.site_settings, 'SITE_URL'):
            site_url = self.site_settings.SITE_URL
        
        # Create configuration with site-specific settings
        # Ad configuration is now handled inside SiteConfig class
        self.config = SiteConfig(language_code=self.language, site=self.site)
        
        # Update site URL if provided
        if site_url:
            self.config.update_site_url(site_url)
        
        log_info("SiteGenerator", f"Using site URL: {self.config.site_url}", "🌐")
        log_info("SiteGenerator", f"Using language: {self.language}", "🌐")
        
        if site:
            log_info("SiteGenerator", f"Site: {site}", "🏢")
            log_info("SiteGenerator", f"Content: {self.content_dir}", "📁")
            log_info("SiteGenerator", f"Static: {self.static_dir}", "📁")
            log_info("SiteGenerator", f"Output: {self.output_dir}", "📁")
        
        # Setup Jinja2 environment
        self.env = self._setup_jinja_environment()
        
        # Initialize build cache for incremental builds first (needed by managers)
        cache_file = os.path.join(self.output_dir, ".build_cache.json")
        self.build_cache = BuildCache(cache_file)
        
        # Initialize managers (now they can use build_cache)
        self._initialize_managers()
        
        # Setup file tracking
        self._setup_file_tracking()
    
    def _setup_jinja_environment(self):
        """Setup Jinja2 environment with template loaders"""
        template_loaders = []
        
        # Check for site-specific templates first
        if self.site:
            site_template_dir = os.path.join(self.site_paths["site_root"], "templates")
            if os.path.exists(site_template_dir):
                template_loaders.append(FileSystemLoader(site_template_dir))
                log_info("SiteGenerator", f"Site-specific templates found: {site_template_dir}", "📄")
        
        # Always include shared templates as fallback
        template_loaders.append(FileSystemLoader(self.template_dir))
        
        env = Environment(
            loader=ChoiceLoader(template_loaders) if len(template_loaders) > 1 else template_loaders[0],
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add translate filter - just returns the default value for now
        def translate_filter(key, default=None):
            return default if default else key
        env.filters['translate'] = translate_filter
        
        return env
    
    def _initialize_managers(self):
        """Initialize all manager components"""
        self.game_manager = GameManager(self.content_dir, self.config.site_url)
        self.page_builder = PageBuilder(self.env, self.output_dir, self.config.site_url)
        self.seo_manager = SEOManager(self.config.site_url, self.config.site_name, self.output_dir)
        self.asset_manager = AssetManager(self.static_dir, self.output_dir, build_cache=self.build_cache)
        self.image_optimizer = ImageOptimizer(self.static_dir, self.output_dir, build_cache=self.build_cache)
    
    def _setup_file_tracking(self):
        """Setup file tracking for incremental builds"""
        with time_operation("file_tracking_setup"):
            log_phase_start("SiteGenerator", "file tracking setup", "📋")
            
            total_files = 0
            
            # Track content HTML files
            if os.path.exists(self.content_dir):
                content_files = self.build_cache.scan_directory(
                    self.content_dir, 
                    patterns=['*.html'], 
                    category='content'
                )
                total_files += len(content_files)
                log_info("SiteGenerator", f"Tracking {len(content_files)} content files", "📄")
            
            # Track static files
            if os.path.exists(self.static_dir):
                static_files = self.build_cache.scan_directory(
                    self.static_dir, 
                    patterns=['*.css', '*.js', '*.png', '*.jpg', '*.jpeg', '*.webp', '*.svg', '*.ico'], 
                    category='static'
                )
                total_files += len(static_files)
                log_info("SiteGenerator", f"Tracking {len(static_files)} static files", "📁")
            
            # Track template files
            if os.path.exists(self.template_dir):
                template_files = self.build_cache.scan_directory(
                    self.template_dir, 
                    patterns=['*.html'], 
                    category='templates'
                )
                total_files += len(template_files)
                log_info("SiteGenerator", f"Tracking {len(template_files)} template files", "📄")
            
            # Track configuration files
            config_files = []
            if hasattr(self.site_settings, '__file__'):
                config_files.append(self.site_settings.__file__)
            
            self.build_cache.track_files(config_files, category='config')
            if config_files:
                total_files += len(config_files)
                log_info("SiteGenerator", f"Tracking {len(config_files)} config files", "⚙️")
            
            update_stats("file_tracking", files_processed=total_files)
    
    def generate_site(self):
        """Generate the complete website with incremental build support"""
        overall_timer = logger.start_timing("overall_build")
        log_phase_start("SiteGenerator", "website generation", "🚀")
        start_time = datetime.now()
        
        try:
            # Create output directory
            with time_operation("output_directory_setup"):
                os.makedirs(self.output_dir, exist_ok=True)
                log_info("SiteGenerator", "Output directory ready", "📁")
            
            # Process CSS with color palette from site settings
            templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
            templates_css = os.path.join(templates_dir, 'styles.css')
            if os.path.exists(templates_css):
                # Copy to assets/css directory (proper location for CSS files)
                output_css_dir = os.path.join(self.output_dir, 'assets', 'css')
                os.makedirs(output_css_dir, exist_ok=True)
                output_css = os.path.join(output_css_dir, 'styles.css')
                
                # Get color palette from site settings (default to palette 1)
                color_palette = getattr(self.site_settings, 'COLOR_PALETTE', 1)
                
                # Import and use CSS processor
                from .css_processor import generate_css_for_site
                if generate_css_for_site(templates_css, output_css, color_palette):
                    from .color_palettes import get_palette_info
                    palette_info = get_palette_info(color_palette)
                    log_info("SiteGenerator", f"Generated styles.css with {palette_info['name']} palette", "🎨")
                else:
                    # Fallback to simple copy if processing fails
                    shutil.copy2(templates_css, output_css)
                    log_info("SiteGenerator", "Copied styles.css (fallback)", "⚠️")
            
            # Generate service worker from template
            sw_template = os.path.join(templates_dir, 'sw.js')
            if os.path.exists(sw_template):
                with open(sw_template, 'r', encoding='utf-8') as f:
                    sw_content = f.read()
                # Replace placeholders with site-specific values
                cache_name = self.config.site_name.lower().replace(' ', '-')
                sw_content = sw_content.replace('{{ site_name }}', self.config.site_name)
                sw_content = sw_content.replace('{{ cache_name }}', cache_name)
                # Write to output root
                with open(os.path.join(self.output_dir, 'sw.js'), 'w', encoding='utf-8') as f:
                    f.write(sw_content)
                log_info("SiteGenerator", "Generated service worker from template", "✅")
            
            # Check if any files have changed
            if not self.force:
                with time_operation("change_detection"):
                    log_info("SiteGenerator", "Checking for file changes...", "🔍")
                    self.build_cache.print_cache_stats()
            
            # Check for static file changes and optimize images
            static_changed = self.build_cache.has_changes(category='static', force=self.force)
            if static_changed:
                static_timer = logger.start_timing("static_processing")
                
                # Image optimization
                log_phase_start("SiteGenerator", "image optimization", "🖼️")
                self._optimize_images()
                
                # Copy static files
                log_phase_start("SiteGenerator", "static file copying", "📄")
                self.asset_manager.copy_static_files(force=self.force)
                
                # Optimize assets (CSS/JS minification)
                log_phase_start("SiteGenerator", "asset optimization", "🔧")
                self.asset_manager.optimize_assets()
                
                # Update cache for static files
                self.build_cache.update_file_cache(self.build_cache.file_categories['static'])
                
                static_duration = logger.stop_timing(static_timer)
                log_phase_complete("SiteGenerator", "static processing", static_duration or 0.0, "✅")
            else:
                log_info("SiteGenerator", "Skipping static file processing - no changes detected", "⚡")
                update_stats("static_processing", cache_hits=1)
            
            # Check for content changes
            content_changed = self.build_cache.has_changes(category='content', force=self.force)
            template_changed = self.build_cache.has_changes(category='templates', force=self.force)
            config_changed = self.build_cache.has_changes(category='config', force=self.force)
            
            pages_need_rebuild = content_changed or template_changed or config_changed or self.force
            
            if pages_need_rebuild:
                pages_timer = logger.start_timing("page_generation")
                
                # Scan games content
                with time_operation("games_content_scan"):
                    log_info("SiteGenerator", "Scanning games content...", "🎮")
                    games = self.game_manager.scan_games_content(
                        default_embed_url=self.config.seo_config.get("game_embed", {}).get("url", "about:blank"),
                        default_hero_image=self.config.get_dynamic_hero_image()
                    )
                    self._games = games
                
                # Generate pages
                pages = self._get_pages_from_config()
                log_info("SiteGenerator", f"Generating {len(pages)} pages...", "📝")
                
                with time_operation("static_pages_generation", {"page_count": len(pages)}):
                    for i, (page_key, template_name) in enumerate(pages, 1):
                        log_info("SiteGenerator", f"Processing {page_key} ({i}/{len(pages)})", "📄")
                        self._generate_page(page_key, template_name)
                
                # Generate game pages and listing
                if games:
                    with time_operation("game_pages_generation", {"game_count": len(games)}):
                        log_info("SiteGenerator", f"Found {len(games)} game(s)", "🕹️")
                        self._generate_game_pages(games)
                        self.page_builder.generate_games_listing(games, self.config.get_base_context())
                    
                    update_stats("page_generation", files_processed=len(games) + len(pages) + 1)  # +1 for games listing
                else:
                    log_info("SiteGenerator", "No games found in content_html/games", "ℹ️")
                    update_stats("page_generation", files_processed=len(pages))
                
                # Update cache for content and template files
                self.build_cache.update_file_cache(self.build_cache.file_categories['content'])
                self.build_cache.update_file_cache(self.build_cache.file_categories['templates'])
                self.build_cache.update_file_cache(self.build_cache.file_categories['config'])
                
                pages_duration = logger.stop_timing(pages_timer)
                log_phase_complete("SiteGenerator", "page generation", pages_duration or 0.0, "✅", 
                                 files_processed=len(games) + len(pages) if games else len(pages))
            else:
                log_info("SiteGenerator", "Skipping page generation - no changes detected", "⚡")
                update_stats("page_generation", cache_hits=1)
                # Still need to load games for other operations
                games = self.game_manager.scan_games_content(
                    default_embed_url=self.config.seo_config.get("game_embed", {}).get("url", "about:blank"),
                    default_hero_image=self.config.get_dynamic_hero_image()
                )
                self._games = games
            
            # Generate error and offline pages (404.html, offline.html)
            log_phase_start("SiteGenerator", "Error and offline pages generation", "🚨")
            base_context = self.config.get_base_context()
            self.page_builder.generate_error_pages(base_context)
            log_phase_complete("SiteGenerator", "Error and offline pages generation", 0.0, "✅")
            
            # Generate SEO files (manifest, robots.txt, sitemap.xml)
            log_phase_start("SiteGenerator", "SEO file generation", "🔍")
            self.create_manifest()
            self.create_robots_txt()
            self.create_sitemap_xml()
            log_phase_complete("SiteGenerator", "SEO file generation", 0.0, "✅")
            
            # Save the build cache
            self.build_cache.save_cache()
            
            # Calculate generation time and finalize metrics
            overall_duration = logger.stop_timing(overall_timer)
            end_time = datetime.now()
            
            # Update overall build statistics
            memory_usage = logger.get_memory_usage()
            update_stats("overall_build", 
                        files_processed=1,  # One build completed
                        memory_usage_mb=memory_usage)
            
            if static_changed or pages_need_rebuild or self.force:
                # Final cleanup of all legacy files to prevent duplicate content
                self._final_cleanup_legacy_files()
                
                log_success("SiteGenerator", f"Website generated successfully in '{self.output_dir}' directory!", "✅")
            else:
                log_success("SiteGenerator", "Website up to date (incremental build)!", "⚡")
            
            if overall_duration is not None and overall_duration < 1.0:
                log_success("SiteGenerator", "Fast incremental build achieved!", "🚀")
            
            if static_changed or pages_need_rebuild or self.force:
                log_info("SiteGenerator", "Next steps:", "📋")
                log_info("SiteGenerator", "1. Images have been optimized for SEO with multiple sizes", "")
                log_info("SiteGenerator", "2. Favicon generated in multiple sizes for all devices", "")
                log_info("SiteGenerator", "3. Test the website locally", "")
                log_info("SiteGenerator", "4. Deploy to your web server", "")
            
            # Print comprehensive build summary
            print_build_summary()
            
        except (OSError, IOError) as e:
            log_error("SiteGenerator", f"File system error during website generation: {e}", "❌")
            raise
        except Exception as e:
            log_error("SiteGenerator", f"Fatal error during website generation: {e}", "❌")
            raise
    
    def _optimize_images(self):
        """Optimize images using the ImageOptimizer"""
        with time_operation("image_optimization"):
            try:
                self.image_optimizer.optimize_all_images(force=self.force)
                self.image_optimizer.generate_image_manifest()
            except (OSError, IOError) as e:
                log_warn("SiteGenerator", f"File system error during image optimization: {e}", "⚠️")
            except Exception as e:
                log_warn("SiteGenerator", f"Warning: Image optimization failed: {e}", "⚠️")
    
    def _get_pages_from_config(self):
        """Get pages configuration"""
        return [
            ("index", "index.html"),
            ("about-us", "page.html"),
            ("contact", "page.html"),
            ("privacy-policy", "page.html"),
            ("terms-of-service", "page.html"),
            ("cookies-policy", "page.html"),
            ("dmca", "page.html"),
            ("parents-information", "page.html"),
        ]
    
    def _generate_page(self, page_key, template_name):
        """Generate a single page"""
        try:
            # Get page configuration
            page_config = self.config.get_page_config(page_key)
            
            # Load HTML content from file
            content_file = self._get_content_file(page_key)
            if os.path.exists(content_file):
                with open(content_file, 'r', encoding='utf-8') as f:
                    page_config['custom_html_content'] = f.read()
            else:
                page_config['custom_html_content'] = f"<p>Content not found for {page_key}</p>"
            
            # Get base context and merge with page config
            context = {**self.config.get_base_context(), **page_config}
            
            # Update context with asset mappings
            context = self.asset_manager.update_template_context_for_assets(context)
            
            # Add games for sidebar if available
            if hasattr(self, '_games') and self._games:
                context['games'] = self.game_manager.get_random_games_for_widget(self._games)
                context['all_games'] = self.game_manager.get_all_games_for_widget(self._games)
                context['sidebar_title'] = "More Games"
            
            # Add missing hero SEO attributes and game embed for index page
            if page_key == "index":
                context['hero_seo_attributes'] = self.config.get_image_seo_attributes(
                    self.config.get_dynamic_hero_image(),
                    context_type='hero'
                )
                # Add game_embed for index page
                context['game_embed'] = {"url": self.config.seo_config.get("game_embed", {}).get("url", self.config.game_embed_url)}
                # Add game_url for template to use in data-game-url attribute
                context['game_url'] = self.config.game_embed_url
            
            # Get full output path for clean URLs
            full_output_path, _ = self.page_builder.get_page_output_path(page_key)
            
            # Ensure output directory exists for clean URLs
            os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
            
            # Generate the page directly to the clean URL path
            self.page_builder.generate_page_direct(template_name, context, full_output_path)
            
            # Clean up legacy .html files to prevent duplicate content
            self._cleanup_legacy_files(page_key)
            
        except (OSError, IOError) as e:
            log_warn("SiteGenerator", f"File system error generating page {page_key}: {e}", "⚠️")
            update_stats("page_generation", files_error=1)
        except Exception as e:
            log_warn("SiteGenerator", f"Template error generating page {page_key}: {e}", "⚠️")
            update_stats("page_generation", files_error=1)
    
    def _cleanup_legacy_files(self, page_key):
        """Clean up legacy .html files to prevent duplicate content"""
        try:
            # Map of legacy paths to clean for each page type
            legacy_paths = {
                "about-us": ["pages/about-us.html"],
                "contact": ["pages/contact.html"],
                "privacy-policy": ["legal/privacy-policy.html"],
                "terms-of-service": ["legal/terms-of-service.html"],
                "cookies-policy": ["legal/cookies-policy.html"],
                "dmca": ["legal/dmca.html"],
                "parents-information": ["legal/parents-information.html"],
                "games": ["games.html"]  # Clean up old games listing file
            }
            
            paths_to_remove = legacy_paths.get(page_key, [])
            
            for legacy_path in paths_to_remove:
                full_legacy_path = os.path.join(self.output_dir, legacy_path)
                if os.path.exists(full_legacy_path):
                    os.remove(full_legacy_path)
                    log_info("SiteGenerator", f"Cleaned up legacy file: {legacy_path}", "🧹")
                    
        except Exception as e:
            log_warn("SiteGenerator", f"Error cleaning up legacy files for {page_key}: {e}", "⚠️")

    def _cleanup_legacy_game_files(self):
        """Clean up legacy game .html files from games directory"""
        try:
            games_dir = os.path.join(self.output_dir, "games")
            if os.path.exists(games_dir):
                # Remove all .html files in games directory (keeping only directories with index.html)
                for file in os.listdir(games_dir):
                    if file.endswith('.html') and file != 'index.html':
                        legacy_file = os.path.join(games_dir, file)
                        os.remove(legacy_file)
                        log_info("SiteGenerator", f"Cleaned up legacy game file: games/{file}", "🧹")
        except Exception as e:
            log_warn("SiteGenerator", f"Error cleaning up legacy game files: {e}", "⚠️")

    def _final_cleanup_legacy_files(self):
        """Final comprehensive cleanup of all legacy files after build completion"""
        try:
            cleanup_files = []
            cleanup_dirs = []
            
            # Root-level legacy files that should be removed
            root_legacy_files = ["games.html"]
            for legacy_file in root_legacy_files:
                full_path = os.path.join(self.output_dir, legacy_file)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    cleanup_files.append(legacy_file)
            
            # Legacy directories that might be empty and should be removed
            legacy_directories = ["pages", "legal"]
            for legacy_dir in legacy_directories:
                dir_path = os.path.join(self.output_dir, legacy_dir)
                if os.path.exists(dir_path):
                    try:
                        # Remove directory if it's empty
                        os.rmdir(dir_path)
                        cleanup_dirs.append(legacy_dir)
                    except OSError:
                        # Directory not empty, check for specific legacy files
                        for root, dirs, files in os.walk(dir_path, topdown=False):
                            for file in files:
                                if file.endswith('.html'):
                                    legacy_file_path = os.path.join(root, file)
                                    os.remove(legacy_file_path)
                                    rel_path = os.path.relpath(legacy_file_path, self.output_dir)
                                    cleanup_files.append(rel_path)
                            # Try to remove empty directories
                            try:
                                os.rmdir(root)
                            except OSError:
                                pass  # Directory not empty, keep it
            
            if cleanup_files or cleanup_dirs:
                files_msg = f", files: {', '.join(cleanup_files)}" if cleanup_files else ""
                dirs_msg = f", dirs: {', '.join(cleanup_dirs)}" if cleanup_dirs else ""
                log_info("SiteGenerator", f"Final cleanup completed{files_msg}{dirs_msg}", "🧹")
            
        except Exception as e:
            log_warn("SiteGenerator", f"Error in final cleanup: {e}", "⚠️")

    def _get_content_file(self, page_key):
        """Get content file path for a page"""
        # Map page keys to content files
        mapping = {
            "cookies-policy": "cookies",
        }
        content_name = mapping.get(page_key, page_key)
        return os.path.join(self.content_dir, f"{content_name}.html")
    
    def _generate_game_pages(self, games):
        """Generate individual game pages"""
        try:
            template = self.env.get_template("index.html")
        except Exception as e:
            log_warn("SiteGenerator", f"Missing template index.html for game pages: {e}", "⚠️")
            return
        
        for game in games:
            try:
                # Create breadcrumbs
                breadcrumbs = [
                    {"title": "Home", "url": "/"},
                    {"title": "Games", "url": "/games/"},
                    {"title": game["title"], "url": None}
                ]
                
                # Get game rating
                rating = self.game_manager.generate_game_rating(
                    game["slug"],
                    game.get("meta", {}).get("rating")
                )
                
                # Get software application schema
                software_schema = self.seo_manager.get_software_application_schema(
                    game["title"],
                    game["slug"],
                    game.get("description"),
                    rating
                )
                
                # Build context
                base_context = self.config.get_base_context()
                base_context['software_application_schema'] = software_schema
                base_context['breadcrumb_schema'] = self.seo_manager.get_breadcrumb_schema(breadcrumbs)
                base_context['hero_seo_attributes'] = self.config.get_image_seo_attributes(
                    game["hero_image"],
                    context_type='hero',
                    game_title=game["title"]
                )
                
                # Get games for sidebar
                sidebar_games = self.game_manager.get_random_games_for_widget(games, game["slug"])
                all_games = self.game_manager.get_all_games_for_widget(games, game["slug"])
                
                # Fix image paths in game content HTML
                if 'content_html' in game:
                    game['content_html'] = self.page_builder.resolve_asset_links(game['content_html'])
                
                # Add all_games for widget
                base_context['all_games'] = all_games
                
                # Generate the page
                self.page_builder.generate_game_page(
                    game, template, base_context, sidebar_games, breadcrumbs
                )
                
            except Exception as e:
                log_warn("SiteGenerator", f"Error generating game page {game.get('slug')}: {e}", "⚠️")
                update_stats("page_generation", files_error=1)
        
        # Clean up legacy game .html files after all games are generated
        self._cleanup_legacy_game_files()
    
    def create_manifest(self):
        """Create web manifest"""
        config = {
            'seo_filename': self.config.seo_filename,
            'description': self.config.centralized_description,
            'theme_color': self.config.theme_color,
            'background_color': self.config.css_bg,
            'language': self.language
        }
        self.seo_manager.create_manifest(config)
    
    def create_robots_txt(self):
        """Create robots.txt"""
        self.seo_manager.create_robots_txt()
    
    def create_sitemap_xml(self):
        """Create sitemap.xml using crawler to discover all pages"""
        log_info("SiteGenerator", "Creating comprehensive sitemap using crawler...", "🗺️")
        
        # Use the crawler to discover all pages
        crawler = SiteCrawler(self.output_dir, self.config.site_url)
        crawl_results = crawler.crawl_site()
        
        # Generate sitemap entries from discovered pages
        sitemap_entries = crawler.generate_sitemap_entries()
        
        # Create the sitemap XML
        self.seo_manager.create_sitemap_xml(sitemap_entries, games=None)
        
        # Validate the build
        if not crawler.validate_build(fail_on_errors=False):
            log_warn("SiteGenerator", "Build validation found issues - check logs above", "⚠️")
        
        log_success("SiteGenerator", f"Generated sitemap with {len(sitemap_entries)} URLs from crawled site", "✅")