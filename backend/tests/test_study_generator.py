from typing import Any

from app.services.ai_provider import AIProvider, FakeAIProvider
from app.services.study_generator import StudyGenerator


class MalformedAIProvider(AIProvider):
    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        return {
            "title": "",
            "overview": None,
            "key_points": ["", 42],
            "key_terms": [{"term": "", "definition": ""}, "bad"],
            "source_quotes": [{"quote": "", "reason": ""}],
        }

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        return [
            {"front": "", "back": None, "topic": "", "difficulty": "impossible", "source_quote": ""},
            {"front": "Provided front"},
        ]

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        return {
            "title": "",
            "questions": [
                {
                    "question": "",
                    "choices": ["First", "Second"],
                    "correct_answer": "Z",
                    "difficulty": "unknown",
                }
            ],
        }


class CapturingFakeAIProvider(FakeAIProvider):
    def __init__(self) -> None:
        self.last_summary_input = ""
        super().__init__()

    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        self.last_summary_input = document_text
        return super().generate_summary(document_text, summary_type)


def test_study_generator_normalizes_malformed_summary() -> None:
    generator = StudyGenerator(MalformedAIProvider())

    summary = generator.generate_summary(_source_text(), "concise")

    assert summary["title"]
    assert summary["overview"]
    assert summary["key_points"]
    assert summary["key_terms"][0]["term"]
    assert summary["source_quotes"][0]["quote"]


def test_study_generator_normalizes_malformed_flashcards_to_requested_count() -> None:
    generator = StudyGenerator(MalformedAIProvider())

    flashcards = generator.generate_flashcards(_source_text(), 3)

    assert len(flashcards) == 3
    assert all(card["front"] for card in flashcards)
    assert all(card["back"] for card in flashcards)
    assert all(card["difficulty"] in {"easy", "medium", "hard"} for card in flashcards)


def test_study_generator_normalizes_malformed_quiz_to_requested_count() -> None:
    generator = StudyGenerator(MalformedAIProvider())

    quiz = generator.generate_quiz(_source_text(), 3, "mixed")

    assert quiz["title"]
    assert len(quiz["questions"]) == 3
    for question in quiz["questions"]:
        assert question["question"]
        assert len(question["choices"]) == 4
        assert question["correct_answer"] in {"A", "B", "C", "D"}
        assert question["difficulty"] in {"easy", "medium", "hard"}
        assert question["explanation"]
        assert question["topic"]


def test_summary_uses_direct_source_context_for_medium_length_documents() -> None:
    provider = CapturingFakeAIProvider()
    generator = StudyGenerator(provider)
    long_source = _linear_programming_source() * 45

    summary = generator.generate_summary(long_source, "concise")

    assert "Chunk 1" not in provider.last_summary_input
    assert "Source Part 1" not in provider.last_summary_input
    assert "convex feasible region" in provider.last_summary_input
    assert "unbounded" in provider.last_summary_input.lower()
    assert "convex" in " ".join(summary["key_points"]).lower()


def _source_text() -> str:
    return (
        "Artificial Intelligence studies rational agents. "
        "Search algorithms explore state spaces with heuristics. "
        "Planning uses actions, preconditions, effects, and goals."
    )


def _linear_programming_source() -> str:
    return (
        "Linear programming geometry explains how constraints define half-spaces and how their intersection "
        "forms a convex feasible region. The simplex method can move between vertices of this region because "
        "a bounded feasible linear program reaches an optimum at a vertex. Infeasible programs have constraints "
        "whose half-spaces do not intersect, so no point satisfies all constraints. Unbounded programs have a "
        "feasible direction where the objective can increase without limit, even though some other objectives "
        "on the same region may still have a vertex optimum. "
    )
