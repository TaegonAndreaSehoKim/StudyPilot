# StudyPilot Mobile Demo Walkthrough

Use this checklist for a repeatable Expo Go demo against the local FastAPI backend or the EC2 backend.

## Prerequisites

- Backend is running from `backend/`, or the EC2 backend is reachable.
- Mobile app is running from `mobile/`, or the latest preview update has been published with `npm run update:preview`.
- Expo Go can reach the backend URL.
- For a physical iPhone, the backend should be started with:

```bash
uvicorn app.main:app --host 0.0.0.0 --reload
```

Use the computer LAN IP in the mobile Settings screen, for example:

```text
http://192.168.1.25:8000
```

For the current EC2 MVP backend, use:

```text
http://3.23.120.213:8000
```

## Demo Steps

1. Open StudyPilot in Expo Go.
2. Open Settings.
3. Enter the backend API base URL.
4. Enter the backend access token if the backend requires it.
5. Tap the health check button and confirm the backend responds.
6. Confirm the App Update card is visible when testing through EAS preview updates.
7. Return to the dashboard.
8. Create a course named `OMSCS AI`.
9. Open the course and upload `docs/demo/omscs_ai_sample_notes.md`.
10. Open the uploaded source material.
11. Open Full Extracted Text and confirm the full source is readable.
12. Return to the source screen.
13. Create Quick Review notes.
14. Open the saved review notes and confirm full content is readable.
15. Return to the source screen.
16. Create flashcards.
17. Return to the course Library tab and open course flashcards.
18. Create a practice quiz from the source.
19. Confirm the quiz answer progress card updates as choices are selected.
20. Submit the quiz with at least one wrong answer.
21. Confirm result actions can return to the source and course.
22. Return to the dashboard.
23. Confirm Continue Studying, review notes, practice quizzes, and weak areas are visible.
24. Open the course Deadlines tab.
25. Add an assignment or exam date.
26. Return to the dashboard and confirm the upcoming schedule item appears globally.

## Expected Results

- Missing `OPENAI_API_KEY` should not block the demo.
- Generated content should be deterministic through `FakeAIProvider`.
- Full source text and saved review-note screens should show complete content, not only previews.
- Recent generated materials should be accessible from the dashboard.
- Continue Studying should show the next useful action after materials, quizzes, weak areas, or deadline items exist.
- Quiz misses should update weak areas.
- Schedule items should appear both in the course and on the dashboard.

## Troubleshooting

- If the iPhone cannot connect, confirm both devices are on the same network.
- If the backend URL uses `127.0.0.1`, replace it with the computer LAN IP for physical devices.
- If a PDF extracts little or no text, it may be scanned or image-only. Use the source screen's text-recognition action when the backend has OCR enabled.
- If Expo Go shows stale UI, pull to refresh or navigate away and back; primary screens reload on focus.
- If an EAS preview update does not appear, fully quit Expo Go and reopen StudyPilot from the project list.
