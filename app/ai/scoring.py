def safe_margin(revenue: float | None, ebitda: float | None) -> float | None:
    if revenue and ebitda and revenue > 0:
        return ebitda / revenue
    return None


def safe_multiple(asking_price: float | None, ebitda: float | None) -> float | None:
    if asking_price and ebitda and ebitda > 0:
        return asking_price / ebitda
    return None


def compute_deterministic_score(deal: dict, ai_output: dict) -> dict:
    score = 0
    reasons: list[str] = []

    revenue = deal.get("revenue_value")
    ebitda = deal.get("ebitda_value")
    asking_price = deal.get("asking_price_value")
    description = deal.get("description") or ""

    if revenue and revenue < 1000:
        score -= 10
        reasons.append("Revenue appears malformed or too small")

    if revenue and ebitda and ebitda > revenue:
        score -= 15
        reasons.append("Suspicious financial relationship: EBITDA exceeds revenue")

    if ebitda:
        score += 15
        reasons.append("EBITDA available")

    if revenue:
        score += 10
        reasons.append("Revenue available")

    if asking_price:
        score += 5
        reasons.append("Asking price available")

    margin = safe_margin(revenue, ebitda)
    if margin is not None:
        if margin > 0.15:
            score += 15
            reasons.append("Healthy EBITDA margin")
        elif margin < 0.05:
            score -= 10
            reasons.append("Weak EBITDA margin")

    if asking_price and 500_000 <= asking_price <= 5_000_000:
        score += 15
        reasons.append("Attractive SMB deal size")

    multiple = safe_multiple(asking_price, ebitda)
    if multiple is not None:
        if multiple < 4:
            score += 15
            reasons.append("Low purchase multiple")
        elif multiple > 7:
            score -= 10
            reasons.append("High purchase multiple")

    if ai_output.get("recurring_revenue_signal") is True:
        score += 10
        reasons.append("Recurring revenue signal")

    if deal.get("location"):
        score += 5
        reasons.append("Location available")

    if len(description) > 200:
        score += 5
        reasons.append("Detailed description")

    risk_flags = ai_output.get("risk_flags") or []
    if len(risk_flags) >= 3:
        score -= 10
        reasons.append("Multiple risk flags")

    missing_count = sum(
        1 for x in [revenue, ebitda, asking_price, deal.get("location"), description] if not x
    )
    if missing_count >= 3:
        score -= 15
        reasons.append("Too many missing fields")

    score = max(0, min(100, score))

    return {
        "deterministic_score": score,
        "score_reason": "; ".join(reasons),
    }


def combine_scores(ai_score: int | None, deterministic_score: int | None) -> int:
    ai_score = ai_score or 0
    deterministic_score = deterministic_score or 0
    return round((0.6 * ai_score) + (0.4 * deterministic_score))


def label_from_score(score: int) -> str:
    if score >= 75:
        return "strong_review"
    if score >= 60:
        return "watchlist"
    return "reject"
