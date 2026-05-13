from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_ai_provider
from app.models import Document, Flashcard
from app.schemas import FlashcardCreate, FlashcardOut
from app.services.study_generator import StudyGenerator

router = APIRouter(tags=["flashcards"])


def _document_ready(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.status != "extracted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document text is not available for generation")
    return document


@router.post("/documents/{document_id}/flashcards", response_model=list[FlashcardOut], status_code=status.HTTP_201_CREATED)
def create_flashcards(document_id: int, payload: FlashcardCreate, db: Session = Depends(get_db)) -> list[Flashcard]:
    document = _document_ready(db, document_id)
    generator = StudyGenerator(get_ai_provider())
    result = generator.generate_flashcards(document.extracted_text, payload.count)
    flashcards = [
        Flashcard(
            document_id=document_id,
            front=str(item.get("front") or "Question"),
            back=str(item.get("back") or "Answer"),
            topic=str(item.get("topic") or "General"),
            difficulty=str(item.get("difficulty") or "medium"),
            source_quote=item.get("source_quote"),
        )
        for item in result
    ]
    db.add_all(flashcards)
    db.commit()
    for flashcard in flashcards:
        db.refresh(flashcard)
    return flashcards


@router.get("/documents/{document_id}/flashcards", response_model=list[FlashcardOut])
def list_flashcards(document_id: int, db: Session = Depends(get_db)) -> list[Flashcard]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return db.query(Flashcard).filter(Flashcard.document_id == document_id).order_by(Flashcard.created_at.desc()).all()
