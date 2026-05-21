import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_ai_provider
from app.models import Course, Document, Summary
from app.schemas import ExplanationCreate, SummaryCreate, SummaryOut
from app.services.study_generator import StudyGenerator

router = APIRouter(tags=["summaries"])


SUMMARY_TYPE_LABELS = {
    "concise": "Concise Review Notes",
    "detailed": "Detailed Explanation",
    "exam": "Exam Review Notes",
    "explanation": "Detailed Explanation",
}


def _summary_title(summary: Summary) -> str:
    if summary.section is not None:
        label = SUMMARY_TYPE_LABELS.get(summary.summary_type, "Review Notes")
        return f"{summary.section.title} - {label}"
    return summary.title


def _summary_out(summary: Summary) -> SummaryOut:
    return SummaryOut(
        id=summary.id,
        document_id=summary.document_id,
        section_id=summary.section_id,
        summary_type=summary.summary_type,
        title=_summary_title(summary),
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


def _summary_or_404(db: Session, summary_id: int) -> Summary:
    summary = db.get(Summary, summary_id)
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    return summary


def _save_summary(
    db: Session,
    document_id: int | None,
    result: dict,
    summary_type: str,
    section_id: int | None = None,
    title: str | None = None,
) -> SummaryOut:
    summary = Summary(
        document_id=document_id,
        section_id=section_id,
        summary_type=summary_type,
        title=title or str(result.get("title") or "Study Notes"),
        overview=str(result.get("overview") or ""),
        key_points_json=json.dumps(result.get("key_points") or []),
        key_terms_json=json.dumps(result.get("key_terms") or []),
        source_quotes_json=json.dumps(result.get("source_quotes") or []),
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return _summary_out(summary)


@router.post("/documents/{document_id}/summaries", response_model=SummaryOut, status_code=status.HTTP_201_CREATED)
def create_summary(document_id: int, payload: SummaryCreate, db: Session = Depends(get_db)) -> SummaryOut:
    document = _document_ready(db, document_id)
    generator = StudyGenerator(get_ai_provider())
    result = generator.generate_summary(
        document.extracted_text,
        payload.summary_type,
        course_title=document.course.title if document.course else None,
        course_description=document.course.description if document.course else None,
    )
    return _save_summary(db, document_id, result, payload.summary_type)


@router.post("/documents/{document_id}/explanations", response_model=SummaryOut, status_code=status.HTTP_201_CREATED)
def create_explanation(document_id: int, payload: ExplanationCreate | None = None, db: Session = Depends(get_db)) -> SummaryOut:
    document = _document_ready(db, document_id)
    focus = payload.focus if payload else None
    learner_request = (
        "The learner is struggling to understand this lecture. Create a detailed explanation, not a compressed summary. "
        "Remove casual filler, greetings, agenda chatter, and repeated transition phrases, but preserve as much concept-bearing "
        "explanation, examples, comparisons, caveats, and source teaching order as possible."
    )
    if focus:
        learner_request += f" Pay special attention to: {focus}"
    generator = StudyGenerator(get_ai_provider())
    result = generator.generate_summary(
        document.extracted_text,
        "explanation",
        course_title=document.course.title if document.course else None,
        course_description=document.course.description if document.course else None,
        learner_request=learner_request,
    )
    return _save_summary(db, document_id, result, "explanation")


@router.get("/documents/{document_id}/summaries", response_model=list[SummaryOut])
def list_summaries(document_id: int, db: Session = Depends(get_db)) -> list[SummaryOut]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    summaries = db.query(Summary).filter(Summary.document_id == document_id).order_by(Summary.created_at.desc()).all()
    return [_summary_out(summary) for summary in summaries]


@router.get("/summaries/{summary_id}", response_model=SummaryOut)
def get_summary(summary_id: int, db: Session = Depends(get_db)) -> SummaryOut:
    return _summary_out(_summary_or_404(db, summary_id))


@router.delete("/summaries/{summary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_summary(summary_id: int, db: Session = Depends(get_db)) -> None:
    summary = _summary_or_404(db, summary_id)
    db.delete(summary)
    db.commit()


@router.get("/courses/{course_id}/summaries", response_model=list[SummaryOut])
def list_course_summaries(course_id: int, db: Session = Depends(get_db)) -> list[SummaryOut]:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    summaries = (
        db.query(Summary)
        .join(Document, Summary.document_id == Document.id)
        .filter(Document.course_id == course_id)
        .order_by(Summary.created_at.desc())
        .all()
    )
    return [_summary_out(summary) for summary in summaries]
