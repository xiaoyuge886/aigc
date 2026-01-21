#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discover_categories.py - Discover documentation categories from sitemap

Extracts unique categories from sitemap.xml for documentation discovery.

Usage:
    python discover_categories.py --sitemap https://docs.claude.com/sitemap.xml
    python discover_categories.py --sitemap https://docs.claude.com/sitemap.xml --domain docs.claude.com
    python discover_categories.py --sitemap https://docs.claude.com/sitemap.xml --format filter

Dependencies:
    pip install requests
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import re

from utils.script_utils import configure_utf8_output
configure_utf8_output()

try:
    import requests
except ImportError:
    print("❌ Missing dependency: requests")
    print("Install with: pip install requests")
    sys.exit(1)

def discover_categories(sitemap_url: str, domain: str | None = None, 
                        language_code: str = 'en') -> list[str]:
    """
    Discover unique categories from sitemap
    
    Args:
        sitemap_url: URL to sitemap.xml
        domain: Domain to filter (auto-detected if not provided)
        language_code: Language code to filter (default: 'en')
    
    Returns:
        List of unique category names (e.g., ['docs', 'api', 'resources'])
    """
    try:
        print(f"📄 Fetching sitemap: {sitemap_url}")
        # Import config for timeout
        from config_helpers import get_http_timeout
        timeout = get_http_timeout()
        response = requests.get(sitemap_url, timeout=timeout)
        response.raise_for_status()
        content = response.text
        
        # Extract domain if not provided
        if not domain:
            domain_match = re.search(r'https?://([^/]+)', sitemap_url)
            if domain_match:
                domain = domain_match.group(1)
            else:
                print("❌ Could not auto-detect domain from sitemap URL")
                return []
        
        print(f"   Domain: {domain}")
        print(f"   Language: {language_code}")
        
        # Find all URLs with pattern: domain/{language_code}/CATEGORY/
        # Pattern matches: domain/en/docs/, domain/en/api/, etc.
        pattern = rf'{re.escape(domain)}/{re.escape(language_code)}/([^/]+)/'
        matches = re.findall(pattern, content)
        categories = sorted(set(matches))
        
        print(f"   Found {len(categories)} unique categories")
        
        return categories
        
    except requests.RequestException as e:
        print(f"❌ Error fetching sitemap: {e}")
        return []
    except Exception as e:
        print(f"❌ Error discovering categories: {e}")
        return []

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Discover documentation categories from sitemap',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover all categories
  python discover_categories.py --sitemap https://docs.claude.com/sitemap.xml
  
  # Output as filter patterns for scraping
  python discover_categories.py --sitemap https://docs.claude.com/sitemap.xml --format filter
  
  # Output as JSON
  python discover_categories.py --sitemap https://docs.claude.com/sitemap.xml --format json
  
  # Specify domain explicitly
  python discover_categories.py --sitemap https://docs.claude.com/sitemap.xml --domain docs.claude.com
        """
    )
    
    parser.add_argument('--sitemap', required=True,
                       help='Sitemap URL (e.g., https://docs.claude.com/sitemap.xml)')
    parser.add_argument('--domain',
                       help='Domain to filter (auto-detected from sitemap URL if not provided)')
    parser.add_argument('--language', default='en',
                       help='Language code to filter (default: en)')
    parser.add_argument('--format', choices=['list', 'json', 'filter'], default='list',
                       help='Output format (default: list)')
    
    args = parser.parse_args()
    
    categories = discover_categories(args.sitemap, args.domain, args.language)
    
    if not categories:
        print("\n❌ No categories found")
        sys.exit(1)
    
    # Output in requested format
    if args.format == 'list':
        print(f"\n📋 Categories found ({len(categories)}):")
        for cat in categories:
            print(f"   /{args.language}/{cat}/")
    elif args.format == 'json':
        import json
        output = {
            'sitemap_url': args.sitemap,
            'domain': args.domain or 'auto-detected',
            'language': args.language,
            'categories': categories,
            'filter_patterns': [f"/{args.language}/{cat}/" for cat in categories]
        }
        print(json.dumps(output, indent=2))
    elif args.format == 'filter':
        # Output as filter patterns for scraping
        print(f"\n📋 Filter patterns for scraping:")
        for cat in categories:
            print(f'--filter "/{args.language}/{cat}/"')
    
    sys.exit(0)

if __name__ == '__main__':
    main()

