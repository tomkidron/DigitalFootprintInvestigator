"""LangGraph workflow definition"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from graph.nodes.advanced import advanced_analysis_node
from graph.nodes.analysis import analysis_node
from graph.nodes.report import report_node
from graph.nodes.search import google_node, social_node
from graph.state import OSINTState


def should_run_advanced_analysis(state: OSINTState) -> str:
    """Conditional routing for advanced analysis"""
    config = state.get("config", {})
    advanced = config.get("advanced_analysis", {})

    if any(advanced.values()):
        return "advanced_analysis"
    return "report"


def create_workflow():
    """Create OSINT investigation workflow with parallel execution"""
    workflow = StateGraph(OSINTState)

    workflow.add_node("google_search", google_node)
    workflow.add_node("social_search", social_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("advanced_analysis", advanced_analysis_node)
    workflow.add_node("report", report_node)

    # Parallel fan-out from START
    workflow.add_edge(START, "google_search")
    workflow.add_edge(START, "social_search")

    # Both searches converge to analysis
    workflow.add_edge("google_search", "analysis")
    workflow.add_edge("social_search", "analysis")

    # Conditional routing after analysis
    workflow.add_conditional_edges(
        "analysis", should_run_advanced_analysis, {"advanced_analysis": "advanced_analysis", "report": "report"}
    )

    workflow.add_edge("advanced_analysis", "report")
    workflow.add_edge("report", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
