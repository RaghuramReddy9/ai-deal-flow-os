from dataclasses import dataclass
from typing import Optional


@dataclass
class DealListing:
    title: str
    location: Optional[str]
    asking_price: Optional[str]
    revenue: Optional[str]
    profit: Optional[str]
    listing_type: Optional[str]
    description: Optional[str]
    source_url: str
    source_name: str


def looks_blocked(html: str, final_url: str = "", title: str = "") -> bool:
    text = f"{title}\n{final_url}\n{html[:5000]}".lower()

    strong_signals = [
        "access denied",
        "forbidden",
        "captcha",
        "verify you are human",
        "attention required",
        "cf-challenge",
        "please enable javascript",
        "request unsuccessful",
    ]

    return any(signal in text for signal in strong_signals)