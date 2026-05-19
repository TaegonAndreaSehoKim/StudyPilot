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


class LabeledSummaryProvider(AIProvider):
    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        return {
            "title": "Movement Notes",
            "overview": "Movement notes explain how agents update position over time.",
            "key_points": [
                "Additional explanation - Seek behavior: Seek computes a direction to the target and updates incrementally.",
                "Concept overview - Arrive behavior: Arrive slows near the target to avoid jitter.",
                "Core concept - Update loop: The game loop limits how much movement logic can run each frame.",
            ],
            "key_terms": [{"term": "Seek", "definition": "A movement behavior that heads toward a target."}],
            "source_quotes": [{"quote": "Seek computes a direction to the target", "reason": "Shows the movement rule."}],
        }

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        return []

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        return {"title": "Quiz", "questions": []}


class CapturingFakeAIProvider(FakeAIProvider):
    def __init__(self) -> None:
        self.last_summary_input = ""
        self.last_quiz_input = ""
        super().__init__()

    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        self.last_summary_input = document_text
        return super().generate_summary(document_text, summary_type)

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        self.last_quiz_input = document_text
        return super().generate_quiz(document_text, question_count, difficulty)


def test_study_generator_normalizes_malformed_summary() -> None:
    generator = StudyGenerator(MalformedAIProvider())

    summary = generator.generate_summary(_source_text(), "concise")

    assert summary["title"]
    assert summary["overview"]
    assert summary["key_points"]
    assert summary["key_terms"][0]["term"]
    assert summary["source_quotes"][0]["quote"]


def test_summary_normalization_removes_repetitive_point_labels() -> None:
    generator = StudyGenerator(LabeledSummaryProvider())

    summary = generator.generate_summary(_source_text(), "explanation")

    assert summary["key_points"][0].startswith("Seek computes")
    assert summary["key_points"][1].startswith("Arrive slows")
    assert summary["key_points"][2].startswith("The game loop")
    assert all("Additional explanation -" not in point for point in summary["key_points"])
    assert all("Concept overview -" not in point for point in summary["key_points"])


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


def test_summary_generation_includes_course_context_without_using_it_as_source_quote() -> None:
    provider = CapturingFakeAIProvider()
    generator = StudyGenerator(provider)

    summary = generator.generate_summary(
        _source_text(),
        "detailed",
        course_title="OMSCS Artificial Intelligence",
        course_description="Graduate course covering search, planning, and game-playing agents.",
    )

    assert "Course title: OMSCS Artificial Intelligence" in provider.last_summary_input
    assert "Course description: Graduate course covering search" in provider.last_summary_input
    assert "Source Material:" in provider.last_summary_input
    assert "Artificial Intelligence studies rational agents" in provider.last_summary_input
    assert all("OMSCS" not in quote["quote"] for quote in summary["source_quotes"])


def test_quiz_generation_includes_course_context() -> None:
    provider = CapturingFakeAIProvider()
    generator = StudyGenerator(provider)

    quiz = generator.generate_quiz(
        _source_text(),
        2,
        "mixed",
        course_title="OMSCS Artificial Intelligence",
        course_description="Graduate course covering search, planning, and game-playing agents.",
    )

    assert "Course title: OMSCS Artificial Intelligence" in provider.last_quiz_input
    assert "Course description: Graduate course covering search" in provider.last_quiz_input
    assert "Source Material:" in provider.last_quiz_input
    assert len(quiz["questions"]) == 2


def test_generation_includes_section_context() -> None:
    provider = CapturingFakeAIProvider()
    generator = StudyGenerator(provider)

    generator.generate_summary(
        _source_text(),
        "exam",
        course_title="OMSCS Artificial Intelligence",
        section_title="Midterm 1",
        section_description="Covers search, heuristics, and planning foundations.",
    )

    assert "Course title: OMSCS Artificial Intelligence" in provider.last_summary_input
    assert "Section title: Midterm 1" in provider.last_summary_input
    assert "Section description: Covers search" in provider.last_summary_input
    assert "Source Material:" in provider.last_summary_input


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
