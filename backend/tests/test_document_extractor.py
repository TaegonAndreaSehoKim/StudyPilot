from pathlib import Path

from app.services import document_extractor


class FakePdfPage:
    def __init__(self, default_text: str, layout_text: str = "") -> None:
        self.default_text = default_text
        self.layout_text = layout_text

    def extract_text(self, **kwargs) -> str:
        if kwargs.get("extraction_mode") == "layout":
            return self.layout_text
        return self.default_text


class FakePdfReader:
    def __init__(self, pages: list[FakePdfPage]) -> None:
        self.pages = pages


def test_pdf_extraction_marks_all_pages_and_empty_pages(monkeypatch) -> None:
    pages = [
        FakePdfPage("Short text.", "Longer layout text about rational agents and state spaces."),
        FakePdfPage(""),
        FakePdfPage("Planning uses actions, preconditions, effects, and goals."),
    ]
    monkeypatch.setattr(document_extractor, "PdfReader", lambda _: FakePdfReader(pages))

    text, status = document_extractor.extract_text_from_pdf(Path("unused.pdf"))

    assert status == "extracted"
    assert "--- Page 1 of 3 ---" in text
    assert "--- Page 2 of 3 ---" in text
    assert "--- Page 3 of 3 ---" in text
    assert "Longer layout text about rational agents" in text
    assert "No extractable text found on this page" in text
    assert "1 of 3 pages had no extractable text" in text


def test_pdf_extraction_errors_when_no_pages_have_text(monkeypatch) -> None:
    pages = [FakePdfPage(""), FakePdfPage("")]
    monkeypatch.setattr(document_extractor, "PdfReader", lambda _: FakePdfReader(pages))

    text, status = document_extractor.extract_text_from_pdf(Path("unused.pdf"))

    assert status == "error"
    assert "Checked 2 pages" in text
    assert "OCR" in text
