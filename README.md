# StudyPilot — AI-Powered Mobile Study Assistant

StudyPilot is a local-first mobile study assistant that turns course materials into summaries, flashcards, quizzes, and weak-topic reviews.

The project is built as a full-stack monorepo with a React Native Expo mobile app and a FastAPI backend. It is designed to feel like an early-stage product MVP rather than a toy demo, while still staying simple enough to run locally after cloning.

The MVP works without an OpenAI API key. When `OPENAI_API_KEY` is missing, the backend automatically uses a deterministic fake AI provider so the full demo flow and backend tests can run without external network calls or paid API usage.

## Highlights

- **Mobile app:** Expo Router, React Native, TypeScript
- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Document support:** `.txt`, `.md`, and text-based `.pdf`
- **Study generation:** summaries, flashcards, and multiple-choice quizzes
- **Learning loop:** quiz attempts update weak-topic tracking
- **Local demo mode:** deterministic `FakeAIProvider` is used when no API key exists
- **Security boundary:** mobile app never reads or stores LLM API keys
- **Quality checkpoint:** backend pytest suite currently passes at `11 passed`; mobile TypeScript check passes

## Current Status

StudyPilot currently supports:

- course creation and listing
- course detail dashboards
- document upload and extraction
- document previews
- fake-AI summary generation
- fake-AI flashcard generation
- fake-AI quiz generation
- quiz taking and scoring
- weak-topic tracking from missed questions
- global dashboard with counts, recent courses, recent documents, and weak topics
- mobile API base URL settings
- backend test coverage for the core local workflow

Current validation state:

- `python -m pytest -q` from `backend/` -> `11 passed`
- `npm run typecheck` from `mobile/` -> passed
- `npx expo config --type public` from `mobile/` -> passed
- backend `/health` smoke check returned `{"status":"ok","app":"StudyPilot"}`

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

Development log:

- `docs/devlog/week1.md`

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
│   ├── architecture/
│   └── devlog/
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
DATABASE_URL=sqlite:///./studypilot.db
STORAGE_DIR=backend/app/storage
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.5
USE_FAKE_AI=false
MAX_UPLOAD_MB=10
```

AI provider behavior:

- if `USE_FAKE_AI=true`, use `FakeAIProvider`
- if `OPENAI_API_KEY` is missing, use `FakeAIProvider`
- if `OPENAI_API_KEY` exists and `USE_FAKE_AI=false`, use `OpenAIProvider`

Do not place LLM API keys in the mobile app.

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

- `concise`
- `detailed`
- `exam`

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

1. Start the backend.
2. Start the mobile app.
3. Open Settings and test the backend connection.
4. Create a course such as `OMSCS AI`.
5. Open the course.
6. Upload a `.txt`, `.md`, or text-based `.pdf` file.
7. Open the uploaded document.
8. Generate a concise summary.
9. Generate flashcards.
10. Generate a quiz.
11. Take the quiz and submit answers.
12. Return to the dashboard to inspect weak topics and recent activity.

---

## Testing

Run the backend suite:

```bash
cd backend
python -m pytest -q
```

Current status:

```text
11 passed
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

Check Expo config loading:

```bash
cd mobile
npx expo config --type public
```

---

## Known Limitations

- No authentication or multi-user support.
- SQLite and local file storage are intended for local MVP persistence.
- PDF extraction supports text-based PDFs only.
- Scanned/image-only PDFs need OCR, which is not implemented.
- AI calls are synchronous.
- The OpenAI provider has fallback behavior but still needs more robust structured-output validation.
- Quiz responses include correct answers in the MVP API for mobile simplicity.
- Mobile automated tests are not added yet.
- No cloud deployment or app store packaging.
- Generated study material may contain mistakes. Students should verify against original course materials.

---

## Next Steps

Planned follow-up improvements:

- run a full simulator or physical-device Expo smoke test
- capture screenshots and polish mobile layout
- add sample notes for repeatable demos
- add mobile component or interaction tests
- improve OpenAI JSON schema handling
- add a text-based PDF fixture test
- improve document-generation error states
- hide quiz correct answers until submission in a production-oriented API mode
- prepare deployment notes after the local MVP flow is stable

---

## Resume Bullet Draft

StudyPilot — AI-Powered Mobile Study Assistant | React Native, Expo, FastAPI, Python, SQLite, LLM APIs

- Built a mobile study assistant that imports course materials and generates structured summaries, flashcards, quizzes, and weak-topic reviews through a FastAPI-based AI pipeline.
- Implemented document upload, PDF/text extraction, chunking, prompt-based generation, quiz attempts, and mobile dashboard views for personalized study workflows.
- Added deterministic fake-AI mode and pytest coverage to support local demos without external API calls.
