# StudyPilot Development Plan

## Purpose

StudyPilot is an AI-powered mobile study assistant MVP. It lets students create courses, manage course deadlines, upload study materials, generate summaries, flashcards, and quizzes, take quizzes, and track weak topics.

This document preserves the implementation plan so the project can be built in a controlled order instead of drifting into partial features.

## Product Goal

Build a full-stack monorepo that works locally after cloning:

1. Start the FastAPI backend.
2. Start the Expo mobile app.
3. Create a course.
4. Upload a text, markdown, or text-based PDF document.
5. Generate a summary.
6. Generate flashcards.
7. Generate a quiz.
8. Submit quiz answers.
9. Add assignment deadlines or exam dates.
10. View weak topics, upcoming schedule, and dashboard activity.

The MVP must work without `OPENAI_API_KEY` by using a deterministic fake AI provider.

## Non-Goals

Do not implement these in the MVP:

- Authentication
- Payments or subscriptions
- Cloud file storage
- Push notifications
- App Store or Play Store packaging
- Complex spaced repetition
- Real-time collaboration
- OCR for scanned PDFs
- Full offline mode
- Vector database, embeddings, or RAG

The code should stay simple, but organized so these features can be added later.

## Architecture

```text
StudyPilot/
├── backend/          FastAPI, SQLite, SQLAlchemy, pytest
├── mobile/           React Native, Expo, TypeScript, Expo Router
├── README.md         Root setup and architecture documentation
└── DEVELOPMENT_PLAN.md
```

## Key Constraints

- Never put an LLM API key in the mobile app.
- The mobile app calls only the FastAPI backend.
- Only the backend reads `OPENAI_API_KEY`.
- Tests must use fake AI and must not call external APIs.
- The local demo must work with no paid API calls.
- Generated study content should be source-grounded in uploaded documents.
- If source content is insufficient, generation should say so instead of inventing facts.

## Implementation Phases

### Phase 1: Monorepo Foundation

- [x] Create root `.gitignore`.
- [x] Create root `README.md`.
- [x] Create `backend/` structure.
- [x] Create `mobile/` structure.
- [x] Add `.env.example` files for backend and mobile.

### Phase 2: Backend Core

- [x] Add `backend/requirements.txt`.
- [x] Implement `app/config.py` with `pydantic-settings`.
- [x] Implement `app/database.py` with SQLAlchemy engine, session, and startup table creation.
- [x] Implement `app/models.py`.
- [x] Implement `app/schemas.py`.
- [x] Implement dependency helpers in `app/deps.py`.
- [x] Implement FastAPI app in `app/main.py`.
- [x] Implement `GET /health`.

### Phase 3: Course API

- [x] Implement `POST /courses`.
- [x] Implement `GET /courses`.
- [x] Implement `GET /courses/{course_id}`.
- [x] Implement `PATCH /courses/{course_id}`.
- [x] Implement `DELETE /courses/{course_id}`.
- [x] Include course detail counts where practical.

### Phase 4: Document Upload and Extraction

- [x] Implement upload validation for `.txt`, `.md`, and `.pdf`.
- [x] Enforce max upload size.
- [x] Save files under backend storage.
- [x] Extract text from text and markdown files.
- [x] Extract text from text-based PDFs using `pypdf`.
- [x] Mark scanned or image-only PDFs as unsupported.
- [x] Implement `POST /documents/upload`.
- [x] Implement `GET /documents/{document_id}`.
- [x] Implement `GET /courses/{course_id}/documents`.
- [x] Implement `DELETE /documents/{document_id}`.

### Phase 5: AI Provider Layer

- [x] Define `AIProvider`.
- [x] Implement deterministic `FakeAIProvider`.
- [x] Implement `OpenAIProvider`.
- [x] Select fake provider when `USE_FAKE_AI=true` or `OPENAI_API_KEY` is missing.
- [x] Add robust JSON parsing and fallback behavior.
- [x] Keep prompts source-grounded.
- [x] Add section-aware document preparation before generation.
- [x] Add lightweight AI quality eval coverage for summaries and quizzes.
- [x] Validate required OpenAI output fields before accepting generated summaries, flashcards, and quizzes.
- [x] Remove broken generated-output labels from fake AI quality fixtures.

### Phase 6: Study Material Generation

- [x] Implement text chunking.
- [x] Implement summary generation service.
- [x] Implement flashcard generation service.
- [x] Implement quiz generation service.
- [x] Implement `POST /documents/{document_id}/summaries`.
- [x] Implement `GET /documents/{document_id}/summaries`.
- [x] Implement `POST /documents/{document_id}/flashcards`.
- [x] Implement `GET /documents/{document_id}/flashcards`.
- [x] Implement `POST /documents/{document_id}/quizzes`.
- [x] Implement `GET /quizzes/{quiz_id}`.

### Phase 7: Quiz Attempts and Weak Topics

- [x] Implement quiz attempt scoring.
- [x] Store submitted answers and explanations.
- [x] Update weak topics for missed questions.
- [x] Implement `POST /quizzes/{quiz_id}/attempts`.
- [x] Implement `GET /courses/{course_id}/weak-topics`.
- [x] Implement weak-topic review quiz generation.

### Phase 8: Dashboard API

- [x] Implement `GET /dashboard`.
- [x] Implement `GET /courses/{course_id}/dashboard`.
- [x] Include counts, recent courses, recent documents, recent quizzes, and weak topics.

### Phase 8A: Course Schedule Management

- [x] Add course schedule persistence for assignments, exams, readings, projects, and other milestones.
- [x] Implement course-specific schedule CRUD.
- [x] Implement global upcoming schedule aggregation across all courses.
- [x] Track completion state for schedule items.
- [x] Show countdown/overdue status in the mobile app.
- [x] Surface upcoming schedule items on the main dashboard regardless of course.

### Phase 9: Backend Tests

- [x] Use temporary SQLite database in tests.
- [x] Use temporary storage directory in tests.
- [x] Force fake AI in tests.
- [x] Add health tests.
- [x] Add course CRUD tests.
- [x] Add document upload tests.
- [x] Add summary generation tests.
- [x] Add flashcard generation tests.
- [x] Add quiz and attempt tests.
- [x] Add dashboard tests.
- [x] Ensure `pytest -q` passes.

### Phase 10: Mobile Foundation

- [x] Add Expo app configuration.
- [x] Add TypeScript configuration.
- [x] Add Expo Router layout.
- [x] Implement `src/api/client.ts`.
- [x] Implement `src/api/types.ts`.
- [x] Implement shared UI components.
- [x] Add API base URL setting with AsyncStorage.

### Phase 11: Mobile Screens

- [x] Implement dashboard screen.
- [x] Implement courses list screen.
- [x] Implement new course screen.
- [x] Implement course detail screen.
- [x] Implement document upload flow with `expo-document-picker`.
- [x] Implement document detail screen.
- [x] Implement summary display.
- [x] Implement flashcard display.
- [x] Implement quiz taking screen.
- [x] Implement course schedule management screen.
- [x] Show upcoming schedule on the dashboard screen.
- [x] Implement settings screen.
- [x] Handle loading, empty, and error states.
- [x] Add tablet-aware containers and responsive card grids for dashboard, course, document, schedule, saved-material, and quiz screens.

### Phase 12: Documentation

- [x] Write root README with overview, setup, architecture, demo flow, testing, limitations, and resume bullets.
- [x] Write backend README.
- [x] Write mobile README.
- [x] Document API base URL notes for iOS simulator, Android emulator, and physical devices.
- [x] Document that generated content may contain mistakes and should be verified against source materials.

### Phase 13: Deployment Prep

- [x] Add backend write-request protection with optional `BACKEND_ACCESS_TOKEN`.
- [x] Keep local development usable without a token.
- [x] Require a configured backend access token for mutating requests in production mode.
- [x] Add mobile Settings support for storing the backend access token.
- [x] Add in-memory rate limiting for write requests and stricter AI-generation requests.
- [x] Add production environment example values.
- [x] Add backend Dockerfile and root Docker Compose configuration.
- [x] Document AWS EC2 + Docker Compose deployment flow.
- [x] Clarify EC2-local SQLite/file-storage limitations and future S3/database migration path.

## Backend Endpoint Checklist

### Health

- [x] `GET /health`

### Courses

- [x] `POST /courses`
- [x] `GET /courses`
- [x] `GET /courses/{course_id}`
- [x] `PATCH /courses/{course_id}`
- [x] `DELETE /courses/{course_id}`

### Documents

- [x] `POST /documents/upload`
- [x] `GET /documents/{document_id}`
- [x] `GET /courses/{course_id}/documents`
- [x] `DELETE /documents/{document_id}`

### Summaries

- [x] `POST /documents/{document_id}/summaries`
- [x] `GET /documents/{document_id}/summaries`

### Flashcards

- [x] `POST /documents/{document_id}/flashcards`
- [x] `GET /documents/{document_id}/flashcards`

### Quizzes

- [x] `POST /documents/{document_id}/quizzes`
- [x] `GET /quizzes/{quiz_id}`
- [x] `POST /quizzes/{quiz_id}/attempts`
- [x] `POST /courses/{course_id}/review-quiz`

### Schedule

- [x] `POST /courses/{course_id}/schedule`
- [x] `GET /courses/{course_id}/schedule`
- [x] `GET /schedule`
- [x] `GET /schedule/{item_id}`
- [x] `PATCH /schedule/{item_id}`
- [x] `DELETE /schedule/{item_id}`

### Weak Topics and Dashboard

- [x] `GET /courses/{course_id}/weak-topics`
- [x] `GET /dashboard`
- [x] `GET /courses/{course_id}/dashboard`

## Mobile Screen Checklist

- [x] `app/index.tsx`: dashboard
- [x] `app/index.tsx`: global upcoming schedule
- [x] `app/courses/index.tsx`: courses list
- [x] `app/courses/new.tsx`: create course
- [x] `app/courses/[courseId].tsx`: course detail and upload
- [x] `app/documents/[documentId].tsx`: document detail and generated materials
- [x] `app/quiz/[quizId].tsx`: quiz taking
- [x] `app/schedule/course/[courseId].tsx`: course schedule management
- [x] `app/settings.tsx`: API base URL and connection test

## Test Gate

Backend implementation is not considered complete until:

```bash
cd backend
pytest -q
```

passes using fake AI and temporary test storage.

## Run Commands

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Mobile:

```bash
cd mobile
npm install
npx expo start
```

## Known Risks

- PDF extraction works only for text-based PDFs.
- Mobile device networking may require replacing `127.0.0.1` with an emulator host address or LAN IP.
- OpenAI responses may be malformed, so the backend needs parsing guards and fallback behavior.
- MVP quiz responses include correct answers for mobile simplicity; production should hide answers until submission.
- SQLite is suitable for local MVP persistence, not multi-user production scale.

## Acceptance Criteria

- [x] Backend starts with `uvicorn app.main:app --reload`.
- [x] `GET /health` returns ok.
- [x] Backend tests pass with `pytest -q`.
- [x] User can create a course.
- [x] User can upload `.txt`, `.md`, and text-based `.pdf` files.
- [x] User can generate summaries.
- [x] User can generate flashcards.
- [x] User can generate quizzes.
- [x] User can submit quiz answers and see score, missed topics, and explanations.
- [x] User can add assignment deadlines or exam dates for a course.
- [x] Dashboard shows upcoming schedule items across all courses.
- [x] Weak topics update after missed quiz questions.
- [x] Dashboard shows useful counts and recent activity.
- [x] Mobile app starts with `npx expo start`.
- [x] Mobile app can connect to backend.
- [x] README files explain setup clearly.
- [x] No API key is required for local demo.
