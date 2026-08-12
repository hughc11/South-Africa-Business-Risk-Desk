"""
Format backend intelligence for the South Africa Business Risk Desk website.

The backend produces:
- metadata
- national_risk
- items

The website expects:
- metadata
- national
- timeline
- cities
- travel_advice
- incidents
- news
- daily_language_brief
- conversation_brief

Version 2 output principles:
- Keep FCDO travel advice separate from operational notices.
- Operational notices are current or imminent only.
- Operational notices are limited to:
    - road closures / significant traffic disruption
    - demonstrations / protests
    - major sports matches
    - major music events
- Ordinary news must never appear as an operational notice.
- General news must be recent and materially business-relevant.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
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


ROAD_KEYWORDS = {
    "road closure",
    "road closed",
    "road closures",
    "roads closed",
    "lane closure",
    "lane closed",
    "lane closures",
    "traffic closure",
    "traffic disruption",
    "traffic delays",
    "traffic delay",
    "route closed",
    "route closure",
    "motorway closure",
    "highway closure",
    "bridge closed",
    "street closed",
    "roadworks",
    "collision",
    "crash",
    "accident",
    "traffic backed up",
    "traffic backed-up",
}


PROTEST_KEYWORDS = {
    "protest",
    "protests",
    "demonstration",
    "demonstrations",
    "march",
    "marches",
    "strike",
    "strikes",
    "picket",
    "picketing",
    "civil unrest",
}


SPORT_KEYWORDS = {
    "rugby",
    "football",
    "soccer",
    "cricket",
    "fixture",
    "stadium",
    "springboks",
    "bafana bafana",
    "proteas",
    "premiership",
    "united rugby championship",
    "currie cup",
    "test match",
    "international match",
    "league match",
}


MUSIC_KEYWORDS = {
    "concert",
    "music festival",
    "live music",
    "tour date",
    "arena concert",
    "live performance",
    "gig",
}



# ---------------------------------------------------------------------------
# DAILY BUSINESS LANGUAGE BRIEF
#
# Curated rather than generated live so the dashboard remains deterministic,
# reliable and independent of external APIs. The formatter selects one entry
# from each language using the briefing date.
# ---------------------------------------------------------------------------

AFRIKAANS_BUSINESS_LANGUAGE = [
    {
        "word": "Dankie",
        "english": "Thank you",
        "pronunciation": "DAHN-kee",
        "example": "Dankie vir jou tyd.",
        "example_english": "Thank you for your time.",
        "use_note": "A simple, widely useful expression of thanks after a meeting, introduction or assistance.",
    },
    {
        "word": "Baie dankie",
        "english": "Thank you very much",
        "pronunciation": "BY-uh DAHN-kee",
        "example": "Baie dankie vir die vergadering.",
        "example_english": "Thank you very much for the meeting.",
        "use_note": "A warmer form of thanks that remains appropriate in professional and hospitality settings.",
    },
    {
        "word": "Asseblief",
        "english": "Please",
        "pronunciation": "AH-suh-bleef",
        "example": "Koffie, asseblief.",
        "example_english": "Coffee, please.",
        "use_note": "Useful for polite requests; courtesy is important when dealing with colleagues, hosts and service staff.",
    },
    {
        "word": "Goeiedag",
        "english": "Good day / Hello",
        "pronunciation": "KHOO-ee-dakh",
        "example": "Goeiedag. Dis goed om jou te ontmoet.",
        "example_english": "Good day. It is good to meet you.",
        "use_note": "A useful professional greeting, particularly when meeting someone for the first time.",
    },
    {
        "word": "Goeiemôre",
        "english": "Good morning",
        "pronunciation": "KHOO-ee-MOR-ruh",
        "example": "Goeiemôre. Hoe gaan dit?",
        "example_english": "Good morning. How are you?",
        "use_note": "A polite way to open an early meeting or workplace conversation.",
    },
    {
        "word": "Vergadering",
        "english": "Meeting",
        "pronunciation": "fur-KHAH-duh-ring",
        "example": "Hoe laat begin die vergadering?",
        "example_english": "What time does the meeting start?",
        "use_note": "Core workplace vocabulary and useful when confirming schedules or meeting arrangements.",
    },
    {
        "word": "Besigheid",
        "english": "Business",
        "pronunciation": "buh-SAY-khite",
        "example": "Ons praat oor besigheid.",
        "example_english": "We are talking about business.",
        "use_note": "A common general term for business and commercial discussion.",
    },
    {
        "word": "Ooreenkoms",
        "english": "Agreement / Deal",
        "pronunciation": "OO-ruhn-koms",
        "example": "Ons het 'n ooreenkoms.",
        "example_english": "We have an agreement.",
        "use_note": "Useful in negotiation and commercial discussions; context determines whether it means an agreement or deal.",
    },
    {
        "word": "Kontrak",
        "english": "Contract",
        "pronunciation": "KON-trak",
        "example": "Ons bespreek die kontrak.",
        "example_english": "We are discussing the contract.",
        "use_note": "Straightforward commercial vocabulary that may be recognised easily by English speakers.",
    },
    {
        "word": "Kollega",
        "english": "Colleague",
        "pronunciation": "koo-LEH-khah",
        "example": "Laat ek jou aan my kollega voorstel.",
        "example_english": "Let me introduce you to my colleague.",
        "use_note": "Useful when making introductions in meetings or workplace settings.",
    },
    {
        "word": "Kantoor",
        "english": "Office",
        "pronunciation": "kahn-TOOR",
        "example": "Ons ontmoet by die kantoor.",
        "example_english": "We are meeting at the office.",
        "use_note": "Useful for confirming a workplace or meeting location.",
    },
    {
        "word": "Afspraak",
        "english": "Appointment",
        "pronunciation": "AHF-sprahk",
        "example": "Ek sien uit na ons afspraak.",
        "example_english": "I am looking forward to our appointment.",
        "use_note": "Useful when arranging or referring to a scheduled professional meeting.",
    },
    {
        "word": "Skedule",
        "english": "Schedule",
        "pronunciation": "skuh-DOO-luh",
        "example": "Hoe besig is jou skedule?",
        "example_english": "How busy is your schedule?",
        "use_note": "Practical vocabulary for arranging meetings and discussing availability.",
    },
    {
        "word": "Begin",
        "english": "Begin / Start",
        "pronunciation": "buh-KHIN",
        "example": "Sal ons begin?",
        "example_english": "Shall we begin?",
        "use_note": "A concise and useful phrase for opening a meeting once everyone is ready.",
    },
    {
        "word": "Saamstem",
        "english": "Agree",
        "pronunciation": "SAHM-stem",
        "example": "Ek stem saam.",
        "example_english": "I agree.",
        "use_note": "Useful in meetings and negotiations when expressing agreement clearly and politely.",
    },
    {
        "word": "Voorstel",
        "english": "Suggestion / Proposal",
        "pronunciation": "FOOR-stel",
        "example": "Wat stel jy voor?",
        "example_english": "What do you suggest?",
        "use_note": "Useful for inviting another person's recommendation during a discussion or negotiation.",
    },
    {
        "word": "Verslag",
        "english": "Report",
        "pronunciation": "fur-SLAKH",
        "example": "Ek het die verslag nodig.",
        "example_english": "I need the report.",
        "use_note": "Common workplace vocabulary for written reporting and business information.",
    },
    {
        "word": "Aanbieding",
        "english": "Presentation",
        "pronunciation": "AHN-bee-ding",
        "example": "Dankie vir die aanbieding.",
        "example_english": "Thank you for the presentation.",
        "use_note": "Useful around briefings, pitches and formal business presentations.",
    },
    {
        "word": "Adviseur",
        "english": "Adviser",
        "pronunciation": "at-fuh-SUR",
        "example": "Sy is ons adviseur.",
        "example_english": "She is our adviser.",
        "use_note": "Useful when describing professional roles in consulting or business discussions.",
    },
    {
        "word": "Produktief",
        "english": "Productive",
        "pronunciation": "pro-duk-TEEF",
        "example": "Dit was baie produktief.",
        "example_english": "That was very productive.",
        "use_note": "A positive, professional way to describe a useful meeting or discussion.",
    },
]

ISIXHOSA_BUSINESS_LANGUAGE = [
    {
        "word": "Enkosi",
        "english": "Thank you",
        "pronunciation": "en-KOH-see",
        "example": "Enkosi.",
        "example_english": "Thank you.",
        "use_note": "One of the most useful isiXhosa expressions for polite professional, hospitality and everyday interaction.",
    },
    {
        "word": "Molo",
        "english": "Hello (one person)",
        "pronunciation": "MOH-loh",
        "example": "Molo.",
        "example_english": "Hello.",
        "use_note": "Use when greeting one person; a simple local greeting can be a respectful way to begin an interaction.",
    },
    {
        "word": "Molweni",
        "english": "Hello (several people)",
        "pronunciation": "moh-LWEH-nee",
        "example": "Molweni.",
        "example_english": "Hello, everyone.",
        "use_note": "The plural greeting, useful when entering a meeting or greeting a group.",
    },
    {
        "word": "Wamkelekile",
        "english": "Welcome",
        "pronunciation": "wahm-keh-LEH-kee-leh",
        "example": "Wamkelekile.",
        "example_english": "Welcome.",
        "use_note": "Useful in hospitality and welcoming contexts; the exact form can vary with who is being addressed.",
    },
    {
        "word": "Unjani?",
        "english": "How are you? (one person)",
        "pronunciation": "oon-JAH-nee",
        "example": "Molo, unjani?",
        "example_english": "Hello, how are you?",
        "use_note": "A friendly follow-up to a greeting when speaking to one person.",
    },
    {
        "word": "Ninjani?",
        "english": "How are you? (several people)",
        "pronunciation": "neen-JAH-nee",
        "example": "Molweni, ninjani?",
        "example_english": "Hello, how are you all?",
        "use_note": "The plural form, useful when greeting a small group or team.",
    },
    {
        "word": "Ndiphilile",
        "english": "I am well",
        "pronunciation": "n-dee-pee-LEE-leh",
        "example": "Ndiphilile, enkosi.",
        "example_english": "I am well, thank you.",
        "use_note": "A useful response when someone asks how you are.",
    },
    {
        "word": "Igama",
        "english": "Name",
        "pronunciation": "ee-GAH-mah",
        "example": "Lithini igama lakho?",
        "example_english": "What is your name?",
        "use_note": "Useful in introductions; the full phrase is more practical than using the noun on its own.",
    },
    {
        "word": "Ewe",
        "english": "Yes",
        "pronunciation": "EH-weh",
        "example": "Ewe.",
        "example_english": "Yes.",
        "use_note": "A basic affirmative response useful in everyday interaction.",
    },
    {
        "word": "Hayi",
        "english": "No",
        "pronunciation": "HAH-yee",
        "example": "Hayi.",
        "example_english": "No.",
        "use_note": "A basic negative response; tone and context remain important in professional interaction.",
    },
    {
        "word": "Uxolo",
        "english": "Excuse me / Sorry",
        "pronunciation": "oo-KHOH-loh",
        "example": "Uxolo.",
        "example_english": "Excuse me / Sorry.",
        "use_note": "Useful for politely getting attention or apologising in everyday interaction.",
    },
    {
        "word": "Sala kakuhle",
        "english": "Goodbye (to one person staying)",
        "pronunciation": "SAH-lah kah-KOO-hleh",
        "example": "Sala kakuhle.",
        "example_english": "Goodbye.",
        "use_note": "Traditionally said by the person leaving to one person who is staying.",
    },
    {
        "word": "Hamba kakuhle",
        "english": "Goodbye (to one person leaving)",
        "pronunciation": "HAHM-bah kah-KOO-hleh",
        "example": "Hamba kakuhle.",
        "example_english": "Go well / Goodbye.",
        "use_note": "Traditionally said to one person who is leaving; useful when ending an interaction courteously.",
    },
    {
        "word": "Kulungile",
        "english": "It is okay / All right",
        "pronunciation": "koo-loon-GEE-leh",
        "example": "Kulungile.",
        "example_english": "All right.",
        "use_note": "A useful acknowledgement in everyday conversation.",
    },
    {
        "word": "Nceda",
        "english": "Please / Help",
        "pronunciation": "n-CEH-dah",
        "example": "Nceda.",
        "example_english": "Please / Help.",
        "use_note": "A useful polite or assistance-related expression; the precise meaning depends on the sentence around it.",
    },
    {
        "word": "Ndiyabulela",
        "english": "I thank you",
        "pronunciation": "n-dee-yah-boo-LEH-lah",
        "example": "Ndiyabulela.",
        "example_english": "I thank you.",
        "use_note": "A fuller expression of gratitude that can add warmth to a courteous interaction.",
    },
]

FCDO_PREFERRED_SECTIONS = (
    "warnings and insurance",
    "safety and security",
    "getting help",
    "entry requirements",
    "health",
)


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
    Convert a business-impact score into an operational severity.
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


def _normalise_text(value: Any) -> str:
    """
    Convert text into a simple lowercase comparison string.
    """

    return " ".join(
        str(value or "").lower().split()
    )


def _combined_text(
    item: dict[str, Any],
) -> str:
    """
    Combine useful text fields for keyword matching.
    """

    return " ".join(
        [
            _normalise_text(
                item.get("title")
            ),
            _normalise_text(
                item.get("summary")
            ),
            _normalise_text(
                item.get("category")
            ),
            _normalise_text(
                item.get("raw_category")
            ),
            _normalise_text(
                item.get("section")
            ),
        ]
    )


def _contains_any(
    text: str,
    keywords: set[str],
) -> bool:
    """
    Check whether a text contains any supplied keyword.
    """

    return any(
        keyword in text
        for keyword in keywords
    )


def _parse_datetime(
    value: Any,
) -> datetime | None:
    """
    Parse the date formats used by the collection engine.
    """

    raw = str(value or "").strip()

    if not raw:
        return None

    candidates = [raw]

    if raw.endswith("Z"):
        candidates.append(
            raw[:-1] + "+00:00"
        )

    for candidate in candidates:

        try:
            parsed = datetime.fromisoformat(
                candidate
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.astimezone(
                timezone.utc
            )

        except ValueError:
            pass

    formats = (
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%d %b %Y, %H:%M UTC",
        "%Y-%m-%d",
    )

    for fmt in formats:

        try:
            parsed = datetime.strptime(
                raw,
                fmt,
            )

            return parsed.replace(
                tzinfo=timezone.utc
            )

        except ValueError:
            continue

    return None


def _item_datetime(
    item: dict[str, Any],
    key: str,
) -> datetime | None:
    """
    Extract either the publication date or event date.
    """

    if key == "published":

        values = (
            item.get(
                "published_timestamp"
            ),
            item.get(
                "published"
            ),
            item.get(
                "published_display"
            ),
        )

    else:

        values = (
            item.get(
                "event_date"
            ),
            item.get(
                "event_timestamp"
            ),
        )

    for value in values:

        parsed = _parse_datetime(
            value
        )

        if parsed is not None:
            return parsed

    return None


def _is_fcdo_item(
    item: dict[str, Any],
) -> bool:
    """
    Identify official UK FCDO travel-advice material.
    """

    source = _normalise_text(
        item.get("source")
    )

    collector = _normalise_text(
        item.get("collector")
    )

    raw_category = _normalise_text(
        item.get("raw_category")
    )

    return (
        "foreign, commonwealth & development office"
        in source
        or "fcdo" in source
        or collector == "gov_uk"
        or "official travel advice"
        in raw_category
    )


def _analysis_items(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Remove FCDO pages from dashboard risk-display calculations.

    FCDO pages are authoritative travel guidance rather than
    individual live incidents. They are therefore presented in
    their own dedicated travel-advice section.
    """

    return [
        item
        for item in items
        if not _is_fcdo_item(item)
    ]


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
                item.get(
                    "business_impact_score"
                )
            )
            for item in items
        ),
        reverse=True,
    )

    selected_scores = scores[
        :maximum_items
    ]

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
    Build the national-risk breakdown bars.
    """

    components: list[
        dict[str, Any]
    ] = []

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
                "name": (
                    definition["name"]
                ),
                "score": score,
            }
        )

    return components


def _item_matches_city(
    item: dict[str, Any],
    city: dict[str, Any],
) -> bool:
    """
    Check whether an intelligence item belongs to a configured city.
    """

    item_city_id = _normalise_text(
        item.get("city_id")
    )

    if item_city_id == city["id"]:
        return True

    location = _normalise_text(
        item.get("location")
    )

    return any(
        city_name.lower()
        in location
        for city_name
        in city["location_names"]
    )


def _build_cities(
    items: list[dict[str, Any]],
    national_score: int,
) -> list[dict[str, Any]]:
    """
    Build city-risk information used by the map.
    """

    cities: list[
        dict[str, Any]
    ] = []

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

            city_score = (
                _average_top_scores(
                    city_items,
                    maximum_items=5,
                )
            )

            strongest_categories: list[
                str
            ] = []

            for item in sorted(
                city_items,
                key=lambda story: (
                    _safe_int(
                        story.get(
                            "business_impact_score"
                        )
                    )
                ),
                reverse=True,
            ):

                category = str(
                    item.get(
                        "category",
                        "Current incidents",
                    )
                ).strip()

                if (
                    category
                    and category
                    not in strongest_categories
                ):

                    strongest_categories.append(
                        category
                    )

            category_text = ", ".join(
                strongest_categories[:2]
            )

            summary = (
                "Current city risk is being "
                "driven by "
                f"{category_text.lower()}."
            )

        else:

            city_score = max(
                10,
                round(
                    national_score * 0.55
                ),
            )

            summary = (
                "No strong city-specific "
                "incidents were identified "
                "in the current collection "
                "period."
            )

        cities.append(
            {
                "id": city["id"],
                "name": city["name"],
                "latitude": (
                    city["latitude"]
                ),
                "longitude": (
                    city["longitude"]
                ),
                "default_zoom": (
                    city["default_zoom"]
                ),
                "score": city_score,
                "level": _risk_level(
                    city_score
                ),
                "summary": summary,
            }
        )

    return cities


def _build_travel_advice(
    items: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    """
    Build a dedicated UK Government Travel Advice object.
    """

    fcdo_items = [
        item
        for item in items
        if _is_fcdo_item(item)
    ]

    if not fcdo_items:

        return {
            "available": False,
            "source": (
                "UK Foreign, Commonwealth "
                "& Development Office"
            ),
            "status": (
                "Advice unavailable in "
                "current collection"
            ),
            "last_updated": "",
            "last_checked": generated_at,
            "summary": (
                "The current collection did "
                "not return FCDO travel advice. "
                "Check GOV.UK before travel."
            ),
            "url": (
                "https://www.gov.uk/"
                "foreign-travel-advice/"
                "south-africa"
            ),
            "confidence": (
                "Official source"
            ),
        }

    def priority(
        item: dict[str, Any],
    ) -> tuple[int, datetime]:

        section = _normalise_text(
            item.get("section")
        )

        title = _normalise_text(
            item.get("title")
        )

        section_rank = len(
            FCDO_PREFERRED_SECTIONS
        )

        for (
            index,
            preferred,
        ) in enumerate(
            FCDO_PREFERRED_SECTIONS
        ):

            if (
                preferred in section
                or preferred in title
            ):

                section_rank = index
                break

        published = _item_datetime(
            item,
            "published",
        )

        if published is None:
            published = datetime(
                1970,
                1,
                1,
                tzinfo=timezone.utc,
            )

        return (
            -section_rank,
            published,
        )

    selected = max(
        fcdo_items,
        key=priority,
    )

    summary = str(
        selected.get("summary")
        or ""
    ).strip()

    if len(summary) > 520:

        summary = (
            summary[:517].rstrip()
            + "..."
        )

    latest_dates = [
        _item_datetime(
            item,
            "published",
        )
        for item in fcdo_items
    ]

    latest_dates = [
        date
        for date in latest_dates
        if date is not None
    ]

    latest_update = (
        max(latest_dates)
        if latest_dates
        else None
    )

    if latest_update:

        last_updated = (
            latest_update.strftime(
                "%d %b %Y, %H:%M UTC"
            )
        )

    else:

        last_updated = str(
            selected.get(
                "published_display"
            )
            or ""
        )

    return {
        "available": True,
        "source": (
            "UK Foreign, Commonwealth "
            "& Development Office"
        ),
        "status": (
            "Official travel advice available"
        ),
        "section": (
            selected.get("section")
            or "South Africa travel advice"
        ),
        "last_updated": (
            last_updated
        ),
        "last_checked": (
            generated_at
        ),
        "summary": (
            summary
            or (
                "Official FCDO travel advice "
                "was collected successfully."
            )
        ),
        "url": (
            selected.get("url")
            or (
                "https://www.gov.uk/"
                "foreign-travel-advice/"
                "south-africa"
            )
        ),
        "confidence": "Confirmed",
    }


def _operational_type(
    item: dict[str, Any],
) -> str | None:
    """
    Determine whether an item belongs in the very selective
    Active Operational Notices section.
    """

    text = _combined_text(
        item
    )

    category = _normalise_category(
        item.get("category")
    )

    # IMPORTANT:
    # Do not classify every transport story as a road closure.
    # It must contain explicit road/traffic-disruption language.

    if _contains_any(
        text,
        ROAD_KEYWORDS,
    ):
        return "Road closure"

    if (
        _contains_any(
            text,
            PROTEST_KEYWORDS,
        )
        or category
        == "protests and civil unrest"
    ):
        return "Demonstration"

    if _contains_any(
        text,
        SPORT_KEYWORDS,
    ):
        return "Sport"

    if _contains_any(
        text,
        MUSIC_KEYWORDS,
    ):
        return "Music"

    return None


def _is_current_operational_item(
    item: dict[str, Any],
    now_utc: datetime,
) -> bool:
    """
    Enforce strict freshness rules for operational notices.
    """

    notice_type = _operational_type(
        item
    )

    if (
        notice_type is None
        or _is_fcdo_item(item)
    ):
        return False

    published = _item_datetime(
        item,
        "published",
    )

    event_date = _item_datetime(
        item,
        "event",
    )

    text = _combined_text(
        item
    )

    # ---------------------------------------------------------
    # ROAD CLOSURES
    #
    # Only current / very recent road disruption should survive.
    # ---------------------------------------------------------

    if notice_type == "Road closure":

        if event_date is not None:

            return (
                now_utc
                - timedelta(hours=12)
                <= event_date
                <= now_utc
                + timedelta(days=3)
            )

        if published is None:
            return False

        current_language = any(
            phrase in text
            for phrase in (
                "closed",
                "closure",
                "ongoing",
                "today",
                "currently",
                "traffic",
                "roadworks",
                "delays",
                "backed up",
                "backed-up",
            )
        )

        return (
            current_language
            and (
                now_utc
                - timedelta(hours=48)
                <= published
                <= now_utc
                + timedelta(hours=2)
            )
        )

    # ---------------------------------------------------------
    # DEMONSTRATIONS
    #
    # Only active events or credible imminent events.
    # ---------------------------------------------------------

    if notice_type == "Demonstration":

        if event_date is not None:

            return (
                now_utc
                - timedelta(hours=12)
                <= event_date
                <= now_utc
                + timedelta(hours=72)
            )

        if published is None:
            return False

        imminent_language = any(
            phrase in text
            for phrase in (
                "today",
                "tomorrow",
                "planned",
                "scheduled",
                "ongoing",
                "currently",
                "march",
                "protest",
                "demonstration",
                "strike",
            )
        )

        return (
            imminent_language
            and (
                now_utc
                - timedelta(hours=36)
                <= published
                <= now_utc
                + timedelta(hours=2)
            )
        )

    # ---------------------------------------------------------
    # SPORT / MUSIC
    #
    # These must have an actual event date.
    # Past-event reporting is excluded.
    # ---------------------------------------------------------

    if notice_type in {
        "Sport",
        "Music",
    }:

        if event_date is None:
            return False

        return (
            now_utc
            - timedelta(hours=4)
            <= event_date
            <= now_utc
            + timedelta(days=7)
        )

    return False


def _time_window(
    item: dict[str, Any],
    notice_type: str,
) -> str:
    """
    Produce concise date/time text for an operational notice.
    """

    event_date = _item_datetime(
        item,
        "event",
    )

    if event_date is not None:

        if notice_type in {
            "Sport",
            "Music",
        }:

            return event_date.strftime(
                "%d %b %Y, %H:%M"
            )

        return event_date.strftime(
            "%d %b %Y"
        )

    return str(
        item.get(
            "published_display"
        )
        or item.get(
            "published"
        )
        or "Current"
    )


def _notice_status(
    item: dict[str, Any],
    notice_type: str,
    now_utc: datetime,
) -> str:
    """
    Label an operational notice Active or Upcoming.
    """

    event_date = _item_datetime(
        item,
        "event",
    )

    if notice_type in {
        "Sport",
        "Music",
    }:
        return "Upcoming"

    if (
        event_date is not None
        and event_date
        > now_utc
        + timedelta(hours=2)
    ):
        return "Upcoming"

    return "Active"


def _suggested_action(
    notice_type: str,
) -> str:
    """
    Provide short business-travel advice for each notice type.
    """

    if notice_type == "Demonstration":

        return (
            "Avoid the affected area, "
            "confirm meeting access and "
            "allow additional travel time."
        )

    if notice_type == "Road closure":

        return (
            "Check the route before departure "
            "and allow additional journey time."
        )

    if notice_type == "Sport":

        return (
            "Expect congestion around the venue "
            "and major approach roads. Avoid "
            "time-critical vehicle movements "
            "close to the event."
        )

    if notice_type == "Music":

        return (
            "Expect heavier traffic and transport "
            "demand near the venue. Allow extra "
            "journey time and pre-book transport "
            "where practical."
        )

    return (
        "Check the latest local "
        "conditions before travel."
    )


def _build_incidents(
    items: list[dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    """
    Build the selective Active Operational Notices feed.
    """

    now_utc = (
        _parse_datetime(
            generated_at
        )
        or datetime.now(
            timezone.utc
        )
    )

    eligible = [
        item
        for item in items
        if _is_current_operational_item(
            item,
            now_utc,
        )
    ]

    def rank(
        item: dict[str, Any],
    ) -> tuple[int, int, float]:

        notice_type = (
            _operational_type(item)
            or ""
        )

        type_priority = {
            "Road closure": 4,
            "Demonstration": 3,
            "Sport": 2,
            "Music": 1,
        }.get(
            notice_type,
            0,
        )

        impact = _safe_int(
            item.get(
                "business_impact_score"
            )
        )

        event_date = _item_datetime(
            item,
            "event",
        )

        if event_date is None:

            event_date = _item_datetime(
                item,
                "published",
            )

        if event_date is None:

            event_date = datetime(
                1970,
                1,
                1,
                tzinfo=timezone.utc,
            )

        return (
            type_priority,
            impact,
            event_date.timestamp(),
        )

    ranked_items = sorted(
        eligible,
        key=rank,
        reverse=True,
    )

    incidents: list[
        dict[str, Any]
    ] = []

    for item in ranked_items[:8]:

        notice_type = (
            _operational_type(item)
        )

        if notice_type is None:
            continue

        score = _safe_int(
            item.get(
                "business_impact_score"
            )
        )

        summary = str(
            item.get("summary")
            or ""
        ).strip()

        if len(summary) > 300:

            summary = (
                summary[:297].rstrip()
                + "..."
            )

        incidents.append(
            {
                "title": item.get(
                    "title",
                    "Operational notice",
                ),
                "location": item.get(
                    "location",
                    "National",
                ),
                "type": notice_type,
                "severity": (
                    _severity_level(
                        score
                    )
                ),
                "status": (
                    _notice_status(
                        item,
                        notice_type,
                        now_utc,
                    )
                ),
                "time_window": (
                    _time_window(
                        item,
                        notice_type,
                    )
                ),
                "summary": (
                    summary
                    or (
                        "No additional "
                        "detail available."
                    )
                ),
                "action": (
                    _suggested_action(
                        notice_type
                    )
                ),
                "confidence": item.get(
                    "confidence",
                    "Reported",
                ),
                "source": item.get(
                    "source",
                    "Unknown source",
                ),
                "url": item.get(
                    "url",
                    "",
                ),
                "business_impact_score": (
                    score
                ),
            }
        )

    return incidents


def _build_news(
    items: list[dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    """
    Build a much tighter general-intelligence feed.

    Rules:
    - FCDO advice is excluded because it has its own section.
    - Items must have a publication date.
    - Items older than 48 hours are excluded.
    - Unclassified / entertainment / generic sports stories are excluded.
    - Weakly relevant material is excluded.
    - Maximum ten stories.
    """

    now_utc = (
        _parse_datetime(
            generated_at
        )
        or datetime.now(
            timezone.utc
        )
    )

    news: list[
        dict[str, Any]
    ] = []

    for item in items:

        if _is_fcdo_item(item):
            continue

        published = _item_datetime(
            item,
            "published",
        )

        if published is None:
            continue

        if (
            published
            < now_utc
            - timedelta(hours=48)
        ):
            continue

        impact = _safe_int(
            item.get(
                "business_impact_score"
            )
        )

        relevance = _safe_int(
            item.get(
                "relevance_score"
            )
        )

        category = _normalise_category(
            item.get("category")
        )

        if category in {
            "unclassified news",
            "entertainment",
            "sport",
        }:
            continue

        if (
            impact < 35
            and relevance < 55
        ):
            continue

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
                    "Business intelligence",
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
                    impact
                ),
            }
        )

    news.sort(
        key=lambda story: (
            story[
                "business_impact_score"
            ]
        ),
        reverse=True,
    )

    return news[:10]


def _build_timeline(
    national_score: int,
    national_summary: str,
    generated_at: str,
) -> list[dict[str, Any]]:
    """
    Create the current timeline point.

    A complete historical timeline can later use the planned
    historical intelligence database.
    """

    try:

        parsed_date = (
            datetime.fromisoformat(
                generated_at
            )
        )

        display_date = (
            parsed_date.strftime(
                "%d %b"
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        display_date = (
            datetime.now().strftime(
                "%d %b"
            )
        )

    return [
        {
            "date": display_date,
            "score": national_score,
            "explanation": (
                national_summary
            ),
        }
    ]



def _build_daily_language_brief(
    generated_at: str,
) -> dict[str, Any]:
    """
    Select one curated Afrikaans entry and one curated isiXhosa entry.

    Selection is deterministic: the same briefing date always produces the
    same pair, while the pair advances automatically when the date changes.
    No external API or manual daily edit is required.
    """

    briefing_datetime = _parse_datetime(
        generated_at
    )

    if briefing_datetime is None:
        briefing_datetime = datetime.now(
            timezone.utc
        )

    briefing_date = briefing_datetime.date()
    day_number = briefing_date.toordinal()

    afrikaans_index = (
        day_number
        % len(AFRIKAANS_BUSINESS_LANGUAGE)
    )

    isixhosa_index = (
        (day_number * 7)
        % len(ISIXHOSA_BUSINESS_LANGUAGE)
    )

    return {
        "date": briefing_date.isoformat(),
        "afrikaans": dict(
            AFRIKAANS_BUSINESS_LANGUAGE[
                afrikaans_index
            ]
        ),
        "isixhosa": dict(
            ISIXHOSA_BUSINESS_LANGUAGE[
                isixhosa_index
            ]
        ),
        "rotation": "daily",
        "source_type": "curated",
    }

def _build_conversation_brief(
) -> list[dict[str, str]]:
    """
    Provide neutral business-conversation guidance.
    """

    return [
        {
            "topic": (
                "Business climate"
            ),
            "heading": (
                "Discussing current "
                "operating conditions"
            ),
            "context": (
                "Economic and infrastructure "
                "conditions can affect industries "
                "and locations differently."
            ),
            "starter": (
                "How are current operating "
                "conditions affecting businesses "
                "in your sector?"
            ),
            "avoid": (
                "Assuming every company or "
                "region is experiencing the "
                "same conditions."
            ),
        },
        {
            "topic": (
                "Infrastructure"
            ),
            "heading": (
                "Discussing practical "
                "disruption"
            ),
            "context": (
                "Service disruption can be "
                "discussed through its business "
                "effects rather than political "
                "blame."
            ),
            "starter": (
                "Have recent infrastructure "
                "conditions changed how your "
                "organisation plans day-to-day "
                "operations?"
            ),
            "avoid": (
                "Assuming who the other person "
                "blames for a local service "
                "problem."
            ),
        },
        {
            "topic": (
                "Current affairs"
            ),
            "heading": (
                "Approaching sensitive "
                "developments"
            ),
            "context": (
                "Political and social issues "
                "may be strongly felt, so neutral "
                "and open questions are safer."
            ),
            "starter": (
                "Which recent developments are "
                "having the greatest effect on "
                "your industry?"
            ),
            "avoid": (
                "Assuming a person's political "
                "affiliation or view on a "
                "controversial issue."
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

    metadata[
        "data_status"
    ] = "live intelligence"

    items = backend_output.get(
        "items",
        [],
    )

    if not isinstance(
        items,
        list,
    ):
        items = []

    national_risk = (
        backend_output.get(
            "national_risk",
            {},
        )
    )

    national_score = (
        _safe_int(
            national_risk.get(
                "score"
            )
        )
    )

    national_level = str(
        national_risk.get(
            "level",
            _risk_level(
                national_score
            ),
        )
    )

    national_summary = str(
        national_risk.get(
            "summary",
            (
                f"{national_level} "
                "national business risk "
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

    analysis_items = (
        _analysis_items(
            items
        )
    )

    return {
        "metadata": metadata,

        "national": {
            "score": (
                national_score
            ),
            "level": (
                national_level
            ),
            "seven_day_change": 0,
            "summary": (
                national_summary
            ),
            "components": (
                _build_components(
                    analysis_items
                )
            ),
        },

        "timeline": (
            _build_timeline(
                national_score=(
                    national_score
                ),
                national_summary=(
                    national_summary
                ),
                generated_at=(
                    generated_at
                ),
            )
        ),

        "cities": (
            _build_cities(
                items=analysis_items,
                national_score=(
                    national_score
                ),
            )
        ),

        "travel_advice": (
            _build_travel_advice(
                items=items,
                generated_at=(
                    generated_at
                ),
            )
        ),

        "incidents": (
            _build_incidents(
                items=analysis_items,
                generated_at=(
                    generated_at
                ),
            )
        ),

        "news": (
            _build_news(
                items=analysis_items,
                generated_at=(
                    generated_at
                ),
            )
        ),

        "daily_language_brief": (
            _build_daily_language_brief(
                generated_at=(
                    generated_at
                ),
            )
        ),

        "conversation_brief": (
            _build_conversation_brief()
        ),
    }