export interface Course {
  id: number;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: number;
  course_id: number;
  filename: string;
  file_type: string;
  char_count: number;
  status: string;
  page_count: number;
  extracted_page_count: number;
  extraction_coverage: number;
  extraction_method: string;
  extraction_quality: 'good' | 'partial' | 'poor' | 'ocr';
  extraction_notes: string | null;
  ocr_status: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends Document {
  preview: string;
  preview_char_count: number;
  preview_is_truncated: boolean;
}

export interface DocumentText extends Document {
  text: string;
}

export interface OcrJob {
  id: number;
  document_id: number;
  status: 'queued' | 'running' | 'completed' | 'failed';
  provider: string;
  error_message: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface KeyTerm {
  term: string;
  definition: string;
}

export interface SourceQuote {
  quote: string;
  reason: string;
}

export interface Summary {
  id: number;
  document_id: number;
  summary_type: string;
  title: string;
  overview: string;
  key_points: string[];
  key_terms: KeyTerm[];
  source_quotes: SourceQuote[];
  created_at: string;
}

export interface Flashcard {
  id: number;
  document_id: number;
  front: string;
  back: string;
  topic: string;
  difficulty: string;
  source_quote: string | null;
  created_at: string;
}

export interface QuizQuestion {
  id: number;
  quiz_id: number;
  question: string;
  choices: string[];
  correct_answer: string;
  explanation: string;
  topic: string;
  difficulty: string;
}

export interface Quiz {
  id: number;
  document_id: number;
  title: string;
  created_at: string;
  questions: QuizQuestion[];
}

export interface QuizAnswerResult {
  question_id: number;
  selected_answer: string | null;
  correct_answer: string;
  is_correct: boolean;
  explanation: string;
  topic: string;
}

export interface QuizAttemptResult {
  id: number;
  quiz_id: number;
  score: number;
  total_questions: number;
  correct_count: number;
  missed_topics: string[];
  answers: QuizAnswerResult[];
  created_at: string;
}

export interface CourseQuizAttempt {
  id: number;
  quiz_id: number;
  quiz_title: string;
  document_id: number;
  score: number;
  total_questions: number;
  correct_count: number;
  missed_topics: string[];
  created_at: string;
}

export type ScheduleEventType = 'assignment' | 'exam' | 'reading' | 'project' | 'other';

export interface ScheduleItem {
  id: number;
  course_id: number;
  title: string;
  event_type: ScheduleEventType;
  due_at: string;
  notes: string | null;
  is_completed: boolean;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface GlobalScheduleItem extends ScheduleItem {
  course_title: string;
}

export interface WeakTopic {
  id: number;
  course_id: number;
  topic: string;
  miss_count: number;
  last_missed_at: string;
}

export interface Dashboard {
  course_count: number;
  document_count: number;
  summary_count: number;
  flashcard_count: number;
  quiz_count: number;
  recent_courses: Course[];
  recent_documents: Document[];
  recent_summaries: Summary[];
  recent_quizzes: Quiz[];
  weak_topics: WeakTopic[];
}

export interface CourseDashboard {
  course: Course;
  document_count: number;
  summary_count: number;
  flashcard_count: number;
  quiz_count: number;
  recent_documents: Document[];
  recent_quizzes: Quiz[];
  weak_topics: WeakTopic[];
}
