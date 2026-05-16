# API Endpoints

The FastAPI backend exposes local MVP endpoints for courses, source materials, review notes, flashcards, quizzes, weak areas, deadlines, OCR, and dashboards.

Open interactive docs when the backend is running:

```text
http://127.0.0.1:8000/docs
```

## Access Rules

- `GET /health` and read endpoints are public in the MVP.
- If `BACKEND_ACCESS_TOKEN` is set, every `POST`, `PATCH`, and `DELETE` request must include `X-StudyPilot-Key`.
- In `ENVIRONMENT=production`, mutating requests fail unless `BACKEND_ACCESS_TOKEN` is configured.
- Write, OCR, and AI-generation endpoints are protected by in-memory rate limits.

The mobile app stores only the backend URL and optional backend access token. It must never store `OPENAI_API_KEY`.

## Endpoint Summary

### Health

- `GET /health`

### Courses

- `POST /courses`
- `GET /courses`
- `GET /courses/{course_id}`
- `PATCH /courses/{course_id}`
- `DELETE /courses/{course_id}`
- `GET /courses/{course_id}/dashboard`

### Source Materials

- `POST /documents/upload`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/text`
- `GET /documents/{document_id}/download`
- `GET /courses/{course_id}/documents`
- `DELETE /documents/{document_id}`

### OCR

- `POST /documents/{document_id}/ocr`
- `GET /ocr-jobs/{job_id}`

### Review Notes

- `POST /documents/{document_id}/summaries`
- `GET /documents/{document_id}/summaries`
- `GET /summaries/{summary_id}`
- `DELETE /summaries/{summary_id}`
- `GET /courses/{course_id}/summaries`

### Flashcards

- `POST /documents/{document_id}/flashcards`
- `GET /documents/{document_id}/flashcards`
- `GET /courses/{course_id}/flashcards`

### Quizzes And Attempts

- `POST /documents/{document_id}/quizzes`
- `POST /courses/{course_id}/review-quiz`
- `GET /documents/{document_id}/quizzes`
- `GET /courses/{course_id}/quizzes`
- `GET /quizzes/{quiz_id}`
- `DELETE /quizzes/{quiz_id}`
- `GET /quizzes/{quiz_id}/attempts`
- `GET /courses/{course_id}/attempts`
- `POST /quizzes/{quiz_id}/attempts`

### Deadlines

- `POST /courses/{course_id}/schedule`
- `GET /courses/{course_id}/schedule`
- `GET /schedule`
- `GET /schedule/{item_id}`
- `PATCH /schedule/{item_id}`
- `DELETE /schedule/{item_id}`

### Weak Areas And Dashboard

- `GET /courses/{course_id}/weak-topics`
- `GET /dashboard`

## Common Requests

### Create A Course

```json
POST /courses
{
  "title": "OMSCS AI",
  "description": "Artificial Intelligence notes"
}
```

### Upload Source Material

Use multipart form data:

```text
POST /documents/upload
course_id=<course id>
file=<notes.txt | notes.md | notes.pdf>
```

Supported file types:

- `.txt`
- `.md`
- text-based `.pdf`
- scanned PDFs when OCR is configured and run after upload

### Create Review Notes

```json
POST /documents/1/summaries
{
  "summary_type": "concise"
}
```

Supported summary types:

- `concise`: core concepts and broad flow
- `detailed`: conceptual explanation and principles
- `exam`: likely test points, similar-concept comparisons, memorization anchors

### Create Flashcards

```json
POST /documents/1/flashcards
{
  "count": 10
}
```

### Create A Practice Quiz

```json
POST /documents/1/quizzes
{
  "question_count": 5,
  "difficulty": "mixed"
}
```

### Create Weak-Area Practice

```json
POST /courses/1/review-quiz
{
  "question_count": 5,
  "difficulty": "medium"
}
```

If `topics` is omitted, StudyPilot uses the course's highest-miss weak areas.

### Submit A Quiz Attempt

```json
POST /quizzes/1/attempts
{
  "answers": [
    {
      "question_id": 1,
      "selected_answer": "A"
    }
  ]
}
```

The backend scores the attempt, stores the result, and updates weak areas for missed questions.
