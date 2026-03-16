import json
import re
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from app.scraper.broker_scraper import DealListing


FLIPPA_SEARCH_URL = "https://flippa.com/search"


def fetch_search_page() -> tuple[str, dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1440, "height": 900},
                locale="en-US",
            )

            page.goto(FLIPPA_SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(6000)

            html = page.content()
            meta = {
                "final_url": page.url,
                "title": page.title(),
            }

            return html, meta
        finally:
            browser.close()


def fetch_listing_page(url: str) -> tuple[str, dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1440, "height": 900},
                locale="en-US",
            )

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            html = page.content()
            meta = {
                "final_url": page.url,
                "title": page.title(),
            }

            return html, meta
        finally:
            browser.close()


def extract_listing_urls(html: str) -> List[str]:
    """
    Extract only real Flippa detail page URLs from the search page.
    """
    soup = BeautifulSoup(html, "html.parser")
    urls = set()

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue

        full_url = href if href.startswith("http") else urljoin("https://flippa.com", href)

        if _is_listing_url(full_url):
            urls.add(full_url)

    return sorted(urls)


def parse_listing_detail(html: str, url: str) -> DealListing:
    soup = BeautifulSoup(html, "html.parser")

    title = _extract_title(soup)
    asking_price = _extract_money_near_label(soup, ["asking price", "sale price", "price"])
    revenue = _extract_revenue(soup)
    profit = _extract_profit(soup)
    location = _extract_text_near_label(soup, ["location"])
    listing_type = _extract_listing_type_from_title(title) 
    description = _extract_description(soup)

    return DealListing(
        title=title or "Unknown Listing",
        location=location,
        asking_price=asking_price,
        revenue=revenue,
        profit=profit,
        listing_type=listing_type,
        description=description,
        source_url=url,
        source_name="flippa",
    )


def _is_listing_url(url: str) -> bool:
    """
    Flippa listing detail pages are usually numeric:
    https://flippa.com/12345678
    """
    if not url.startswith("https://flippa.com/"):
        return False

    path = url.replace("https://flippa.com/", "").strip("/")

    banned = {
        "",
        "search",
        "login",
        "signup",
        "exit-intent",
        "brokerage",
        "websites",
        "apps",
        "amazon-fba",
        "saas",
        "domains",
    }

    if path in banned:
        return False

    if re.fullmatch(r"\d{6,}", path):
        return True

    return False


def _extract_title(soup: BeautifulSoup) -> str | None:
    if soup.title and soup.title.string:
        raw = soup.title.string.strip()
        if raw:
            return raw

    h1 = soup.find("h1")
    if h1:
        txt = h1.get_text(" ", strip=True)
        if txt:
            return txt

    og = soup.find("meta", attrs={"property": "og:title"})
    if og and og.get("content"):
        return og["content"].strip()

    return None


def _extract_money_near_label(soup: BeautifulSoup, labels: list[str]) -> str | None:
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for i, line in enumerate(lines):
        low = line.lower()

        for label in labels:
            if re.search(r'\b' + re.escape(label) + r'\b', low):
                # check same line - improved regex for various money formats
                money = re.search(r'\$?\s*[\d,]+(?:\.\d+)?\s*[kKmMbBtT]?', line)
                if money:
                    return money.group(0).strip()

                # check next lines
                for j in range(i + 1, min(i + 3, len(lines))):
                    candidate = lines[j]
                    money = re.search(r'\$?\s*[\d,]+(?:\.\d+)?\s*[kKmMbBtT]?', candidate)
                    if money:
                        return money.group(0).strip()

    return None


def _extract_text_near_label(soup: BeautifulSoup, labels: list[str]) -> str | None:
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for i, line in enumerate(lines):
        low = line.lower()
        if any(label in low for label in labels):
            if i + 1 < len(lines):
                value = lines[i + 1].strip()
                if len(value) <= 120:
                    return value
    return None


def _extract_description(soup: BeautifulSoup) -> str | None:
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        return meta_desc["content"].strip()

    og_desc = soup.find("meta", attrs={"property": "og:description"})
    if og_desc and og_desc.get("content"):
        return og_desc["content"].strip()

    return None


def _extract_revenue(soup: BeautifulSoup) -> str | None:
    return _extract_money_near_label(
        soup,
        ["revenue", "annual revenue", "ttm revenue", "annualized revenue"]
    )


def _extract_profit(soup: BeautifulSoup) -> str | None:
    return _extract_money_near_label(
        soup,
        ["profit", "net profit", "ttm profit", "annual profit"]
    )


def _extract_listing_type_from_title(title: str | None) -> str | None:
    if not title:
        return None

    markers = [
        " For Sale on Flippa:",
        " for sale on flippa:",
    ]

    for marker in markers:
        if marker in title:
            return title.split(marker)[0].strip()

    return None