import { Link, router } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { Dashboard } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { colors } from '@/constants/colors';
import { formatDate } from '@/utils/format';

export default function DashboardScreen() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setDashboard(await api.dashboard());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load dashboard');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <LoadingState message="Loading dashboard" />;
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}

      <View style={styles.header}>
        <Text style={styles.title}>StudyPilot</Text>
        <Text style={styles.subtitle}>Turn course materials into review tools.</Text>
      </View>

      <View style={styles.actions}>
        <Button title="Create Course" onPress={() => router.push('/courses/new')} />
        <Button title="View Courses" variant="secondary" onPress={() => router.push('/courses')} />
        <Button title="Settings" variant="secondary" onPress={() => router.push('/settings')} />
      </View>

      {dashboard ? (
        <>
          <View style={styles.grid}>
            <Metric label="Courses" value={dashboard.course_count} />
            <Metric label="Documents" value={dashboard.document_count} />
            <Metric label="Summaries" value={dashboard.summary_count} />
            <Metric label="Quizzes" value={dashboard.quiz_count} />
          </View>

          <Section title="Recent Courses">
            {dashboard.recent_courses.length ? (
              dashboard.recent_courses.map((course) => (
                <Link key={course.id} href={`/courses/${course.id}`} asChild>
                  <Card>
                    <Text style={styles.itemTitle}>{course.title}</Text>
                    <Text style={styles.itemMeta}>{formatDate(course.created_at)}</Text>
                  </Card>
                </Link>
              ))
            ) : (
              <EmptyState title="No courses yet" message="Create a course to start building study materials." />
            )}
          </Section>

          <Section title="Recent Documents">
            {dashboard.recent_documents.length ? (
              dashboard.recent_documents.map((document) => (
                <Link key={document.id} href={`/documents/${document.id}`} asChild>
                  <Card>
                    <Text style={styles.itemTitle}>{document.filename}</Text>
                    <Text style={styles.itemMeta}>{document.char_count} chars · {document.status}</Text>
                  </Card>
                </Link>
              ))
            ) : (
              <EmptyState title="No documents" message="Upload notes from a course detail screen." />
            )}
          </Section>

          <Section title="Weak Topics">
            {dashboard.weak_topics.length ? (
              dashboard.weak_topics.map((topic) => (
                <Card key={topic.id}>
                  <Text style={styles.itemTitle}>{topic.topic}</Text>
                  <Text style={styles.itemMeta}>Missed {topic.miss_count} times</Text>
                </Card>
              ))
            ) : (
              <EmptyState title="No weak topics" message="Missed quiz questions will appear here." />
            )}
          </Section>
        </>
      ) : null}
    </ScrollView>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
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
    fontSize: 28,
    fontWeight: '900',
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: 15,
  },
  actions: {
    gap: 10,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  metric: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    minWidth: '47%',
    padding: 14,
  },
  metricValue: {
    color: colors.text,
    fontSize: 24,
    fontWeight: '900',
  },
  metricLabel: {
    color: colors.textMuted,
    fontSize: 13,
  },
  section: {
    gap: 10,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '800',
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
