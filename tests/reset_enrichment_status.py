from app.db.repository import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    UPDATE deals
    SET
        asking_price_value = NULL,
        revenue_value = NULL,
        ebitda_value = NULL,
        normalized_industry = NULL,
        ai_summary = NULL,
        ai_risks = NULL,
        recurring_revenue_signal = NULL,
        growth_potential = NULL,
        ai_score = NULL,
        deterministic_score = NULL,
        final_score = NULL,
        score_reason = NULL,
        investment_label = NULL,
        enrichment_status = 'pending',
        enrichment_error = NULL,
        enriched_at = NULL,
        llm_raw_json = NULL,
        notion_sync_status = 'pending',
        notion_page_id = NULL,
        notion_last_synced_at = NULL
""")

conn.commit()
conn.close()

print("Reset enrichment fields for all deals.")