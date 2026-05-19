from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.text_normalization import normalize_extracted_text, normalize_inline_text


@dataclass(frozen=True)
class StudySection:
    title: str
    content: str


GENERIC_SECTION_TITLE = "Source Notes"


def prepare_study_text(text: str) -> str:
    normalized = normalize_extracted_text(text)
    normalized = _insert_study_boundaries(normalized)
    lines = [line.rstrip() for line in normalized.splitlines()]
    repeated_lines = _repeated_noise_lines(lines)
    cleaned_lines = []
    previous_blank = False

    for line in lines:
        stripped = line.strip()
        if stripped in repeated_lines:
            continue
        if re.fullmatch(r"\d{1,4}", stripped):
            continue
        if re.fullmatch(r"(?:---\s*)?Page\s+\d+\s+of\s+\d+(?:\s*---)?", stripped, flags=re.IGNORECASE):
            continue
        if stripped.lower().startswith("extraction note:"):
            continue

        is_blank = not stripped
        if is_blank and previous_blank:
            continue
        cleaned_lines.append(stripped if stripped else "")
        previous_blank = is_blank

    return "\n".join(cleaned_lines).strip()


def extract_study_sections(text: str) -> list[StudySection]:
    prepared = prepare_study_text(text)
    if not prepared:
        return []

    sections: list[StudySection] = []
    current_title = GENERIC_SECTION_TITLE
    current_lines: list[str] = []

    for raw_line in prepared.splitlines():
        line = raw_line.strip()
        if _looks_like_heading(line):
            _append_section(sections, current_title, current_lines)
            current_title = _clean_heading(line)
            current_lines = []
            continue
        current_lines.append(line)

    _append_section(sections, current_title, current_lines)
    return sections


def build_study_context(text: str, focus_topics: list[str] | None = None) -> str:
    sections = extract_study_sections(text)
    if not sections:
        return prepare_study_text(text)

    parts = []
    if focus_topics:
        topics = ", ".join(normalize_inline_text(topic) for topic in focus_topics if normalize_inline_text(topic))
        if topics:
            parts.append(f"Review Focus Topics: {topics}")

    for section in sections:
        parts.append(f"Section: {section.title}\n{section.content}")
    return "\n\n".join(parts).strip()


def _repeated_noise_lines(lines: list[str]) -> set[str]:
    counts: dict[str, int] = {}
    for line in lines:
        stripped = normalize_inline_text(line)
        if len(stripped) < 4 or len(stripped) > 90:
            continue
        counts[stripped] = counts.get(stripped, 0) + 1
    return {line for line, count in counts.items() if count >= 3}


def _looks_like_heading(line: str) -> bool:
    if not line:
        return False
    cleaned = _clean_heading(line)
    if not cleaned or len(cleaned) > 90:
        return False
    if line.startswith(("#", "##", "###")):
        return True
    if re.match(r"^\(?slide\s+\d+\)?\s+", cleaned, flags=re.IGNORECASE):
        return True
    if re.match(r"^(chapter|section|lecture|unit|module)\s+\d+", cleaned, flags=re.IGNORECASE):
        return True
    if re.match(r"^\d+(?:\.\d+)*\s+[A-Z]", cleaned):
        return True
    if cleaned.endswith(":") and len(cleaned.split()) <= 8:
        return True
    if len(cleaned.split()) <= 6 and not cleaned.endswith((".", "!", "?")) and any(char.isupper() for char in cleaned):
        return True
    return False


def _clean_heading(line: str) -> str:
    return normalize_inline_text(line.strip("# -*\t:"))


def _insert_study_boundaries(text: str) -> str:
    text = re.sub(r"\s*\*{3,}\s*", "\n", text)
    return re.sub(r"(?<!\n)(\(\s*Slide\s+\d+\s*\)\s+)", r"\n\1", text, flags=re.IGNORECASE)


def _append_section(sections: list[StudySection], title: str, lines: list[str]) -> None:
    content = "\n".join(lines).strip()
    if content:
        sections.append(StudySection(title=title, content=content))
