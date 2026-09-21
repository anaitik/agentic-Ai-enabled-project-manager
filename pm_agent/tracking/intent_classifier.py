"""Cheap intent classifier for developer chat messages."""

from pm_agent.llm import get_llm


VALID_INTENTS = {"status_update", "blocker", "question", "other"}

INTENT_PROMPT = """Classify the developer message into exactly one intent.

Return only one of these strings:
status_update
blocker
question
other

Definitions:
- status_update: progress update about work started, in progress, in review, completed, or ready.
- blocker: the developer is blocked, stuck, or waiting on something.
- question: the developer asks for information or clarification.
- other: anything else.
"""


def classify_intent(message: str) -> str:
    """Classify a developer message before story matching."""

    llm = get_llm()
    response = llm.invoke(
        [
            {"role": "system", "content": INTENT_PROMPT},
            {"role": "user", "content": message},
        ]
    )
    intent = str(getattr(response, "content", response)).strip().lower()
    return intent if intent in VALID_INTENTS else "other"

