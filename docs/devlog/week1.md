# Week 1 Devlog

Week 1 covers the project setup and the first full MVP foundation pass.
The focus was to move StudyPilot from planning notes into a working local full-stack prototype.

---

## Day 1 - Planning, Repository Setup, and GitHub Connection

### Focus
Define the MVP scope, preserve the development plan, and connect the project to GitHub before starting implementation.

### What was done
- Converted the requested StudyPilot product brief into a concrete implementation plan.
- Added `DEVELOPMENT_PLAN.md` with:
  - product goal
  - non-goals
  - architecture direction
  - backend phases
  - mobile phases
  - endpoint checklist
  - acceptance criteria
- Initialized the local Git repository.
- Added `.gitignore` rules for:
  - Python virtual environments
  - SQLite database files
  - uploaded storage files
  - Node and Expo artifacts
  - `.env` files
  - IDE and OS files
- Connected the repository to GitHub:
  - `https://github.com/TaegonAndreaSehoKim/StudyPilot.git`
- Pushed the initial planning commit.

### Key decisions
- GitHub is the source of truth for code, planning notes, and documentation.
- The project will be built as a full-stack monorepo.
- The backend must be the only place that can read LLM API keys.
- The local demo must work without `OPENAI_API_KEY`.

### Result
The project had a clean repository baseline and a preserved development plan before implementation began.

---

## Day 2 - Backend Foundation and Core API

### Focus
Build the backend foundation first so mobile development has a real API contract to call.

### What was done
- Removed the default PyCharm sample `main.py`.
- Created the backend structure under `backend/`.
- Added backend dependencies in `requirements.txt`.
- Added `.env.example`.
- Implemented `app/config.py` with `pydantic-settings`.
- Implemented `app/database.py` with SQLAlchemy engine, session, table creation, and test reconfiguration support.
- Implemented SQLAlchemy models for:
  - Course
  - Document
  - Summary
  - Flashcard
  - Quiz
  - QuizQuestion
  - QuizAttempt
  - WeakTopic
- Implemented Pydantic schemas for request and response payloads.
- Added FastAPI app creation, CORS, lifespan startup, and router registration.
- Implemented `/health`.
- Implemented course CRUD endpoints.

### Key decisions
- Use SQLite for local MVP persistence.
- Use SQLAlchemy ORM rather than raw SQL.
- Keep startup table creation for MVP simplicity.
- Keep route modules separated by product area.

### Result
The backend had a stable application skeleton, persistence layer, and course API.

---

## Day 3 - Document Upload, AI Provider Layer, and Study Generation

### Focus
Connect the main study workflow: upload source material, extract text, and generate study outputs.

### What was done
- Implemented document upload validation for `.txt`, `.md`, and `.pdf`.
- Enforced upload size limits from settings.
- Saved uploads under backend storage.
- Implemented text extraction for text and markdown files.
- Implemented PDF extraction with `pypdf`.
- Marked text-poor PDFs as unsupported scanned/image-only files.
- Added document endpoints:
  - `POST /documents/upload`
  - `GET /documents/{document_id}`
  - `GET /courses/{course_id}/documents`
  - `DELETE /documents/{document_id}`
- Implemented `chunk_text`.
- Added `AIProvider` abstraction.
- Implemented deterministic `FakeAIProvider`.
- Implemented `OpenAIProvider` with safe fallback behavior.
- Implemented `StudyGenerator`.
- Added summary endpoints.
- Added flashcard endpoints.
- Added quiz generation and quiz retrieval endpoints.

### Key decisions
- Treat `FakeAIProvider` as a first-class local/demo feature.
- Keep AI calls synchronous for the MVP.
- Store structured generated output as JSON text fields where the schema is still simple.
- Use source-grounded fake outputs so the UI can be demoed without paid calls.

### Result
The backend could turn uploaded notes into summaries, flashcards, and quizzes without requiring an API key.

---

## Day 4 - Quiz Attempts, Weak Topics, Dashboard, and Backend Tests

### Focus
Complete the backend learning loop and make it test-backed.

### What was done
- Implemented quiz attempt submission.
- Added answer comparison and score calculation.
- Stored attempt answers, missed topics, and explanations.
- Implemented weak-topic updates for missed questions.
- Added course weak-topic endpoint.
- Added global dashboard endpoint.
- Added course dashboard endpoint.
- Added pytest setup using:
  - temporary SQLite database
  - temporary storage directory
  - fake AI forced through environment variables
- Added backend tests for:
  - health
  - course CRUD
  - document upload
  - unsupported extension rejection
  - upload size rejection
  - summary generation
  - flashcard generation
  - quiz generation and attempts
  - dashboard counts
  - chunking
- Cleaned warnings from FastAPI startup and SQLAlchemy query usage.

### Validation

```text
python -m pytest -q -> 11 passed
```

### Result
The backend MVP became test-backed and covered the complete local study workflow.

---

## Day 5 - Mobile Expo App Foundation

### Focus
Build the mobile shell and connect it to the backend API.

### What was done
- Created the Expo app structure under `mobile/`.
- Added Expo Router configuration.
- Added TypeScript configuration.
- Added `package.json` and installed dependencies.
- Added AsyncStorage-backed API base URL handling.
- Added `src/api/client.ts`.
- Added `src/api/types.ts`.
- Added shared UI components:
  - Button
  - Card
  - EmptyState
  - LoadingState
  - ErrorState
  - SummaryView
  - FlashcardList
  - QuizQuestionView
- Added app color constants and formatting helpers.

### Key decisions
- Keep mobile dependencies minimal.
- Use `fetch` directly instead of adding a data-fetching library.
- Make the API base URL editable because emulator and physical-device networking differ.

### Result
The mobile app had a typed API client, reusable UI components, and router foundation.

---

## Day 6 - Mobile Screens and Demo Flow

### Focus
Implement the end-to-end user flow in the mobile app.

### What was done
- Added dashboard screen.
- Added courses list screen.
- Added new course screen.
- Added course detail screen.
- Added document picker upload flow with `expo-document-picker`.
- Added document detail screen.
- Added summary generation buttons and display.
- Added flashcard generation and display.
- Added quiz generation list.
- Added quiz-taking screen.
- Added quiz submission result display with score, missed topics, and explanations.
- Added settings screen for API base URL and health check.
- Added backend `GET /documents/{document_id}/quizzes` so document detail can reload existing quizzes.

### Validation

```text
npm run typecheck -> passed
npx expo config --type public -> passed
```

### Result
The mobile app now covers the planned local MVP flow from course creation through quiz attempt review.

---

## Day 7 - Documentation Pass and First MVP Commit

### Focus
Document the project clearly enough that a developer can clone it and run the MVP.

### What was done
- Added root `README.md`.
- Added `backend/README.md`.
- Added `mobile/README.md`.
- Updated `DEVELOPMENT_PLAN.md` checkboxes to match the implemented state.
- Documented:
  - overview
  - architecture
  - setup commands
  - environment variables
  - demo flow
  - testing commands
  - known limitations
  - future improvements
  - resume bullet draft
- Verified backend health by starting the app on a temporary port and calling `/health`.
- Committed and pushed the MVP foundation.

### Validation

```text
python -m pytest -q -> 11 passed
npm run typecheck -> passed
npx expo config --type public -> passed
GET /health -> {"status":"ok","app":"StudyPilot"}
```

### Result
StudyPilot became a working local MVP foundation with backend tests, mobile TypeScript validation, and setup documentation.

---

## Week 1 Snapshot

### Current project state
- Backend starts successfully.
- Backend test suite passes at **11 passed**.
- Mobile TypeScript check passes.
- Expo config loads successfully.
- GitHub remote is connected and current.
- The app supports:
  - course creation
  - document upload
  - text extraction
  - fake-AI summary generation
  - fake-AI flashcard generation
  - fake-AI quiz generation
  - quiz attempts
  - weak-topic tracking
  - dashboard counts and recent activity

### Quality checkpoint
- Backend: `python -m pytest -q` -> **11 passed**
- Mobile: `npm run typecheck` -> passed
- Expo config: `npx expo config --type public` -> passed

### Remaining next steps
- Run `npx expo start` and complete a real device/simulator smoke test.
- Capture any mobile layout issues from screenshots.
- Improve mobile empty/error states after manual testing.
- Add mobile test coverage.
- Improve OpenAI structured-output parsing and validation.

## Day 8 - Demo Materials and PDF Upload Coverage

### Focus
Close a small MVP acceptance gap and make manual demos more repeatable.

### What was done
- Added `docs/demo/omscs_ai_sample_notes.md` as a short repeatable OMSCS AI demo document.
- Added `docs/demo/README.md` with a suggested demo flow.
- Added backend test coverage for uploading a text-based `.pdf` file.
- Generated the test PDF bytes inside the test so the repository does not need an external binary fixture.
- Updated README demo flow to point to the sample notes file.

### Validation

```text
python -m pytest tests/test_document_upload.py -q -> 5 passed
python -m pytest -q -> 12 passed
npm run typecheck -> passed
npx expo config --type public -> passed
```

### Result
The backend now has direct regression coverage for `.txt`, `.md`, and text-based `.pdf` uploads.
The project also has a small sample note file that can be used for consistent mobile demos.

---

## Week 1 Updated Snapshot

### Current project state
- Backend starts successfully.
- Backend test suite passes at **12 passed**.
- Mobile TypeScript check passes.
- Expo config loads successfully.
- GitHub remote is connected and current.
- Demo materials exist under `docs/demo/`.
- The app supports:
  - course creation
  - document upload for `.txt`, `.md`, and text-based `.pdf`
  - text extraction
  - fake-AI summary generation
  - fake-AI flashcard generation
  - fake-AI quiz generation
  - quiz attempts
  - weak-topic tracking
  - dashboard counts and recent activity

### Quality checkpoint
- Backend: `python -m pytest -q` -> **12 passed**
- Mobile: `npm run typecheck` -> passed
- Expo config: `npx expo config --type public` -> passed

### Remaining next steps
- Run `npx expo start` and complete a real device/simulator smoke test.
- Capture any mobile layout issues from screenshots.
- Improve mobile empty/error states after manual testing.
- Add mobile test coverage.
- Improve OpenAI structured-output parsing and validation.

---

## Day 9 - Backend Demo Smoke and Expo Startup Check

### Focus
Make the demo flow easier to verify repeatedly and confirm the mobile project can start under Expo.

### What was done
- Added `backend/scripts/smoke_demo.py`.
- The smoke script verifies the full backend demo path against a running API:
  - health check
  - course creation
  - sample note upload
  - summary generation
  - flashcard generation
  - quiz generation
  - intentionally wrong quiz attempt
  - weak-topic update
  - dashboard counts
- Added backend README instructions for the smoke script.
- Fixed backend storage path handling so relative `STORAGE_DIR` values resolve from `backend/`.
- Added config tests for storage path resolution.
- Fixed Expo SDK dependency drift by aligning packages with `npx expo install`.
- Added explicit `react-dom` and `react-native-web` dependencies so Expo Router/runtime dependency resolution stays consistent.
- Confirmed Expo dependency compatibility with `npx expo install --check`.
- Smoke-checked Metro startup with `npx expo start --localhost --port 8085`.

### Smoke result

```json
{
  "health": {
    "status": "ok",
    "app": "StudyPilot"
  },
  "document_status": "extracted",
  "flashcard_count": 5,
  "question_count": 3,
  "attempt_score": 0.0,
  "weak_topic_count": 3,
  "cleanup": true
}
```

Metro startup reached:

```text
Waiting on http://localhost:8085
```

### Validation

```text
python -m pytest -q -> 14 passed
npm run typecheck -> passed
npx expo install --check -> Dependencies are up to date
npx expo config --type public -> passed
```

### Result
The backend demo flow is now repeatable through a single command, default upload storage resolves correctly, and the mobile dependency set is aligned with Expo SDK 55.

---

## Week 1 Latest Snapshot

### Current project state
- Backend starts successfully.
- Backend test suite passes at **14 passed**.
- Backend demo smoke flow passes against a running API.
- Mobile TypeScript check passes.
- Expo dependency compatibility check passes.
- Expo config loads successfully.
- Expo Metro starts and reaches `Waiting on http://localhost:8085`.
- Demo materials exist under `docs/demo/`.

### Remaining next steps
- Complete an interactive simulator or physical-device pass through the mobile UI.
- Capture any mobile layout issues from screenshots.
- Improve mobile empty/error states after manual testing.
- Add mobile test coverage.
- Improve OpenAI structured-output parsing and validation.
