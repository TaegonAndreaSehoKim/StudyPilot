# StudyPilot Backend

FastAPI backend for StudyPilot. It handles course data, document uploads, text extraction, AI generation, quizzes, weak topics, and dashboard APIs.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the FastAPI docs.

## Test

```bash
python -m pytest -q
```

The test suite forces fake AI behavior and uses temporary SQLite/storage paths.

## Demo Smoke

With the backend running, execute the full API demo flow:

```bash
python scripts/smoke_demo.py --base-url http://127.0.0.1:8000 --cleanup
```

The smoke flow creates a course, uploads the sample notes from `docs/demo/`, generates a summary, flashcards, and quiz, submits intentionally wrong answers, verifies weak topics, and optionally deletes the smoke course.

## Environment

Copy `.env.example` to `.env` if you want custom values.

```text
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

When `OPENAI_API_KEY` is missing or `USE_FAKE_AI=true`, the backend uses `FakeAIProvider`.

If `BACKEND_ACCESS_TOKEN` is set, every `POST`, `PATCH`, and `DELETE` request must include:

```text
X-StudyPilot-Key: <token>
```

In `ENVIRONMENT=production`, the backend rejects mutating requests unless `BACKEND_ACCESS_TOKEN` is configured.

Rate limiting is enabled by default. `POST`, `PATCH`, and `DELETE` requests use `MUTATION_RATE_LIMIT_PER_MINUTE`; OCR and AI-generation endpoints use the stricter `AI_RATE_LIMIT_PER_MINUTE`. Limits are in-memory and intended for the single-container EC2 MVP.

PDF extraction first uses embedded text through `pypdf`. If a PDF has no reliable embedded text or too few readable pages, it is saved with `status=needs_ocr` and `ocr_status=available`. API responses include `extraction_quality` and `extraction_coverage` so clients can explain partial extraction clearly. `POST /documents/{document_id}/ocr` starts a backend OCR job and returns a job record; use `GET /ocr-jobs/{job_id}` to poll completion. Use `OCR_PROVIDER=fake` for local demos/tests, `OCR_PROVIDER=textract` for Amazon Textract, or `OCR_PROVIDER=disabled` to turn OCR off.

## Docker

From the repository root:

```bash
docker compose up -d --build
docker compose logs -f backend
```

The Compose setup stores SQLite data in the `studypilot_data` volume and uploaded files in the `studypilot_storage` volume. See `docs/deployment/aws_ec2_docker.md` for the EC2 deployment flow.

## API Summary

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

## Notes

The generation pipeline prepares section-aware study context before calling the AI provider. The OpenAI provider is source-grounded, requests structured JSON, and validates required fields before accepting generated summaries, flashcards, or quizzes. If model output is invalid, malformed, or the provider fails, generation falls back to deterministic fake output instead of crashing the API.
