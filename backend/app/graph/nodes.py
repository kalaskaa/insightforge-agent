from backend.app.graph.state import ResearchState
from backend.app.services.llm import generate_research_response


async def planner_node(state: ResearchState) -> dict[str, str]:
    plan = (
        "Research the market context and key competitive factors for: "
        f"{state['brief']}"
    )
    return {"plan": plan}


async def researcher_node(state: ResearchState) -> dict[str, str]:
    research = await generate_research_response(state["brief"])
    return {"research": research}


async def complete_node(state: ResearchState) -> dict[str, str]:
    return {"status": "complete"}