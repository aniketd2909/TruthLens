from langgraph.graph import StateGraph, END
from state import NewsState
from agents import fetch_agent, dedup_agent, summarize_agent, present_agent

def build_graph():
    graph = StateGraph(NewsState)

    # Add nodes
    graph.add_node("fetch", fetch_agent)
    graph.add_node("deduplicate", dedup_agent)
    graph.add_node("summarize", summarize_agent)
    graph.add_node("present", present_agent)

    # Add edges (flow)
    graph.set_entry_point("fetch")
    graph.add_edge("fetch", "deduplicate")
    graph.add_edge("deduplicate", "summarize")
    graph.add_edge("summarize", "present")
    graph.add_edge("present", END)

    return graph.compile()

news_graph = build_graph()