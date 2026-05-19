import { Link, router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { RefreshControl, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { Course } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { ResponsiveGrid, ScreenScrollView, useTabletLayout } from '@/components/Screen';
import { colors } from '@/constants/colors';

export default function CoursesScreen() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isTablet = useTabletLayout();

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

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  if (loading) {
    return <LoadingState message="Loading courses" />;
  }

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      <View style={[styles.actions, isTablet && styles.tabletActions]}>
        <Button title="Create Course" onPress={() => router.push('/courses/new')} />
      </View>
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {courses.length ? (
        <ResponsiveGrid minItemWidth={320}>
          {courses.map((course) => (
            <Link key={course.id} href={`/courses/${course.id}`} asChild>
              <Card>
                <Text style={styles.title}>{course.title}</Text>
                {course.description ? <Text style={styles.description}>{course.description}</Text> : null}
                <Text style={styles.openLabel}>Open course</Text>
              </Card>
            </Link>
          ))}
        </ResponsiveGrid>
      ) : (
        <EmptyState title="No courses" message="Create your first course to upload notes and generate study tools." />
      )}
    </ScreenScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 12,
  },
  actions: {
    gap: 10,
  },
  tabletActions: {
    alignItems: 'flex-start',
  },
  title: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '900',
    lineHeight: 24,
  },
  description: {
    color: colors.textMuted,
    lineHeight: 20,
  },
  openLabel: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '900',
    marginTop: 2,
  },
});
