from typing import Any

from app.services.ai_provider import AIProvider
from app.services.chunking import chunk_text
from app.services.document_structure import build_study_context
from app.services.study_outputs import normalize_flashcards_result, normalize_quiz_result, normalize_summary_result


DIRECT_STUDY_CONTEXT_MAX_CHARS = 80000
CHUNKED_STUDY_CONTEXT_MAX_CHARS = 24000
CHUNKED_STUDY_CONTEXT_OVERLAP_CHARS = 1000
COMPACTED_STUDY_CONTEXT_MAX_CHARS = 70000
COURSE_CONTEXT_MAX_CHARS = 1200


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
        return self._compact_large_context(chunks, focus_topics)

    def _compact_large_context(self, chunks: list[str], focus_topics: list[str] | None = None) -> str:
        prefix = ""
        if focus_topics:
            prefix = "Review Focus Topics: " + ", ".join(focus_topics) + "\n\n"

        available = max(COMPACTED_STUDY_CONTEXT_MAX_CHARS - len(prefix), 10000)
        per_chunk_budget = max(3000, available // len(chunks))
        compacted_parts = []
        for index, chunk in enumerate(chunks, start=1):
            compacted_parts.append(
                f"Source Part {index}\n"
                f"{self._balanced_excerpt(chunk, per_chunk_budget)}"
            )
        return (prefix + "\n\n".join(compacted_parts))[:COMPACTED_STUDY_CONTEXT_MAX_CHARS]

    def _balanced_excerpt(self, text: str, max_chars: int) -> str:
        cleaned = " ".join(text.split())
        if len(cleaned) <= max_chars:
            return cleaned
        marker = "\n[...]\n"
        head_chars = max_chars * 2 // 3
        tail_chars = max_chars - head_chars - len(marker)
        head = cleaned[:head_chars].rsplit(" ", 1)[0].strip()
        tail = cleaned[-tail_chars:].split(" ", 1)[-1].strip()
        return f"{head}{marker}{tail}"

    def _with_generation_context(
        self,
        prepared_text: str,
        course_title: str | None = None,
        course_description: str | None = None,
        section_title: str | None = None,
        section_description: str | None = None,
        learner_request: str | None = None,
    ) -> str:
        context_lines = []
        if course_title and course_title.strip():
            context_lines.append(f"Course title: {course_title.strip()}")
        if course_description and course_description.strip():
            context_lines.append(f"Course description: {course_description.strip()}")
        if section_title and section_title.strip():
            context_lines.append(f"Section title: {section_title.strip()}")
        if section_description and section_description.strip():
            context_lines.append(f"Section description: {section_description.strip()}")
        if learner_request and learner_request.strip():
            context_lines.append(f"Learner request: {learner_request.strip()}")
        if not context_lines:
            return prepared_text
        context = "\n".join(context_lines)[:COURSE_CONTEXT_MAX_CHARS].strip()
        return (
            "Course and Section Context (use for scope and emphasis, not as source evidence):\n"
            f"{context}\n\n"
            f"Source Material:\n{prepared_text}"
        )

    def generate_summary(
        self,
        document_text: str,
        summary_type: str,
        course_title: str | None = None,
        course_description: str | None = None,
        section_title: str | None = None,
        section_description: str | None = None,
        learner_request: str | None = None,
    ) -> dict[str, Any]:
        prepared_text = self._prepared_text(document_text)
        generation_text = self._with_generation_context(
            prepared_text,
            course_title,
            course_description,
            section_title,
            section_description,
            learner_request,
        )
        return normalize_summary_result(self.ai_provider.generate_summary(generation_text, summary_type), prepared_text, summary_type)

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        prepared_text = self._prepared_text(document_text)
        return normalize_flashcards_result(self.ai_provider.generate_flashcards(prepared_text, count), count, prepared_text)

    def generate_quiz(
        self,
        document_text: str,
        question_count: int,
        difficulty: str,
        course_title: str | None = None,
        course_description: str | None = None,
        section_title: str | None = None,
        section_description: str | None = None,
    ) -> dict[str, Any]:
        prepared_text = self._prepared_text(document_text)
        generation_text = self._with_generation_context(
            prepared_text,
            course_title,
            course_description,
            section_title,
            section_description,
        )
        return normalize_quiz_result(self.ai_provider.generate_quiz(generation_text, question_count, difficulty), question_count, difficulty, prepared_text)

    def generate_review_quiz(
        self,
        document_text: str,
        topics: list[str],
        question_count: int,
        difficulty: str,
        course_title: str | None = None,
        course_description: str | None = None,
        section_title: str | None = None,
        section_description: str | None = None,
    ) -> dict[str, Any]:
        prepared_text = self._prepared_text(document_text, focus_topics=topics)
        generation_text = self._with_generation_context(
            prepared_text,
            course_title,
            course_description,
            section_title,
            section_description,
        )
        result = self.ai_provider.generate_quiz(generation_text, question_count, difficulty)
        normalized = normalize_quiz_result(result, question_count, difficulty, prepared_text)
        if topics:
            normalized["title"] = f"Weak Topic Review: {', '.join(topics[:3])}"
        return normalized
