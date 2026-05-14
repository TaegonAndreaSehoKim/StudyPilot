import { Link, useFocusEffect, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useState } from 'react';
import { RefreshControl, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { Quiz } from '@/api/types';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { ResponsiveGrid, ScreenScrollView } from '@/components/Screen';
import { colors } from '@/constants/colors';

export default function CourseQuizzesScreen() {
  const { courseId } = useLocalSearchParams<{ courseId: string }>();
  const id = Number(courseId);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setQuizzes(await api.courseQuizzes(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load practice quizzes');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  if (loading) {
    return <LoadingState message="Loading practice quizzes" />;
  }

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      <View style={styles.header}>
        <Text style={styles.title}>Practice Quizzes</Text>
        <Text style={styles.subtitle}>{quizzes.length} practice set{quizzes.length === 1 ? '' : 's'} ready for this course</Text>
      </View>

      {quizzes.length ? (
        <ResponsiveGrid minItemWidth={340}>
          {quizzes.map((quiz) => (
            <Link key={quiz.id} href={`/quiz/${quiz.id}` as Href} asChild>
              <Card>
                <Text style={styles.itemTitle}>{quiz.title}</Text>
                <Text style={styles.itemMeta}>
                  {quiz.questions.length} questions ready
                </Text>
              </Card>
            </Link>
          ))}
        </ResponsiveGrid>
      ) : (
        <EmptyState title="No practice quizzes" message="Create a quiz from a source material and it will appear here." />
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
  itemTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '800',
  },
  itemMeta: {
    color: colors.textMuted,
    fontSize: 13,
  },
});
