#!/usr/bin/env python3
"""
SEO Scanner - Comprehensive SEO analysis for generated websites
Scans for common SEO issues and provides actionable recommendations
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET


class SEOScanner:
    """Comprehensive SEO scanner for static websites"""
    
    def __init__(self, output_dir: str, site_url: str):
        self.output_dir = Path(output_dir)
        self.site_url = site_url.rstrip('/')
        self.issues = []
        self.warnings = []
        self.successes = []
        
    def scan_all(self) -> Dict:
        """Perform comprehensive SEO scan"""
        print("\n" + "="*60)
        print("🔍 Starting Comprehensive SEO Scan")
        print("="*60)
        
        # Scan different SEO aspects
        self._scan_meta_tags()
        self._scan_headings()
        self._scan_images()
        self._scan_sitemap()
        self._scan_robots_txt()
        self._scan_structured_data()
        self._scan_page_speed_factors()
        self._scan_mobile_optimization()
        self._scan_urls()
        self._scan_content_quality()
        self._scan_internal_links()
        self._scan_social_media_tags()
        
        return self._generate_report()
    
    def _scan_meta_tags(self):
        """Scan HTML files for meta tag issues"""
        html_files = list(self.output_dir.glob("**/*.html"))
        
        for html_file in html_files[:10]:  # Sample first 10 files
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check title tag
                title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                if not title_match:
                    self.issues.append(f"Missing title tag: {html_file.relative_to(self.output_dir)}")
                elif len(title_match.group(1)) > 60:
                    self.warnings.append(f"Title too long (>60 chars): {html_file.relative_to(self.output_dir)}")
                elif len(title_match.group(1)) < 30:
                    self.warnings.append(f"Title too short (<30 chars): {html_file.relative_to(self.output_dir)}")
                
                # Check meta description
                desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', content, re.IGNORECASE)
                if not desc_match:
                    self.issues.append(f"Missing meta description: {html_file.relative_to(self.output_dir)}")
                elif len(desc_match.group(1)) > 160:
                    self.warnings.append(f"Description too long (>160 chars): {html_file.relative_to(self.output_dir)}")
                elif len(desc_match.group(1)) < 50:
                    self.warnings.append(f"Description too short (<50 chars): {html_file.relative_to(self.output_dir)}")
                
                # Check canonical URL
                if '<link rel="canonical"' not in content:
                    self.issues.append(f"Missing canonical URL: {html_file.relative_to(self.output_dir)}")
                
                # Check viewport meta
                if 'viewport' not in content:
                    self.issues.append(f"Missing viewport meta tag: {html_file.relative_to(self.output_dir)}")
                    
            except (OSError, IOError, UnicodeDecodeError) as e:
                self.warnings.append(f"Failed to scan {html_file.name}: {str(e)}")
    
    def _scan_headings(self):
        """Check heading structure"""
        html_files = list(self.output_dir.glob("**/*.html"))
        
        for html_file in html_files[:5]:  # Sample first 5 files
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for H1
                h1_count = len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE))
                if h1_count == 0:
                    self.issues.append(f"Missing H1 tag: {html_file.relative_to(self.output_dir)}")
                elif h1_count > 1:
                    self.warnings.append(f"Multiple H1 tags ({h1_count}): {html_file.relative_to(self.output_dir)}")
                
                # Check heading hierarchy
                h2_count = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
                h3_count = len(re.findall(r'<h3[^>]*>', content, re.IGNORECASE))
                
                if h3_count > 0 and h2_count == 0:
                    self.warnings.append(f"H3 without H2: {html_file.relative_to(self.output_dir)}")
                    
            except (OSError, IOError, UnicodeDecodeError):
                pass
    
    def _scan_images(self):
        """Check image optimization"""
        html_files = list(self.output_dir.glob("**/*.html"))
        
        for html_file in html_files[:5]:  # Sample first 5 files
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for alt attributes
                img_tags = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
                for img_tag in img_tags[:5]:  # Check first 5 images per file
                    if 'alt=' not in img_tag:
                        self.issues.append(f"Image missing alt text in {html_file.relative_to(self.output_dir)}")
                        break
                    
                    # Check for empty alt
                    if 'alt=""' in img_tag or "alt=''" in img_tag:
                        self.warnings.append(f"Empty alt text in {html_file.relative_to(self.output_dir)}")
                        break
                        
                # Check for lazy loading
                if img_tags and 'loading="lazy"' not in content:
                    self.warnings.append(f"Images not using lazy loading: {html_file.relative_to(self.output_dir)}")
                    
            except (OSError, IOError, UnicodeDecodeError):
                pass
    
    def _scan_sitemap(self):
        """Check sitemap.xml"""
        sitemap_path = self.output_dir / "sitemap.xml"
        
        if not sitemap_path.exists():
            self.issues.append("Missing sitemap.xml")
            return
        
        try:
            tree = ET.parse(sitemap_path)
            root = tree.getroot()
            
            # Count URLs
            urls = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url")
            if len(urls) == 0:
                self.issues.append("Empty sitemap.xml")
            else:
                self.successes.append(f"Sitemap contains {len(urls)} URLs")
                
            # Check for lastmod dates
            lastmods = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
            if len(lastmods) == 0:
                self.warnings.append("Sitemap URLs missing lastmod dates")
                
        except (ET.ParseError, OSError, IOError) as e:
            self.issues.append(f"Invalid sitemap.xml: {str(e)}")
    
    def _scan_robots_txt(self):
        """Check robots.txt"""
        robots_path = self.output_dir / "robots.txt"
        
        if not robots_path.exists():
            self.issues.append("Missing robots.txt")
            return
        
        try:
            with open(robots_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "User-agent:" not in content:
                self.issues.append("Invalid robots.txt format")
            
            if "Sitemap:" not in content:
                self.warnings.append("robots.txt missing sitemap reference")
            else:
                self.successes.append("robots.txt properly configured with sitemap")
                
        except (OSError, IOError, UnicodeDecodeError) as e:
            self.issues.append(f"Failed to read robots.txt: {str(e)}")
    
    def _scan_structured_data(self):
        """Check for structured data (JSON-LD)"""
        html_files = list(self.output_dir.glob("**/*.html"))
        
        structured_data_found = False
        for html_file in html_files[:5]:  # Sample first 5 files
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'application/ld+json' in content:
                    structured_data_found = True
                    # Validate JSON-LD
                    json_ld_matches = re.findall(
                        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                        content, re.DOTALL | re.IGNORECASE
                    )
                    
                    for json_ld in json_ld_matches:
                        try:
                            data = json.loads(json_ld)
                            if '@context' not in data:
                                self.warnings.append(f"JSON-LD missing @context: {html_file.relative_to(self.output_dir)}")
                            if '@type' not in data:
                                self.warnings.append(f"JSON-LD missing @type: {html_file.relative_to(self.output_dir)}")
                        except json.JSONDecodeError:
                            self.issues.append(f"Invalid JSON-LD: {html_file.relative_to(self.output_dir)}")
                            
            except (OSError, IOError, UnicodeDecodeError):
                pass
        
        if structured_data_found:
            self.successes.append("Structured data (JSON-LD) implemented")
        else:
            self.warnings.append("No structured data found (consider adding JSON-LD)")
    
    def _scan_page_speed_factors(self):
        """Check page speed optimization factors"""
        # Check for minified files
        css_files = list(self.output_dir.glob("**/*.css"))
        js_files = list(self.output_dir.glob("**/*.js"))
        
        # Check CSS
        for css_file in css_files[:2]:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple check for minification
                    if '\n\n' in content or '  ' in content:
                        self.warnings.append(f"CSS not minified: {css_file.name}")
            except (OSError, IOError, UnicodeDecodeError):
                pass
        
        # Check service worker
        sw_path = self.output_dir / "sw.js"
        if sw_path.exists():
            self.successes.append("Service Worker implemented (offline support)")
        else:
            self.warnings.append("No Service Worker found")
    
    def _scan_mobile_optimization(self):
        """Check mobile optimization"""
        manifest_path = self.output_dir / "site.webmanifest"
        
        if manifest_path.exists():
            self.successes.append("PWA manifest found")
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    
                if 'name' not in manifest:
                    self.warnings.append("PWA manifest missing 'name'")
                if 'icons' not in manifest or len(manifest.get('icons', [])) == 0:
                    self.warnings.append("PWA manifest missing icons")
                    
            except (OSError, IOError, json.JSONDecodeError):
                self.issues.append("Invalid PWA manifest")
        else:
            self.warnings.append("Missing PWA manifest (site.webmanifest)")
    
    def _scan_urls(self):
        """Check URL structure"""
        html_files = list(self.output_dir.glob("**/*.html"))
        
        for html_file in html_files[:10]:
            rel_path = str(html_file.relative_to(self.output_dir))
            
            # Check for URL issues
            if '__' in rel_path:
                self.warnings.append(f"URL contains double underscores: {rel_path}")
            
            if rel_path.count('/') > 3:
                self.warnings.append(f"URL too deep (>3 levels): {rel_path}")
            
            # Check for spaces or special characters
            if ' ' in rel_path or '%20' in rel_path:
                self.issues.append(f"URL contains spaces: {rel_path}")
    
    def _scan_content_quality(self):
        """Check content quality factors"""
        # Check FAQ implementation
        faq_implemented = False
        html_files = list(self.output_dir.glob("**/*.html"))
        
        for html_file in html_files[:5]:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '"FAQPage"' in content or 'itemtype="https://schema.org/FAQPage"' in content:
                        faq_implemented = True
                        break
            except (OSError, IOError, UnicodeDecodeError):
                pass
        
        if not faq_implemented:
            self.warnings.append("FAQ structured data not implemented")
        else:
            self.successes.append("FAQ structured data found")
    
    def _scan_internal_links(self):
        """Check internal linking"""
        html_files = list(self.output_dir.glob("**/*.html"))
        
        for html_file in html_files[:5]:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for broken internal links (only relative URLs starting with /)
                # Exclude protocol-relative URLs (starting with //)
                internal_links = re.findall(r'href="(/[^/"][^"]*)"', content)
                
                for link in internal_links[:10]:
                    # Skip protocol-relative URLs (e.g., //fonts.gstatic.com)
                    if link.startswith('//'):
                        continue
                        
                    # Remove anchor and query strings
                    clean_link = link.split('#')[0].split('?')[0]
                    
                    if clean_link.endswith('/'):
                        link_path = self.output_dir / clean_link.lstrip('/') / 'index.html'
                    else:
                        link_path = self.output_dir / clean_link.lstrip('/')
                    
                    if not link_path.exists() and not link_path.with_suffix('.html').exists():
                        self.issues.append(f"Broken internal link {link} in {html_file.relative_to(self.output_dir)}")
                        break
                        
            except (OSError, IOError, UnicodeDecodeError):
                pass
    
    def _scan_social_media_tags(self):
        """Check Open Graph and Twitter Card tags"""
        html_files = list(self.output_dir.glob("**/*.html"))
        
        for html_file in html_files[:5]:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check Open Graph tags
                og_tags = ['og:title', 'og:description', 'og:image', 'og:url']
                missing_og = []
                
                for tag in og_tags:
                    if f'property="{tag}"' not in content:
                        missing_og.append(tag)
                
                if missing_og:
                    self.warnings.append(f"Missing Open Graph tags ({', '.join(missing_og)}): {html_file.relative_to(self.output_dir)}")
                
                # Check Twitter Card tags
                if 'twitter:card' not in content:
                    self.warnings.append(f"Missing Twitter Card tags: {html_file.relative_to(self.output_dir)}")
                    
            except (OSError, IOError, UnicodeDecodeError):
                pass
    
    def _generate_report(self) -> Dict:
        """Generate SEO report"""
        total_issues = len(self.issues) + len(self.warnings)
        
        print("\n" + "="*60)
        print("📊 SEO SCAN RESULTS")
        print("="*60)
        
        if self.issues:
            print("\n❌ CRITICAL ISSUES (Fix immediately):")
            for issue in self.issues[:10]:  # Show first 10
                print(f"  • {issue}")
            if len(self.issues) > 10:
                print(f"  ... and {len(self.issues) - 10} more issues")
        
        if self.warnings:
            print("\n⚠️  WARNINGS (Should fix):")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  • {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")
        
        if self.successes:
            print("\n✅ GOOD PRACTICES FOUND:")
            for success in self.successes:
                print(f"  • {success}")
        
        # Calculate SEO score
        base_score = 100
        critical_penalty = len(self.issues) * 10
        warning_penalty = len(self.warnings) * 3
        seo_score = max(0, min(100, base_score - critical_penalty - warning_penalty))
        
        print("\n" + "="*60)
        print(f"🎯 SEO SCORE: {seo_score}/100")
        
        if seo_score >= 90:
            print("   Excellent SEO! Minor improvements possible.")
        elif seo_score >= 70:
            print("   Good SEO, but room for improvement.")
        elif seo_score >= 50:
            print("   Fair SEO. Several issues need attention.")
        else:
            print("   Poor SEO. Critical issues must be addressed.")
        
        print("="*60)
        
        return {
            "score": seo_score,
            "issues": self.issues,
            "warnings": self.warnings,
            "successes": self.successes,
            "total_problems": total_issues
        }


def run_seo_scan(site_name: str):
    """Run SEO scan for a specific site"""
    output_dir = Path(__file__).parent.parent / "output" / site_name
    site_url = f"https://{site_name}/"
    
    if not output_dir.exists():
        print(f"❌ Output directory not found: {output_dir}")
        return None
    
    scanner = SEOScanner(output_dir, site_url)
    return scanner.scan_all()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        site = sys.argv[1]
    else:
        site = "slitheriofree.net"
    
    run_seo_scan(site)