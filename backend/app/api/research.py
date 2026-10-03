from fastapi import APIRouter, HTTPException

from backend.app.agents.research_agent import run_research_agent
from backend.app.graph.research_graph import research_graph
from backend.app.models.research import (
    ResearchAgentRequest,
    ResearchAgentResponse,
    ResearchGraphRequest,
    ResearchGraphResponse,
    ResearchTestRequest,
    ResearchTestResponse,
)
from backend.app.services.llm import generate_research_response

#  Create a router; APIRouter is a class provided by FastAPI. 
# This creates a router object
# Think of router as an empty reception desk
router = APIRouter() 


# Register an address on that router
# it tells the router: If someone sends a POST request to /research/test, 
# use the function immediately below me.
@router.post(
    "/research/test",                    # INPUT ADDRESS
    response_model=ResearchTestResponse  # OUTPUT FORMAT
)
##Attach a Python function to that address 
async def test_research(request: ResearchTestRequest) -> ResearchTestResponse:
#Define an asynchronous function called test_research.
#It receives a variable called request, which should be a ResearchTestRequest.
#It returns a ResearchTestResponse.
    try:
        response = await generate_research_response(request.brief)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="LLM service unavailable",
        ) from exc

    return ResearchTestResponse(brief=request.brief, response=response)


@router.post("/research/graph", response_model=ResearchGraphResponse)
async def run_research_graph(
    request: ResearchGraphRequest,
) -> ResearchGraphResponse:
    initial_state = {
        "brief": request.brief,
        "plan": "",
        "research": "",
        "status": "",
    }

    try:
        final_state = await research_graph.ainvoke(initial_state)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Research workflow unavailable",
        ) from exc

    return ResearchGraphResponse(
        brief=final_state["brief"],
        plan=final_state["plan"],
        research=final_state["research"],
        status=final_state["status"],
    )


@router.post("/research/agent", response_model=ResearchAgentResponse)
async def run_research_agent_endpoint(
    request: ResearchAgentRequest,
) -> ResearchAgentResponse:
    try:
        response = await run_research_agent(request.brief)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Research agent unavailable",
        ) from exc

    return ResearchAgentResponse(brief=request.brief, response=response)