from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SummaryType = Literal["concise", "detailed", "exam", "explanation"]
SummaryRequestType = Literal["concise", "detailed", "exam"]
Difficulty = Literal["easy", "medium", "hard"]
ScheduleEventType = Literal["assignment", "exam", "reading", "project", "other"]


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class CourseSectionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class CourseSectionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ScheduleItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    event_type: ScheduleEventType = "assignment"
    due_at: datetime
    notes: str | None = None
    reminder_minutes_before: int | None = Field(default=None, ge=0, le=10080)


class ScheduleItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    event_type: ScheduleEventType | None = None
    due_at: datetime | None = None
    notes: str | None = None
    reminder_minutes_before: int | None = Field(default=None, ge=0, le=10080)
    is_completed: bool | None = None


class ScheduleItemOut(BaseModel):
    id: int
    course_id: int
    title: str
    event_type: str
    due_at: datetime
    notes: str | None
    reminder_minutes_before: int | None
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


class CourseSectionOut(BaseModel):
    id: int
    course_id: int
    title: str
    description: str | None
    document_count: int = 0
    summary_count: int = 0
    quiz_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int
    course_id: int
    section_id: int | None
    filename: str
    file_type: str
    char_count: int
    status: str
    page_count: int
    extracted_page_count: int
    extraction_coverage: float
    extraction_method: str
    extraction_quality: str
    extraction_notes: str | None
    ocr_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailOut(DocumentOut):
    preview: str
    preview_char_count: int
    preview_is_truncated: bool


class DocumentTextOut(DocumentOut):
    text: str


class OcrJobOut(BaseModel):
    id: int
    document_id: int
    status: str
    provider: str
    error_message: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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
    summary_type: SummaryRequestType = "concise"


class ExplanationCreate(BaseModel):
    focus: str | None = Field(default=None, max_length=500)


class SummaryOut(BaseModel):
    id: int
    document_id: int | None
    section_id: int | None = None
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
    document_id: int | None
    section_id: int | None = None
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
    document_id: int | None
    section_id: int | None = None
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
    section_count: int = 0
    document_count: int
    summary_count: int
    flashcard_count: int
    quiz_count: int
    recent_documents: list[DocumentOut]
    recent_sections: list[CourseSectionOut] = []
    recent_quizzes: list[QuizOut]
    weak_topics: list[WeakTopicOut]


class HealthOut(BaseModel):
    status: str
    app: str
