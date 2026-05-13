# StudyPilot Mobile Demo Walkthrough

Use this checklist for a repeatable Expo Go demo against the local FastAPI backend.

## Prerequisites

- Backend is running from `backend/`.
- Mobile app is running from `mobile/`.
- Expo Go can reach the backend URL.
- For a physical iPhone, the backend should be started with:

```bash
uvicorn app.main:app --host 0.0.0.0 --reload
```

Use the computer LAN IP in the mobile Settings screen, for example:

```text
http://192.168.1.25:8000
```

## Demo Steps

1. Open StudyPilot in Expo Go.
2. Open Settings.
3. Enter the backend API base URL.
4. Tap the health check button and confirm the backend responds.
5. Return to the dashboard.
6. Create a course named `OMSCS AI`.
7. Open the course and upload `docs/demo/omscs_ai_sample_notes.md`.
8. Open the uploaded document.
9. Open Full Extracted Text and confirm the full source is readable.
10. Return to the document screen.
11. Generate a concise summary.
12. Open the saved summary and confirm full summary content is readable.
13. Return to the document screen.
14. Generate flashcards.
15. Return to the course Materials tab and open course flashcards.
16. Generate a quiz from the document.
17. Submit the quiz with at least one wrong answer.
18. Return to the dashboard.
19. Confirm recent summaries, recent quizzes, and weak topics are visible.
20. Open the course Schedule tab.
21. Add an assignment or exam date.
22. Return to the dashboard and confirm the upcoming schedule item appears globally.

## Expected Results

- Missing `OPENAI_API_KEY` should not block the demo.
- Generated content should be deterministic through `FakeAIProvider`.
- Full extracted text and saved summary screens should show complete content, not only previews.
- Recent generated materials should be accessible from the dashboard.
- Quiz misses should update weak topics.
- Schedule items should appear both in the course and on the dashboard.

## Troubleshooting

- If the iPhone cannot connect, confirm both devices are on the same network.
- If the backend URL uses `127.0.0.1`, replace it with the computer LAN IP for physical devices.
- If a PDF extracts little or no text, it may be scanned or image-only. Use the document screen's Run OCR action when the backend has OCR enabled.
- If Expo Go shows stale UI, pull to refresh or navigate away and back; primary screens reload on focus.
