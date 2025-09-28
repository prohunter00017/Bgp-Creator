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
# AD PLACEMENT SETTINGS
# =============================================================================

# Enable/disable ads globally
ADS_ENABLED = True  # Set to False to disable all ads

# Ad network configuration (supports multiple networks)
AD_NETWORKS = {
    "ezoic": {
        "enabled": True,
        "placeholder_ids": {
            "before_game": "ezoic-pub-ad-placeholder-100",
            "after_game": "ezoic-pub-ad-placeholder-101", 
            "left_sidebar": "ezoic-pub-ad-placeholder-102",
            "right_sidebar": "ezoic-pub-ad-placeholder-103"
        }
    },
    "google_adsense": {
        "enabled": False,
        "publisher_id": "ca-pub-XXXXXXXXXXXXX",  # Replace with your AdSense publisher ID
        "slots": {
            "before_game": "1234567890",
            "after_game": "2345678901",
            "left_sidebar": "3456789012",
            "right_sidebar": "4567890123"
        }
    },
    "custom": {
        "enabled": False,
        "html": {
            "before_game": "<!-- Custom ad code here -->",
            "after_game": "<!-- Custom ad code here -->",
            "left_sidebar": "<!-- Custom ad code here -->",
            "right_sidebar": "<!-- Custom ad code here -->"
        }
    }
}

# Ad sizes for different positions (width x height in pixels)
AD_SIZES = {
    "before_game": {"width": 728, "height": 90},     # Leaderboard
    "after_game": {"width": 728, "height": 90},      # Leaderboard
    "left_sidebar": {"width": 160, "height": 600},   # Wide Skyscraper
    "right_sidebar": {"width": 160, "height": 600}   # Wide Skyscraper
}

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
    "facebook":
    "https://www.facebook.com/slitheriofree",
    "twitter":
    "https://twitter.com/slitheriofree",
    "youtube":
    "https://www.youtube.com/@slitheriofree",
    "app_store":
    "https://apps.apple.com/us/app/slither-io/id1091944550",
    "play_store":
    "https://play.google.com/store/apps/details?id=air.com.hypah.io.slither&hl=en&gl=US"
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
# RATING SETTINGS (for structured data)
# =============================================================================

# App/Game rating configuration for SEO structured data
APP_RATING = {
    "rating_value": "4.5",        # Current rating (1-5)
    "best_rating": "5",           # Maximum possible rating
    "worst_rating": "1",          # Minimum possible rating
    "rating_count": "1250"        # Number of ratings/reviews
}

# =============================================================================
# VISUAL THEME SETTINGS
# =============================================================================

# Color palette (1-4):
# 1 = Dark Ocean (deep blue with cyan accents)
# 2 = Neon Purple (cyberpunk purple with electric accents)  
# 3 = Forest Green (natural green with earth tones)
# 4 = Fire Orange (warm orange with energy accents)
COLOR_PALETTE = 1

# =============================================================================
# ADVANCED SETTINGS (usually don't need to change)
# =============================================================================

# Image optimization settings
IMAGE_SIZES = [{
    "name": "mobile",
    "width": 480,
    "height": 270
}, {
    "name": "tablet",
    "width": 768,
    "height": 432
}, {
    "name": "desktop",
    "width": 1200,
    "height": 675
}, {
    "name": "large",
    "width": 1920,
    "height": 1080
}]

# Site pages and their priorities for sitemap
SITE_PAGES = [
    {
        "url": "",
        "priority": "1.0",
        "changefreq": "daily"
    },  # Homepage
    {
        "url": "about-us/",
        "priority": "0.8",
        "changefreq": "monthly"
    },
    {
        "url": "contact/",
        "priority": "0.7",
        "changefreq": "monthly"
    },
    {
        "url": "privacy-policy/",
        "priority": "0.5",
        "changefreq": "yearly"
    },
    {
        "url": "terms-of-service/",
        "priority": "0.5",
        "changefreq": "yearly"
    },
    {
        "url": "cookies-policy/",
        "priority": "0.5",
        "changefreq": "yearly"
    },
    {
        "url": "dmca/",
        "priority": "0.3",
        "changefreq": "yearly"
    },
    {
        "url": "parents-information/",
        "priority": "0.6",
        "changefreq": "monthly"
    }
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
        "site_pages": SITE_PAGES,
        "ads_enabled": ADS_ENABLED,
        "ad_networks": AD_NETWORKS,
        "ad_sizes": AD_SIZES
    }


if __name__ == "__main__":
    import json
    config = get_site_config()
    print(json.dumps(config, indent=2, ensure_ascii=False))
