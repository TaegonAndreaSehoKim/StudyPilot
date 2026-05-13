# StudyPilot Architecture Overview

StudyPilot is a full-stack local MVP for turning uploaded course materials into interactive study tools.

The architecture is intentionally simple:

```text
Expo mobile app
  -> HTTP fetch calls
FastAPI backend
  -> SQLite database
  -> local document storage
  -> OCR provider abstraction
  -> AI provider abstraction
       -> FakeAIProvider by default without API key
       -> OpenAIProvider when OPENAI_API_KEY exists
```

## Product Flow

1. A user creates a course.
2. The user uploads course material such as `.txt`, `.md`, text-based `.pdf`, or scanned PDFs.
3. The backend saves the file and extracts text.
4. If a PDF has too little embedded text, the backend marks it `needs_ocr`; the user can run OCR before generation.
5. The backend prepares section-aware study context from the extracted text.
6. The user requests generated study material:
   - concise summary
   - exam-focused summary
   - flashcards
   - quiz
7. The backend calls the configured AI provider.
8. Generated materials are persisted in SQLite.
9. The user takes a quiz.
10. The backend scores the attempt and updates weak topics.
11. The user can generate weak-topic review quizzes from missed topics.
12. Dashboard endpoints surface counts, recent activity, generated materials, schedules, and weak topics.

## Backend

The backend lives under `backend/app`.

Main responsibilities:

- expose FastAPI routes
- validate request payloads
- manage SQLite persistence through SQLAlchemy
- save uploaded files
- extract embedded document text and identify OCR-required PDFs
- run optional OCR through fake local OCR or Amazon Textract
- prepare section-aware study context
- select fake or real AI provider
- persist generated summaries, flashcards, quizzes, and attempts
- update weak-topic counters

Important files:

- `main.py`: FastAPI app factory, CORS, router registration, startup table creation
- `config.py`: environment-driven settings
- `database.py`: SQLAlchemy engine/session helpers
- `models.py`: ORM models
- `schemas.py`: Pydantic request/response models
- `routers/`: API route modules
- `services/`: extraction, chunking, AI, study generation, weak-topic logic

## Mobile

The mobile app lives under `mobile/`.

Main responsibilities:

- route between dashboard, courses, documents, quizzes, and settings
- store editable API base URL in AsyncStorage
- call the FastAPI backend through `fetch`
- pick local documents through `expo-document-picker`
- render summaries, flashcards, quizzes, and attempt results

Important files:

- `app/_layout.tsx`: Expo Router stack
- `app/index.tsx`: dashboard
- `app/courses/`: course list, creation, detail, upload
- `app/documents/[documentId].tsx`: document preview and generated materials
- `app/quiz/[quizId].tsx`: quiz taking and result review
- `app/settings.tsx`: API base URL and health check
- `src/api/client.ts`: backend client
- `src/api/types.ts`: TypeScript API contracts
- `src/components/`: shared UI components

## AI Provider Boundary

The AI provider boundary is backend-only.

The mobile app must never read:

- `OPENAI_API_KEY`
- model provider credentials
- provider-specific configuration beyond the backend URL

Provider selection:

```text
USE_FAKE_AI=true
  -> FakeAIProvider

OPENAI_API_KEY missing
  -> FakeAIProvider

OPENAI_API_KEY present and USE_FAKE_AI=false
  -> OpenAIProvider
```

`FakeAIProvider` is part of the product, not just a test stub. It keeps local demos free and deterministic. Quality eval tests assert that generated topics, explanations, source quotes, and insufficient-source behavior stay useful for demos.

## OCR Provider Boundary

OCR is backend-only. The mobile app can request OCR through the backend but never receives AWS credentials.

Provider selection:

```text
OCR_PROVIDER=fake
  -> FakeOCRProvider

OCR_PROVIDER=textract
  -> TextractOCRProvider

OCR_PROVIDER=disabled
  -> OCR endpoint returns an error
```

The backend first tries embedded PDF text with `pypdf`. If too little text is found, the document is saved as `needs_ocr`. Partially extracted PDFs remain usable but can show `ocr_status=recommended`.

## Persistence

SQLite is used for local MVP persistence.

Stored records include:

- courses
- uploaded documents
- summaries
- flashcards
- quizzes
- quiz questions
- quiz attempts
- weak topics

Uploaded files are stored under `backend/app/storage/documents/` by default. Relative `STORAGE_DIR` values are resolved from the `backend/` directory.

## Testing Strategy

Backend tests use:

- temporary SQLite database files
- temporary storage directories
- fake AI only
- FastAPI TestClient

Current backend coverage checks:

- health
- course CRUD
- document upload
- text-based PDF upload extraction
- summary generation
- flashcard generation
- quiz generation and attempts
- dashboard counts
- text chunking

Mobile currently has TypeScript validation through:

```bash
npm run typecheck
```

## Current Limitations

- no authentication
- no cloud storage
- no production database migrations
- OCR is synchronous in the MVP and should move to a background job for large PDFs
- no background job queue
- no mobile automated tests yet
- correct quiz answers are included in MVP quiz payloads

These limitations are acceptable for the current local MVP stage.
