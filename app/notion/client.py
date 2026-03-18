import os
import time

import requests


NOTION_VERSION = "2022-06-28"


def get_notion_headers():
    """Returns the headers required for Notion API requests, including authentication and versioning.
    """
    notion_api_key = os.getenv("NOTION_API_KEY")
    if not notion_api_key:
        raise ValueError("NOTION_API_KEY environment variable not set")

    return {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def notion_request(method: str, url: str, payload: dict) -> dict:
    """
    Send a Notion API request with a small retry loop for transient failures.
    """
    max_attempts = 3
    retry_delay_seconds = 2

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.request(
                method,
                url,
                headers=get_notion_headers(),
                json=payload,
                timeout=30,
            )
        except requests.RequestException as exc:
            if attempt == max_attempts:
                raise RuntimeError(f"Notion request failed after retries: {exc}") from exc

            time.sleep(retry_delay_seconds * attempt)
            continue

        if response.ok:
            return response.json()

        if response.status_code in {429, 500, 502, 503, 504} and attempt < max_attempts:
            time.sleep(retry_delay_seconds * attempt)
            continue

        raise RuntimeError(
            f"Notion request failed: {response.status_code} - {response.text}"
        )

    raise RuntimeError("Notion request failed after retries.")


def create_notion_page(properties: dict) -> dict:
    """Creates a new page in the Notion database with the given properties."""
    notion_database_id = os.getenv("NOTION_DATABASE_ID")
    if not notion_database_id:
        raise ValueError("NOTION_DATABASE_ID environment variable not set")

    url = "https://api.notion.com/v1/pages"

    payload = {
        "parent": {
            "database_id": notion_database_id
        },
        "properties": properties,
    }

    return notion_request("POST", url, payload)


def update_notion_page(page_id: str, properties: dict) -> dict:
    """Updates an existing Notion page with the given properties."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": properties,
    }
    return notion_request("PATCH", url, payload)
