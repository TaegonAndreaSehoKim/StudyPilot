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

## Preview Updates Without A Local Dev Server

For device checks through Expo Go after the project is already connected to EAS, publish a preview update:

```bash
cd mobile
npm run update:preview -- --message "preview update"
```

Then reopen the StudyPilot project in Expo Go from the same Expo account. Expo Go applies compatible preview updates when the project is reopened, so the local `npx expo start` server does not need to stay running for this kind of check.

Use `npx expo start` when you need live reload while actively coding. Use `npm run update:preview` when you want a stable mobile preview bundle available from Expo's servers.

## API Base URL

Default:

```text
http://127.0.0.1:8000
```

Use the Settings screen to update and test the backend URL.

- iOS simulator usually works with `http://127.0.0.1:8000`.
- Android emulator usually needs `http://10.0.2.2:8000`.
- Physical devices need your computer's LAN IP, such as `http://192.168.1.25:8000`.
- EC2 deployments should use the associated Elastic IP, such as `http://<elastic-ip>:8000`.
- The Settings screen includes presets for local iOS, Android emulator, and the current AWS EC2 backend.

If using a physical device, start the backend with a host that accepts LAN traffic:

```bash
uvicorn app.main:app --host 0.0.0.0 --reload
```

## Backend Access Token

If the backend sets `BACKEND_ACCESS_TOKEN`, enter the same value in the Settings screen. The app sends it as `X-StudyPilot-Key` for course creation, uploads, AI generation, quiz attempts, schedule edits, and other write requests.

Do not put `OPENAI_API_KEY` in the mobile app. The mobile app only stores the backend URL and optional backend access token.

## Type Check

```bash
npm run typecheck
```

Run mobile smoke checks for app config, route presence, EAS preview setup, and backend-token wiring:

```bash
npm run smoke
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

- Visual palette: warm study palette based on `#D9C3B0`, `#8C7161`, `#D9663D`, `#A64029`, and `#261714`
- Responsive layout: phone-first screens use wider max-width containers and two-column card grids on tablet-sized displays
- Dashboard: Continue Studying cards, counts, recent courses, recent sources, review notes, practice quizzes, and weak areas
- Dashboard deadlines: upcoming assignments and exams across all courses
- Courses: course list and course creation
- Course detail: Study, Library, Practice, and Deadlines tabs with source upload, review notes, flashcards, quizzes, weak areas, and course actions
- Weak-area review quiz: generate focused practice from missed quiz topics on the course Practice tab
- Deadlines: course deadlines, exams, readings, projects, countdowns, completion, and delete actions
- Source detail: read full source, open original file, text-recognition guidance, source preview, review-note options, quiz options, generation feedback, and saved materials
- Full text: complete readable source text with Save / Share support
- Summary detail: full saved review notes with key points, key terms, source quotes, and Save / Share support
- Flashcards: course-level saved card review with Save / Share support
- Quizzes: course-level saved quiz list with links back into quiz taking
- Quiz: answer progress, submit attempt, highlighted answers, source quotes, distractor explanations, retake, and return links to the source document/course
- Attempts: course-level quiz score history and missed-topic review
- Settings: backend presets, API base URL, backend access token status, health check, and current EAS update metadata

## Troubleshooting

- If health check fails, confirm the backend is running.
- If Android cannot connect to `127.0.0.1`, use `10.0.2.2`.
- If a physical device cannot connect, use the computer's LAN IP and allow local firewall access.
- Scanned PDFs are marked as requiring OCR. Use the document screen's Run OCR action when the backend has OCR enabled; the app starts an OCR job and polls until it completes or fails.
- On tablets, rotate between portrait and landscape during manual testing because dashboard, course, document, schedule, quiz history, and saved-material screens use responsive grids.
- Expo Go may not support manual in-app `expo-updates` checks. If the Settings screen reports that manual update checks are unavailable, publish a preview update and reopen the project from Expo Go.

More detail:

- EAS preview workflow: `docs/deployment/eas_preview_updates.md`
- Manual demo checklist: `docs/demo/mobile_walkthrough.md`
- Presentation script: `docs/demo/demo_script.md`
