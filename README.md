# StudyPilot - AI-Powered Mobile Study Assistant

StudyPilot is a local-first mobile study assistant that turns course materials into summaries, flashcards, quizzes, and weak-topic reviews.

The project is built as a full-stack monorepo with a React Native Expo mobile app and a FastAPI backend. It is designed to feel like an early-stage product MVP rather than a toy demo, while still staying simple enough to run locally after cloning.

The MVP works without an OpenAI API key. When `OPENAI_API_KEY` is missing, the backend automatically uses a deterministic fake AI provider so the full demo flow and backend tests can run without external network calls or paid API usage.

## Highlights

- **Mobile app:** Expo Router, React Native, TypeScript
- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Document support:** `.txt`, `.md`, text-based `.pdf`, and OCR handoff for scanned PDFs
- **Study generation:** summaries, flashcards, and multiple-choice quizzes
- **Quality loop:** section-aware generation, weak-topic review quizzes, and lightweight AI quality evals
- **Learning loop:** quiz attempts update weak-topic tracking
- **Tablet layout:** responsive containers and card grids for wider Expo tablet displays
- **Local demo mode:** deterministic `FakeAIProvider` is used when no API key exists
- **Security boundary:** mobile app never reads or stores LLM API keys
- **Quality checkpoint:** backend pytest suite currently passes at `59 passed`; mobile TypeScript and Expo export checks pass

The mobile app currently targets Expo SDK 54 so it can run in the App Store version of Expo Go.

## Current Status

StudyPilot currently supports:

- course creation and listing
- course detail dashboards
- course schedule tracking for assignments, exams, readings, projects, and milestones
- global upcoming schedule view across all courses
- document upload and extraction
- PDF extraction diagnostics with `needs_ocr`, quality labels, page coverage, and optional OCR execution
- document previews, full extracted-text reading, original-file download, and guided generation options
- fake-AI summary generation
- saved summary detail screens with share/export support
- fake-AI flashcard generation
- saved course flashcard review with share/export support
- fake-AI quiz generation
- saved course quiz review
- quiz taking, scoring, source-grounded explanations, and highlighted answer review
- course-level quiz attempt history
- weak-topic review quiz generation
- weak-topic tracking from missed questions
- global dashboard with counts, upcoming schedule, recent courses, recent documents, recent generated materials, and weak topics
- mobile API base URL settings
- tablet-friendly responsive layouts for dashboard, course, document, schedule, quiz, and saved-material screens
- backend access token protection and in-memory rate limiting for write and AI-generation requests
- backend test coverage for the core local workflow

Current validation state:

- `python -m pytest -q` from `backend/` -> `59 passed`
- `npm run typecheck` from `mobile/` -> passed
- `npx expo install --check` from `mobile/` -> dependencies up to date
- `npx expo config --type public` from `mobile/` -> passed
- `npx expo start --localhost --port 8085` reached `Waiting on http://localhost:8085`
- backend `/health` smoke check returned `{"status":"ok","app":"StudyPilot"}`
- backend demo smoke flow passed with course, upload, summary, flashcards, quiz, attempt, weak topics, and dashboard verification

---

## What the Project Does

StudyPilot supports the following flow:

1. Create a course, such as `OMSCS AI`.
2. Upload lecture notes, markdown notes, text files, or text-based PDFs.
3. Extract text on the backend.
4. Generate a concise or exam-focused summary.
5. Generate flashcards.
6. Generate a quiz.
7. Take the quiz in the mobile app.
8. Save attempt results.
9. Track missed topics as weak topics.
10. Review recent activity and weak topics on the dashboard.

The current implementation is intentionally transparent and local-first. It is designed for demo-quality study workflows and future extension.

---

## Architecture

```text
Expo mobile app
  -> fetch HTTP requests
FastAPI backend
  -> SQLite database
  -> local upload storage
  -> AIProvider abstraction
       -> FakeAIProvider when OPENAI_API_KEY is missing
       -> OpenAIProvider when OPENAI_API_KEY is set
```

The mobile app calls the FastAPI backend only. It does not access OpenAI or any LLM provider directly.

Architecture notes:

- `docs/architecture/overview.md`
- `docs/architecture/schema.md`

Agent/developer guidance:

- `AGENTS.md`

---

## Project Structure

```text
StudyPilot/
├── AGENTS.md
├── DEVELOPMENT_PLAN.md
├── README.md
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── main.py
│   ├── tests/
│   ├── README.md
│   └── requirements.txt
├── docs/
│   └── architecture/
└── mobile/
    ├── app/
    ├── src/
    ├── README.md
    └── package.json
```

---

## Backend Setup

Create and activate a virtual environment, then install dependencies.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "app": "StudyPilot"
}
```

---

## Mobile Setup

Install dependencies:

```bash
cd mobile
npm install
```

Start Expo:

```bash
npx expo start
```

The mobile app stores the API base URL in Settings.
If the backend has `BACKEND_ACCESS_TOKEN` configured, enter the same backend access token in Settings. This is not an OpenAI API key.

Common backend URLs:

- iOS simulator: `http://127.0.0.1:8000`
- Android emulator: `http://10.0.2.2:8000`
- Physical device: `http://<your-computer-lan-ip>:8000`

For physical-device testing, run the backend with:

```bash
uvicorn app.main:app --host 0.0.0.0 --reload
```

---

## Environment Variables

Backend variables are documented in `backend/.env.example`.

```text
APP_NAME=StudyPilot
ENVIRONMENT=development
DATABASE_URL=sqlite:///./studypilot.db
STORAGE_DIR=app/storage
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.5
USE_FAKE_AI=false
BACKEND_ACCESS_TOKEN=
CORS_ORIGINS=*
RATE_LIMIT_ENABLED=true
MUTATION_RATE_LIMIT_PER_MINUTE=60
AI_RATE_LIMIT_PER_MINUTE=12
OCR_PROVIDER=fake
AWS_REGION=us-east-1
MAX_UPLOAD_MB=10
```

AI provider behavior:

- if `USE_FAKE_AI=true`, use `FakeAIProvider`
- if `OPENAI_API_KEY` is missing, use `FakeAIProvider`
- if `OPENAI_API_KEY` exists and `USE_FAKE_AI=false`, use `OpenAIProvider`

Do not place LLM API keys in the mobile app.

API access behavior:

- `GET` endpoints such as `/health` and dashboards remain readable.
- If `BACKEND_ACCESS_TOKEN` is set, every `POST`, `PATCH`, and `DELETE` request must include `X-StudyPilot-Key`.
- In `ENVIRONMENT=production`, mutating requests fail unless `BACKEND_ACCESS_TOKEN` is configured.
- Mutating requests are rate-limited in memory. OCR and AI-generation endpoints use the stricter `AI_RATE_LIMIT_PER_MINUTE` limit.
- OCR uses `OCR_PROVIDER=fake` for local demos/tests. Set `OCR_PROVIDER=textract` and configure AWS credentials on the backend host for real scanned PDFs. `POST /documents/{document_id}/ocr` starts a backend OCR job and returns a job record; poll `GET /ocr-jobs/{job_id}` until it is completed or failed.

---

## Docker And AWS Deployment

The current deployment MVP is one EC2 instance running the backend with Docker Compose:

```bash
cp backend/.env.production.example backend/.env
docker compose up -d --build
docker compose logs -f backend
```

The Compose setup stores SQLite in the `studypilot_data` volume and uploaded files in the `studypilot_storage` volume.

For a stable mobile API URL, associate an Elastic IP with the EC2 instance and use `http://<elastic-ip>:8000` in the mobile Settings screen. Full deployment notes are in `docs/deployment/aws_ec2_docker.md`.

---

## API Usage

Main endpoints:

- `GET /health`
- `POST /courses`
- `GET /courses`
- `GET /courses/{course_id}`
- `PATCH /courses/{course_id}`
- `DELETE /courses/{course_id}`
- `POST /documents/upload`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/text`
- `GET /documents/{document_id}/download`
- `POST /documents/{document_id}/ocr`
- `GET /ocr-jobs/{job_id}`
- `GET /courses/{course_id}/documents`
- `DELETE /documents/{document_id}`
- `POST /documents/{document_id}/summaries`
- `GET /documents/{document_id}/summaries`
- `GET /summaries/{summary_id}`
- `GET /courses/{course_id}/summaries`
- `POST /documents/{document_id}/flashcards`
- `GET /documents/{document_id}/flashcards`
- `GET /courses/{course_id}/flashcards`
- `POST /documents/{document_id}/quizzes`
- `POST /courses/{course_id}/review-quiz`
- `GET /documents/{document_id}/quizzes`
- `GET /courses/{course_id}/quizzes`
- `GET /quizzes/{quiz_id}`
- `GET /quizzes/{quiz_id}/attempts`
- `GET /courses/{course_id}/attempts`
- `POST /quizzes/{quiz_id}/attempts`
- `POST /courses/{course_id}/schedule`
- `GET /courses/{course_id}/schedule`
- `GET /schedule`
- `GET /schedule/{item_id}`
- `PATCH /schedule/{item_id}`
- `DELETE /schedule/{item_id}`
- `GET /courses/{course_id}/weak-topics`
- `GET /dashboard`
- `GET /courses/{course_id}/dashboard`

### Create a Course

```json
POST /courses
{
  "title": "OMSCS AI",
  "description": "Artificial Intelligence notes"
}
```

### Upload a Document

Use multipart form data:

```text
POST /documents/upload
course_id=<course id>
file=<notes.txt | notes.md | notes.pdf>
```

### Generate a Summary

```json
POST /documents/1/summaries
{
  "summary_type": "concise"
}
```

Supported summary types:

- `concise`: summarize core concepts and the broad flow of the material
- `detailed`: explain the concepts at a general/theoretical level, prioritizing principles over examples
- `exam`: focus on likely test points, similar-concept comparisons, and memorization anchors

### Generate Flashcards

```json
POST /documents/1/flashcards
{
  "count": 10
}
```

### Generate a Quiz

```json
POST /documents/1/quizzes
{
  "question_count": 5,
  "difficulty": "mixed"
}
```

### Generate a Weak-Topic Review Quiz

```json
POST /courses/1/review-quiz
{
  "question_count": 5,
  "difficulty": "medium"
}
```

If `topics` is omitted, StudyPilot uses the course's highest-miss weak topics.

### Submit a Quiz Attempt

```json
POST /quizzes/1/attempts
{
  "answers": [
    {
      "question_id": 1,
      "selected_answer": "A"
    }
  ]
}
```

---

## Demo Flow

For a detailed Expo Go checklist, see [`docs/demo/mobile_walkthrough.md`](docs/demo/mobile_walkthrough.md).

1. Start the backend.
2. Start the mobile app.
3. Open Settings and test the backend connection.
4. Create a course such as `OMSCS AI`.
5. Open the course.
6. Upload a `.txt`, `.md`, or text-based `.pdf` file. For a repeatable text upload demo, use `docs/demo/sample-study-notes.txt`; for markdown, use `docs/demo/omscs_ai_sample_notes.md`.
7. Open the uploaded document.
8. Open the full extracted text or original file if you need to inspect the source.
9. Generate a concise summary.
10. Open the saved summary from the course screen and use Save / Share if needed.
11. Generate flashcards.
12. Generate a quiz.
13. Take the quiz and submit answers.
14. Return to the dashboard to inspect weak topics and recent activity.

---

## Testing

Run the backend suite:

```bash
cd backend
python -m pytest -q
```

Current status:

```text
59 passed
```

The backend tests use:

- temporary SQLite databases
- temporary upload storage
- fake AI
- no external model API calls

Run the mobile type check:

```bash
cd mobile
npm run typecheck
```

Run all mobile local checks:

```bash
cd mobile
npm run check
```

Check Expo config loading:

```bash
cd mobile
npx expo config --type public
```

Run the Expo web bundle smoke:

```bash
cd mobile
npm run export:web
```

Run the backend demo smoke flow against a running backend:

```bash
cd backend
python scripts/smoke_demo.py --base-url http://127.0.0.1:8000 --cleanup
```

Check Expo dependency compatibility:

```bash
cd mobile
npx expo install --check
```

GitHub Actions runs backend tests and mobile checks on pushes and pull requests to `main`.

---

## Known Limitations

- No authentication or multi-user support.
- SQLite and local file storage are intended for local MVP persistence. The Docker deployment keeps them in EC2-local volumes.
- PDF extraction first uses embedded text. Scanned/image-only PDFs and low-coverage partial extractions are marked `needs_ocr` and can be processed through a backend OCR job using the configured OCR provider.
- The built-in fake OCR provider is for demos/tests; real OCR requires Amazon Textract configuration and AWS credentials.
- The mobile document screen shows a bounded extracted-text preview; summaries, flashcards, and quizzes use the full extracted text stored by the backend.
- OCR jobs use FastAPI background tasks for the single-server MVP. A production deployment should move OCR work to a durable queue.
- AI calls are synchronous.
- The OpenAI provider validates required summary, flashcard, and quiz fields before accepting model output, then falls back to fake AI if the response shape is unsafe.
- Quiz responses include correct answers in the MVP API for mobile simplicity.
- Mobile automated tests are not added yet.
- Docker Compose deployment notes exist for an EC2 MVP, but there is no managed database, S3 storage, HTTPS reverse proxy, or app store packaging yet.
- Generated study material may contain mistakes. Students should verify against original course materials.

---

## Next Steps

Planned follow-up improvements:

- run a full simulator or physical-device Expo smoke test
- capture screenshots and polish mobile layout
- add mobile component or interaction tests
- improve strict OpenAI JSON Schema enforcement
- improve document-generation error states
- hide quiz correct answers until submission in a production-oriented API mode
- add HTTPS/reverse proxy and S3 once the EC2 MVP is exercised

---

## Resume Bullet Draft

StudyPilot — AI-Powered Mobile Study Assistant | React Native, Expo, FastAPI, Python, SQLite, LLM APIs

- Built a mobile study assistant that imports course materials and generates structured summaries, flashcards, quizzes, and weak-topic reviews through a FastAPI-based AI pipeline.
- Implemented document upload, PDF/text extraction, chunking, prompt-based generation, quiz attempts, and mobile dashboard views for personalized study workflows.
- Added deterministic fake-AI mode and pytest coverage to support local demos without external API calls.
