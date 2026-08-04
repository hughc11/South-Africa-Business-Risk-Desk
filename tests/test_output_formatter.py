"""
Test the website Output Formatter.

This reads data/briefing_test.json and creates
data/briefing_dashboard_test.json without changing the live website file.
"""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from intelligence.output_formatter import format_dashboard_output


INPUT_FILE = PROJECT_ROOT / "data" / "briefing_test.json"
OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "briefing_dashboard_test.json"
)


def main() -> None:
    """
    Format the backend test output for the website.
    """

    if not INPUT_FILE.exists():
        print(
            "Test failed: data/briefing_test.json "
            "could not be found."
        )
        return

    try:
        backend_output = json.loads(
            INPUT_FILE.read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError as exc:
        print(
            "Test failed: briefing_test.json "
            f"is not valid JSON. Error: {exc}"
        )
        return

    dashboard_output = format_dashboard_output(
        backend_output
    )

    required_sections = [
        "metadata",
        "national",
        "timeline",
        "cities",
        "incidents",
        "news",
        "conversation_brief",
    ]

    missing_sections = [
        section
        for section in required_sections
        if section not in dashboard_output
    ]

    if missing_sections:
        print(
            "Test failed. Missing sections: "
            + ", ".join(missing_sections)
        )
        return

    OUTPUT_FILE.write_text(
        json.dumps(
            dashboard_output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("=" * 68)
    print("OUTPUT FORMATTER TEST")
    print("=" * 68)

    print(
        f"National score: "
        f"{dashboard_output['national']['score']}/100"
    )

    print(
        f"National level: "
        f"{dashboard_output['national']['level']}"
    )

    print(
        f"Cities created: "
        f"{len(dashboard_output['cities'])}"
    )

    print(
        f"Incidents created: "
        f"{len(dashboard_output['incidents'])}"
    )

    print(
        f"News stories created: "
        f"{len(dashboard_output['news'])}"
    )

    print(
        f"Output written to: "
        f"{OUTPUT_FILE}"
    )

    print(
        "\nTest completed successfully."
    )


if __name__ == "__main__":
    main()