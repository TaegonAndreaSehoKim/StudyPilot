import { Link, router } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { Course } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { colors } from '@/constants/colors';

export default function CoursesScreen() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setCourses(await api.courses());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load courses');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <LoadingState message="Loading courses" />;
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      <Button title="Create Course" onPress={() => router.push('/courses/new')} />
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {courses.length ? (
        courses.map((course) => (
          <Link key={course.id} href={`/courses/${course.id}`} asChild>
            <Card>
              <Text style={styles.title}>{course.title}</Text>
              {course.description ? <Text style={styles.description}>{course.description}</Text> : null}
            </Card>
          </Link>
        ))
      ) : (
        <EmptyState title="No courses" message="Create your first course to upload notes and generate study tools." />
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 12,
    padding: 16,
  },
  title: {
    color: colors.text,
    fontSize: 17,
    fontWeight: '800',
  },
  description: {
    color: colors.textMuted,
    lineHeight: 20,
  },
});
