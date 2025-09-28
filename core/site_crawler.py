#!/usr/bin/env python3
"""
Site crawler module for discovering all generated pages and validating links.
Ensures complete sitemap coverage and identifies broken links or missing assets.
"""

import os
import re
from typing import Dict, List, Set, Tuple, Optional, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime
from .performance_logger import log_info, log_success, log_error, log_warn, time_operation, update_stats


class SiteCrawler:
    """Crawls generated site to discover all pages and validate links"""
    
    def __init__(self, output_dir: str, site_url: str):
        """
        Initialize the site crawler.
        
        Args:
            output_dir: Directory containing generated site files
            site_url: Base URL of the site (e.g., https://example.com/)
        """
        self.output_dir = output_dir
        self.site_url = site_url.rstrip('/') + '/'
        self.discovered_pages = set()
        self.broken_links = []
        self.missing_assets = []
        self.external_links = set()
        
    def crawl_site(self) -> Dict[str, Any]:
        """
        Crawl the entire site to discover all pages and validate links.
        
        Returns:
            Dictionary containing crawl results
        """
        with time_operation("site_crawling"):
            log_info("SiteCrawler", "Starting site crawl...", "🕷️")
            
            # Discover all HTML files
            self._discover_html_files()
            
            # Validate internal links and assets
            self._validate_links()
            
            # Generate results
            results = {
                'discovered_pages': sorted(list(self.discovered_pages)),
                'total_pages': len(self.discovered_pages),
                'broken_links': self.broken_links,
                'missing_assets': self.missing_assets,
                'external_links': sorted(list(self.external_links))
            }
            
            # Log summary
            log_success("SiteCrawler", f"Discovered {len(self.discovered_pages)} pages", "✅")
            if self.broken_links:
                log_warn("SiteCrawler", f"Found {len(self.broken_links)} broken links", "⚠️")
            if self.missing_assets:
                log_warn("SiteCrawler", f"Found {len(self.missing_assets)} missing assets", "⚠️")
            
            update_stats("site_crawling", files_processed=len(self.discovered_pages))
            
            return results
    
    def _discover_html_files(self):
        """Recursively discover all HTML files in the output directory"""
        for root, dirs, files in os.walk(self.output_dir):
            # Skip hidden and internal directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.output_dir)
                    
                    # Convert file path to URL
                    url_path = self._file_to_url(relative_path)
                    if url_path:
                        self.discovered_pages.add(url_path)
    
    def _file_to_url(self, file_path: str) -> Optional[str]:
        """
        Convert a file path to a clean URL.
        
        Args:
            file_path: Relative file path from output directory
            
        Returns:
            Clean URL path or None if should be excluded
        """
        # Normalize path separators
        file_path = file_path.replace('\\', '/')
        
        # Skip special files that shouldn't be in sitemap
        if file_path in ['404.html', 'offline.html']:
            return None
            
        # Convert index.html to clean URLs
        if file_path.endswith('/index.html'):
            # Directory index -> /directory/
            return '/' + file_path[:-10]  # Remove 'index.html'
        elif file_path == 'index.html':
            # Root index
            return '/'
        elif file_path.endswith('.html'):
            # Legacy .html file (shouldn't exist with clean URLs)
            log_warn("SiteCrawler", f"Found legacy HTML file: {file_path}", "⚠️")
            return '/' + file_path
        
        return None
    
    def _validate_links(self):
        """Validate all internal links and assets in discovered pages"""
        for page_url in self.discovered_pages:
            self._validate_page_links(page_url)
    
    def _validate_page_links(self, page_url: str):
        """
        Validate links in a specific page.
        
        Args:
            page_url: URL path of the page to validate
        """
        # Convert URL back to file path
        if page_url == '/':
            file_path = os.path.join(self.output_dir, 'index.html')
        else:
            # Clean URL -> add index.html
            file_path = os.path.join(self.output_dir, page_url.strip('/'), 'index.html')
        
        if not os.path.exists(file_path):
            # Try legacy .html file
            file_path = os.path.join(self.output_dir, page_url.strip('/') + '.html')
        
        if not os.path.exists(file_path):
            log_error("SiteCrawler", f"Cannot find file for URL: {page_url}", "❌")
            return
        
        # Read and parse the HTML file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract all links and assets
            links = self._extract_links(content)
            assets = self._extract_assets(content)
            
            # Validate each link
            for link in links:
                self._validate_link(link, page_url)
            
            # Validate each asset
            for asset in assets:
                self._validate_asset(asset, page_url)
                
        except Exception as e:
            log_error("SiteCrawler", f"Error reading {file_path}: {e}", "❌")
    
    def _extract_links(self, html_content: str) -> List[str]:
        """Extract all href links from HTML content"""
        # Find all href attributes
        href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        links = href_pattern.findall(html_content)
        return links
    
    def _extract_assets(self, html_content: str) -> List[str]:
        """Extract all asset references (images, scripts, stylesheets) from HTML content"""
        assets = []
        
        # Extract src attributes (images, scripts)
        src_pattern = re.compile(r'src=["\']([^"\']+)["\']', re.IGNORECASE)
        assets.extend(src_pattern.findall(html_content))
        
        # Extract stylesheet links
        link_pattern = re.compile(r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\']', re.IGNORECASE)
        assets.extend(link_pattern.findall(html_content))
        
        return assets
    
    def _validate_link(self, link: str, source_page: str):
        """
        Validate a single link.
        
        Args:
            link: The link to validate
            source_page: The page containing the link
        """
        # Skip anchors, mailto, tel, and javascript links
        if link.startswith(('#', 'mailto:', 'tel:', 'javascript:', 'data:')):
            return
        
        # Check if it's an external link
        if link.startswith(('http://', 'https://', '//')):
            parsed = urlparse(link)
            if parsed.netloc and parsed.netloc not in self.site_url:
                self.external_links.add(link)
            return
        
        # Internal link - check if it exists
        if link.startswith('/'):
            # Absolute path
            target_url = link
        else:
            # Relative path
            target_url = urljoin(source_page, link)
        
        # Check if the target exists
        if not self._url_exists(target_url):
            self.broken_links.append({
                'source': source_page,
                'target': link,
                'type': 'internal_link'
            })
    
    def _validate_asset(self, asset: str, source_page: str):
        """
        Validate a single asset reference.
        
        Args:
            asset: The asset path to validate
            source_page: The page containing the asset reference
        """
        # Skip external assets and data URIs
        if asset.startswith(('http://', 'https://', '//', 'data:')):
            return
        
        # Check if asset file exists
        if asset.startswith('/'):
            # Absolute path from web root
            # Split the URL path and use os.path.join to create proper OS path
            asset_parts = asset.lstrip('/').split('/')
            asset_path = os.path.join(self.output_dir, *asset_parts)
        else:
            # Relative path from current page
            page_dir = os.path.dirname(source_page.strip('/'))
            if page_dir:
                # Split URL paths into parts for proper OS path joining
                page_parts = page_dir.split('/')
                asset_parts = asset.split('/')
                asset_path = os.path.join(self.output_dir, *page_parts, *asset_parts)
            else:
                # Asset is relative to root
                asset_parts = asset.split('/')
                asset_path = os.path.join(self.output_dir, *asset_parts)
        
        # Normalize path (handles .. and . properly)
        asset_path = os.path.normpath(asset_path)
        
        if not os.path.exists(asset_path):
            self.missing_assets.append({
                'source': source_page,
                'asset': asset,
                'expected_path': asset_path
            })
    
    def _url_exists(self, url: str) -> bool:
        """
        Check if a URL corresponds to an existing file.
        
        Args:
            url: URL to check
            
        Returns:
            True if the URL exists, False otherwise
        """
        # Remove query string and fragment
        url = url.split('?')[0].split('#')[0]
        
        # Check if it's a discovered page
        if url in self.discovered_pages:
            return True
        
        # Check with trailing slash (directory index)
        if not url.endswith('/'):
            if url + '/' in self.discovered_pages:
                return True
        
        # Check for actual file
        if url == '/':
            file_path = os.path.join(self.output_dir, 'index.html')
        else:
            # Try as clean URL with index.html
            url_parts = url.strip('/').split('/')
            file_path = os.path.join(self.output_dir, *url_parts, 'index.html')
            if not os.path.exists(file_path):
                # Try as direct file
                url_parts = url.strip('/').split('/')
                file_path = os.path.join(self.output_dir, *url_parts)
                if not os.path.exists(file_path):
                    # Try with .html extension
                    url_parts = url.strip('/').split('/')
                    if url_parts:
                        url_parts[-1] = url_parts[-1] + '.html'
                        file_path = os.path.join(self.output_dir, *url_parts)
                    else:
                        file_path = os.path.join(self.output_dir, 'index.html')
        
        return os.path.exists(file_path)
    
    def generate_sitemap_entries(self) -> List[Dict[str, str]]:
        """
        Generate sitemap entries for all discovered pages.
        
        Returns:
            List of dictionaries with URL and metadata for sitemap
        """
        entries = []
        now = datetime.now().strftime('%Y-%m-%d')
        
        for page_url in sorted(self.discovered_pages):
            # Determine priority and change frequency based on URL
            if page_url == '/':
                priority = '1.0'
                changefreq = 'daily'
            elif page_url.startswith('/games/'):
                if page_url == '/games/':
                    priority = '0.9'
                    changefreq = 'daily'
                else:
                    priority = '0.8'
                    changefreq = 'weekly'
            elif page_url in ['/about-us/', '/contact/']:
                priority = '0.6'
                changefreq = 'monthly'
            elif page_url in ['/privacy-policy/', '/terms-of-service/', '/dmca/', '/cookies-policy/']:
                priority = '0.3'
                changefreq = 'yearly'
            else:
                priority = '0.5'
                changefreq = 'monthly'
            
            entries.append({
                'loc': self.site_url + page_url.lstrip('/'),
                'lastmod': now,
                'changefreq': changefreq,
                'priority': priority
            })
        
        return entries
    
    def validate_build(self, fail_on_errors: bool = True) -> bool:
        """
        Validate the build and optionally fail if errors are found.
        
        Args:
            fail_on_errors: Whether to raise an exception on errors
            
        Returns:
            True if build is valid, False otherwise
            
        Raises:
            ValueError: If fail_on_errors is True and errors are found
        """
        is_valid = True
        error_messages = []
        
        if self.broken_links:
            is_valid = False
            error_messages.append(f"Found {len(self.broken_links)} broken links")
            for link in self.broken_links[:5]:  # Show first 5
                log_error("SiteCrawler", f"Broken link in {link['source']}: {link['target']}", "🔗")
        
        if self.missing_assets:
            is_valid = False
            error_messages.append(f"Found {len(self.missing_assets)} missing assets")
            for asset in self.missing_assets[:5]:  # Show first 5
                log_error("SiteCrawler", f"Missing asset in {asset['source']}: {asset['asset']}", "🖼️")
        
        if not self.discovered_pages:
            is_valid = False
            error_messages.append("No pages were discovered")
        
        if is_valid:
            log_success("SiteCrawler", "Build validation passed!", "✅")
        else:
            log_error("SiteCrawler", f"Build validation failed: {', '.join(error_messages)}", "❌")
            if fail_on_errors:
                raise ValueError(f"Build validation failed: {', '.join(error_messages)}")
        
        return is_valid