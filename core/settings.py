#!/usr/bin/env python3
"""
ARCADEFORGE SITE CONFIGURATION
==============================

This is the MAIN configuration file - edit this to customize your site!
All other config files will be generated from this one.
"""

# =============================================================================
# BASIC SITE SETTINGS (EDIT THESE!)
# =============================================================================

SITE_NAME = "Slither Io"
SITE_URL = "https://slitheriofree.net/"
SITE_DOMAIN = "slitheriofree.net"

# Game embed URL - where your game is hosted
GAME_EMBED_URL = "https://gulper.io/"

# Contact information
CONTACT_EMAIL = "support@slitheriofree.net"
CONTACT_PHONE = "+1-555-123-4567"

# Google Analytics ID (optional)
GOOGLE_ANALYTICS_ID = "G-FGRWDEFQY4"

# =============================================================================
# CSS THEME SETTINGS - Dark Theme
# =============================================================================

CSS_BG = "#000000"
CSS_FG = "#ffffff"
CSS_MUTED = "#999999"
CSS_BRAND = "#4a9eff"
CSS_BRAND_2 = "#357acc"
CSS_SURFACE = "#222222"
CSS_RADIUS = "8px"
CSS_FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
CONTAINER_MAX_WIDTH = "1400px"

# =============================================================================
# LANGUAGE SETTINGS - CHANGE THIS LINE TO SWITCH LANGUAGES!
# =============================================================================

DEFAULT_LANGUAGE = "en-US"  # English only

# =============================================================================
# INDEX PAGE CONTENT (THE ONLY CONTENT YOU NEED TO EDIT!)
# =============================================================================

# Homepage title (same for all languages - keep it simple)
INDEX_TITLE = "Slither Io"

# English homepage description
INDEX_DESCRIPTION = "Play Slither Io online for free! Control your snake, grow with pellets and defeat opponents in this exciting multiplayer io game."

# English SEO keywords
INDEX_SEO_KEYWORDS = "slither io, io games, free play, snake game, multiplayer online, browser game, arcade game, free online game"

# =============================================================================
# SOCIAL MEDIA & SEO
# =============================================================================

# Social media links (optional - leave empty if not needed)
SOCIAL_MEDIA = {
    "facebook": "https://www.facebook.com/slitheriofree",
    "twitter": "https://twitter.com/slitheriofree",
    "youtube": "https://www.youtube.com/@slitheriofree",
    "app_store": "https://apps.apple.com/us/app/slither-io/id1091944550",
    "play_store": "https://play.google.com/store/apps/details?id=air.com.hypah.io.slither&hl=en&gl=US"
}

# SEO filename (used for image names and URLs)
SEO_FILENAME = "slither-io"

# =============================================================================
# COMPANY/FOUNDER INFO (for structured data)
# =============================================================================

FOUNDER_INFO = {
    "name": "Game Creator",
    "job_title": "Creator",
    "twitter": "https://twitter.com/gamecreator",
    "linkedin": "https://www.linkedin.com/in/gamecreator"
}

COMPANY_ADDRESS = {
    "street": "123 Main Street",
    "city": "New York",
    "postal_code": "10001",
    "country": "US"
}

# =============================================================================
# ADVANCED SETTINGS (usually don't need to change)
# =============================================================================

# Image optimization settings
IMAGE_SIZES = [
    {"name": "mobile", "width": 480, "height": 270},
    {"name": "tablet", "width": 768, "height": 432},
    {"name": "desktop", "width": 1200, "height": 675},
    {"name": "large", "width": 1920, "height": 1080}
]

# Site pages and their priorities for sitemap
SITE_PAGES = [
    {"url": "", "priority": "1.0", "changefreq": "daily"},  # Homepage
    {"url": "pages/about-us.html", "priority": "0.8", "changefreq": "monthly"},
    {"url": "pages/contact.html", "priority": "0.7", "changefreq": "monthly"},
    {"url": "legal/privacy-policy.html", "priority": "0.5", "changefreq": "yearly"},
    {"url": "legal/terms-of-service.html", "priority": "0.5", "changefreq": "yearly"},
    {"url": "legal/cookies-policy.html", "priority": "0.5", "changefreq": "yearly"},
    {"url": "legal/dmca.html", "priority": "0.3", "changefreq": "yearly"},
    {"url": "legal/parents-information.html", "priority": "0.6", "changefreq": "monthly"}
]

# =============================================================================
# HELPER FUNCTIONS (don't edit these)
# =============================================================================

def get_page_title(page_key, language_code=None):
    """Get page title - index from config, others from page_content.py"""
    if page_key == "index":
        return INDEX_TITLE
    
    # English only - simplified (page_content.py was removed)
    return page_key.replace('-', ' ').title()

def get_page_description(page_key, language_code=None):
    """Get page description - index from config, others from page_content.py"""
    if page_key == "index":
        return INDEX_DESCRIPTION
    
    # English only - simplified (page_content.py was removed)
    return ""

def get_seo_keywords(page_key, language_code=None):
    """Get SEO keywords - only index has keywords (keep it simple)"""
    if page_key == "index":
        return INDEX_SEO_KEYWORDS
    
    # No keywords for other pages - keep it simple
    return ""

def get_site_config():
    """Get all configuration as a dictionary"""
    return {
        "site_name": SITE_NAME,
        "site_url": SITE_URL,
        "site_domain": SITE_DOMAIN,
        "game_embed_url": GAME_EMBED_URL,
        "contact_email": CONTACT_EMAIL,
        "contact_phone": CONTACT_PHONE,
        "google_analytics_id": GOOGLE_ANALYTICS_ID,
        "default_language": DEFAULT_LANGUAGE,
        "index_title": INDEX_TITLE,
        "index_description": INDEX_DESCRIPTION,
        "index_seo_keywords": INDEX_SEO_KEYWORDS,
        "social_media": SOCIAL_MEDIA,
        "seo_filename": SEO_FILENAME,
        "founder_info": FOUNDER_INFO,
        "company_address": COMPANY_ADDRESS,
        "image_sizes": IMAGE_SIZES,
        "site_pages": SITE_PAGES
    }

if __name__ == "__main__":
    import json
    config = get_site_config()
    print(json.dumps(config, indent=2, ensure_ascii=False))
