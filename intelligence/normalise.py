from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from settings import MAX_ITEM_AGE_DAYS


def clean_text(value: str) -> str:
    """
    Remove HTML and unnecessary spaces from text.
    """

    if not value:
        return ""

    text = " ".join(
        BeautifulSoup(value, "html.parser").stripped_strings
    )

    return re.sub(r"\s+", " ", text).strip()


def parse_timestamp(value: str) -> str:
    """
    Convert different publication-date formats into
    one consistent UTC timestamp.
    """

    if not value:
        return ""

    try:
        parsed = date_parser.parse(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        parsed = parsed.astimezone(timezone.utc)

        return parsed.isoformat()

    except (ValueError, TypeError, OverflowError):
        return ""


def is_too_old(
    timestamp: str,
    source_type: str,
) -> bool:
    """
    Remove ordinary news that is older than the allowed age.

    Official information is retained because official advice
    can remain important even when it was published earlier.
    """

    if not timestamp:
        return False

    if source_type in {
        "official",
        "official traffic",
    }:
        return False

    try:
        published = datetime.fromisoformat(timestamp)
    except ValueError:
        return False

    oldest_allowed = (
        datetime.now(timezone.utc)
        - timedelta(days=MAX_ITEM_AGE_DAYS)
    )

    return published < oldest_allowed


def normalise_item(
    item: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Clean and standardise one intelligence item.
    """

    title = clean_text(
        str(item.get("title") or "")
    )

    summary = clean_text(
        str(item.get("summary") or "")
    )

    if not title:
        return None

    published_timestamp = parse_timestamp(
        str(item.get("published") or "")
    )

    source_type = str(
        item.get("source_type")
        or "news"
    )

    if is_too_old(
        published_timestamp,
        source_type,
    ):
        return None

    if published_timestamp:
        try:
            published_display = datetime.fromisoformat(
                published_timestamp
            ).strftime("%d %b %Y, %H:%M UTC")
        except ValueError:
            published_display = (
                "Publication time unavailable"
            )
    else:
        published_display = (
            "Publication time unavailable"
        )

    normalised = dict(item)

    normalised["title"] = title
    normalised["summary"] = summary[:1500]
    normalised["published_timestamp"] = (
        published_timestamp
    )
    normalised["published_display"] = (
        published_display
    )

    normalised["source"] = clean_text(
        str(item.get("source") or "Unknown source")
    )

    normalised["location"] = clean_text(
        str(item.get("location") or "National")
    )

    normalised["confidence"] = clean_text(
        str(item.get("confidence") or "Reported")
    )

    return normalised


def normalise_items(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Clean and standardise all collected items.
    """

    output: list[dict[str, Any]] = []

    for item in items:

        normalised = normalise_item(item)

        if normalised is not None:
            output.append(normalised)

    return output