from __future__ import annotations

import feedparser
from collectors.common import get_text
from settings import MAX_ITEMS_PER_FEED

GOVERNMENT_FEEDS = [
    {"name": "South African Government news", "url": "https://www.gov.za/rss.xml"},
    {"name": "Statistics South Africa", "url": "https://www.statssa.gov.za/?feed=rss2"},
]


def collect_sa_government_news() -> list[dict]:
    items = []
    for feed_config in GOVERNMENT_FEEDS:
        try:
            content = get_text(feed_config["url"])
            feed = feedparser.parse(content)
        except Exception as exc:
            print(f"  Skipped {feed_config['name']}: {exc}")
            continue
        for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
            published = entry.get("published") or entry.get("updated") or ""
            items.append({
                "title": entry.get("title", "Untitled government update"),
                "summary": entry.get("summary", ""),
                "url": entry.get("link", ""),
                "source": feed_config["name"],
                "source_type": "official",
                "location": "National",
                "city_id": None,
                "published": published,
                "event_date": published,
                "collector": "sa_government",
                "raw_category": "Government and regulation",
                "confidence": "Confirmed",
            })
    return items
