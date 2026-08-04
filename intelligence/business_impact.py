"""
Business impact scoring for the South Africa Business Risk Desk.

This module examines each collected story and estimates how important it may
be for a British business traveller or company operating in South Africa.

It adds three fields to every story:

- business_impact_score
- business_impact_level
- business_impact_explanation
"""

from typing import Any


# ---------------------------------------------------------------------------
# SCORING RULES
# ---------------------------------------------------------------------------

# Each keyword is connected to a number of impact points.
# Higher numbers represent issues that are more likely to disrupt business
# travel, operations, safety, transport, infrastructure or investment.

HIGH_IMPACT_KEYWORDS = {
    "terror attack": 45,
    "terrorism": 40,
    "bomb": 40,
    "explosion": 35,
    "armed attack": 40,
    "shooting": 35,
    "hostage": 40,
    "kidnapping": 40,
    "state of emergency": 45,
    "national shutdown": 45,
    "airport closed": 45,
    "airport closure": 45,
    "flight cancellations": 35,
    "flight cancellation": 35,
    "major power outage": 40,
    "nationwide blackout": 45,
    "blackout": 30,
    "load shedding": 25,
    "violent protest": 35,
    "violent protests": 35,
    "civil unrest": 35,
    "riot": 35,
    "riots": 35,
    "flooding": 30,
    "severe flooding": 40,
    "wildfire": 30,
    "evacuation": 35,
    "border closed": 40,
    "border closure": 40,
    "port closure": 40,
    "rail shutdown": 35,
    "road closure": 25,
    "road closures": 25,
}

MEDIUM_IMPACT_KEYWORDS = {
    "protest": 20,
    "protests": 20,
    "strike": 20,
    "industrial action": 20,
    "transport disruption": 25,
    "traffic disruption": 18,
    "airport disruption": 25,
    "flight delay": 18,
    "flight delays": 18,
    "train disruption": 20,
    "rail disruption": 20,
    "power outage": 22,
    "electricity outage": 22,
    "water outage": 18,
    "water shortage": 18,
    "service delivery protest": 22,
    "crime": 15,
    "robbery": 20,
    "hijacking": 25,
    "carjacking": 25,
    "security alert": 25,
    "travel warning": 30,
    "travel advice": 25,
    "health warning": 22,
    "disease outbreak": 30,
    "cyber attack": 30,
    "cyberattack": 30,
    "infrastructure failure": 28,
    "supply chain disruption": 30,
    "fuel shortage": 25,
    "port congestion": 22,
    "road accident": 15,
    "major accident": 22,
}

BUSINESS_AND_POLICY_KEYWORDS = {
    "interest rate": 18,
    "inflation": 15,
    "currency": 12,
    "rand": 10,
    "tax": 15,
    "tariff": 18,
    "trade restriction": 22,
    "trade agreement": 15,
    "sanctions": 25,
    "regulation": 15,
    "new law": 18,
    "legislation": 15,
    "government policy": 15,
    "budget": 15,
    "investment": 12,
    "foreign investment": 18,
    "business confidence": 15,
    "economic growth": 12,
    "recession": 25,
    "unemployment": 12,
    "company closure": 20,
    "factory closure": 25,
    "retrenchment": 18,
    "job losses": 18,
    "banking": 12,
    "financial markets": 12,
    "corruption": 18,
    "investigation": 10,
    "procurement": 10,
    "tender": 8,
    "mining": 10,
    "energy": 10,
    "logistics": 15,
    "shipping": 12,
    "tourism": 10,
}

LOW_VALUE_ROUTINE_KEYWORDS = {
    "speech": -8,
    "remarks by": -8,
    "keynote address": -8,
    "welcomes": -5,
    "congratulates": -8,
    "commemorates": -6,
    "celebrates": -6,
    "media invitation": -12,
    "media briefing": -5,
    "minister to visit": -8,
    "public participation": -5,
    "meeting held": -5,
    "official statement": -3,
}


# Categories that are generally important to business travellers.
CATEGORY_BONUSES = {
    "security": 18,
    "crime and security": 18,
    "protests and civil unrest": 20,
    "transport": 15,
    "road and transport disruption": 18,
    "infrastructure": 15,
    "energy": 15,
    "economy and business": 12,
    "government and regulation": 10,
    "politics and government": 8,
    "health": 12,
    "weather": 12,
    "travel advice": 20,
}


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def _build_story_text(item: dict[str, Any]) -> str:
    """
    Combine the useful story fields into one lowercase text string.
    """

    parts = [
        item.get("title", ""),
        item.get("summary", ""),
        item.get("description", ""),
        item.get("category", ""),
        item.get("raw_category", ""),
        item.get("location", ""),
        item.get("city", ""),
        item.get("province", ""),
        item.get("source", ""),
    ]

    return " ".join(str(part) for part in parts if part).lower()


def _find_keyword_scores(
    text: str,
    keyword_rules: dict[str, int],
) -> tuple[int, list[tuple[str, int]]]:
    """
    Find matching keywords and return their combined score and details.
    """

    score = 0
    matches: list[tuple[str, int]] = []

    for keyword, points in keyword_rules.items():
        if keyword in text:
            score += points
            matches.append((keyword, points))

    return score, matches


def _get_category_bonus(item: dict[str, Any]) -> tuple[int, str]:
    """
    Add points when the story belongs to a business-relevant category.
    """

    category = str(item.get("category", "")).strip().lower()

    if not category:
        return 0, ""

    for category_name, bonus in CATEGORY_BONUSES.items():
        if category_name in category:
            return bonus, category_name

    return 0, ""


def _limit_score(score: int) -> int:
    """
    Keep the final score between 0 and 100.
    """

    return max(0, min(100, score))


def _determine_impact_level(score: int) -> str:
    """
    Convert the numerical score into a clear impact level.
    """

    if score >= 75:
        return "Critical"

    if score >= 50:
        return "High"

    if score >= 25:
        return "Moderate"

    return "Low"


def _create_explanation(
    score: int,
    level: str,
    positive_matches: list[tuple[str, int]],
    category_match: str,
    routine_matches: list[tuple[str, int]],
) -> str:
    """
    Produce a short explanation showing why the story received its score.
    """

    strongest_matches = sorted(
        positive_matches,
        key=lambda match: match[1],
        reverse=True,
    )[:3]

    reasons: list[str] = []

    if strongest_matches:
        readable_keywords = [
            keyword.replace("_", " ")
            for keyword, _points in strongest_matches
        ]

        reasons.append(
            "Relevant indicators include "
            + ", ".join(readable_keywords)
        )

    if category_match:
        reasons.append(
            f"the story is classified under {category_match}"
        )

    if routine_matches and not positive_matches:
        reasons.append(
            "the story appears to be a routine announcement with limited "
            "immediate operational impact"
        )

    if not reasons:
        reasons.append(
            "no strong immediate business disruption indicators were found"
        )

    explanation = ". ".join(reasons).strip()

    if explanation:
        explanation = explanation[0].upper() + explanation[1:]

    return (
        f"{level} business impact ({score}/100). "
        f"{explanation}."
    )


# ---------------------------------------------------------------------------
# MAIN SCORING FUNCTIONS
# ---------------------------------------------------------------------------

def score_business_impact(item: dict[str, Any]) -> dict[str, Any]:
    """
    Score one story and return a copy containing the new impact fields.

    The original story dictionary is not modified.
    """

    scored_item = dict(item)
    text = _build_story_text(item)

    base_score = 5

    high_score, high_matches = _find_keyword_scores(
        text,
        HIGH_IMPACT_KEYWORDS,
    )

    medium_score, medium_matches = _find_keyword_scores(
        text,
        MEDIUM_IMPACT_KEYWORDS,
    )

    business_score, business_matches = _find_keyword_scores(
        text,
        BUSINESS_AND_POLICY_KEYWORDS,
    )

    routine_score, routine_matches = _find_keyword_scores(
        text,
        LOW_VALUE_ROUTINE_KEYWORDS,
    )

    category_bonus, category_match = _get_category_bonus(item)

    positive_matches = (
        high_matches
        + medium_matches
        + business_matches
    )

    total_score = (
        base_score
        + high_score
        + medium_score
        + business_score
        + routine_score
        + category_bonus
    )

    # Avoid excessive scoring caused by several very similar keyword matches.
    if len(positive_matches) >= 4:
        total_score += 5

    final_score = _limit_score(total_score)
    impact_level = _determine_impact_level(final_score)

    explanation = _create_explanation(
        score=final_score,
        level=impact_level,
        positive_matches=positive_matches,
        category_match=category_match,
        routine_matches=routine_matches,
    )

    scored_item["business_impact_score"] = final_score
    scored_item["business_impact_level"] = impact_level
    scored_item["business_impact_explanation"] = explanation

    return scored_item


def apply_business_impact(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Apply business impact scoring to a complete list of stories.

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