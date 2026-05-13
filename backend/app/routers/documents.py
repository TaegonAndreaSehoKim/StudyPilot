from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import Course, Document
from app.schemas import DocumentDetailOut, DocumentOut
from app.services.document_extractor import extract_text_from_path, save_upload_file, validate_upload
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
    extracted_text, document_status = extract_text_from_path(path, extension)

    document = Document(
        course_id=course_id,
        filename=file.filename or path.name,
        file_type=extension,
        storage_path=str(path),
        extracted_text=extracted_text,
        char_count=len(extracted_text),
        status=document_status,
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


@router.get("/courses/{course_id}/documents", response_model=list[DocumentOut])
def list_course_documents(course_id: int, db: Session = Depends(get_db)) -> list[Document]:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return db.query(Document).filter(Document.course_id == course_id).order_by(Document.created_at.desc()).all()


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
