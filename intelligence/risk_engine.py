"""
National risk scoring for the South Africa Business Risk Desk.

This module uses the business-impact scores already attached to stories
to calculate one national business-risk score.

It returns:

- score
- level
- summary
- primary_drivers
- story_count
"""

from typing import Any


RISK_LEVELS = (
    (80, "Severe"),
    (60, "High"),
    (35, "Moderate"),
    (0, "Low"),
)


CATEGORY_WEIGHTS = {
    "protests and civil unrest": 1.30,
    "security and crime": 1.25,
    "crime and security": 1.25,
    "road and transport disruption": 1.20,
    "transport": 1.20,
    "infrastructure": 1.15,
    "travel advice": 1.25,
    "health": 1.10,
    "weather": 1.10,
    "economy and business": 0.85,
    "politics and government": 0.80,
    "government": 0.70,
}


def _safe_int(value: Any) -> int:
    """
    Convert a value to an integer safely.
    """

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _get_category_weight(item: dict[str, Any]) -> float:
    """
    Return the risk multiplier for the story category.
    """

    category = str(
        item.get("category", "")
    ).strip().lower()

    if not category:
        return 1.0

    for category_name, weight in CATEGORY_WEIGHTS.items():
        if category_name in category:
            return weight

    return 1.0


def _calculate_weighted_story_score(
    item: dict[str, Any],
) -> float:
    """
    Calculate the national-risk contribution of one story.
    """

    impact_score = _safe_int(
        item.get("business_impact_score")
    )

    category_weight = _get_category_weight(item)

    confidence = str(
        item.get("confidence", "")
    ).strip().lower()

    confidence_weight = 1.05 if confidence == "confirmed" else 1.0

    return (
        impact_score
        * category_weight
        * confidence_weight
    )


def _determine_risk_level(score: int) -> str:
    """
    Convert a score from 0 to 100 into a risk level.
    """

    for minimum_score, level in RISK_LEVELS:
        if score >= minimum_score:
            return level

    return "Low"


def _build_primary_drivers(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Return the strongest current risk drivers.
    """

    ranked_items = sorted(
        items,
        key=_calculate_weighted_story_score,
        reverse=True,
    )

    drivers: list[dict[str, Any]] = []

    for item in ranked_items[:5]:
        drivers.append(
            {
                "title": item.get(
                    "title",
                    "Untitled story",
                ),
                "category": item.get(
                    "category",
                    "Unclassified",
                ),
                "location": item.get(
                    "location",
                    "National",
                ),
                "business_impact_score": _safe_int(
                    item.get(
                        "business_impact_score"
                    )
                ),
            }
        )

    return drivers


def _build_summary(
    score: int,
    level: str,
    drivers: list[dict[str, Any]],
) -> str:
    """
    Create a plain-English explanation of the national score.
    """

    if not drivers:
        return (
            f"{level} national business risk ({score}/100). "
            "No strong current risk drivers were identified."
        )

    categories: list[str] = []

    for driver in drivers:
        category = str(
            driver.get("category", "")
        ).strip()

        if category and category not in categories:
            categories.append(category)

    category_text = ", ".join(
        categories[:3]
    )

    if not category_text:
        category_text = "current reported incidents"

    return (
        f"{level} national business risk ({score}/100). "
        f"The main current drivers are {category_text}."
    )


def calculate_national_risk(
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate the national business-risk result.

    The method gives greatest weight to the strongest current stories,
    while preventing a large number of routine low-value stories from
    artificially inflating the score.
    """

    if not items:
        return {
            "score": 0,
            "level": "Low",
            "summary": (
                "Low national business risk (0/100). "
                "No stories were available for assessment."
            ),
            "primary_drivers": [],
            "story_count": 0,
        }

    weighted_scores = sorted(
        (
            _calculate_weighted_story_score(item)
            for item in items
        ),
        reverse=True,
    )

    strongest_scores = weighted_scores[:10]

    average_score = sum(
        strongest_scores
    ) / len(strongest_scores)

    critical_count = sum(
        1
        for item in items
        if str(
            item.get(
                "business_impact_level",
                ""
            )
        ).lower() == "critical"
    )

    high_count = sum(
        1
        for item in items
        if str(
            item.get(
                "business_impact_level",
                ""
            )
        ).lower() == "high"
    )

    concentration_bonus = min(
        15,
        (critical_count * 3)
        + high_count,
    )

    final_score = round(
        average_score
        + concentration_bonus
    )

    final_score = max(
        0,
        min(100, final_score),
    )

    level = _determine_risk_level(
        final_score
    )

    primary_drivers = _build_primary_drivers(
        items
    )

    summary = _build_summary(
        score=final_score,
        level=level,
        drivers=primary_drivers,
    )

    return {
        "score": final_score,
        "level": level,
        "summary": summary,
        "primary_drivers": primary_drivers,
        "story_count": len(items),
    }