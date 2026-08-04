from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any


SOURCE_PRIORITY = {
    "official": 3,
    "official traffic": 3,
    "news": 1,
}


def normalise_title(title: str) -> str:
    """
    Convert a headline into a simpler format
    so similar stories can be compared.
    """

    title = title.lower()

    title = re.sub(
        r"[^a-z0-9\s]",
        " ",
        title,
    )

    title = re.sub(
        r"\s+",
        " ",
        title,
    )

    return title.strip()


def title_similarity(
    first: str,
    second: str,
) -> float:
    """
    Return a similarity score between 0 and 1.
    """

    return SequenceMatcher(
        None,
        first,
        second,
    ).ratio()


def is_duplicate(
    current_title: str,
    previous_titles: list[str],
) -> bool:
    """
    Decide whether a story is the same as
    one already kept.
    """

    for previous_title in previous_titles:

        if current_title == previous_title:
            return True

        if title_similarity(
            current_title,
            previous_title,
        ) >= 0.88:
            return True

    return False


def deduplicate_items(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Remove duplicate or near-duplicate stories.

    Official sources are considered first so they
    are preferred over ordinary news reports.
    """

    sorted_items = sorted(
        items,
        key=lambda item: SOURCE_PRIORITY.get(
            str(
                item.get("source_type")
                or "news"
            ),
            0,
        ),
        reverse=True,
    )

    kept_items: list[dict[str, Any]] = []
    kept_titles: list[str] = []

    for item in sorted_items:

        title = normalise_title(
            str(
                item.get("title")
                or ""
            )
        )

        if not title:
            continue

        if is_duplicate(
            title,
            kept_titles,
        ):
            continue

        kept_items.append(item)
        kept_titles.append(title)

    return kept_items