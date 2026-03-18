"""Notion synchronization module for pushing deal data."""

import argparse
import json
from pprint import pprint

from dotenv import load_dotenv

from app.db.repository import (
    get_deals_for_notion_sync,
    get_existing_notion_deals,
    mark_deal_notion_failed,
    mark_deal_notion_synced,
)
from app.notion.client import create_notion_page, update_notion_page


def map_deal_to_notion_properties(deal: dict) -> dict:
    stage = map_stage(deal)

    return {
        "Deal Name": {
            "title": [
                {
                    "text": {
                        "content": deal.get("deal_name") or "Untitled Deal"
                    }
                }
            ]
        },
        "Stage": {
            "select": {
                "name": stage
            }
        },
        "Summary": {
            "rich_text": [
                {
                    "text": {
                        "content": truncate_text(
                            deal.get("ai_summary") or deal.get("summary", ""),
                            1800,
                        )
                    }
                }
            ]
        },
        "Industry": {
            "rich_text": [
                {
                    "text": {
                        "content": truncate_text(
                            deal.get("normalized_industry") or deal.get("industry", ""),
                            1800,
                        )
                    }
                }
            ]
        },
        "Location": {
            "rich_text": [
                {
                    "text": {
                        "content": truncate_text(deal.get("location", ""), 1800)
                    }
                }
            ]
        },
        "Revenue": {
            "number": safe_number(deal.get("revenue_value") or deal.get("revenue"))
        },
        "EBITDA": {
            "number": safe_number(deal.get("ebitda_value") or deal.get("ebitda"))
        },
        "Asking Price": {
            "number": safe_number(deal.get("asking_price_value") or deal.get("asking_price"))
        },
        "Score": {
            "number": safe_number(
                deal.get("final_score") or deal.get("ai_score") or deal.get("score")
            )
        },
        "Risks": {
            "rich_text": [
                {
                    "text": {
                        "content": truncate_text(
                            format_risks(
                                deal.get("ai_risks")
                                or deal.get("risk_flags")
                                or deal.get("risks")
                            ),
                            1800,
                        )
                    }
                }
            ]
        },
        "Source URL": {
            "url": deal.get("source_url") or deal.get("url")
        },
    }


def safe_number(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def truncate_text(text, max_len=1800):
    text = str(text or "").strip()
    return text[:max_len]


def format_risks(risk_flags):
    if not risk_flags:
        return ""
    if isinstance(risk_flags, str):
        try:
            parsed = json.loads(risk_flags)
        except json.JSONDecodeError:
            return risk_flags
        if isinstance(parsed, list):
            return "; ".join(str(x) for x in parsed)
        return str(parsed)
    if isinstance(risk_flags, list):
        return "; ".join(str(x) for x in risk_flags)
    return str(risk_flags)


def map_stage(deal: dict) -> str:
    quality = (deal.get("investment_label") or deal.get("deal_quality") or "").lower()
    score = safe_number(
        deal.get("final_score") or deal.get("ai_score") or deal.get("score")
    )

    if quality == "strong_review":
        return "Review"
    if quality == "watchlist":
        return "Watchlist"
    if quality == "review":
        return "Review"
    if quality == "reject":
        return "Rejected"

    if score is not None:
        if score >= 75:
            return "Review"
        if score >= 60:
            return "Watchlist"
        return "Rejected"

    return "Scored"


def is_recoverable_notion_update_error(error: Exception) -> bool:
    """
    Some old Notion page IDs can become unusable over time.
    In those cases we create a fresh page and replace the stale page ID.
    """
    message = str(error).lower()

    recoverable_signals = [
        "can't edit block that is archived",
        "could not find page",
        "object_not_found",
        "page not found",
        "block not found",
        "inaccessible",
        "restricted resource",
    ]

    return any(signal in message for signal in recoverable_signals)


def sync_one_deal_to_notion(deal: dict) -> tuple[str, str]:
    # Create a new Notion page, or update the existing one on rerun.
    # If the stored page is archived or no longer usable, create a fresh page.
    properties = map_deal_to_notion_properties(deal)
    existing_page_id = deal.get("notion_page_id")

    if existing_page_id:
        try:
            result = update_notion_page(existing_page_id, properties)
            return "updated", result["id"]
        except Exception as exc:
            if not is_recoverable_notion_update_error(exc):
                raise

            result = create_notion_page(properties)
            return "recreated", result["id"]

    result = create_notion_page(properties)
    return "created", result["id"]


def dry_run_deals(limit: int = 5) -> None:
    # Dry run prints the payload only. No Notion page is created.
    deals = get_deals_for_notion_sync(limit=limit)
    deals.extend(get_existing_notion_deals(limit=limit))

    if not deals:
        print("No eligible deals ready for Notion sync.")
        return

    for index, deal in enumerate(deals, start=1):
        action = "update" if deal.get("notion_page_id") else "create"
        print(f"Deal #{index} (db id={deal['id']}, action={action})")
        pprint(map_deal_to_notion_properties(deal))
        print("-" * 80)


def sync_deals_to_notion(limit: int = 20, include_existing: bool = False) -> int:
    # First sync new eligible deals.
    new_deals = get_deals_for_notion_sync(limit=limit)
    deals = list(new_deals)

    # On reruns, include rows that already have a Notion page so they update.
    if include_existing:
        existing_deals = get_existing_notion_deals(limit=limit)
        deals.extend(existing_deals)

    synced_count = 0

    if not deals:
        print("No eligible deals ready for Notion sync.")
        return synced_count

    print(f"Found {len(deals)} deal(s) to sync.")

    for deal in deals:
        deal_id = deal["id"]
        deal_name = deal.get("deal_name") or "Untitled Deal"

        try:
            action, notion_page_id = sync_one_deal_to_notion(deal)
            mark_deal_notion_synced(deal_id, notion_page_id)
            synced_count += 1
            print(f"[SYNCED] Deal #{deal_id}: {deal_name} -> {notion_page_id} ({action})")
        except Exception as exc:
            mark_deal_notion_failed(deal_id, str(exc))
            print(f"[FAILED] Deal #{deal_id}: {deal_name} -> {exc}")

    return synced_count


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description="Sync enriched deals to Notion")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print mapped Notion payloads from SQLite without creating Notion pages",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of deals to dry-run or sync",
    )
    args = parser.parse_args()

    if args.dry_run:
        dry_run_deals(limit=args.limit)
    else:
        total = sync_deals_to_notion(limit=args.limit, include_existing=False)
        print(f"Synced {total} deal(s) to Notion")
