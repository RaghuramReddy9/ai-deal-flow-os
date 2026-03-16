from app.db.repository import get_connection


def main():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT deal_name, industry, location, asking_price, revenue, ebitda, source_name
        FROM deals
        ORDER BY rowid DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()
    conn.close()

    print(f"Rows found: {len(rows)}")
    print("-" * 80)

    for i, row in enumerate(rows, start=1):
        deal_name, industry, location, asking_price, revenue, ebitda, source_name = row

        print(f"Deal #{i}")
        print(f"Name        : {deal_name}")
        print(f"Industry    : {industry}")
        print(f"Location    : {location}")
        print(f"Asking Price: {asking_price}")
        print(f"Revenue     : {revenue}")
        print(f"EBITDA      : {ebitda}")
        print(f"Source      : {source_name}")
        print("-" * 80)


if __name__ == "__main__":
    main()