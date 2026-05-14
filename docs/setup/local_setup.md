# Local Setup

This guide gets StudyPilot running locally after cloning the repository.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Expo Go on iOS or Android for device testing

The app works without `OPENAI_API_KEY`. If the key is missing, the backend uses deterministic fake AI so local demos and tests still work.

## Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```powershell
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
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

For physical-device testing on the same network:

```bash
uvicorn app.main:app --host 0.0.0.0 --reload
```

Then use your computer LAN IP in the mobile Settings screen, for example:

```text
http://192.168.1.25:8000
```

## Mobile

```bash
cd mobile
npm install
npx expo start
```

Then open the project in Expo Go, an iOS simulator, an Android emulator, or web.

## Mobile Backend URLs

The mobile app stores the API base URL in Settings.

- iOS simulator: `http://127.0.0.1:8000`
- Android emulator: `http://10.0.2.2:8000`
- Physical device: `http://<your-computer-lan-ip>:8000`
- Current EC2 MVP backend: `http://3.23.120.213:8000`

If the backend has `BACKEND_ACCESS_TOKEN` configured, enter that same backend access token in Settings. This is not an OpenAI API key.

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

- `USE_FAKE_AI=true` uses `FakeAIProvider`
- missing `OPENAI_API_KEY` uses `FakeAIProvider`
- present `OPENAI_API_KEY` and `USE_FAKE_AI=false` uses `OpenAIProvider`

OCR provider behavior:

- `OCR_PROVIDER=fake` uses fake OCR for local demos/tests
- `OCR_PROVIDER=textract` uses Amazon Textract on the backend host
- `OCR_PROVIDER=disabled` blocks OCR requests

## EAS Preview Updates

For device checks without a local Metro dev server:

```bash
cd mobile
npm run update:preview -- --message "preview update"
```

Then reopen StudyPilot in Expo Go from the same Expo account.

More detail: `docs/deployment/eas_preview_updates.md`.
