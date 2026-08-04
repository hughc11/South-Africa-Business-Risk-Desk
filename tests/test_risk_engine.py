"""
Test the National Risk Engine using data/briefing_test.json.
"""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from intelligence.risk_engine import calculate_national_risk


DATA_FILE = PROJECT_ROOT / "data" / "briefing_test.json"


def main() -> None:
    """
    Load the current test briefing and display the risk result.
    """

    if not DATA_FILE.exists():
        print(
            "Test failed: data/briefing_test.json "
            "could not be found."
        )
        return

    try:
        data = json.loads(
            DATA_FILE.read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError as exc:
        print(
            "Test failed: briefing_test.json "
            f"is not valid JSON. Error: {exc}"
        )
        return

    items = data.get("items", [])

    if not isinstance(items, list):
        print(
            "Test failed: the 'items' section "
            "is not a list."
        )
        return

    result = calculate_national_risk(
        items
    )

    print("=" * 68)
    print("NATIONAL RISK ENGINE TEST")
    print("=" * 68)

    print(
        f"Stories assessed: "
        f"{result['story_count']}"
    )

    print(
        f"National risk score: "
        f"{result['score']}/100"
    )

    print(
        f"National risk level: "
        f"{result['level']}"
    )

    print(
        f"Summary: "
        f"{result['summary']}"
    )

    print("\nTop five risk drivers:")

    drivers = result.get(
        "primary_drivers",
        [],
    )

    if not drivers:
        print(
            "No risk drivers were identified."
        )

    for position, driver in enumerate(
        drivers,
        start=1,
    ):
        print(
            f"{position}. "
            f"{driver.get('title', 'Untitled story')}"
        )

        print(
            f"   Category: "
            f"{driver.get('category', 'Unclassified')}"
        )

        print(
            f"   Location: "
            f"{driver.get('location', 'National')}"
        )

        print(
            f"   Business impact: "
            f"{driver.get('business_impact_score', 0)}/100"
        )

    print("\nTest completed successfully.")


if __name__ == "__main__":
    main()