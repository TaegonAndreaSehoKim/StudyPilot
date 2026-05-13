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
    cleaned = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [part.strip() for part in parts if len(part.strip()) > 20]


def _first_line(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip("# -*\t ")
        if clean:
            return clean[:80]
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
    }
    candidates = [word.strip("-") for word in words if word.lower() not in stop]
    capitalized = [word for word in candidates if word[:1].isupper()]
    source = capitalized if capitalized else candidates
    counts = Counter(word for word in source)
    return [word for word, _ in counts.most_common(limit)]


def _excerpt(text: str, max_len: int = 180) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean[:max_len].rstrip()


class FakeAIProvider(AIProvider):
    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        sentences = _sentences(document_text)
        keywords = _keywords(document_text)
        title = _first_line(document_text)
        overview_sentences = sentences[:2] or ["The uploaded material is short, so StudyPilot generated a limited source-grounded overview."]
        key_points = sentences[1:6] or sentences[:1] or ["The source material is limited; review the original document for more detail."]

        return {
            "title": f"{title} ({summary_type.title()} Summary)",
            "overview": " ".join(overview_sentences),
            "key_points": key_points[:6],
            "key_terms": [
                {"term": keyword, "definition": f"{keyword} appears as an important term in the uploaded notes."}
                for keyword in keywords[:6]
            ],
            "source_quotes": [
                {"quote": _excerpt(sentence), "reason": "Representative excerpt from the uploaded source."}
                for sentence in (sentences[:3] or [_excerpt(document_text)])
            ],
        }

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        sentences = _sentences(document_text)
        keywords = _keywords(document_text, limit=max(count, 6))
        cards: list[dict[str, Any]] = []

        for index in range(count):
            keyword = keywords[index % len(keywords)] if keywords else f"Concept {index + 1}"
            sentence = sentences[index % len(sentences)] if sentences else "The uploaded material is too short for a detailed source quote."
            difficulty = ["easy", "medium", "hard"][index % 3]
            cards.append(
                {
                    "front": f"What should you remember about {keyword}?",
                    "back": sentence,
                    "topic": keyword,
                    "difficulty": difficulty,
                    "source_quote": _excerpt(sentence),
                }
            )
        return cards

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        sentences = _sentences(document_text)
        keywords = _keywords(document_text, limit=max(question_count, 6))
        questions: list[dict[str, Any]] = []

        for index in range(question_count):
            keyword = keywords[index % len(keywords)] if keywords else f"Concept {index + 1}"
            sentence = sentences[index % len(sentences)] if sentences else "The source material is limited."
            correct_letter = ["A", "B", "C", "D"][index % 4]
            correct_choice = f"{correct_letter}. {_excerpt(sentence, 90)}"
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
                    "question": f"Which option is best supported by the notes about {keyword}?",
                    "choices": choices,
                    "correct_answer": correct_letter,
                    "explanation": f"The selected answer is grounded in this source excerpt: {_excerpt(sentence)}",
                    "topic": keyword,
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
            "Create a source-grounded study summary as JSON with keys title, overview, "
            "key_points, key_terms, source_quotes. Only use facts from the notes. "
            f"Summary type: {summary_type}.\n\nNotes:\n{document_text[:30000]}"
        )
        data = self._json_response(prompt)
        if isinstance(data, dict) and {"title", "overview", "key_points"}.issubset(data):
            return data
        return self.fallback.generate_summary(document_text, summary_type)

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        prompt = (
            "Create source-grounded flashcards as a JSON array. Each item must include "
            "front, back, topic, difficulty, source_quote. "
            f"Count: {count}.\n\nNotes:\n{document_text[:30000]}"
        )
        data = self._json_response(prompt)
        if isinstance(data, list):
            return data[:count]
        return self.fallback.generate_flashcards(document_text, count)

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        prompt = (
            "Create a source-grounded multiple-choice quiz as JSON with keys title and questions. "
            "Each question must include question, choices, correct_answer, explanation, topic, difficulty. "
            f"Question count: {question_count}. Difficulty: {difficulty}.\n\nNotes:\n{document_text[:30000]}"
        )
        data = self._json_response(prompt)
        if isinstance(data, dict) and isinstance(data.get("questions"), list):
            return data
        return self.fallback.generate_quiz(document_text, question_count, difficulty)

    def _json_response(self, prompt: str) -> Any:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                response_format={"type": "json_object"},
            )
            text = getattr(response, "output_text", "")
            return json.loads(text)
        except Exception:
            return None
