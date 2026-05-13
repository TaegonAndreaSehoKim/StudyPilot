# StudyPilot Schema Notes

This document summarizes the current backend persistence and API data model.

## Course

Represents a course or class workspace.

Fields:

- `id`
- `title`
- `description`
- `created_at`
- `updated_at`

Relationships:

- has many documents
- has many weak topics

## Document

Represents one uploaded study file.

Fields:

- `id`
- `course_id`
- `filename`
- `file_type`
- `storage_path`
- `extracted_text`
- `char_count`
- `status`
- `page_count`
- `extracted_page_count`
- `extraction_method`
- `extraction_notes`
- `ocr_status`
- `created_at`
- `updated_at`

Status values:

- `uploaded`
- `extracted`
- `needs_ocr`

Notes:

- `.txt` and `.md` files are decoded as UTF-8 with replacement.
- `.pdf` files are parsed with `pypdf`.
- text-poor PDFs are marked `needs_ocr`.
- partially extracted PDFs stay `extracted` but can set `ocr_status=recommended`.
- `POST /documents/{document_id}/ocr` updates the document text through the configured OCR provider.

## Summary

Represents generated study notes for one document.

Fields:

- `id`
- `document_id`
- `summary_type`
- `title`
- `overview`
- `key_points_json`
- `key_terms_json`
- `source_quotes_json`
- `created_at`

Summary types:

- `concise`: core concepts and broad content flow
- `detailed`: general conceptual explanation, principles, and relationships over examples
- `exam`: likely test points, similar-concept comparisons, and memorization anchors

API responses deserialize JSON fields into:

- `key_points: string[]`
- `key_terms: { term, definition }[]`
- `source_quotes: { quote, reason }[]`

## Flashcard

Represents one generated flashcard.

Fields:

- `id`
- `document_id`
- `front`
- `back`
- `topic`
- `difficulty`
- `source_quote`
- `created_at`

Difficulty values:

- `easy`
- `medium`
- `hard`

## Quiz

Represents a generated quiz for one document.

Fields:

- `id`
- `document_id`
- `title`
- `created_at`

Relationships:

- has many quiz questions
- has many quiz attempts

## QuizQuestion

Represents one multiple-choice question.

Fields:

- `id`
- `quiz_id`
- `question`
- `choices_json`
- `correct_answer`
- `explanation`
- `topic`
- `difficulty`

Notes:

- `choices_json` stores a JSON array of answer strings.
- `correct_answer` is currently included in MVP quiz responses for mobile simplicity.
- A production version should hide correct answers until attempt submission.

## QuizAttempt

Represents one submitted quiz attempt.

Fields:

- `id`
- `quiz_id`
- `score`
- `total_questions`
- `correct_count`
- `missed_topics_json`
- `answers_json`
- `created_at`

Attempt scoring:

- compare selected answer letters against `correct_answer`
- score is `correct_count / total_questions`
- missed question topics are saved and passed to weak-topic updating

## WeakTopic

Represents accumulated missed-question topics for a course.

Fields:

- `id`
- `course_id`
- `topic`
- `miss_count`
- `last_missed_at`

Update behavior:

- each missed quiz question increments the course-specific topic count
- repeated missed topics accumulate
- dashboard endpoints sort by miss count and most recent miss time

## API Response Groups

Course responses:

- `CourseOut`
- `CourseDetailOut`

Document responses:

- `DocumentOut`
- `DocumentDetailOut`

Generated material responses:

- `SummaryOut`
- `FlashcardOut`
- `QuizOut`
- `QuizQuestionOut`

Quiz attempt responses:

- `QuizAttemptResult`
- `QuizAnswerResult`

Dashboard responses:

- `DashboardOut`
- `CourseDashboardOut`

## Schema Evolution Notes

Likely future schema changes:

- add user/account ownership once authentication exists
- add migration tooling before production deployment
- add generation status or error records for long-running AI calls
- split source quotes into a dedicated table if quote-level UX becomes richer
- hide correct quiz answers from initial quiz payloads
- add spaced repetition fields to flashcards
