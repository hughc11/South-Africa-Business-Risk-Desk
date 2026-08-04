from __future__ import annotations

from typing import Any

from collectors.common import get_json
from settings import ITRAFFIC_API_KEY


ITRAFFIC_API_URL = "https://www.i-traffic.co.za/api/getevents"


def collect_i_traffic() -> list[dict[str, Any]]:
    """
    Collect road traffic incidents.

    If no API key has been configured, the collector
    quietly skips itself without causing the collection
    engine to fail.
    """

    if not ITRAFFIC_API_KEY:
        print(
            "No ITRAFFIC_API_KEY configured. "
            "Traffic collector skipped."
        )
        return []

    data = get_json(
        ITRAFFIC_API_URL,
        params={
            "key": ITRAFFIC_API_KEY,
            "format": "json",
        },
    )

    if isinstance(data, dict):
        events = (
            data.get("Events")
            or data.get("events")
            or data.get("Items")
            or data.get("items")
            or []
        )
    elif isinstance(data, list):
        events = data
    else:
        events = []

    items: list[dict[str, Any]] = []

    for event in events:

        title = (
            event.get("EventDescription")
            or event.get("Description")
            or "Traffic Event"
        )

        published = (
            event.get("LastUpdated")
            or event.get("StartDate")
            or ""
        )

        items.append(
            {
                "title": title,
                "summary": title,
                "url": "https://www.i-traffic.co.za/",
                "source": "i-TRAFFIC South Africa",
                "source_type": "official traffic",
                "location": "South Africa",
                "city_id": None,
                "published": published,
                "event_date": published,
                "collector": "traffic",
                "raw_category": "Road and transport disruption",
                "confidence": "Confirmed",
                "latitude": event.get("Latitude"),
                "longitude": event.get("Longitude"),
            }
        )

    return items