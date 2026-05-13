from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import Course, Document, Quiz
from app.schemas import CourseCreate, CourseDetailOut, CourseOut, CourseUpdate, DocumentOut
from app.services.storage_cleanup import remove_document_files

router = APIRouter(prefix="/courses", tags=["courses"])


def get_course_or_404(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)) -> Course:
    course = Course(title=payload.title, description=payload.description)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db)) -> list[Course]:
    return db.query(Course).order_by(Course.created_at.desc()).all()


@router.get("/{course_id}", response_model=CourseDetailOut)
def get_course(course_id: int, db: Session = Depends(get_db)) -> CourseDetailOut:
    course = get_course_or_404(db, course_id)
    document_count = db.query(func.count(Document.id)).filter(Document.course_id == course_id).scalar() or 0
    quiz_count = (
        db.query(func.count(Quiz.id))
        .join(Document, Quiz.document_id == Document.id)
        .filter(Document.course_id == course_id)
        .scalar()
        or 0
    )
    recent_documents = (
        db.query(Document)
        .filter(Document.course_id == course_id)
        .order_by(Document.created_at.desc())
        .limit(5)
        .all()
    )
    return CourseDetailOut(
        **CourseOut.model_validate(course).model_dump(),
        document_count=document_count,
        quiz_count=quiz_count,
        recent_documents=[DocumentOut.model_validate(document) for document in recent_documents],
    )


@router.patch("/{course_id}", response_model=CourseOut)
def update_course(course_id: int, payload: CourseUpdate, db: Session = Depends(get_db)) -> Course:
    course = get_course_or_404(db, course_id)
    if payload.title is not None:
        course.title = payload.title
    if "description" in payload.model_fields_set:
        course.description = payload.description
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    course = get_course_or_404(db, course_id)
    documents = list(course.documents)
    db.delete(course)
    db.commit()
    remove_document_files(documents, Path(settings.storage_dir))
