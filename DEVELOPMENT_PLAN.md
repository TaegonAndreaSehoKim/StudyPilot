# StudyPilot Development Plan

## Purpose

StudyPilot is an AI-powered mobile study assistant MVP. It lets students create courses, upload study materials, generate summaries, flashcards, and quizzes, take quizzes, and track weak topics.

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
9. View weak topics and dashboard activity.

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

- [ ] Create root `.gitignore`.
- [ ] Create root `README.md`.
- [ ] Create `backend/` structure.
- [ ] Create `mobile/` structure.
- [ ] Add `.env.example` files for backend and mobile.

### Phase 2: Backend Core

- [ ] Add `backend/requirements.txt`.
- [ ] Implement `app/config.py` with `pydantic-settings`.
- [ ] Implement `app/database.py` with SQLAlchemy engine, session, and startup table creation.
- [ ] Implement `app/models.py`.
- [ ] Implement `app/schemas.py`.
- [ ] Implement dependency helpers in `app/deps.py`.
- [ ] Implement FastAPI app in `app/main.py`.
- [ ] Implement `GET /health`.

### Phase 3: Course API

- [ ] Implement `POST /courses`.
- [ ] Implement `GET /courses`.
- [ ] Implement `GET /courses/{course_id}`.
- [ ] Implement `PATCH /courses/{course_id}`.
- [ ] Implement `DELETE /courses/{course_id}`.
- [ ] Include course detail counts where practical.

### Phase 4: Document Upload and Extraction

- [ ] Implement upload validation for `.txt`, `.md`, and `.pdf`.
- [ ] Enforce max upload size.
- [ ] Save files under backend storage.
- [ ] Extract text from text and markdown files.
- [ ] Extract text from text-based PDFs using `pypdf`.
- [ ] Mark scanned or image-only PDFs as unsupported.
- [ ] Implement `POST /documents/upload`.
- [ ] Implement `GET /documents/{document_id}`.
- [ ] Implement `GET /courses/{course_id}/documents`.
- [ ] Implement `DELETE /documents/{document_id}`.

### Phase 5: AI Provider Layer

- [ ] Define `AIProvider`.
- [ ] Implement deterministic `FakeAIProvider`.
- [ ] Implement `OpenAIProvider`.
- [ ] Select fake provider when `USE_FAKE_AI=true` or `OPENAI_API_KEY` is missing.
- [ ] Add robust JSON parsing and fallback behavior.
- [ ] Keep prompts source-grounded.

### Phase 6: Study Material Generation

- [ ] Implement text chunking.
- [ ] Implement summary generation service.
- [ ] Implement flashcard generation service.
- [ ] Implement quiz generation service.
- [ ] Implement `POST /documents/{document_id}/summaries`.
- [ ] Implement `GET /documents/{document_id}/summaries`.
- [ ] Implement `POST /documents/{document_id}/flashcards`.
- [ ] Implement `GET /documents/{document_id}/flashcards`.
- [ ] Implement `POST /documents/{document_id}/quizzes`.
- [ ] Implement `GET /quizzes/{quiz_id}`.

### Phase 7: Quiz Attempts and Weak Topics

- [ ] Implement quiz attempt scoring.
- [ ] Store submitted answers and explanations.
- [ ] Update weak topics for missed questions.
- [ ] Implement `POST /quizzes/{quiz_id}/attempts`.
- [ ] Implement `GET /courses/{course_id}/weak-topics`.

### Phase 8: Dashboard API

- [ ] Implement `GET /dashboard`.
- [ ] Implement `GET /courses/{course_id}/dashboard`.
- [ ] Include counts, recent courses, recent documents, recent quizzes, and weak topics.

### Phase 9: Backend Tests

- [ ] Use temporary SQLite database in tests.
- [ ] Use temporary storage directory in tests.
- [ ] Force fake AI in tests.
- [ ] Add health tests.
- [ ] Add course CRUD tests.
- [ ] Add document upload tests.
- [ ] Add summary generation tests.
- [ ] Add flashcard generation tests.
- [ ] Add quiz and attempt tests.
- [ ] Add dashboard tests.
- [ ] Ensure `pytest -q` passes.

### Phase 10: Mobile Foundation

- [ ] Add Expo app configuration.
- [ ] Add TypeScript configuration.
- [ ] Add Expo Router layout.
- [ ] Implement `src/api/client.ts`.
- [ ] Implement `src/api/types.ts`.
- [ ] Implement shared UI components.
- [ ] Add API base URL setting with AsyncStorage.

### Phase 11: Mobile Screens

- [ ] Implement dashboard screen.
- [ ] Implement courses list screen.
- [ ] Implement new course screen.
- [ ] Implement course detail screen.
- [ ] Implement document upload flow with `expo-document-picker`.
- [ ] Implement document detail screen.
- [ ] Implement summary display.
- [ ] Implement flashcard display.
- [ ] Implement quiz taking screen.
- [ ] Implement settings screen.
- [ ] Handle loading, empty, and error states.

### Phase 12: Documentation

- [ ] Write root README with overview, setup, architecture, demo flow, testing, limitations, and resume bullets.
- [ ] Write backend README.
- [ ] Write mobile README.
- [ ] Document API base URL notes for iOS simulator, Android emulator, and physical devices.
- [ ] Document that generated content may contain mistakes and should be verified against source materials.

## Backend Endpoint Checklist

### Health

- [ ] `GET /health`

### Courses

- [ ] `POST /courses`
- [ ] `GET /courses`
- [ ] `GET /courses/{course_id}`
- [ ] `PATCH /courses/{course_id}`
- [ ] `DELETE /courses/{course_id}`

### Documents

- [ ] `POST /documents/upload`
- [ ] `GET /documents/{document_id}`
- [ ] `GET /courses/{course_id}/documents`
- [ ] `DELETE /documents/{document_id}`

### Summaries

- [ ] `POST /documents/{document_id}/summaries`
- [ ] `GET /documents/{document_id}/summaries`

### Flashcards

- [ ] `POST /documents/{document_id}/flashcards`
- [ ] `GET /documents/{document_id}/flashcards`

### Quizzes

- [ ] `POST /documents/{document_id}/quizzes`
- [ ] `GET /quizzes/{quiz_id}`
- [ ] `POST /quizzes/{quiz_id}/attempts`

### Weak Topics and Dashboard

- [ ] `GET /courses/{course_id}/weak-topics`
- [ ] `GET /dashboard`
- [ ] `GET /courses/{course_id}/dashboard`

## Mobile Screen Checklist

- [ ] `app/index.tsx`: dashboard
- [ ] `app/courses/index.tsx`: courses list
- [ ] `app/courses/new.tsx`: create course
- [ ] `app/courses/[courseId].tsx`: course detail and upload
- [ ] `app/documents/[documentId].tsx`: document detail and generated materials
- [ ] `app/quiz/[quizId].tsx`: quiz taking
- [ ] `app/settings.tsx`: API base URL and connection test

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

- [ ] Backend starts with `uvicorn app.main:app --reload`.
- [ ] `GET /health` returns ok.
- [ ] Backend tests pass with `pytest -q`.
- [ ] User can create a course.
- [ ] User can upload `.txt`, `.md`, and text-based `.pdf` files.
- [ ] User can generate summaries.
- [ ] User can generate flashcards.
- [ ] User can generate quizzes.
- [ ] User can submit quiz answers and see score, missed topics, and explanations.
- [ ] Weak topics update after missed quiz questions.
- [ ] Dashboard shows useful counts and recent activity.
- [ ] Mobile app starts with `npx expo start`.
- [ ] Mobile app can connect to backend.
- [ ] README files explain setup clearly.
- [ ] No API key is required for local demo.
