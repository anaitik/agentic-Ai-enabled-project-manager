"""Structured JSONL logging for tracking decisions."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_LOG_PATH = "tracking_matches.jsonl"


def log_match_attempt(
    message: str,
    matched_story_key: str | None,
    score: float,
    chosen_path: str,
    final_action: str,
) -> None:
    """Append one tracking decision event as a JSON line."""

    log_path = Path(os.getenv("TRACKING_LOG_PATH", DEFAULT_LOG_PATH))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "message": message,
        "matched_story_key": matched_story_key,
        "score": score,
        "chosen_path": chosen_path,
        "final_action": final_action,
    }
    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")

