from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
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


@dataclass(frozen=True)
class SourceSection:
    title: str
    content: str
    sentences: list[str]


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


def _source_sections(text: str) -> list[SourceSection]:
    sections: list[SourceSection] = []
    current_title = "Source Notes"
    current_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("review focus topics:"):
            continue
        if lower.startswith("section:"):
            _append_source_section(sections, current_title, current_lines)
            current_title = line.split(":", 1)[1].strip() or "Source Notes"
            current_lines = []
            continue
        if line.startswith("#"):
            _append_source_section(sections, current_title, current_lines)
            current_title = line.strip("# -*\t ") or "Source Notes"
            current_lines = []
            continue
        current_lines.append(line)

    _append_source_section(sections, current_title, current_lines)
    if not sections:
        content = re.sub(r"\s+", " ", text).strip()
        sentences = _sentences(content)
        if content:
            sections.append(SourceSection(title=_first_line(text), content=content, sentences=sentences))
    return sections


def _append_source_section(sections: list[SourceSection], title: str, lines: list[str]) -> None:
    content = re.sub(r"\s+", " ", " ".join(lines)).strip()
    sentences = _sentences(content)
    if content and sentences:
        clean_title = re.sub(r"^Section:\s*", "", title).strip() or "Source Notes"
        sections.append(SourceSection(title=clean_title, content=content, sentences=sentences))


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


def _section_topics(text: str, limit: int = 8) -> list[str]:
    sections = _source_sections(text)
    focus_topics = []
    for line in _meaningful_lines(text):
        if line.lower().startswith("review focus topics:"):
            focus = line.split(":", 1)[1] if ":" in line else ""
            focus_topics.extend(topic.strip() for topic in focus.split(",") if topic.strip())
    topics = focus_topics + [section.title for section in sections if section.title and section.title != "Source Notes"]
    topics.extend(_topics(text, limit=limit * 2))
    seen: set[str] = set()
    unique = []
    for topic in topics:
        cleaned = re.sub(r"^Section:\s*", "", topic).strip()
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)
        if len(unique) >= limit:
            break
    return unique


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


def _section_for_topic(topic: str, sections: list[SourceSection]) -> SourceSection | None:
    topic_words = {word.lower() for word in re.findall(r"\b[A-Za-z][A-Za-z0-9-]{2,}\b", topic)}
    for section in sections:
        title_words = {word.lower() for word in re.findall(r"\b[A-Za-z][A-Za-z0-9-]{2,}\b", section.title)}
        if topic_words & title_words:
            return section
    for section in sections:
        content_words = {word.lower() for word in re.findall(r"\b[A-Za-z][A-Za-z0-9-]{2,}\b", section.content)}
        if topic_words & content_words:
            return section
    return sections[0] if sections else None


def _section_summary(section: SourceSection, max_sentences: int = 2) -> str:
    selected = section.sentences[:max_sentences]
    if not selected:
        return _excerpt(section.content)
    return " ".join(selected)


def _overview_from_sections(sections: list[SourceSection], summary_type: str) -> str:
    names = [section.title for section in sections[:4]]
    if not names:
        return "The uploaded notes contain limited extractable study context."
    topic_text = ", ".join(names[:-1]) + (f", and {names[-1]}" if len(names) > 1 else names[0])
    if summary_type == "exam":
        return f"These notes are organized around {topic_text}. For exam review, focus on likely test points, comparisons with similar concepts, and memorization anchors."
    if summary_type == "detailed":
        return f"These notes cover {topic_text}. This detailed summary emphasizes the general principles and conceptual roles of each topic rather than examples."
    return f"These notes focus on {topic_text}. The concise summary follows the broad flow of the material and highlights the central concepts."


def _concise_point(section: SourceSection) -> str:
    return f"핵심개념 - {section.title}: {_section_summary(section, 1)}"


def _detailed_point(section: SourceSection) -> str:
    return f"개괄설명 - {section.title}: {_section_summary(section, 2)}"


def _exam_points(sections: list[SourceSection]) -> list[str]:
    points: list[str] = []
    for index, section in enumerate(sections[:4]):
        detail = _section_summary(section, 2)
        points.append(f"출제 포인트 - {section.title}: {detail}")
        if len(sections) > 1:
            other = sections[(index + 1) % len(sections)]
            points.append(f"유사개념 비교 - {section.title} vs {other.title}: distinguish the source claim about {section.title} from the source claim about {other.title}.")
        points.append(f"암기 포인트 - {section.title}: remember the terms and relationships stated in this section rather than unsupported examples.")
    return points


def _distractors(topic: str, topics: list[str], sentence: str) -> list[str]:
    alternatives = [candidate for candidate in topics if candidate.lower() != topic.lower()]
    first = alternatives[0] if alternatives else "a nearby concept"
    second = alternatives[1] if len(alternatives) > 1 else "a broader course theme"
    return [
        f"It primarily describes {first}, not the source detail tied to {topic}.",
        f"It adds a stronger claim about {topic} than the uploaded notes support.",
        f"It confuses {topic} with {second} instead of using the cited section.",
    ]


def _conceptual_answer(topic: str, sentence: str) -> str:
    clean = _excerpt(sentence, 150)
    if clean.lower().startswith("section:"):
        clean = clean.split(".", 1)[1].strip() if "." in clean else clean
    return f"{topic} is best understood through this source claim: {clean}"


def _question_for_topic(topic: str, index: int) -> str:
    templates = [
        "Which option best captures how the notes frame {topic}?",
        "What is the most source-grounded interpretation of {topic}?",
        "When reviewing {topic}, which statement should be treated as supported by the notes?",
        "Which answer best connects {topic} to the surrounding study material?",
    ]
    return templates[index % len(templates)].format(topic=topic)


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
        sections = _source_sections(document_text)
        topics = _section_topics(document_text)
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

        if summary_type == "exam":
            key_points = _exam_points(sections)
        elif summary_type == "detailed":
            key_points = [_detailed_point(section) for section in sections[:8]]
        else:
            key_points = [_concise_point(section) for section in sections[:8]]
        if not key_points:
            key_points = sentences[:6] or ["The source material is limited; review the original document for more detail."]

        key_terms = []
        for topic in topics[:8]:
            section = _section_for_topic(topic, sections)
            definition = _section_summary(section, 2) if section else _best_sentence_for_topic(topic, sentences)
            key_terms.append({"term": topic, "definition": definition})

        return {
            "title": f"{title} ({summary_type.title()} Summary)",
            "overview": _overview_from_sections(sections, summary_type),
            "key_points": key_points[:6],
            "key_terms": key_terms[:6],
            "source_quotes": [
                {"quote": _excerpt(_section_summary(section, 1)), "reason": f"Representative source detail for {section.title}."}
                for section in (sections[:3] or [])
            ],
        }

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        sentences = _sentences(document_text)
        sections = _source_sections(document_text)
        topics = _section_topics(document_text, limit=max(count, 6))
        cards: list[dict[str, Any]] = []
        insufficient = _is_insufficient(document_text)

        for index in range(count):
            topic = topics[index % len(topics)] if topics else f"Concept {index + 1}"
            section = _section_for_topic(topic, sections)
            sentence = _section_summary(section, 2) if section else _best_sentence_for_topic(topic, sentences)
            difficulty = ["easy", "medium", "hard"][index % 3]
            front_templates = [
                f"How would you explain {topic} using the uploaded notes?",
                f"What role does {topic} play in this material?",
                f"What should you compare or watch for when reviewing {topic}?",
            ]
            cards.append(
                {
                    "front": front_templates[index % len(front_templates)],
                    "back": "The uploaded material is too short for a reliable card." if insufficient else sentence,
                    "topic": topic,
                    "difficulty": difficulty,
                    "source_quote": _excerpt(sentence if not insufficient else document_text),
                }
            )
        return cards

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        sentences = _sentences(document_text)
        sections = _source_sections(document_text)
        topics = _section_topics(document_text, limit=max(question_count, 6))
        questions: list[dict[str, Any]] = []
        insufficient = _is_insufficient(document_text)

        for index in range(question_count):
            topic = topics[index % len(topics)] if topics else f"Concept {index + 1}"
            section = _section_for_topic(topic, sections)
            sentence = _section_summary(section, 2) if section else _best_sentence_for_topic(topic, sentences)
            correct_letter = ["A", "B", "C", "D"][index % 4]
            correct_choice_text = "The source is too limited to support a detailed answer." if insufficient else _conceptual_answer(topic, sentence)
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
                    "question": _question_for_topic(topic, index),
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
            "concise": (
                "Focus on core concepts and the broad flow of the material. "
                "Do not over-explain details; show how the major ideas connect."
            ),
            "detailed": (
                "Give a general conceptual explanation of the ideas covered in the source. "
                "Prioritize principles, definitions, mechanisms, and relationships over examples."
            ),
            "exam": (
                "Organize the output around likely test points, comparisons with similar concepts, "
                "and memorization anchors. Make exam-facing distinctions explicit."
            ),
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
            "- For concise summaries, emphasize core concepts and the big-picture flow.\n"
            "- For detailed summaries, explain the concepts at a general theoretical level and avoid centering the output on examples.\n"
            "- For exam summaries, include key_points labeled or phrased as test points, similar-concept comparisons, and memorization points.\n"
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
