"""Terminal approval helpers."""

import json


def request_approval(stories: list[dict]) -> bool:
    """Pretty-print stories and ask for terminal approval."""

    print("\nGenerated stories:")
    print(json.dumps(stories, indent=2))

    while True:
        answer = input("\nCreate these stories in Jira? [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer y or n.")
