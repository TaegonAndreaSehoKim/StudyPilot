from __future__ import annotations

import json
from typing import Any

from app.services.ai_provider import FakeAIProvider, OpenAIProvider
from app.services.study_outputs import normalize_summary_result


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
            "```json\n"
            '{"title":"Search Study Guide",'
            '"overview":"Search algorithms help an agent explore a state space by expanding possible states, '
            'comparing paths, and using heuristics when exhaustive search is too expensive. The notes connect '
            'search to rational action because the agent must choose actions that move it toward goals.",'
            '"key_points":["Search algorithms organize problem solving as movement through a state space, so the student should understand what states, actions, and paths represent before memorizing algorithm names.",'
            '"Heuristics matter because they estimate which paths are promising, allowing the search process to focus effort when exhaustive exploration would be too costly.",'
            '"The source frames search as part of rational agency, which means the algorithm is useful because it supports choosing actions that achieve goals."],'
            '"key_terms":[{"term":"Search algorithm","definition":"A method for exploring state spaces to find paths or solutions."},'
            '{"term":"State space","definition":"The set of possible states that can be explored during problem solving."},'
            '{"term":"Heuristic","definition":"A source-supported guide for prioritizing promising paths."}],'
            '"source_quotes":[{"quote":"Search algorithms explore state spaces","reason":"Shows the core mechanism."},'
            '{"quote":"uses heuristics","reason":"Shows how search can be guided."}]}'
            "\n```"
        )
    )

    result = provider.generate_summary("AI search uses heuristics.", "concise")

    assert result["title"] == "Search Study Guide"
    assert "state space" in result["overview"]
    assert len(result["key_points"]) == 3


def test_openai_provider_accepts_string_source_quotes() -> None:
    provider = provider_with_response(
        DummyResponse(
            '{"title":"Game AI Foundations",'
            '"overview":"Artificial intelligence in video games is introduced as a practical way to create agent behavior when conventional algorithms are not enough. The source connects game AI to decision making, rules, search, planning, tactics, and strategy, so the learner should treat it as a design space rather than a single algorithm. It also distinguishes ordinary predefined logic from AI-style approaches that help with behavior and choice.",'
            '"key_points":["Game AI is framed as a practical toolkit for producing behavior in video games, so the learner should connect each technique to the gameplay problem it helps solve rather than memorizing a disconnected list of names.",'
            '"The source defines AI around problems that cannot realistically be solved with conventional algorithms, which means the important distinction is whether ordinary fixed procedures are enough for the behavior the designer wants.",'
            '"Decision making and rules appear as basic ways to structure agent behavior, while search and planning suggest methods for reasoning through options or action sequences when the immediate choice is less obvious.",'
            '"Tactics and strategy extend the discussion from local action choice to broader behavior, showing that game AI can operate at different time scales depending on the gameplay role of the agent."],'
            '"key_terms":[{"term":"Game AI","definition":"Game AI is the use of AI techniques to create behavior for video games, especially when simple conventional algorithms are not enough for the desired agent behavior."},'
            '{"term":"Conventional algorithms","definition":"Conventional algorithms are fixed procedures that may be insufficient when the game problem requires flexible behavior, choice, or adaptation."},'
            '{"term":"Decision making","definition":"Decision making is the process by which a game agent selects actions from the state of the game."}],'
            '"source_quotes":["artificial intelligence for video games","conventional algorithms","decision making, rules, search, planning"]}'
        )
    )

    result = provider.generate_summary("Artificial intelligence for video games uses decision making, rules, search, planning, tactics, and strategy.", "concise")

    assert result["title"] == "Game AI Foundations"
    assert result["source_quotes"] == [
        "artificial intelligence for video games",
        "conventional algorithms",
        "decision making, rules, search, planning",
    ]


def test_openai_provider_rejects_shallow_meta_summary() -> None:
    provider = provider_with_response(
        DummyResponse(
            '{"title":"Quick Review","overview":"These notes focus on Source Notes. The concise summary follows the broad flow.",'
            '"key_points":["Core concept - Source Notes: Chunk 1 Overview repeats the source labels without explaining concepts."],'
            '"key_terms":[{"term":"Chunk 1","definition":"Chunk overview."}],'
            '"source_quotes":[{"quote":"Chunk 1 Overview","reason":"Meta text."}]}'
        )
    )

    result = provider.generate_summary("Linear programming constraints define a convex feasible region.", "concise")

    assert "Concise Summary" in result["title"]
    assert "Source Notes" not in [term["term"] for term in result["key_terms"]]


def test_openai_provider_rejects_pdf_artifact_summary() -> None:
    provider = provider_with_response(
        DummyResponse(
            '{"title":"Study Notes","overview":"Section: Source Material 1: transcript_en.txt Page 3 of 37",'
            '"key_points":["Concept overview - Page 3 of 37: Ty p e o f M o v e m e n t explains movement.",'
            '"Concept overview - A Specific locations are connected according to adjacency.",'
            '"Concept overview - Relaxed de.nition uses .xed size variables and .oats."],'
            '"key_terms":[{"term":"Page 3 of 37","definition":"Ty p e o f M o v e m e n t"},'
            '{"term":"A Specific locations","definition":"connected according to adjacency"},'
            '{"term":"Relaxed de.nition","definition":"uses .xed variables"}],'
            '"source_quotes":[{"quote":"Ty p e o f M o v e m e n t","reason":"Artifact"},'
            '{"quote":"A Specific locations are connected","reason":"Artifact"}]}'
        )
    )

    result = provider.generate_summary(
        "Discrete movement uses adjacent grid locations. Continuous movement uses small position changes.",
        "detailed",
    )

    combined = " ".join([result["overview"], *result["key_points"], *(term["term"] for term in result["key_terms"])])
    assert "Page 3 of 37" not in combined
    assert "Ty p e" not in combined
    assert "de.nition" not in combined


def test_openai_provider_accepts_isolated_artifact_false_positive() -> None:
    points = [
        "Game AI is framed as a practical design problem because the agent should support gameplay, challenge, and believability rather than simply maximize an abstract intelligence score. The source connects this to how a designer decides what behavior belongs in the agent and what behavior belongs in the world. This means the learner should study the concept as a design tradeoff, not as a single algorithm.",
        "A Specific genre constraint can change what kind of behavior is useful, but this sentence is still a normal explanatory point rather than a PDF artifact. The source's broader idea is that different games need different levels of autonomy, planning, and reaction. The key distinction is that useful AI depends on the player's experience, not only on technical sophistication, because the same technique can feel appropriate in one genre and distracting in another.",
        "Rules, search, and planning are presented as different tools that can help an agent select actions under different constraints. Rules encode designer knowledge, search evaluates possibilities, and planning reasons about sequences of actions. The reason this matters is that each method solves a different kind of game behavior problem, so the learner should connect methods to the design pressure that motivates them.",
        "Tactics and strategy operate at different scales of decision making, so they should not be treated as interchangeable labels. Tactical behavior handles immediate local choices, while strategic behavior concerns broader plans or opponent direction. This distinction matters because games often need both short-term reactions and long-term coherence, and because confusing those scales can make an agent look either aimless or unfair.",
        "Projectile and aiming examples show that game AI often reasons under spatial or physical constraints. The source uses these examples to move beyond abstract definitions and into concrete gameplay problems. This means the learner should connect AI techniques to the constraints created by genre, controls, timing, and player expectations, then ask whether the result should be optimal, believable, or deliberately imperfect.",
    ]
    provider = provider_with_response(
        DummyResponse(
            '{"title":"Game AI Design Explanation",'
            '"overview":"Game AI is explained as a practical design area where agents, rules, search, planning, tactics, strategy, and genre constraints all shape behavior. The source emphasizes that useful AI should support gameplay and player experience rather than simply solve everything optimally. This makes the material a detailed explanation of design tradeoffs, not just a list of techniques. The learner should therefore preserve the lecture examples and comparisons because they show how each method becomes useful in a particular game context.",'
            f'"key_points":{json.dumps(points)},'
            '"key_terms":[{"term":"Game AI","definition":"Game AI is a practical design area for creating behavior that supports gameplay, challenge, believability, and player experience rather than abstract optimal intelligence."},'
            '{"term":"Rules","definition":"Rules encode designer knowledge so an agent can choose behavior from recognizable conditions in the current game state without solving every situation from scratch."},'
            '{"term":"Planning","definition":"Planning reasons about action sequences and goals when the behavior problem requires more than a single immediate rule or local reaction."}],'
            '"source_quotes":[{"quote":"artificial intelligence for video games","reason":"Names the scope."},'
            '{"quote":"conventional algorithms","reason":"Supports the AI definition."}]}'
        )
    )

    result = provider.generate_summary("Artificial intelligence for video games uses rules, search, planning, tactics, and strategy.", "detailed")

    assert result["title"] == "Game AI Design Explanation"


def test_openai_provider_keeps_strong_summary_with_missing_terms_and_quotes() -> None:
    points = [
        "Game AI movement should use the simplest representation that supports the movement task because AI shares limited frame time with rendering, audio, input, and other systems. This means the representation is a practical tradeoff, not just a mathematical preference. The source teaches that movement logic should preserve the behavior the game needs while avoiding unnecessary computation. The reason this matters is that a more complicated model can waste time without improving the player-visible result. It also prepares the learner to judge later algorithms by whether their extra realism is worth the cost in a running game.",
        "Discrete movement and continuous movement are introduced as different ways to represent where an agent can be. Discrete movement uses recognizable locations and adjacency rules, while continuous movement appears smooth to the player even though the computer still stores finite numeric values. The distinction matters because it changes the algorithms and assumptions used to update the agent. This also explains why the same game world can require different movement models for different gameplay situations. For study purposes, the important ordering is to understand the representation first, then understand which update rule that representation makes possible.",
        "The simulation loop explains why movement code must be incremental. The game repeatedly reads input, updates state, renders the world, and synchronizes timing, so the agent cannot spend unlimited time deciding how to move. This connects movement algorithms to real-time constraints and explains why simple kinematic formulas are useful. The key point is that movement behavior must fit inside repeated small updates rather than one large offline calculation. That framing helps explain why elapsed time is part of the movement formula instead of an incidental programming detail.",
        "Seek behavior demonstrates how vectors turn a target location into movement. The agent computes the relative vector to the target, normalizes it to separate direction from speed, and multiplies by maximum speed and elapsed time. This avoids teleportation and keeps motion consistent across different frame rates. The reason this matters is that direction, speed, and time are separate concerns, and mixing them together makes movement harder to control. It also gives the learner a concrete example of how a mathematical vector operation becomes a visible behavior in the game world.",
        "Arrive, wander, flee, and path following extend the same kinematic idea by changing the desired velocity or target sequence. The source also notes the limitation: these methods can change velocity or orientation too abruptly, which motivates later steering behaviors. This caveat is important because it shows where the simple model stops being visually natural. The learner should preserve that caveat because it explains why a working algorithm can still produce unconvincing game animation. This is also where the lecture shifts from merely reaching positions to making motion look intentional and believable.",
        "Orientation is treated as related to movement but not identical to position. Some agents can move without changing facing direction, while others need orientation represented as a vector or angle so the rendered character looks believable. This distinction matters because a movement update can be numerically correct while still looking wrong to the player. It also shows why movement systems often track both where the agent is and what direction it appears to face. The concept helps learners separate the physics-like state update from the presentation problem of showing an agent facing the correct way.",
    ]
    provider = provider_with_response(
        DummyResponse(
            '{"title":"Basic Kinematic Agent Movement",'
            '"overview":"The lecture explains game-agent movement as a sequence of representation and update choices. It starts from the need to keep movement simple enough for the game loop, then compares discrete and continuous movement, introduces vector positions, and builds seek-style behavior from direction, speed, and elapsed time. The source also preserves caveats about abrupt motion, capture radius, and why later steering behavior is needed. A useful detailed explanation should therefore keep the lecture order and expand each movement idea as a practical game programming decision: what state is stored, how that state changes during each update, what behavior the player sees, and where the simple kinematic model begins to look unnatural.",'
            f'"key_points":{json.dumps(points + ["key_terms:"]) }'
            '}'
        )
    )

    source_text = (
        "Agent movement distinguishes discrete movement, continuous movement, the simulation loop, seek, arrive, wander, "
        "and path following."
    )
    result = provider.generate_summary(source_text, "explanation")
    normalized = normalize_summary_result(result, source_text, "explanation")

    assert result["title"] == "Basic Kinematic Agent Movement"
    assert "key_terms" not in normalized["key_points"]
    assert normalized["key_terms"]
    assert normalized["source_quotes"]


def test_openai_provider_rejects_thin_detailed_summary() -> None:
    provider = provider_with_response(
        DummyResponse(
            '{"title":"Agent Movement","overview":"Agent movement covers discrete and continuous movement. It also mentions update loops and vectors.",'
            '"key_points":["Discrete movement uses distinct locations.",'
            '"Continuous movement uses small position changes.",'
            '"The update loop runs movement code.",'
            '"Vectors represent positions.",'
            '"Orientation stores facing direction."],'
            '"key_terms":[{"term":"Discrete movement","definition":"Distinct locations."},'
            '{"term":"Continuous movement","definition":"Small changes."},'
            '{"term":"Update loop","definition":"Repeated updates."}],'
            '"source_quotes":[{"quote":"discrete movement","reason":"Term"},'
            '{"quote":"continuous movement","reason":"Term"}]}'
        )
    )

    result = provider.generate_summary(
        "Agent movement distinguishes discrete movement, continuous movement, update loops, vectors, orientation, and arrive behavior.",
        "detailed",
    )

    assert result["title"] != "Agent Movement"
    assert "Detailed Explanation" in result["title"]


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


def test_quiz_prompt_requires_conceptual_explanations() -> None:
    provider = provider_with_response(DummyResponse("{}"))

    prompt = provider._quiz_prompt("Linear programs can be infeasible or unbounded.", 5, "mixed")

    assert "concept-understanding questions" in prompt
    assert "plausible misunderstandings" in prompt
    assert "Why other choices are wrong" in prompt
    assert "exceptions, constraints, or failure cases" in prompt
    assert "If Course Context is provided" in prompt
    assert "correct answer must still be grounded in Source Material" in prompt


def test_summary_prompt_teaches_from_source_order_with_scaffolding() -> None:
    provider = provider_with_response(DummyResponse("{}"))

    prompt = provider._summary_prompt("Linear programming introduces constraints before rounding.", "detailed")

    assert "source's own teaching path as the backbone" in prompt
    assert "detailed study explanation, not a transcript summary" in prompt
    assert "Remove filler aggressively" in prompt
    assert "mini-lesson" in prompt
    assert "source-consistent teaching explanation" in prompt
    assert "at least 60 words" in prompt
    assert "Do not treat context as source evidence" in prompt


def test_explanation_prompt_expands_beyond_compression() -> None:
    provider = provider_with_response(DummyResponse("{}"))

    prompt = provider._summary_prompt("Discrete movement uses adjacency while continuous movement uses vectors.", "explanation")

    assert "expanded explanatory guide" in prompt
    assert "Do not compress the useful teaching content" in prompt
    assert "Remove casual filler and transcript chatter" in prompt
    assert "4-7 sentences and at least 65 words" in prompt
    assert "background explanations, analogies, or intuition" in prompt


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
