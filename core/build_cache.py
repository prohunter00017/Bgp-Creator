#!/usr/bin/env python3
"""
Build Cache System for Incremental Builds
Tracks file modification times and content hashes to enable fast incremental builds
"""

import os
import json
import hashlib
import time
from typing import Dict, Set, List, Optional, Any
from pathlib import Path


class BuildCache:
    """
    Manages build cache to enable incremental builds by tracking file changes
    """
    
    def __init__(self, cache_file: str = ".build_cache.json"):
        """
        Initialize build cache
        
        Args:
            cache_file: Path to cache file (relative to project root)
        """
        self.cache_file = cache_file
        self.cache_data = {}
        self.current_build_time = time.time()
        
        # Categories of files to track
        self.file_categories = {
            'content': [],      # HTML content files
            'static': [],       # Static assets (CSS, JS, images)
            'templates': [],    # Jinja2 templates
            'config': [],       # Configuration files
            'processed_images': []  # Source images processed by ImageOptimizer
        }
        
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load existing cache data from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache_data = json.load(f)
                print(f"📋 Loaded build cache from {self.cache_file}")
            except (json.JSONDecodeError, OSError) as e:
                print(f"⚠️  Could not load build cache: {e}")
                self.cache_data = {}
        else:
            print(f"📋 No existing build cache found, starting fresh")
            self.cache_data = {}
    
    def save_cache(self) -> None:
        """Save current cache data to file"""
        try:
            # Update build timestamp
            self.cache_data['last_build'] = self.current_build_time
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2)
            print(f"💾 Saved build cache to {self.cache_file}")
        except OSError as e:
            print(f"⚠️  Could not save build cache: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA-256 hash of file content
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA-256 hash of file content
        """
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except OSError:
            return ""
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get file information including modification time and content hash
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file info (mtime, hash, size)
        """
        try:
            stat = os.stat(file_path)
            return {
                'mtime': stat.st_mtime,
                'size': stat.st_size,
                'hash': self._get_file_hash(file_path)
            }
        except OSError:
            return {'mtime': 0, 'size': 0, 'hash': ''}
    
    def scan_directory(self, directory: str, patterns: Optional[List[str]] = None, 
                      category: str = 'static') -> List[str]:
        """
        Scan directory for files matching patterns
        
        Args:
            directory: Directory to scan
            patterns: List of file patterns (e.g., ['*.html', '*.css'])
            category: File category for tracking
            
        Returns:
            List of found file paths
        """
        if not os.path.exists(directory):
            return []
        
        files = []
        patterns = patterns or ['*']
        
        for pattern in patterns:
            if pattern == '*':
                # All files
                for root, dirs, filenames in os.walk(directory):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
            else:
                # Use glob for pattern matching
                import glob
                pattern_path = os.path.join(directory, '**', pattern)
                files.extend(glob.glob(pattern_path, recursive=True))
        
        # Filter out directories and add to category
        file_paths = [f for f in files if os.path.isfile(f)]
        self.file_categories[category].extend(file_paths)
        
        return file_paths
    
    def track_files(self, file_paths: List[str], category: str = 'static') -> None:
        """
        Add files to tracking for a specific category
        
        Args:
            file_paths: List of file paths to track
            category: Category to assign files to
        """
        if category not in self.file_categories:
            self.file_categories[category] = []
        
        self.file_categories[category].extend(file_paths)
    
    def has_changes(self, file_paths: Optional[List[str]] = None, category: Optional[str] = None,
                   force: bool = False) -> bool:
        """
        Check if any tracked files have changed since last build
        
        Args:
            file_paths: Specific files to check (optional)
            category: Specific category to check (optional)
            force: Force rebuild regardless of changes
            
        Returns:
            True if changes detected or force is True
        """
        if force:
            print("🔄 Force rebuild requested")
            return True
        
        if not self.cache_data:
            print("📋 No cache data, assuming first build")
            return True
        
        files_to_check = []
        
        if file_paths:
            files_to_check = file_paths
        elif category:
            files_to_check = self.file_categories.get(category, [])
        else:
            # Check all tracked files
            for cat_files in self.file_categories.values():
                files_to_check.extend(cat_files)
        
        changed_files = self.get_changed_files(files_to_check)
        
        if changed_files:
            print(f"📝 {len(changed_files)} file(s) changed since last build")
            changed_list = list(changed_files)  # Convert set to list
            for file_path in changed_list[:5]:  # Show first 5
                print(f"   • {os.path.relpath(file_path)}")
            if len(changed_files) > 5:
                print(f"   • ... and {len(changed_files) - 5} more")
            return True
        
        print("✅ No changes detected, skipping rebuild")
        return False
    
    def get_changed_files(self, file_paths: List[str]) -> Set[str]:
        """
        Get list of files that have changed since last build
        
        Args:
            file_paths: Files to check for changes
            
        Returns:
            Set of changed file paths
        """
        changed_files = set()
        cached_files = self.cache_data.get('files', {})
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                # File was deleted
                if file_path in cached_files:
                    changed_files.add(file_path)
                continue
            
            current_info = self._get_file_info(file_path)
            cached_info = cached_files.get(file_path, {})
            
            # Compare modification time and hash
            if (current_info.get('mtime', 0) != cached_info.get('mtime', 0) or
                current_info.get('hash', '') != cached_info.get('hash', '') or
                current_info.get('size', 0) != cached_info.get('size', 0)):
                changed_files.add(file_path)
        
        return changed_files
    
    def update_file_cache(self, file_paths: List[str]) -> None:
        """
        Update cache with current file information
        
        Args:
            file_paths: Files to update in cache
        """
        if 'files' not in self.cache_data:
            self.cache_data['files'] = {}
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                self.cache_data['files'][file_path] = self._get_file_info(file_path)
    
    def clear_cache(self) -> None:
        """Clear all cache data"""
        self.cache_data = {}
        if os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
                print(f"🗑️  Cleared build cache")
            except OSError as e:
                print(f"⚠️  Could not remove cache file: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        total_files = sum(len(files) for files in self.file_categories.values())
        cached_files = len(self.cache_data.get('files', {}))
        last_build = self.cache_data.get('last_build')
        
        stats = {
            'total_tracked_files': total_files,
            'cached_files': cached_files,
            'last_build_time': last_build,
            'categories': {cat: len(files) for cat, files in self.file_categories.items()},
            'cache_file_exists': os.path.exists(self.cache_file)
        }
        
        return stats
    
    def print_cache_stats(self) -> None:
        """Print cache statistics"""
        stats = self.get_cache_stats()
        
        print("📊 Build Cache Statistics:")
        print(f"   • Total tracked files: {stats['total_tracked_files']}")
        print(f"   • Cached files: {stats['cached_files']}")
        
        if stats['last_build_time']:
            last_build = time.strftime('%Y-%m-%d %H:%M:%S', 
                                     time.localtime(stats['last_build_time']))
            print(f"   • Last build: {last_build}")
        
        print("   • File categories:")
        for category, count in stats['categories'].items():
            if count > 0:
                print(f"     - {category}: {count} files")
    
    def register_processed_image(self, source_image_path: str) -> None:
        """
        Register a source image as processed by ImageOptimizer
        
        Args:
            source_image_path: Path to the source image that was processed
        """
        if 'processed_images' not in self.cache_data:
            self.cache_data['processed_images'] = []
        
        # Normalize path for consistent tracking
        normalized_path = os.path.normpath(source_image_path)
        
        if normalized_path not in self.cache_data['processed_images']:
            self.cache_data['processed_images'].append(normalized_path)
            print(f"📝 Registered processed image: {os.path.relpath(normalized_path)}")
    
    def is_image_processed(self, image_path: str) -> bool:
        """
        Check if an image has been processed by ImageOptimizer
        
        Args:
            image_path: Path to the image to check
            
        Returns:
            True if image was already processed, False otherwise
        """
        if 'processed_images' not in self.cache_data:
            return False
        
        # Normalize path for consistent checking
        normalized_path = os.path.normpath(image_path)
        return normalized_path in self.cache_data['processed_images']
    
    def get_processed_images(self) -> List[str]:
        """
        Get list of all processed images
        
        Returns:
            List of processed image paths
        """
        return self.cache_data.get('processed_images', [])
    
    def clear_processed_images(self) -> None:
        """Clear the list of processed images"""
        if 'processed_images' in self.cache_data:
            del self.cache_data['processed_images']
            print("🗑️  Cleared processed images registry")