import asyncio
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from backend.app.agents import research_agent
from backend.app.api import research
from backend.app.main import app
from backend.app.tools.company_profile import get_company_profile


client = TestClient(app)


def test_research_agent_returns_final_response(monkeypatch) -> None:
    brief = "Compare Tesla and BYD in the Indian EV market."
    final_answer = "A mocked final research answer."
    run_agent = AsyncMock(return_value=final_answer)
    monkeypatch.setattr(research, "run_research_agent", run_agent)

    response = client.post("/research/agent", json={"brief": brief})

    assert response.status_code == 200
    assert response.json() == {"brief": brief, "response": final_answer}
    run_agent.assert_awaited_once_with(brief)


def test_research_agent_rejects_short_brief_without_running_agent(monkeypatch) -> None:
    run_agent = AsyncMock()
    monkeypatch.setattr(research, "run_research_agent", run_agent)

    response = client.post("/research/agent", json={"brief": "Too short"})

    assert response.status_code == 422
    run_agent.assert_not_awaited()


def test_research_agent_hides_execution_error(monkeypatch) -> None:
    run_agent = AsyncMock(side_effect=RuntimeError("provider secret"))
    monkeypatch.setattr(research, "run_research_agent", run_agent)

    response = client.post(
        "/research/agent",
        json={"brief": "Compare electric vehicle market trends."},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Research agent unavailable"}


def test_research_agent_sends_tool_result_back_to_model(monkeypatch) -> None:
    brief = "Give me the company profile for Tesla."
    final_answer = "Tesla is a US-based electric vehicle and clean energy company."
    tool_call_response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "get_company_profile",
                "args": {"company": "Tesla"},
                "id": "call_1",
                "type": "tool_call",
            }
        ],
    )
    final_response = AIMessage(content=final_answer)

    model_with_tools = MagicMock()
    model_with_tools.ainvoke = AsyncMock(
        side_effect=[tool_call_response, final_response]
    )
    model = MagicMock()
    model.bind_tools.return_value = model_with_tools
    monkeypatch.setattr(research_agent, "create_chat_model", lambda: model)

    result = asyncio.run(research_agent.run_research_agent(brief))

    assert result == final_answer
    model.bind_tools.assert_called_once_with([get_company_profile])
    assert model_with_tools.ainvoke.await_count == 2

    first_messages = model_with_tools.ainvoke.await_args_list[0].args[0]
    assert isinstance(first_messages[0], SystemMessage)
    assert isinstance(first_messages[1], HumanMessage)

    second_messages = model_with_tools.ainvoke.await_args_list[1].args[0]
    tool_message = next(
        message for message in second_messages if isinstance(message, ToolMessage)
    )
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.tool_call_id == "call_1"
    assert tool_message.content == get_company_profile.invoke({"company": "Tesla"})