import { router, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { DocumentDetail, Quiz, QuizAttemptResult } from '@/api/types';
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
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<QuizAttemptResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const loadedQuiz = await api.quiz(id);
      setQuiz(loadedQuiz);
      setDocument(await api.document(loadedQuiz.document_id));
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
            {document ? <Text style={styles.subtitle}>From {document.filename}</Text> : null}
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
              <Text style={styles.resultEyebrow}>Practice Result</Text>
              <Text style={styles.resultTitle}>{formatPercent(result.score)}</Text>
              <Text style={styles.resultMeta}>{result.correct_count} of {result.total_questions} correct</Text>
              {result.missed_topics.length ? (
                <View style={styles.weakAreaBox}>
                  <Text style={styles.weakAreaTitle}>Review Next</Text>
                  <Text style={styles.resultMeta}>{result.missed_topics.join(', ')}</Text>
                </View>
              ) : (
                <View style={styles.strongBox}>
                  <Text style={styles.strongTitle}>No weak areas recorded</Text>
                  <Text style={styles.resultMeta}>You answered every question correctly on this attempt.</Text>
                </View>
              )}
              <View style={styles.resultActions}>
                {document ? (
                  <>
                    <Button title="Review Source" variant="secondary" onPress={() => router.push(`/documents/${document.id}`)} />
                    <Button title="Back to Course" variant="secondary" onPress={() => router.push(`/courses/${document.course_id}`)} />
                  </>
                ) : null}
                <Button
                  title="Practice Again"
                  variant="secondary"
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
    gap: 14,
    maxWidth: 920,
  },
  header: {
    gap: 4,
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: '900',
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
    backgroundColor: colors.primary,
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
    backgroundColor: colors.surfaceMuted,
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
