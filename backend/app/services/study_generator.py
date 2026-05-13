from typing import Any

from app.services.ai_provider import AIProvider
from app.services.chunking import chunk_text


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
            intermediate.append(f"Chunk {index}: {summary.get('overview', chunk[:500])}")
        return "\n\n".join(intermediate)

    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        return self.ai_provider.generate_summary(self._prepared_text(document_text), summary_type)

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        return self.ai_provider.generate_flashcards(self._prepared_text(document_text), count)

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        return self.ai_provider.generate_quiz(self._prepared_text(document_text), question_count, difficulty)
