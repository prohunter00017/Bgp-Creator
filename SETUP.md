# BGP Creator - Quick Setup Guide

## 🎮 What This Tool Does
BGP Creator generates complete gaming websites with games, SEO optimization, and ads support.

## 📁 Folder Structure
```
BgpCreator/
├── sites/          → Your website configurations
├── games/          → Your game files  
├── output/         → Generated websites
└── main.py         → Generator script
```

## 🚀 How to Add a New Website

### 1. Copy an Example Site
- Go to `sites/` folder
- Copy the `slitheriofree.net` folder
- Rename it to your domain (example: `mygames.com`)

### 2. Edit Settings
Open `sites/yourdomain.com/settings.py` and change:

```python
# Your Website Info
SITE_NAME = "Your Game Name"
SITE_URL = "https://yourdomain.com/"
SITE_DOMAIN = "yourdomain.com"

# Where Your Game is Hosted
GAME_EMBED_URL = "https://yourgame.com/"

# Contact Info
CONTACT_EMAIL = "support@yourdomain.com"

# Google Analytics (optional - leave empty if none)
GOOGLE_ANALYTICS_ID = ""

# Your Game Description
INDEX_DESCRIPTION = "Play your game online for free!"

# Social Media (optional - delete lines you don't use)
SOCIAL_MEDIA = {
    "facebook": "https://facebook.com/yourpage",
    "twitter": "https://twitter.com/yourhandle"
}
```

### 3. Add Your Logo
- Put your logo image in: `sites/yourdomain.com/static/logo.png`
- Best size: 512x512 pixels

### 4. Add Your Games
Put game HTML files in: `sites/yourdomain.com/content_html/games/`
- Example: `golf.html` for a golf game
- The system will automatically find and add them

### 5. Generate Your Website
Run this command:
```bash
cd BgpCreator
python main.py --site yourdomain.com
```

Your website will be in: `output/yourdomain.com/`

## 💰 Adding Ads (Optional)

Edit `sites/yourdomain.com/settings.py`:

```python
# Enable Ads
ADS_ENABLED = True

# For Google AdSense
AD_NETWORKS = {
    "google_adsense": {
        "enabled": True,
        "publisher_id": "ca-pub-YOUR-NUMBER-HERE"
    }
}
```

## 🎨 Changing Colors

In `settings.py`, change `COLOR_PALETTE`:
- `1` = Blue theme
- `2` = Purple theme  
- `3` = Green theme
- `4` = Orange theme

## ⭐ Changing Ratings

Edit the rating shown in Google:
```python
APP_RATING = {
    "rating_value": "4.8",    # Your rating (1-5)
    "rating_count": "2000"     # Number of reviews
}
```

## 📝 Editing Page Content

To edit About, Contact, or other pages:
1. Go to: `sites/yourdomain.com/content_html/`
2. Edit the HTML files directly
3. Regenerate the website

## 🔄 Updating Your Website

After any changes, just run:
```bash
python main.py --site yourdomain.com --force
```

## 📤 Publishing Your Website

1. Generate your site (see above)
2. Upload everything from `output/yourdomain.com/` to your web host
3. Done! Your site is live

## ❓ Need Help?

- Make sure Python 3 is installed
- Install required packages: `pip install Pillow psutil Jinja2`
- The `--force` flag rebuilds everything fresh

That's it! No coding needed - just edit the settings file and run the generator.