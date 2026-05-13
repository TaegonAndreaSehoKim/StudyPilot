# StudyPilot AI Quality Eval Notes

This folder documents lightweight quality expectations for generated study material.

The current automated evals use deterministic `FakeAIProvider` outputs because local tests must not call external LLM APIs.

## Quality Checks

- Section headings should influence generated topics.
- Summaries should include source-grounded key terms.
- Quizzes should avoid generic topics for sufficiently rich notes.
- Quiz explanations should include a source quote or source-grounded rationale.
- Quiz explanations should explain why distractors are wrong.
- Very short notes should be marked as insufficient instead of expanded with invented detail.

## Sample Source Themes

- Search algorithms explore state spaces.
- Heuristics guide search toward promising solutions.
- Adversarial search models competitive games.
- Planning uses actions, preconditions, effects, and goals.

These expectations are intentionally small and stable. They are not a replacement for human review, but they catch regressions that would make the demo feel less like a real study product.
