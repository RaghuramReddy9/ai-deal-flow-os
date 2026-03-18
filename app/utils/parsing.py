import re


def parse_money_to_float(value: str | None) -> float | None:
    """
    Parse money-like strings into float values.

    Handles examples like:
    - $1.8m, 1.8 m, 1.8 million -> 1800000.0
    - $500k, 500K -> 500000.0
    - $3.4 b, 3.4 billion -> 3400000000.0
    - $100 -> 100.0

    Rejects:
    - percentages like 60%
    - placeholders like N/A, unknown, tbd
    - tiny ambiguous naked numbers like 1.4 or 6
    """

    if not value:
        return None

    text = value.strip().lower().replace(",", "").replace("$", "")
    if not text or text in {"n/a", "na", "unknown", "-", "tbd"}:
        return None

    # Reject percentages and non-money ratio-like values
    if "%" in text or "percent" in text:
        return None

    # Match formats like:
    # 1.8m / 1.8 m / 1.8 million / 500k / 400000
    match = re.search(
        r"(?P<number>\d+(?:\.\d+)?)\s*(?P<suffix>k|m|mm|mn|b|bn|million|billion)?\b",
        text
    )
    if not match:
        return None

    try:
        number = float(match.group("number"))
    except ValueError:
        return None

    suffix = match.group("suffix")

    # Reject tiny ambiguous naked numbers like "1.8" or "6"
    # unless they have an explicit suffix like m/k/b
    if suffix is None and number < 10:
        return None

    multiplier = 1.0
    if suffix == "k":
        multiplier = 1_000
    elif suffix in {"m", "mm", "mn", "million"}:
        multiplier = 1_000_000
    elif suffix in {"b", "bn", "billion"}:
        multiplier = 1_000_000_000

    result = number * multiplier

    # Optional sanity check
    if result > 1_000_000_000:
        return None

    return result