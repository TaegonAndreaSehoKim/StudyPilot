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

This project currently targets Expo SDK 54 so it can run in the App Store version of Expo Go. If the QR code still opens an incompatibility screen, stop Metro and restart with:

```bash
npx expo start --clear
```

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

Run all mobile checks:

```bash
npm run check
```

Check Expo SDK dependency compatibility:

```bash
npx expo install --check
```

Run the Expo web export smoke:

```bash
npm run export:web
```

## Main Screens

- Dashboard: counts, recent courses, recent documents, weak topics
- Dashboard schedule: upcoming deadlines and exams across all courses
- Courses: course list and course creation
- Course detail: tabbed overview, materials, practice, schedule, document upload, and course actions
- Schedule: course deadlines, exams, readings, projects, countdowns, completion, and delete actions
- Document detail: extracted preview, full extracted text link, original file link, generation feedback, generated summary, flashcards, quizzes
- Full text: complete extracted document text with Save / Share support
- Summary detail: full saved summary with key points, key terms, source quotes, and Save / Share support
- Flashcards: course-level saved card review with Save / Share support
- Quizzes: course-level saved quiz list with links back into quiz taking
- Quiz: answer questions, submit attempt, view explanations
- Attempts: course-level quiz score history and missed-topic review
- Settings: API base URL and health check

## Troubleshooting

- If health check fails, confirm the backend is running.
- If Android cannot connect to `127.0.0.1`, use `10.0.2.2`.
- If a physical device cannot connect, use the computer's LAN IP and allow local firewall access.
- Scanned PDFs are not supported by the MVP backend.
