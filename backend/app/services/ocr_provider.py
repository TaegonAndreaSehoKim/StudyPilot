from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.config import Settings
from app.services.text_normalization import normalize_extracted_text


class OCRProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class OCRResult:
    text: str
    page_count: int
    extracted_page_count: int
    extraction_method: str
    extraction_notes: str | None = None


class OCRProvider(Protocol):
    def extract_text(self, path: Path, page_count: int = 0) -> OCRResult:
        raise NotImplementedError


class FakeOCRProvider:
    def extract_text(self, path: Path, page_count: int = 0) -> OCRResult:
        effective_page_count = max(page_count, 1)
        stem = path.stem.replace("-", " ").replace("_", " ").strip() or "uploaded PDF"
        pages = [
            (
                f"--- OCR Page {index} of {effective_page_count} ---\n\n"
                f"Fake OCR extracted study text from {stem}. "
                "Use this deterministic OCR mode for local demos and tests without external network calls."
            )
            for index in range(1, effective_page_count + 1)
        ]
        text = normalize_extracted_text("\n\n".join(pages))
        return OCRResult(
            text=text,
            page_count=effective_page_count,
            extracted_page_count=effective_page_count,
            extraction_method="fake_ocr",
            extraction_notes="Deterministic fake OCR output. Configure OCR_PROVIDER=textract for real scanned PDFs.",
        )


class DisabledOCRProvider:
    def extract_text(self, path: Path, page_count: int = 0) -> OCRResult:
        raise OCRProviderError("OCR is disabled. Set OCR_PROVIDER=fake or OCR_PROVIDER=textract to enable it.")


class TextractOCRProvider:
    def __init__(self, region_name: str) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise OCRProviderError("boto3 is required for OCR_PROVIDER=textract. Install backend requirements first.") from exc
        self.client = boto3.client("textract", region_name=region_name)

    def extract_text(self, path: Path, page_count: int = 0) -> OCRResult:
        try:
            response = self.client.detect_document_text(Document={"Bytes": path.read_bytes()})
        except Exception as exc:
            raise OCRProviderError(f"Textract OCR failed: {exc}") from exc

        lines = [
            block.get("Text", "")
            for block in response.get("Blocks", [])
            if block.get("BlockType") == "LINE" and block.get("Text")
        ]
        text = normalize_extracted_text("\n".join(lines))
        if not text:
            raise OCRProviderError("Textract OCR completed but returned no readable text.")

        detected_pages = int(response.get("DocumentMetadata", {}).get("Pages") or page_count or 1)
        return OCRResult(
            text=text,
            page_count=detected_pages,
            extracted_page_count=detected_pages,
            extraction_method="textract",
            extraction_notes="OCR completed with Amazon Textract DetectDocumentText.",
        )


def get_ocr_provider(settings: Settings) -> OCRProvider:
    provider = settings.ocr_provider.lower()
    if provider == "fake":
        return FakeOCRProvider()
    if provider == "textract":
        return TextractOCRProvider(region_name=settings.aws_region)
    if provider == "disabled":
        return DisabledOCRProvider()
    raise OCRProviderError(f"Unsupported OCR_PROVIDER value: {settings.ocr_provider}")
