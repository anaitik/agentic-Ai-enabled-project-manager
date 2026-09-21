"""Print available Jira workflow transitions for a project."""

import argparse
import json

from pm_agent.tools.jira_tools import get_workflow_transitions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect runtime Jira transitions for a project key."
    )
    parser.add_argument("project_key", help="Jira project key, such as PROJ")
    args = parser.parse_args()

    transitions = get_workflow_transitions(args.project_key)
    print(json.dumps(transitions, indent=2))


if __name__ == "__main__":
    main()
