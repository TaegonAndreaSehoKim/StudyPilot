import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_ai_provider
from app.models import Document, Summary
from app.schemas import SummaryCreate, SummaryOut
from app.services.study_generator import StudyGenerator

router = APIRouter(tags=["summaries"])


def _summary_out(summary: Summary) -> SummaryOut:
    return SummaryOut(
        id=summary.id,
        document_id=summary.document_id,
        summary_type=summary.summary_type,
        title=summary.title,
        overview=summary.overview,
        key_points=json.loads(summary.key_points_json),
        key_terms=json.loads(summary.key_terms_json),
        source_quotes=json.loads(summary.source_quotes_json),
        created_at=summary.created_at,
    )


def _document_ready(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.status != "extracted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document text is not available for generation")
    return document


@router.post("/documents/{document_id}/summaries", response_model=SummaryOut, status_code=status.HTTP_201_CREATED)
def create_summary(document_id: int, payload: SummaryCreate, db: Session = Depends(get_db)) -> SummaryOut:
    document = _document_ready(db, document_id)
    generator = StudyGenerator(get_ai_provider())
    result = generator.generate_summary(document.extracted_text, payload.summary_type)
    summary = Summary(
        document_id=document_id,
        summary_type=payload.summary_type,
        title=str(result.get("title") or "Study Notes"),
        overview=str(result.get("overview") or ""),
        key_points_json=json.dumps(result.get("key_points") or []),
        key_terms_json=json.dumps(result.get("key_terms") or []),
        source_quotes_json=json.dumps(result.get("source_quotes") or []),
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return _summary_out(summary)


@router.get("/documents/{document_id}/summaries", response_model=list[SummaryOut])
def list_summaries(document_id: int, db: Session = Depends(get_db)) -> list[SummaryOut]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    summaries = db.query(Summary).filter(Summary.document_id == document_id).order_by(Summary.created_at.desc()).all()
    return [_summary_out(summary) for summary in summaries]
