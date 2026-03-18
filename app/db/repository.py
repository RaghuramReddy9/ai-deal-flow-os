import sqlite3
from datetime import datetime, timezone
from typing import Any

from .constants import DB_PATH


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_table_exists() -> None:
    from app.db.init_db import init_database
    init_database()


def insert_deal(deal: dict[str, Any]) -> bool:
    ensure_table_exists()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT OR IGNORE INTO deals (
                deal_name,
                industry,
                location,
                asking_price,
                revenue,
                ebitda,
                description,
                source_url,
                source_name,
                stage
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                deal.get("deal_name"),
                deal.get("industry"),
                deal.get("location"),
                deal.get("asking_price"),
                deal.get("revenue"),
                deal.get("ebitda"),
                deal.get("description"),
                deal.get("source_url"),
                deal.get("source_name"),
                deal.get("stage", "New"),
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Database error: {e}")
        raise
    finally:
        conn.close()


def insert_deals(deals: list[dict[str, Any]]) -> dict[str, int]:
    inserted_count = 0
    skipped_count = 0

    for deal in deals:
        was_inserted = insert_deal(deal)
        if was_inserted:
            inserted_count += 1
        else:
            skipped_count += 1

    return {
        "inserted_count": inserted_count,
        "skipped_count": skipped_count,
    }


def get_unenriched_deals(limit: int = 20) -> list[dict[str, Any]]:
    ensure_table_exists()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM deals
        WHERE enrichment_status IS NULL
           OR enrichment_status = 'pending'
           OR enrichment_status = 'failed'
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_deal_enrichment(deal_id: int, payload: dict[str, Any]) -> None:
    ensure_table_exists()

    allowed_fields = {
        "asking_price_value",
        "revenue_value",
        "ebitda_value",
        "normalized_industry",
        "ai_summary",
        "ai_risks",
        "recurring_revenue_signal",
        "growth_potential",
        "ai_score",
        "deterministic_score",
        "final_score",
        "score_reason",
        "investment_label",
        "enrichment_status",
        "enrichment_error",
        "enriched_at",
        "llm_raw_json",
        "notion_sync_status",
        "notion_sync_error",
        "notion_page_id",
        "notion_last_synced_at",
    }

    update_data = {k: v for k, v in payload.items() if k in allowed_fields}
    if not update_data:
        raise ValueError("No valid enrichment fields provided for update.")

    set_clause = ", ".join(f"{key} = ?" for key in update_data.keys())
    values = list(update_data.values()) + [deal_id]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"""
        UPDATE deals
        SET {set_clause}
        WHERE id = ?
        """,
        values,
    )

    conn.commit()
    conn.close()


def mark_enrichment_failed(deal_id: int, error_message: str, raw_output: str | None = None) -> None:
    update_deal_enrichment(
        deal_id,
        {
            "enrichment_status": "failed",
            "enrichment_error": error_message[:1000],
            "llm_raw_json": raw_output,
        },
    )


def get_deals_ready_for_notion(limit: int = 50) -> list[dict[str, Any]]:
    ensure_table_exists()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM deals
        WHERE enrichment_status = 'done'
          AND (notion_sync_status IS NULL OR notion_sync_status = 'pending')
        ORDER BY final_score DESC, created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_eligible_deals_for_notion(limit: int = 50) -> list[dict[str, Any]]:
    """
    Return only high-quality enriched deals for Notion sync.

    We sync deals labeled:
    - watchlist
    - strong_review

    This includes:
    - new rows that need a Notion page
    - previously synced rows that should update an existing page on rerun
    """
    ensure_table_exists()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM deals
        WHERE enrichment_status = 'done'
          AND investment_label IN ('watchlist', 'strong_review')
        ORDER BY final_score DESC, created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_deals_for_notion_sync(limit: int = 50) -> list[dict[str, Any]]:
    """
    Fetch eligible deals that do not have a Notion page yet.
    """
    ensure_table_exists()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM deals
        WHERE enrichment_status = 'done'
          AND investment_label IN ('watchlist', 'strong_review')
          AND notion_page_id IS NULL
        ORDER BY final_score DESC, created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_existing_notion_deals(limit: int = 50) -> list[dict[str, Any]]:
    """
    Fetch eligible deals that already have a Notion page.
    """
    ensure_table_exists()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM deals
        WHERE enrichment_status = 'done'
          AND investment_label IN ('watchlist', 'strong_review')
          AND notion_page_id IS NOT NULL
        ORDER BY final_score DESC, created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_notion_sync_success(deal_id: int, notion_page_id: str) -> None:
    """Save successful Notion sync details for a deal."""
    update_deal_enrichment(
        deal_id,
        {
            "notion_sync_status": "done",
            "notion_sync_error": None,
            "notion_page_id": notion_page_id,
            "notion_last_synced_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def mark_notion_sync_failure(deal_id: int, error_message: str | None = None) -> None:
    """Mark a deal as failed during Notion sync."""
    update_deal_enrichment(
        deal_id,
        {
            "notion_sync_status": "failed",
            "notion_sync_error": (error_message or "")[:1000] or None,
        },
    )


def mark_deal_notion_synced(deal_id: int, notion_page_id: str) -> None:
    """
    Wrapper with a clearer name for Notion sync success.
    """
    mark_notion_sync_success(deal_id, notion_page_id)


def mark_deal_notion_failed(deal_id: int, error_message: str | None = None) -> None:
    """
    Wrapper with a clearer name for Notion sync failure.

    We currently store only the failed status in SQLite.
    The error message is accepted so the sync loop can stay simple.
    """
    mark_notion_sync_failure(deal_id, error_message)


def reset_notion_sync_for_eligible_deals() -> int:
    """
    Reset Notion sync fields for eligible deals so they can be synced again.

    This is useful after deleting old test pages from Notion.
    """
    ensure_table_exists()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE deals
        SET notion_sync_status = 'pending',
            notion_page_id = NULL,
            notion_last_synced_at = NULL
        WHERE investment_label IN ('watchlist', 'strong_review')
        """
    )

    updated_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return updated_rows


def get_all_deals(limit: int = 100) -> list[dict[str, Any]]:
    ensure_table_exists()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM deals
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def clear_all_deals() -> int:
    """
    Remove all deals so the pipeline can be tested from a clean slate.
    """
    ensure_table_exists()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS cnt FROM deals")
    existing_count = cursor.fetchone()["cnt"]

    cursor.execute("DELETE FROM deals")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'deals'")

    conn.commit()
    conn.close()
    return existing_count


def get_existing_source_urls() -> set[str]:
    """
    Return all source URLs already stored in SQLite.
    """
    ensure_table_exists()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT source_url FROM deals WHERE source_url IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    return {row["source_url"] for row in rows}
