from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.app.graph import nodes
from backend.app.main import app


client = TestClient(app)


def test_research_graph_returns_completed_workflow(monkeypatch) -> None:
    brief = "Compare Tesla and BYD in the Indian EV market."
    mocked_research = "A fixed market research response."
    generate_response = AsyncMock(return_value=mocked_research)
    monkeypatch.setattr(nodes, "generate_research_response", generate_response)

    response = client.post("/research/graph", json={"brief": brief})
    result = response.json()

    assert response.status_code == 200
    assert result["brief"] == brief
    assert result["plan"]
    assert result["research"] == mocked_research
    assert result["status"] == "complete"
    generate_response.assert_awaited_once_with(brief)


def test_research_graph_rejects_short_brief_without_calling_llm(monkeypatch) -> None:
    generate_response = AsyncMock()
    monkeypatch.setattr(nodes, "generate_research_response", generate_response)

    response = client.post("/research/graph", json={"brief": "Too short"})

    assert response.status_code == 422
    generate_response.assert_not_awaited()


def test_research_graph_hides_llm_error_details(monkeypatch) -> None:
    generate_response = AsyncMock(side_effect=RuntimeError("provider secret"))
    monkeypatch.setattr(nodes, "generate_research_response", generate_response)

    response = client.post(
        "/research/graph",
        json={"brief": "Compare electric vehicle market trends."},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Research workflow unavailable"}