import { useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { Quiz, QuizAttemptResult } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { QuizQuestionView } from '@/components/QuizQuestionView';
import { colors } from '@/constants/colors';
import { formatPercent } from '@/utils/format';

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
    <ScrollView contentContainerStyle={styles.container}>
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {quiz ? (
        <>
          <Text style={styles.title}>{quiz.title}</Text>
          {quiz.questions.map((question) => (
            <QuizQuestionView
              key={question.id}
              question={question}
              selected={answers[question.id]}
              onSelect={(answer) => setAnswers((current) => ({ ...current, [question.id]: answer }))}
            />
          ))}
          <Button
            title={submitting ? 'Submitting...' : unansweredCount > 0 ? `Answer ${unansweredCount} more` : 'Submit Answers'}
            disabled={!canSubmit}
            onPress={submit}
          />

          {result ? (
            <Card>
              <Text style={styles.resultTitle}>Score: {formatPercent(result.score)}</Text>
              <Text style={styles.resultMeta}>{result.correct_count} of {result.total_questions} correct</Text>
              {result.missed_topics.length ? (
                <Text style={styles.resultMeta}>Missed topics: {result.missed_topics.join(', ')}</Text>
              ) : null}
              <View style={styles.explanations}>
                {result.answers.map((answer) => (
                  <View key={answer.question_id} style={styles.explanation}>
                    <Text style={answer.is_correct ? styles.correct : styles.incorrect}>
                      {answer.is_correct ? 'Correct' : 'Missed'} - {answer.topic}
                    </Text>
                    <Text style={styles.resultMeta}>{answer.explanation}</Text>
                  </View>
                ))}
              </View>
            </Card>
          ) : null}
        </>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 14,
    padding: 16,
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
    gap: 4,
  },
  correct: {
    color: colors.success,
    fontWeight: '800',
  },
  incorrect: {
    color: colors.danger,
    fontWeight: '800',
  },
});
