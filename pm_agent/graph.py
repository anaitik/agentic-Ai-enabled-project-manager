"""LangGraph graph assembly for the project manager agent."""

from langgraph.graph import END, START, StateGraph

from pm_agent.nodes import (
    provisioning_node,
    scoping_node,
    story_gen_node,
    tracking_node,
)
from pm_agent.state import PMAgentState


def _route_after_scoping(state: PMAgentState) -> str:
    if state["scope_approved"]:
        return "provisioning"
    return "scoping"


def build_graph():
    """Build and compile the project manager agent graph."""

    graph = StateGraph(PMAgentState)

    graph.add_node("scoping", scoping_node)
    graph.add_node("provisioning", provisioning_node)
    graph.add_node("story_gen", story_gen_node)
    graph.add_node("tracking", tracking_node)

    graph.add_edge(START, "scoping")
    graph.add_conditional_edges(
        "scoping",
        _route_after_scoping,
        {
            "scoping": "scoping",
            "provisioning": "provisioning",
        },
    )
    graph.add_edge("provisioning", "story_gen")
    graph.add_edge("story_gen", "tracking")
    graph.add_edge("tracking", END)

    return graph.compile()


app = build_graph()
