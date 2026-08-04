import json


with open(
    "data/briefing_test.json",
    "r",
    encoding="utf-8",
) as file:
    data = json.load(file)


for number, item in enumerate(
    data["items"][:20],
    start=1,
):
    location = item.get(
        "location",
        "Unknown location",
    )

    category = item.get(
        "category",
        "Unknown category",
    )

    title = item.get(
        "title",
        "Untitled",
    )

    print(
        f"{number}. "
        f"[{location}] "
        f"[{category}] "
        f"{title}"
    )