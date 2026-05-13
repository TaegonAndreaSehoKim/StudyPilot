import { useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { Quiz, QuizAttemptResult } from '@/api/types';
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
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<QuizAttemptResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setQuiz(await api.quiz(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load quiz');
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
      setError(err instanceof Error ? err.message : 'Unable to submit quiz');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <LoadingState message="Loading quiz" />;
  }

  const unansweredCount = quiz?.questions.filter((question) => !answers[question.id]).length ?? 0;
  const canSubmit = !!quiz && unansweredCount === 0 && !submitting;

  return (
    <ScreenScrollView contentContainerStyle={styles.container}>
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {quiz ? (
        <>
          <Text style={styles.title}>{quiz.title}</Text>
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
              title={submitting ? 'Submitting...' : unansweredCount > 0 ? `Answer ${unansweredCount} more` : 'Submit Answers'}
              disabled={!canSubmit}
              onPress={submit}
            />
          ) : null}

          {result ? (
            <Card>
              <Text style={styles.resultTitle}>Score: {formatPercent(result.score)}</Text>
              <Text style={styles.resultMeta}>{result.correct_count} of {result.total_questions} correct</Text>
              {result.missed_topics.length ? (
                <Text style={styles.resultMeta}>Missed topics: {result.missed_topics.join(', ')}</Text>
              ) : null}
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
        {answer.is_correct ? 'Correct' : 'Missed'} - {answer.topic}
      </Text>
      <Text style={styles.resultMeta}>{parsed.summary}</Text>
      {parsed.sourceQuote ? (
        <View style={styles.quoteBox}>
          <Text style={styles.quoteLabel}>Source quote</Text>
          <Text style={styles.quoteText}>{parsed.sourceQuote}</Text>
        </View>
      ) : null}
      {parsed.wrongChoiceReasons.length ? (
        <View style={styles.rationaleBox}>
          <Text style={styles.rationaleTitle}>Why other choices are wrong</Text>
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
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: '900',
  },
  resultTitle: {
    color: colors.text,
    fontSize: 20,
    fontWeight: '900',
  },
  resultMeta: {
    color: colors.text,
    lineHeight: 20,
  },
  explanations: {
    gap: 12,
    marginTop: 8,
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
