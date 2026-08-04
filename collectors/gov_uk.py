from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from collectors.common import CollectionRequestError, get_json


FCDO_API_URL = (
    "https://www.gov.uk/api/content/"
    "foreign-travel-advice/south-africa"
)

FCDO_PUBLIC_URL = (
    "https://www.gov.uk/foreign-travel-advice/south-africa"
)


def clean_html(value: str) -> str:
    """
    Convert HTML returned by GOV.UK into readable plain text.
    """

    if not value:
        return ""

    soup = BeautifulSoup(value, "html.parser")

    return " ".join(soup.stripped_strings)


def create_item(
    *,
    title: str,
    summary: str,
    url: str,
    published: str,
    section: str,
) -> dict[str, Any]:
    """
    Create one standard intelligence item.
    """

    return {
        "title": title,
        "summary": summary,
        "url": url,
        "source": (
            "UK Foreign, Commonwealth "
            "& Development Office"
        ),
        "source_type": "official",
        "location": "National",
        "city_id": None,
        "published": published,
        "event_date": published,
        "collector": "gov_uk",
        "raw_category": "Official travel advice",
        "confidence": "Confirmed",
        "section": section,
    }


def collect_fcdo_advice() -> list[dict[str, Any]]:
    """
    Collect official British government travel advice
    for South Africa.

    The collector returns:
    - the main country advice item
    - individual items for each available advice section
    """

    data = get_json(FCDO_API_URL)

    if not isinstance(data, dict):
        raise CollectionRequestError(
            "The GOV.UK Content API returned an unexpected format."
        )

    title = str(
        data.get("title")
        or "South Africa travel advice"
    )

    description = clean_html(
        str(data.get("description") or "")
    )

    updated_at = str(
        data.get("public_updated_at")
        or data.get("updated_at")
        or ""
    )

    details = data.get("details", {})

    if not isinstance(details, dict):
        details = {}

    change_note = clean_html(
        str(details.get("change_note") or "")
    )

    main_summary = change_note or description

    items: list[dict[str, Any]] = []

    items.append(
        create_item(
            title=title,
            summary=main_summary,
            url=FCDO_PUBLIC_URL,
            published=updated_at,
            section="Main travel advice",
        )
    )

    parts = details.get("parts", [])

    if not isinstance(parts, list):
        parts = []

    for part in parts:
        if not isinstance(part, dict):
            continue

        part_title = clean_html(
            str(part.get("title") or "")
        )

        part_body = clean_html(
            str(part.get("body") or "")
        )

        part_slug = str(
            part.get("slug") or ""
        ).strip()

        if not part_title or not part_body:
            continue

        part_url = FCDO_PUBLIC_URL

        if part_slug:
            part_url = f"{FCDO_PUBLIC_URL}/{part_slug}"

        items.append(
            create_item(
                title=f"FCDO advice: {part_title}",
                summary=part_body[:1500],
                url=part_url,
                published=updated_at,
                section=part_title,
            )
        )

    return items