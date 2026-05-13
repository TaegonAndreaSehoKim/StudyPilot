from pathlib import Path
import mimetypes

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app import database
from app.database import get_db
from app.models import Course, Document, OcrJob, utc_now
from app.schemas import DocumentDetailOut, DocumentOut, DocumentTextOut, OcrJobOut
from app.services.document_extractor import extract_text_from_path, save_upload_file, validate_upload
from app.services.ocr_provider import OCRProviderError, get_ocr_provider
from app.services.storage_cleanup import remove_document_files

router = APIRouter(tags=["documents"])
DOCUMENT_PREVIEW_CHAR_LIMIT = 5000


def get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("/documents/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    course_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Document:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    content = await file.read()
    extension = validate_upload(
        filename=file.filename or "",
        content_type=file.content_type,
        file_size=len(content),
        max_upload_mb=settings.max_upload_mb,
        allowed_extensions=settings.allowed_extensions,
    )
    path = await save_upload_file(file, Path(settings.storage_dir), content)
    extraction = extract_text_from_path(path, extension)

    document = Document(
        course_id=course_id,
        filename=file.filename or path.name,
        file_type=extension,
        storage_path=str(path),
        extracted_text=extraction.text,
        char_count=len(extraction.text),
        status=extraction.status,
        page_count=extraction.page_count,
        extracted_page_count=extraction.extracted_page_count,
        extraction_method=extraction.extraction_method,
        extraction_notes=extraction.extraction_notes,
        ocr_status=extraction.ocr_status,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/documents/{document_id}", response_model=DocumentDetailOut)
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentDetailOut:
    document = get_document_or_404(db, document_id)
    preview = document.extracted_text[:DOCUMENT_PREVIEW_CHAR_LIMIT]
    return DocumentDetailOut(
        **DocumentOut.model_validate(document).model_dump(),
        preview=preview,
        preview_char_count=len(preview),
        preview_is_truncated=len(document.extracted_text) > len(preview),
    )


@router.get("/documents/{document_id}/text", response_model=DocumentTextOut)
def get_document_text(document_id: int, db: Session = Depends(get_db)) -> DocumentTextOut:
    document = get_document_or_404(db, document_id)
    return DocumentTextOut(**DocumentOut.model_validate(document).model_dump(), text=document.extracted_text)


@router.post("/documents/{document_id}/ocr", response_model=OcrJobOut, status_code=status.HTTP_202_ACCEPTED)
def start_document_ocr(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OcrJob:
    document = get_document_or_404(db, document_id)
    if document.file_type != ".pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OCR is only available for PDF documents.")

    active_job = (
        db.query(OcrJob)
        .filter(OcrJob.document_id == document_id, OcrJob.status.in_(("queued", "running")))
        .order_by(OcrJob.created_at.desc())
        .first()
    )
    if active_job:
        return active_job

    if document.ocr_status not in {"available", "recommended", "error"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OCR is not required for this document.")

    job = OcrJob(document_id=document.id, status="queued", provider=settings.ocr_provider)
    document.ocr_status = "queued"
    db.add(job)
    db.add(document)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_ocr_job, job.id)
    return job


@router.get("/ocr-jobs/{job_id}", response_model=OcrJobOut)
def get_ocr_job(job_id: int, db: Session = Depends(get_db)) -> OcrJob:
    job = db.get(OcrJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR job not found")
    return job


def process_ocr_job(job_id: int) -> None:
    db = database.SessionLocal()
    try:
        settings = get_settings()
        job = db.get(OcrJob, job_id)
        if job is None:
            return
        document = db.get(Document, job.document_id)
        if document is None:
            job.status = "failed"
            job.error_message = "Document no longer exists."
            job.completed_at = utc_now()
            db.add(job)
            db.commit()
            return

        job.status = "running"
        document.ocr_status = "running"
        db.add_all([job, document])
        db.commit()

        try:
            path = _safe_stored_document_path(document, Path(settings.storage_dir))
            provider = get_ocr_provider(settings)
            result = provider.extract_text(path, page_count=document.page_count)
        except (OCRProviderError, HTTPException, OSError, ValueError) as exc:
            error_message = exc.detail if isinstance(exc, HTTPException) else str(exc)
            job.status = "failed"
            job.error_message = error_message
            job.completed_at = utc_now()
            document.ocr_status = "error"
            document.extraction_notes = error_message
            db.add_all([job, document])
            db.commit()
            return

        document.extracted_text = result.text
        document.char_count = len(result.text)
        document.status = "extracted"
        document.page_count = result.page_count or document.page_count
        document.extracted_page_count = result.extracted_page_count
        document.extraction_method = result.extraction_method
        document.extraction_notes = result.extraction_notes
        document.ocr_status = "completed"
        job.status = "completed"
        job.completed_at = utc_now()
        db.add_all([job, document])
        db.commit()
    finally:
        db.close()


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    document = get_document_or_404(db, document_id)
    path = _safe_stored_document_path(document, Path(settings.storage_dir))
    media_type = mimetypes.guess_type(document.filename)[0] or "application/octet-stream"
    return FileResponse(path=path, media_type=media_type, filename=document.filename)


@router.get("/courses/{course_id}/documents", response_model=list[DocumentOut])
def list_course_documents(course_id: int, db: Session = Depends(get_db)) -> list[Document]:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return db.query(Document).filter(Document.course_id == course_id).order_by(Document.created_at.desc()).all()


def _safe_stored_document_path(document: Document, storage_dir: Path) -> Path:
    try:
        path = Path(document.storage_path).resolve()
        root = storage_dir.resolve()
        path.relative_to(root)
    except (OSError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file is unavailable") from None

    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file is unavailable")
    return path


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    document = get_document_or_404(db, document_id)
    db.delete(document)
    db.commit()
    remove_document_files([document], Path(settings.storage_dir))
