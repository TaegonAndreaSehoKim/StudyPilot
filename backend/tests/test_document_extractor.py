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

    result = document_extractor.extract_text_from_pdf(Path("unused.pdf"))

    assert result.status == "extracted"
    assert result.page_count == 3
    assert result.extracted_page_count == 2
    assert result.extraction_method == "pypdf"
    assert result.ocr_status == "recommended"
    text = result.text
    assert "--- Page 1 of 3 ---" in text
    assert "--- Page 2 of 3 ---" in text
    assert "--- Page 3 of 3 ---" in text
    assert "Longer layout text about rational agents" in text
    assert "No extractable text found on this page" in text
    assert "1 of 3 pages had no extractable text" in text


def test_pdf_extraction_errors_when_no_pages_have_text(monkeypatch) -> None:
    pages = [FakePdfPage(""), FakePdfPage("")]
    monkeypatch.setattr(document_extractor, "PdfReader", lambda _: FakePdfReader(pages))

    result = document_extractor.extract_text_from_pdf(Path("unused.pdf"))

    assert result.status == "needs_ocr"
    assert result.page_count == 2
    assert result.extracted_page_count == 0
    assert result.ocr_status == "available"
    assert "Checked 2 pages" in result.text
    assert "OCR" in result.text


def test_pdf_extraction_requires_ocr_when_page_coverage_is_low(monkeypatch) -> None:
    pages = [
        FakePdfPage("Planning uses actions, preconditions, effects, and goals."),
        FakePdfPage(""),
        FakePdfPage(""),
        FakePdfPage(""),
    ]
    monkeypatch.setattr(document_extractor, "PdfReader", lambda _: FakePdfReader(pages))

    result = document_extractor.extract_text_from_pdf(Path("unused.pdf"))

    assert result.status == "needs_ocr"
    assert result.page_count == 4
    assert result.extracted_page_count == 1
    assert result.ocr_status == "available"
    assert "from 1 pages" in result.text
