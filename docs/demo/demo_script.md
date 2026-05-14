# StudyPilot Demo Script

This script is for a short, repeatable product demo. It assumes the backend is running on EC2 and the mobile app is opened through Expo Go preview updates.

## Demo Goal

Show that StudyPilot can turn uploaded course material into a study loop:

```text
course -> document -> summary -> flashcards -> quiz -> weak topics -> schedule
```

## Demo Setup

Use:

- Backend: `http://3.23.120.213:8000`
- Mobile: Expo Go, preview update channel
- Sample document: `docs/demo/omscs_ai_sample_notes.md`
- Optional text fallback: `docs/demo/sample-study-notes.txt`

Before the demo:

```powershell
cd mobile
npm run check
npm run update:preview -- --message "demo update"
```

On the iPhone:

1. Reopen StudyPilot in Expo Go.
2. Open Settings.
3. Select the AWS EC2 backend preset.
4. Enter the backend access token.
5. Tap Save & Test Connection.

## Talk Track

### 1. Dashboard

Open StudyPilot.

Point out:

- global counts
- Study Focus cards
- upcoming schedule across all courses
- recent summaries/quizzes/documents
- weak topics

Say:

> StudyPilot starts from the student's next study action, not just a file list. The dashboard pulls together deadlines, weak topics, recent generated materials, and practice items.

### 2. Course

Create or open `OMSCS AI`.

Point out:

- Overview tab
- Materials tab
- Practice tab
- Schedule tab

Say:

> Each course acts as a study workspace. Documents, generated materials, quizzes, attempts, weak topics, and schedule items stay grouped by course, while the dashboard aggregates the important items globally.

### 3. Document Upload

Upload `docs/demo/omscs_ai_sample_notes.md`.

Open the document detail screen.

Point out:

- extraction status
- extracted text preview
- full extracted text link
- original file link

Say:

> The backend extracts text and stores it. Generation uses the full extracted text, even though the document screen only shows a preview.

### 4. Summary

Generate a concise summary.

Open the saved summary.

Point out:

- overview
- key points
- key terms
- source quotes
- save/share action

Say:

> The summary is saved as a durable study material and is available again from the course and dashboard. Source quotes help keep the generated output grounded in the uploaded notes.

### 5. Flashcards

Return to the document.

Generate flashcards.

Open course flashcards from Materials.

Say:

> Flashcards provide quick recall from the same uploaded material. They are saved across the course, not just temporarily displayed.

### 6. Quiz

Generate a quiz from the document.

Answer at least one question incorrectly.

Submit.

Point out:

- answer progress
- score
- missed topics
- highlighted choices
- explanations and source quotes
- return links to source document and course

Say:

> Missed topics are recorded automatically. This closes the loop from generated practice back into personalized review.

### 7. Weak Topic Review

Return to the course Practice tab.

Generate a weak-topic quiz if weak topics are available.

Say:

> StudyPilot can use the weak-topic history to create a focused review quiz.

### 8. Schedule

Open the Schedule tab.

Add an assignment or exam date.

Return to the dashboard.

Say:

> Deadlines and exams are course-specific, but the main dashboard aggregates them so students can see what is coming next across all courses.

## Success Criteria

- Settings health check succeeds.
- Course creation works.
- Document upload and extraction work.
- Full extracted text is readable.
- Summary is generated and saved.
- Flashcards are generated and reachable from course materials.
- Quiz can be submitted.
- Missed answers create weak topics.
- Schedule item appears on the dashboard.

## Known Caveats To Mention

- This MVP has no user authentication yet.
- The EC2 backend currently uses HTTP for MVP testing.
- SQLite and uploaded files are stored on the EC2 instance.
- Generated study material can contain mistakes and should be checked against original course materials.
- Scanned PDFs require OCR; text-based PDFs usually extract directly.
