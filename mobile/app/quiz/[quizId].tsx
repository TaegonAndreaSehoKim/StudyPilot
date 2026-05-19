import { router, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Alert, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { CourseSection, DocumentDetail, Quiz, QuizAttemptResult } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { QuizQuestionView } from '@/components/QuizQuestionView';
import { ScreenScrollView } from '@/components/Screen';
import { colors } from '@/constants/colors';
import { formatPercent } from '@/utils/format';
import { parseQuizExplanation } from '@/utils/quizExplanation';

export default function QuizScreen() {
  const { quizId } = useLocalSearchParams<{ quizId: string }>();
  const id = Number(quizId);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [section, setSection] = useState<CourseSection | null>(null);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<QuizAttemptResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const loadedQuiz = await api.quiz(id);
      setQuiz(loadedQuiz);
      setSection(loadedQuiz.section_id ? await api.section(loadedQuiz.section_id) : null);
      setDocument(loadedQuiz.document_id ? await api.document(loadedQuiz.document_id) : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load this practice quiz');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function submit() {
    if (!quiz) {
      return;
    }
    const unansweredCount = quiz.questions.filter((question) => !answers[question.id]).length;
    if (unansweredCount > 0) {
      setError(`Answer ${unansweredCount} more question${unansweredCount === 1 ? '' : 's'} before submitting.`);
      return;
    }
    try {
      setSubmitting(true);
      setError(null);
      const payload = quiz.questions.map((question) => ({
        question_id: question.id,
        selected_answer: answers[question.id] || '',
      }));
      setResult(await api.submitQuiz(quiz.id, payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to submit this practice quiz');
    } finally {
      setSubmitting(false);
    }
  }

  async function createSimilarQuiz() {
    if (!quiz || (!document && !quiz.section_id)) {
      return;
    }
    try {
      setRegenerating(true);
      setError(null);
      const newQuiz = quiz.section_id
        ? await api.createSectionQuiz(quiz.section_id, quiz.questions.length || 5, 'mixed')
        : await api.createQuiz(document!.id, quiz.questions.length || 5, 'mixed');
      router.replace(`/quiz/${newQuiz.id}` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create another practice quiz');
    } finally {
      setRegenerating(false);
    }
  }

  function confirmDeleteQuiz() {
    Alert.alert(
      'Delete practice quiz?',
      'This removes the quiz and its saved attempts. Weak-topic history from past attempts is kept for now.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: deleteQuiz },
      ],
    );
  }

  async function deleteQuiz() {
    if (!quiz) {
      return;
    }
    try {
      setDeleting(true);
      setError(null);
      await api.deleteQuiz(quiz.id);
      if (quiz.section_id) {
        router.replace(`/sections/${quiz.section_id}` as Href);
      } else if (document) {
        router.replace(`/documents/${document.id}` as Href);
      } else {
        router.back();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete this practice quiz');
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return <LoadingState message="Loading practice quiz" />;
  }

  const unansweredCount = quiz?.questions.filter((question) => !answers[question.id]).length ?? 0;
  const answeredCount = quiz ? quiz.questions.length - unansweredCount : 0;
  const canSubmit = !!quiz && unansweredCount === 0 && !submitting;

  return (
    <ScreenScrollView contentContainerStyle={styles.container}>
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {quiz ? (
        <>
          <View style={styles.header}>
            <Text style={styles.title}>{quiz.title}</Text>
            {section ? <Text style={styles.subtitle}>From section: {section.title}</Text> : document ? <Text style={styles.subtitle}>From {document.filename}</Text> : null}
          </View>
          <View style={styles.managementActions}>
            <Button
              title={regenerating ? 'Creating...' : 'Create Similar Quiz'}
              disabled={(!document && !quiz.section_id) || submitting || regenerating || deleting}
              variant="secondary"
              onPress={createSimilarQuiz}
            />
          </View>
          <Card>
            <View style={styles.progressHeader}>
              <Text style={styles.progressTitle}>{result ? 'Review your practice' : 'Answer progress'}</Text>
              <Text style={styles.progressMeta}>
                {answeredCount}/{quiz.questions.length} answered
              </Text>
            </View>
            <View style={styles.progressTrack}>
              <View style={[styles.progressFill, { width: `${quiz.questions.length ? (answeredCount / quiz.questions.length) * 100 : 0}%` }]} />
            </View>
            <Text style={styles.resultMeta}>
              {result
                ? result.missed_topics.length
                  ? `Review ${result.missed_topics.length} weak area${result.missed_topics.length === 1 ? '' : 's'} before practicing again.`
                  : 'No weak areas from this attempt. Keep the source fresh with another practice pass later.'
                : unansweredCount > 0
                  ? `Answer ${unansweredCount} more question${unansweredCount === 1 ? '' : 's'} before submitting.`
                  : 'Ready to submit.'}
            </Text>
          </Card>
          {quiz.questions.map((question) => {
            const answerResult = result?.answers.find((answer) => answer.question_id === question.id);
            return (
              <QuizQuestionView
                key={question.id}
                question={question}
                selected={answers[question.id]}
                result={answerResult}
                onSelect={(answer) => setAnswers((current) => ({ ...current, [question.id]: answer }))}
              />
            );
          })}
          {!result ? (
            <Button
              title={submitting ? 'Submitting...' : unansweredCount > 0 ? `Answer ${unansweredCount} more` : 'Submit Practice'}
              disabled={!canSubmit}
              onPress={submit}
            />
          ) : null}

          {result ? (
            <Card>
              <Text style={styles.resultEyebrow}>Review Next</Text>
              {result.missed_topics.length ? (
                <View style={styles.weakAreaBox}>
                  <Text style={styles.weakAreaTitle}>{result.missed_topics.join(', ')}</Text>
                  <Text style={styles.resultMeta}>Revisit these topics before creating another practice quiz.</Text>
                </View>
              ) : (
                <View style={styles.strongBox}>
                  <Text style={styles.strongTitle}>No weak areas recorded</Text>
                  <Text style={styles.resultMeta}>You answered every question correctly on this attempt.</Text>
                </View>
              )}
              <View style={styles.scoreRow}>
                <View>
                  <Text style={styles.resultEyebrow}>Score</Text>
                  <Text style={styles.resultTitle}>{formatPercent(result.score)}</Text>
                </View>
                <View style={styles.scoreMetaBox}>
                  <Text style={styles.resultMeta}>{result.correct_count} of {result.total_questions} correct</Text>
                </View>
              </View>
              <View style={styles.resultActions}>
                {document ? (
                  <>
                    <Button title="Review Source" variant="secondary" onPress={() => router.push(`/documents/${document.id}`)} />
                    <Button title="Back to Course" variant="secondary" onPress={() => router.push(`/courses/${document.course_id}`)} />
                  </>
                ) : null}
                {section ? (
                  <Button title="Back to Section" variant="secondary" onPress={() => router.push(`/sections/${section.id}` as Href)} />
                ) : null}
                <Button
                  title="Practice Again"
                  variant="secondary"
                  disabled={regenerating || deleting}
                  onPress={() => {
                    setAnswers({});
                    setResult(null);
                    setError(null);
                  }}
                />
              </View>
              <View style={styles.explanations}>
                {result.answers.map((answer) => (
                  <ExplanationBlock key={answer.question_id} answer={answer} />
                ))}
              </View>
            </Card>
          ) : null}

          <Card>
            <Text style={styles.resultEyebrow}>Quiz Management</Text>
            <Text style={styles.resultMeta}>Delete this quiz only when you no longer need its questions or saved attempts.</Text>
            <Button
              title={deleting ? 'Deleting...' : 'Delete Quiz'}
              disabled={submitting || regenerating || deleting}
              variant="danger"
              onPress={confirmDeleteQuiz}
            />
          </Card>
        </>
      ) : null}
    </ScreenScrollView>
  );
}

function ExplanationBlock({ answer }: { answer: QuizAttemptResult['answers'][number] }) {
  const parsed = parseQuizExplanation(answer.explanation);
  return (
    <View style={styles.explanation}>
      <Text style={answer.is_correct ? styles.correct : styles.incorrect}>
        {answer.is_correct ? 'Correct' : 'Review'} - {answer.topic}
      </Text>
      <Text style={styles.resultMeta}>{parsed.summary}</Text>
      {parsed.sourceQuote ? (
        <View style={styles.quoteBox}>
          <Text style={styles.quoteLabel}>Source Evidence</Text>
          <Text style={styles.quoteText}>{parsed.sourceQuote}</Text>
        </View>
      ) : null}
      {parsed.wrongChoiceReasons.length ? (
        <View style={styles.rationaleBox}>
          <Text style={styles.rationaleTitle}>Why The Other Choices Do Not Fit</Text>
          {parsed.wrongChoiceReasons.map((reason) => (
            <Text key={reason} style={styles.rationaleText}>{reason}</Text>
          ))}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
    maxWidth: 920,
  },
  header: {
    gap: 4,
  },
  title: {
    color: colors.text,
    fontSize: 26,
    fontWeight: '900',
    lineHeight: 32,
  },
  subtitle: {
    color: colors.textMuted,
    lineHeight: 20,
  },
  progressHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  managementActions: {
    gap: 8,
  },
  progressTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '900',
  },
  progressMeta: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: '800',
  },
  progressTrack: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: 8,
    height: 10,
    overflow: 'hidden',
  },
  progressFill: {
    backgroundColor: colors.accent,
    borderRadius: 8,
    height: '100%',
  },
  resultTitle: {
    color: colors.text,
    fontSize: 34,
    fontWeight: '900',
    lineHeight: 40,
  },
  resultEyebrow: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  resultMeta: {
    color: colors.text,
    lineHeight: 20,
  },
  explanations: {
    gap: 12,
    marginTop: 8,
  },
  resultActions: {
    gap: 8,
    marginTop: 12,
  },
  scoreRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 14,
    justifyContent: 'space-between',
  },
  scoreMetaBox: {
    alignItems: 'flex-end',
    flex: 1,
  },
  weakAreaBox: {
    backgroundColor: colors.warningSurface,
    borderRadius: 8,
    gap: 5,
    padding: 10,
  },
  weakAreaTitle: {
    color: colors.primary,
    fontWeight: '900',
  },
  strongBox: {
    backgroundColor: colors.successSurface,
    borderRadius: 8,
    gap: 5,
    padding: 10,
  },
  strongTitle: {
    color: colors.text,
    fontWeight: '900',
  },
  explanation: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    gap: 8,
    paddingTop: 12,
  },
  correct: {
    color: colors.success,
    fontWeight: '800',
  },
  incorrect: {
    color: colors.danger,
    fontWeight: '800',
  },
  quoteBox: {
    backgroundColor: colors.accentSurface,
    borderLeftColor: colors.accent,
    borderLeftWidth: 3,
    borderRadius: 8,
    gap: 4,
    padding: 10,
  },
  quoteLabel: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  quoteText: {
    color: colors.text,
    fontStyle: 'italic',
    lineHeight: 20,
  },
  rationaleBox: {
    gap: 6,
  },
  rationaleTitle: {
    color: colors.text,
    fontWeight: '800',
  },
  rationaleText: {
    color: colors.textMuted,
    lineHeight: 19,
  },
});
