#!/usr/bin/env python3
"""
ArcadeForge - Static Game Site Generator
Main entry point for generating game websites
"""

import argparse
import sys
import os
from pathlib import Path
from core.generator_refactored import SiteGenerator
from core.performance_logger import log_error, log_warn, print_build_summary


def get_available_sites():
    """Get list of available sites from the sites directory"""
    sites_dir = Path(__file__).parent / "sites"
    sites = []
    
    if sites_dir.exists():
        for site_path in sites_dir.iterdir():
            if site_path.is_dir() and not site_path.name.startswith('.'):
                # Check if site has required files
                settings_file = site_path / "settings.py"
                if settings_file.exists():
                    sites.append(site_path.name)
    
    return sorted(sites)


def display_menu(sites):
    """Display interactive menu for site selection"""
    print("\n" + "=" * 60)
    print("🎮 ArcadeForge - Static Game Site Generator 🎮")
    print("=" * 60)
    
    if not sites:
        print("\n❌ No sites found in the sites/ directory")
        print("   Please create a site configuration first.")
        return None
    
    print("\n📋 Available Websites:")
    print("-" * 40)
    
    for i, site in enumerate(sites, 1):
        print(f"  [{i}] {site}")
    
    print(f"  [0] Exit")
    print("-" * 40)
    
    while True:
        try:
            choice = input("\n🎯 Enter number to generate website (or 0 to exit): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(sites):
                selected_site = sites[choice_num - 1]
                print(f"\n✅ Selected: {selected_site}")
                return selected_site
            else:
                print(f"❌ Invalid choice. Please enter a number between 0 and {len(sites)}")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user")
            return None


def ask_force_rebuild():
    """Ask user if they want to force rebuild"""
    print("\n🔄 Rebuild Options:")
    print("  [1] Normal build (incremental - faster)")
    print("  [2] Force rebuild (regenerate everything)")
    
    while True:
        choice = input("\n📦 Select build type (1 or 2): ").strip()
        if choice == "1":
            return False
        elif choice == "2":
            return True
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")


def generate_site(site_name, force=False, output_dir=None, site_url=None):
    """Generate the specified site"""
    try:
        print(f"\n🚀 Generating website: {site_name}")
        print("=" * 60)
        
        # Create generator instance
        generator = SiteGenerator(
            site=site_name,
            output_dir=output_dir,
            site_url=site_url,
            force=force
        )
        
        # Generate the site
        generator.generate_site()
        
        # Print build summary
        print_build_summary()
        
        print("\n✅ Website generation complete!")
        print(f"📁 Output directory: output/{site_name}/")
        print(f"🌐 To view the site, run: python -m http.server 5000 --bind 0.0.0.0")
        print(f"   from the output/{site_name}/ directory")
        
    except MemoryError as e:
        log_error("Main", f"Out of memory during site generation: {str(e)}", "❌")
        print("⚠️ Try reducing the number of parallel workers or processing fewer images at once")
        sys.exit(1)
    except PermissionError as e:
        log_error("Main", f"Permission denied: {str(e)}", "❌")
        print("⚠️ Check file permissions in the output directory")
        sys.exit(1)
    except FileNotFoundError as e:
        log_error("Main", f"Required file not found: {str(e)}", "❌")
        sys.exit(1)
    except (OSError, IOError) as e:
        log_error("Main", f"File system error: {str(e)}", "❌")
        sys.exit(1)
    except ValueError as e:
        log_error("Main", f"Configuration error: {str(e)}", "❌")
        sys.exit(1)
    except KeyboardInterrupt:
        log_warn("Main", "Site generation interrupted by user", "⚠️")
        sys.exit(0)
    except Exception as e:
        log_error("Main", f"Unexpected error during site generation: {type(e).__name__}: {str(e)}", "❌")
        sys.exit(1)


def main():
    """Main entry point for the site generator"""
    parser = argparse.ArgumentParser(
        description='Generate static game websites',
        epilog='Run without arguments for interactive mode'
    )
    parser.add_argument('--site', help='Site to generate (e.g., slitheriofree.net)')
    parser.add_argument('--force', action='store_true', help='Force regenerate all files')
    parser.add_argument('--output-dir', help='Output directory (optional)')
    parser.add_argument('--site-url', help='Site URL (optional)')
    parser.add_argument('--list', action='store_true', help='List available sites')
    
    args = parser.parse_args()
    
    # Get available sites
    sites = get_available_sites()
    
    # Handle --list flag
    if args.list:
        print("\n📋 Available Websites:")
        if sites:
            for site in sites:
                print(f"  • {site}")
            print(f"\n💡 To generate a site, run:")
            print(f"   python main.py --site <sitename>")
            print(f"   Example: python main.py --site {sites[0]}")
        else:
            print("  No sites found")
        sys.exit(0)
    
    # If --site is provided, use command line mode
    if args.site:
        if args.site not in sites:
            print(f"❌ Error: Site '{args.site}' not found")
            print(f"📋 Available sites: {', '.join(sites)}")
            sys.exit(1)
        
        generate_site(
            args.site, 
            force=args.force,
            output_dir=args.output_dir,
            site_url=args.site_url
        )
    else:
        # Interactive mode
        selected_site = display_menu(sites)
        
        if selected_site:
            force_rebuild = ask_force_rebuild()
            generate_site(selected_site, force=force_rebuild)


if __name__ == "__main__":
    main()