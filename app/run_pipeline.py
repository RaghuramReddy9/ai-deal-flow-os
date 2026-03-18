"""Run the full deal pipeline from scrape to Notion sync."""

import argparse

from dotenv import load_dotenv

from app.ai.enrich_deals import run as enrich_deals
from app.notion.sync_notion import sync_deals_to_notion
from app.scraper.run_flippa_pipeline import run_pipeline as run_scraper


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full AI Deal Flow pipeline")
    parser.add_argument(
        "--scrape-limit",
        type=int,
        default=15,
        help="Maximum number of listings to scrape",
    )
    parser.add_argument(
        "--enrich-limit",
        type=int,
        default=15,
        help="Maximum number of deals to enrich",
    )
    parser.add_argument(
        "--sync-limit",
        type=int,
        default=15,
        help="Maximum number of deals to sync to Notion",
    )
    parser.add_argument(
        "--refresh-existing",
        action="store_true",
        help="Also update deals already synced to Notion",
    )
    args = parser.parse_args()

    load_dotenv()

    try:
        print("\n=== STEP 1: SCRAPE DEALS ===")
        run_scraper(limit=args.scrape_limit)
    except Exception as e:
        print(f"[FAILED] Scrape step: {e}")
        return

    try:
        print("\n=== STEP 2: ENRICH / SCORE DEALS ===")
        enrich_deals(limit=args.enrich_limit)
    except Exception as e:
        print(f"[FAILED] Enrichment step: {e}")
        return

    try:
        print("\n=== STEP 3: SYNC TO NOTION ===")
        sync_deals_to_notion(
            limit=args.sync_limit,
            include_existing=args.refresh_existing,
        )
    except Exception as e:
        print(f"[FAILED] Notion sync step: {e}")
        return

    print("\n=== PIPELINE COMPLETE ===")


if __name__ == "__main__":
    main()