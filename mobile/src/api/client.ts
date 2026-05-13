import AsyncStorage from '@react-native-async-storage/async-storage';

import type {
  Course,
  CourseDashboard,
  Dashboard,
  Document,
  DocumentDetail,
  DocumentText,
  Flashcard,
  Quiz,
  QuizAttemptResult,
  Summary,
} from './types';

const API_BASE_URL_KEY = 'studypilot.apiBaseUrl';
export const DEFAULT_API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

export async function getApiBaseUrl(): Promise<string> {
  return (await AsyncStorage.getItem(API_BASE_URL_KEY)) || DEFAULT_API_BASE_URL;
}

export async function setApiBaseUrl(value: string): Promise<void> {
  await AsyncStorage.setItem(API_BASE_URL_KEY, value.trim());
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = await getApiBaseUrl();
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${baseUrl}${path}`, { ...options, headers });
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
  documentDownloadUrl: async (documentId: number) => `${await getApiBaseUrl()}/documents/${documentId}/download`,
  deleteDocument: (documentId: number) => request<void>(`/documents/${documentId}`, { method: 'DELETE' }),
  summary: (summaryId: number) => request<Summary>(`/summaries/${summaryId}`),
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
  documentQuizzes: (documentId: number) => request<Quiz[]>(`/documents/${documentId}/quizzes`),
  courseQuizzes: (courseId: number) => request<Quiz[]>(`/courses/${courseId}/quizzes`),
  quiz: (quizId: number) => request<Quiz>(`/quizzes/${quizId}`),
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
