import AsyncStorage from '@react-native-async-storage/async-storage';

import type {
  Course,
  CourseDashboard,
  CourseQuizAttempt,
  Dashboard,
  Document,
  DocumentDetail,
  DocumentText,
  Flashcard,
  GlobalScheduleItem,
  OcrJob,
  Quiz,
  QuizAttemptResult,
  ScheduleEventType,
  ScheduleItem,
  Summary,
} from './types';

const API_BASE_URL_KEY = 'studypilot.apiBaseUrl';
const ACCESS_TOKEN_KEY = 'studypilot.accessToken';
const REQUEST_TIMEOUT_MS = 10000;
export const DEFAULT_API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

export async function getApiBaseUrl(): Promise<string> {
  return (await AsyncStorage.getItem(API_BASE_URL_KEY)) || DEFAULT_API_BASE_URL;
}

export async function setApiBaseUrl(value: string): Promise<void> {
  await AsyncStorage.setItem(API_BASE_URL_KEY, value.trim());
}

export async function getAccessToken(): Promise<string> {
  return (await AsyncStorage.getItem(ACCESS_TOKEN_KEY)) || '';
}

export async function setAccessToken(value: string): Promise<void> {
  const trimmed = value.trim();
  if (trimmed) {
    await AsyncStorage.setItem(ACCESS_TOKEN_KEY, trimmed);
  } else {
    await AsyncStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = await getApiBaseUrl();
  const accessToken = await getAccessToken();
  const headers = new Headers(options.headers);
  const controller = new AbortController();
  const timeout = setTimeout(() => {
    controller.abort();
  }, REQUEST_TIMEOUT_MS);
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (accessToken && !headers.has('X-StudyPilot-Key')) {
    headers.set('X-StudyPilot-Key', accessToken);
  }

  try {
    const response = await fetch(`${baseUrl}${path}`, { ...options, headers, signal: controller.signal });
    if (!response.ok) {
      let message = `Request failed with ${response.status}`;
      try {
        const body = await response.json();
        message = body.detail || message;
      } catch {
        // Keep the status-based fallback.
      }
      throw new Error(message);
    }

    if (response.status === 204) {
      return undefined as T;
    }
    return response.json() as Promise<T>;
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new Error(`Request timed out. Check the API Base URL in Settings: ${baseUrl}`);
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  health: () => request<{ status: string; app: string }>('/health'),
  dashboard: () => request<Dashboard>('/dashboard'),
  courses: () => request<Course[]>('/courses'),
  course: (courseId: number) => request<Course>(`/courses/${courseId}`),
  courseDashboard: (courseId: number) => request<CourseDashboard>(`/courses/${courseId}/dashboard`),
  createCourse: (payload: { title: string; description?: string }) =>
    request<Course>('/courses', { method: 'POST', body: JSON.stringify(payload) }),
  deleteCourse: (courseId: number) => request<void>(`/courses/${courseId}`, { method: 'DELETE' }),
  courseDocuments: (courseId: number) => request<Document[]>(`/courses/${courseId}/documents`),
  document: (documentId: number) => request<DocumentDetail>(`/documents/${documentId}`),
  documentText: (documentId: number) => request<DocumentText>(`/documents/${documentId}/text`),
  runDocumentOcr: (documentId: number) => request<OcrJob>(`/documents/${documentId}/ocr`, { method: 'POST' }),
  ocrJob: (jobId: number) => request<OcrJob>(`/ocr-jobs/${jobId}`),
  documentDownloadUrl: async (documentId: number) => `${await getApiBaseUrl()}/documents/${documentId}/download`,
  deleteDocument: (documentId: number) => request<void>(`/documents/${documentId}`, { method: 'DELETE' }),
  summary: (summaryId: number) => request<Summary>(`/summaries/${summaryId}`),
  deleteSummary: (summaryId: number) => request<void>(`/summaries/${summaryId}`, { method: 'DELETE' }),
  courseSummaries: (courseId: number) => request<Summary[]>(`/courses/${courseId}/summaries`),
  summaries: (documentId: number) => request<Summary[]>(`/documents/${documentId}/summaries`),
  createSummary: (documentId: number, summary_type: 'concise' | 'detailed' | 'exam') =>
    request<Summary>(`/documents/${documentId}/summaries`, {
      method: 'POST',
      body: JSON.stringify({ summary_type }),
    }),
  flashcards: (documentId: number) => request<Flashcard[]>(`/documents/${documentId}/flashcards`),
  courseFlashcards: (courseId: number) => request<Flashcard[]>(`/courses/${courseId}/flashcards`),
  createFlashcards: (documentId: number, count = 10) =>
    request<Flashcard[]>(`/documents/${documentId}/flashcards`, {
      method: 'POST',
      body: JSON.stringify({ count }),
    }),
  createQuiz: (documentId: number, question_count = 5, difficulty = 'mixed') =>
    request<Quiz>(`/documents/${documentId}/quizzes`, {
      method: 'POST',
      body: JSON.stringify({ question_count, difficulty }),
    }),
  createReviewQuiz: (courseId: number, question_count = 5, difficulty = 'mixed') =>
    request<Quiz>(`/courses/${courseId}/review-quiz`, {
      method: 'POST',
      body: JSON.stringify({ question_count, difficulty }),
    }),
  documentQuizzes: (documentId: number) => request<Quiz[]>(`/documents/${documentId}/quizzes`),
  courseQuizzes: (courseId: number) => request<Quiz[]>(`/courses/${courseId}/quizzes`),
  quiz: (quizId: number) => request<Quiz>(`/quizzes/${quizId}`),
  deleteQuiz: (quizId: number) => request<void>(`/quizzes/${quizId}`, { method: 'DELETE' }),
  quizAttempts: (quizId: number) => request<QuizAttemptResult[]>(`/quizzes/${quizId}/attempts`),
  courseAttempts: (courseId: number) => request<CourseQuizAttempt[]>(`/courses/${courseId}/attempts`),
  courseSchedule: (courseId: number, includeCompleted = true) =>
    request<ScheduleItem[]>(`/courses/${courseId}/schedule?include_completed=${includeCompleted}`),
  globalSchedule: (includeCompleted = false, limit = 20) =>
    request<GlobalScheduleItem[]>(`/schedule?include_completed=${includeCompleted}&limit=${limit}`),
  createScheduleItem: (courseId: number, payload: { title: string; event_type: ScheduleEventType; due_at: string; notes?: string }) =>
    request<ScheduleItem>(`/courses/${courseId}/schedule`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateScheduleItem: (itemId: number, payload: Partial<{ title: string; event_type: ScheduleEventType; due_at: string; notes: string | null; is_completed: boolean }>) =>
    request<ScheduleItem>(`/schedule/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  deleteScheduleItem: (itemId: number) => request<void>(`/schedule/${itemId}`, { method: 'DELETE' }),
  submitQuiz: (quizId: number, answers: { question_id: number; selected_answer: string }[]) =>
    request<QuizAttemptResult>(`/quizzes/${quizId}/attempts`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    }),
  uploadDocument: (courseId: number, file: { uri: string; name: string; mimeType?: string | null }) => {
    const form = new FormData();
    form.append('course_id', String(courseId));
    form.append('file', {
      uri: file.uri,
      name: file.name,
      type: file.mimeType || 'application/octet-stream',
    } as unknown as Blob);
    return request<Document>('/documents/upload', { method: 'POST', body: form });
  },
};
