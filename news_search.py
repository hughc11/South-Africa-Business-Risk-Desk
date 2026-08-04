from __future__ import annotations

from urllib.parse import quote_plus
import feedparser
from collectors.common import get_text
from settings import CITY_QUERIES, MAX_ITEMS_PER_FEED, NATIONAL_QUERIES

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-ZA&gl=ZA&ceid=ZA:en"


def _collect_query(query: str, location: str, city_id: str | None) -> list[dict]:
    url = GOOGLE_NEWS_RSS.format(query=quote_plus(query))
    feed = feedparser.parse(get_text(url))
    items = []
    for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
        source_name = "Google News result"
        source = entry.get("source")
        if isinstance(source, dict):
            source_name = source.get("title", source_name)
        published = entry.get("published") or entry.get("updated") or ""
        items.append({
            "title": entry.get("title", "Untitled news result"),
            "summary": entry.get("summary", ""),
            "url": entry.get("link", ""),
            "source": source_name,
            "source_type": "news",
            "location": location,
            "city_id": city_id,
            "published": published,
            "event_date": "",
            "collector": "news_search",
            "raw_category": "Unclassified news",
            "confidence": "Reported",
        })
    return items


def collect_news_searches() -> list[dict]:
    items = []
    for query in NATIONAL_QUERIES:
        try:
            items.extend(_collect_query(query, "National", None))
        except Exception as exc:
            print(f"  National query skipped: {query} — {exc}")
    for city_name, queries in CITY_QUERIES.items():
        city_id = city_name.lower().replace(" / ", "-").replace(" ", "-")
        for query in queries:
            try:
                items.extend(_collect_query(query, city_name, city_id))
            except Exception as exc:
                print(f"  City query skipped: {query} — {exc}")
    return items
