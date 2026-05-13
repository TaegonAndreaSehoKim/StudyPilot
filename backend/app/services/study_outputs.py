from __future__ import annotations

import re
from typing import Any

VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_ANSWERS = {"A", "B", "C", "D"}


def _clean_text(value: Any, fallback: str) -> str:
    if isinstance(value, str):
        cleaned = re.sub(r"\s+", " ", value).strip()
        if cleaned:
            return cleaned
    return fallback


def _sentences(document_text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", document_text).strip()
    parts = re.split(r"(?<=[.!?])\s+", clean)
    return [part.strip() for part in parts if part.strip()]


def _excerpt(document_text: str, max_len: int = 180) -> str:
    clean = re.sub(r"\s+", " ", document_text).strip()
    return clean[:max_len].rstrip() or "The uploaded source text is limited."


def _keywords(document_text: str, limit: int) -> list[str]:
    words = re.findall(r"\b[A-Za-z][A-Za-z0-9-]{3,}\b", document_text)
    stop = {"that", "this", "with", "from", "have", "will", "into", "about", "their", "there"}
    seen: set[str] = set()
    keywords: list[str] = []
    for word in words:
        normalized = word.strip("-")
        key = normalized.lower()
        if key in stop or key in seen:
            continue
        seen.add(key)
        keywords.append(normalized)
        if len(keywords) >= limit:
            break
    return keywords or ["General"]


def normalize_summary_result(result: Any, document_text: str, summary_type: str) -> dict[str, Any]:
    source = result if isinstance(result, dict) else {}
    sentences = _sentences(document_text)
    fallback_overview = " ".join(sentences[:2]) or _excerpt(document_text)
    key_points = source.get("key_points") if isinstance(source.get("key_points"), list) else []
    normalized_points = [_clean_text(point, "") for point in key_points]
    normalized_points = [point for point in normalized_points if point]
    if not normalized_points:
        normalized_points = sentences[:5] or [_excerpt(document_text)]

    key_terms = []
    raw_terms = source.get("key_terms") if isinstance(source.get("key_terms"), list) else []
    for item in raw_terms:
        if not isinstance(item, dict):
            continue
        term = _clean_text(item.get("term"), "")
        if not term:
            continue
        key_terms.append(
            {
                "term": term,
                "definition": _clean_text(item.get("definition"), f"{term} appears in the uploaded notes."),
            }
        )
    if not key_terms:
        key_terms = [
            {"term": keyword, "definition": f"{keyword} appears in the uploaded notes."}
            for keyword in _keywords(document_text, 5)
        ]

    source_quotes = []
    raw_quotes = source.get("source_quotes") if isinstance(source.get("source_quotes"), list) else []
    for item in raw_quotes:
        if not isinstance(item, dict):
            continue
        quote = _clean_text(item.get("quote"), "")
        if not quote:
            continue
        source_quotes.append(
            {
                "quote": quote[:240],
                "reason": _clean_text(item.get("reason"), "Representative source excerpt."),
            }
        )
    if not source_quotes:
        source_quotes = [{"quote": _excerpt(document_text), "reason": "Representative source excerpt."}]

    return {
        "title": _clean_text(source.get("title"), f"Study Notes ({summary_type.title()} Summary)"),
        "overview": _clean_text(source.get("overview"), fallback_overview),
        "key_points": normalized_points[:8],
        "key_terms": key_terms[:8],
        "source_quotes": source_quotes[:5],
    }


def normalize_flashcards_result(result: Any, count: int, document_text: str) -> list[dict[str, Any]]:
    raw_items = result if isinstance(result, list) else []
    sentences = _sentences(document_text) or [_excerpt(document_text)]
    keywords = _keywords(document_text, max(count, 1))
    flashcards: list[dict[str, Any]] = []

    for index in range(count):
        raw_item = raw_items[index] if index < len(raw_items) and isinstance(raw_items[index], dict) else {}
        keyword = keywords[index % len(keywords)]
        sentence = sentences[index % len(sentences)]
        difficulty = _clean_text(raw_item.get("difficulty"), "medium").lower()
        if difficulty not in VALID_DIFFICULTIES:
            difficulty = "medium"
        source_quote = raw_item.get("source_quote")
        flashcards.append(
            {
                "front": _clean_text(raw_item.get("front"), f"What should you remember about {keyword}?"),
                "back": _clean_text(raw_item.get("back"), sentence),
                "topic": _clean_text(raw_item.get("topic"), keyword),
                "difficulty": difficulty,
                "source_quote": _clean_text(source_quote, _excerpt(sentence)) if source_quote is not None else _excerpt(sentence),
            }
        )

    return flashcards


def _normalize_choices(value: Any, fallback_sentence: str) -> list[str]:
    if isinstance(value, list):
        choices = [_clean_text(choice, "") for choice in value]
        choices = [choice for choice in choices if choice]
    else:
        choices = []

    if len(choices) < 4:
        choices = [
            f"A. {_excerpt(fallback_sentence, 90)}",
            "B. A distractor not directly supported by the notes",
            "C. A broader claim not established by the document",
            "D. An unrelated interpretation",
        ]

    normalized = choices[:4]
    for index, letter in enumerate(["A", "B", "C", "D"]):
        if not normalized[index].startswith(f"{letter}."):
            normalized[index] = f"{letter}. {normalized[index]}"
    return normalized


def normalize_quiz_result(result: Any, question_count: int, difficulty: str, document_text: str) -> dict[str, Any]:
    source = result if isinstance(result, dict) else {}
    raw_questions = source.get("questions") if isinstance(source.get("questions"), list) else []
    sentences = _sentences(document_text) or [_excerpt(document_text)]
    keywords = _keywords(document_text, max(question_count, 1))
    questions: list[dict[str, Any]] = []

    for index in range(question_count):
        raw_item = raw_questions[index] if index < len(raw_questions) and isinstance(raw_questions[index], dict) else {}
        keyword = keywords[index % len(keywords)]
        sentence = sentences[index % len(sentences)]
        correct_answer = _clean_text(raw_item.get("correct_answer"), "A").upper()[:1]
        if correct_answer not in VALID_ANSWERS:
            correct_answer = "A"
        question_difficulty = _clean_text(raw_item.get("difficulty"), difficulty if difficulty in VALID_DIFFICULTIES else "medium").lower()
        if question_difficulty not in VALID_DIFFICULTIES:
            question_difficulty = "medium"

        questions.append(
            {
                "question": _clean_text(raw_item.get("question"), f"Which option is best supported by the notes about {keyword}?"),
                "choices": _normalize_choices(raw_item.get("choices"), sentence),
                "correct_answer": correct_answer,
                "explanation": _clean_text(raw_item.get("explanation"), f"The answer is grounded in this source excerpt: {_excerpt(sentence)}"),
                "topic": _clean_text(raw_item.get("topic"), keyword),
                "difficulty": question_difficulty,
            }
        )

    return {
        "title": _clean_text(source.get("title"), "Study Quiz"),
        "questions": questions,
    }
