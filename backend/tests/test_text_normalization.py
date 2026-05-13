from app.services.text_normalization import normalize_extracted_text, normalize_inline_text


def test_normalize_extracted_text_removes_broken_pdf_characters() -> None:
    text = "Arti\ufb01cial\u0000 Intelligence \ufffd studies\r\n\r\n\r\n\r\n rational agents."

    normalized = normalize_extracted_text(text)

    assert normalized == "Artificial Intelligence studies\n\n\n rational agents."
    assert "\ufffd" not in normalized
    assert "\u0000" not in normalized


def test_normalize_inline_text_collapses_whitespace_for_generated_outputs() -> None:
    text = "Search\talgorithms\n\nuse   heuristics."

    assert normalize_inline_text(text) == "Search algorithms use heuristics."
