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
            choices = [
                "A. A concept directly supported by the uploaded notes",
                "B. A distractor that is not the best source-grounded answer",
                "C. A broad claim not established by the document",
                "D. An unrelated interpretation",
            ]
            choices[index % 4] = correct_choice
            question_difficulty = difficulty if difficulty in {"easy", "medium", "hard"} else ["easy", "medium", "hard"][index % 3]
            questions.append(
                {
                    "question": f"Which option is best supported by the notes about {topic}?",
                    "choices": choices,
                    "correct_answer": correct_letter,
                    "explanation": f"The selected answer is grounded in this source excerpt: {_excerpt(sentence if not insufficient else document_text)}",
                    "topic": topic,
                    "difficulty": question_difficulty,
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
        prompt = (
            "Create a source-grounded study summary as a JSON object with keys title, overview, "
            "key_points, key_terms, source_quotes. Return only JSON. Only use facts from the notes. "
            f"Summary type: {summary_type}.\n\nNotes:\n{document_text[:30000]}"
        )
        data = self._json_response(prompt)
        if isinstance(data, dict) and {"title", "overview", "key_points"}.issubset(data):
            return data
        return self.fallback.generate_summary(document_text, summary_type)

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        prompt = (
            "Create source-grounded flashcards as a JSON object with key flashcards. "
            "flashcards must be an array and each item must include front, back, topic, difficulty, source_quote. "
            "Return only JSON. "
            f"Count: {count}.\n\nNotes:\n{document_text[:30000]}"
        )
        data = self._json_response(prompt)
        cards = data.get("flashcards") if isinstance(data, dict) else data
        if isinstance(cards, list):
            return cards[:count]
        return self.fallback.generate_flashcards(document_text, count)

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        prompt = (
            "Create a source-grounded multiple-choice quiz as JSON with keys title and questions. "
            "Each question must include question, choices, correct_answer, explanation, topic, difficulty. "
            "Return only JSON. "
            f"Question count: {question_count}. Difficulty: {difficulty}.\n\nNotes:\n{document_text[:30000]}"
        )
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
