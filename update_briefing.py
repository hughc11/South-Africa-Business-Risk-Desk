from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from collectors.gov_uk import collect_fcdo_advice
from collectors.news_search import collect_news_searches
from collectors.sa_government import collect_sa_government_news
from collectors.traffic import collect_i_traffic
from intelligence.business_impact import apply_business_impact
from intelligence.classify import classify_items
from intelligence.deduplicate import deduplicate_items
from intelligence.normalise import normalise_items
from intelligence.output_formatter import format_dashboard_output
from intelligence.risk_engine import calculate_national_risk
from settings import PROJECT_NAME, TIMEZONE


LIVE_OUTPUT_FILE = "data/briefing.json"


def run_collector(
    label: str,
    collector: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Run one collector safely.

    If one collector fails, the rest of the engine continues.
    """

    print(f"\nCollecting: {label}")

    try:
        items = collector()

        print(
            f"Collected {len(items)} item(s) "
            f"from {label}."
        )

        return items, {
            "status": "success",
            "item_count": len(items),
        }

    except Exception as exc:
        print(
            f"Collector failed safely: "
            f"{label}. Error: {exc}"
        )

        return [], {
            "status": "failed",
            "item_count": 0,
            "error": str(exc),
        }


def sort_items(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Sort the most business-relevant items first.
    """

    return sorted(
        items,
        key=lambda item: (
            int(item.get("business_impact_score") or 0),
            int(item.get("relevance_score") or 0),
            str(item.get("published_timestamp") or ""),
        ),
        reverse=True,
    )


def write_output(
    output: dict[str, Any],
    output_file: str,
) -> None:
    """
    Save formatted dashboard data as JSON.
    """

    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def main() -> None:
    """
    Run the complete intelligence pipeline and update the live dashboard file.
    """

    print("=" * 68)
    print(PROJECT_NAME)
    print("Live intelligence update")
    print("=" * 68)

    collectors = [
        (
            "FCDO travel advice",
            collect_fcdo_advice,
        ),
        (
            "South African Government",
            collect_sa_government_news,
        ),
        (
            "National and city news",
            collect_news_searches,
        ),
        (
            "i-TRAFFIC",
            collect_i_traffic,
        ),
    ]

    all_items: list[dict[str, Any]] = []
    collector_results: dict[str, Any] = {}

    for label, collector in collectors:
        items, result = run_collector(
            label,
            collector,
        )

        all_items.extend(items)
        collector_results[label] = result

    print(
        f"\nRaw total collected: "
        f"{len(all_items)}"
    )

    normalised_items = normalise_items(
        all_items
    )

    print(
        f"After normalising: "
        f"{len(normalised_items)}"
    )

    deduplicated_items = deduplicate_items(
        normalised_items
    )

    print(
        f"After deduplication: "
        f"{len(deduplicated_items)}"
    )

    classified_items = classify_items(
        deduplicated_items
    )

    business_scored_items = apply_business_impact(
        classified_items
    )

    print(
        f"After business impact scoring: "
        f"{len(business_scored_items)}"
    )

    final_items = sort_items(
        business_scored_items
    )

    national_risk = calculate_national_risk(
        final_items
    )

    try:
        local_now = datetime.now(
            ZoneInfo(TIMEZONE)
        )
    except Exception:
        local_now = datetime.now()

    backend_output = {
        "metadata": {
            "project": PROJECT_NAME,
            "data_status": "live intelligence",
            "generated_at": local_now.isoformat(),
            "generated_display": local_now.strftime(
                "%d %b %Y, %H:%M"
            ),
            "timezone": TIMEZONE,
            "raw_item_count": len(all_items),
            "normalised_item_count": len(
                normalised_items
            ),
            "final_item_count": len(
                final_items
            ),
            "collector_results": collector_results,
        },
        "national_risk": national_risk,
        "items": final_items,
    }

    dashboard_output = format_dashboard_output(
        backend_output
    )

    write_output(
        dashboard_output,
        LIVE_OUTPUT_FILE,
    )

    print(
        f"\nLive dashboard data written to: "
        f"{LIVE_OUTPUT_FILE}"
    )

    print(
        f"National risk score: "
        f"{dashboard_output['national']['score']}/100"
    )

    print(
        f"Generated date: "
        f"{dashboard_output['metadata']['generated_display']}"
    )


if __name__ == "__main__":
    main()
