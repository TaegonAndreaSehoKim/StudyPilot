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
    assert any("exam review" in point.lower() for point in summary["key_points"])
    assert any("distinguish" in point.lower() for point in summary["key_points"])
    assert any("memorizing" in point.lower() for point in summary["key_points"])


def test_eval_summary_modes_have_distinct_study_intent() -> None:
    generator = StudyGenerator(FakeAIProvider())

    concise = generator.generate_summary(EVAL_NOTES, "concise")
    detailed = generator.generate_summary(EVAL_NOTES, "detailed")

    assert "broad flow" in concise["overview"]
    assert all(not point.startswith("Core concept -") for point in concise["key_points"])
    assert all(not point.startswith("Concept overview -") for point in detailed["key_points"])
    assert "detailed explanation" in detailed["overview"].lower() or "teaching logic" in detailed["overview"].lower()


def test_transcript_style_detailed_summary_uses_real_concepts_not_pipeline_labels() -> None:
    generator = StudyGenerator(FakeAIProvider())
    transcript = _agent_movement_transcript_excerpt()

    summary = generator.generate_summary(transcript, "detailed")
    combined = " ".join(
        [summary["title"], summary["overview"], *summary["key_points"], *(term["term"] for term in summary["key_terms"])]
    )

    assert len(summary["key_points"]) >= 4
    assert "Source Part" not in combined
    assert "Concrete study points" not in combined
    assert "Concept definitions" not in combined
    assert "Source evidence" not in combined
    assert any("Discrete movement" in point or "Discrete movement" in term["term"] for point in summary["key_points"] for term in summary["key_terms"])
    assert any("Continuous movement" in point or "Continuous movement" in term["term"] for point in summary["key_points"] for term in summary["key_terms"])
    assert any("Simulation update loop" in point or "Simulation update loop" in term["term"] for point in summary["key_points"] for term in summary["key_terms"])


def test_game_ai_intro_transcript_does_not_collapse_into_agent_movement() -> None:
    generator = StudyGenerator(FakeAIProvider())
    transcript = _game_ai_intro_transcript_excerpt()

    summary = generator.generate_summary(transcript, "explanation")
    combined = " ".join(
        [summary["title"], summary["overview"], *summary["key_points"], *(term["term"] for term in summary["key_terms"])]
    )

    assert summary["title"].startswith("Introduction to Game AI")
    assert "AI definition and scope" in combined
    assert "Game AI design space" in combined
    assert "Rules, search, and planning" in combined
    assert "Discrete movement" not in combined
    assert "Continuous movement" not in combined
    assert "Arrive behavior" not in combined
    assert "concise summary" not in summary["overview"].lower()


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


def _agent_movement_transcript_excerpt() -> str:
    return """
[00:00:12] This lecture introduces basic agent movement for game AI. The goal is to keep the representation simple because AI has limited computation time inside a game.
[00:02:14] Discrete movement uses distinct locations, like board game grid cells, and agents move through adjacency rules. The layout is motivated by gameplay rules and often uses turn-based or slow updates.
[00:03:46] Continuous movement lets a character move by small increments, as in real-time arcade or platform games. Even though computers represent positions discretely, the player perceives movement as smooth because there are many tiny locations and high frame rates.
[00:12:00] A game runs through a simulation update loop: observe input, update the simulation and AI, render the result, synchronize timing, and repeat. Agent code only gets a fraction of a second each frame.
[00:16:10] For continuous worlds, position vectors describe where an agent is relative to an origin in a 2D coordinate system. Many 3D games still use 2D movement planning because gravity keeps most characters on a surface.
[00:20:01] The agent can be simplified to a point for movement decisions, with extra data such as radius used when collision or gameplay interactions matter.
[00:21:35] Seeking a target starts by subtracting the agent position from the target position to get a relative vector. Moving by the whole vector would teleport, so the agent should move incrementally through the update loop.
[00:27:20] To standardize speed, normalize the direction vector, multiply by the agent's maximum speed, and scale by elapsed time. This separates direction from speed.
[00:47:07] Orientation stores which direction the agent faces. It can be represented as a unit vector or angle, and functions like atan2 help recover the angle without losing quadrant information.
[01:00:04] Arrive behavior adds a capture radius and slows down near the target. This avoids exact floating-point equality checks and prevents the agent from wiggling around the target.
[01:07:06] Wander behavior uses the previous orientation and adds a small biased random change so the agent drifts naturally instead of zigzagging randomly.
[01:10:34] Path following uses seek for a sequence of waypoints and may use arrive for the final waypoint. Steering behaviors are introduced later because basic kinematic movement can turn too sharply and lacks momentum.
""".strip()


def _game_ai_intro_transcript_excerpt() -> str:
    return """
[00:00:05] Hello. In this video I'm going to present an introduction to artificial intelligence for video games. I want to start by asking what AI is outside of games. One earlier view is that AI is any task performed by a machine that had previously been considered to require a human, but that definition has evolved.
[00:01:01] A more modern view is that AI provides solutions for problems that can't be realistically solved using conventional algorithms. In games, the practical question is how AI can support gameplay and create useful behavior.
[00:03:15] We can think about autonomy and behavior for non-player characters. The designer decides what the agent can observe, what it controls, and how its actions should appear to the player.
[00:06:20] Some game AI can be rule based. In other cases you might use decision trees, state machines, or behavior trees to select actions from the current state of the game.
[00:09:40] Limited search and path planning can help when an agent needs to reason about possible options or move through the world. These methods are tools within a larger game AI design space, not the whole definition of AI.
[00:13:25] Tactics and strategy appear in war game scenarios where the opponent needs immediate local choices and broader strategic behavior. Projectile games also raise aiming problems where the AI needs to reason about spatial constraints.
[00:16:42] Later lectures will talk more about movement and path planning, but this lecture is setting up the range of problems and techniques that count as game AI.
""".strip()
