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
    provider = provider_with_response(
        DummyResponse(
            '```json\n{"title":"Notes","overview":"Grounded.","key_points":["One"],"key_terms":[],"source_quotes":[]}\n```'
        )
    )

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
                                "text": (
                                    '{"title":"Nested","questions":[{"question":"What is supported?",'
                                    '"choices":["A. Local search appears","B. Unsupported","C. Unsupported","D. Unsupported"],'
                                    '"correct_answer":"A","explanation":"A is grounded in the notes.","topic":"Local search","difficulty":"medium"}]}'
                                ),
                            }
                        ]
                    }
                ]
            }
        )
    )

    result = provider.generate_quiz("Local search appears in the notes.", 2, "mixed")

    assert result["title"] == "Nested"
    assert len(result["questions"]) == 1


def test_openai_provider_falls_back_for_malformed_summary_shape() -> None:
    provider = provider_with_response(DummyResponse('{"title":"Notes","overview":"Missing arrays","key_points":["One"]}'))

    result = provider.generate_summary("Alpha Beta concepts appear in this source text.", "concise")

    assert "Concise Summary" in result["title"]
    assert result["source_quotes"]


def test_openai_provider_falls_back_for_malformed_quiz_shape() -> None:
    provider = provider_with_response(DummyResponse('{"title":"Quiz","questions":[{"question":"Q","choices":["A"],"correct_answer":"Z"}]}'))

    result = provider.generate_quiz("Alpha Beta concepts appear in this source text.", 2, "medium")

    assert "Quiz" in result["title"]
    assert len(result["questions"]) == 2
    assert all(question["correct_answer"] in {"A", "B", "C", "D"} for question in result["questions"])


def test_openai_provider_falls_back_for_invalid_json() -> None:
    provider = provider_with_response(DummyResponse("not json"))

    result = provider.generate_summary("Alpha Beta concepts appear in this source text.", "exam")

    assert "Exam Summary" in result["title"]
    assert result["key_points"]


def test_fake_ai_marks_insufficient_source_material() -> None:
    provider = FakeAIProvider()

    summary = provider.generate_summary("Too short.", "concise")
    flashcards = provider.generate_flashcards("Too short.", 2)
    quiz = provider.generate_quiz("Too short.", 2, "mixed")

    assert "too short" in summary["overview"].lower()
    assert "Insufficient source" == summary["key_terms"][0]["term"]
    assert all("too short" in card["back"].lower() for card in flashcards)
    assert all("limited" in question["choices"][index].lower() for index, question in enumerate(quiz["questions"]))


def test_fake_ai_uses_source_sentences_for_term_definitions() -> None:
    provider = FakeAIProvider()
    text = (
        "# Search Algorithms\n\n"
        "Artificial Intelligence studies rational agents. "
        "Search algorithms explore state spaces with heuristics. "
        "Planning uses actions, preconditions, effects, and goals."
    )

    summary = provider.generate_summary(text, "exam")
    cards = provider.generate_flashcards(text, 2)

    assert summary["key_terms"][0]["term"] == "Search Algorithms"
    assert "state spaces" in summary["key_terms"][0]["definition"]
    assert cards[0]["front"] == "How would you explain Search Algorithms using the uploaded notes?"
    assert "state spaces" in cards[0]["back"]
