from __future__ import annotations

from bs4 import BeautifulSoup
from collectors.common import get_json

FCDO_API_URL = "https://www.gov.uk/api/content/foreign-travel-advice/south-africa"


def _plain_text(value: str) -> str:
    return " ".join(BeautifulSoup(value or "", "html.parser").stripped_strings)


def collect_fcdo_advice() -> list[dict]:
    data = get_json(FCDO_API_URL)
    details = data.get("details", {})
    change_note = _plain_text(details.get("change_note", ""))
    summary = data.get("description", "")
    updated_at = data.get("public_updated_at", "")

    items = [{
        "title": data.get("title", "South Africa travel advice"),
        "summary": change_note or summary,
        "url": "https://www.gov.uk/foreign-travel-advice/south-africa",
        "source": "UK Foreign, Commonwealth & Development Office",
        "source_type": "official",
        "location": "National",
        "city_id": None,
        "published": updated_at,
        "event_date": updated_at,
        "collector": "gov_uk",
        "raw_category": "Official travel advice",
        "confidence": "Confirmed",
    }]

    for part in details.get("parts", []):
        title = part.get("title", "")
        body = _plain_text(part.get("body", ""))
        if not title or not body:
            continue
        items.append({
            "title": f"FCDO advice: {title}",
            "summary": body[:1000],
            "url": "https://www.gov.uk/foreign-travel-advice/south-africa/" + part.get("slug", ""),
            "source": "UK Foreign, Commonwealth & Development Office",
            "source_type": "official",
            "location": "National",
            "city_id": None,
            "published": updated_at,
            "event_date": updated_at,
            "collector": "gov_uk",
            "raw_category": "Official travel advice",
            "confidence": "Confirmed",
        })
    return items
