import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path("data/processed/ai_deals.db")


def get_connection() -> sqlite3.Connection:
    """Get database connection, creating database if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def ensure_table_exists():
    """Ensure the deals table exists."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_name TEXT,
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
    """)
    
    conn.commit()
    conn.close()


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