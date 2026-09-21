"""Pure Python validation for generated stories."""


ALLOWED_STORY_POINTS = {1, 2, 3, 5, 8, 13}


def validate_stories(stories: list[dict]) -> tuple[bool, list[str]]:
    """Validate generated stories without using an LLM."""

    errors = []
    seen_internal_ids = set()

    for index, story in enumerate(stories):
        label = f"story[{index}]"

        internal_id = story.get("internal_id")
        if not isinstance(internal_id, str) or not internal_id.strip():
            errors.append(f"{label}.internal_id must be a non-empty string.")
        elif internal_id in seen_internal_ids:
            errors.append(f"{label}.internal_id '{internal_id}' is duplicated.")
        else:
            seen_internal_ids.add(internal_id)

        title = story.get("title")
        if not isinstance(title, str) or not 5 <= len(title.strip()) <= 100:
            errors.append(f"{label}.title must be between 5 and 100 characters.")

        description = story.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{label}.description must be non-empty.")

        acceptance_criteria = story.get("acceptance_criteria")
        if (
            not isinstance(acceptance_criteria, list)
            or not acceptance_criteria
            or not all(isinstance(item, str) and item.strip() for item in acceptance_criteria)
        ):
            errors.append(
                f"{label}.acceptance_criteria must contain at least one non-empty string."
            )

        story_points = story.get("story_points")
        if not isinstance(story_points, int) or story_points not in ALLOWED_STORY_POINTS:
            errors.append(
                f"{label}.story_points must be an int in {sorted(ALLOWED_STORY_POINTS)}."
            )

    return not errors, errors

