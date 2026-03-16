import re


def parse_money_to_float(value: str | None) -> float | None:
    if not value:
        return None

    text = value.strip().lower().replace(",", "")
    if not text or text in {"n/a", "na", "unknown", "-"}:
        return None

    multiplier = 1.0

    if "million" in text or re.search(r"\bmm\b", text):
        multiplier = 1_000_000
    elif "billion" in text or re.search(r"\bbb\b", text):
        multiplier = 1_000_000_000
    elif "k" in text:
        multiplier = 1_000

    match = re.search(r"(\d+(\.\d+)?)", text)
    if not match:
        return None

    number = float(match.group(1))
    return number * multiplier