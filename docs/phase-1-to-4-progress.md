# InsightForge — Phase 1 to Phase 4 Progress Report

## 1. Project Objective

InsightForge is being built incrementally as an Autonomous Market Intelligence and Agentic AI research application. The goal is to learn how a research application can receive a question, use language models and tools, and gradually grow into a more complete research workflow.

The project is deliberately divided into small phases so each concept can be understood before the next is introduced. The current implementation covers a FastAPI foundation, a direct LLM call, a developer-defined LangGraph workflow, and a first tool-calling agent. DeepAgents, richer research sources, RAG, vector databases, a frontend, Docker, and AWS deployment are future learning topics, not current features.

## 2. Current Technology Stack

These technologies are present in the project configuration or lockfile:

| Technology | Role in InsightForge |
| --- | --- |
| Python 3.12 | The language and supported runtime for the backend. |
| uv | Installs and runs the project environment and commands. |
| FastAPI | Defines the HTTP application and API endpoints. |
| Uvicorn | Runs the FastAPI application as an ASGI server. |
| Pydantic | Defines request and response data models and validates incoming briefs. |
| pydantic-settings | Loads application settings, including the Groq key and model, from the root `.env`. |
| LangChain | Provides the LLM integration and application building blocks. |
| langchain-core | Provides shared message and tool abstractions used by the agent. It is present through the locked LangChain dependencies. |
| langchain-groq | Connects LangChain's `ChatGroq` model to Groq. |
| LangGraph | Builds and runs the Phase 3 state-based workflow. |
| Groq | The configured LLM provider used by `ChatGroq`. |
| `openai/gpt-oss-20b` | The configured model name in settings and `.env.example`; it is used through Groq. |
| pytest | Runs the automated test suite. |
| HTTPX | Supports FastAPI's test client in the development dependencies. |
| python-dotenv | Supports loading `.env` configuration. |

The repository declares dependencies in `pyproject.toml` and locks resolved packages in `uv.lock`. The Groq API key is read from the local root `.env`; it is not stored in source code.

## 3. Phase 1 — FastAPI Foundation

Phase 1 established the backend skeleton:

- `backend/app/main.py` creates the application with `app = FastAPI(...)`.
- The health router in `backend/app/api/health.py` is an `APIRouter` with `GET /health`.
- `main.py` imports the router and registers it with `app.include_router(health_router)`.
- `backend/app/config.py` defines the Pydantic `Settings` class and loads the root `.env` file.
- `backend/tests/test_health.py` checks the health response with FastAPI's test client.

`main.py` is the application entry point used by Uvicorn. It constructs the FastAPI app and connects routers so their endpoints become available on that app.

```text
User
  |
  v
Uvicorn
  |
  v
main.py
  |
  v
FastAPI app
  |
  v
include_router(health_router)
  |
  v
GET /health
```

In the command `uv run uvicorn backend.app.main:app --reload`, Uvicorn imports `backend.app.main` and serves the `app` object defined there.

## 4. Phase 2 — First LLM Integration

Phase 2 added `POST /research/test`. The endpoint receives a brief and returns a response from one LLM call.

- `ResearchTestRequest` validates `brief` as text between 10 and 500 characters. FastAPI returns HTTP 422 when validation fails.
- The route reads `request.brief` and awaits `generate_research_response(request.brief)`.
- The service creates a `ChatGroq` model configured with the Groq API key, `groq_model`, and `temperature=0`, sends a concise market-research prompt, and awaits the model response.
- The model is configured as `openai/gpt-oss-20b` through settings; the request is sent to Groq by `ChatGroq`.
- `ResearchTestResponse` contains the original `brief` and the returned `response`.
- If the LLM service raises an exception, the route returns HTTP 502 with `LLM service unavailable`, not provider details.

The endpoint and service are `async def` functions. `await` pauses the current async function while the LLM request completes, allowing the async application to continue handling other work.

The current service has a reusable `create_chat_model()` helper, extracted in Phase 4. It creates the same configured `ChatGroq` model used by the Phase 2 service and the Phase 4 agent.

```text
User
  |
  v
POST /research/test
  |
  v
ResearchTestRequest
  |
  v
test_research()
  |
  v
generate_research_response()
  |
  v
ChatGroq
  |
  v
Groq / configured LLM
  |
  v
ResearchTestResponse
  |
  v
User
```

Phase 2 is a direct LLM call. The application sends one prompt and returns the model's answer; it is not yet an agent deciding to use tools.

## 5. Phase 3 — LangGraph Workflow

Phase 3 added `POST /research/graph`, which runs a small, linear LangGraph workflow.

- `ResearchState` is a `TypedDict` with `brief`, `plan`, `research`, and `status` fields.
- `StateGraph(ResearchState)` creates a graph builder whose nodes read and update this state.
- `add_node()` registers `planner`, `researcher`, and `complete`.
- `add_edge()` defines the fixed path from `START` to `planner`, then `researcher`, then `complete`, and finally `END`.
- `compile()` builds the runnable graph, exposed as the module-level `research_graph`.
- The endpoint creates `initial_state`, awaits `research_graph.ainvoke(initial_state)`, and uses the returned `final_state` to construct `ResearchGraphResponse`.
- `ResearchGraphRequest` validates the brief; `ResearchGraphResponse` returns the brief, plan, research, and completion status.

```text
POST /research/graph
        |
        v
ResearchGraphRequest
        |
        v
initial_state
        |
        v
research_graph.ainvoke()
        |
        v
START
        |
        v
planner
        |
        v
researcher
        |
        v
complete
        |
        v
END
        |
        v
final_state
        |
        v
ResearchGraphResponse
```

LangGraph controls orchestration, but the developer currently defines the sequence through graph edges: `planner -> researcher -> complete`. These nodes are not automatically autonomous agents:

- `planner_node` creates deterministic Python text from the brief; it does not call an LLM.
- `researcher_node` calls the existing `generate_research_response()` service.
- `complete_node` sets `status` to `complete`.

## 6. Phase 4 — First Tool-Calling Agent

Phase 4 added `POST /research/agent` and a small explicit LLM tool-calling loop.

`ResearchAgentRequest` validates the brief at 10–500 characters. `ResearchAgentResponse` returns the original brief and final response. The route awaits `run_research_agent(request.brief)` and returns HTTP 502 with `Research agent unavailable` if agent execution fails.

The agent starts with `create_chat_model()`, which returns the configured `ChatGroq` instance. It calls `bind_tools([get_company_profile])` so the LLM knows the available tool and its schema. Its initial message history contains:

- A `SystemMessage` describing the assistant and the available company profile tool.
- A `HumanMessage` containing the research brief.

The `@tool`-decorated `get_company_profile(company: str)` function is described by its docstring. The tool uses the local `COMPANY_PROFILES` dictionary, which contains short neutral descriptions for Tesla, BYD, Tata Motors, and Mahindra. It does not call a web or other external data API.

For each LLM iteration, the agent awaits `model_with_tools.ainvoke(messages)`. The result is an `AIMessage`. Its `tool_calls` list, if present, describes a requested tool call:

- `name` identifies the tool, currently `get_company_profile`.
- `args` contains the argument values, such as `{"company": "Tesla"}`.
- `id` identifies that particular tool call so the result can be associated with it.

Python, not the LLM, executes the tool using `get_company_profile.invoke(tool_call["args"])`. The agent wraps the result in a `ToolMessage` with the matching tool-call ID, appends it to message history, and calls the LLM again. If the LLM returns an `AIMessage` with no tool calls, the agent returns its final textual answer. `MAX_ITERATIONS = 5` limits the loop; reaching the limit raises a `RuntimeError`, which the API turns into the sanitized 502 response.

```text
User
  |
  v
POST /research/agent
  |
  v
ResearchAgentRequest
  |
  v
run_research_agent()
  |
  v
create_chat_model()
  |
  v
bind_tools([get_company_profile])
  |
  v
LLM
  |
  v
AIMessage
  |
  +---- no tool_calls ----> Final Answer
  |
  +---- tool_calls
           |
           v
     get_company_profile
           |
           v
       Tool Result
           |
           v
       ToolMessage
           |
           v
     message history
           |
           v
       LLM again
           |
           v
      Final Answer
```

The LLM decides whether it wants to request a bound tool. Python executes the requested local function. The result is sent back to the LLM as a `ToolMessage`, and the LLM can then produce the final answer.

This differs from Phase 3: Phase 3 follows a developer-defined graph path, while in Phase 4 the LLM can dynamically request whether to use the bound tool. The Phase 4 loop is written explicitly in Python; it does not use a prebuilt agent helper or LangGraph.

## 7. Important Phase 4 Grounding Limitation

The company profile tool only supplies short, deterministic descriptions. For example, it can return the local Tesla and BYD profiles, but it does not provide sourced market analysis or live facts. The LLM may add information from its own model knowledge when producing the final response.

```text
Tool information       LLM internal knowledge
       \                 /
        \               /
         v             v
              LLM
               |
               v
         Final response
```

Therefore, the current Phase 4 agent is not a fully evidence-grounded research system. Future evidence handling, RAG, and fact-checking phases are intended to improve grounding; none of those capabilities are implemented yet.

## 8. Current API Endpoints

| Method | Endpoint | Phase | Purpose |
| --- | --- | --- | --- |
| GET | `/health` | 1 | Return a basic health status and service name. |
| POST | `/research/test` | 2 | Send a brief to one LLM call and return its response. |
| POST | `/research/graph` | 3 | Run the fixed planner, researcher, and complete LangGraph workflow. |
| POST | `/research/agent` | 4 | Let the LLM request the local company profile tool and return a final response. |

## 9. Current Project Structure

```text
backend/
  app/
    __init__.py
    agents/
      __init__.py
      research_agent.py
    api/
      __init__.py
      health.py
      research.py
    graph/
      __init__.py
      nodes.py
      research_graph.py
      state.py
    models/
      __init__.py
      research.py
    services/
      __init__.py
      llm.py
    tools/
      __init__.py
      company_profile.py
    config.py
    main.py
  tests/
    __init__.py
    test_company_profile_tool.py
    test_health.py
    test_research.py
    test_research_agent.py
    test_research_graph.py
docs/
  phase-1-to-4-progress.md
```

- `agents/` contains the explicit Phase 4 research-agent loop.
- `api/` contains FastAPI routers and endpoint functions.
- `graph/` contains the Phase 3 graph state, nodes, and compiled workflow.
- `models/` contains Pydantic request and response models.
- `services/` contains reusable application services, including the ChatGroq model factory and direct research call.
- `tools/` contains deterministic local tools exposed to the agent.
- `tests/` contains health, endpoint, workflow, tool, and agent tests.
- `docs/` contains this project learning report.

## 10. Testing Strategy

The project uses `pytest` and FastAPI's `TestClient` to check API behavior. Tests use `monkeypatch` to replace runtime dependencies; `AsyncMock` verifies awaited async calls, and `MagicMock` simulates the model and its `bind_tools()` result. Tool-profile tests call only the local deterministic tool.

Automated tests should not call the real Groq API: tests stay deterministic, do not need internet access, do not use API tokens, and do not incur provider costs.

The important Phase 4 loop test simulates:

```text
Mocked LLM response
    -> tool call
    -> local tool execution
    -> ToolMessage
    -> second mocked LLM response
    -> final answer
```

Current verified checkpoint: **14 tests passed** with `uv run pytest backend/tests -q`. The Phase 4 endpoint was also manually tested against the configured Groq model and returned a successful response.

## 11. Learning Progression

```text
Phase 1
API
 |
 v
FastAPI

Phase 2
API
 |
 v
LLM

Phase 3
API
 |
 v
LangGraph
 |
 v
LLM

Phase 4
API
 |
 v
Research Agent
 |
 v
LLM
 |
 v
Tool
 |
 v
LLM
 |
 v
Final Answer
```

- Phase 1 introduced HTTP routes and the FastAPI application.
- Phase 2 introduced request validation and a direct asynchronous LLM call.
- Phase 3 introduced shared workflow state, graph nodes, and explicit orchestration.
- Phase 4 introduced tool descriptions, LLM tool requests, Python tool execution, tool results, and a repeated LLM call.

## 12. Current Architecture

```text
User
 |
 v
Uvicorn
 |
 v
FastAPI (main.py)
 |
+-- health_router --> GET /health
|
`-- research_router
  |
  +-- POST /research/test --> generate_research_response()
  |                                  |
  |                                  v
  |                             ChatGroq / Groq
  |
  +-- POST /research/graph --> research_graph.ainvoke()
  |                              |
  |                              v
  |                  START -> planner -> researcher -> complete -> END
  |                                       |
  |                                       v
  |                             generate_research_response()
  |                                       |
  |                                       v
  |                                  ChatGroq / Groq
  |
  `-- POST /research/agent --> run_research_agent()
                |
                v
            create_chat_model()
                |
                v
              ChatGroq / Groq
                |
          +-----------------+------------------+
          |                                    |
       no tool calls                         tool call
          |                                    |
          v                                    v
       Final answer                    get_company_profile()
                       |
                       v
                      ToolMessage
                       |
                       +--> LLM again
```

`GET /health` is also registered by `main.py` through `health_router`. The three research endpoints are registered on the existing `research_router`.

## 13. Future Roadmap

These are planned learning directions only; they are not implemented or included in the current architecture.

| Planned phase | High-level direction |
| --- | --- |
| Phase 5 | Learn DeepAgents, multi-agent concepts, and delegation. |
| Phase 6 | Add real research sources such as web or PDF ingestion, evidence handling, and RAG/vector database concepts. |
| Phase 7 | Build a more complete research pipeline with synthesis, writing, fact checking, report generation, and persistence. |
| Phase 8 | Add a frontend and productization, then learn Docker and AWS cloud deployment. |

Docker and AWS deployment are intentionally planned as part of an end-to-end, production-style learning journey. No roadmap item above should be read as a completed capability.

## 14. Phase Status

| Phase | Description | Status |
| --- | --- | --- |
| Phase 1 | FastAPI Foundation | COMPLETE |
| Phase 2 | LLM Integration | COMPLETE |
| Phase 3 | LangGraph Workflow | COMPLETE |
| Phase 4 | Tool-Calling Agent | COMPLETE |
| Phase 5 | DeepAgents / Multi-Agent | NOT STARTED |

Current Git checkpoint: `Complete InsightForge phases 1-4` (`c0bf9b3`).

Current branch: `main`.
