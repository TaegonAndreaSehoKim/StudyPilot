import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_ai_provider
from app.models import Course, Document, Quiz, QuizAttempt, QuizQuestion, WeakTopic
from app.schemas import CourseQuizAttemptOut, QuizAnswerResult, QuizAttemptCreate, QuizAttemptResult, QuizCreate, QuizOut, QuizQuestionOut, ReviewQuizCreate
from app.services.study_generator import StudyGenerator
from app.services.weak_topics import update_weak_topics

router = APIRouter(tags=["quizzes"])


def _document_ready(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.status != "extracted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document text is not available for generation")
    return document


def _quiz_out(quiz: Quiz) -> QuizOut:
    questions = [
        QuizQuestionOut(
            id=question.id,
            quiz_id=question.quiz_id,
            question=question.question,
            choices=json.loads(question.choices_json),
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            topic=question.topic,
            difficulty=question.difficulty,
        )
        for question in quiz.questions
    ]
    return QuizOut(
        id=quiz.id,
        document_id=quiz.document_id,
        title=quiz.title,
        created_at=quiz.created_at,
        questions=questions,
    )


def _attempt_out(attempt: QuizAttempt) -> QuizAttemptResult:
    return QuizAttemptResult(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        score=attempt.score,
        total_questions=attempt.total_questions,
        correct_count=attempt.correct_count,
        missed_topics=json.loads(attempt.missed_topics_json),
        answers=[QuizAnswerResult(**answer) for answer in json.loads(attempt.answers_json)],
        created_at=attempt.created_at,
    )


def _course_attempt_out(attempt: QuizAttempt) -> CourseQuizAttemptOut:
    return CourseQuizAttemptOut(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        quiz_title=attempt.quiz.title,
        document_id=attempt.quiz.document_id,
        score=attempt.score,
        total_questions=attempt.total_questions,
        correct_count=attempt.correct_count,
        missed_topics=json.loads(attempt.missed_topics_json),
        created_at=attempt.created_at,
    )


def _save_quiz(db: Session, document_id: int, result: dict) -> QuizOut:
    quiz = Quiz(document_id=document_id, title=str(result.get("title") or "Study Quiz"))
    db.add(quiz)
    db.flush()

    for item in result.get("questions") or []:
        db.add(
            QuizQuestion(
                quiz_id=quiz.id,
                question=str(item.get("question") or "Question"),
                choices_json=json.dumps(item.get("choices") or []),
                correct_answer=str(item.get("correct_answer") or "A").upper()[:1],
                explanation=str(item.get("explanation") or ""),
                topic=str(item.get("topic") or "General"),
                difficulty=str(item.get("difficulty") or "medium"),
            )
        )

    db.commit()
    db.refresh(quiz)
    return _quiz_out(quiz)


@router.post("/documents/{document_id}/quizzes", response_model=QuizOut, status_code=status.HTTP_201_CREATED)
def create_quiz(document_id: int, payload: QuizCreate, db: Session = Depends(get_db)) -> QuizOut:
    document = _document_ready(db, document_id)
    generator = StudyGenerator(get_ai_provider())
    result = generator.generate_quiz(document.extracted_text, payload.question_count, payload.difficulty)
    return _save_quiz(db, document_id, result)


@router.post("/courses/{course_id}/review-quiz", response_model=QuizOut, status_code=status.HTTP_201_CREATED)
def create_weak_topic_review_quiz(course_id: int, payload: ReviewQuizCreate, db: Session = Depends(get_db)) -> QuizOut:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    documents = (
        db.query(Document)
        .filter(Document.course_id == course_id, Document.status == "extracted")
        .order_by(Document.created_at.desc())
        .all()
    )
    if not documents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No extracted documents are available for this course")

    topics = [topic.strip() for topic in (payload.topics or []) if topic.strip()]
    if not topics:
        weak_topics = (
            db.query(WeakTopic)
            .filter(WeakTopic.course_id == course_id)
            .order_by(WeakTopic.miss_count.desc(), WeakTopic.last_missed_at.desc())
            .limit(5)
            .all()
        )
        topics = [topic.topic for topic in weak_topics]
    if not topics:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No weak topics are available for this course yet")

    combined_text = "\n\n".join(f"# {document.filename}\n\n{document.extracted_text}" for document in documents)
    generator = StudyGenerator(get_ai_provider())
    result = generator.generate_review_quiz(combined_text, topics[:5], payload.question_count, payload.difficulty)
    return _save_quiz(db, documents[0].id, result)


@router.get("/documents/{document_id}/quizzes", response_model=list[QuizOut])
def list_document_quizzes(document_id: int, db: Session = Depends(get_db)) -> list[QuizOut]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    quizzes = db.query(Quiz).filter(Quiz.document_id == document_id).order_by(Quiz.created_at.desc()).all()
    return [_quiz_out(quiz) for quiz in quizzes]


@router.get("/courses/{course_id}/quizzes", response_model=list[QuizOut])
def list_course_quizzes(course_id: int, db: Session = Depends(get_db)) -> list[QuizOut]:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    quizzes = (
        db.query(Quiz)
        .join(Document, Quiz.document_id == Document.id)
        .filter(Document.course_id == course_id)
        .order_by(Quiz.created_at.desc())
        .all()
    )
    return [_quiz_out(quiz) for quiz in quizzes]


@router.get("/quizzes/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)) -> QuizOut:
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    return _quiz_out(quiz)


@router.delete("/quizzes/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(quiz_id: int, db: Session = Depends(get_db)) -> None:
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    db.delete(quiz)
    db.commit()


@router.get("/quizzes/{quiz_id}/attempts", response_model=list[QuizAttemptResult])
def list_quiz_attempts(quiz_id: int, db: Session = Depends(get_db)) -> list[QuizAttemptResult]:
    if db.get(Quiz, quiz_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id).order_by(QuizAttempt.created_at.desc()).all()
    return [_attempt_out(attempt) for attempt in attempts]


@router.get("/courses/{course_id}/attempts", response_model=list[CourseQuizAttemptOut])
def list_course_attempts(course_id: int, db: Session = Depends(get_db)) -> list[CourseQuizAttemptOut]:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    attempts = (
        db.query(QuizAttempt)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .join(Document, Quiz.document_id == Document.id)
        .filter(Document.course_id == course_id)
        .order_by(QuizAttempt.created_at.desc())
        .all()
    )
    return [_course_attempt_out(attempt) for attempt in attempts]


@router.post("/quizzes/{quiz_id}/attempts", response_model=QuizAttemptResult, status_code=status.HTTP_201_CREATED)
def submit_attempt(quiz_id: int, payload: QuizAttemptCreate, db: Session = Depends(get_db)) -> QuizAttemptResult:
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    submitted = {answer.question_id: answer.selected_answer.upper()[:1] for answer in payload.answers}
    results = []
    missed_topics: list[str] = []
    correct_count = 0

    for question in quiz.questions:
        selected = submitted.get(question.id)
        is_correct = selected == question.correct_answer
        if is_correct:
            correct_count += 1
        else:
            missed_topics.append(question.topic)
        results.append(
            {
                "question_id": question.id,
                "selected_answer": selected,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "explanation": question.explanation,
                "topic": question.topic,
            }
        )

    total = len(quiz.questions)
    score = correct_count / total if total else 0.0
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        score=score,
        total_questions=total,
        correct_count=correct_count,
        missed_topics_json=json.dumps(missed_topics),
        answers_json=json.dumps(results),
    )
    db.add(attempt)

    document = db.get(Document, quiz.document_id)
    if document is not None:
        update_weak_topics(db, document.course_id, missed_topics)

    db.commit()
    db.refresh(attempt)

    return _attempt_out(attempt)
