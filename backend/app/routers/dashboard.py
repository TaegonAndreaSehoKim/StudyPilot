from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, Document, Flashcard, Quiz, Summary, WeakTopic
from app.routers.quizzes import _quiz_out
from app.routers.summaries import _summary_out
from app.schemas import CourseDashboardOut, CourseOut, DashboardOut, DocumentOut, WeakTopicOut

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardOut:
    recent_courses = db.query(Course).order_by(Course.created_at.desc()).limit(5).all()
    recent_documents = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
    recent_summaries = db.query(Summary).order_by(Summary.created_at.desc()).limit(5).all()
    recent_quizzes = db.query(Quiz).order_by(Quiz.created_at.desc()).limit(5).all()
    weak_topics = (
        db.query(WeakTopic)
        .order_by(WeakTopic.miss_count.desc(), WeakTopic.last_missed_at.desc())
        .limit(10)
        .all()
    )
    return DashboardOut(
        course_count=db.query(func.count(Course.id)).scalar() or 0,
        document_count=db.query(func.count(Document.id)).scalar() or 0,
        summary_count=db.query(func.count(Summary.id)).scalar() or 0,
        flashcard_count=db.query(func.count(Flashcard.id)).scalar() or 0,
        quiz_count=db.query(func.count(Quiz.id)).scalar() or 0,
        recent_courses=[CourseOut.model_validate(course) for course in recent_courses],
        recent_documents=[DocumentOut.model_validate(document) for document in recent_documents],
        recent_summaries=[_summary_out(summary) for summary in recent_summaries],
        recent_quizzes=[_quiz_out(quiz) for quiz in recent_quizzes],
        weak_topics=[WeakTopicOut.model_validate(topic) for topic in weak_topics],
    )


@router.get("/courses/{course_id}/weak-topics", response_model=list[WeakTopicOut])
def list_weak_topics(course_id: int, db: Session = Depends(get_db)) -> list[WeakTopic]:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return (
        db.query(WeakTopic)
        .filter(WeakTopic.course_id == course_id)
        .order_by(WeakTopic.miss_count.desc(), WeakTopic.last_missed_at.desc())
        .all()
    )


@router.get("/courses/{course_id}/dashboard", response_model=CourseDashboardOut)
def get_course_dashboard(course_id: int, db: Session = Depends(get_db)) -> CourseDashboardOut:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    recent_documents = (
        db.query(Document)
        .filter(Document.course_id == course_id)
        .order_by(Document.created_at.desc())
        .limit(5)
        .all()
    )
    recent_quizzes = (
        db.query(Quiz)
        .join(Document, Quiz.document_id == Document.id)
        .filter(Document.course_id == course_id)
        .order_by(Quiz.created_at.desc())
        .limit(5)
        .all()
    )
    weak_topics = (
        db.query(WeakTopic)
        .filter(WeakTopic.course_id == course_id)
        .order_by(WeakTopic.miss_count.desc(), WeakTopic.last_missed_at.desc())
        .limit(10)
        .all()
    )
    document_ids = select(Document.id).where(Document.course_id == course_id)

    return CourseDashboardOut(
        course=CourseOut.model_validate(course),
        document_count=db.query(func.count(Document.id)).filter(Document.course_id == course_id).scalar() or 0,
        summary_count=db.query(func.count(Summary.id)).filter(Summary.document_id.in_(document_ids)).scalar() or 0,
        flashcard_count=db.query(func.count(Flashcard.id)).filter(Flashcard.document_id.in_(document_ids)).scalar() or 0,
        quiz_count=db.query(func.count(Quiz.id)).filter(Quiz.document_id.in_(document_ids)).scalar() or 0,
        recent_documents=[DocumentOut.model_validate(document) for document in recent_documents],
        recent_quizzes=[_quiz_out(quiz) for quiz in recent_quizzes],
        weak_topics=[WeakTopicOut.model_validate(topic) for topic in weak_topics],
    )
