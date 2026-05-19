# StudyPilot Demo Script

This script is for a short, repeatable product demo. It assumes the backend is running on EC2 and the mobile app is opened through Expo Go preview updates.

## Demo Goal

Show that StudyPilot can turn uploaded course material into a scoped study loop:

```text
course -> section scope -> source material -> explanation/notes -> quiz -> weak topics -> schedule
```

In the mobile UI, the same flow is presented in learner-facing language:

```text
course -> section -> source material -> study tools -> practice quiz -> weak areas -> deadlines
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
- Continue Studying cards
- upcoming schedule across all courses
- recent review notes, practice quizzes, and source materials
- weak areas

Say:

> StudyPilot starts from the student's next study action, not just a file list. The dashboard pulls together deadlines, weak areas, recent generated materials, and practice items.

### 2. Course

Create or open `OMSCS AI`.

Point out:

- Study tab
- Library tab
- Practice tab
- Deadlines tab
- New Section action
- editable course name and description

Say:

> Each course acts as a study workspace. Sections let a student group multiple sources by unit, chapter, midterm, or final, while the dashboard still aggregates deadlines, weak areas, and recent study work globally.

### 3. Section Scope

Create or open a section such as `Midterm 1`.

Point out:

- section name and description
- source count, review-note count, and quiz count
- Generate Section Tools panel

Say:

> The section is the study scope. A student can add several lectures or readings into one exam range, then generate notes, additional explanations, or a quiz from the combined source set.

### 4. Source Material

Add `docs/demo/omscs_ai_sample_notes.md` as source material.

Open the source material screen.

Point out:

- study readiness
- source preview
- full extracted text link
- original file link
- Generate Study Tools panel

Say:

> The backend extracts readable text and stores it. StudyPilot uses the full readable source, even though this screen only shows a preview.

### 5. Additional Explanation And Review Notes

Create Additional Explanation first, then optionally create Quick Review notes.

Open the saved review notes.

Point out:

- overview
- additional explanation or key points
- key terms
- source quotes
- save/share action

Say:

> Additional Explanation is intentionally less compressed than a summary. It is for cases where the lecture is hard to understand and the student needs slower teaching, intuition, and source-grounded context.

### 6. Flashcards

Return to the source material.

Create flashcards.

Open course flashcards from Materials.

Say:

> Flashcards provide quick recall from the same uploaded material. They are saved across the course, not just temporarily displayed.

### 7. Quiz

Create a practice quiz from the source material.

Answer at least one question incorrectly.

Submit.

Point out:

- answer progress
- score
- weak areas
- highlighted choices
- explanations and source quotes
- return links to source material and course

Say:

> Missed topics are recorded automatically. This closes the loop from generated practice back into personalized review.

### 8. Weak Topic Review

Return to the course Practice tab.

Create weak-area practice if weak areas are available.

Say:

> StudyPilot can use the weak-topic history to create a focused review quiz.

### 9. Schedule

Open the Deadlines tab.

Add an assignment or exam date with a popup reminder.

Return to the dashboard.

Say:

> Deadlines and exams are course-specific, but the main dashboard aggregates them so students can see what is coming next across all courses. Reminder settings are stored by the backend and scheduled as local device notifications by the mobile app.

## Success Criteria

- Settings health check succeeds.
- Course creation works.
- Section creation works.
- Source upload and text extraction work.
- Full extracted text is readable.
- Additional explanations or review notes are generated and saved.
- Flashcards are generated and reachable from course materials.
- Quiz can be submitted.
- Missed answers create weak areas.
- Schedule item appears on the dashboard, with reminder preference saved.

## Known Caveats To Mention

- This MVP has no user authentication yet.
- The EC2 backend currently uses HTTP for MVP testing.
- SQLite and uploaded files are stored on the EC2 instance.
- Generated study material can contain mistakes and should be checked against original source materials.
- Scanned PDFs require OCR; text-based PDFs usually extract directly.
