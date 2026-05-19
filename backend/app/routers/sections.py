from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_ai_provider
from app.models import Course, CourseSection, Document, Quiz, Summary
from app.routers.quizzes import _quiz_out, _save_quiz
from app.routers.summaries import _save_summary, _summary_out
from app.schemas import CourseSectionCreate, CourseSectionOut, CourseSectionUpdate, ExplanationCreate, QuizCreate, QuizOut, SummaryCreate, SummaryOut
from app.services.study_generator import StudyGenerator

router = APIRouter(tags=["sections"])


def _section_or_404(db: Session, section_id: int) -> CourseSection:
    section = db.get(CourseSection, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return section


def _section_out(db: Session, section: CourseSection) -> CourseSectionOut:
    return CourseSectionOut(
        id=section.id,
        course_id=section.course_id,
        title=section.title,
        description=section.description,
        document_count=db.query(func.count(Document.id)).filter(Document.section_id == section.id).scalar() or 0,
        summary_count=db.query(func.count(Summary.id)).filter(Summary.section_id == section.id).scalar() or 0,
        quiz_count=db.query(func.count(Quiz.id)).filter(Quiz.section_id == section.id).scalar() or 0,
        created_at=section.created_at,
        updated_at=section.updated_at,
    )


def _section_documents_for_generation(db: Session, section_id: int) -> list[Document]:
    documents = (
        db.query(Document)
        .filter(Document.section_id == section_id, Document.status == "extracted")
        .order_by(Document.created_at.asc())
        .all()
    )
    if not documents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No extracted documents are available for this section")
    return documents


def _section_source_text(documents: list[Document]) -> str:
    if len(documents) == 1:
        return documents[0].extracted_text
    return "\n\n".join(
        f"Document {index}: {document.filename}\n\n{document.extracted_text}"
        for index, document in enumerate(documents, start=1)
    )


@router.post("/courses/{course_id}/sections", response_model=CourseSectionOut, status_code=status.HTTP_201_CREATED)
def create_section(course_id: int, payload: CourseSectionCreate, db: Session = Depends(get_db)) -> CourseSectionOut:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    section = CourseSection(course_id=course_id, title=payload.title, description=payload.description)
    db.add(section)
    db.commit()
    db.refresh(section)
    return _section_out(db, section)


@router.get("/courses/{course_id}/sections", response_model=list[CourseSectionOut])
def list_course_sections(course_id: int, db: Session = Depends(get_db)) -> list[CourseSectionOut]:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    sections = db.query(CourseSection).filter(CourseSection.course_id == course_id).order_by(CourseSection.created_at.desc()).all()
    return [_section_out(db, section) for section in sections]


@router.get("/sections/{section_id}", response_model=CourseSectionOut)
def get_section(section_id: int, db: Session = Depends(get_db)) -> CourseSectionOut:
    return _section_out(db, _section_or_404(db, section_id))


@router.patch("/sections/{section_id}", response_model=CourseSectionOut)
def update_section(section_id: int, payload: CourseSectionUpdate, db: Session = Depends(get_db)) -> CourseSectionOut:
    section = _section_or_404(db, section_id)
    if payload.title is not None:
        section.title = payload.title
    if "description" in payload.model_fields_set:
        section.description = payload.description
    db.commit()
    db.refresh(section)
    return _section_out(db, section)


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(section_id: int, db: Session = Depends(get_db)) -> None:
    section = _section_or_404(db, section_id)
    for document in section.documents:
        document.section_id = None
    db.delete(section)
    db.commit()


@router.post("/sections/{section_id}/summaries", response_model=SummaryOut, status_code=status.HTTP_201_CREATED)
def create_section_summary(section_id: int, payload: SummaryCreate, db: Session = Depends(get_db)) -> SummaryOut:
    section = _section_or_404(db, section_id)
    documents = _section_documents_for_generation(db, section_id)
    generator = StudyGenerator(get_ai_provider())
    result = generator.generate_summary(
        _section_source_text(documents),
        payload.summary_type,
        course_title=section.course.title,
        course_description=section.course.description,
        section_title=section.title,
        section_description=section.description,
    )
    return _save_summary(db, documents[0].id, result, payload.summary_type, section_id=section.id)


@router.post("/sections/{section_id}/explanations", response_model=SummaryOut, status_code=status.HTTP_201_CREATED)
def create_section_explanation(section_id: int, payload: ExplanationCreate | None = None, db: Session = Depends(get_db)) -> SummaryOut:
    section = _section_or_404(db, section_id)
    documents = _section_documents_for_generation(db, section_id)
    focus = payload.focus if payload else None
    learner_request = (
        "The learner is struggling to understand this section. Create an expanded additional explanation across all "
        "section source materials, teaching the concepts more slowly and richly than a summary."
    )
    if focus:
        learner_request += f" Pay special attention to: {focus}"
    generator = StudyGenerator(get_ai_provider())
    result = generator.generate_summary(
        _section_source_text(documents),
        "explanation",
        course_title=section.course.title,
        course_description=section.course.description,
        section_title=section.title,
        section_description=section.description,
        learner_request=learner_request,
    )
    return _save_summary(db, documents[0].id, result, "explanation", section_id=section.id)


@router.get("/sections/{section_id}/summaries", response_model=list[SummaryOut])
def list_section_summaries(section_id: int, db: Session = Depends(get_db)) -> list[SummaryOut]:
    _section_or_404(db, section_id)
    summaries = db.query(Summary).filter(Summary.section_id == section_id).order_by(Summary.created_at.desc()).all()
    return [_summary_out(summary) for summary in summaries]


@router.post("/sections/{section_id}/quizzes", response_model=QuizOut, status_code=status.HTTP_201_CREATED)
def create_section_quiz(section_id: int, payload: QuizCreate, db: Session = Depends(get_db)) -> QuizOut:
    section = _section_or_404(db, section_id)
    documents = _section_documents_for_generation(db, section_id)
    generator = StudyGenerator(get_ai_provider())
    result = generator.generate_quiz(
        _section_source_text(documents),
        payload.question_count,
        payload.difficulty,
        course_title=section.course.title,
        course_description=section.course.description,
        section_title=section.title,
        section_description=section.description,
    )
    return _save_quiz(db, documents[0].id, result, section_id=section.id)


@router.get("/sections/{section_id}/quizzes", response_model=list[QuizOut])
def list_section_quizzes(section_id: int, db: Session = Depends(get_db)) -> list[QuizOut]:
    _section_or_404(db, section_id)
    quizzes = db.query(Quiz).filter(Quiz.section_id == section_id).order_by(Quiz.created_at.desc()).all()
    return [_quiz_out(quiz) for quiz in quizzes]
