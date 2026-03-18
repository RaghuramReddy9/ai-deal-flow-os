from app.db.repository import reset_notion_sync_for_eligible_deals


def main():
    updated = reset_notion_sync_for_eligible_deals()
    print(f"Reset Notion sync status for {updated} eligible deal(s).")


if __name__ == "__main__":
    main()
