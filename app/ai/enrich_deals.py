import json
from datetime import datetime, timezone

from app.ai.client import FakeLLMClient
from app.ai.prompts import build_deal_enrichment_prompt
from app.ai.scoring import compute_deterministic_score, combine_scores, label_from_score
from app.db.repository import (
    get_unenriched_deals,
    update_deal_enrichment,
    mark_enrichment_failed,
)
from app.utils.parsing import parse_money_to_float


def enrich_one_deal(deal: dict, llm_client) -> None:
    deal_id = deal["id"]

    try:
        asking_price_value = parse_money_to_float(deal.get("asking_price"))
        revenue_value = parse_money_to_float(deal.get("revenue"))
        ebitda_value = parse_money_to_float(deal.get("ebitda"))

        enriched_input = {
            **deal,
            "asking_price_value": asking_price_value,
            "revenue_value": revenue_value,
            "ebitda_value": ebitda_value,
        }

        prompt = build_deal_enrichment_prompt(deal)
        raw_output = llm_client.generate(prompt)
        ai_output = json.loads(raw_output)

        det = compute_deterministic_score(enriched_input, ai_output)
        final_score = combine_scores(
            ai_output.get("overall_score"),
            det["deterministic_score"],
        )

        payload = {
            "asking_price_value": asking_price_value,
            "revenue_value": revenue_value,
            "ebitda_value": ebitda_value,
            "normalized_industry": ai_output.get("industry"),
            "ai_summary": ai_output.get("summary"),
            "ai_risks": json.dumps(ai_output.get("risk_flags", [])),
            "recurring_revenue_signal": 1 if ai_output.get("recurring_revenue_signal") else 0,
            "growth_potential": ai_output.get("growth_potential"),
            "ai_score": ai_output.get("overall_score"),
            "deterministic_score": det["deterministic_score"],
            "final_score": final_score,
            "score_reason": ai_output.get("score_reason") or det["score_reason"],
            "investment_label": label_from_score(final_score),
            "enrichment_status": "done",
            "enrichment_error": None,
            "enriched_at": datetime.now(timezone.utc).isoformat(),
            "llm_raw_json": raw_output,
            "notion_sync_status": "pending",
        }

        update_deal_enrichment(deal_id, payload)
        print(f"Enriched deal #{deal_id}: score={final_score}, label={payload['investment_label']}")

    except Exception as e:
        mark_enrichment_failed(deal_id, str(e))
        print(f"Failed to enrich deal #{deal_id}: {e}")


def run(limit: int = 10) -> None:
    deals = get_unenriched_deals(limit=limit)
    print(f"Found {len(deals)} deals to enrich")

    llm_client = FakeLLMClient()

    for deal in deals:
        enrich_one_deal(deal, llm_client)


if __name__ == "__main__":
    run(limit=10)