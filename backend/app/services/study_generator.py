from typing import Any

from app.services.ai_provider import AIProvider
from app.services.chunking import chunk_text
from app.services.document_structure import build_study_context
from app.services.study_outputs import normalize_flashcards_result, normalize_quiz_result, normalize_summary_result


class StudyGenerator:
    def __init__(self, ai_provider: AIProvider) -> None:
        self.ai_provider = ai_provider

    def _prepared_text(self, document_text: str, focus_topics: list[str] | None = None) -> str:
        study_context = build_study_context(document_text, focus_topics=focus_topics)
        chunks = chunk_text(study_context)
        if len(chunks) <= 1:
            return study_context
        intermediate = []
        for index, chunk in enumerate(chunks, start=1):
            summary = self.ai_provider.generate_summary(chunk, "concise")
            normalized = normalize_summary_result(summary, chunk, "concise")
            terms = ", ".join(term["term"] for term in normalized["key_terms"][:5])
            points = "; ".join(normalized["key_points"][:5])
            intermediate.append(
                f"Chunk {index}\nOverview: {normalized['overview']}\nKey terms: {terms}\nKey points: {points}"
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
