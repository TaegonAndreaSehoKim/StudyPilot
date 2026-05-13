from app.services.ai_provider import FakeAIProvider
from app.services.study_generator import StudyGenerator


EVAL_NOTES = """
# Search Algorithms

Artificial Intelligence studies rational agents that choose actions to achieve goals.
Search algorithms explore state spaces by expanding states and evaluating possible paths.
Heuristics guide search toward promising solutions when exhaustive search is too expensive.

# Adversarial Search

Adversarial search models competitive games where agents choose actions against opponents.
Minimax evaluates possible future game states under optimal opposing play.

# Planning

Planning uses actions, preconditions, effects, and goals to build a sequence of steps.
""".strip()


def test_eval_summary_uses_section_topics_and_source_terms() -> None:
    generator = StudyGenerator(FakeAIProvider())

    summary = generator.generate_summary(EVAL_NOTES, "exam")
    terms = [term["term"] for term in summary["key_terms"]]

    assert "Search Algorithms" in terms
    assert "Adversarial Search" in terms
    assert "Planning" in terms
    assert any("state spaces" in point for point in summary["key_points"])
    assert "test points" in summary["overview"]
    assert all(not point.startswith("Section:") for point in summary["key_points"])
    assert any(point.startswith("출제 포인트") for point in summary["key_points"])
    assert any(point.startswith("유사개념 비교") for point in summary["key_points"])
    assert any(point.startswith("암기 포인트") for point in summary["key_points"])


def test_eval_summary_modes_have_distinct_study_intent() -> None:
    generator = StudyGenerator(FakeAIProvider())

    concise = generator.generate_summary(EVAL_NOTES, "concise")
    detailed = generator.generate_summary(EVAL_NOTES, "detailed")

    assert "broad flow" in concise["overview"]
    assert all(point.startswith("핵심개념") for point in concise["key_points"])
    assert "general principles" in detailed["overview"]
    assert all(point.startswith("개괄설명") for point in detailed["key_points"])


def test_eval_quiz_has_specific_topics_and_distractor_rationales() -> None:
    generator = StudyGenerator(FakeAIProvider())

    quiz = generator.generate_quiz(EVAL_NOTES, 4, "mixed")

    assert len(quiz["questions"]) == 4
    assert all(question["topic"] != "General" for question in quiz["questions"])
    assert any(question["topic"] == "Search Algorithms" for question in quiz["questions"])
    assert all("Why other choices are wrong" in question["explanation"] for question in quiz["questions"])
    assert all("Source quote:" in question["explanation"] for question in quiz["questions"])
    assert all("\nSource quote:" in question["explanation"] for question in quiz["questions"])
    assert all("\nWhy other choices are wrong:" in question["explanation"] for question in quiz["questions"])
    assert all("Section:" not in choice for question in quiz["questions"] for choice in question["choices"])
    assert all("source claim" in question["choices"][ord(question["correct_answer"]) - ord("A")] for question in quiz["questions"])


def test_eval_review_quiz_prioritizes_weak_topics() -> None:
    generator = StudyGenerator(FakeAIProvider())

    quiz = generator.generate_review_quiz(EVAL_NOTES, ["Planning"], 2, "medium")

    assert quiz["title"].startswith("Weak Topic Review")
    assert quiz["questions"][0]["topic"] == "Planning"


def test_eval_fake_ai_outputs_contextual_questions_not_raw_sentence_lookup() -> None:
    generator = StudyGenerator(FakeAIProvider())

    quiz = generator.generate_quiz(EVAL_NOTES, 4, "medium")
    questions = [question["question"] for question in quiz["questions"]]

    assert any("how the notes frame" in question for question in questions)
    assert any("surrounding study material" in question for question in questions)
