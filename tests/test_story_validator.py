from pm_agent.validation.story_validator import validate_stories


def _valid_story(**overrides):
    story = {
        "internal_id": "story-001",
        "title": "Create task",
        "description": "Allow users to create a task.",
        "acceptance_criteria": ["A user can create a task."],
        "story_points": 3,
        "priority": "must-have",
    }
    story.update(overrides)
    return story


def test_valid_story_passes():
    is_valid, errors = validate_stories([_valid_story()])

    assert is_valid is True
    assert errors == []


def test_title_must_be_between_5_and_100_chars():
    is_valid, errors = validate_stories([_valid_story(title="Bad")])

    assert is_valid is False
    assert any("title" in error for error in errors)


def test_description_must_be_non_empty():
    is_valid, errors = validate_stories([_valid_story(description="")])

    assert is_valid is False
    assert any("description" in error for error in errors)


def test_acceptance_criteria_requires_at_least_one_item():
    is_valid, errors = validate_stories([_valid_story(acceptance_criteria=[])])

    assert is_valid is False
    assert any("acceptance_criteria" in error for error in errors)


def test_story_points_must_be_allowed_int():
    is_valid, errors = validate_stories([_valid_story(story_points=4)])

    assert is_valid is False
    assert any("story_points" in error for error in errors)


def test_internal_id_must_be_unique():
    is_valid, errors = validate_stories([
        _valid_story(internal_id="story-001"),
        _valid_story(internal_id="story-001", title="Update task"),
    ])

    assert is_valid is False
    assert any("duplicated" in error for error in errors)

