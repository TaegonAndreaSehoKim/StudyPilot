from __future__ import annotations

from typing import Any

from app.services.ai_provider import FakeAIProvider, OpenAIProvider


class DummyResponse:
    def __init__(self, output_text: str = "", payload: dict[str, Any] | None = None) -> None:
        self.output_text = output_text
        self.payload = payload

    def model_dump(self) -> dict[str, Any]:
        return self.payload or {}


class DummyResponses:
    def __init__(self, response: DummyResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> DummyResponse:
        self.calls.append(kwargs)
        return self.response


class DummyClient:
    def __init__(self, response: DummyResponse) -> None:
        self.responses = DummyResponses(response)


def provider_with_response(response: DummyResponse) -> OpenAIProvider:
    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.client = DummyClient(response)
    provider.model = "test-model"
    provider.fallback = FakeAIProvider()
    return provider


def test_openai_provider_parses_json_code_fence() -> None:
    provider = provider_with_response(DummyResponse('```json\n{"title":"Notes","overview":"Grounded.","key_points":["One"]}\n```'))

    result = provider.generate_summary("AI search uses heuristics.", "concise")

    assert result["title"] == "Notes"
    assert result["overview"] == "Grounded."
    assert result["key_points"] == ["One"]


def test_openai_provider_accepts_wrapped_flashcards() -> None:
    provider = provider_with_response(
        DummyResponse(
            '{"flashcards":[{"front":"What is A*?","back":"A search algorithm.","topic":"A*","difficulty":"medium","source_quote":"A* search"}]}'
        )
    )

    result = provider.generate_flashcards("A* search uses heuristics.", 3)

    assert len(result) == 1
    assert result[0]["front"] == "What is A*?"
    assert provider.client.responses.calls[0]["text"] == {"format": {"type": "json_object"}}


def test_openai_provider_reads_nested_response_payload() -> None:
    provider = provider_with_response(
        DummyResponse(
            payload={
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"title":"Nested","questions":[]}',
                            }
                        ]
                    }
                ]
            }
        )
    )

    result = provider.generate_quiz("Local search appears in the notes.", 2, "mixed")

    assert result["title"] == "Nested"
    assert result["questions"] == []


def test_openai_provider_falls_back_for_invalid_json() -> None:
    provider = provider_with_response(DummyResponse("not json"))

    result = provider.generate_summary("Alpha Beta concepts appear in this source text.", "exam")

    assert "Exam Summary" in result["title"]
    assert result["key_points"]
