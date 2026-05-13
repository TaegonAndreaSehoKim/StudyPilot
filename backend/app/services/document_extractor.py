from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader

from app.services.text_normalization import normalize_extracted_text

NO_EXTRACTABLE_TEXT_MESSAGE = (
    "[No extractable text found on this page. Scanned/image-only PDF pages are not supported in this MVP.]"
)


def extension_for(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_upload(filename: str, content_type: str | None, file_size: int, max_upload_mb: int, allowed_extensions: tuple[str, ...]) -> str:
    extension = extension_for(filename)
    if extension not in allowed_extensions:
        allowed = ", ".join(allowed_extensions)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed extensions: {allowed}",
        )

    max_bytes = max_upload_mb * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File is too large. Maximum upload size is {max_upload_mb} MB.",
        )

    return extension


async def save_upload_file(upload_file: UploadFile, storage_dir: Path, content: bytes | None = None) -> Path:
    documents_dir = storage_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)
    extension = extension_for(upload_file.filename or "")
    safe_name = f"{uuid4().hex}{extension}"
    destination = documents_dir / safe_name
    data = content if content is not None else await upload_file.read()
    destination.write_bytes(data)
    return destination


def extract_text_from_path(path: Path, extension: str) -> tuple[str, str]:
    if extension in {".txt", ".md"}:
        return extract_text_from_txt_or_md(path), "extracted"
    if extension == ".pdf":
        return extract_text_from_pdf(path)
    raise ValueError(f"Unsupported extension: {extension}")


def extract_text_from_txt_or_md(path: Path) -> str:
    return normalize_extracted_text(path.read_text(encoding="utf-8", errors="replace"))


def extract_text_from_pdf(path: Path) -> tuple[str, str]:
    reader = PdfReader(str(path))
    pages: list[str] = []
    extracted_char_count = 0
    empty_page_count = 0
    page_count = len(reader.pages)

    for index, page in enumerate(reader.pages, start=1):
        page_text = _extract_pdf_page_text(page)
        if page_text:
            extracted_char_count += len(page_text)
            pages.append(f"--- Page {index} of {page_count} ---\n\n{normalize_extracted_text(page_text)}")
        else:
            empty_page_count += 1
            pages.append(f"--- Page {index} of {page_count} ---\n\n{NO_EXTRACTABLE_TEXT_MESSAGE}")

    text = "\n\n".join(pages).strip()
    if extracted_char_count < 100:
        return (
            f"No extractable text was found in this PDF. Checked {page_count} pages. "
            "Scanned/image-only PDFs need OCR, which is not supported in the StudyPilot MVP.",
            "error",
        )
    if empty_page_count:
        text += (
            f"\n\nExtraction note: {empty_page_count} of {page_count} pages had no extractable text. "
            "Those pages may be scanned images or use PDF encoding that pypdf cannot read."
        )
    return normalize_extracted_text(text), "extracted"


def _extract_pdf_page_text(page: object) -> str:
    best_text = ""
    extraction_attempts = ({}, {"extraction_mode": "layout"})
    for kwargs in extraction_attempts:
        try:
            text = page.extract_text(**kwargs) or ""
        except TypeError:
            continue
        except Exception:
            continue

        cleaned = text.strip()
        if len(cleaned) > len(best_text):
            best_text = cleaned

    return best_text
