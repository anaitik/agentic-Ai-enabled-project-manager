"""Match developer messages to assigned open stories with local embeddings."""

import math
from functools import lru_cache

from pm_agent.state import PMAgentState


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def _embed_text(text: str) -> list[float]:
    embedding = _get_embedding_model().encode(text, normalize_embeddings=True)
    return [float(value) for value in embedding]


def match_story(
    message: str,
    developer_id: str,
    state: PMAgentState,
) -> tuple[dict | None, float]:
    """Return the best matching non-done story assigned to the developer."""

    candidates = [
        story
        for story in state["stories"]
        if story.get("assignee") == developer_id and story.get("status") != "done"
    ]
    if not candidates:
        return None, 0.0

    message_embedding = _embed_text(message)
    story_embeddings = state.setdefault("story_embeddings", {})

    best_story = None
    best_score = 0.0

    for story in candidates:
        cache_key = _story_cache_key(story)
        story_embedding = story_embeddings.get(cache_key)
        if story_embedding is None:
            story_embedding = _embed_text(_story_text(story))
            story_embeddings[cache_key] = story_embedding

        score = _cosine_similarity(message_embedding, story_embedding)
        if score > best_score:
            best_story = story
            best_score = score

    return best_story, best_score


def _story_cache_key(story: dict) -> str:
    return str(story.get("jira_issue_key") or story.get("internal_id"))


def _story_text(story: dict) -> str:
    return f"{story.get('title', '')}\n{story.get('description', '')}"


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)

