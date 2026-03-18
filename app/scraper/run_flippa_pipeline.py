#!/usr/bin/env python3
"""
Flippa Pipeline Runner

Combines the Flippa scraping pipeline into one command:
1. Fetch Flippa search page
2. Extract listing URLs
3. Prefer fresh URLs not already in SQLite
4. Fetch detail pages
5. Parse listings
6. Insert into SQLite
"""

import argparse
import sys
import time
from typing import List

from app.db.repository import get_existing_source_urls, insert_deals
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

            if looks_blocked(html, meta.get("final_url", ""), meta.get("title", "")):
                print(f"Warning: page appears blocked (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(delay * (2 ** attempt))
                    continue
                raise Exception("Page appears to be blocked or captcha detected")

            return result
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Warning: fetch failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(delay * (2 ** attempt))
            else:
                raise e

    raise Exception(f"Failed to fetch after {max_retries} attempts")


def validate_deal_data(deal: DealListing) -> bool:
    """Basic validation of parsed deal data."""
    if not deal.title or len(deal.title.strip()) < 10:
        return False

    if not deal.source_url or "flippa.com" not in deal.source_url:
        return False

    if deal.profit and deal.revenue:
        if deal.profit.strip().lower() == deal.revenue.strip().lower():
            return False

    return True


def convert_deal_listing_to_dict(deal: DealListing) -> dict:
    """Convert DealListing to dict format expected by insert_deal."""
    return {
        "deal_name": deal.title,
        "industry": deal.listing_type,
        "location": deal.location,
        "asking_price": deal.asking_price,
        "revenue": deal.revenue,
        "ebitda": deal.profit,
        "description": deal.description,
        "source_url": deal.source_url,
        "source_name": deal.source_name,
        "stage": "New",
    }


def collect_fresh_listing_urls(limit: int, max_search_pages: int = 5) -> list[str]:
    """
    Collect fresh listing URLs across multiple Flippa search pages.
    """
    existing_urls = get_existing_source_urls()
    fresh_urls: list[str] = []
    seen_urls: set[str] = set()

    for page_number in range(1, max_search_pages + 1):
        print(f"\n=== Fetch Search Page {page_number} ===")
        search_html, search_meta = retry_fetch(fetch_search_page, page_number)
        print(f"Search page fetched: {search_meta['title']}")

        page_urls = extract_listing_urls(search_html)
        print(f"Found {len(page_urls)} listing URLs on search page {page_number}")

        for url in page_urls:
            if url in seen_urls:
                continue
            seen_urls.add(url)

            if url in existing_urls:
                continue

            fresh_urls.append(url)
            if len(fresh_urls) >= limit:
                return fresh_urls

    return fresh_urls


def run_pipeline(limit: int = 5) -> None:
    """Run the complete Flippa scraping pipeline."""
    print("Starting Flippa scraping pipeline...")
    print(f"Will process up to {limit} fresh listings")

    try:
        urls_to_process = collect_fresh_listing_urls(limit=limit)
    except Exception as e:
        print(f"Failed to collect fresh listing URLs: {e}")
        sys.exit(1)

    print(f"\nFound {len(urls_to_process)} fresh URLs not yet in SQLite")
    print(f"Processing {len(urls_to_process)} fresh URLs")

    if not urls_to_process:
        print("No new listing URLs to process")
        return

    print("\n=== Fetch Detail Pages ===")
    listings: List[DealListing] = []
    for i, url in enumerate(urls_to_process, 1):
        print(f"Fetching {i}/{len(urls_to_process)}: {url}")
        try:
            detail_html, detail_meta = retry_fetch(fetch_listing_page, url)
            print(f"Fetched: {detail_meta['title'][:50]}...")
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue

        try:
            deal = parse_listing_detail(detail_html, url)
            if not validate_deal_data(deal):
                print(f"Skipped invalid data for: {deal.title[:30]}...")
                continue

            listings.append(deal)
            print(f"Parsed: {deal.title[:50]}...")
        except Exception as e:
            print(f"Failed to parse {url}: {e}")
            continue

        if i < len(urls_to_process):
            time.sleep(1)

    print(f"\nSuccessfully parsed {len(listings)} listings")

    print("\n=== Insert Into SQLite ===")
    if listings:
        try:
            deal_dicts = [convert_deal_listing_to_dict(deal) for deal in listings]
            result = insert_deals(deal_dicts)
            print(f"Inserted new deals: {result['inserted_count']}")
            print(f"Skipped existing deals: {result['skipped_count']}")
        except Exception as e:
            print(f"Failed to insert deals: {e}")
            sys.exit(1)
    else:
        print("No valid listings to insert")

    print("\nScrape pipeline completed successfully")


def main():
    parser = argparse.ArgumentParser(description="Run Flippa scraping pipeline")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of fresh listings to process (default: 5)",
    )
    args = parser.parse_args()

    run_pipeline(limit=args.limit)


if __name__ == "__main__":
    main()
