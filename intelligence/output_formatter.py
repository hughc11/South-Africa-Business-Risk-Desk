"""
Format backend intelligence for the South Africa Business Risk Desk website.

The collection engine produces:

- metadata
- national_risk
- items

The website expects:

- metadata
- national
- timeline
- cities
- incidents
- news
- conversation_brief
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


CITY_DEFINITIONS = [
    {
        "id": "johannesburg",
        "name": "Johannesburg",
        "latitude": -26.2041,
        "longitude": 28.0473,
        "default_zoom": 11,
        "location_names": [
            "Johannesburg",
        ],
    },
    {
        "id": "cape-town",
        "name": "Cape Town",
        "latitude": -33.9249,
        "longitude": 18.4241,
        "default_zoom": 11,
        "location_names": [
            "Cape Town",
        ],
    },
    {
        "id": "pretoria-tshwane",
        "name": "Pretoria / Tshwane",
        "latitude": -25.7479,
        "longitude": 28.2293,
        "default_zoom": 11,
        "location_names": [
            "Pretoria",
            "Pretoria / Tshwane",
            "Tshwane",
        ],
    },
    {
        "id": "durban-ethekwini",
        "name": "Durban / eThekwini",
        "latitude": -29.8587,
        "longitude": 31.0218,
        "default_zoom": 11,
        "location_names": [
            "Durban",
            "Durban / eThekwini",
            "eThekwini",
        ],
    },
    {
        "id": "gqeberha",
        "name": "Gqeberha",
        "latitude": -33.9608,
        "longitude": 25.6022,
        "default_zoom": 11,
        "location_names": [
            "Gqeberha",
            "Port Elizabeth",
        ],
    },
    {
        "id": "bloemfontein",
        "name": "Bloemfontein",
        "latitude": -29.0852,
        "longitude": 26.1596,
        "default_zoom": 11,
        "location_names": [
            "Bloemfontein",
        ],
    },
    {
        "id": "east-london",
        "name": "East London",
        "latitude": -33.0153,
        "longitude": 27.9116,
        "default_zoom": 11,
        "location_names": [
            "East London",
        ],
    },
]


COMPONENT_DEFINITIONS = [
    {
        "name": "Security",
        "categories": [
            "security and crime",
            "crime and security",
        ],
    },
    {
        "name": "Civil unrest",
        "categories": [
            "protests and civil unrest",
        ],
    },
    {
        "name": "Infrastructure",
        "categories": [
            "infrastructure",
            "energy",
        ],
    },
    {
        "name": "Transport",
        "categories": [
            "road and transport disruption",
            "transport",
        ],
    },
    {
        "name": "Business environment",
        "categories": [
            "economy and business",
            "government",
            "politics and government",
        ],
    },
]


INCIDENT_CATEGORIES = {
    "protests and civil unrest",
    "security and crime",
    "crime and security",
    "road and transport disruption",
    "transport",
    "infrastructure",
    "energy",
    "health",
    "weather",
    "travel advice",
}


def _safe_int(value: Any) -> int:
    """
    Convert a value to an integer safely.
    """

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _risk_level(score: int) -> str:
    """
    Convert a score into a website risk label.
    """

    if score >= 85:
        return "Severe"

    if score >= 70:
        return "High"

    if score >= 50:
        return "Elevated"

    if score >= 30:
        return "Guarded"

    return "Low"


def _severity_level(score: int) -> str:
    """
    Convert a business impact score into an incident severity.
    """

    if score >= 70:
        return "High"

    if score >= 35:
        return "Medium"

    return "Low"


def _normalise_category(value: Any) -> str:
    """
    Return a lowercase category for comparisons.
    """

    return str(value or "").strip().lower()


def _average_top_scores(
    items: list[dict[str, Any]],
    maximum_items: int = 5,
) -> int:
    """
    Calculate the average of the strongest business-impact scores.
    """

    scores = sorted(
        (
            _safe_int(
                item.get("business_impact_score")
            )
            for item in items
        ),
        reverse=True,
    )

    selected_scores = scores[:maximum_items]

    if not selected_scores:
        return 0

    return round(
        sum(selected_scores)
        / len(selected_scores)
    )


def _build_components(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build the national risk breakdown bars.
    """

    components: list[dict[str, Any]] = []

    for definition in COMPONENT_DEFINITIONS:
        matching_items = [
            item
            for item in items
            if _normalise_category(
                item.get("category")
            )
            in definition["categories"]
        ]

        score = _average_top_scores(
            matching_items
        )

        components.append(
            {
                "name": definition["name"],
                "score": score,
            }
        )

    return components


def _item_matches_city(
    item: dict[str, Any],
    city: dict[str, Any],
) -> bool:
    """
    Check whether a story belongs to a configured city.
    """

    item_city_id = str(
        item.get("city_id") or ""
    ).strip().lower()

    if item_city_id == city["id"]:
        return True

    location = str(
        item.get("location") or ""
    ).strip().lower()

    return any(
        city_name.lower() in location
        for city_name in city["location_names"]
    )


def _build_cities(
    items: list[dict[str, Any]],
    national_score: int,
) -> list[dict[str, Any]]:
    """
    Build city risk cards and map markers.
    """

    cities: list[dict[str, Any]] = []

    for city in CITY_DEFINITIONS:
        city_items = [
            item
            for item in items
            if _item_matches_city(
                item,
                city,
            )
        ]

        if city_items:
            city_score = _average_top_scores(
                city_items,
                maximum_items=5,
            )

            strongest_categories: list[str] = []

            for item in sorted(
                city_items,
                key=lambda story: _safe_int(
                    story.get(
                        "business_impact_score"
                    )
                ),
                reverse=True,
            ):
                category = str(
                    item.get(
                        "category",
                        "Current incidents",
                    )
                )

                if category not in strongest_categories:
                    strongest_categories.append(
                        category
                    )

            category_text = ", ".join(
                strongest_categories[:2]
            )

            summary = (
                f"Current city risk is being driven by "
                f"{category_text.lower()}."
            )
        else:
            city_score = max(
                10,
                round(national_score * 0.55),
            )

            summary = (
                "No strong city-specific incidents were identified "
                "in the current collection period."
            )

        cities.append(
            {
                "id": city["id"],
                "name": city["name"],
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "default_zoom": city["default_zoom"],
                "score": city_score,
                "level": _risk_level(
                    city_score
                ),
                "summary": summary,
            }
        )

    return cities


def _incident_type(category: str) -> str:
    """
    Convert a category into a concise incident type.
    """

    category_lower = category.lower()

    if "protest" in category_lower:
        return "Protest"

    if "security" in category_lower or "crime" in category_lower:
        return "Security"

    if "transport" in category_lower or "road" in category_lower:
        return "Transport"

    if "infrastructure" in category_lower or "energy" in category_lower:
        return "Infrastructure"

    if "weather" in category_lower:
        return "Weather"

    if "health" in category_lower:
        return "Health"

    if "travel advice" in category_lower:
        return "Travel advice"

    return category


def _suggested_action(category: str) -> str:
    """
    Produce a simple business-travel action.
    """

    category_lower = category.lower()

    if "protest" in category_lower:
        return (
            "Avoid affected areas, confirm meeting access "
            "and allow additional travel time."
        )

    if "security" in category_lower or "crime" in category_lower:
        return (
            "Review local security arrangements and avoid "
            "unnecessary travel near the reported area."
        )

    if "transport" in category_lower or "road" in category_lower:
        return (
            "Check the route before departure and allow "
            "additional journey time."
        )

    if "infrastructure" in category_lower or "energy" in category_lower:
        return (
            "Confirm backup arrangements and check whether "
            "the disruption affects the destination."
        )

    if "weather" in category_lower:
        return (
            "Check local conditions and confirm that planned "
            "transport remains operational."
        )

    if "health" in category_lower:
        return (
            "Review official health guidance before travel "
            "or attending affected locations."
        )

    if "travel advice" in category_lower:
        return (
            "Review the latest official travel advice before "
            "making or changing travel plans."
        )

    return (
        "Review the report and confirm whether it affects "
        "planned business activity."
    )


def _build_incidents(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert the strongest operational stories into incident cards.
    """

    relevant_items = [
        item
        for item in items
        if (
            _normalise_category(
                item.get("category")
            )
            in INCIDENT_CATEGORIES
            and _safe_int(
                item.get("business_impact_score")
            ) >= 25
        )
    ]

    ranked_items = sorted(
        relevant_items,
        key=lambda item: _safe_int(
            item.get("business_impact_score")
        ),
        reverse=True,
    )

    incidents: list[dict[str, Any]] = []

    for item in ranked_items[:10]:
        score = _safe_int(
            item.get("business_impact_score")
        )

        category = str(
            item.get(
                "category",
                "Current incident",
            )
        )

        incidents.append(
            {
                "title": item.get(
                    "title",
                    "Untitled incident",
                ),
                "location": item.get(
                    "location",
                    "National",
                ),
                "type": _incident_type(
                    category
                ),
                "severity": _severity_level(
                    score
                ),
                "status": "Active",
                "time_window": item.get(
                    "published_display",
                    "Current reporting period",
                ),
                "summary": item.get(
                    "summary",
                    "No summary available.",
                ),
                "action": _suggested_action(
                    category
                ),
                "confidence": item.get(
                    "confidence",
                    "Reported",
                ),
                "source": item.get(
                    "source",
                    "Unknown source",
                ),
            }
        )

    return incidents


def _build_news(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert collected stories into the website news format.
    """

    news: list[dict[str, Any]] = []

    for item in items:
        news.append(
            {
                "title": item.get(
                    "title",
                    "Untitled story",
                ),
                "location": item.get(
                    "location",
                    "National",
                ),
                "city_id": item.get(
                    "city_id"
                ),
                "category": item.get(
                    "category",
                    "Unclassified news",
                ),
                "relevance": item.get(
                    "business_impact_level",
                    item.get(
                        "relevance",
                        "Low",
                    ),
                ),
                "published": item.get(
                    "published_display",
                    item.get(
                        "published",
                        "",
                    ),
                ),
                "event_date": item.get(
                    "event_date",
                    "",
                ),
                "summary": item.get(
                    "business_impact_explanation",
                    item.get(
                        "summary",
                        "",
                    ),
                ),
                "source": item.get(
                    "source",
                    "Unknown source",
                ),
                "confidence": item.get(
                    "confidence",
                    "Reported",
                ),
                "url": item.get(
                    "url",
                    "",
                ),
                "business_impact_score": (
                    _safe_int(
                        item.get(
                            "business_impact_score"
                        )
                    )
                ),
            }
        )

    return news


def _build_timeline(
    national_score: int,
    national_summary: str,
    generated_at: str,
) -> list[dict[str, Any]]:
    """
    Create the first timeline point.

    A full historical timeline will be created after the historical
    database is added.
    """

    try:
        parsed_date = datetime.fromisoformat(
            generated_at
        )

        display_date = parsed_date.strftime(
            "%d %b"
        )
    except (TypeError, ValueError):
        display_date = datetime.now().strftime(
            "%d %b"
        )

    return [
        {
            "date": display_date,
            "score": national_score,
            "explanation": national_summary,
        }
    ]


def _build_conversation_brief() -> list[dict[str, str]]:
    """
    Provide safe Version 1 business conversation guidance.
    """

    return [
        {
            "topic": "Business climate",
            "heading": "Discussing current operating conditions",
            "context": (
                "Economic and infrastructure conditions can affect "
                "industries and locations differently."
            ),
            "starter": (
                "How are current operating conditions affecting "
                "businesses in your sector?"
            ),
            "avoid": (
                "Assuming every company or region is experiencing "
                "the same conditions."
            ),
        },
        {
            "topic": "Infrastructure",
            "heading": "Discussing practical disruption",
            "context": (
                "Service disruption can be discussed through its "
                "business effects rather than political blame."
            ),
            "starter": (
                "Have recent infrastructure conditions changed how "
                "your organisation plans day-to-day operations?"
            ),
            "avoid": (
                "Assuming who the other person blames for a local "
                "service problem."
            ),
        },
        {
            "topic": "Current affairs",
            "heading": "Approaching sensitive developments",
            "context": (
                "Political and social issues may be strongly felt, "
                "so neutral and open questions are safer."
            ),
            "starter": (
                "Which recent developments are having the greatest "
                "effect on your industry?"
            ),
            "avoid": (
                "Assuming a person's political affiliation or view "
                "on a controversial issue."
            ),
        },
    ]


def format_dashboard_output(
    backend_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert backend intelligence into the website JSON structure.
    """

    metadata = dict(
        backend_output.get(
            "metadata",
            {},
        )
    )

    metadata["data_status"] = (
        "live intelligence test"
    )

    items = backend_output.get(
        "items",
        [],
    )

    if not isinstance(items, list):
        items = []

    national_risk = backend_output.get(
        "national_risk",
        {},
    )

    national_score = _safe_int(
        national_risk.get("score")
    )

    national_level = str(
        national_risk.get(
            "level",
            _risk_level(national_score),
        )
    )

    national_summary = str(
        national_risk.get(
            "summary",
            (
                f"{national_level} national business risk "
                f"({national_score}/100)."
            ),
        )
    )

    generated_at = str(
        metadata.get(
            "generated_at",
            "",
        )
    )

    return {
        "metadata": metadata,
        "national": {
            "score": national_score,
            "level": national_level,
            "seven_day_change": 0,
            "summary": national_summary,
            "components": _build_components(
                items
            ),
        },
        "timeline": _build_timeline(
            national_score=national_score,
            national_summary=national_summary,
            generated_at=generated_at,
        ),
        "cities": _build_cities(
            items=items,
            national_score=national_score,
        ),
        "incidents": _build_incidents(
            items
        ),
        "news": _build_news(
            items
        ),
        "conversation_brief": (
            _build_conversation_brief()
        ),
    }