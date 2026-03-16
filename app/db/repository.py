import sqlite3
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


def insert_deal(deal: dict[str, Any]) -> None:
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
    except Exception as e:
        print(f"Database error: {e}")
        raise
    finally:
        conn.close()


def insert_deals(deals: list[dict[str, Any]]) -> None:
    for deal in deals:
        insert_deal(deal)


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