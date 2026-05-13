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
