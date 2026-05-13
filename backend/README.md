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

## Environment

Copy `.env.example` to `.env` if you want custom values.

```text
DATABASE_URL=sqlite:///./studypilot.db
STORAGE_DIR=backend/app/storage
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.5
USE_FAKE_AI=false
MAX_UPLOAD_MB=10
```

When `OPENAI_API_KEY` is missing or `USE_FAKE_AI=true`, the backend uses `FakeAIProvider`.

## API Summary

- `GET /health`
- `POST /courses`
- `GET /courses`
- `GET /courses/{course_id}`
- `PATCH /courses/{course_id}`
- `DELETE /courses/{course_id}`
- `POST /documents/upload`
- `GET /documents/{document_id}`
- `GET /courses/{course_id}/documents`
- `DELETE /documents/{document_id}`
- `POST /documents/{document_id}/summaries`
- `GET /documents/{document_id}/summaries`
- `POST /documents/{document_id}/flashcards`
- `GET /documents/{document_id}/flashcards`
- `POST /documents/{document_id}/quizzes`
- `GET /documents/{document_id}/quizzes`
- `GET /quizzes/{quiz_id}`
- `POST /quizzes/{quiz_id}/attempts`
- `GET /courses/{course_id}/weak-topics`
- `GET /dashboard`
- `GET /courses/{course_id}/dashboard`

## Notes

The OpenAI provider is source-grounded and requests structured JSON. If model output is invalid or the provider fails, generation falls back to deterministic fake output instead of crashing the API.
