from langgraph.graph import END, START, StateGraph

from backend.app.graph.nodes import complete_node, planner_node, researcher_node
from backend.app.graph.state import ResearchState


builder = StateGraph(ResearchState)
builder.add_node("planner", planner_node)
builder.add_node("researcher", researcher_node)
builder.add_node("complete", complete_node)

builder.add_edge(START, "planner")
builder.add_edge("planner", "researcher")
builder.add_edge("researcher", "complete")
builder.add_edge("complete", END)

research_graph = builder.compile()