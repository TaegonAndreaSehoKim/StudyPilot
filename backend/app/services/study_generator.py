from typing import Any

from app.services.ai_provider import AIProvider
from app.services.chunking import chunk_text
from app.services.document_structure import build_study_context
from app.services.study_outputs import normalize_flashcards_result, normalize_quiz_result, normalize_summary_result


DIRECT_STUDY_CONTEXT_MAX_CHARS = 28000
CHUNKED_STUDY_CONTEXT_MAX_CHARS = 24000
CHUNKED_STUDY_CONTEXT_OVERLAP_CHARS = 1000


class StudyGenerator:
    def __init__(self, ai_provider: AIProvider) -> None:
        self.ai_provider = ai_provider

    def _prepared_text(self, document_text: str, focus_topics: list[str] | None = None) -> str:
        study_context = build_study_context(document_text, focus_topics=focus_topics)
        if len(study_context) <= DIRECT_STUDY_CONTEXT_MAX_CHARS:
            return study_context

        chunks = chunk_text(
            study_context,
            max_chars=CHUNKED_STUDY_CONTEXT_MAX_CHARS,
            overlap_chars=CHUNKED_STUDY_CONTEXT_OVERLAP_CHARS,
        )
        if len(chunks) <= 1:
            return study_context
        intermediate = []
        for index, chunk in enumerate(chunks, start=1):
            summary = self.ai_provider.generate_summary(chunk, "detailed")
            normalized = normalize_summary_result(summary, chunk, "detailed")
            terms = "\n".join(
                f"- {term['term']}: {term['definition']}" for term in normalized["key_terms"][:8]
            )
            points = "\n".join(f"- {point}" for point in normalized["key_points"][:8])
            quotes = "\n".join(
                f"- {quote['quote']} ({quote['reason']})" for quote in normalized["source_quotes"][:4]
            )
            intermediate.append(
                f"Source Part {index}\n"
                f"Part overview: {normalized['overview']}\n"
                f"Concrete study points:\n{points}\n"
                f"Concept definitions:\n{terms}\n"
                f"Source evidence:\n{quotes}"
            )
        prefix = ""
        if focus_topics:
            prefix = "Review Focus Topics: " + ", ".join(focus_topics) + "\n\n"
        return prefix + "\n\n".join(intermediate)

    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        prepared_text = self._prepared_text(document_text)
        return normalize_summary_result(self.ai_provider.generate_summary(prepared_text, summary_type), prepared_text, summary_type)

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        prepared_text = self._prepared_text(document_text)
        return normalize_flashcards_result(self.ai_provider.generate_flashcards(prepared_text, count), count, prepared_text)

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        prepared_text = self._prepared_text(document_text)
        return normalize_quiz_result(self.ai_provider.generate_quiz(prepared_text, question_count, difficulty), question_count, difficulty, prepared_text)

    def generate_review_quiz(self, document_text: str, topics: list[str], question_count: int, difficulty: str) -> dict[str, Any]:
        prepared_text = self._prepared_text(document_text, focus_topics=topics)
        result = self.ai_provider.generate_quiz(prepared_text, question_count, difficulty)
        normalized = normalize_quiz_result(result, question_count, difficulty, prepared_text)
        if topics:
            normalized["title"] = f"Weak Topic Review: {', '.join(topics[:3])}"
        return normalized
