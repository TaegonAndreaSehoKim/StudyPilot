# Validation And Smoke Checks

Use this page when validating changes before committing or demoing StudyPilot.

## Backend Tests

```bash
cd backend
python -m pytest -q
```

Expected result: all backend tests pass without external OpenAI calls.

Backend tests use:

- temporary SQLite databases
- temporary upload storage
- fake AI
- fake OCR unless a test explicitly targets extraction behavior
- no external OpenAI network calls

## Backend Smoke Flow

With the backend running:

```bash
cd backend
python scripts/smoke_demo.py --base-url http://127.0.0.1:8000 --cleanup
```

This checks the basic product loop:

```text
course -> upload -> review notes -> flashcards -> quiz -> attempt -> weak areas -> dashboard
```

The script is intentionally document-level. Section-level generation, additional explanations, and device-local reminder behavior are covered by backend tests plus the manual product smoke below.

## Mobile Checks

TypeScript:

```bash
cd mobile
npm run typecheck
```

Mobile smoke checks:

```bash
cd mobile
npm run smoke
```

The smoke script checks:

- Expo project ID
- EAS update URL
- runtime version policy
- preview channel setup
- iOS tablet support
- no mobile OpenAI key dependency
- backend access token header wiring
- expected Expo Router routes

All mobile checks:

```bash
cd mobile
npm run check
```

This runs:

- `npm run typecheck`
- `npm run smoke`
- `expo install --check`
- `npm run export:web`

## Expo Config

```bash
cd mobile
npx expo config --type public
```

## Expo Web Export Smoke

```bash
cd mobile
npm run export:web
```

## Docker Compose Config

```bash
docker compose config
```

## EC2 Backend Health

PowerShell:

```powershell
Invoke-RestMethod -Uri "http://3.23.120.213:8000/health"
```

Expected response:

```json
{
  "status": "ok",
  "app": "StudyPilot"
}
```

## Manual Product Smoke

1. Start or verify the backend.
2. Open StudyPilot in Expo Go.
3. Open Settings and test the backend connection.
4. Create a course.
5. Create a section for a unit, chapter, midterm, or final.
6. Add source material to that section.
7. Open the source and read the full extracted text.
8. Create Additional Explanation or Quick Review notes from Generate Study Tools.
9. Create flashcards.
10. Create a practice quiz.
11. Submit quiz answers with at least one miss.
12. Confirm weak areas update.
13. Return to the section and create section-level notes or a section quiz from the combined source set.
14. Add a deadline with a popup reminder.
15. Confirm the dashboard shows Continue Studying, weak areas, and deadlines.

Detailed checklist: `docs/demo/mobile_walkthrough.md`.

## GitHub Actions

GitHub Actions runs backend tests and mobile checks on pushes and pull requests to `main`.
