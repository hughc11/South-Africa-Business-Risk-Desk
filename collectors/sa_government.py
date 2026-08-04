from __future__ import annotations

from typing import Any

import feedparser

from collectors.common import get_text
from settings import MAX_ITEMS_PER_FEED


GOVERNMENT_FEEDS = [
    {
        "name": "South African Government",
        "url": "https://www.gov.za/rss.xml",
    },
    {
        "name": "Statistics South Africa",
        "url": "https://www.statssa.gov.za/?feed=rss2",
    },
]


def collect_sa_government_news() -> list[dict[str, Any]]:
    """
    Collect official South African government updates.
    """

    items: list[dict[str, Any]] = []

    for feed in GOVERNMENT_FEEDS:

        try:
            xml = get_text(feed["url"])

        except Exception as exc:
            print(f"Government feed unavailable: {exc}")
            continue

        parsed = feedparser.parse(xml)

        for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:

            published = (
                entry.get("published")
                or entry.get("updated")
                or ""
            )

            items.append(
                {
                    "title": entry.get(
                        "title",
                        "Government Update",
                    ),
                    "summary": entry.get(
                        "summary",
                        "",
                    ),
                    "url": entry.get(
                        "link",
                        "",
                    ),
                    "source": feed["name"],
                    "source_type": "official",
                    "location": "National",
                    "city_id": None,
                    "published": published,
                    "event_date": published,
                    "collector": "sa_government",
                    "raw_category": "Government",
                    "confidence": "Confirmed",
                }
            )

    return items