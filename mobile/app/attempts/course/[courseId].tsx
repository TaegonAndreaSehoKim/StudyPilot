import { Link, useFocusEffect, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { CourseQuizAttempt } from '@/api/types';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { colors } from '@/constants/colors';
import { formatDate, formatPercent } from '@/utils/format';

export default function CourseAttemptsScreen() {
  const { courseId } = useLocalSearchParams<{ courseId: string }>();
  const id = Number(courseId);
  const [attempts, setAttempts] = useState<CourseQuizAttempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setAttempts(await api.courseAttempts(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load attempts');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  if (loading) {
    return <LoadingState message="Loading attempts" />;
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      <View style={styles.header}>
        <Text style={styles.title}>Quiz Attempts</Text>
        <Text style={styles.subtitle}>{attempts.length} attempts across this course</Text>
      </View>

      {attempts.length ? (
        attempts.map((attempt) => (
          <Link key={attempt.id} href={`/quiz/${attempt.quiz_id}` as Href} asChild>
            <Card>
              <View style={styles.attemptHeader}>
                <Text style={styles.itemTitle}>{attempt.quiz_title}</Text>
                <Text style={styles.score}>{formatPercent(attempt.score)}</Text>
              </View>
              <Text style={styles.itemMeta}>
                {attempt.correct_count} of {attempt.total_questions} correct - {formatDate(attempt.created_at)}
              </Text>
              {attempt.missed_topics.length ? (
                <Text style={styles.itemMeta}>Missed: {attempt.missed_topics.join(', ')}</Text>
              ) : (
                <Text style={styles.itemMeta}>No missed topics</Text>
              )}
            </Card>
          </Link>
        ))
      ) : (
        <EmptyState title="No attempts" message="Submit a quiz and your scores will appear here." />
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
    padding: 16,
  },
  header: {
    gap: 4,
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: '800',
    lineHeight: 30,
  },
  subtitle: {
    color: colors.textMuted,
  },
  attemptHeader: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    gap: 12,
    justifyContent: 'space-between',
  },
  itemTitle: {
    color: colors.text,
    flex: 1,
    fontSize: 16,
    fontWeight: '800',
  },
  score: {
    color: colors.primary,
    fontSize: 18,
    fontWeight: '900',
  },
  itemMeta: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 18,
  },
});
