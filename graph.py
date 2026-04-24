from langgraph.graph import StateGraph, END
from state import NewsState
from agents import (
    fetch_agent, dedup_agent, summarize_agent,
    cross_source_verifier_agent, credibility_scorer_agent,
    bias_detector_agent, ai_detector_agent,
    verdict_agent, present_agent
)

def build_graph():
    graph = StateGraph(NewsState)

    graph.add_node("fetch", fetch_agent)
    graph.add_node("deduplicate", dedup_agent)
    graph.add_node("summarize", summarize_agent)
    graph.add_node("cross_verify", cross_source_verifier_agent)
    graph.add_node("credibility", credibility_scorer_agent)
    graph.add_node("bias", bias_detector_agent)
    graph.add_node("ai_detect", ai_detector_agent)
    graph.add_node("verdict", verdict_agent)
    graph.add_node("present", present_agent)

    graph.set_entry_point("fetch")
    graph.add_edge("fetch", "deduplicate")
    graph.add_edge("deduplicate", "summarize")
    graph.add_edge("summarize", "cross_verify")
    graph.add_edge("cross_verify", "credibility")
    graph.add_edge("credibility", "bias")
    graph.add_edge("bias", "ai_detect")
    graph.add_edge("ai_detect", "verdict")
    graph.add_edge("verdict", "present")
    graph.add_edge("present", END)

    return graph.compile()

news_graph = build_graph()
