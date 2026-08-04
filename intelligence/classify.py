from __future__ import annotations

from typing import Any


CATEGORY_KEYWORDS = {
    "Protests and civil unrest": [
        "protest",
        "demonstration",
        "march",
        "riot",
        "unrest",
        "shutdown",
        "picket",
        "strike",
    ],

    "Road and transport disruption": [
        "road closure",
        "closed road",
        "traffic",
        "rail",
        "train",
        "airport",
        "flight",
        "port",
        "freight",
        "transport",
        "delay",
    ],

    "Infrastructure": [
        "electricity",
        "power",
        "outage",
        "water",
        "infrastructure",
        "load shedding",
        "substation",
        "service interruption",
    ],

    "Security and crime": [
        "crime",
        "robbery",
        "kidnap",
        "shooting",
        "security",
        "violence",
        "attack",
        "theft",
        "hijacking",
    ],

    "Economy and business": [
        "business",
        "economy",
        "economic",
        "investment",
        "company",
        "market",
        "inflation",
        "trade",
        "currency",
        "growth",
    ],

    "Politics and government": [
        "government",
        "minister",
        "president",
        "parliament",
        "election",
        "coalition",
        "policy",
        "regulation",
        "municipality",
    ],
}


DISRUPTION_KEYWORDS = {
    "protest",
    "demonstration",
    "closure",
    "closed",
    "strike",
    "shutdown",
    "outage",
    "disruption",
    "delay",
    "violence",
    "robbery",
    "attack",
    "flood",
    "fire",
    "hijacking",
}


def determine_category(
    text: str,
    fallback: str,
) -> str:
    """
    Choose the most suitable category for an item.
    """

    lowered_text = text.lower()

    category_scores = {
        category: sum(
            keyword in lowered_text
            for keyword in keywords
        )
        for category, keywords in CATEGORY_KEYWORDS.items()
    }

    best_category, best_score = max(
        category_scores.items(),
        key=lambda item: item[1],
    )

    if best_score == 0:
        return fallback or "General intelligence"

    return best_category


def calculate_relevance_score(
    item: dict[str, Any],
    text: str,
) -> int:
    """
    Calculate a simple first-stage business-risk relevance score.
    """

    score = 25

    source_type = str(
        item.get("source_type")
        or "news"
    )

    if source_type in {
        "official",
        "official traffic",
    }:
        score += 25

    if item.get("location") != "National":
        score += 10

    disruption_matches = sum(
        keyword in text
        for keyword in DISRUPTION_KEYWORDS
    )

    score += min(
        30,
        disruption_matches * 6,
    )

    if item.get("published_timestamp"):
        score += 10

    return max(
        0,
        min(100, score),
    )


def relevance_label(score: int) -> str:
    """
    Convert the numerical score into a readable label.
    """

    if score >= 70:
        return "High"

    if score >= 45:
        return "Medium"

    return "Low"


def classify_items(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Add category and relevance information to all items.
    """

    output: list[dict[str, Any]] = []

    for item in items:

        text = (
            f"{item.get('title', '')} "
            f"{item.get('summary', '')}"
        ).lower()

        category = determine_category(
            text,
            str(
                item.get("raw_category")
                or ""
            ),
        )

        relevance_score = calculate_relevance_score(
            item,
            text,
        )

        classified = dict(item)

        classified["category"] = category
        classified["relevance_score"] = relevance_score
        classified["relevance"] = relevance_label(
            relevance_score
        )

        output.append(classified)

    return output