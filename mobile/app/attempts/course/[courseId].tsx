import { Link, useFocusEffect, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useState } from 'react';
import { RefreshControl, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { CourseQuizAttempt } from '@/api/types';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { ResponsiveGrid, ScreenScrollView } from '@/components/Screen';
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
      setError(err instanceof Error ? err.message : 'Unable to load practice history');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  if (loading) {
    return <LoadingState message="Loading practice history" />;
  }

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      <View style={styles.header}>
        <Text style={styles.title}>Practice History</Text>
        <Text style={styles.subtitle}>{attempts.length} saved practice attempt{attempts.length === 1 ? '' : 's'} for this course</Text>
      </View>

      {attempts.length ? (
        <ResponsiveGrid minItemWidth={340}>
          {attempts.map((attempt) => (
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
                  <Text style={styles.itemMeta}>Weak areas: {attempt.missed_topics.join(', ')}</Text>
                ) : (
                  <Text style={styles.itemMeta}>No weak areas recorded</Text>
                )}
              </Card>
            </Link>
          ))}
        </ResponsiveGrid>
      ) : (
        <EmptyState title="No practice history" message="Submit a practice quiz and your scores will appear here." />
      )}
    </ScreenScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
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
