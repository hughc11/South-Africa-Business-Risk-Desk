from __future__ import annotations

CATEGORY_KEYWORDS = {
    "Protests and civil unrest": ["protest", "demonstration", "march", "riot", "unrest", "shutdown", "picket"],
    "Road and transport disruption": ["road closure", "closed road", "traffic", "rail", "train", "airport", "flight", "port", "freight", "transport"],
    "Infrastructure": ["electricity", "power", "outage", "water", "infrastructure", "load shedding", "substation"],
    "Security and crime": ["crime", "robbery", "kidnap", "shooting", "security", "violence", "attack"],
    "Economy and business": ["business", "economy", "economic", "investment", "company", "market", "inflation", "trade", "currency"],
    "Politics and government": ["government", "minister", "president", "parliament", "election", "coalition", "policy", "regulation"],
}
DISRUPTION_KEYWORDS = {"protest", "demonstration", "closure", "closed", "strike", "shutdown", "outage", "disruption", "delay", "violence", "robbery", "attack", "flood", "fire"}


def _category_for(text: str, fallback: str) -> str:
    scores = {category: sum(keyword in text for keyword in keywords) for category, keywords in CATEGORY_KEYWORDS.items()}
    category, score = max(scores.items(), key=lambda entry: entry[1])
    return category if score else (fallback or "General intelligence")


def _relevance_score(item: dict, text: str) -> int:
    score = 25
    if item.get("source_type") in {"official", "official traffic"}: score += 25
    if item.get("location") != "National": score += 10
    score += min(30, sum(keyword in text for keyword in DISRUPTION_KEYWORDS) * 6)
    if item.get("published_timestamp"): score += 10
    return max(0, min(100, score))


def classify_items(items: list[dict]) -> list[dict]:
    output = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        classified = dict(item)
        classified["category"] = _category_for(text, item.get("raw_category", ""))
        classified["relevance_score"] = _relevance_score(item, text)
        classified["relevance"] = "High" if classified["relevance_score"] >= 70 else "Medium" if classified["relevance_score"] >= 45 else "Low"
        output.append(classified)
    return output
