import { Link, router, useFocusEffect } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';

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
      setError(err instanceof Error ? err.message : 'Unable to load your study dashboard');
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
        <Text style={styles.subtitle}>Pick up where your studying needs attention.</Text>
      </View>

      {!dashboard ? (
        <View style={[styles.actions, isTablet && styles.tabletActions]}>
          <Button title="Settings" variant="secondary" onPress={() => router.push('/settings')} />
        </View>
      ) : null}

      {loading ? <LoadingState message="Loading your study dashboard" /> : null}

      {dashboard ? (
        <>
          <Card style={styles.todayCard}>
            <Text style={styles.eyebrow}>Today</Text>
            <Text style={styles.todayTitle}>{dashboardHeadline(dashboard, schedule)}</Text>
            <Text style={styles.todayDetail}>{dashboardMessage(dashboard, schedule)}</Text>
            <View style={[styles.actions, isTablet && styles.tabletActions]}>
              <Button title={dashboardPrimaryActionLabel(dashboard, schedule)} onPress={() => openDashboardPrimaryAction(dashboard, schedule)} />
              <Button title="My Courses" variant="secondary" onPress={() => router.push('/courses')} />
            </View>
          </Card>

          <Section title="Due Soon">
            {schedule.length ? (
              <ResponsiveGrid minItemWidth={340}>
                {schedule.slice(0, 3).map((item) => (
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
                ))}
              </ResponsiveGrid>
            ) : (
              <EmptyState title="No deadlines yet" message="Add assignments or exam dates from a course page." />
            )}
          </Section>

          <Section title="Continue Studying">
            <ResponsiveGrid minItemWidth={300}>
              {dashboard.weak_topics[0] ? (
                <FocusCard
                  eyebrow="Review Weak Area"
                  title={dashboard.weak_topics[0].topic}
                  detail={`Missed ${dashboard.weak_topics[0].miss_count} times. Practice this from the course page.`}
                  actionLabel="Start review"
                  href={`/courses/${dashboard.weak_topics[0].course_id}` as Href}
                />
              ) : null}
              {dashboard.recent_quizzes[0] ? (
                <FocusCard
                  eyebrow="Practice"
                  title={dashboard.recent_quizzes[0].title}
                  detail={`${dashboard.recent_quizzes[0].questions.length} questions ready`}
                  actionLabel="Start quiz"
                  href={`/quiz/${dashboard.recent_quizzes[0].id}` as Href}
                />
              ) : null}
              {dashboard.recent_summaries[0] ? (
                <FocusCard
                  eyebrow="Review"
                  title={dashboard.recent_summaries[0].title}
                  detail={`${summaryTypeLabel(dashboard.recent_summaries[0].summary_type)} review notes`}
                  actionLabel="Read notes"
                  href={`/summaries/${dashboard.recent_summaries[0].id}` as Href}
                />
              ) : null}
              {!dashboard.weak_topics.length && !dashboard.recent_quizzes.length && !dashboard.recent_summaries.length ? (
                <EmptyState title="Nothing queued yet" message="Add a course and source notes to start building review notes and practice." />
              ) : null}
            </ResponsiveGrid>
          </Section>

          <View style={[styles.actions, isTablet && styles.tabletActions]}>
            <Button title="New Course" variant="secondary" onPress={() => router.push('/courses/new')} />
            <Button title="Settings" variant="secondary" onPress={() => router.push('/settings')} />
          </View>

          <View style={styles.grid}>
            <Metric label="Courses" value={dashboard.course_count} />
            <Metric label="Sources" value={dashboard.document_count} onPress={() => router.push('/documents' as Href)} />
            <Metric label="Review Notes" value={dashboard.summary_count} />
            <Metric label="Practice" value={dashboard.quiz_count} />
          </View>

          <ResponsiveGrid minItemWidth={340}>
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
                <EmptyState title="No courses yet" message="Create a course to organize notes, reviews, practice, and deadlines." />
              )}
            </Section>

            <Section title="Recent Sources">
              {dashboard.recent_documents.length ? (
                dashboard.recent_documents.map((document) => (
                  <Link key={document.id} href={`/documents/${document.id}`} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>{document.filename}</Text>
                      <Text style={styles.itemMeta}>{sourceStatusLabel(document.status, document.extraction_quality)}</Text>
                      {document.file_type === '.pdf' ? (
                        <Text style={styles.itemMeta}>
                          {document.ocr_status !== 'not_required'
                            ? textRecognitionLabel(document.ocr_status)
                            : `${Math.round(document.extraction_coverage * 100)}% of PDF text available`}
                        </Text>
                      ) : null}
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No source materials" message="Open a course and add lecture notes, PDFs, or markdown files." />
              )}
            </Section>

            <Section title="Review Notes">
              {dashboard.recent_summaries.length ? (
                dashboard.recent_summaries.map((summary) => (
                  <Link key={summary.id} href={`/summaries/${summary.id}` as Href} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>{summary.title}</Text>
                      <Text style={styles.itemMeta}>{summaryTypeLabel(summary.summary_type)} notes</Text>
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No review notes" message="Create review notes from a source material and they will appear here." />
              )}
            </Section>

            <Section title="Practice Quizzes">
              {dashboard.recent_quizzes.length ? (
                dashboard.recent_quizzes.map((quiz) => (
                  <Link key={quiz.id} href={`/quiz/${quiz.id}`} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>{quiz.title}</Text>
                      <Text style={styles.itemMeta}>{quiz.questions.length} questions ready</Text>
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No practice quizzes" message="Create a quiz from source material when you are ready to test yourself." />
              )}
            </Section>

            <Section title="Weak Areas">
              {dashboard.weak_topics.length ? (
                dashboard.weak_topics.map((topic) => (
                  <Link key={topic.id} href={`/courses/${topic.course_id}` as Href} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>{topic.topic}</Text>
                      <Text style={styles.itemMeta}>Missed {topic.miss_count} times - practice from the course page</Text>
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No weak areas yet" message="Missed quiz questions will show where to review next." />
              )}
            </Section>
          </ResponsiveGrid>
        </>
      ) : null}
    </ScreenScrollView>
  );
}

function Metric({ label, value, onPress }: { label: string; value: number; onPress?: () => void }) {
  const content = (
    <>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </>
  );

  if (onPress) {
    return (
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`Open ${label}`}
        onPress={onPress}
        style={({ pressed }) => [styles.metric, styles.metricButton, pressed && styles.metricPressed]}
      >
        {content}
      </Pressable>
    );
  }

  return (
    <View style={styles.metric}>
      {content}
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

function dashboardHeadline(dashboard: Dashboard, schedule: GlobalScheduleItem[]): string {
  if (schedule[0]) {
    return `${formatTimeRemaining(schedule[0].due_at, schedule[0].is_completed)}: ${schedule[0].title}`;
  }
  if (dashboard.weak_topics[0]) {
    return `Review ${dashboard.weak_topics[0].topic}`;
  }
  if (dashboard.recent_quizzes[0]) {
    return 'Resume practice';
  }
  if (dashboard.recent_summaries[0]) {
    return 'Review latest notes';
  }
  return 'Set up your first study loop';
}

function dashboardMessage(dashboard: Dashboard, schedule: GlobalScheduleItem[]): string {
  if (schedule[0]) {
    return `${schedule[0].course_title} has the next deadline. Open it first, then review notes or practice.`;
  }
  if (dashboard.weak_topics[0]) {
    return 'A missed topic is ready for review. Practice it before adding more material.';
  }
  if (dashboard.recent_quizzes[0]) {
    return 'A practice quiz is ready. Use it to turn review into active recall.';
  }
  if (dashboard.recent_summaries[0]) {
    return 'Review notes are ready. Read them once, then create practice from the source.';
  }
  return 'Create a course, add a source, then build review notes and practice.';
}

function dashboardPrimaryActionLabel(dashboard: Dashboard, schedule: GlobalScheduleItem[]): string {
  if (schedule[0]) {
    return 'Open Deadline';
  }
  if (dashboard.weak_topics[0]) {
    return 'Review Course';
  }
  if (dashboard.recent_quizzes[0]) {
    return 'Start Practice';
  }
  if (dashboard.recent_summaries[0]) {
    return 'Read Notes';
  }
  return 'Create Course';
}

function openDashboardPrimaryAction(dashboard: Dashboard, schedule: GlobalScheduleItem[]) {
  if (schedule[0]) {
    router.push(`/schedule/course/${schedule[0].course_id}` as Href);
    return;
  }
  if (dashboard.weak_topics[0]) {
    router.push(`/courses/${dashboard.weak_topics[0].course_id}` as Href);
    return;
  }
  if (dashboard.recent_quizzes[0]) {
    router.push(`/quiz/${dashboard.recent_quizzes[0].id}` as Href);
    return;
  }
  if (dashboard.recent_summaries[0]) {
    router.push(`/summaries/${dashboard.recent_summaries[0].id}` as Href);
    return;
  }
  router.push('/courses/new');
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
  if (value === 'explanation') {
    return 'Additional Explanation';
  }
  return value;
}

function sourceStatusLabel(status: string, quality: string): string {
  if (status === 'needs_ocr' || quality === 'poor') {
    return 'Needs text recognition before studying';
  }
  if (quality === 'partial') {
    return 'Partially readable - review source text before generating';
  }
  return 'Ready for review notes and practice';
}

function textRecognitionLabel(value: string): string {
  if (value === 'completed') {
    return 'Text recognition complete';
  }
  if (value === 'queued' || value === 'running') {
    return 'Text recognition in progress';
  }
  return 'Text recognition available';
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
    padding: 16,
  },
  header: {
    gap: 6,
    paddingTop: 2,
  },
  title: {
    color: colors.text,
    fontSize: 30,
    fontWeight: '900',
    lineHeight: 36,
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: 15,
    lineHeight: 21,
  },
  actions: {
    gap: 10,
  },
  tabletActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
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
    flexGrow: 1,
    minWidth: '47%',
    padding: 14,
  },
  metricButton: {
    borderColor: colors.primarySurface,
  },
  metricPressed: {
    borderColor: colors.primary,
    opacity: 0.9,
    transform: [{ translateY: 1 }],
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
  todayCard: {
    backgroundColor: colors.primarySurface,
    borderColor: colors.primary,
  },
  eyebrow: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  todayTitle: {
    color: colors.text,
    fontSize: 22,
    fontWeight: '900',
    lineHeight: 28,
  },
  todayDetail: {
    color: colors.textMuted,
    lineHeight: 20,
  },
  focusCard: {
    backgroundColor: colors.surface,
    borderColor: colors.primarySurface,
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
    backgroundColor: colors.accentSurface,
    borderRadius: 8,
    color: colors.accent,
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
