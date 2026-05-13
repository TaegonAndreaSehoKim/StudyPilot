from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )
    weak_topics: Mapped[list["WeakTopic"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="uploaded")

    course: Mapped["Course"] = relationship(back_populates="documents")
    summaries: Mapped[list["Summary"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    flashcards: Mapped[list["Flashcard"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    summary_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    overview: Mapped[str] = mapped_column(Text, nullable=False)
    key_points_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    key_terms_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    source_quotes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped["Document"] = relationship(back_populates="summaries")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(40), nullable=False, default="medium")
    source_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped["Document"] = relationship(back_populates="flashcards")


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped["Document"] = relationship(back_populates="quizzes")
    questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="quiz", cascade="all, delete-orphan")
    attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    choices_json: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(1), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(40), nullable=False, default="medium")

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    missed_topics_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    answers_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")


class WeakTopic(Base):
    __tablename__ = "weak_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    miss_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_missed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    course: Mapped["Course"] = relationship(back_populates="weak_topics")
