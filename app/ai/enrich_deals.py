import json
from datetime import datetime, timezone

from dotenv import load_dotenv

from app.ai.client import OpenRouterClient
from app.ai.prompts import build_deal_enrichment_prompt
from app.ai.scoring import compute_deterministic_score, combine_scores, label_from_score
from app.db.repository import (
    get_unenriched_deals,
    update_deal_enrichment,
    mark_enrichment_failed,
)
from app.utils.parsing import parse_money_to_float


def parse_ai_json(raw_output: str) -> dict:
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        start = raw_output.find("{")
        end = raw_output.rfind("}")
        if start != -1 and end != -1 and end > start:
            data = json.loads(raw_output[start:end + 1])
        else:
            raise

    if not isinstance(data, dict):
        raise ValueError("AI output is not a JSON object.")

    return data


def validate_ai_output(ai_output: dict) -> dict:
    summary = ai_output.get("summary")
    industry = ai_output.get("industry")
    risk_flags = ai_output.get("risk_flags")

    if not isinstance(summary, str) or not summary.strip():
        summary = "No summary returned."

    if not isinstance(industry, str) or not industry.strip():
        industry = None

    if not isinstance(risk_flags, list):
        risk_flags = []

    try:
        growth_potential = int(ai_output.get("growth_potential", 3))
    except Exception:
        growth_potential = 3
    growth_potential = max(1, min(5, growth_potential))

    try:
        overall_score = int(ai_output.get("overall_score", 50))
    except Exception:
        overall_score = 50
    overall_score = max(0, min(100, overall_score))

    score_reason = ai_output.get("score_reason")
    if not isinstance(score_reason, str) or not score_reason.strip():
        score_reason = "No score reason returned."

    recurring_revenue_signal = bool(ai_output.get("recurring_revenue_signal", False))

    return {
        "summary": summary,
        "industry": industry,
        "recurring_revenue_signal": recurring_revenue_signal,
        "risk_flags": risk_flags,
        "growth_potential": growth_potential,
        "overall_score": overall_score,
        "score_reason": score_reason,
    }


def generate_validated_ai_output(prompt: str, llm_client, max_attempts: int = 3) -> tuple[str, dict]:
    """
    Retry a few times when the model returns empty or invalid JSON.
    """
    last_error = None
    last_raw_output = None

    for attempt in range(1, max_attempts + 1):
        raw_output = llm_client.generate(prompt)
        last_raw_output = raw_output

        try:
            ai_output = validate_ai_output(parse_ai_json(raw_output))
            return raw_output, ai_output
        except Exception as exc:
            last_error = exc
            print(f"Retrying AI output parse ({attempt}/{max_attempts}): {exc}")

    raise ValueError(f"AI output invalid after retries: {last_error}\nRaw output: {last_raw_output}")


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
        raw_output, ai_output = generate_validated_ai_output(prompt, llm_client)

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
        raw_text = raw_output if "raw_output" in locals() else None
        mark_enrichment_failed(deal_id, str(e), raw_text)
        print(f"Failed to enrich deal #{deal_id}: {e}")


def run(limit: int = 10) -> None:
    load_dotenv()
    deals = get_unenriched_deals(limit=limit)
    print(f"Found {len(deals)} deals to enrich")

    llm_client = OpenRouterClient()

    for deal in deals:
        enrich_one_deal(deal, llm_client)


if __name__ == "__main__":
    run(limit=10)
