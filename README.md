# StudyPilot — AI-Powered Mobile Study Assistant

## Overview

StudyPilot is a local-first MVP that turns course materials into summaries, flashcards, quizzes, and weak-topic reviews. It uses a React Native Expo mobile app, a FastAPI backend, SQLite persistence, and an AI provider layer that can run with either OpenAI or a deterministic fake provider.

The MVP is intentionally scoped for local development and demos. It does not require an API key.

## Features

- Create and manage courses.
- Upload `.txt`, `.md`, and text-based `.pdf` documents.
- Extract source text on the backend.
- Generate concise and exam-focused summaries.
- Generate flashcards.
- Generate multiple-choice quizzes.
- Submit quiz attempts and review explanations.
- Track missed quiz topics.
- View dashboard counts, recent activity, and weak topics.

## Architecture

```text
Mobile app (Expo)
  -> fetch HTTP requests
FastAPI backend
  -> SQLite database
  -> local upload storage
  -> AIProvider abstraction
       -> FakeAIProvider when OPENAI_API_KEY is missing
       -> OpenAIProvider when OPENAI_API_KEY is set
```

The mobile app never reads or stores an LLM API key. Only the backend can read `OPENAI_API_KEY`.

## Tech Stack

- Mobile: React Native, Expo, Expo Router, TypeScript
- Backend: Python, FastAPI, SQLAlchemy, Pydantic
- Database: SQLite
- AI: OpenAI-compatible provider through backend only
- Tests: pytest, FastAPI TestClient

## Project Structure

```text
StudyPilot/
├── backend/
│   ├── app/
│   └── tests/
├── mobile/
│   ├── app/
│   └── src/
├── DEVELOPMENT_PLAN.md
└── README.md
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Mobile Setup

```bash
cd mobile
npm install
npx expo start
```

Use the Settings screen to change the API base URL if needed.

- iOS simulator: `http://127.0.0.1:8000`
- Android emulator: `http://10.0.2.2:8000`
- Physical device: `http://<your-computer-lan-ip>:8000`

## Environment Variables

Backend variables are documented in `backend/.env.example`.

Important defaults:

- `DATABASE_URL=sqlite:///./studypilot.db`
- `STORAGE_DIR=backend/app/storage`
- `OPENAI_MODEL=gpt-5.5`
- `USE_FAKE_AI=false`
- `MAX_UPLOAD_MB=10`

If `OPENAI_API_KEY` is missing, StudyPilot automatically uses `FakeAIProvider`.

## Demo Flow

1. Start the backend.
2. Start the mobile app.
3. Open Settings and test the backend connection.
4. Create a course such as `OMSCS AI`.
5. Open the course and upload a `.txt`, `.md`, or text-based `.pdf` file.
6. Open the document.
7. Generate a concise summary.
8. Generate flashcards.
9. Generate a quiz.
10. Take the quiz and submit answers.
11. Return to the dashboard to see weak topics.

## Testing

```bash
cd backend
python -m pytest -q
```

Tests use temporary SQLite databases, temporary storage directories, and fake AI. They do not call OpenAI or any external model provider.

Mobile type check:

```bash
cd mobile
npm run typecheck
```

## Known Limitations

- No authentication or multi-user support.
- SQLite and local file storage are for local MVP persistence.
- PDF extraction supports text-based PDFs only; scanned PDFs need OCR, which is out of scope.
- Generated study content may contain mistakes. Students should verify against original course materials.
- Quiz responses include correct answers in the MVP API to simplify the mobile flow. A production app should hide them until submission.
- No cloud deployment, push notifications, billing, or app store packaging.

## Future Improvements

- Authentication and per-user data.
- Cloud object storage.
- Production database migrations.
- Better PDF processing and OCR.
- Spaced repetition scheduling.
- Hidden quiz answers until submission.
- Embeddings or retrieval for larger document collections.
- CI for backend tests and mobile type checking.

## Resume Bullet Draft

StudyPilot — AI-Powered Mobile Study Assistant | React Native, Expo, FastAPI, Python, SQLite, LLM APIs

- Built a mobile study assistant that imports course materials and generates structured summaries, flashcards, quizzes, and weak-topic reviews through a FastAPI-based AI pipeline.
- Implemented document upload, PDF/text extraction, chunking, prompt-based generation, quiz attempts, and mobile dashboard views for personalized study workflows.
- Added deterministic fake-AI mode and pytest coverage to support local demos without external API calls.
