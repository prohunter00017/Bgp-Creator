#!/usr/bin/env python3
"""
SEO and Schema management module
Handles SEO optimization, structured data, and meta tags
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
from .url_utils import URLBuilder


class SEOManager:
    """Manages SEO optimization and structured data generation"""
    
    def __init__(self, site_url: str, site_name: str, output_dir: str):
        self.site_url = site_url.rstrip('/') + '/'
        self.site_name = site_name
        self.output_dir = output_dir
        self.url_builder = URLBuilder(site_url)
    
    def create_robots_txt(self, sitemap_url: Optional[str] = None) -> None:
        """
        Create robots.txt file.
        
        Args:
            sitemap_url: Optional custom sitemap URL
        """
        robots_content = [
            "User-agent: *",
            "Allow: /",
            "",
            "# Crawl-delay: 1",
            "",
            f"Sitemap: {sitemap_url or self.url_builder.get_canonical_url('sitemap.xml')}"
        ]
        
        robots_path = os.path.join(self.output_dir, "robots.txt")
        with open(robots_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(robots_content))
        
        print("📄 Generated robots.txt")
    
    def create_sitemap_xml(self, pages: List[Dict[str, Any]], 
                          games: Optional[List[Dict]] = None) -> None:
        """
        Create sitemap.xml file.
        
        Args:
            pages: List of page configurations
            games: Optional list of games to include
        """
        # Create root element
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # Add pages
        for page in pages:
            url = ET.SubElement(urlset, 'url')
            
            # Check if this is from the crawler (has 'loc' key) or old format (has 'url' key)
            if 'loc' in page:
                # From crawler - already has full URL
                page_url = page['loc']
            else:
                # Old format - build URL
                page_url = page.get('url', '')
                if not page_url.startswith('http'):
                    page_url = self.url_builder.get_canonical_url(page_url)
            
            ET.SubElement(url, 'loc').text = page_url
            ET.SubElement(url, 'changefreq').text = page.get('changefreq', 'monthly')
            ET.SubElement(url, 'priority').text = page.get('priority', '0.5')
            ET.SubElement(url, 'lastmod').text = page.get('lastmod', datetime.now().strftime('%Y-%m-%d'))
        
        # Add games if provided
        if games:
            for game in games:
                url = ET.SubElement(urlset, 'url')
                game_url = self.url_builder.get_canonical_url(f"games/{game['slug']}")
                ET.SubElement(url, 'loc').text = game_url
                ET.SubElement(url, 'changefreq').text = 'weekly'
                ET.SubElement(url, 'priority').text = '0.8'
                ET.SubElement(url, 'lastmod').text = datetime.now().strftime('%Y-%m-%d')
        
        # Pretty print XML
        xml_str = minidom.parseString(ET.tostring(urlset)).toprettyxml(indent="  ")
        
        # Write sitemap
        sitemap_path = os.path.join(self.output_dir, "sitemap.xml")
        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        
        print(f"📄 Generated sitemap.xml with {len(pages) + (len(games) if games else 0)} URLs")
    
    def create_manifest(self, config: Dict[str, Any]) -> None:
        """
        Create web manifest for PWA support.
        
        Args:
            config: Configuration dictionary with site details
        """
        # Get SEO filename for icons
        seo_filename = config.get('seo_filename', 'game')
        
        manifest = {
            "name": self.site_name,
            "short_name": self.site_name,
            "description": config.get('description', f"Play {self.site_name} online"),
            "start_url": "/",
            "display": "standalone",
            "orientation": "portrait",
            "theme_color": config.get('theme_color', "#0369a1"),
            "background_color": config.get('background_color', "#ffffff"),
            "icons": self._generate_icon_list(seo_filename),
            "screenshots": self._generate_screenshot_list(seo_filename),
            "categories": ["games", "entertainment"],
            "lang": config.get('language', 'en-US')
        }
        
        manifest_path = os.path.join(self.output_dir, "site.webmanifest")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        print("📄 Generated site.webmanifest")
    
    def _generate_icon_list(self, seo_filename: str) -> List[Dict[str, str]]:
        """Generate icon list for manifest"""
        sizes = ["72x72", "96x96", "128x128", "144x144", "152x152", 
                "192x192", "384x384", "512x512"]
        
        icons = []
        for size in sizes:
            icons.append({
                "src": self.url_builder.normalize_asset_path(f"/assets/pwa/{seo_filename}-icon-{size}.png"),
                "sizes": size,
                "type": "image/png",
                "purpose": "any"
            })
        
        # Add maskable icons
        for size in ["192x192", "512x512"]:
            icons.append({
                "src": self.url_builder.normalize_asset_path(f"/assets/pwa/{seo_filename}-icon-{size}-maskable.png"),
                "sizes": size,
                "type": "image/png",
                "purpose": "maskable"
            })
        
        return icons
    
    def _generate_screenshot_list(self, seo_filename: str) -> List[Dict[str, str]]:
        """Generate screenshot list for manifest"""
        return [
            {
                "src": self.url_builder.normalize_asset_path(f"/assets/pwa/{seo_filename}-screenshot-mobile.png"),
                "sizes": "390x844",
                "type": "image/png",
                "form_factor": "narrow",
                "label": "Mobile view"
            },
            {
                "src": self.url_builder.normalize_asset_path(f"/assets/pwa/{seo_filename}-screenshot-tablet.png"),
                "sizes": "768x1024",
                "type": "image/png",
                "form_factor": "wide",
                "label": "Tablet view"
            },
            {
                "src": self.url_builder.normalize_asset_path(f"/assets/pwa/{seo_filename}-screenshot-desktop.png"),
                "sizes": "1280x720",
                "type": "image/png",
                "form_factor": "wide",
                "label": "Desktop view"
            }
        ]
    
    def get_breadcrumb_schema(self, breadcrumbs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate breadcrumb schema for structured data.
        
        Args:
            breadcrumbs: List of breadcrumb items
            
        Returns:
            BreadcrumbList schema
        """
        items = []
        for i, crumb in enumerate(breadcrumbs):
            item = {
                "@type": "ListItem",
                "position": i + 1,
                "name": crumb["title"]
            }
            
            if crumb.get("url") is not None:
                url = crumb['url']
                if url == "" or url == "/":
                    item["item"] = self.url_builder.get_canonical_url("")
                else:
                    item["item"] = self.url_builder.get_canonical_url(url)
            
            items.append(item)
        
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": items
        }
    
    def get_organization_schema(self, support_email: str, 
                               logo_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate Organization schema for structured data.
        
        Args:
            support_email: Support email address
            logo_url: Optional logo URL
            
        Returns:
            Organization schema
        """
        return {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": f"{self.site_url}#organization",
            "name": self.site_name,
            "url": self.site_url,
            "email": support_email,
            "logo": {
                "@type": "ImageObject",
                "url": logo_url or self.url_builder.get_og_image_url("logo.png"),
                "width": 1024,
                "height": 1024
            }
        }
    
    def get_website_schema(self, description: str) -> Dict[str, Any]:
        """
        Generate WebSite schema for structured data.
        
        Args:
            description: Website description
            
        Returns:
            WebSite schema
        """
        return {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{self.site_url}#website",
            "name": self.site_name,
            "url": self.site_url,
            "description": description,
            "publisher": {
                "@id": f"{self.site_url}#organization"
            }
        }
    
    def get_software_application_schema(self, game_title: str, game_slug: str,
                                       game_description: Optional[str] = None,
                                       game_rating: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate SoftwareApplication schema for game pages.
        
        Args:
            game_title: Game title
            game_slug: Game URL slug
            game_description: Optional game description
            game_rating: Optional rating data
            
        Returns:
            SoftwareApplication schema
        """
        import hashlib
        
        # Generate default rating if not provided
        if not game_rating:
            try:
                h = int(hashlib.sha256(game_slug.encode('utf-8')).hexdigest()[:8], 16)
            except (UnicodeEncodeError, AttributeError):
                h = sum(ord(c) for c in game_slug)
            
            rating_value = round(3.5 + ((h % 150) / 100.0), 1)
            if rating_value > 4.9:
                rating_value = 4.9
            
            rating_count = 150 + (h % 3351)
        else:
            rating_value = game_rating.get("ratingValue", 4.5)
            rating_count = game_rating.get("ratingCount", 1000)
        
        return {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "@id": self.url_builder.get_canonical_url(f"games/{game_slug}") + "#software",
            "name": game_title,
            "url": self.url_builder.get_canonical_url(f"games/{game_slug}"),
            "description": game_description or f"Play {game_title} free online - {self.site_name}",
            "applicationCategory": "GameApplication",
            "operatingSystem": "Web Browser",
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock"
            },
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": str(rating_value),
                "bestRating": "5",
                "ratingCount": str(rating_count),
                "worstRating": "3"
            },
            "isPartOf": {
                "@type": "WebSite",
                "@id": f"{self.site_url}#website"
            }
        }