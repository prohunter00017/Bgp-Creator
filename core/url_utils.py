#!/usr/bin/env python3
"""
URL utility module for consistent URL generation across the site.
Ensures proper canonical URLs, clean URLs, and SEO-friendly paths.
"""

from urllib.parse import urljoin


class URLBuilder:
    """Centralized URL builder for consistent URL generation"""
    
    def __init__(self, site_url: str):
        """
        Initialize URL builder with site base URL.
        
        Args:
            site_url: Base URL of the site (e.g., https://example.com/)
        """
        # Ensure site URL has trailing slash
        self.site_url = site_url.rstrip('/') + '/'
        
    def get_canonical_url(self, page_path: str) -> str:
        """
        Get canonical URL for a page with proper formatting.
        
        Args:
            page_path: Page path (e.g., 'about-us', '/games/', 'games/golf')
            
        Returns:
            Properly formatted canonical URL with trailing slash for directories
        """
        # Handle special cases
        if not page_path or page_path in ['/', 'index', 'index.html']:
            return self.site_url
        
        # Remove .html extension if present (legacy)
        if page_path.endswith('.html'):
            page_path = page_path[:-5]
        
        # Remove leading slash for proper joining
        page_path = page_path.lstrip('/')
        
        # Build the URL
        canonical = urljoin(self.site_url, page_path)
        
        # Ensure directories have trailing slash (clean URLs)
        # Game pages and other content pages should have trailing slash
        if not canonical.endswith('/') and not self._is_file_resource(canonical):
            canonical += '/'
        
        return canonical
    
    def get_relative_url(self, page_path: str) -> str:
        """
        Get relative URL for internal links.
        
        Args:
            page_path: Page path
            
        Returns:
            Relative URL with proper formatting
        """
        # Handle special cases
        if not page_path or page_path in ['index', 'index.html']:
            return '/'
        
        # Remove .html extension if present
        if page_path.endswith('.html'):
            page_path = page_path[:-5]
        
        # Ensure leading slash
        if not page_path.startswith('/'):
            page_path = '/' + page_path
        
        # Add trailing slash for clean URLs (except for file resources)
        if not page_path.endswith('/') and not self._is_file_resource(page_path):
            page_path += '/'
        
        return page_path
    
    def get_og_image_url(self, image_path: str) -> str:
        """
        Get absolute URL for Open Graph image.
        
        Args:
            image_path: Image path (can be relative or absolute)
            
        Returns:
            Absolute URL for the image
        """
        # If already absolute URL, return as is
        if image_path.startswith(('http://', 'https://', '//')):
            return image_path
        
        # Ensure leading slash for absolute path
        if not image_path.startswith('/'):
            image_path = '/' + image_path
        
        # Remove any double slashes
        image_path = image_path.replace('//', '/')
        
        # Build absolute URL
        return urljoin(self.site_url, image_path.lstrip('/'))
    
    def get_sitemap_url(self, page_path: str, priority: str = '0.5', 
                       changefreq: str = 'monthly') -> dict:
        """
        Get sitemap entry for a page.
        
        Args:
            page_path: Page path
            priority: Sitemap priority (0.0-1.0)
            changefreq: Change frequency
            
        Returns:
            Dictionary with sitemap entry data
        """
        from datetime import datetime
        
        return {
            'loc': self.get_canonical_url(page_path),
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'changefreq': changefreq,
            'priority': priority
        }
    
    def normalize_asset_path(self, asset_path: str) -> str:
        """
        Normalize asset paths for consistency.
        
        Args:
            asset_path: Asset path (image, CSS, JS, etc.)
            
        Returns:
            Normalized asset path
        """
        # Handle old img/ paths
        if asset_path.startswith('img/'):
            asset_path = '/assets/images/' + asset_path[4:]
        elif asset_path.startswith('/img/'):
            asset_path = '/assets/images/' + asset_path[5:]
        
        # Handle old css/ and js/ paths
        elif asset_path.startswith('css/'):
            asset_path = '/assets/css/' + asset_path[4:]
        elif asset_path.startswith('js/'):
            asset_path = '/assets/js/' + asset_path[3:]
        
        # Ensure leading slash for absolute paths
        elif not asset_path.startswith('/') and not asset_path.startswith(('http://', 'https://', '//', 'data:')):
            asset_path = '/' + asset_path
        
        return asset_path
    
    def _is_file_resource(self, path: str) -> bool:
        """
        Check if a path is a file resource (not a page).
        
        Args:
            path: Path to check
            
        Returns:
            True if path is a file resource
        """
        # Check for common file extensions
        file_extensions = [
            '.xml', '.txt', '.json', '.js', '.css',
            '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico',
            '.woff', '.woff2', '.ttf', '.eot',
            '.pdf', '.zip'
        ]
        
        lower_path = path.lower()
        for ext in file_extensions:
            if lower_path.endswith(ext):
                return True
        
        return False
    
    @staticmethod
    def clean_double_slashes(url: str) -> str:
        """
        Clean double slashes from URL (except after protocol).
        
        Args:
            url: URL to clean
            
        Returns:
            Cleaned URL
        """
        # Split protocol from the rest
        if '://' in url:
            protocol, rest = url.split('://', 1)
            # Clean double slashes in the path part
            rest = rest.replace('//', '/')
            return protocol + '://' + rest
        else:
            # No protocol, just clean all double slashes
            return url.replace('//', '/')