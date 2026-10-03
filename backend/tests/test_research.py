from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.app.api import research
from backend.app.main import app


client = TestClient(app)


def test_research_returns_mocked_llm_response(monkeypatch) -> None:
    brief = "Compare Tesla and BYD in the Indian EV market."
    mocked_response = (
        "Tesla and BYD have different competitive positions in the Indian EV market."
    )
    generate_response = AsyncMock(return_value=mocked_response)
    monkeypatch.setattr(research, "generate_research_response", generate_response)

    response = client.post("/research/test", json={"brief": brief})

    assert response.status_code == 200
    assert response.json() == {"brief": brief, "response": mocked_response}
    generate_response.assert_awaited_once_with(brief)


def test_research_rejects_short_brief_without_calling_llm(monkeypatch) -> None:
    generate_response = AsyncMock()
    monkeypatch.setattr(research, "generate_research_response", generate_response)

    response = client.post("/research/test", json={"brief": "Too short"})

    assert response.status_code == 422
    generate_response.assert_not_awaited()


def test_research_hides_llm_error_details(monkeypatch) -> None:
    generate_response = AsyncMock(side_effect=RuntimeError("provider secret"))
    monkeypatch.setattr(research, "generate_research_response", generate_response)

    response = client.post(
        "/research/test",
        json={"brief": "Compare electric vehicle market trends."},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "LLM service unavailable"}