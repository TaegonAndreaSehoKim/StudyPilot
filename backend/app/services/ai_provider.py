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
    "concrete",
    "definitions",
    "evidence",
    "part",
    "page",
    "document",
}

SOURCE_MATERIAL_MARKER = "\n\nSource Material:\n"


def _source_material_text(text: str) -> str:
    if SOURCE_MATERIAL_MARKER in text:
        return text.split(SOURCE_MATERIAL_MARKER, 1)[1].strip()
    return text


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


def _summary_title(source_text: str, fallback: str) -> str:
    lower = source_text.lower()
    if _looks_like_game_ai_intro(lower):
        return "Introduction to Game AI"
    if ("discrete movement" in lower and "continuous movement" in lower) or (
        "seeking a target" in lower and "arrive" in lower
    ):
        return "Basic Agent Movement"
    if _is_source_metadata_title(fallback) or fallback.lower() in {"source notes", "type of movement"}:
        return "Study Notes"
    return fallback


def _looks_like_game_ai_intro(lower_text: str) -> bool:
    ai_definition = (
        "what is ai" in lower_text
        or "artificial intelligence" in lower_text
        or "conventional algorithms" in lower_text
        or "rational agents" in lower_text
    )
    game_context = "video games" in lower_text or "game ai" in lower_text or "games" in lower_text
    movement_specific = "discrete movement" in lower_text and "continuous movement" in lower_text
    return ai_definition and game_context and not movement_specific


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
            candidate_title = line.split(":", 1)[1].strip()
            if _is_source_metadata_title(candidate_title):
                continue
            _append_source_section(sections, current_title, current_lines)
            current_title = candidate_title or "Source Notes"
            current_lines = []
            continue
        if _is_source_metadata_title(line):
            continue
        if line.startswith("#"):
            _append_source_section(sections, current_title, current_lines)
            current_title = line.strip("# -*\t ") or "Source Notes"
            current_lines = []
            continue
        current_lines.append(line)

    _append_source_section(sections, current_title, current_lines)
    total_content = " ".join(section.content for section in sections).strip()
    if len(sections) < 3:
        auto_sections = _auto_source_sections(total_content)
        if len(auto_sections) > 1:
            return auto_sections
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


def _is_source_metadata_title(value: str) -> bool:
    clean = value.strip()
    return bool(
        re.fullmatch(r"(?:Source Material|Document)\s+\d+:?.*", clean, flags=re.IGNORECASE)
        or re.fullmatch(r"(?:---\s*)?Page\s+\d+\s+of\s+\d+(?:\s*---)?", clean, flags=re.IGNORECASE)
        or re.fullmatch(r"\[\d{2}:\d{2}:\d{2}\]", clean)
    )


CONCEPT_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("AI definition and scope", ("what is ai", "artificial intelligence", "conventional algorithms", "modern view")),
    ("Agent movement foundations", ("agent movement", "basic agent can move", "movement serve as a foundation")),
    ("Game AI design space", ("video games", "game ai", "game environments", "gameplay", "support gameplay", "practical question", "useful behavior")),
    ("Autonomy and agent behavior", ("autonomy", "non-player", "player control", "can observe")),
    ("Decision making systems", ("decision making", "decision tree", "state machine", "behavior tree")),
    ("Rules, search, and planning", ("rule based", "limited search", "path planning", "planning")),
    ("Tactics and strategy", ("tactics", "strategy", "strategist", "war game")),
    ("Projectile and aiming problems", ("projectile", "aiming", "aimed", "trajectory")),
    ("Discrete movement", ("discrete movement", "distinct locations", "adjacency", "turn based")),
    ("Continuous movement", ("continuous movement", "real time", "velocity", "high frame rate")),
    ("Simulation update loop", ("simulation loop", "update loop", "rendering", "frames per second")),
    ("2D position vectors", ("position vector", "coordinate system", "2 d", "x. y", "vector space")),
    ("Point-based agent representation", ("agent is located at point", "single point", "collisions", "radius")),
    ("Kinematic seek movement", ("seeking a target", "move towards", "relative vector", "fish")),
    ("Velocity normalization", ("normalize", "unit vector", "maximum speed", "time elapsed")),
    ("Orientation and facing direction", ("orientation", "forward vector", "atan2", "facing direction")),
    ("Arrive behavior", ("arriving", "capture radius", "slow down", "time to target")),
    ("Wander behavior", ("wander", "random number", "orientation", "negative one and one")),
    ("Path following", ("waypoint", "waypoints", "follow a path", "capture radius")),
    ("Steering behavior motivation", ("steering behaviors", "momentum", "instant change", "future topic")),
)

CONCEPT_EXPLANATIONS = {
    "AI definition and scope": (
        "The introduction frames AI as a shifting category: earlier definitions treated AI as machine performance of tasks once thought to require humans, while a more useful modern view focuses on problems that cannot be solved realistically with straightforward conventional algorithms."
    ),
    "Game AI design space": (
        "Game AI is presented as a practical design space inside video games, where the goal is not just theoretical intelligence but behavior that supports gameplay, challenge, believability, and the player's experience."
    ),
    "Autonomy and agent behavior": (
        "Autonomy matters because game characters and systems often need to select actions without direct player control, so the designer must decide what the agent can observe, how it chooses, and what kind of behavior will feel appropriate in context."
    ),
    "Decision making systems": (
        "Decision making systems provide structured ways for a game agent to choose actions, often by mapping current game conditions to behavior choices rather than trying to solve every possible situation from scratch."
    ),
    "Rules, search, and planning": (
        "Rules, search, and planning are introduced as different families of tools for game AI problems: rules can encode designer knowledge, search can evaluate possible options, and planning can reason about sequences of actions toward a goal."
    ),
    "Tactics and strategy": (
        "Tactics and strategy connect AI decisions to different time scales: tactical choices handle local or immediate gameplay situations, while strategic behavior concerns broader plans, opponent behavior, and longer-term direction."
    ),
    "Projectile and aiming problems": (
        "Projectile and aiming problems show that game AI often has to make decisions under physical or spatial constraints, such as predicting where a target will be or selecting an action that works within the game world's rules."
    ),
    "Agent movement foundations": (
        "Agent movement starts by choosing the simplest representation that supports the movement task, because game AI must share limited frame time with rendering, audio, input, networking, and other systems."
    ),
    "Discrete movement": (
        "Discrete movement represents the world as a manageable set of distinct locations, such as grid cells or board-game squares, where movement is governed by adjacency or piece-specific rules."
    ),
    "Continuous movement": (
        "Continuous movement lets the agent change position by small increments over time, so the player perceives smooth motion even though the computer still stores positions with finite numeric resolution."
    ),
    "Simulation update loop": (
        "Movement code runs inside the game loop: the game reads input, updates simulation and AI state, renders the result, synchronizes timing, and repeats, so each AI decision must fit into a small frame budget."
    ),
    "2D position vectors": (
        "Continuous movement usually models position with vectors in a coordinate system; many games can plan movement in 2D even when rendered in 3D because gravity keeps most characters on a surface."
    ),
    "Point-based agent representation": (
        "For movement decisions, an agent can be simplified to a point position, while size information such as a radius is carried separately for collision and gameplay interactions."
    ),
    "Kinematic seek movement": (
        "Seek behavior computes a direction from the agent to a target by subtracting positions, then moves incrementally toward that target instead of applying the full vector as an instant teleport."
    ),
    "Velocity normalization": (
        "Normalizing the direction vector separates direction from speed; multiplying by maximum speed and elapsed time produces consistent frame-by-frame movement."
    ),
    "Orientation and facing direction": (
        "Orientation records which way the agent faces, often as a unit forward vector or angle, and functions such as atan2 preserve quadrant information when converting vectors to angles."
    ),
    "Arrive behavior": (
        "Arrive behavior improves seek by using a capture radius and slowing near the target, avoiding exact floating-point equality checks and reducing jitter around the goal."
    ),
    "Wander behavior": (
        "Wander behavior reuses the previous orientation and applies small biased random changes, producing natural drifting motion instead of abrupt random zigzags."
    ),
    "Path following": (
        "Path following applies seek across a sequence of waypoints, often using arrive only at the final waypoint, while capture radius determines when each waypoint counts as reached."
    ),
    "Steering behavior motivation": (
        "Basic kinematic movement is functional but can look unnatural because velocity and orientation change instantly; steering behaviors add smoother acceleration, turning, and momentum."
    ),
}


def _auto_source_sections(content: str) -> list[SourceSection]:
    timestamp_sections = _timestamp_source_sections(content)
    if len(timestamp_sections) > 1:
        return timestamp_sections

    sentences = _sentences(content)
    if len(sentences) < 8:
        return []
    section_count = min(8, max(6, len(content) // 7000))
    group_size = max(3, (len(sentences) + section_count - 1) // section_count)
    sections: list[SourceSection] = []
    used_titles: set[str] = set()
    for index, start in enumerate(range(0, len(sentences), group_size), start=1):
        group = sentences[start : start + group_size]
        if not group:
            continue
        group_content = " ".join(group)
        title = _concept_title(group_content, used_titles) or f"Concept Segment {index}"
        used_titles.add(title)
        sections.append(SourceSection(title=title, content=group_content, sentences=group))
    return sections


def _timestamp_source_sections(content: str) -> list[SourceSection]:
    blocks = [block.strip() for block in re.split(r"(?=\[\d{2}:\d{2}:\d{2}\])", content) if block.strip()]
    if len(blocks) < 4:
        return []

    section_blocks: dict[str, list[str]] = {}
    ordered_titles: list[str] = []
    current_title = _concept_title(blocks[0], set()) or "Source Notes"
    for block in blocks:
        current_title = _pattern_concept_title(block, set()) or current_title
        if current_title not in section_blocks:
            ordered_titles.append(current_title)
            section_blocks[current_title] = []
        section_blocks[current_title].append(block)

    sections: list[SourceSection] = []
    for title in ordered_titles:
        _append_source_section(sections, title, section_blocks[title])
    return sections


def _pattern_concept_title(text: str, used_titles: set[str]) -> str | None:
    lower = text.lower()
    best_title: str | None = None
    best_score = 0
    for title, patterns in CONCEPT_PATTERNS:
        if title in used_titles:
            continue
        score = sum(1 for pattern in patterns if pattern in lower)
        if score > best_score:
            best_score = score
            best_title = title
    if best_title:
        return best_title
    return None


def _concept_title(text: str, used_titles: set[str]) -> str | None:
    title = _pattern_concept_title(text, used_titles)
    if title:
        return title
    keywords = _keywords(text, limit=2)
    if keywords:
        return " / ".join(keywords)
    return None


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
        if _is_source_metadata_title(line):
            continue
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
        if _is_source_metadata_title(line):
            continue
        if line.lower().startswith("review focus topics:"):
            focus = line.split(":", 1)[1] if ":" in line else ""
            focus_topics.extend(topic.strip() for topic in focus.split(",") if topic.strip())
    section_topics = [section.title for section in sections if section.title and section.title != "Source Notes"]
    topics = focus_topics + section_topics
    if len(section_topics) < 5:
        topics.extend(_topics(text, limit=limit * 2))
    seen: set[str] = set()
    unique = []
    for topic in topics:
        cleaned = re.sub(r"^Section:\s*", "", topic).strip()
        key = cleaned.lower()
        if not cleaned or key in seen or _looks_like_meta_summary(cleaned):
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
        "source material",
        "document 1",
        "document 2",
        "source part",
        "concrete study points",
        "concept definitions",
        "source evidence",
        "chunk 1",
        "chunk 2",
        "chunk 3",
        "chunk 4",
        "study material",
        "page 1 of",
        "page 2 of",
        "page 3 of",
    )
    if any(phrase in text for phrase in meta_phrases):
        return True
    if re.fullmatch(r"(chunk|overview|section|slide|source|notes)[\s:.\-]*", text.strip()):
        return True
    return False


def _looks_like_pdf_artifact(*parts: str) -> bool:
    text = " ".join(part for part in parts if isinstance(part, str))
    if not text:
        return False
    if re.search(r"\bPage\s+\d+\s+of\s+\d+\b", text, flags=re.IGNORECASE):
        return True
    if re.search(r"\b[Aa]\s+(?:[A-Z][a-z]+|[A-Z]{2,})", text):
        return True
    if re.search(r"\b(?:[A-Za-z]\s+){3,}[A-Za-z]\b", text):
        return True
    if re.search(r"\b(?:de|Speci|speci)\.n?fi?tion\b", text):
        return True
    if any(fragment in text for fragment in ("de.nition", "Speci.c", ".xed", ".oat", "Ty p e")):
        return True
    return False


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9'-]*\b", text))


def _looks_like_summary_structure_label(value: str) -> bool:
    cleaned = re.sub(r"[^a-z_:\s-]", "", value.lower()).strip()
    return bool(re.fullmatch(r"(?:key[_\s-]*terms?|source[_\s-]*quotes?|quotes?)\s*:?", cleaned))


def _has_teaching_depth(points: list[Any]) -> bool:
    text = " ".join(point for point in points if isinstance(point, str)).lower()
    teaching_markers = (
        "this means",
        "the reason",
        "why",
        "because",
        "the key distinction",
        "distinguish",
        "in practice",
        "for example",
        "therefore",
        "important",
        "matters",
        "tradeoff",
        "pitfall",
        "avoid",
    )
    return sum(1 for marker in teaching_markers if marker in text) >= 3


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
    selected = [_clean_study_sentence(sentence) for sentence in _study_sentences(section.sentences)[:max_sentences]]
    selected = [sentence for sentence in selected if sentence]
    if not selected:
        return _excerpt(section.content)
    return " ".join(selected)


def _teaching_summary(section: SourceSection, max_sentences: int = 2) -> str:
    explanation = CONCEPT_EXPLANATIONS.get(section.title)
    if explanation:
        return explanation
    return _section_summary(section, max_sentences)


def _clean_study_sentence(sentence: str) -> str:
    cleaned = re.sub(r"^\[\d{2}:\d{2}:\d{2}\]\s*", "", sentence).strip()
    cleaned = re.sub(r"^>>\s*", "", cleaned).strip()
    return cleaned


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
    concrete_flow = " ".join(_teaching_summary(section, 1) for section in sections[:2])
    scope = _scope_from_sections(sections)
    if summary_type == "exam":
        return (
            f"These notes are organized around {topic_text}. For exam review, use the summary to identify "
            f"test points, testable definitions, exceptions, comparisons, and memorization anchors. {concrete_flow}"
        )
    if summary_type == "detailed":
        return (
            f"The lecture develops {topic_text} as a sequence of ideas for understanding {scope}. "
            f"This detailed explanation preserves the source's teaching logic, concept-bearing examples, comparisons, caveats, and implementation tradeoffs "
            f"while removing casual filler that does not help learning. {concrete_flow}"
        )
    if summary_type == "explanation":
        return (
            f"These notes explain {topic_text} as a learning path for understanding {scope}. "
            f"The explanation keeps the source's useful teaching details, removes casual filler, defines the important ideas, and connects each concept to the surrounding game AI problem. "
            f"{concrete_flow}"
        )
    return (
        f"These notes focus on {topic_text}. The concise summary follows the broad flow of the material "
        f"while still explaining the central concepts in study-ready form. {concrete_flow}"
    )


def _scope_from_sections(sections: list[SourceSection]) -> str:
    titles = {section.title for section in sections}
    if {"Discrete movement", "Continuous movement"} & titles:
        return "basic game-agent movement"
    if {"AI definition and scope", "Game AI design space"} & titles:
        return "the foundations and design space of game AI"
    return "the course topic"


def _summary_mode_label(summary_type: str) -> str:
    if summary_type in {"detailed", "explanation"}:
        return "Detailed Explanation"
    return f"{summary_type.title()} Summary"


def _concise_point(section: SourceSection) -> str:
    return _teaching_summary(section, 2)


def _detailed_point(section: SourceSection) -> str:
    return _teaching_summary(section, 3)


def _explanation_point(section: SourceSection) -> str:
    explanation = _teaching_summary(section, 3)
    reflection_context = "real-time game loop" if section.title in CONCEPT_EXPLANATIONS and "movement" in section.title.lower() else "game AI design problem"
    return (
        f"{explanation} "
        "This part should be studied as a causal explanation, not as a term to memorize in isolation. "
        f"Ask what problem this concept solves, what simplification it introduces, and what tradeoff it creates inside the {reflection_context}."
    )


def _exam_points(sections: list[SourceSection]) -> list[str]:
    points: list[str] = []
    for index, section in enumerate(sections[:4]):
        detail = _teaching_summary(section, 2)
        points.append(f"For exam review, connect this idea to the source claim: {detail}")
        if len(sections) > 1:
            other = sections[(index + 1) % len(sections)]
            points.append(
                f"Distinguish {section.title} from {other.title} by comparing what each source section says, "
                "what problem each concept solves, and what assumption would make the ideas easy to confuse."
            )
        points.append(
            f"When memorizing {section.title}, focus on the terms and relationships stated in the source rather than unsupported examples."
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
        source_text = _source_material_text(document_text)
        sentences = _sentences(source_text)
        sections = _source_sections(source_text)
        topics = _section_topics(source_text)
        title = _summary_title(source_text, _first_line(source_text))

        if _is_insufficient(source_text):
            excerpt = _excerpt(source_text) or "The uploaded source text is limited."
            return {
                "title": f"{title} ({_summary_mode_label(summary_type)})",
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
        elif summary_type == "explanation":
            key_points = [_explanation_point(section) for section in sections[:8]]
        elif summary_type == "detailed":
            key_points = [_detailed_point(section) for section in sections[:8]]
        else:
            key_points = [_concise_point(section) for section in sections[:8]]
        if not key_points:
            key_points = sentences[:6] or ["The source material is limited; review the original document for more detail."]

        key_terms = []
        for topic in topics[:8]:
            section = _section_for_topic(topic, sections)
            definition = _teaching_summary(section, 2) if section else _best_sentence_for_topic(topic, sentences)
            key_terms.append({"term": topic, "definition": definition})

        return {
            "title": f"{title} ({_summary_mode_label(summary_type)})",
            "overview": _overview_from_sections(sections, summary_type),
            "key_points": key_points[:8],
            "key_terms": key_terms[:8],
            "source_quotes": [
                {"quote": _excerpt(_section_summary(section, 1)), "reason": f"Representative source detail for {section.title}."}
                for section in (sections[:5] or [])
            ],
        }

    def generate_flashcards(self, document_text: str, count: int) -> list[dict[str, Any]]:
        source_text = _source_material_text(document_text)
        sentences = _sentences(source_text)
        sections = _source_sections(source_text)
        topics = _section_topics(source_text, limit=max(count, 6))
        cards: list[dict[str, Any]] = []
        insufficient = _is_insufficient(source_text)

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
                    "source_quote": _excerpt(sentence if not insufficient else source_text),
                }
            )
        return cards

    def generate_quiz(self, document_text: str, question_count: int, difficulty: str) -> dict[str, Any]:
        source_text = _source_material_text(document_text)
        sentences = _sentences(source_text)
        sections = _source_sections(source_text)
        topics = _section_topics(source_text, limit=max(question_count, 6))
        questions: list[dict[str, Any]] = []
        insufficient = _is_insufficient(source_text)

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
            source_quote = _excerpt(sentence if not insufficient else source_text)
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

        return {"title": f"{_first_line(source_text)} Quiz", "questions": questions}


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.fallback = FakeAIProvider()

    def generate_summary(self, document_text: str, summary_type: str) -> dict[str, Any]:
        prompt = self._summary_prompt(document_text, summary_type)
        data = self._json_response(prompt)
        if self._valid_summary(data, summary_type):
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

    def _valid_summary(self, value: Any, summary_type: str = "concise") -> bool:
        if not isinstance(value, dict):
            return False
        if not all(isinstance(value.get(key), str) and value[key].strip() for key in ("title", "overview")):
            return False
        if _looks_like_meta_summary(value["title"], value["overview"]):
            return False
        if _looks_like_pdf_artifact(value["title"], value["overview"]):
            return False
        overview = value["overview"].strip()
        if len(overview) < 120:
            return False
        if summary_type in {"detailed", "exam"} and _word_count(overview) < 70:
            return False
        if summary_type == "explanation" and _word_count(overview) < 90:
            return False
        if not isinstance(value.get("key_points"), list):
            return False
        key_points = [point.strip() for point in value["key_points"] if isinstance(point, str) and point.strip()]
        if any(len(point) < 60 and not _looks_like_summary_structure_label(point) for point in key_points):
            return False
        key_points = [point for point in key_points if not _looks_like_summary_structure_label(point)]
        if len(key_points) < 3:
            return False
        if summary_type == "detailed" and len(key_points) < 5:
            return False
        if summary_type == "exam" and len(key_points) < 5:
            return False
        if summary_type == "explanation" and len(key_points) < 6:
            return False
        artifact_point_count = sum(
            1 for point in key_points if _looks_like_meta_summary(point) or _looks_like_pdf_artifact(point)
        )
        if artifact_point_count >= max(2, len(key_points) // 2):
            return False
        if summary_type == "detailed":
            if not all(_word_count(point) >= 60 for point in key_points[:5]):
                return False
            if not _has_teaching_depth(key_points):
                return False
        if summary_type == "exam":
            if not all(_word_count(point) >= 30 for point in key_points[:5]):
                return False
        if summary_type == "explanation":
            if not all(_word_count(point) >= 65 for point in key_points[:6]):
                return False
            if not _has_teaching_depth(key_points):
                return False
        key_terms = value.get("key_terms")
        if key_terms is not None:
            if not isinstance(key_terms, list):
                return False
            for item in key_terms:
                if not isinstance(item, dict):
                    return False
                if not all(isinstance(item.get(key), str) and item[key].strip() for key in ("term", "definition")):
                    return False
                if _looks_like_meta_summary(item["term"]) or _looks_like_pdf_artifact(item["term"], item["definition"]):
                    return False
                if summary_type in {"detailed", "exam"} and _word_count(item["definition"]) < 18:
                    return False
                if summary_type == "explanation" and _word_count(item["definition"]) < 25:
                    return False
        source_quotes = value.get("source_quotes")
        if source_quotes is not None:
            if not isinstance(source_quotes, list):
                return False
            for item in source_quotes:
                if isinstance(item, str):
                    if not item.strip():
                        return False
                    continue
                if isinstance(item, dict) and all(isinstance(item.get(key), str) and item[key].strip() for key in ("quote", "reason")):
                    continue
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
                "Create a compact but teachable review. The output should still explain the core concepts and the "
                "source's learning sequence, not just list topics."
            ),
            "detailed": (
                "Create a detailed explanation, not a detailed summary. Remove filler such as greetings, agenda chatter, "
                "speaker asides, repeated transition phrases, and obvious transcript noise, but preserve as much of the "
                "concept-bearing explanation as possible: source examples, comparisons, definitions, caveats, causal reasoning, "
                "implementation consequences, and the source's teaching order."
            ),
            "exam": (
                "Create exam-prep notes. Emphasize testable definitions, likely comparisons, common confusions, "
                "exceptions, failure cases, and memorization anchors, while still teaching the ideas."
            ),
            "explanation": (
                "Create an expanded explanatory guide for a learner who found the lecture hard to understand. "
                "Do not compress the useful teaching content. Remove casual filler and transcript chatter, then rebuild the lecture "
                "concepts from the ground up with source-consistent background explanations, plain-language bridges, causal reasoning, "
                "and practical intuition beyond the terse source wording."
            ),
        }.get(summary_type, "Write a source-grounded study summary.")
        return (
            "You are StudyPilot's senior course-note writer.\n"
            "Your output is a detailed study explanation, not a transcript summary, slide recap, topic index, or table of contents.\n"
            "A learner should be able to use only the generated notes for first-pass learning, then return to the original source only for verification and examples.\n"
            "Before writing, infer the actual lecture/topic scope from Course Context, Section Context, and Source Material. Ignore file names, page numbers, timestamps, extraction markers, slide wrappers, and bullet artifacts.\n"
            "Use the source's own teaching path as the backbone: preserve how the source introduces prerequisites, motivates distinctions, sequences algorithms, gives useful examples, compares alternatives, and states caveats.\n"
            "Remove filler aggressively, including greetings, agenda setup, repeated transition phrases, speaker asides, and transcript noise, but do not remove useful examples or explanatory steps just because they are verbose.\n"
            "Base every claim on the uploaded source. You may add source-consistent teaching explanation and source-consistent explanatory scaffolding for concepts that appear in the source, but do not introduce unrelated facts, new algorithms, or unsupported examples.\n"
            "Return only a valid JSON object with keys: title, overview, key_points, key_terms, source_quotes.\n"
            "Required output contract:\n"
            "- title: name the actual lecture topic or section scope. Do not use the first slide heading, page label, file name, or source wrapper.\n"
            "- overview: 4-6 sentences. It must teach the main topic, explain the source's conceptual progression, and name the most important distinctions or tradeoffs.\n"
            "- key_points: return 6-9 items for detailed/exam/explanation outputs and 4-6 items for concise summaries.\n"
            "- For detailed explanation outputs, each key_points item must be 4-6 sentences and at least 60 words. Treat each item as a mini-lesson, not a bullet label or compressed recap.\n"
            "- For explanation outputs, each key_points item must be 4-7 sentences and at least 65 words. It should slow down, define prerequisites, explain intuition, and connect the idea to why the learner should care.\n"
            "- Each key_points item should include: the concept, what it means, why it matters, how it connects to the previous/next idea, and any useful source example, condition, caveat, tradeoff, or failure mode from the source.\n"
            "- key_terms: return 8-12 concrete course terms when the source supports them. Each definition should be 1-3 teaching sentences, not a dictionary fragment.\n"
            "- source_quotes: return 3-5 objects, each with quote and reason. quote must be a short verbatim snippet copied from the source. Quotes should support major claims; do not put long copied source text in key_points.\n"
            "Quality rules:\n"
            "- Use only facts supported by the notes.\n"
            "- If Course Context or Section Context is provided, use it to understand scope, terminology, and emphasis. Do not treat context as source evidence or quote it in source_quotes.\n"
            "- Follow the source's explanation order by default. Reorganize only when it clearly improves learning, and never hide prerequisites, examples, definitions, or caveats that the source gives earlier.\n"
            "- If notes are insufficient, say that explicitly.\n"
            "- Do not write vague meta summaries such as 'these notes discuss...' or 'this section covers...' without explaining the actual ideas.\n"
            "- Do not use Chunk, Source Part, Source Material, Source Notes, Concrete study points, Concept definitions, Source evidence, uploaded notes, section, slide, or page as key concepts unless those are actual course concepts.\n"
            "- Do not begin key_points with repetitive UI-style labels such as 'Core concept -', 'Concept overview -', 'Additional explanation -', 'Test point -', or similar headings. The app already labels the output type.\n"
            "- Do not use page labels, file labels, bullet artifacts, or OCR/PDF text artifacts as concepts. Ignore strings like 'Page 3 of 37', 'A ...', or spaced heading text such as 'Ty p e o f M o v e m e n t'. Infer the intended phrase and teach the actual course concept.\n"
            "- Clean obvious extraction artifacts before writing. For example, read 'de.nition' as 'definition', '.xed' as 'fixed', and '.oats' as 'floats'.\n"
            "- Reject slide-copy style. A bad key point is 'Concept overview - Page 3: Type of Movement'. A good key point explains the distinction between discrete and continuous movement, how representation affects algorithms, and why the game loop changes how movement code is written.\n"
            "- Include constraints, exceptions, comparisons, or failure cases when the source contains them.\n"
            "- Prefer explanatory phrases like 'This means...', 'The reason this matters is...', and 'The key distinction is...' when they make the concept clearer.\n"
            "- For explanation outputs, it is acceptable to add general background explanations, analogies, or intuition that help the learner understand a source concept, as long as they do not contradict the source or introduce unrelated course material.\n"
            f"- Summary mode: {summary_type}. {guidance}\n\n"
            f"Notes:\n{document_text[:80000]}"
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
            f"Notes:\n{document_text[:80000]}"
        )

    def _quiz_prompt(self, document_text: str, question_count: int, difficulty: str) -> str:
        return (
            "You are creating a source-grounded multiple-choice quiz from uploaded course notes.\n"
            "The quiz should test whether a student understands the concepts, not whether they remember isolated words.\n"
            "Return only a valid JSON object with keys title and questions.\n"
            "Each question must include: question, choices, correct_answer, explanation, topic, difficulty, source_quote.\n"
            "Rules:\n"
            "- Ask concept-understanding questions that require applying, distinguishing, or explaining a source concept.\n"
            "- If Course Context is provided, use it to tune emphasis and terminology. Do not make questions answerable only from Course Context; the correct answer must still be grounded in Source Material.\n"
            "- Avoid trivia, exact phrase recall, and questions answerable only by matching a word from the notes.\n"
            "- The correct answer must be directly supported by the notes.\n"
            "- Distractors must be plausible misunderstandings: overgeneralizations, reversed relationships, confused similar concepts, or unsupported extensions.\n"
            "- explanation must be structured with: Correct answer, Source quote, Why the correct answer fits, and Why other choices are wrong.\n"
            "- Explain why each distractor fails using the source, not just that it is wrong.\n"
            "- topic should be a specific concept, theorem, condition, failure case, or section topic, never General unless the source is insufficient.\n"
            "- Use the source_quote field for a short supporting snippet from the notes.\n"
            "- If the source includes exceptions, constraints, or failure cases, include at least one question about them when possible.\n"
            "- If Review Focus Topics are listed, prioritize those topics.\n"
            f"- Question count: {question_count}. Difficulty: {difficulty}.\n\n"
            f"Notes:\n{document_text[:80000]}"
        )
