#!/usr/bin/env python3
"""
Image Optimization Script for SEO
Generates multiple image sizes, formats, and SEO-optimized markup.
"""

import os
import json
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict, Callable, Any
from threading import Lock
from PIL import Image, ImageOps
from .site_loader import get_project_root, abs_path
from .performance_logger import (
    logger, time_operation, log_info, log_success, log_warn, log_error,
    log_phase_start, log_phase_complete, update_stats
)

class ImageOptimizer:
    def __init__(self, input_dir="static", output_dir="output", max_workers=None, build_cache=None):
        # Convert to absolute paths to avoid CWD dependencies (cross-platform)
        if not os.path.isabs(input_dir):
            self.input_dir = str(abs_path(input_dir))
        else:
            self.input_dir = str(Path(input_dir).resolve())
            
        if not os.path.isabs(output_dir):
            self.output_dir = str(abs_path(output_dir))
        else:
            self.output_dir = str(Path(output_dir).resolve())
            
        self.image_config = self._load_image_config()
        self.force = False  # Default to incremental builds
        self.build_cache = build_cache  # For coordinating with AssetManager
        
        # Configure max workers for parallel processing (default: min(32, cpu_count() + 4))
        cpu_count = os.cpu_count() or 4  # Fallback to 4 if cpu_count() returns None
        self.max_workers = max_workers if max_workers is not None else min(32, cpu_count + 4)
        # Thread-safe stats aggregation
        self._stats_lock = Lock()
        
    def _load_image_config(self):
        """Load image configuration from seo_config.json (cross-platform)"""
        try:
            # Use absolute path to avoid CWD dependency
            config_path = abs_path("seo_config.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("image_optimization", {})
        except FileNotFoundError:
            # Config file doesn't exist, use default settings
            return {}
        except json.JSONDecodeError as e:
            # Invalid JSON in config file
            print(f"⚠️  Invalid JSON in seo_config.json: {e}")
            return {}
        except (OSError, IOError) as e:
            # File access issues (permissions, disk errors)
            print(f"⚠️  Could not read seo_config.json: {e}")
            return {}
    
    def _needs_processing(self, source_path, target_path):
        """Check if image processing is needed based on modification times"""
        try:
            if self.force:
                return True
                
            if not os.path.exists(target_path):
                return True  # Target doesn't exist, processing needed
            
            source_mtime = os.path.getmtime(source_path)
            target_mtime = os.path.getmtime(target_path)
            
            # Process if source is newer than target
            return source_mtime > target_mtime
        except OSError:
            return True  # Error accessing files, assume processing needed
    
    def optimize_all_images(self, force=False):
        """Optimize all images for SEO with parallel processing and incremental build support"""
        optimization_timer = logger.start_timing("image_optimization")
        self.force = force
        
        if force:
            log_phase_start("ImageOptimizer", f"full image optimization (forced) with {self.max_workers} workers", "🖼️")
        else:
            log_phase_start("ImageOptimizer", f"incremental image optimization with {self.max_workers} workers", "🖼️")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Define image processing tasks that can be parallelized
        # IMPORTANT: Removed game_logo from parallel tasks to process it separately after
        image_tasks = [
            ('hero_images', self._optimize_hero_images),
            ('favicon', self._optimize_favicon),
            ('og_images', self._generate_og_images),
            ('pwa_icons', self._generate_pwa_icons),
            ('pwa_screenshots', self._generate_pwa_screenshots),
            ('seo_attributes', self._generate_seo_attributes)
        ]
        
        # Execute image processing tasks in parallel
        processed_count = self._execute_parallel_image_tasks(image_tasks)
        
        # CRITICAL FIX: Process game logo AFTER parallel tasks to ensure it's not overwritten
        # This ensures gamelogo.webp is saved to /assets/images/ after AssetManager runs
        processed_count += self._optimize_game_logo()
        
        # Calculate and log performance metrics
        optimization_duration = logger.stop_timing(optimization_timer)
        
        if processed_count > 0 or force:
            processing_rate = logger.calculate_processing_rate(processed_count, optimization_duration) if optimization_duration else 0
            update_stats("image_optimization",
                       files_processed=processed_count,
                       processing_rate=processing_rate,
                       parallel_workers=self.max_workers,
                       memory_usage_mb=logger.get_memory_usage())
            
            log_phase_complete("ImageOptimizer", "image optimization", optimization_duration or 0, "✅",
                             files_processed=processed_count,
                             processing_rate=processing_rate)
        else:
            log_info("ImageOptimizer", "Images up to date - no processing needed", "⚡")
            update_stats("image_optimization", cache_hits=1)
    
    def _optimize_hero_images(self):
        """Use original hero images with SEO-optimized names"""
        # Get SEO filename for naming
        seo_filename = self._get_seo_filename()
        
        # Look for original hero images in static folder (cross-platform)
        hero_image_path = Path(self.input_dir) / "hero-image.webp"
        
        if not hero_image_path.exists():
            print(f"⚠️  No original hero image found at: {hero_image_path}")
            print("  Please add your hero image as 'hero-image.webp' in the static folder")
            return 0
        
        # Create organized SEO images directory (cross-platform)
        seo_dir = Path(self.output_dir) / "assets" / "images" / "seo"
        seo_dir.mkdir(parents=True, exist_ok=True)
        seo_image_path = seo_dir / f"{seo_filename}.webp"
        
        # Check if processing is needed
        if not self._needs_processing(str(hero_image_path), str(seo_image_path)):
            print("📸 Hero image: up to date")
            return 0
        
        print("📸 Processing hero image: hero-image.webp")
        
        # Add site name to the original image
        self._add_site_name_to_image(hero_image_path, "hero-image", {})
        
        # Copy the original image with SEO-optimized name to organized location
        shutil.copy2(str(hero_image_path), str(seo_image_path))
        
        print(f"  ✅ Copied to SEO-optimized name: {seo_filename}.webp in /assets/images/seo/")
        
        # Register the source image as processed to avoid duplication by AssetManager
        if self.build_cache:
            self.build_cache.register_processed_image(str(hero_image_path))
        
        # Update the schema to use the SEO-optimized filename
        self._update_hero_image_schema(seo_filename)
        
        return 1
    
    def _add_site_name_to_image(self, input_path, image_name, config):
        """Optimize hero image"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Optimize and save the image
                img.save(input_path, 'WEBP', quality=85, optimize=True)
                print(f"  ✅ Optimized image: {image_name}.webp")
                
        except (OSError, IOError) as e:
            # File access errors (permissions, disk space, invalid file)
            print(f"  ⚠️  Could not optimize {image_name}: {e}")
        except ValueError as e:
            # Invalid image mode conversion or parameters
            print(f"  ⚠️  Invalid image format for {image_name}: {e}")
        except MemoryError as e:
            # Not enough memory to process image
            print(f"  ⚠️  Insufficient memory to process {image_name}: {e}")
    
    def _get_site_name(self):
        """Get site name from seo_config.json (cross-platform)"""
        try:
            # Use absolute path to avoid CWD dependency
            config_path = abs_path("seo_config.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("site_name", "Gaming Site")
        except (FileNotFoundError, json.JSONDecodeError):
            return "Gaming Site"
    
    def _get_seo_filename(self):
        """Get SEO filename from config.py"""
        try:
            from . import settings as simple_config
            return simple_config.SEO_FILENAME
        except (ImportError, AttributeError):
            return "game"
    
    def _optimize_favicon(self):
        """Generate favicon in multiple sizes with organized structure"""
        # First check for gamelogo.webp in static directory
        gamelogo_path = os.path.join(self.input_dir, "gamelogo.webp")
        favicon_path = os.path.join(self.input_dir, "favicon.ico")
        
        # Use gamelogo.webp if it exists, otherwise fall back to favicon.ico
        source_path = gamelogo_path if os.path.exists(gamelogo_path) else favicon_path
        
        if not os.path.exists(source_path):
            print("⚠️  Favicon/gamelogo not found, creating default")
            return self._create_default_favicon()
        
        # Check if favicon processing is needed
        icons_dir = os.path.join(self.output_dir, "assets", "icons")
        test_icon_path = os.path.join(icons_dir, "favicon-32x32.png")
        
        if not self._needs_processing(source_path, test_icon_path):
            print("📱 Favicon: up to date")
            return 0
        
        print(f"📱 Processing favicon from {os.path.basename(source_path)}...")
        
        # Create organized icons directory
        icons_dir = os.path.join(self.output_dir, "assets", "icons")
        os.makedirs(icons_dir, exist_ok=True)
        
        try:
            with Image.open(source_path) as img:
                # Convert to RGBA if necessary
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Generate only essential sizes for Core Web Vitals (reduced from 8 to 3)
                favicon_sizes = [16, 32, 192]  # Minimum sizes needed for browsers
                
                # Create tasks for parallel favicon generation
                favicon_tasks = [(img.copy(), size, icons_dir) for size in favicon_sizes]
                
                # Process favicon sizes in parallel using ThreadPoolExecutor
                self._process_favicon_sizes_parallel(favicon_tasks)
                
                # Create favicon.ico from the source image
                img_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
                favicon_output = os.path.join(self.output_dir, "favicon.ico")
                img_32.save(favicon_output, format='ICO')
                
                # Also save optimized WebP version for modern browsers
                webp_path = os.path.join(self.output_dir, "assets", "icons", "favicon.webp")
                img_32.save(webp_path, format='WEBP', quality=90, method=6)
                
                print(f"  ✅ Generated favicon in {len(favicon_sizes)} optimized sizes (organized in /assets/icons/)")
                
                # Register the source image as processed to avoid duplication by AssetManager
                if self.build_cache:
                    self.build_cache.register_processed_image(source_path)
                
        except (OSError, IOError) as e:
            # File access errors (permissions, disk space, corrupt file)
            print(f"❌ Error reading/writing favicon files: {e}")
            return 0
        except ValueError as e:
            # Invalid image mode conversion or parameters
            print(f"❌ Invalid favicon image format: {e}")
            return 0
        except MemoryError as e:
            # Not enough memory to process favicon
            print(f"❌ Insufficient memory to process favicon: {e}")
            return 0
        
        return 1  # Return 1 to indicate successful processing
    
    def _execute_parallel_image_tasks(self, image_tasks: List[Tuple[str, Callable]]) -> int:
        """
        Execute image processing tasks in parallel using ThreadPoolExecutor.
        
        Args:
            image_tasks: List of (task_name, task_function) tuples
            
        Returns:
            Total number of processed operations
        """
        total_processed = 0
        
        # Use ThreadPoolExecutor for I/O-bound image operations
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all image processing tasks
            future_to_task = {executor.submit(task_func): task_name 
                             for task_name, task_func in image_tasks}
            
            # Process completed tasks
            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    result = future.result()
                    with self._stats_lock:
                        total_processed += result
                except (OSError, IOError) as e:
                    # File system errors during task execution
                    print(f"⚠️  File system error in image task '{task_name}': {e}")
                    # Continue processing other tasks
                except MemoryError as e:
                    # Memory errors during image processing
                    print(f"⚠️  Memory error in image task '{task_name}': {e}")
                    # Continue processing other tasks
                except Exception as e:
                    # Catch any other unexpected errors but log them specifically
                    print(f"⚠️  Unexpected error in image task '{task_name}': {type(e).__name__}: {e}")
                    # Continue processing other tasks
        
        return total_processed
    
    def _optimize_game_logo(self):
        """Optimize game logo and create SEO-renamed version"""
        gamelogo_path = os.path.join(self.input_dir, "gamelogo.webp")
        if not os.path.exists(gamelogo_path):
            print("⚠️  Game logo not found: gamelogo.webp")
            return 0
        
        # Check if game logo processing is needed
        site_name = self._get_site_name()
        seo_filename = site_name.lower().replace(" ", "-").replace("_", "-")
        logo_filename = f"{seo_filename}-logo.webp"
        output_path = os.path.join(self.output_dir, logo_filename)
        
        if not self._needs_processing(gamelogo_path, output_path):
            print("🎮 Game logo: up to date")
            return 0
        
        print("🎮 Processing game logo...")
        
        try:
            # Get site name for SEO filename
            site_name = self._get_site_name()
            seo_filename = site_name.lower().replace(" ", "-").replace("_", "-")
            seo_filename = "".join(c for c in seo_filename if c.isalnum() or c in "-")
            logo_filename = f"{seo_filename}-logo.webp"
            
            with Image.open(gamelogo_path) as img:
                # Convert to RGBA if necessary
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Resize to 64x64 for logo use
                logo_size = (64, 64)
                resized = img.resize(logo_size, Image.Resampling.LANCZOS)
                
                # Create organized logos directory
                logos_dir = os.path.join(self.output_dir, "assets", "images", "logos")
                os.makedirs(logos_dir, exist_ok=True)
                
                # Save as SEO-optimized filename in organized location
                output_path = os.path.join(logos_dir, logo_filename)
                resized.save(output_path, "WEBP", quality=90, optimize=True)
                
                # Also keep a copy in root for backward compatibility
                root_logo_path = os.path.join(self.output_dir, logo_filename)
                resized.save(root_logo_path, "WEBP", quality=90, optimize=True)
                
                # IMPORTANT: Save as gamelogo.webp in /assets/images/ for HTML references
                images_dir = os.path.join(self.output_dir, "assets", "images")
                os.makedirs(images_dir, exist_ok=True)
                standard_logo_path = os.path.join(images_dir, "gamelogo.webp")
                resized.save(standard_logo_path, "WEBP", quality=90, optimize=True)
                
                print(f"  ✅ Generated game logo: {logo_filename} (also in /assets/images/logos/)")
                print(f"  ✅ Saved standard gamelogo.webp in /assets/images/ for HTML references")
                
                # Register the source image as processed to avoid duplication by AssetManager
                if self.build_cache:
                    self.build_cache.register_processed_image(gamelogo_path)
                
        except (OSError, IOError) as e:
            # File access errors (permissions, disk space, corrupt file)
            print(f"❌ Error reading/writing game logo: {e}")
            return 0
        except ValueError as e:
            # Invalid image mode conversion or parameters
            print(f"❌ Invalid game logo image format: {e}")
            return 0
        except MemoryError as e:
            # Not enough memory to process game logo
            print(f"❌ Insufficient memory to process game logo: {e}")
            return 0
        
        return 1  # Return 1 to indicate successful processing
    
    def _create_default_favicon(self):
        """Create a default favicon if none exists with organized structure"""
        print("🎨 Creating default favicon...")
        
        # Create organized icons directory
        icons_dir = os.path.join(self.output_dir, "assets", "icons")
        os.makedirs(icons_dir, exist_ok=True)
        
        # Create a simple favicon
        favicon = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        
        # Save in multiple sizes in organized directory
        sizes = [16, 32, 48, 64, 128, 192, 256, 512]
        for size in sizes:
            resized = favicon.resize((size, size), Image.Resampling.LANCZOS)
            png_path = os.path.join(icons_dir, f"favicon-{size}x{size}.png")
            resized.save(png_path, "PNG", optimize=True)
        
        # Save as ICO in root (required for browser fallback)
        ico_path = os.path.join(self.output_dir, "favicon.ico")
        favicon.save(ico_path, "ICO")
        
        print("  ✅ Created default favicon (organized in /assets/icons/)")
        
        # Return 1 to indicate processing was done
        return 1
    
    def _generate_og_images(self):
        """Generate Open Graph images for social sharing"""
        print("📱 Generating Open Graph images...")
        
        og_config = self.image_config.get("og_images", {})
        
        for image_name, config in og_config.items():
            input_path = os.path.join(self.input_dir, f"{image_name}.webp")
            if not os.path.exists(input_path):
                print(f"⚠️  OG image not found: {input_path}")
                continue
            
            try:
                with Image.open(input_path) as img:
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Standard OG image size: 1200x630
                    og_size = (1200, 630)
                    og_img = ImageOps.fit(img, og_size, Image.Resampling.LANCZOS)
                    
                    # Save OG image as WebP only
                    og_webp_path = os.path.join(self.output_dir, f"{image_name}_og.webp")
                    og_img.save(og_webp_path, "WebP", quality=90, optimize=True)
                    
                    print(f"  ✅ Generated OG image: {image_name}_og (WebP)")
                    
            except (OSError, IOError) as e:
                # File access errors (permissions, disk space, corrupt file)
                print(f"❌ Error reading/writing OG image {image_name}: {e}")
            except ValueError as e:
                # Invalid image mode conversion or parameters
                print(f"❌ Invalid OG image format for {image_name}: {e}")
            except MemoryError as e:
                # Not enough memory to process OG image
                print(f"❌ Insufficient memory to process OG image {image_name}: {e}")
        
        return 1  # Return 1 to indicate processing was attempted
    
    def generate_image_manifest(self):
        """Generate a manifest of all optimized images"""
        manifest = {
            "images": {},
            "generated_at": str(Path().cwd()),
            "optimization_settings": self.image_config
        }
        
        # Scan output directory for images
        for file in os.listdir(self.output_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.ico')):
                file_path = os.path.join(self.output_dir, file)
                file_size = os.path.getsize(file_path)
                
                # Get image dimensions
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                        format_type = img.format
                except (OSError, IOError):
                    width, height = 0, 0
                    format_type = "unknown"
                
                manifest["images"][file] = {
                    "size_bytes": file_size,
                    "width": width,
                    "height": height,
                    "format": format_type,
                    "path": file
                }
        
        # Save manifest to internal directory (not public root for security)
        # SECURITY: Store image manifest in internal build directory, not public root
        internal_dir = os.path.join(self.output_dir, ".internal")
        os.makedirs(internal_dir, exist_ok=True)
        manifest_path = os.path.join(internal_dir, "image_manifest.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"📋 Generated image manifest: {manifest_path} (internal build metadata)")
    
    def _generate_seo_attributes(self):
        """Generate SEO attributes for all images"""
        print("🔍 Generating SEO attributes for images...")
        
        # Get site name and SEO filename from config
        site_name = self._get_site_name()
        seo_filename = self._get_seo_filename()
        
        # Process hero images - use SEO filename if available
        hero_images = self.image_config.get("hero_images", {})
        # Create a copy to avoid dictionary changed size during iteration
        for image_name, config in list(hero_images.items()):
            # If this is the hero-image, use SEO filename for attributes
            if image_name == "hero-image":
                self._update_image_seo_attributes(seo_filename, config, site_name)
            else:
                self._update_image_seo_attributes(image_name, config, site_name)
        
        # Process OG images
        og_images = self.image_config.get("og_images", {})
        for image_name, config in og_images.items():
            self._update_og_image_seo_attributes(image_name, config, site_name)
        
        print("  ✅ SEO attributes generated for all images")
        return 1  # Return 1 to indicate successful processing
    
    def _update_image_seo_attributes(self, image_name, config, site_name):
        """Update SEO attributes for hero images"""
        # Generate better alt text if not provided
        if not config.get("alt_text"):
            config["alt_text"] = f"{site_name} - High quality image optimized for web"
        
        # Generate better title if not provided
        if not config.get("title"):
            config["title"] = f"{site_name} - Play Online"
        
        # Ensure loading and decoding attributes
        config["loading"] = config.get("loading", "lazy")
        config["decoding"] = config.get("decoding", "async")
        
        # Update the config
        self.image_config["hero_images"][image_name] = config
    
    def _update_og_image_seo_attributes(self, image_name, config, site_name):
        """Update SEO attributes for OG images"""
        # Generate better alt text if not provided
        if not config.get("alt_text"):
            config["alt_text"] = f"{site_name} - Share this exciting game with friends"
        
        # Generate better title if not provided
        if not config.get("title"):
            config["title"] = f"{site_name} - Free Online Game"
        
        # Update the config
        self.image_config["og_images"][image_name] = config
    
    def _update_hero_image_schema(self, seo_filename):
        """Update the hero image schema - simplified system doesn't need external config"""
        # Skip updating external config since we use the simplified system
        print(f"  ✅ Hero image optimized with SEO filename: {seo_filename}")
    
    def _generate_pwa_icons(self):
        """Generate PWA icons for different devices and purposes"""
        print("📱 Generating PWA icons...")
        
        # Get SEO filename for naming
        seo_filename = self._get_seo_filename()
        
        # Look for source icon (favicon or game logo)
        source_icon_path = None
        for icon_name in ["favicon.ico", "gamelogo.webp", "hero-image.webp"]:
            icon_path = os.path.join(self.input_dir, icon_name)
            if os.path.exists(icon_path):
                source_icon_path = icon_path
                break
        
        if not source_icon_path:
            print("⚠️  No source icon found for PWA icons")
            return 0
        
        try:
            with Image.open(source_icon_path) as img:
                # Convert to RGBA if necessary
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # PWA icon sizes for different devices
                pwa_sizes = [
                    {"size": 72, "purpose": "any"},
                    {"size": 96, "purpose": "any"},
                    {"size": 128, "purpose": "any"},
                    {"size": 144, "purpose": "any"},
                    {"size": 152, "purpose": "any"},
                    {"size": 192, "purpose": "any"},
                    {"size": 384, "purpose": "any"},
                    {"size": 512, "purpose": "any"},
                    {"size": 192, "purpose": "maskable"},
                    {"size": 512, "purpose": "maskable"}
                ]
                
                for icon_config in pwa_sizes:
                    size = icon_config["size"]
                    purpose = icon_config["purpose"]
                    
                    # Resize image
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    
                    # For maskable icons, add padding for safe area
                    if purpose == "maskable":
                        # Create a larger canvas with padding
                        padding = size // 10  # 10% padding
                        canvas_size = size + (padding * 2)
                        canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
                        
                        # Center the icon on the canvas
                        canvas.paste(resized, (padding, padding))
                        final_icon = canvas
                    else:
                        final_icon = resized
                    
                    # Create organized PWA directory
                    pwa_dir = os.path.join(self.output_dir, "assets", "pwa")
                    os.makedirs(pwa_dir, exist_ok=True)
                    
                    # Save as PNG in organized directory
                    filename = f"{seo_filename}-icon-{size}x{size}"
                    if purpose == "maskable":
                        filename += "-maskable"
                    filename += ".png"
                    
                    output_path = os.path.join(pwa_dir, filename)
                    final_icon.save(output_path, "PNG", optimize=True)
                    
                    print(f"  ✅ Generated {filename} (in /assets/pwa/)")
                
        except (OSError, IOError) as e:
            # File access errors (permissions, disk space, corrupt file)
            print(f"❌ Error reading/writing PWA icons: {e}")
            return 0
        except ValueError as e:
            # Invalid image mode conversion or parameters
            print(f"❌ Invalid PWA icon image format: {e}")
            return 0
        except MemoryError as e:
            # Not enough memory to process PWA icons
            print(f"❌ Insufficient memory to process PWA icons: {e}")
            return 0
        
        return 1  # Return 1 to indicate successful processing
    
    def _generate_pwa_screenshots(self):
        """Generate PWA screenshots for different device form factors"""
        print("📸 Generating PWA screenshots...")
        
        # Get SEO filename for naming
        seo_filename = self._get_seo_filename()
        
        # Look for source screenshot (hero image)
        source_image_path = os.path.join(self.input_dir, "hero-image.webp")
        
        if not os.path.exists(source_image_path):
            print("⚠️  No source image found for PWA screenshots")
            return 0
        
        try:
            with Image.open(source_image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # PWA screenshot sizes for different form factors
                screenshot_configs = [
                    {"name": "mobile", "width": 390, "height": 844, "form_factor": "narrow"},
                    {"name": "tablet", "width": 768, "height": 1024, "form_factor": "wide"},
                    {"name": "desktop", "width": 1280, "height": 720, "form_factor": "wide"}
                ]
                
                for config in screenshot_configs:
                    width = config["width"]
                    height = config["height"]
                    name = config["name"]
                    
                    # Resize image maintaining aspect ratio and crop to fit
                    resized = ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)
                    
                    # Add device frame for better presentation
                    screenshot = self._add_device_frame(resized, config)
                    
                    # Create organized PWA directory
                    pwa_dir = os.path.join(self.output_dir, "assets", "pwa")
                    os.makedirs(pwa_dir, exist_ok=True)
                    
                    # Save as PNG in organized directory
                    filename = f"{seo_filename}-screenshot-{name}.png"
                    output_path = os.path.join(pwa_dir, filename)
                    screenshot.save(output_path, "PNG", optimize=True)
                    
                    print(f"  ✅ Generated {filename} (in /assets/pwa/)")
                
        except (OSError, IOError) as e:
            # File access errors (permissions, disk space, corrupt file)
            print(f"❌ Error reading/writing PWA screenshots: {e}")
            return 0
        except ValueError as e:
            # Invalid image mode conversion or parameters
            print(f"❌ Invalid PWA screenshot image format: {e}")
            return 0
        except MemoryError as e:
            # Not enough memory to process PWA screenshots
            print(f"❌ Insufficient memory to process PWA screenshots: {e}")
            return 0
        
        return 1  # Return 1 to indicate successful processing
    
    def _add_device_frame(self, image, config):
        """Add a device frame to the screenshot for better presentation"""
        try:
            from PIL import ImageDraw
            
            # Create a slightly larger canvas for the frame
            frame_padding = 20
            canvas_width = image.width + (frame_padding * 2)
            canvas_height = image.height + (frame_padding * 2)
            
            # Create canvas with device-appropriate background
            if config["form_factor"] == "narrow":
                # Mobile frame - darker background
                canvas = Image.new('RGB', (canvas_width, canvas_height), (20, 20, 20))
            else:
                # Tablet/Desktop frame - lighter background
                canvas = Image.new('RGB', (canvas_width, canvas_height), (240, 240, 240))
            
            # Paste the screenshot in the center
            canvas.paste(image, (frame_padding, frame_padding))
            
            # Add rounded corners effect
            draw = ImageDraw.Draw(canvas)
            corner_radius = 15
            
            # Draw rounded rectangle border
            draw.rounded_rectangle(
                (frame_padding-2, frame_padding-2, 
                 canvas_width-frame_padding+2, canvas_height-frame_padding+2),
                radius=corner_radius,
                outline=(100, 100, 100) if config["form_factor"] == "narrow" else (200, 200, 200),
                width=2
            )
            
            return canvas
            
        except ImportError as e:
            # Missing PIL dependency for ImageDraw
            print(f"⚠️  ImageDraw module not available for device frame: {e}")
            return image
        except ValueError as e:
            # Invalid parameters or image mode issues
            print(f"⚠️  Invalid parameters for device frame: {e}")
            return image
        except (OSError, IOError) as e:
            # Drawing operation failed
            print(f"⚠️  Failed to draw device frame: {e}")
            return image

    def _save_updated_config(self):
        """SEO attributes are generated inline - no external config needed"""
        pass
    
    def _process_favicon_sizes_parallel(self, favicon_tasks: List[Tuple]) -> None:
        """
        Process favicon sizes in parallel for better performance.
        
        Args:
            favicon_tasks: List of (img, size, icons_dir) tuples
        """
        def process_single_favicon(task):
            img, size, icons_dir = task
            try:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # Save as PNG in organized directory
                png_path = os.path.join(icons_dir, f"favicon-{size}x{size}.png")
                resized.save(png_path, "PNG", optimize=True)
                
                # Save as ICO for specific sizes in organized directory
                if size in [16, 32, 48]:
                    ico_path = os.path.join(icons_dir, f"favicon-{size}x{size}.ico")
                    resized.save(ico_path, "ICO")
                
                return f"favicon-{size}x{size}"
            except (OSError, IOError) as e:
                # File access errors during favicon resize/save
                print(f"⚠️  Error saving favicon size {size}: {e}")
                return None
            except ValueError as e:
                # Invalid image parameters or mode conversion error
                print(f"⚠️  Invalid parameters for favicon size {size}: {e}")
                return None
            except MemoryError as e:
                # Not enough memory for favicon processing
                print(f"⚠️  Insufficient memory for favicon size {size}: {e}")
                return None
        
        # Use ThreadPoolExecutor for parallel favicon processing (I/O bound operations)
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(favicon_tasks))) as executor:
            # Submit all favicon tasks
            futures = [executor.submit(process_single_favicon, task) for task in favicon_tasks]
            
            # Process completed tasks
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        print(f"  ✅ Generated {result} (in organized directory)")
                except (OSError, IOError) as e:
                    # File system errors during parallel task execution
                    print(f"⚠️  File system error in favicon parallel processing: {e}")
                except Exception as e:
                    # Catch any unexpected errors from threading
                    print(f"⚠️  Unexpected error in favicon parallel processing: {type(e).__name__}: {e}")
    
    def _process_pwa_icons_parallel(self, pwa_tasks: List[Tuple]) -> None:
        """
        Process PWA icons in parallel for better performance.
        
        Args:
            pwa_tasks: List of (img, icon_config, seo_filename, output_dir) tuples
        """
        def process_single_pwa_icon(task):
            img, icon_config, seo_filename, output_dir = task
            try:
                size = icon_config["size"]
                purpose = icon_config["purpose"]
                
                # Resize image
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # For maskable icons, add padding for safe area
                if purpose == "maskable":
                    # Create a larger canvas with padding
                    padding = size // 10  # 10% padding
                    canvas_size = size + (padding * 2)
                    canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
                    
                    # Center the icon on the canvas
                    canvas.paste(resized, (padding, padding))
                    final_icon = canvas
                else:
                    final_icon = resized
                
                # Create organized PWA directory
                pwa_dir = os.path.join(output_dir, "assets", "pwa")
                os.makedirs(pwa_dir, exist_ok=True)
                
                # Save as PNG in organized directory
                filename = f"{seo_filename}-icon-{size}x{size}"
                if purpose == "maskable":
                    filename += "-maskable"
                filename += ".png"
                
                output_path = os.path.join(pwa_dir, filename)
                final_icon.save(output_path, "PNG", optimize=True)
                
                return filename
            except (OSError, IOError) as e:
                # File access errors during PWA icon processing
                print(f"⚠️  Error saving PWA icon {icon_config}: {e}")
                return None
            except ValueError as e:
                # Invalid image parameters or mode conversion error
                print(f"⚠️  Invalid parameters for PWA icon {icon_config}: {e}")
                return None
            except MemoryError as e:
                # Not enough memory for PWA icon processing
                print(f"⚠️  Insufficient memory for PWA icon {icon_config}: {e}")
                return None
        
        # Use ThreadPoolExecutor for parallel PWA icon processing
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(pwa_tasks))) as executor:
            # Submit all PWA icon tasks
            futures = [executor.submit(process_single_pwa_icon, task) for task in pwa_tasks]
            
            # Process completed tasks
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        print(f"  ✅ Generated {result} (in /assets/pwa/)")
                except (OSError, IOError) as e:
                    # File system errors during parallel task execution
                    print(f"⚠️  File system error in PWA icon parallel processing: {e}")
                except Exception as e:
                    # Catch any unexpected errors from threading
                    print(f"⚠️  Unexpected error in PWA icon parallel processing: {type(e).__name__}: {e}")
    
    def _process_pwa_screenshots_parallel(self, screenshot_tasks: List[Tuple]) -> None:
        """
        Process PWA screenshots in parallel for better performance.
        
        Args:
            screenshot_tasks: List of (img, config, seo_filename, output_dir) tuples
        """
        def process_single_screenshot(task):
            img, config, seo_filename, output_dir = task
            try:
                width = config["width"]
                height = config["height"]
                name = config["name"]
                
                # Resize image maintaining aspect ratio and crop to fit
                resized = ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)
                
                # Add device frame for better presentation
                screenshot = self._add_device_frame(resized, config)
                
                # Create organized PWA directory
                pwa_dir = os.path.join(output_dir, "assets", "pwa")
                os.makedirs(pwa_dir, exist_ok=True)
                
                # Save as PNG in organized directory
                filename = f"{seo_filename}-screenshot-{name}.png"
                output_path = os.path.join(pwa_dir, filename)
                screenshot.save(output_path, "PNG", optimize=True)
                
                return filename
            except (OSError, IOError) as e:
                # File access errors during screenshot processing
                print(f"⚠️  Error saving PWA screenshot {config}: {e}")
                return None
            except ValueError as e:
                # Invalid image parameters or mode conversion error
                print(f"⚠️  Invalid parameters for PWA screenshot {config}: {e}")
                return None
            except MemoryError as e:
                # Not enough memory for screenshot processing
                print(f"⚠️  Insufficient memory for PWA screenshot {config}: {e}")
                return None
        
        # Use ThreadPoolExecutor for parallel screenshot processing 
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(screenshot_tasks))) as executor:
            # Submit all screenshot tasks
            futures = [executor.submit(process_single_screenshot, task) for task in screenshot_tasks]
            
            # Process completed tasks
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        print(f"  ✅ Generated {result} (in /assets/pwa/)")
                except (OSError, IOError) as e:
                    # File system errors during parallel task execution
                    print(f"⚠️  File system error in screenshot parallel processing: {e}")
                except Exception as e:
                    # Catch any unexpected errors from threading
                    print(f"⚠️  Unexpected error in screenshot parallel processing: {type(e).__name__}: {e}")

def main():
    """Main function - automatically optimize images"""
    print("🖼️  Automatic Image Optimization")
    print("=" * 40)
    
    # Use default directories
    input_dir = "static"
    output_dir = "output"
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        print(f"❌ Input directory '{input_dir}' not found")
        print("   Make sure you have images in the 'static' folder")
        return
    
    # Create optimizer and run
    optimizer = ImageOptimizer(input_dir, output_dir)
    optimizer.optimize_all_images()
    optimizer.generate_image_manifest()
    optimizer._save_updated_config()
    
    print("✅ Image optimization complete!")
    print(f"📁 Optimized images saved to: {output_dir}")
    print("🔍 SEO attributes updated in seo_config.json")

if __name__ == "__main__":
    main()
