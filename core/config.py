#!/usr/bin/env python3
"""
MINIMAL SITE CONFIG
===================

This is a minimal replacement for the complex site_config.py
It only provides the essential functionality needed by generate_site.py
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from .url_utils import URLBuilder

class SiteConfig:
    """Configuration class for site generation with support for multi-site architecture.
    
    Attributes:
        ads_enabled (bool): Whether advertisements are enabled
        ad_networks (Dict[str, Any]): Configuration for various ad networks
        ad_sizes (Dict[str, Dict[str, int]]): Ad size specifications by position
    """
    
    def __init__(self, language_code: str = "en-US", site: Optional[str] = None) -> None:
        # Initialize cross-platform path handling
        self.static_dir = None
        self._current_site = site
        
        # Load site-specific settings if site is provided
        if site:
            from .site_loader import load_site_settings, get_site_paths
            self._settings = load_site_settings(site)
            site_paths = get_site_paths(site)
            self.static_dir = site_paths["static_dir"]
        else:
            # Fallback to core settings
            try:
                from . import settings as simple_config
                self._settings = simple_config
            except ImportError:
                self._settings = None
        
        # Initialize properties from loaded settings with generic fallbacks
        if self._settings:
            self._site_name = getattr(self._settings, 'SITE_NAME', "Gaming Site")
            self.site_url = getattr(self._settings, 'SITE_URL', "https://example.com/")
            self.site_domain = getattr(self._settings, 'SITE_DOMAIN', "example.com")
            self.game_embed_url = getattr(self._settings, 'GAME_EMBED_URL', "https://example.com/game")
            self.google_analytics_id = getattr(self._settings, 'GOOGLE_ANALYTICS_ID', "")
            self.seo_filename = getattr(self._settings, 'SEO_FILENAME', "game")
        else:
            # Default fallback - generic gaming site
            self._site_name = "Gaming Site"
            self.site_url = "https://example.com/"
            self.site_domain = "example.com"
            self.game_embed_url = "https://example.com/game"
            self.google_analytics_id = ""
            self.seo_filename = "game"
        
        self.language = language_code
        self.current_year = datetime.now().year
        self.support_email = f"support@{self.site_domain}"
        
        # Initialize URLBuilder
        self.url_builder = URLBuilder(self.site_url)
        
        # Initialize ad configuration attributes (fixes LSP errors)
        self.ads_enabled = False
        self.ad_networks = {}
        self.ad_sizes = {}
        
        # Load ad settings from site-specific settings if available
        if self._settings:
            self.ads_enabled = getattr(self._settings, 'ADS_ENABLED', False)
            self.ad_networks = getattr(self._settings, 'AD_NETWORKS', {})
            self.ad_sizes = getattr(self._settings, 'AD_SIZES', {})
        
        # Minimal required properties
        self.language_config = {}
        self.seo_config = {
            "site_name": self.site_name,
            "site_url": self.site_url,
            "site_domain": self.site_domain,
            "seo_filename": self.seo_filename,
            "google_analytics_id": self.google_analytics_id,
            "game_embed": {"url": self.game_embed_url},
            "image_optimization": {}
        }

    def get_page_config(self, page_key: str) -> Dict[str, Any]:
        """Get page configuration with appropriate schemas.
        
        Args:
            page_key: The identifier for the page type
            
        Returns:
            Dictionary containing page configuration including title, description, and schemas
        """
        # Localized labels (duplicate minimal map to avoid circular deps)
        lang = (self.language or "en").lower()
        lang_short = lang.split('-')[0]
        nav_titles = {
            "de": {"home": "Home"},
            "en": {"home": "Home"},
            "fr": {"home": "Accueil"},
            "nl": {"home": "Home"},
        }.get(lang_short, {"home": "Home"})

        # Defaults
        page_title = page_key.title()
        # Use URLBuilder for canonical URLs
        canonical_url = self.url_builder.get_canonical_url(page_key)
        breadcrumbs = [
            {"title": nav_titles["home"], "url": "/"},
            {"title": page_title, "url": None}
        ]

        # Special-case index page: use root canonical and Home label
        if page_key == "index":
            page_title = self.centralized_game_name
            canonical_url = self.url_builder.get_canonical_url("")
            breadcrumbs = [
                {"title": nav_titles["home"], "url": "/"},
                {"title": nav_titles["home"], "url": None}
            ]

        # SEO-optimized titles (max 60 chars) and descriptions for different pages
        seo_titles = {
            "index": f"Play {self.centralized_game_name} Free - Browser Games",
            "about-us": f"About {self.site_name} - Free Games Online",
            "contact": f"Contact Us - {self.site_name} Support",
            "privacy-policy": f"Privacy Policy - {self.site_name}",
            "terms-of-service": f"Terms of Service - {self.site_name}",
            "404": f"Page Not Found - {self.site_name}",
            "offline": f"Offline - {self.site_name} Games"
        }
        
        seo_descriptions = {
            "index": f"Play {self.centralized_game_name} and hundreds of other free online games instantly. No downloads, no registration required. Enjoy the best browser-based gaming experience.",
            "about-us": f"Discover {self.site_name}, your premier destination for free online games. Learn about our mission to bring quality browser gaming to players worldwide.",
            "contact": f"Get in touch with the {self.site_name} team. We're here to help with game issues, feedback, or partnership inquiries. Contact us today.",
            "privacy-policy": f"Read our comprehensive privacy policy to understand how {self.site_name} protects your data and ensures safe online gaming for all players.",
            "terms-of-service": f"Review the terms and conditions for using {self.site_name}. Understand your rights and responsibilities while enjoying our free online games.",
            "404": f"The page you're looking for couldn't be found on {self.site_name}. Return to our homepage to continue playing free online games.",
            "offline": f"You appear to be offline. Check your internet connection to continue playing games on {self.site_name}."
        }
        
        # Use SEO-optimized values or fall back to defaults
        final_title = seo_titles.get(page_key, f"{page_title} - {self.site_name} Free Online Games")
        final_description = seo_descriptions.get(page_key, f"Enjoy {page_title} and other free online games at {self.site_name}. No downloads required, play instantly in your browser.")
        
        config = {
            "page_title": final_title,
            "page_description": final_description,
            "canonical_url": canonical_url,
            "current_page": page_key,
            "breadcrumbs": breadcrumbs,
            "custom_html_content": f"content_html/{page_key}.html"
        }
        
        # Add specific schemas based on page type
        if page_key == "index":
            # Index page gets: SoftwareApplication + FAQ schemas (WebSite now in base context)
            config.update({
                "software_application_schema": self.get_software_application_schema(),
                "faq_schema": self.get_faq_schema()
            })
        
        # All pages get breadcrumb schema
        config["breadcrumb_schema"] = self.get_breadcrumb_schema(config["breadcrumbs"])
        
        return config
    
    def get_base_context(self) -> Dict[str, Any]:
        """Get minimal base context for templates - Organization + WebSite schemas on ALL pages.
        
        Returns:
            Dictionary containing base context for all templates
        """
        # English only navigation titles
        nav_titles = {"home": "Home", "games": "Games", "about": "About", "contact": "Contact", "privacy": "Privacy"}
        footer_titles = {"privacy": "Privacy Policy", "terms": "Terms of Service", "contact": "Contact", "dmca": "DMCA"}

        # Dark Theme CSS design tokens
        # Try to get from settings first, then use defaults
        try:
            from . import settings as simple_config
            css_bg = getattr(simple_config, "CSS_BG", "#000000")
            css_fg = getattr(simple_config, "CSS_FG", "#ffffff")
            css_muted = getattr(simple_config, "CSS_MUTED", "#999999")
            css_brand = getattr(simple_config, "CSS_BRAND", "#4a9eff")
            css_brand_2 = getattr(simple_config, "CSS_BRAND_2", "#357acc")
            css_surface = getattr(simple_config, "CSS_SURFACE", "#222222")
            css_radius = getattr(simple_config, "CSS_RADIUS", "8px")
            css_font_family = getattr(simple_config, "CSS_FONT_FAMILY", "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif")
            container_max_width = getattr(simple_config, "CONTAINER_MAX_WIDTH", "1400px")
        except ImportError:
            # Fallback to defaults if settings not available
            css_bg = "#000000"
            css_fg = "#ffffff"
            css_muted = "#999999"
            css_brand = "#4a9eff"
            css_brand_2 = "#357acc"
            css_surface = "#222222"
            css_radius = "8px"
            css_font_family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
            container_max_width = "1400px"

        # Generate logo SEO attributes
        logo_seo_attributes = self.get_image_seo_attributes('/logo.png', context_type='logo')
        
        return {
            "site_name": self.site_name,
            "logo_seo_attributes": logo_seo_attributes,
            "site_url": self.site_url,
            "site_domain": self.site_domain,
            "support_email": self.support_email,
            "current_year": self.current_year,
            "language": self.language,
            "locale": self.language,
            "google_analytics_id": self.google_analytics_id,
            "game_embed": {"url": self.game_embed_url},
            "game_name": self.centralized_game_name,
            # Add ad configuration to context
            "ads_enabled": getattr(self, 'ads_enabled', False),
            "ad_networks": getattr(self, 'ad_networks', {}),
            "ad_sizes": getattr(self, 'ad_sizes', {}),
            "navigation": [
                {"title": nav_titles["home"], "url": "/", "key": "index"},
                {"title": nav_titles["games"], "url": "/games/", "key": "games"},
                {"title": nav_titles["about"], "url": self._get_about_url(), "key": "about"},
                {"title": nav_titles["contact"], "url": self._get_contact_url(), "key": "contact"},
                {"title": nav_titles["privacy"], "url": self._get_privacy_url(), "key": "privacy"}
            ],
            "footer_links": [
                {"title": footer_titles["privacy"], "url": self._get_privacy_url()},
                {"title": footer_titles["terms"], "url": self._get_terms_url()},
                {"title": footer_titles["contact"], "url": self._get_contact_url()},
                {"title": footer_titles["dmca"], "url": "/dmca/"}
            ],
            "robots_content": "index,follow",
            "og_type": "website",
            "og_image": self.url_builder.normalize_asset_path(f"/assets/images/seo/{self.seo_filename}.webp"),
            "theme_color": "#0369a1",
            # CSS tokens for templates
            "css_bg": css_bg,
            "css_fg": css_fg,
            "css_muted": css_muted,
            "css_brand": css_brand,
            "css_brand_2": css_brand_2,
            "css_surface": css_surface,
            "css_radius": css_radius,
            "css_font_family": css_font_family,
            "container_max_width": container_max_width,
            # Organization + WebSite schemas on ALL pages
            "organization_schema": self.get_organization_schema(),
            "website_schema": self.get_website_schema()
        }
    
    def get_dynamic_hero_image(self):
        """Get hero image filename with correct path"""
        # Use configured SEO filename or default
        seo_filename = self.seo_filename or "default"
        return f"/assets/images/seo/{seo_filename}.webp"
    
    def _get_about_url(self):
        """Get About page URL - English only"""
        return "/about-us/"
    
    def _get_contact_url(self):
        """Get Contact page URL - English only"""
        return "/contact/"
    
    def _get_privacy_url(self):
        """Get Privacy page URL - English only"""
        return "/privacy-policy/"
    
    def _get_terms_url(self):
        """Get Terms page URL - English only"""
        return "/terms-of-service/"
    
    def update_site_url(self, new_url: str) -> None:
        """Update site URL and related configuration.
        
        Args:
            new_url: The new site URL to use
        """
        if not new_url.startswith(('http://', 'https://')):
            new_url = f"https://{new_url}"
        self.site_url = new_url.rstrip('/') + '/'
        self.site_domain = self.site_url.split('://')[1].split('/')[0]
        self.support_email = f"support@{self.site_domain}"
        # Update URLBuilder with new site URL
        self.url_builder = URLBuilder(self.site_url)
        print(f"✅ Updated site URL to: {self.site_url}")
    
    # Additional properties needed by generate_site.py
    @property
    def centralized_description(self):
        if self._settings:
            return getattr(self._settings, 'INDEX_DESCRIPTION', f"Play {self.site_name} free online!")
        return f"Play {self.site_name} free online!"
    
    @property 
    def centralized_game_name(self):
        if self._settings:
            return getattr(self._settings, 'INDEX_TITLE', self.site_name)
        return self.site_name
    
    @property
    def site_name(self):
        return self._site_name
    
    @site_name.setter
    def site_name(self, value):
        self._site_name = value
    
    @property
    def css_bg(self):
        return "#ffffff"
    
    @property
    def theme_color(self):
        return "#0369a1"
    
    def get_favicon_links(self):
        """Get favicon links with root-absolute paths"""
        return [
            {"rel": "icon", "type": "image/x-icon", "href": "/favicon.ico"},
            {"rel": "icon", "type": "image/png", "sizes": "32x32", "href": "/assets/icons/favicon-32x32.png"},
            {"rel": "icon", "type": "image/png", "sizes": "192x192", "href": "/assets/icons/favicon-192x192.png"},
            {"rel": "apple-touch-icon", "href": "/assets/icons/favicon-192x192.png"},
            {"rel": "apple-touch-icon-precomposed", "href": "/assets/icons/favicon-192x192.png"}
        ]
    
    def get_breadcrumb_schema(self, breadcrumbs):
        """Get breadcrumb schema"""
        items = []
        for i, crumb in enumerate(breadcrumbs):
            item = {"@type": "ListItem", "position": i + 1, "name": crumb["title"]}
            if crumb.get("url") is not None:
                if crumb["url"] == "":
                    item["item"] = self.url_builder.get_canonical_url("")
                else:
                    # Use URLBuilder to ensure consistent URLs
                    item["item"] = self.url_builder.get_canonical_url(crumb['url'])
            items.append(item)
        
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList", 
            "itemListElement": items
        }
    
    def get_faq_schema(self):
        """Get FAQ schema for index page - load from static/faq.json"""
        try:
            # Use the static directory set by generator, fallback to site loader
            if hasattr(self, 'static_dir') and self.static_dir:
                static_dir = self.static_dir
            else:
                # Try to get static directory from site loader if available
                try:
                    from .site_loader import get_site_paths
                    # Use current site paths if available (this will be None for legacy mode)
                    site_paths = get_site_paths(getattr(self, '_current_site', None))
                    static_dir = site_paths['static_dir']
                except (ImportError, AttributeError, TypeError):
                    # Fallback to legacy path
                    project_root = os.path.dirname(os.path.dirname(__file__))
                    static_dir = os.path.join(project_root, "static")
            
            faq_file = os.path.join(static_dir, "faq.json")
            with open(faq_file, 'r', encoding='utf-8') as f:
                faq_schema = json.load(f)
            
            # Add @id field for consistency
            faq_schema["@id"] = f"{self.site_url}#faq"
            # Ensure language matches current site language
            faq_schema["inLanguage"] = (self.language or "en-US").split('-')[0]
            return faq_schema
        except FileNotFoundError:
            pass  # FAQ file is optional
        except json.JSONDecodeError as e:
            print(f"⚠️  Warning: Invalid JSON in FAQ file: {e}")
        except Exception as e:
            print(f"⚠️  Warning: Could not load FAQ schema: {e}")
            
        # Return minimal fallback FAQ schema for all exception cases
            return {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "How do I play this game?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Follow the game instructions and controls displayed on the screen to play."
                        }
                    }
                ]
            }
    
    def _generate_automatic_description(self, page_type, title):
        """Generate automatic description"""
        return f"Learn more about {title} - {self.site_name}"
    
    def get_organization_schema(self):
        """Get Organization schema for SEO with social media and company info"""
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": self.url_builder.get_canonical_url("") + "#organization",
            "name": self.site_name,
            "url": self.url_builder.get_canonical_url(""),
            "description": self.centralized_description,
            "email": self.support_email,
            "logo": {
                "@type": "ImageObject",
                "url": self.url_builder.get_og_image_url("logo.png"),
                "width": 1024,
                "height": 1024
            }
        }
        
        # Add social media links if available
        same_as = []
        if self._settings and hasattr(self._settings, 'SOCIAL_MEDIA'):
            social = self._settings.SOCIAL_MEDIA
            if social.get('facebook'):
                same_as.append(social['facebook'])
            if social.get('twitter'):
                same_as.append(social['twitter'])
            if social.get('youtube'):
                same_as.append(social['youtube'])
        
        # Don't include internal pages in sameAs - only external social profiles
        
        if same_as:
            schema["sameAs"] = same_as
        
        # Add founder info if available
        if self._settings and hasattr(self._settings, 'FOUNDER_INFO'):
            founder = self._settings.FOUNDER_INFO
            if founder.get('name'):
                schema["founder"] = {
                    "@type": "Person",
                    "name": founder['name'],
                    "jobTitle": founder.get('job_title', 'Founder')
                }
                # Add founder social links if present
                if founder.get('twitter'):
                    schema["founder"]["sameAs"] = [founder['twitter']]
                    if founder.get('linkedin'):
                        schema["founder"]["sameAs"].append(founder['linkedin'])
                elif founder.get('linkedin'):
                    schema["founder"]["sameAs"] = [founder['linkedin']]
        
        # Add company address if available
        if self._settings and hasattr(self._settings, 'COMPANY_ADDRESS'):
            address = self._settings.COMPANY_ADDRESS
            if address.get('street'):
                schema["address"] = {
                    "@type": "PostalAddress",
                    "streetAddress": address['street'],
                    "addressLocality": address.get('city', ''),
                    "postalCode": address.get('postal_code', ''),
                    "addressCountry": address.get('country', 'US')
                }
        
        return schema
    
    def get_website_schema(self):
        """Get WebSite schema for SEO"""
        return {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": self.url_builder.get_canonical_url("") + "#website",
            "name": self.site_name,
            "url": self.url_builder.get_canonical_url(""),
            "description": self.centralized_description,
            "publisher": {
                "@id": self.url_builder.get_canonical_url("") + "#organization"
            }
        }
    
    def get_software_application_schema(self):
        """Get SoftwareApplication schema for INDEX page only with app store links"""
        schema = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "@id": self.url_builder.get_canonical_url("") + "#software",
            "name": self.centralized_game_name,
            "url": self.url_builder.get_canonical_url(""),
            "description": self.centralized_description,
            "applicationCategory": "GameApplication",
            "operatingSystem": "Web Browser",
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock"
            },
        }
        
        # Add rating from settings if available
        if self._settings:
            rating = getattr(self._settings, 'APP_RATING', None)
            if rating:
                schema["aggregateRating"] = {
                    "@type": "AggregateRating",
                    "ratingValue": rating.get('rating_value', '4.5'),
                    "bestRating": rating.get('best_rating', '5'),
                    "ratingCount": rating.get('rating_count', '1250'),
                    "worstRating": rating.get('worst_rating', '1')
                }
        else:
            # Default rating if not configured
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": "4.5",
                "bestRating": "5",
                "ratingCount": "1250",
                "worstRating": "1"
            }
        
        # Add app store links if available
        install_targets = []
        if self._settings and hasattr(self._settings, 'SOCIAL_MEDIA'):
            social = self._settings.SOCIAL_MEDIA
            if social.get('app_store'):
                install_targets.append({
                    "@type": "EntryPoint",
                    "urlTemplate": social['app_store'],
                    "actionPlatform": "http://schema.org/IOSPlatform",
                    "name": "Download on App Store"
                })
            if social.get('play_store'):
                install_targets.append({
                    "@type": "EntryPoint",
                    "urlTemplate": social['play_store'],
                    "actionPlatform": "http://schema.org/AndroidPlatform", 
                    "name": "Get it on Google Play"
                })
        
        if install_targets:
            schema["potentialAction"] = {
                "@type": "InstallAction",
                "target": install_targets
            }
        
        # Add publisher (organization)
        schema["publisher"] = {
            "@type": "Organization",
            "@id": self.url_builder.get_canonical_url("") + "#organization"
        }
        
        return schema
    
    def get_game_software_application_schema(self, game_title, game_slug, game_description=None, game_rating=None):
        """Get CUSTOM SoftwareApplication schema for individual GAME pages"""
        import hashlib
        
        # Generate unique ratings per game based on slug
        try:
            h = int(hashlib.sha256(game_slug.encode('utf-8')).hexdigest()[:8], 16)
        except Exception:
            h = sum(ord(c) for c in game_slug)
        
        # Rating between 3.5 and 4.9
        rating_value = round(3.5 + ((h % 150) / 100.0), 1)
        if rating_value > 4.9:
            rating_value = 4.9
            
        # Rating count between 150 and 3500
        rating_count = 150 + (h % 3351)
        
        # Use custom rating if provided
        if game_rating:
            rating_value = game_rating.get("ratingValue", rating_value)
            rating_count = game_rating.get("ratingCount", rating_count)
        
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
                "@id": self.url_builder.get_canonical_url("") + "#website"
            }
        }
    
    
    def get_image_seo_attributes(self, image_name, context_type=None, game_title=None):
        """Get image SEO attributes with context-aware alt text
        
        Args:
            image_name: The image filename or path
            context_type: Type of image (logo, hero, game, screenshot, etc.)
            game_title: Title of the game if this is a game-specific image
        """
        # Generate context-specific alt text
        if game_title:
            # Game-specific images
            if context_type == "hero":
                alt_text = f"{game_title} game screenshot - Play {game_title} free online on {self.site_name}"
            elif context_type == "thumbnail":
                alt_text = f"{game_title} game thumbnail - Free online {game_title} game"
            elif context_type == "icon":
                alt_text = f"{game_title} game icon"
            else:
                alt_text = f"{game_title} - Play free online game on {self.site_name}"
        else:
            # Site-wide images
            if context_type == "logo":
                alt_text = f"{self.site_name} logo - Free online games"
            elif context_type == "hero":
                alt_text = f"{self.site_name} hero banner - Play free online games"
            elif context_type == "screenshot":
                alt_text = f"{self.site_name} website screenshot - Free online gaming platform"
            elif "favicon" in str(image_name).lower():
                alt_text = f"{self.site_name} favicon"
            elif "logo" in str(image_name).lower():
                alt_text = f"{self.site_name} logo - Free online games"
            else:
                alt_text = f"{self.site_name} - Play free online games"
        
        # Generate descriptive title
        if game_title:
            title_text = f"{game_title} on {self.site_name}"
        else:
            title_text = f"{self.site_name} - Free Online Games"
        
        return {
            "alt": alt_text,
            "title": title_text,
            "loading": "lazy",
            "decoding": "async"
        }
    
    def get_hero_image_config(self, image_name):
        """Get hero image config"""
        return {
            "alt_text": f"{self.site_name} - Play Free Online",
            "title": f"{self.site_name}",
            "loading": "eager",
            "decoding": "async"
        }
