#!/usr/bin/env python3
"""
Flippa Pipeline Runner

Combines the entire Flippa scraping pipeline into one command:
1. Fetch Flippa search page
2. Extract listing URLs
3. Fetch first N detail pages
4. Parse listings
5. Insert into SQLite

Usage:
    python -m app.scraper.run_flippa_pipeline [--limit N]

Default limit is 5 listings.
"""

import argparse
import sys
import time
from typing import List

from app.db.repository import insert_deals
from app.scraper.broker_scraper import DealListing, looks_blocked
from app.scraper.sources.flippa import (
    extract_listing_urls,
    fetch_listing_page,
    fetch_search_page,
    parse_listing_detail,
)


def retry_fetch(fetch_func, *args, max_retries=3, delay=2):
    """Retry a fetch function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            result = fetch_func(*args)
            html, meta = result
            
            # Check if page is blocked
            if looks_blocked(html, meta.get('final_url', ''), meta.get('title', '')):
                print(f"⚠️  Page appears blocked (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise Exception("Page appears to be blocked or captcha detected")
            
            return result
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Fetch failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(delay * (2 ** attempt))
            else:
                raise e
    
    raise Exception(f"Failed to fetch after {max_retries} attempts")


def validate_deal_data(deal: DealListing) -> bool:
    """Basic validation of parsed deal data."""
    if not deal.title or len(deal.title.strip()) < 10:
        return False
    
    if not deal.source_url or 'flippa.com' not in deal.source_url:
        return False
    
    # Check for obviously wrong data
    if deal.profit and deal.revenue:
        # If profit exactly equals revenue, likely parsing error
        if deal.profit.strip().lower() == deal.revenue.strip().lower():
            return False
    
    return True


def convert_deal_listing_to_dict(deal: DealListing) -> dict:
    """Convert DealListing to dict format expected by insert_deal."""
    return {
        "deal_name": deal.title,
        "industry": deal.listing_type,  # listing_type maps to industry
        "location": deal.location,
        "asking_price": deal.asking_price,
        "revenue": deal.revenue,
        "ebitda": deal.profit,  # profit maps to ebitda
        "description": deal.description,
        "source_url": deal.source_url,
        "source_name": deal.source_name,
        "stage": "New",
    }


def run_pipeline(limit: int = 5) -> None:
    """Run the complete Flippa scraping pipeline."""
    print("🚀 Starting Flippa scraping pipeline...")
    print(f"📊 Will process up to {limit} listings")

    # Step 1: Fetch search page
    print("\n1️⃣ Fetching Flippa search page...")
    try:
        search_html, search_meta = retry_fetch(fetch_search_page)
        print(f"✅ Search page fetched: {search_meta['title']}")
    except Exception as e:
        print(f"❌ Failed to fetch search page: {e}")
        sys.exit(1)

    # Step 2: Extract listing URLs
    print("\n2️⃣ Extracting listing URLs...")
    try:
        urls = extract_listing_urls(search_html)
        print(f"✅ Found {len(urls)} listing URLs")
        
        if not urls:
            print("❌ No listing URLs found - search page may have changed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to extract URLs: {e}")
        sys.exit(1)

    # Limit to first N URLs
    urls_to_process = urls[:limit]
    print(f"📋 Processing first {len(urls_to_process)} URLs")

    # Step 3: Fetch detail pages
    print("\n3️⃣ Fetching detail pages...")
    listings: List[DealListing] = []
    for i, url in enumerate(urls_to_process, 1):
        print(f"   Fetching {i}/{len(urls_to_process)}: {url}")
        try:
            detail_html, detail_meta = retry_fetch(fetch_listing_page, url)
            print(f"   ✅ Fetched: {detail_meta['title'][:50]}...")
        except Exception as e:
            print(f"   ❌ Failed to fetch {url}: {e}")
            continue

        # Step 4: Parse listing
        try:
            deal = parse_listing_detail(detail_html, url)
            
            # Validate parsed data
            if not validate_deal_data(deal):
                print(f"   ⚠️  Skipped invalid data for: {deal.title[:30]}...")
                continue
                
            listings.append(deal)
            print(f"   ✅ Parsed: {deal.title[:50]}...")
        except Exception as e:
            print(f"   ❌ Failed to parse {url}: {e}")
            continue
        
        # Rate limiting: wait 1 second between requests
        if i < len(urls_to_process):
            time.sleep(1)

    print(f"\n📈 Successfully parsed {len(listings)} listings")

    # Step 5: Insert into database
    print("\n5️⃣ Inserting into SQLite database...")
    if listings:
        try:
            deal_dicts = [convert_deal_listing_to_dict(deal) for deal in listings]
            insert_deals(deal_dicts)
            print(f"✅ Inserted {len(deal_dicts)} deals into database")
        except Exception as e:
            print(f"❌ Failed to insert deals: {e}")
            sys.exit(1)
    else:
        print("⚠️  No valid listings to insert")

    print("\n🎉 Pipeline completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="Run Flippa scraping pipeline")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of listings to process (default: 5)"
    )
    args = parser.parse_args()

    run_pipeline(limit=args.limit)


if __name__ == "__main__":
    main()