# StudyPilot - AI-Powered Mobile Study Assistant

StudyPilot is a full-stack mobile study assistant that turns course materials into review notes, flashcards, practice quizzes, weak-area review, and deadline tracking.

It is built as an early-stage product MVP with a React Native Expo app, a FastAPI backend, SQLite persistence, local file storage, OCR handoff for scanned PDFs, and a backend-only AI provider layer.

The project works without an OpenAI API key. When `OPENAI_API_KEY` is missing, the backend uses a deterministic fake AI provider so the full demo flow and test suite can run locally without paid API calls.

## What It Does

```text
course -> source material -> review notes -> flashcards -> practice quiz -> weak areas -> deadlines
```

Core capabilities:

- Create courses and organize source materials.
- Upload `.txt`, `.md`, text-based `.pdf`, and OCR-required scanned PDFs.
- Create source-grounded review notes, flashcards, and quizzes.
- Save and share review notes as PDFs from the mobile app.
- Take quizzes and track missed topics as weak areas.
- Create weak-area practice quizzes.
- Track assignments, exams, readings, projects, and deadlines per course.
- See Continue Studying cards, recent work, deadlines, and weak areas on the dashboard.
- Run locally with fake AI, or use OpenAI from the backend only.

## Tech Stack

- Mobile: React Native, Expo Router, TypeScript
- Backend: Python, FastAPI, SQLAlchemy
- Database: SQLite
- AI: backend-only provider abstraction with fake AI fallback and OpenAI support
- OCR: fake OCR for local tests, optional Amazon Textract for scanned PDFs
- Testing: pytest for backend, TypeScript and Expo smoke checks for mobile
- Deployment MVP: Docker Compose on EC2, Expo Go plus EAS preview updates

## Architecture

```text
Expo mobile app
  -> HTTP fetch calls
FastAPI backend
  -> SQLite
  -> local upload storage
  -> OCR provider
  -> AI provider
       -> FakeAIProvider without API key
       -> OpenAIProvider with OPENAI_API_KEY
```

The mobile app never reads or stores LLM API keys. It only talks to the FastAPI backend.

More detail:

- [Architecture overview](docs/architecture/overview.md)
- [Database schema](docs/architecture/schema.md)
- [API endpoints](docs/api/endpoints.md)

## Quick Start

Start the backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Start the mobile app:

```bash
cd mobile
npm install
npx expo start
```

Open Settings in the app and set the API base URL:

- iOS simulator: `http://127.0.0.1:8000`
- Android emulator: `http://10.0.2.2:8000`
- Physical device: `http://<your-computer-lan-ip>:8000`
- Current EC2 MVP backend: `http://3.23.120.213:8000`

Full setup guide: [Local setup](docs/setup/local_setup.md).

## Demo Flow

1. Open StudyPilot.
2. Create a course, for example `OMSCS AI`.
3. Add source material such as `docs/demo/omscs_ai_sample_notes.md`.
4. Read the full source text.
5. Create Quick Review notes.
6. Create flashcards.
7. Create a practice quiz.
8. Submit answers with at least one miss.
9. Review weak areas.
10. Add an assignment or exam deadline.
11. Return to the dashboard and continue studying from the next recommended action.

Demo docs:

- [Mobile walkthrough](docs/demo/mobile_walkthrough.md)
- [Demo script](docs/demo/demo_script.md)
- [Sample demo materials](docs/demo/README.md)

## Validation

Backend:

```bash
cd backend
python -m pytest -q
```

Mobile:

```bash
cd mobile
npm run check
```

More checks: [Validation and smoke checks](docs/operations/validation.md).

## Deployment Notes

The current deployment MVP runs the backend on one EC2 instance with Docker Compose. The mobile app is tested through Expo Go and EAS preview updates.

- [AWS EC2 Docker deployment](docs/deployment/aws_ec2_docker.md)
- [EAS preview updates](docs/deployment/eas_preview_updates.md)

## Current Status

Stable MVP foundation:

- backend startup, course CRUD, upload, extraction, OCR jobs, generation, quiz attempts, weak areas, deadlines, dashboards
- deterministic fake AI and fake OCR for local demos/tests
- OpenAI provider path from backend only
- EC2 backend deployment path tested
- Expo Go preview workflow tested
- learner-focused mobile UX for dashboard, course, source, review-note, and practice screens

Still intentionally out of scope:

- authentication and multi-user accounts
- subscriptions or payments
- S3 or managed database persistence
- app store packaging
- advanced spaced repetition
- vector search or RAG

Generated study material may contain mistakes. Students should verify against original course materials.

## Project Map

```text
backend/                 FastAPI app, SQLite models, routers, services, tests
mobile/                  Expo Router app, API client, screens, components
docs/architecture/       architecture and schema notes
docs/api/                API reference
docs/setup/              local setup
docs/deployment/         EC2 and EAS preview operations
docs/demo/               walkthroughs and sample source materials
docs/operations/         validation and smoke checks
AGENTS.md                guidance for future coding agents
DEVELOPMENT_PLAN.md      original build plan and milestone notes
```

## Resume Bullet Draft

StudyPilot - AI-Powered Mobile Study Assistant | React Native, Expo, FastAPI, Python, SQLite, LLM APIs

- Built a mobile study assistant that imports course materials and generates structured review notes, flashcards, quizzes, and weak-area reviews through a FastAPI-based AI pipeline.
- Implemented document upload, PDF/text extraction, OCR handoff, chunking, prompt-based generation, quiz attempts, deadline tracking, and mobile dashboard views for personalized study workflows.
- Added deterministic fake-AI mode, backend-only LLM access, EC2 deployment notes, EAS preview updates, and pytest/mobile smoke checks to support reliable local and device demos.
