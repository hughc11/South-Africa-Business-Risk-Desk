from __future__ import annotations

import re
from difflib import SequenceMatcher


def _normalise_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s]", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def deduplicate_items(items: list[dict]) -> list[dict]:
    kept = []
    previous_titles = []
    priority = {"official": 3, "official traffic": 3, "news": 1}
    for item in sorted(items, key=lambda x: priority.get(x.get("source_type", "news"), 0), reverse=True):
        current = _normalise_title(item.get("title", ""))
        duplicate = any(current == previous or SequenceMatcher(None, current, previous).ratio() >= 0.88 for previous in previous_titles)
        if duplicate:
            continue
        kept.append(item)
        previous_titles.append(current)
    return kept
