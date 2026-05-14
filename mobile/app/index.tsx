import { Link, router, useFocusEffect } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useState } from 'react';
import { RefreshControl, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { Dashboard, GlobalScheduleItem } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { ResponsiveGrid, ScreenScrollView, useTabletLayout } from '@/components/Screen';
import { colors } from '@/constants/colors';
import { formatDate, formatDateTime, formatTimeRemaining } from '@/utils/format';

export default function DashboardScreen() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [schedule, setSchedule] = useState<GlobalScheduleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isTablet = useTabletLayout();

  const load = useCallback(async () => {
    try {
      setError(null);
      const [dashboardData, scheduleData] = await Promise.all([
        api.dashboard(),
        api.globalSchedule(false, 10),
      ]);
      setDashboard(dashboardData);
      setSchedule(scheduleData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load dashboard');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}

      <View style={styles.header}>
        <Text style={styles.title}>StudyPilot</Text>
        <Text style={styles.subtitle}>Turn course materials into review tools.</Text>
      </View>

      <View style={[styles.actions, isTablet && styles.tabletActions]}>
        <Button title="Create Course" onPress={() => router.push('/courses/new')} />
        <Button title="View Courses" variant="secondary" onPress={() => router.push('/courses')} />
        <Button title="Settings" variant="secondary" onPress={() => router.push('/settings')} />
      </View>

      {loading ? <LoadingState message="Loading dashboard" /> : null}

      {dashboard ? (
        <>
          <View style={styles.grid}>
            <Metric label="Courses" value={dashboard.course_count} />
            <Metric label="Documents" value={dashboard.document_count} />
            <Metric label="Summaries" value={dashboard.summary_count} />
            <Metric label="Quizzes" value={dashboard.quiz_count} />
          </View>

          <Section title="Study Focus">
            <ResponsiveGrid minItemWidth={300}>
              {schedule[0] ? (
                <FocusCard
                  eyebrow="Next Deadline"
                  title={schedule[0].title}
                  detail={`${schedule[0].course_title} - ${formatTimeRemaining(schedule[0].due_at, schedule[0].is_completed)}`}
                  actionLabel="Open Schedule"
                  href={`/schedule/course/${schedule[0].course_id}` as Href}
                />
              ) : null}
              {dashboard.weak_topics[0] ? (
                <FocusCard
                  eyebrow="Weak Topic"
                  title={dashboard.weak_topics[0].topic}
                  detail={`Missed ${dashboard.weak_topics[0].miss_count} times. Generate a weak-topic quiz from the course Practice tab.`}
                  actionLabel="Open Course"
                  href={`/courses/${dashboard.weak_topics[0].course_id}` as Href}
                />
              ) : null}
              {dashboard.recent_quizzes[0] ? (
                <FocusCard
                  eyebrow="Practice"
                  title={dashboard.recent_quizzes[0].title}
                  detail={`${dashboard.recent_quizzes[0].questions.length} questions ready`}
                  actionLabel="Take Quiz"
                  href={`/quiz/${dashboard.recent_quizzes[0].id}` as Href}
                />
              ) : null}
              {dashboard.recent_summaries[0] ? (
                <FocusCard
                  eyebrow="Review"
                  title={dashboard.recent_summaries[0].title}
                  detail={`${summaryTypeLabel(dashboard.recent_summaries[0].summary_type)} summary`}
                  actionLabel="Read Summary"
                  href={`/summaries/${dashboard.recent_summaries[0].id}` as Href}
                />
              ) : null}
              {!schedule.length && !dashboard.weak_topics.length && !dashboard.recent_quizzes.length && !dashboard.recent_summaries.length ? (
                <EmptyState title="No study focus yet" message="Create a course, upload notes, and generate a summary or quiz to start a study loop." />
              ) : null}
            </ResponsiveGrid>
          </Section>

          <ResponsiveGrid minItemWidth={340}>
            <Section title="Upcoming Schedule">
              {schedule.length ? (
                schedule.map((item) => (
                  <Link key={item.id} href={`/schedule/course/${item.course_id}` as Href} asChild>
                    <Card>
                      <View style={styles.itemHeader}>
                        <Text style={styles.itemTitle}>{item.title}</Text>
                        <Text style={styles.itemBadge}>{item.event_type}</Text>
                      </View>
                      <Text style={styles.itemMeta}>{item.course_title}</Text>
                      <Text style={styles.itemMeta}>{formatTimeRemaining(item.due_at, item.is_completed)} - {formatDateTime(item.due_at)}</Text>
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No upcoming schedule" message="Add deadlines or exam dates from a course schedule screen." />
              )}
            </Section>

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
                      <Text style={styles.itemMeta}>{document.char_count} chars - {document.status} - {documentExtractionLabel(document.extraction_quality)}</Text>
                      {document.file_type === '.pdf' ? (
                        <Text style={styles.itemMeta}>
                          {Math.round(document.extraction_coverage * 100)}% coverage
                          {document.ocr_status !== 'not_required' ? ` - OCR ${document.ocr_status}` : ''}
                        </Text>
                      ) : null}
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No documents" message="Upload notes from a course detail screen." />
              )}
            </Section>

            <Section title="Recent Summaries">
              {dashboard.recent_summaries.length ? (
                dashboard.recent_summaries.map((summary) => (
                  <Link key={summary.id} href={`/summaries/${summary.id}` as Href} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>{summary.title}</Text>
                      <Text style={styles.itemMeta}>{summary.summary_type} summary - document #{summary.document_id}</Text>
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No summaries" message="Generate a summary from a document and it will appear here." />
              )}
            </Section>

            <Section title="Recent Quizzes">
              {dashboard.recent_quizzes.length ? (
                dashboard.recent_quizzes.map((quiz) => (
                  <Link key={quiz.id} href={`/quiz/${quiz.id}`} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>{quiz.title}</Text>
                      <Text style={styles.itemMeta}>{quiz.questions.length} questions - document #{quiz.document_id}</Text>
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No quizzes" message="Generate a quiz from a document and it will appear here." />
              )}
            </Section>

            <Section title="Weak Topics">
              {dashboard.weak_topics.length ? (
                dashboard.weak_topics.map((topic) => (
                  <Link key={topic.id} href={`/courses/${topic.course_id}` as Href} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>{topic.topic}</Text>
                      <Text style={styles.itemMeta}>Missed {topic.miss_count} times - open course practice</Text>
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No weak topics" message="Missed quiz questions will appear here." />
              )}
            </Section>
          </ResponsiveGrid>
        </>
      ) : null}
    </ScreenScrollView>
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

function FocusCard({
  eyebrow,
  title,
  detail,
  actionLabel,
  href,
}: {
  eyebrow: string;
  title: string;
  detail: string;
  actionLabel: string;
  href: Href;
}) {
  return (
    <Link href={href} asChild>
      <Card style={styles.focusCard}>
        <Text style={styles.focusEyebrow}>{eyebrow}</Text>
        <Text style={styles.focusTitle}>{title}</Text>
        <Text style={styles.focusDetail}>{detail}</Text>
        <Text style={styles.focusAction}>{actionLabel}</Text>
      </Card>
    </Link>
  );
}

function summaryTypeLabel(value: string): string {
  if (value === 'concise') {
    return 'Concise';
  }
  if (value === 'detailed') {
    return 'Detailed';
  }
  if (value === 'exam') {
    return 'Exam';
  }
  return value;
}

function documentExtractionLabel(value: string): string {
  if (value === 'ocr') {
    return 'OCR text';
  }
  if (value === 'poor') {
    return 'OCR required';
  }
  if (value === 'partial') {
    return 'partial extraction';
  }
  return 'good extraction';
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
  tabletActions: {
    flexDirection: 'row',
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
  focusCard: {
    backgroundColor: colors.infoSurface,
  },
  focusEyebrow: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  focusTitle: {
    color: colors.text,
    fontSize: 17,
    fontWeight: '900',
    lineHeight: 23,
  },
  focusDetail: {
    color: colors.textMuted,
    lineHeight: 20,
  },
  focusAction: {
    color: colors.primary,
    fontWeight: '900',
    marginTop: 2,
  },
  itemTitle: {
    color: colors.text,
    flex: 1,
    fontSize: 16,
    fontWeight: '800',
  },
  itemHeader: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    gap: 10,
    justifyContent: 'space-between',
  },
  itemBadge: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: 8,
    color: colors.text,
    fontSize: 12,
    fontWeight: '800',
    overflow: 'hidden',
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  itemMeta: {
    color: colors.textMuted,
    fontSize: 13,
  },
});
