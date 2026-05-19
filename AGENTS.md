# AGENTS.md

## Purpose

This file gives future coding agents a practical operating guide for `StudyPilot`.
It reflects the project state after the first MVP foundation pass.

## Project Snapshot

StudyPilot is currently a local, demoable AI study assistant MVP with:

- Expo Router mobile app under `mobile/`
- FastAPI backend under `backend/`
- SQLite-backed local persistence
- local uploaded-document storage
- course creation and listing
- section creation for units, chapters, midterms, finals, or other study scopes
- document upload for `.txt`, `.md`, text-based `.pdf`, OCR-required scanned PDFs, and low-coverage partial PDFs
- text-based PDF upload regression coverage
- fake OCR provider for local tests and optional Textract provider for deployment
- backend OCR job records with mobile polling
- section-aware document preparation before AI generation
- backend-only AI provider abstraction
- deterministic `FakeAIProvider` fallback when `OPENAI_API_KEY` is absent
- document-level summary/additional-explanation/flashcard/quiz generation endpoints
- section-level summary/additional-explanation and quiz generation endpoints over multiple uploaded documents
- quiz attempt scoring
- weak-topic tracking from missed quiz questions
- weak-topic review quiz generation
- dashboard endpoints for counts, recent activity, and weak topics
- backend access token protection and in-memory rate limiting for mutating and AI-generation requests
- EC2 Docker backend deployment notes and EAS preview update workflow
- mobile smoke checks for route/config/update setup
- repeatable mobile demo walkthrough and presentation script
- pytest coverage for the core backend workflow
- TypeScript mobile API client and screens for the main demo flow

This is not yet production software. It is a strong local MVP intended to support demos, resume discussion, and future iteration.

## Current Development Stage

The project has moved past the initial planning stage and now has a working foundation.

What is stable:

- backend app startup
- health endpoint
- course CRUD
- section CRUD
- document upload and text extraction for supported files
- text-based PDF extraction regression coverage
- fake AI generation path
- document-level and section-level summary/additional-explanation/quiz, flashcard, attempt, weak-topic, and dashboard API flows
- lightweight AI quality eval tests
- backend tests using temporary SQLite and temporary storage
- mobile routing and API client structure
- mobile dashboard, course, section, document, quiz, and settings screens
- tablet-aware mobile layout containers and responsive card grids
- EAS preview update setup for Expo Go device checks
- mobile smoke checks through `npm run smoke`
- demo walkthrough/script documentation

What is still in progress:

- hands-on mobile device testing with Expo
- UI polish after real device screenshots
- hands-on validation of real scanned PDFs through Textract
- stricter OpenAI JSON Schema enforcement
- richer frontend/mobile automated testing beyond smoke checks
- richer empty/error states and loading feedback
- screenshot capture documentation

What is not built yet:

- authentication
- managed database persistence
- push notifications
- vector search, embeddings, or RAG
- spaced repetition scheduling

## Source of Truth

Use these files first when reasoning about behavior:

- `README.md`
- `DEVELOPMENT_PLAN.md`
- `docs/architecture/overview.md`
- `docs/architecture/schema.md`
- `docs/deployment/aws_ec2_docker.md`
- `docs/deployment/eas_preview_updates.md`
- `docs/demo/mobile_walkthrough.md`
- `docs/demo/demo_script.md`
- `backend/app/main.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/services/ai_provider.py`
- `backend/app/services/document_extractor.py`
- `backend/app/services/ocr_provider.py`
- `backend/app/routers/quizzes.py`
- `mobile/src/api/client.ts`
- `mobile/src/api/types.ts`

For current quality expectations, read:

- `backend/tests/test_health.py`
- `backend/tests/test_courses.py`
- `backend/tests/test_document_upload.py`
- `backend/tests/test_document_extractor.py`
- `backend/tests/test_summary_generation.py`
- `backend/tests/test_flashcards.py`
- `backend/tests/test_quizzes.py`
- `backend/tests/test_dashboard.py`
- `backend/tests/test_chunking.py`
- `backend/tests/test_ai_provider.py`
- `backend/tests/test_document_structure.py`
- `backend/tests/test_quality_eval.py`

## Working Principles

1. Preserve backend-only LLM access.
   Never add an OpenAI or LLM provider key to the mobile app. The mobile app should call FastAPI only.

2. Keep fake AI reliable.
   Local demos and tests depend on deterministic generation when no API key is configured.

3. Keep generation source-grounded.
   Summaries, flashcards, and quizzes should come from uploaded document text. Section-level summaries and quizzes should come from the uploaded documents assigned to that section. Do not introduce behavior that invents unsupported facts.

4. Prefer small, test-backed changes.
   Backend behavior should usually be covered with pytest before the task is considered complete.

5. Keep the MVP simple.
   Avoid adding embeddings, background workers, auth, or cloud services unless the task explicitly moves into that milestone.

6. Preserve mobile/backend contract clarity.
   If an API response shape changes, update `backend/app/schemas.py`, backend tests, and `mobile/src/api/types.ts` together.

## Current Priorities

When choosing what to improve next, bias toward these:

- run a full manual Expo demo flow against the local backend
- exercise the EC2 Docker Compose deployment path with a real device
- inspect and polish the tablet layout on a real iPad or tablet simulator
- expand mobile smoke checks into lightweight component or interaction checks
- continue hardening OpenAI structured-output validation with focused regression tests
- refine fake AI output quality without making it nondeterministic
- add screenshots or a short demo video walkthrough

Lower priority for now:

- authentication
- production-grade cloud deployment beyond the EC2 Docker MVP
- vector databases
- advanced spaced repetition
- large dependency additions

## Known Risks and Footguns

1. `OPENAI_API_KEY` is optional by design.
   Do not treat missing API keys as an error. Missing keys should route to `FakeAIProvider`.

2. PDF extraction is embedded-text first.
   Scanned, image-only, or low page-coverage PDFs should be marked `needs_ocr`; OCR runs only when explicitly requested through the backend.

3. OCR jobs are FastAPI background tasks.
   This is enough for the single-server MVP. Use a durable worker queue before relying on OCR jobs for production-scale large PDFs.

4. SQLite is local MVP persistence.
   Do not overfit the code to multi-user production assumptions before auth and database migration are planned.

5. Mobile localhost differs by target.
   iOS simulator, Android emulator, and physical devices need different API base URLs. Keep the Settings screen working.

6. Tests should not call real OpenAI APIs.
   Test setup must keep fake AI and fake OCR forced and should avoid network-dependent assertions.

7. `BACKEND_ACCESS_TOKEN` is a shared backend guard, not user authentication.
   Keep it out of source control. Mobile stores this token only for backend access; never store `OPENAI_API_KEY` in mobile.

8. Rate limits are in-memory and per process.
   They are appropriate for the single-container EC2 MVP, but should move to Redis, a gateway, or managed protection before multi-instance deployment.

8. MVP quiz responses include correct answers.
   This is acceptable for local mobile simplicity, but production should hide answers until submission.

9. Relative backend storage paths are resolved from `backend/`.
   Keep this behavior intact so `cd backend && uvicorn app.main:app --reload` stores uploads under `backend/app/storage`.

## Editing Guidance

- Prefer changing backend behavior in service modules before duplicating logic in routers.
- Use Pydantic schemas for API request/response changes.
- If adding a model field, update SQLAlchemy models, schemas, tests, and mobile types together.
- If changing quiz attempt behavior, verify weak-topic updates.
- If changing upload handling, verify max-size and unsupported-extension tests.
- If changing mobile routes, verify links from dashboard, course detail, document detail, and quiz screens.
- Do not commit `.env`, local database files, uploaded documents, `node_modules`, or generated Expo artifacts.
- Keep durable documentation in sync when behavior changes, especially `README.md`, `AGENTS.md`, and architecture notes.

## Validation Checklist

Run backend tests before closing backend or full-stack changes:

```powershell
cd backend
python -m pytest -q
```

Run mobile type checking before closing mobile changes:

```powershell
cd mobile
npm run typecheck
```

Run mobile smoke checks for app config, routes, EAS preview setup, and backend-token wiring:

```powershell
cd mobile
npm run smoke
```

For mobile changes that touch routing, dependencies, or imports, also run:

```powershell
npm run smoke
npx expo install --check
npx expo export --platform web --output-dir .expo-export-smoke
```

Useful smoke checks:

```powershell
cd backend
uvicorn app.main:app --reload
```

With the backend running:

```powershell
python scripts/smoke_demo.py --base-url http://127.0.0.1:8000 --cleanup
```

```powershell
cd mobile
npx expo install --check
npx expo config --type public
npx expo export --platform web --output-dir .expo-export-smoke
npx expo start
```

Docker deployment config smoke:

```powershell
docker compose config
```

Manual product smoke:

1. Start backend.
2. Start Expo.
3. Test Settings connection.
4. Create a course.
5. Create a section such as `Midterm 1`.
6. Upload one or more `.txt` or `.md` documents into the section.
7. Generate a section summary.
8. Generate a section quiz.
9. Submit quiz answers.
10. Confirm weak topics update.

## Preferred Change Pattern

For most tasks:

1. Read the relevant router/service and tests.
2. Make the smallest coherent change.
3. Update or add backend tests when behavior changes.
4. Update mobile types/client when API shape changes.
5. Run targeted checks.
6. Update durable docs when the task changes setup, architecture, or operating expectations.

## Commit Convention

- Prefer Conventional Commit style messages such as `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, or `chore: ...`.
- Keep the subject line concise and focused on the outcome.
- Group related code, test, and documentation changes when they serve the same milestone.

## Near-Term Roadmap

Reasonable next milestones:

- run and polish the full Expo manual demo
- improve mobile UI density and interaction feedback
- expand frontend/mobile tests beyond smoke checks
- strengthen OpenAI retry/fallback behavior around valid but low-quality model outputs
- prepare demo screenshots or a short video walkthrough
- test the EC2 Docker Compose deployment path
- plan managed database, S3, and HTTPS after the EC2 MVP is stable

## Default Mindset

This repository rewards practical iteration over architectural ambition.
Keep the local demo working, keep AI access backend-only, preserve deterministic fake AI, and make the study workflow clearer with each change.
