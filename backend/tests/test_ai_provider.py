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
