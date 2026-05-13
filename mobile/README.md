# StudyPilot Mobile

React Native Expo app for StudyPilot.

## Setup

```bash
cd mobile
npm install
```

## Run

```bash
npx expo start
```

Then choose iOS simulator, Android emulator, Expo Go, or another Expo target.

## API Base URL

Default:

```text
http://127.0.0.1:8000
```

Use the Settings screen to update and test the backend URL.

- iOS simulator usually works with `http://127.0.0.1:8000`.
- Android emulator usually needs `http://10.0.2.2:8000`.
- Physical devices need your computer's LAN IP, such as `http://192.168.1.25:8000`.

If using a physical device, start the backend with a host that accepts LAN traffic:

```bash
uvicorn app.main:app --host 0.0.0.0 --reload
```

## Type Check

```bash
npm run typecheck
```

Check Expo SDK dependency compatibility:

```bash
npx expo install --check
```

## Main Screens

- Dashboard: counts, recent courses, recent documents, weak topics
- Courses: course list and course creation
- Course detail: document list and upload flow
- Document detail: extracted preview, summary, flashcards, quizzes
- Quiz: answer questions, submit attempt, view explanations
- Settings: API base URL and health check

## Troubleshooting

- If health check fails, confirm the backend is running.
- If Android cannot connect to `127.0.0.1`, use `10.0.2.2`.
- If a physical device cannot connect, use the computer's LAN IP and allow local firewall access.
- Scanned PDFs are not supported by the MVP backend.
