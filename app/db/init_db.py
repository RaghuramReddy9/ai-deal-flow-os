import sqlite3

from .constants import DB_PATH


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_deals_table() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_name TEXT NOT NULL,
            industry TEXT,
            location TEXT,
            asking_price TEXT,
            revenue TEXT,
            ebitda TEXT,
            description TEXT,
            source_url TEXT UNIQUE,
            source_name TEXT,
            stage TEXT DEFAULT 'New',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


def get_existing_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()
    return {row["name"] for row in rows}


def add_missing_columns() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    existing = get_existing_columns(conn, "deals")

    columns_to_add = {
        # parsed numeric fields for scoring
        "asking_price_value": "REAL",
        "revenue_value": "REAL",
        "ebitda_value": "REAL",

        # enrichment fields
        "normalized_industry": "TEXT",
        "ai_summary": "TEXT",
        "ai_risks": "TEXT",  # JSON string
        "recurring_revenue_signal": "INTEGER",
        "growth_potential": "INTEGER",
        "ai_score": "INTEGER",
        "deterministic_score": "INTEGER",
        "final_score": "INTEGER",
        "score_reason": "TEXT",
        "investment_label": "TEXT",

        # workflow/status fields
        "enrichment_status": "TEXT DEFAULT 'pending'",
        "enrichment_error": "TEXT",
        "enriched_at": "TIMESTAMP",
        "llm_raw_json": "TEXT",

        # future notion sync
        "notion_sync_status": "TEXT DEFAULT 'pending'",
        "notion_sync_error": "TEXT",
        "notion_page_id": "TEXT",
        "notion_last_synced_at": "TIMESTAMP",
    }

    for column_name, column_type in columns_to_add.items():
        if column_name not in existing:
            cursor.execute(f"ALTER TABLE deals ADD COLUMN {column_name} {column_type}")

    conn.commit()
    conn.close()


def init_database() -> None:
    create_deals_table()
    add_missing_columns()


if __name__ == "__main__":
    init_database()
    print(f"Database initialized and migrated at: {DB_PATH}")
