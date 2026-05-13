from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any


class AIProvider(ABC):
    @abstractmethod
    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        raise NotImplementedError


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"[\r\n]+", ". ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [part.strip() for part in parts if len(part.strip()) > 20]


def _meaningful_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        clean = line.strip("# -*\t ")
        if len(clean) > 2:
            lines.append(clean)
    return lines


def _first_line(text: str) -> str:
    for line in _meaningful_lines(text):
        return line[:80]
    return "Study Notes"


def _keywords(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"\b[A-Za-z][A-Za-z0-9-]{3,}\b", text)
    stop = {
        "that",
        "this",
        "with",
        "from",
        "have",
        "will",
        "into",
        "about",
        "their",
        "there",
        "these",
        "those",
        "using",
        "page",
        "notes",
        "study",
        "summary",
        "concept",
        "supported",
        "uploaded",
        "material",
        "source",
        "text",
        "short",
        "limited",
    }
    candidates = [word.strip("-") for word in words if word.lower() not in stop]
    capitalized = [word for word in candidates if word[:1].isupper()]
    source = capitalized if capitalized else candidates
    counts = Counter(word for word in source)
    return [word for word, _ in counts.most_common(limit)]


def _topics(text: str, limit: int = 8) -> list[str]:
    headings = []
    for line in _meaningful_lines(text):
        if line.lower().startswith("review focus topics:"):
            focus = line.split(":", 1)[1] if ":" in line else ""
            headings.extend(topic.strip() for topic in focus.split(",") if topic.strip())
            continue
        if line.lower().startswith("section:"):
            headings.append(line.split(":", 1)[1].strip()[:60])
            continue
        if len(line.split()) <= 6 and not line.endswith((".", "!", "?")):
            headings.append(line[:60])
    topics = headings + _keywords(text, limit=limit * 2)
    seen: set[str] = set()
    unique_topics = []
    for topic in topics:
        key = topic.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_topics.append(topic)
        if len(unique_topics) >= limit:
            break
    return unique_topics


def _excerpt(text: str, max_len: int = 180) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean[:max_len].rstrip()


def _is_insufficient(text: str) -> bool:
    return len(re.sub(r"\s+", "", text)) < 80 or not _sentences(text)


def _best_sentence_for_topic(topic: str, sentences: list[str]) -> str:
    topic_words = {word.lower() for word in re.findall(r"\b[A-Za-z][A-Za-z0-9-]{2,}\b", topic)}
    if not topic_words:
        return sentences[0] if sentences else "The uploaded source text is limited."
    for sentence in sentences:
        sentence_words = {word.lower() for word in re.findall(r"\b[A-Za-z][A-Za-z0-9-]{2,}\b", sentence)}
        if topic_words & sentence_words:
            return sentence
    return sentences[0] if sentences else "The uploaded source text is limited."


def _distractors(topic: str, topics: list[str], sentence: str) -> list[str]:
    alternatives = [candidate for candidate in topics if candidate.lower() != topic.lower()]
    first = alternatives[0] if alternatives else "a nearby concept"
    second = alternatives[1] if len(alternatives) > 1 else "a broader course theme"
    return [
        f"This describes {first}, not {topic}.",
        f"This overstates what the source says about {topic}.",
        f"This confuses {topic} with {second}.",
    ]


def _choice_rationale(correct_letter: str, choices: list[str], source_quote: str) -> str:
    lines = [
        f"Correct answer: {correct_letter}.",
        f"Source quote: {source_quote}",
        "Why other choices are wrong:",
    ]
    for choice in choices:
        letter = choice[:1]
        if letter != correct_letter:
            lines.append(f"{letter}: This option is not the best match for the cited source excerpt.")
    return "\n".join(lines)


class FakeAIProvider(AIProvider):
    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        sentences = _sentences(document_text)
        topics = _topics(document_text)
        title = _first_line(document_text)

        if _is_insufficient(document_text):
            excerpt = _excerpt(document_text) or "The uploaded source text is limited."
            return {
                "title": f"{title} ({summary_type.title()} Summary)",
                "overview": "The uploaded material is too short for a reliable generated summary. Review the original document for context.",
                "key_points": [
                    "StudyPilot found limited source text and avoided adding unsupported details.",
                    f"Available source excerpt: {excerpt}",
                ],
                "key_terms": [{"term": "Insufficient source", "definition": "The uploaded notes do not contain enough extractable detail for reliable term extraction."}],
                "source_quotes": [{"quote": excerpt, "reason": "Only available source excerpt."}],
            }

        overview_sentences = sentences[:2] or ["The uploaded material is short, so StudyPilot generated a limited source-grounded overview."]
        key_points = sentences[1:6] or sentences[:1] or ["The source material is limited; review the original document for more detail."]

        return {
            "title": f"{title} ({summary_type.title()} Summary)",
            "overview": " ".join(overview_sentences),
            "key_points": key_points[:6],
            "key_terms": [
                {"term": topic, "definition": _best_sentence_for_topic(topic, sentences)}
                for topic in topics[:6]
            ],
            "source_quotes": [
                {"quote": _excerpt(sentence), "reason": "Representative excerpt from the uploaded source."}
                for sentence in (sentences[:3] or [_excerpt(document_text)])
            ],
        }

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        sentences = _sentences(document_text)
        topics = _topics(document_text, limit=max(count, 6))
        cards: list[dict[str, Any]] = []
        insufficient = _is_insufficient(document_text)

        for index in range(count):
            topic = topics[index % len(topics)] if topics else f"Concept {index + 1}"
            sentence = _best_sentence_for_topic(topic, sentences)
            difficulty = ["easy", "medium", "hard"][index % 3]
            cards.append(
                {
                    "front": f"What does the source say about {topic}?",
                    "back": "The uploaded material is too short for a reliable card." if insufficient else sentence,
                    "topic": topic,
                    "difficulty": difficulty,
                    "source_quote": _excerpt(sentence if not insufficient else document_text),
                }
            )
        return cards

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        sentences = _sentences(document_text)
        topics = _topics(document_text, limit=max(question_count, 6))
        questions: list[dict[str, Any]] = []
        insufficient = _is_insufficient(document_text)

        for index in range(question_count):
            topic = topics[index % len(topics)] if topics else f"Concept {index + 1}"
            sentence = _best_sentence_for_topic(topic, sentences)
            correct_letter = ["A", "B", "C", "D"][index % 4]
            correct_choice_text = "The source is too limited to support a detailed answer." if insufficient else _excerpt(sentence, 90)
            correct_choice = f"{correct_letter}. {correct_choice_text}"
            distractors = _distractors(topic, topics, sentence)
            choices = [
                f"A. {distractors[0]}",
                f"B. {distractors[1]}",
                f"C. {distractors[2]}",
                "D. The source does not provide enough evidence for this claim.",
            ]
            choices[index % 4] = correct_choice
            question_difficulty = difficulty if difficulty in {"easy", "medium", "hard"} else ["easy", "medium", "hard"][index % 3]
            source_quote = _excerpt(sentence if not insufficient else document_text)
            questions.append(
                {
                    "question": f"Which statement is best supported by the notes about {topic}?",
                    "choices": choices,
                    "correct_answer": correct_letter,
                    "explanation": _choice_rationale(correct_letter, choices, source_quote),
                    "topic": topic,
                    "difficulty": question_difficulty,
                    "source_quote": source_quote,
                }
            )

        return {"title": f"{_first_line(document_text)} Quiz", "questions": questions}


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.fallback = FakeAIProvider()

    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        prompt = self._summary_prompt(document_text, summary_type)
        data = self._json_response(prompt)
        if isinstance(data, dict) and {"title", "overview", "key_points"}.issubset(data):
            return data
        return self.fallback.generate_summary(document_text, summary_type)

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        prompt = self._flashcard_prompt(document_text, count)
        data = self._json_response(prompt)
        cards = data.get("flashcards") if isinstance(data, dict) else data
        if isinstance(cards, list):
            return cards[:count]
        return self.fallback.generate_flashcards(document_text, count)

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        prompt = self._quiz_prompt(document_text, question_count, difficulty)
        data = self._json_response(prompt)
        if isinstance(data, dict) and isinstance(data.get("questions"), list):
            return data
        return self.fallback.generate_quiz(document_text, question_count, difficulty)

    def _json_response(self, prompt: str) -> Any:
        try:
            response = self._create_json_response(prompt)
            text = self._response_text(response)
            return self._parse_json(text)
        except Exception:
            return None

    def _create_json_response(self, prompt: str) -> Any:
        try:
            return self.client.responses.create(
                model=self.model,
                input=prompt,
                text={"format": {"type": "json_object"}},
            )
        except TypeError:
            return self.client.responses.create(
                model=self.model,
                input=prompt,
                response_format={"type": "json_object"},
            )

    def _response_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", "")
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        if hasattr(response, "model_dump"):
            dumped = response.model_dump()
            text = self._text_from_mapping(dumped)
            if text:
                return text

        if isinstance(response, dict):
            text = self._text_from_mapping(response)
            if text:
                return text

        return ""

    def _text_from_mapping(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            for item in value:
                text = self._text_from_mapping(item)
                if text:
                    return text
        if isinstance(value, dict):
            for key in ("output_text", "text"):
                text = value.get(key)
                if isinstance(text, str) and text.strip():
                    return text
                if isinstance(text, dict):
                    nested = self._text_from_mapping(text)
                    if nested:
                        return nested
            for key in ("output", "content"):
                nested = self._text_from_mapping(value.get(key))
                if nested:
                    return nested
        return ""

    def _parse_json(self, text: str) -> Any:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        object_start = cleaned.find("{")
        object_end = cleaned.rfind("}")
        array_start = cleaned.find("[")
        array_end = cleaned.rfind("]")
        candidates = []
        if object_start != -1 and object_end > object_start:
            candidates.append(cleaned[object_start : object_end + 1])
        if array_start != -1 and array_end > array_start:
            candidates.append(cleaned[array_start : array_end + 1])
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return None

    def _summary_prompt(self, document_text: str, summary_type: str) -> str:
        guidance = {
            "concise": "Write a compact study summary with the highest-yield ideas only.",
            "detailed": "Write a section-aware summary that preserves relationships between concepts.",
            "exam": "Write an exam-focused summary with likely test points, common confusions, and comparison-oriented key points.",
        }.get(summary_type, "Write a source-grounded study summary.")
        return (
            "You are generating study material from uploaded course notes.\n"
            "Return only a valid JSON object with keys: title, overview, key_points, key_terms, source_quotes.\n"
            "Rules:\n"
            "- Use only facts supported by the notes.\n"
            "- Preserve section structure when available.\n"
            "- If notes are insufficient, say that explicitly.\n"
            "- key_terms must include definitions grounded in the notes.\n"
            "- source_quotes must be short snippets copied from the notes.\n"
            f"- Summary mode: {summary_type}. {guidance}\n\n"
            f"Notes:\n{document_text[:30000]}"
        )

    def _flashcard_prompt(self, document_text: str, count: int) -> str:
        return (
            "You are creating source-grounded study flashcards from uploaded course notes.\n"
            "Return only a valid JSON object with key flashcards.\n"
            "flashcards must be an array. Each item must include front, back, topic, difficulty, source_quote.\n"
            "Rules:\n"
            "- Ask concept-understanding questions, not trivia.\n"
            "- Use only facts supported by the notes.\n"
            "- source_quote must be a short snippet from the notes.\n"
            "- If notes are insufficient, make the card say the source is insufficient.\n"
            f"- Create exactly {count} cards when enough source material exists.\n\n"
            f"Notes:\n{document_text[:30000]}"
        )

    def _quiz_prompt(self, document_text: str, question_count: int, difficulty: str) -> str:
        return (
            "You are creating a source-grounded multiple-choice quiz from uploaded course notes.\n"
            "Return only a valid JSON object with keys title and questions.\n"
            "Each question must include: question, choices, correct_answer, explanation, topic, difficulty, source_quote.\n"
            "Rules:\n"
            "- Ask concept-understanding questions.\n"
            "- The correct answer must be directly supported by the notes.\n"
            "- Distractors must be plausible but clearly wrong based on the notes.\n"
            "- explanation must include why the correct answer is right and why each distractor is wrong.\n"
            "- topic should be a specific section or concept, never General unless the source is insufficient.\n"
            "- If Review Focus Topics are listed, prioritize those topics.\n"
            f"- Question count: {question_count}. Difficulty: {difficulty}.\n\n"
            f"Notes:\n{document_text[:30000]}"
        )
