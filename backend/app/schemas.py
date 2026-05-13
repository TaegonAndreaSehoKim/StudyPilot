from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SummaryType = Literal["concise", "detailed", "exam"]
Difficulty = Literal["easy", "medium", "hard"]
ScheduleEventType = Literal["assignment", "exam", "reading", "project", "other"]


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ScheduleItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    event_type: ScheduleEventType = "assignment"
    due_at: datetime
    notes: str | None = None


class ScheduleItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    event_type: ScheduleEventType | None = None
    due_at: datetime | None = None
    notes: str | None = None
    is_completed: bool | None = None


class ScheduleItemOut(BaseModel):
    id: int
    course_id: int
    title: str
    event_type: str
    due_at: datetime
    notes: str | None
    is_completed: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScheduleItemWithCourseOut(ScheduleItemOut):
    course_title: str


class CourseOut(BaseModel):
    id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int
    course_id: int
    filename: str
    file_type: str
    char_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailOut(DocumentOut):
    preview: str
    preview_char_count: int
    preview_is_truncated: bool


class DocumentTextOut(DocumentOut):
    text: str


class CourseDetailOut(CourseOut):
    document_count: int
    quiz_count: int
    recent_documents: list[DocumentOut]


class KeyTerm(BaseModel):
    term: str
    definition: str


class SourceQuote(BaseModel):
    quote: str
    reason: str


class SummaryCreate(BaseModel):
    summary_type: SummaryType = "concise"


class SummaryOut(BaseModel):
    id: int
    document_id: int
    summary_type: str
    title: str
    overview: str
    key_points: list[str]
    key_terms: list[KeyTerm]
    source_quotes: list[SourceQuote]
    created_at: datetime


class FlashcardCreate(BaseModel):
    count: int = Field(default=10, ge=1, le=30)


class FlashcardOut(BaseModel):
    id: int
    document_id: int
    front: str
    back: str
    topic: str
    difficulty: str
    source_quote: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizCreate(BaseModel):
    question_count: int = Field(default=5, ge=1, le=20)
    difficulty: Literal["easy", "medium", "hard", "mixed"] = "mixed"


class ReviewQuizCreate(QuizCreate):
    topics: list[str] | None = None


class QuizQuestionOut(BaseModel):
    id: int
    quiz_id: int
    question: str
    choices: list[str]
    correct_answer: str
    explanation: str
    topic: str
    difficulty: str


class QuizOut(BaseModel):
    id: int
    document_id: int
    title: str
    created_at: datetime
    questions: list[QuizQuestionOut]


class QuizAnswerIn(BaseModel):
    question_id: int
    selected_answer: str = Field(min_length=1, max_length=1)


class QuizAttemptCreate(BaseModel):
    answers: list[QuizAnswerIn]


class QuizAnswerResult(BaseModel):
    question_id: int
    selected_answer: str | None
    correct_answer: str
    is_correct: bool
    explanation: str
    topic: str


class QuizAttemptResult(BaseModel):
    id: int
    quiz_id: int
    score: float
    total_questions: int
    correct_count: int
    missed_topics: list[str]
    answers: list[QuizAnswerResult]
    created_at: datetime


class CourseQuizAttemptOut(BaseModel):
    id: int
    quiz_id: int
    quiz_title: str
    document_id: int
    score: float
    total_questions: int
    correct_count: int
    missed_topics: list[str]
    created_at: datetime


class WeakTopicOut(BaseModel):
    id: int
    course_id: int
    topic: str
    miss_count: int
    last_missed_at: datetime

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    course_count: int
    document_count: int
    summary_count: int
    flashcard_count: int
    quiz_count: int
    recent_courses: list[CourseOut]
    recent_documents: list[DocumentOut]
    recent_summaries: list[SummaryOut]
    recent_quizzes: list[QuizOut]
    weak_topics: list[WeakTopicOut]


class CourseDashboardOut(BaseModel):
    course: CourseOut
    document_count: int
    summary_count: int
    flashcard_count: int
    quiz_count: int
    recent_documents: list[DocumentOut]
    recent_quizzes: list[QuizOut]
    weak_topics: list[WeakTopicOut]


class HealthOut(BaseModel):
    status: str
    app: str
