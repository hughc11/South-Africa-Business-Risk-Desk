from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from collectors.gov_uk import collect_fcdo_advice
from collectors.news_search import collect_news_searches
from collectors.sa_government import collect_sa_government_news
from collectors.traffic import collect_i_traffic
from intelligence.classify import classify_items
from intelligence.deduplicate import deduplicate_items
from intelligence.normalise import normalise_items
from settings import OUTPUT_FILE, PROJECT_NAME, TIMEZONE


def run_collector(
    label: str,
    collector: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Run one collector safely.

    If the collector fails, the rest of the engine continues.
    """

    print(f"\nCollecting: {label}")

    try:
        items = collector()

        print(
            f"Collected {len(items)} item(s) "
            f"from {label}."
        )

        result = {
            "status": "success",
            "item_count": len(items),
        }

        return items, result

    except Exception as exc:
        print(
            f"Collector failed safely: "
            f"{label}. Error: {exc}"
        )

        result = {
            "status": "failed",
            "item_count": 0,
            "error": str(exc),
        }

        return [], result


def sort_items(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Sort the newest and most relevant items first.
    """

    return sorted(
        items,
        key=lambda item: (
            str(
                item.get("published_timestamp")
                or ""
            ),
            int(
                item.get("relevance_score")
                or 0
            ),
        ),
        reverse=True,
    )


def write_output(
    output: dict[str, Any],
) -> None:
    """
    Save the collection result as formatted JSON.
    """

    output_path = Path(OUTPUT_FILE)

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
    Run the complete first-stage collection engine.
    """

    print("=" * 68)
    print(PROJECT_NAME)
    print("Collection engine test run")
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

    final_items = sort_items(
        classified_items
    )

    london_now = datetime.now()
    

    output = {
        "metadata": {
            "project": PROJECT_NAME,
            "data_status": "collection-engine test",
            "generated_at": london_now.isoformat(),
            "generated_display": london_now.strftime(
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
            "collector_results": (
                collector_results
            ),
        },
        "items": final_items,
    }

    write_output(output)

    print(
        f"\nTest output written to: "
        f"{OUTPUT_FILE}"
    )

    print(
        "\nThe live file data/briefing.json "
        "was not changed."
    )


if __name__ == "__main__":
    main()