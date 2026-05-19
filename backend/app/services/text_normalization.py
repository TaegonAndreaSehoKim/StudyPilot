from __future__ import annotations

import re
import unicodedata

LIGATURES = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
}


def normalize_extracted_text(value: str) -> str:
    text = _replace_ligatures(value)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\ufeff", "")
    text = text.replace("\ufffd", "")
    text = _strip_control_chars(text)
    text = _repair_pdf_text_artifacts(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def normalize_inline_text(value: str) -> str:
    text = normalize_extracted_text(value)
    return re.sub(r"\s+", " ", text).strip()


def _replace_ligatures(value: str) -> str:
    text = value
    for ligature, replacement in LIGATURES.items():
        text = text.replace(ligature, replacement)
    return text


def _strip_control_chars(value: str) -> str:
    return "".join(char for char in value if char in "\n\t" or unicodedata.category(char)[0] != "C")


def _repair_pdf_text_artifacts(value: str) -> str:
    text = value
    text = re.sub(r"\bT\s*y\s*p\s*e\s*o\s*f\s*M\s*o\s*v\s*e\s*m\s*e\s*n\s*t\b", "Type of Movement", text)
    replacements = {
        "Ty peofMovement": "Type of Movement",
        "mi ghthaveaga me with": "might have a game with",
        "mi ght have a ga me with": "might have a game with",
        ".xed": "fixed",
        ".oat": "float",
        ".oats": "floats",
        ".rst": "first",
        ".nal": "final",
        "Speci.c": "Specific",
        "speci.c": "specific",
        "de.nition": "definition",
        "De.nition": "Definition",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)

    # Some PDF extractors split large heading glyphs into single-letter tokens.
    def collapse_spaced_letters(match: re.Match[str]) -> str:
        collapsed = match.group(0).replace(" ", "")
        known = {
            "TypeofMovement": "Type of Movement",
            "ContinuousMovement": "Continuous Movement",
            "DiscreteMovement": "Discrete Movement",
            "AgentRepresentation": "Agent Representation",
        }
        return known.get(collapsed, collapsed)

    text = re.sub(r"\b(?:[A-Za-z]\s+){2,}[A-Za-z]\b", collapse_spaced_letters, text)
    text = text.replace("mi ghthaveaga me with", "might have a game with")
    text = text.replace("We mi ghthaveaga me", "We might have a game")
    text = re.sub(r"(?m)^\s*A\s+(?=[A-Z])", "", text)
    text = re.sub(r"(?<=[.!?])\s+A\s+(?=[A-Z])", " ", text)
    return text
