from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader


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
    return path.read_text(encoding="utf-8", errors="replace").strip()


def extract_text_from_pdf(path: Path) -> tuple[str, str]:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        if page_text:
            pages.append(f"--- Page {index} ---\n\n{page_text}")

    text = "\n\n".join(pages).strip()
    if len(text) < 100:
        return (
            "This PDF appears to be scanned or image-only. OCR is not supported in the StudyPilot MVP.",
            "error",
        )
    return text, "extracted"
