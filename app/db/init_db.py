# Database initialization
import sqlite3
from pathlib import Path

DB_PATH = Path("data/processed/ai_deals.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


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


if __name__ == "__main__":
    create_deals_table()
    print(f"Database initialized at: {DB_PATH}")
