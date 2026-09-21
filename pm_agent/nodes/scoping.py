"""Scoping node for collecting and approving project scope."""

import json
import logging
import re

from pm_agent.llm import get_llm
from pm_agent.prompts.scoping_prompt import SCOPING_SYSTEM_PROMPT
from pm_agent.state import PMAgentState


logger = logging.getLogger(__name__)

FEATURE_LIST_PATTERN = re.compile(
    r"<feature_list>\s*(?P<json>.*?)\s*</feature_list>",
    re.DOTALL,
)


def _response_content(response: object) -> str:
    """Return text content from a LangChain response or a plain string."""

    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    return str(content)


def _messages_from_state(state: PMAgentState) -> list[dict]:
    return [
        {"role": "system", "content": SCOPING_SYSTEM_PROMPT},
        *state["conversation_history"],
    ]


def scoping_node(state: PMAgentState) -> PMAgentState:
    """Run the scoping conversation and update scope if a feature block appears."""

    llm = get_llm()
    response = llm.invoke(_messages_from_state(state))
    assistant_response = _response_content(response)

    updated_state: PMAgentState = {
        **state,
        "conversation_history": [
            *state["conversation_history"],
            {"role": "assistant", "content": assistant_response},
        ],
    }

    match = FEATURE_LIST_PATTERN.search(assistant_response)
    if not match:
        return updated_state

    try:
        parsed = json.loads(match.group("json"))
    except json.JSONDecodeError:
        logger.warning("Failed to parse <feature_list> JSON from scoping response.")
        return updated_state

    if "features" in parsed:
        updated_state["proposed_features"] = parsed["features"]
    if "scope_approved" in parsed:
        updated_state["scope_approved"] = parsed["scope_approved"]

    return updated_state
