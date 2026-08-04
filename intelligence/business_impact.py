"""
Business impact scoring for the South Africa Business Risk Desk.

This module estimates how important each collected story may be for a British
business traveller or company operating in South Africa.

The scoring model uses weighted assessment dimensions rather than adding every
matching keyword together. This prevents several similar words in one story
from producing an unrealistically high score.

It adds three public fields to every story:

- business_impact_score
- business_impact_level
- business_impact_explanation

It also adds an internal assessment dictionary that can support later province,
city and historical-risk development:

- business_impact_factors
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# CALIBRATION
# ---------------------------------------------------------------------------

FACTOR_WEIGHTS = {
    "severity": 0.30,
    "geographic_scope": 0.18,
    "business_disruption": 0.24,
    "duration": 0.08,
    "confidence": 0.10,
    "traveller_relevance": 0.10,
}


# ---------------------------------------------------------------------------
# TEXT INDICATORS
# ---------------------------------------------------------------------------

SEVERITY_RULES = [
    (
        95,
        (
            "terror attack",
            "terrorist attack",
            "state of emergency",
            "nationwide unrest",
            "national shutdown",
            "nationwide shutdown",
            "mass casualty",
        ),
        "critical threat",
    ),
    (
        85,
        (
            "bombing",
            "bomb blast",
            "armed attack",
            "hostage",
            "kidnapping",
            "violent riots",
            "widespread violence",
            "severe flooding",
        ),
        "major safety threat",
    ),
    (
        72,
        (
            "shooting",
            "explosion",
            "violent protest",
            "civil unrest",
            "riot",
            "evacuation",
            "wildfire",
            "major flooding",
        ),
        "serious disruptive incident",
    ),
    (
        56,
        (
            "protest",
            "strike",
            "industrial action",
            "security alert",
            "robbery",
            "hijacking",
            "carjacking",
            "flooding",
            "cyber attack",
            "cyberattack",
        ),
        "material incident",
    ),
    (
        35,
        (
            "road closure",
            "road closures",
            "traffic disruption",
            "flight delay",
            "flight delays",
            "power outage",
            "water outage",
            "service disruption",
            "road accident",
        ),
        "limited disruption",
    ),
    (
        20,
        (
            "planned maintenance",
            "scheduled maintenance",
            "roadworks",
            "routine closure",
            "temporary closure",
            "minor delays",
        ),
        "minor or planned disruption",
    ),
]

SCOPE_RULES = [
    (
        100,
        (
            "nationwide",
            "nationally",
            "across south africa",
            "countrywide",
            "national shutdown",
            "all provinces",
        ),
        "national",
    ),
    (
        78,
        (
            "multiple provinces",
            "several provinces",
            "across gauteng",
            "across western cape",
            "across kwazulu-natal",
            "regional disruption",
        ),
        "multi-area",
    ),
    (
        58,
        (
            "citywide",
            "across johannesburg",
            "across cape town",
            "across durban",
            "central business district",
            "cbd",
            "major routes",
        ),
        "city",
    ),
    (
        35,
        (
            "local",
            "one road",
            "single road",
            "intersection",
            "neighbourhood",
            "near ",
        ),
        "local",
    ),
]

BUSINESS_DISRUPTION_RULES = [
    (
        100,
        (
            "airport closed",
            "airport closure",
            "border closed",
            "border closure",
            "port closure",
            "nationwide blackout",
            "national shutdown",
        ),
        "essential systems unavailable",
    ),
    (
        85,
        (
            "flight cancellations",
            "flight cancellation",
            "rail shutdown",
            "transport strike",
            "large transport strike",
            "major power outage",
            "supply chain disruption",
            "fuel shortage",
        ),
        "major operational disruption",
    ),
    (
        68,
        (
            "airport disruption",
            "transport disruption",
            "port congestion",
            "infrastructure failure",
            "load shedding",
            "factory closure",
            "company closure",
        ),
        "substantial business disruption",
    ),
    (
        50,
        (
            "road closure",
            "road closures",
            "traffic disruption",
            "train disruption",
            "rail disruption",
            "power outage",
            "electricity outage",
            "water outage",
            "service delivery protest",
        ),
        "local operational disruption",
    ),
    (
        30,
        (
            "flight delay",
            "flight delays",
            "road accident",
            "minor delays",
            "planned closure",
            "scheduled maintenance",
            "roadworks",
        ),
        "manageable disruption",
    ),
]

DURATION_RULES = [
    (
        100,
        (
            "indefinitely",
            "until further notice",
            "long-term",
            "several weeks",
            "for weeks",
        ),
        "prolonged",
    ),
    (
        75,
        (
            "several days",
            "for days",
            "week-long",
            "throughout the week",
            "ongoing strike",
        ),
        "multi-day",
    ),
    (
        50,
        (
            "two days",
            "48 hours",
            "all day",
            "overnight",
            "ongoing",
        ),
        "extended",
    ),
    (
        25,
        (
            "several hours",
            "for hours",
            "temporary",
            "today",
            "this morning",
            "this afternoon",
        ),
        "short-term",
    ),
]

TRAVELLER_RELEVANCE_RULES = [
    (
        100,
        (
            "airport",
            "flight",
            "border",
            "travel warning",
            "travel advice",
            "tourist",
            "business traveller",
        ),
        "direct travel relevance",
    ),
    (
        82,
        (
            "road closure",
            "traffic",
            "rail",
            "train",
            "transport",
            "hotel",
            "cbd",
            "central business district",
        ),
        "movement relevance",
    ),
    (
        65,
        (
            "protest",
            "strike",
            "security",
            "crime",
            "power outage",
            "water outage",
            "load shedding",
        ),
        "operational relevance",
    ),
    (
        35,
        (
            "investment",
            "regulation",
            "legislation",
            "interest rate",
            "inflation",
            "currency",
            "rand",
            "tax",
            "tariff",
        ),
        "business environment relevance",
    ),
]

HIGH_CONFIDENCE_SOURCE_TERMS = (
    "gov.uk",
    "south african government",
    "government of south africa",
    "saps",
    "south african police service",
    "acsa",
    "airports company south africa",
    "sanral",
    "city of cape town",
    "city of johannesburg",
    "ethekwini municipality",
    "department of transport",
    "department of international relations",
)

MEDIUM_CONFIDENCE_SOURCE_TERMS = (
    "reuters",
    "associated press",
    "bbc",
    "news24",
    "daily maverick",
    "business day",
    "timeslive",
    "ewn",
    "sabc",
)

ROUTINE_TERMS = (
    "speech",
    "remarks by",
    "keynote address",
    "welcomes",
    "congratulates",
    "commemorates",
    "celebrates",
    "media invitation",
    "media briefing",
    "minister to visit",
    "public participation",
    "meeting held",
)

PLANNED_TERMS = (
    "planned",
    "scheduled",
    "maintenance",
    "roadworks",
    "advance notice",
)

ESCALATION_TERMS = (
    "violent",
    "violence",
    "armed",
    "fatal",
    "deaths",
    "killed",
    "injured",
    "widespread",
    "major",
    "severe",
    "emergency",
)

NATIONAL_TERMS = (
    "nationwide",
    "countrywide",
    "across south africa",
    "national shutdown",
    "all provinces",
)


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def _normalise_text(value: Any) -> str:
    """Return compact lowercase text suitable for phrase matching."""

    text = str(value or "").lower()
    return re.sub(r"\s+", " ", text).strip()


def _build_story_text(item: dict[str, Any]) -> str:
    """Combine useful story fields into one searchable text string."""

    parts = [
        item.get("title", ""),
        item.get("summary", ""),
        item.get("description", ""),
        item.get("content", ""),
        item.get("category", ""),
        item.get("raw_category", ""),
        item.get("location", ""),
        item.get("city", ""),
        item.get("province", ""),
    ]

    return _normalise_text(" ".join(str(part) for part in parts if part))


def _build_source_text(item: dict[str, Any]) -> str:
    """Combine source-related fields for confidence assessment."""

    parts = [
        item.get("source", ""),
        item.get("publisher", ""),
        item.get("source_name", ""),
        item.get("url", ""),
        item.get("link", ""),
    ]

    return _normalise_text(" ".join(str(part) for part in parts if part))


def _contains_phrase(text: str, phrase: str) -> bool:
    """
    Match a phrase using word boundaries where practical.

    This avoids false matches such as 'strike' inside an unrelated longer word.
    """

    phrase = _normalise_text(phrase)

    if not phrase:
        return False

    pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
    return re.search(pattern, text) is not None


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    """Return True when at least one phrase is present."""

    return any(_contains_phrase(text, phrase) for phrase in phrases)


def _highest_rule_match(
    text: str,
    rules: list[tuple[int, tuple[str, ...], str]],
    default_score: int,
    default_label: str,
) -> tuple[int, str, str]:
    """
    Use only the strongest matching rule in one assessment dimension.

    Similar indicators therefore do not stack repeatedly.
    """

    for score, phrases, label in rules:
        for phrase in phrases:
            if _contains_phrase(text, phrase):
                return score, label, phrase

    return default_score, default_label, ""


def _assess_severity(text: str) -> tuple[int, str, str]:
    score, label, indicator = _highest_rule_match(
        text=text,
        rules=SEVERITY_RULES,
        default_score=12,
        default_label="no clear immediate threat",
    )

    if _contains_any(text, PLANNED_TERMS) and not _contains_any(
        text,
        ESCALATION_TERMS,
    ):
        score = min(score, 28)
        label = "planned or routine incident"

    return score, label, indicator


def _assess_scope(
    item: dict[str, Any],
    text: str,
) -> tuple[int, str, str]:
    score, label, indicator = _highest_rule_match(
        text=text,
        rules=SCOPE_RULES,
        default_score=30,
        default_label="local or unspecified",
    )

    city = _normalise_text(item.get("city", ""))
    province = _normalise_text(item.get("province", ""))
    location = _normalise_text(item.get("location", ""))

    if not indicator:
        if city:
            return 42, f"city-level ({city})", city

        if province:
            return 62, f"province-level ({province})", province

        if location and location not in {"south africa", "national"}:
            return 38, f"localised ({location})", location

    if _contains_any(text, NATIONAL_TERMS):
        return 100, "national", "national scope"

    return score, label, indicator


def _assess_business_disruption(text: str) -> tuple[int, str, str]:
    score, label, indicator = _highest_rule_match(
        text=text,
        rules=BUSINESS_DISRUPTION_RULES,
        default_score=15,
        default_label="limited immediate disruption",
    )

    if _contains_any(text, PLANNED_TERMS) and score <= 50:
        score = min(score, 32)
        label = "planned and manageable disruption"

    return score, label, indicator


def _assess_duration(text: str) -> tuple[int, str, str]:
    return _highest_rule_match(
        text=text,
        rules=DURATION_RULES,
        default_score=35,
        default_label="duration unclear",
    )


def _assess_confidence(
    item: dict[str, Any],
    source_text: str,
) -> tuple[int, str, str]:
    if _contains_any(source_text, HIGH_CONFIDENCE_SOURCE_TERMS):
        return 95, "official or primary source", "official source"

    if _contains_any(source_text, MEDIUM_CONFIDENCE_SOURCE_TERMS):
        return 78, "established news source", "established source"

    existing_confidence = item.get("confidence_score")

    if isinstance(existing_confidence, (int, float)):
        value = int(round(float(existing_confidence)))

        if 0 <= value <= 1:
            value = int(round(value * 100))

        value = max(0, min(100, value))

        if value >= 80:
            label = "high reported confidence"
        elif value >= 60:
            label = "moderate reported confidence"
        else:
            label = "limited reported confidence"

        return value, label, "existing confidence field"

    return 60, "source confidence not independently confirmed", ""


def _assess_traveller_relevance(text: str) -> tuple[int, str, str]:
    return _highest_rule_match(
        text=text,
        rules=TRAVELLER_RELEVANCE_RULES,
        default_score=18,
        default_label="indirect traveller relevance",
    )


def _apply_context_adjustments(
    raw_score: float,
    text: str,
    severity_score: int,
    scope_score: int,
    disruption_score: int,
) -> tuple[float, list[str]]:
    """
    Apply a small number of controlled adjustments after weighting.

    Adjustments are intentionally capped so they cannot recreate additive
    keyword inflation.
    """

    score = raw_score
    adjustments: list[str] = []

    if _contains_any(text, ROUTINE_TERMS) and severity_score < 50:
        score -= 12
        adjustments.append("routine-announcement reduction")

    if _contains_any(text, PLANNED_TERMS) and severity_score < 50:
        score -= 8
        adjustments.append("planned-disruption reduction")

    if (
        severity_score >= 85
        and scope_score >= 78
        and disruption_score >= 85
    ):
        score += 5
        adjustments.append("major multi-area escalation")

    if scope_score <= 42 and disruption_score <= 50 and severity_score <= 56:
        score = min(score, 58)
        adjustments.append("local-impact ceiling")

    if (
        _contains_phrase(text, "road closure")
        or _contains_phrase(text, "road closures")
        or _contains_phrase(text, "roadworks")
    ) and severity_score <= 35 and scope_score <= 42:
        score = min(score, 32)
        adjustments.append("minor-road-disruption ceiling")

    if severity_score < 85 or scope_score < 78:
        score = min(score, 89)

    return score, adjustments


def _determine_impact_level(score: int) -> str:
    """Convert the numerical score into a calibrated impact level."""

    if score >= 90:
        return "Critical"

    if score >= 75:
        return "Severe"

    if score >= 60:
        return "High"

    if score >= 40:
        return "Moderate"

    if score >= 20:
        return "Guarded"

    return "Low"


def _create_explanation(
    score: int,
    level: str,
    factors: dict[str, dict[str, Any]],
    adjustments: list[str],
) -> str:
    """Produce a concise explanation based on the weighted dimensions."""

    severity = factors["severity"]
    scope = factors["geographic_scope"]
    disruption = factors["business_disruption"]
    duration = factors["duration"]
    confidence = factors["confidence"]
    traveller = factors["traveller_relevance"]

    explanation = (
        f"{level} business impact ({score}/100). "
        f"Assessed as {severity['label']}, with {scope['label']} scope and "
        f"{disruption['label']}. Duration is {duration['label']}; "
        f"source assessment is {confidence['label']}; traveller relevance is "
        f"{traveller['label']}"
    )

    if adjustments:
        readable = ", ".join(
            adjustment.replace("-", " ")
            for adjustment in adjustments
        )
        explanation += f". Calibration applied: {readable}"

    return explanation + "."


def _limit_score(score: float) -> int:
    """Round and constrain the final score to 0–100."""

    return max(0, min(100, int(round(score))))


# ---------------------------------------------------------------------------
# MAIN SCORING FUNCTIONS
# ---------------------------------------------------------------------------

def score_business_impact(item: dict[str, Any]) -> dict[str, Any]:
    """
    Score one story and return a copy containing business-impact fields.

    The original story dictionary is not modified.
    """

    scored_item = dict(item)
    text = _build_story_text(item)
    source_text = _build_source_text(item)

    severity_score, severity_label, severity_indicator = _assess_severity(text)
    scope_score, scope_label, scope_indicator = _assess_scope(item, text)
    disruption_score, disruption_label, disruption_indicator = (
        _assess_business_disruption(text)
    )
    duration_score, duration_label, duration_indicator = _assess_duration(text)
    confidence_score, confidence_label, confidence_indicator = (
        _assess_confidence(item, source_text)
    )
    traveller_score, traveller_label, traveller_indicator = (
        _assess_traveller_relevance(text)
    )

    factors = {
        "severity": {
            "score": severity_score,
            "weight": FACTOR_WEIGHTS["severity"],
            "label": severity_label,
            "indicator": severity_indicator,
        },
        "geographic_scope": {
            "score": scope_score,
            "weight": FACTOR_WEIGHTS["geographic_scope"],
            "label": scope_label,
            "indicator": scope_indicator,
        },
        "business_disruption": {
            "score": disruption_score,
            "weight": FACTOR_WEIGHTS["business_disruption"],
            "label": disruption_label,
            "indicator": disruption_indicator,
        },
        "duration": {
            "score": duration_score,
            "weight": FACTOR_WEIGHTS["duration"],
            "label": duration_label,
            "indicator": duration_indicator,
        },
        "confidence": {
            "score": confidence_score,
            "weight": FACTOR_WEIGHTS["confidence"],
            "label": confidence_label,
            "indicator": confidence_indicator,
        },
        "traveller_relevance": {
            "score": traveller_score,
            "weight": FACTOR_WEIGHTS["traveller_relevance"],
            "label": traveller_label,
            "indicator": traveller_indicator,
        },
    }

    raw_score = sum(
        factor["score"] * factor["weight"]
        for factor in factors.values()
    )

    adjusted_score, adjustments = _apply_context_adjustments(
        raw_score=raw_score,
        text=text,
        severity_score=severity_score,
        scope_score=scope_score,
        disruption_score=disruption_score,
    )

    final_score = _limit_score(adjusted_score)
    impact_level = _determine_impact_level(final_score)

    explanation = _create_explanation(
        score=final_score,
        level=impact_level,
        factors=factors,
        adjustments=adjustments,
    )

    scored_item["business_impact_score"] = final_score
    scored_item["business_impact_level"] = impact_level
    scored_item["business_impact_explanation"] = explanation
    scored_item["business_impact_factors"] = factors

    return scored_item


def apply_business_impact(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Apply business-impact scoring to a complete story list.

    The returned list is ordered from highest impact to lowest impact.
    """

    scored_items = [
        score_business_impact(item)
        for item in items
    ]

    scored_items.sort(
        key=lambda item: item.get("business_impact_score", 0),
        reverse=True,
    )

    return scored_items
