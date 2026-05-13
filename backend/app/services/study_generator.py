from typing import Any

from app.services.ai_provider import AIProvider
from app.services.chunking import chunk_text
from app.services.study_outputs import normalize_flashcards_result, normalize_quiz_result, normalize_summary_result


class StudyGenerator:
    def __init__(self, ai_provider: AIProvider) -> None:
        self.ai_provider = ai_provider

    def _prepared_text(self, document_text: str) -> str:
        chunks = chunk_text(document_text)
        if len(chunks) <= 1:
            return document_text
        intermediate = []
        for index, chunk in enumerate(chunks, start=1):
            summary = self.ai_provider.generate_summary(chunk, "concise")
            normalized = normalize_summary_result(summary, chunk, "concise")
            intermediate.append(f"Chunk {index}: {normalized['overview']}")
        return "\n\n".join(intermediate)

    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        prepared_text = self._prepared_text(document_text)
        return normalize_summary_result(self.ai_provider.generate_summary(prepared_text, summary_type), prepared_text, summary_type)

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        prepared_text = self._prepared_text(document_text)
        return normalize_flashcards_result(self.ai_provider.generate_flashcards(prepared_text, count), count, prepared_text)

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        prepared_text = self._prepared_text(document_text)
        return normalize_quiz_result(self.ai_provider.generate_quiz(prepared_text, question_count, difficulty), question_count, difficulty, prepared_text)
