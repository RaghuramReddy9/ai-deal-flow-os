import json


def build_deal_enrichment_prompt(deal: dict) -> str:
    payload = {
        "deal_name": deal.get("deal_name"),
        "industry": deal.get("industry"),
        "location": deal.get("location"),
        "asking_price": deal.get("asking_price"),
        "revenue": deal.get("revenue"),
        "ebitda": deal.get("ebitda"),
        "description": deal.get("description"),
        "source_url": deal.get("source_url"),
        "source_name": deal.get("source_name"),
    }

    return f"""
You are evaluating a small business acquisition opportunity for a deal sourcing pipeline.

Use only the provided deal data.
Do not invent missing facts.
If a field is unknown, use null.
Return valid JSON only. No markdown. No explanation.

Required JSON schema:
{{
  "summary": "2-4 sentence investment summary",
  "industry": "normalized industry label or null",
  "recurring_revenue_signal": true,
  "risk_flags": ["risk 1", "risk 2"],
  "growth_potential": 1,
  "overall_score": 1,
  "score_reason": "brief explanation"
}}

Rules:
- growth_potential must be an integer from 1 to 5
- overall_score must be an integer from 0 to 100
- recurring_revenue_signal must be true or false
- risk_flags must be an array of short strings
- summary must be concise and factual
- industry should normalize the listing into a cleaner category when possible

Deal:
{json.dumps(payload, ensure_ascii=False, indent=2)}
""".strip()