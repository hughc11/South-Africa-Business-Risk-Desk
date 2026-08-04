from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from settings import MAX_ITEM_AGE_DAYS


def _clean_text(value: str) -> str:
    text = " ".join(BeautifulSoup(value or "", "html.parser").stripped_strings)
    return re.sub(r"\s+", " ", text).strip()


def _parse_timestamp(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = date_parser.parse(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError, OverflowError):
        return ""


def normalise_items(items: list[dict]) -> list[dict]:
    now = datetime.now(timezone.utc)
    oldest_allowed = now - timedelta(days=MAX_ITEM_AGE_DAYS)
    output = []
    for item in items:
        title = _clean_text(item.get("title", ""))
        summary = _clean_text(item.get("summary", ""))
        timestamp = _parse_timestamp(item.get("published", ""))
        if not title:
            continue
        source_type = item.get("source_type", "news")
        if timestamp and source_type not in {"official"}:
            try:
                if datetime.fromisoformat(timestamp) < oldest_allowed:
                    continue
            except ValueError:
                pass
        normalised = dict(item)
        normalised["title"] = title
        normalised["summary"] = summary[:1200]
        normalised["published_timestamp"] = timestamp
        normalised["published_display"] = datetime.fromisoformat(timestamp).strftime("%d %b %Y, %H:%M UTC") if timestamp else "Publication time unavailable"
        output.append(normalised)
    return output
