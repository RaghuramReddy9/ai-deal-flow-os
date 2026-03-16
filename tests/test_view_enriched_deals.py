from app.db.repository import get_all_deals

rows = get_all_deals(limit=20)

for row in rows:
    print("-" * 80)
    print(f"Deal #{row['id']}")
    print(f"Name               : {row['deal_name']}")
    print(f"Asking Price       : {row['asking_price']}")
    print(f"Parsed Price       : {row.get('asking_price_value')}")
    print(f"Revenue            : {row['revenue']}")
    print(f"Parsed Revenue     : {row.get('revenue_value')}")
    print(f"EBITDA             : {row['ebitda']}")
    print(f"Parsed EBITDA      : {row.get('ebitda_value')}")
    print(f"AI Score           : {row.get('ai_score')}")
    print(f"Deterministic Score: {row.get('deterministic_score')}")
    print(f"Final Score        : {row.get('final_score')}")
    print(f"Label              : {row.get('investment_label')}")
    print(f"Enrichment Status  : {row.get('enrichment_status')}")
    print(f"Summary            : {row.get('ai_summary')}")