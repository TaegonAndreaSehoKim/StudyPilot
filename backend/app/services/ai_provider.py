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


TOPIC_WORD_STOP = {
    "slide",
    "section",
    "source",
    "notes",
    "note",
    "chunk",
    "overview",
    "study",
    "core",
    "concept",
}


def _meaningful_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        clean = line.strip("# -*\t ")
        if len(clean) > 2:
            lines.append(clean)
    return lines


def _first_line(text: str) -> str:
    for line in _meaningful_lines(text):
        return re.sub(r"^Section:\s*", "", line, flags=re.IGNORECASE)[:80]
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
        "core",
        "chunk",
        "overview",
        "slide",
        "section",
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


def _looks_like_meta_summary(*parts: str) -> bool:
    text = " ".join(part for part in parts if isinstance(part, str)).lower()
    if not text:
        return False
    meta_phrases = (
        "source notes",
        "uploaded notes",
        "uploaded course notes",
        "chunk 1",
        "chunk 2",
        "chunk 3",
        "chunk 4",
        "study material",
    )
    if any(phrase in text for phrase in meta_phrases):
        return True
    if re.fullmatch(r"(chunk|overview|section|slide|source|notes)[\s:.\-]*", text.strip()):
        return True
    return False


def _best_sentence_for_topic(topic: str, sentences: list[str]) -> str:
    topic_words = _topic_words(topic)
    if not topic_words:
        return sentences[0] if sentences else "The uploaded source text is limited."
    for sentence in sentences:
        sentence_words = _topic_words(sentence)
        if topic_words & sentence_words:
            return sentence
    return sentences[0] if sentences else "The uploaded source text is limited."


def _section_for_topic(topic: str, sections: list[SourceSection]) -> SourceSection | None:
    topic_words = _topic_words(topic)
    if not topic_words:
        return sections[0] if sections else None
    best_title_match: tuple[int, SourceSection] | None = None
    for section in sections:
        title_words = _topic_words(section.title)
        score = len(topic_words & title_words)
        if score and (best_title_match is None or score > best_title_match[0]):
            best_title_match = (score, section)
    if best_title_match:
        return best_title_match[1]

    best_content_match: tuple[int, SourceSection] | None = None
    for section in sections:
        content_words = _topic_words(section.content)
        score = len(topic_words & content_words)
        if score and (best_content_match is None or score > best_content_match[0]):
            best_content_match = (score, section)
    if best_content_match:
        return best_content_match[1]
    return sections[0] if sections else None


def _topic_words(text: str) -> set[str]:
    return {
        word.lower()
        for word in re.findall(r"\b[A-Za-z][A-Za-z0-9-]{2,}\b", text)
        if word.lower() not in TOPIC_WORD_STOP
    }


def _section_summary(section: SourceSection, max_sentences: int = 2) -> str:
    selected = _study_sentences(section.sentences)[:max_sentences]
    if not selected:
        return _excerpt(section.content)
    return " ".join(selected)


def _study_sentences(sentences: list[str]) -> list[str]:
    filler_prefixes = (
        "let's discuss",
        "let's take",
        "now let's",
        "now here's",
        "here's",
        "so here",
    )
    filtered = []
    for sentence in sentences:
        normalized = sentence.lower().replace("’", "'").lstrip()
        if normalized.startswith(filler_prefixes):
            continue
        filtered.append(sentence)
    return filtered or sentences


def _overview_from_sections(sections: list[SourceSection], summary_type: str) -> str:
    names = [section.title for section in sections[:4]]
    if not names:
        return "The uploaded notes contain limited extractable study context."
    topic_text = ", ".join(names[:-1]) + (f", and {names[-1]}" if len(names) > 1 else names[0])
    concrete_flow = " ".join(_section_summary(section, 1) for section in sections[:2])
    if summary_type == "exam":
        return (
            f"These notes are organized around {topic_text}. For exam review, use the summary to identify "
            f"test points, testable definitions, exceptions, comparisons, and memorization anchors. {concrete_flow}"
        )
    if summary_type == "detailed":
        return (
            f"These notes cover {topic_text}. This detailed summary explains the general principles, "
            f"conceptual roles, and relationships needed to study without rereading the full source. {concrete_flow}"
        )
    return (
        f"These notes focus on {topic_text}. The concise summary follows the broad flow of the material "
        f"while still explaining the central concepts in study-ready form. {concrete_flow}"
    )


def _concise_point(section: SourceSection) -> str:
    return f"Core concept - {section.title}: {_section_summary(section, 2)}"


def _detailed_point(section: SourceSection) -> str:
    return f"Concept overview - {section.title}: {_section_summary(section, 3)}"


def _exam_points(sections: list[SourceSection]) -> list[str]:
    points: list[str] = []
    for index, section in enumerate(sections[:4]):
        detail = _section_summary(section, 2)
        points.append(f"Test point - {section.title}: {detail}")
        if len(sections) > 1:
            other = sections[(index + 1) % len(sections)]
            points.append(
                f"Similar concept comparison - {section.title} vs {other.title}: "
                f"distinguish the source claim about {section.title} from the source claim about {other.title}."
            )
        points.append(
            f"Memorization point - {section.title}: "
            "remember the terms and relationships stated in this section rather than unsupported examples."
        )
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
        if self._valid_summary(data):
            return data
        return self.fallback.generate_summary(document_text, summary_type)

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        prompt = self._flashcard_prompt(document_text, count)
        data = self._json_response(prompt)
        cards = data.get("flashcards") if isinstance(data, dict) else data
        if self._valid_flashcards(cards):
            return cards[:count]
        return self.fallback.generate_flashcards(document_text, count)

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        prompt = self._quiz_prompt(document_text, question_count, difficulty)
        data = self._json_response(prompt)
        if self._valid_quiz(data):
            return data
        return self.fallback.generate_quiz(document_text, question_count, difficulty)

    def _valid_summary(self, value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        if not all(isinstance(value.get(key), str) and value[key].strip() for key in ("title", "overview")):
            return False
        if _looks_like_meta_summary(value["title"], value["overview"]):
            return False
        overview = value["overview"].strip()
        if len(overview) < 120:
            return False
        if not isinstance(value.get("key_points"), list) or len(value["key_points"]) < 3:
            return False
        if not all(isinstance(point, str) and len(point.strip()) >= 60 for point in value["key_points"]):
            return False
        if any(_looks_like_meta_summary(point) for point in value["key_points"]):
            return False
        key_terms = value.get("key_terms")
        if not isinstance(key_terms, list) or len(key_terms) < 3:
            return False
        for item in key_terms:
            if not isinstance(item, dict):
                return False
            if not all(isinstance(item.get(key), str) and item[key].strip() for key in ("term", "definition")):
                return False
            if _looks_like_meta_summary(item["term"]):
                return False
        source_quotes = value.get("source_quotes")
        if not isinstance(source_quotes, list) or len(source_quotes) < 2:
            return False
        for item in source_quotes:
            if not isinstance(item, dict):
                return False
            if not all(isinstance(item.get(key), str) and item[key].strip() for key in ("quote", "reason")):
                return False
        return True

    def _valid_flashcards(self, value: Any) -> bool:
        if not isinstance(value, list) or not value:
            return False
        required = {"front", "back", "topic", "difficulty", "source_quote"}
        for item in value:
            if not isinstance(item, dict):
                return False
            if not all(isinstance(item.get(key), str) and item[key].strip() for key in required):
                return False
            if item["difficulty"] not in {"easy", "medium", "hard"}:
                return False
        return True

    def _valid_quiz(self, value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        if not isinstance(value.get("title"), str) or not value["title"].strip():
            return False
        questions = value.get("questions")
        if not isinstance(questions, list) or not questions:
            return False
        required = {"question", "choices", "correct_answer", "explanation", "topic", "difficulty"}
        text_fields = required - {"choices"}
        for item in questions:
            if not isinstance(item, dict):
                return False
            if not all(key in item for key in required):
                return False
            if not all(isinstance(item.get(key), str) and item[key].strip() for key in text_fields):
                return False
            if item["correct_answer"] not in {"A", "B", "C", "D"}:
                return False
            if item["difficulty"] not in {"easy", "medium", "hard"}:
                return False
            if not isinstance(item["choices"], list) or len(item["choices"]) != 4:
                return False
            if not all(isinstance(choice, str) and choice.strip() for choice in item["choices"]):
                return False
        return True

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
                "Rewrite the source into a compact teaching explanation. Focus on the core concepts, the broad "
                "flow of the argument, and the minimum details needed to understand the material without rereading it."
            ),
            "detailed": (
                "Rewrite the source as a conceptual study guide. Explain the principles, definitions, mechanisms, "
                "relationships, assumptions, and consequences in your own words. Use examples only after explaining "
                "the underlying idea."
            ),
            "exam": (
                "Rewrite the source for exam preparation. Emphasize likely test points, definitions that must be "
                "memorized, comparisons with similar concepts, exceptions, failure cases, and common confusions."
            ),
        }.get(summary_type, "Write a source-grounded study summary.")
        return (
            "You are StudyPilot's study-note writer.\n"
            "Your job is not to make a thin abstract. Your job is to read the source and re-explain the content and concepts in your own words.\n"
            "The result must be self-contained enough that a student can study from the generated notes without opening the original source for first-pass review.\n"
            "Return only a valid JSON object with keys: title, overview, key_points, key_terms, source_quotes.\n"
            "Rules:\n"
            "- Use only facts supported by the notes.\n"
            "- Reorganize the explanation when it helps learning, but do not invent facts beyond the source.\n"
            "- Preserve section structure when useful, but explain the concepts instead of merely listing section titles or transcript order.\n"
            "- If notes are insufficient, say that explicitly.\n"
            "- Do not write vague meta summaries such as 'these notes discuss...' without explaining the actual ideas.\n"
            "- Do not use Chunk, Source Notes, uploaded notes, section, or slide as key concepts unless those are actual source concepts.\n"
            "- overview must be 3-5 sentences that teach the main topic, the conceptual flow, and the major conclusions.\n"
            "- key_points must contain 5-8 study-ready teaching notes. Each point must explain a concept in your own words, include the source's important conditions or exceptions, and state why the idea matters.\n"
            "- key_terms must contain 5-10 concrete terms with source-grounded definitions written as if teaching a student, not as dictionary fragments.\n"
            "- source_quotes must contain 3-5 short snippets copied from the notes with a reason for each quote.\n"
            "- Include constraints, exceptions, comparisons, or failure cases when the source contains them.\n"
            "- Prefer explanatory phrases like 'This means...', 'The reason this matters is...', and 'The key distinction is...' when they make the concept clearer.\n"
            "- Avoid copying long source sentences into key_points. Quotes belong only in source_quotes.\n"
            "- For concise summaries, create a compact conceptual rewrite with the big-picture flow and enough detail to study from.\n"
            "- For detailed summaries, create a deeper teaching explanation of concepts, principles, relationships, and assumptions.\n"
            "- For exam summaries, label or phrase key_points as test points, similar-concept comparisons, exception/failure cases, and memorization anchors.\n"
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
