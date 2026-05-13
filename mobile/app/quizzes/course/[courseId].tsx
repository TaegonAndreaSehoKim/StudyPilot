import { Link, useFocusEffect, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { Quiz } from '@/api/types';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
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
      setError(err instanceof Error ? err.message : 'Unable to load quizzes');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  if (loading) {
    return <LoadingState message="Loading quizzes" />;
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      <View style={styles.header}>
        <Text style={styles.title}>Saved Quizzes</Text>
        <Text style={styles.subtitle}>{quizzes.length} quizzes across this course</Text>
      </View>

      {quizzes.length ? (
        quizzes.map((quiz) => (
          <Link key={quiz.id} href={`/quiz/${quiz.id}` as Href} asChild>
            <Card>
              <Text style={styles.itemTitle}>{quiz.title}</Text>
              <Text style={styles.itemMeta}>
                {quiz.questions.length} questions - document #{quiz.document_id}
              </Text>
            </Card>
          </Link>
        ))
      ) : (
        <EmptyState title="No quizzes" message="Generate a quiz from a document and it will appear here." />
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
