from __future__ import annotations

from collectors.common import get_json
from settings import ITRAFFIC_API_KEY


def collect_i_traffic() -> list[dict]:
    if not ITRAFFIC_API_KEY:
        print("  No ITRAFFIC_API_KEY found. Traffic collection was skipped without failing the run.")
        return []

    data = get_json("https://www.i-traffic.co.za/api/getevents", params={"key": ITRAFFIC_API_KEY, "format": "json"})
    if isinstance(data, dict):
        events = data.get("Events") or data.get("events") or data.get("Items") or data.get("items") or []
    elif isinstance(data, list):
        events = data
    else:
        events = []

    items = []
    for event in events:
        title = event.get("EventDescription") or event.get("Description") or event.get("description") or "Traffic event"
        latitude = event.get("Latitude") or event.get("latitude")
        longitude = event.get("Longitude") or event.get("longitude")
        published = event.get("LastUpdated") or event.get("StartDate") or event.get("startDate") or ""
        items.append({
            "title": title,
            "summary": title,
            "url": "https://www.i-traffic.co.za/",
            "source": "i-TRAFFIC South Africa",
            "source_type": "official traffic",
            "location": "South Africa road network",
            "city_id": None,
            "published": published,
            "event_date": published,
            "collector": "traffic",
            "raw_category": "Road and transport disruption",
            "confidence": "Confirmed",
            "latitude": latitude,
            "longitude": longitude,
        })
    return items
