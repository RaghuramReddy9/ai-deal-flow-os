from app.db.repository import clear_all_deals


def main():
    deleted_count = clear_all_deals()
    print(f"Deleted {deleted_count} deal(s) from SQLite.")


if __name__ == "__main__":
    main()
