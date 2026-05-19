import { router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useState } from 'react';
import { RefreshControl, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { CourseDashboard, CourseQuizAttempt, Document, Quiz, ScheduleItem, Summary } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { ResponsiveGrid, ScreenScrollView } from '@/components/Screen';
import { StatusBanner } from '@/components/StatusBanner';
import { colors } from '@/constants/colors';
import { formatDateTime, formatPercent, formatTimeRemaining } from '@/utils/format';

export default function CourseStudySessionScreen() {
  const { courseId } = useLocalSearchParams<{ courseId: string }>();
  const id = Number(courseId);
  const [dashboard, setDashboard] = useState<CourseDashboard | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [attempts, setAttempts] = useState<CourseQuizAttempt[]>([]);
  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [creatingPractice, setCreatingPractice] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const [courseDashboard, docs, summaryList, quizList, attemptList, scheduleList] = await Promise.all([
        api.courseDashboard(id),
        api.courseDocuments(id),
        api.courseSummaries(id),
        api.courseQuizzes(id),
        api.courseAttempts(id),
        api.courseSchedule(id, false),
      ]);
      setDashboard(courseDashboard);
      setDocuments(docs);
      setSummaries(summaryList);
      setQuizzes(quizList);
      setAttempts(attemptList);
      setSchedule(scheduleList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load this study session');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  async function createPractice() {
    const extractedDocument = documents.find((document) => document.status === 'extracted');
    if (!dashboard || !extractedDocument) {
      return;
    }
    try {
      setCreatingPractice(true);
      setError(null);
      const quiz = dashboard.weak_topics.length
        ? await api.createReviewQuiz(id, 5, 'medium')
        : await api.createQuiz(extractedDocument.id, 5, 'mixed');
      router.push(`/quiz/${quiz.id}` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create practice');
    } finally {
      setCreatingPractice(false);
    }
  }

  if (loading) {
    return <LoadingState message="Building study session" />;
  }

  const latestSummary = summaries[0];
  const latestQuiz = quizzes[0];
  const latestAttempt = attempts[0];
  const nextDeadline = schedule[0];
  const readableDocuments = documents.filter((document) => document.status === 'extracted');
  const attentionDocuments = documents.filter((document) => (
    document.status === 'needs_ocr' ||
    document.extraction_quality === 'poor' ||
    document.extraction_quality === 'partial'
  ));
  const primaryWeakTopic = dashboard?.weak_topics[0];

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {creatingPractice ? (
        <StatusBanner
          title="Creating focused practice"
          message="StudyPilot is turning your course material into a short study session quiz."
        />
      ) : null}
      {dashboard ? (
        <>
          <View style={styles.header}>
            <Text style={styles.title}>Study Session</Text>
            <Text style={styles.subtitle}>{dashboard.course.title}</Text>
          </View>

          <Card style={styles.todayCard}>
            <Text style={styles.eyebrow}>Today</Text>
            <Text style={styles.todayTitle}>{sessionHeadline(primaryWeakTopic?.topic, nextDeadline)}</Text>
            <Text style={styles.bodyText}>{sessionMessage(readableDocuments.length, summaries.length, quizzes.length)}</Text>
            <View style={styles.actions}>
              <Button
                title={creatingPractice ? 'Creating...' : primaryWeakTopic ? 'Practice Weak Area' : 'Create Source Quiz'}
                disabled={creatingPractice || !readableDocuments.length}
                onPress={createPractice}
              />
              {latestSummary ? (
                <Button title="Review Latest Notes" variant="secondary" onPress={() => router.push(`/summaries/${latestSummary.id}` as Href)} />
              ) : null}
            </View>
          </Card>

          <ResponsiveGrid minItemWidth={320}>
            <Card>
              <Text style={styles.cardTitle}>1. Check Deadline</Text>
              {nextDeadline ? (
                <>
                  <Text style={styles.itemTitle}>{nextDeadline.title}</Text>
                  <Text style={styles.itemMeta}>{formatTimeRemaining(nextDeadline.due_at, nextDeadline.is_completed)}</Text>
                  <Text style={styles.itemMeta}>{formatDateTime(nextDeadline.due_at)}</Text>
                </>
              ) : (
                <Text style={styles.bodyText}>No active deadlines are scheduled for this course.</Text>
              )}
              <Button title="Open Deadlines" variant="secondary" onPress={() => router.push(`/schedule/course/${id}` as Href)} />
            </Card>

            <Card>
              <Text style={styles.cardTitle}>2. Review Notes</Text>
              {latestSummary ? (
                <>
                  <Text style={styles.itemTitle}>{latestSummary.title}</Text>
                  <Text style={styles.itemMeta}>{summaryTypeLabel(latestSummary.summary_type)} notes</Text>
                  <Button title="Open Notes" variant="secondary" onPress={() => router.push(`/summaries/${latestSummary.id}` as Href)} />
                </>
              ) : (
                <EmptyState title="No review notes yet" message="Create notes from a source before starting deeper review." />
              )}
            </Card>

            <Card>
              <Text style={styles.cardTitle}>3. Practice</Text>
              {latestQuiz ? (
                <>
                  <Text style={styles.itemTitle}>{latestQuiz.title}</Text>
                  <Text style={styles.itemMeta}>{latestQuiz.questions.length} questions ready</Text>
                  {latestAttempt ? (
                    <Text style={styles.itemMeta}>Last score: {formatPercent(latestAttempt.score)}</Text>
                  ) : null}
                  <Button title="Open Practice" variant="secondary" onPress={() => router.push(`/quiz/${latestQuiz.id}` as Href)} />
                </>
              ) : (
                <>
                  <Text style={styles.bodyText}>Create a short quiz from weak areas or the latest readable source.</Text>
                  <Button title={creatingPractice ? 'Creating...' : 'Create Practice'} disabled={creatingPractice || !readableDocuments.length} onPress={createPractice} />
                </>
              )}
            </Card>

            <Card>
              <Text style={styles.cardTitle}>4. Source Health</Text>
              <Text style={styles.bodyText}>{sourceHealthMessage(documents.length, readableDocuments.length, attentionDocuments.length)}</Text>
              {attentionDocuments[0] ? (
                <>
                  <Text style={styles.itemTitle}>{attentionDocuments[0].filename}</Text>
                  <Text style={styles.itemMeta}>{sourceStatusLabel(attentionDocuments[0])}</Text>
                  <Button title="Review Source" variant="secondary" onPress={() => router.push(`/documents/${attentionDocuments[0].id}` as Href)} />
                </>
              ) : documents[0] ? (
                <Button title="Open Sources" variant="secondary" onPress={() => router.push(`/courses/${id}` as Href)} />
              ) : null}
            </Card>
          </ResponsiveGrid>
        </>
      ) : null}
    </ScreenScrollView>
  );
}

function sessionHeadline(weakTopic: string | undefined, deadline: ScheduleItem | undefined): string {
  if (weakTopic) {
    return `Start with ${weakTopic}`;
  }
  if (deadline) {
    return `Prepare for ${deadline.title}`;
  }
  return 'Build a short review loop';
}

function sessionMessage(readableSources: number, notes: number, quizzes: number): string {
  if (!readableSources) {
    return 'Add or recognize source text first. StudyPilot needs readable material before it can create reliable notes or practice.';
  }
  if (!notes) {
    return 'Create review notes first, then use a short quiz to check understanding.';
  }
  if (!quizzes) {
    return 'Review the latest notes, then create a short quiz to turn reading into active recall.';
  }
  return 'Review notes, answer a practice quiz, then revisit weak areas before the next deadline.';
}

function sourceHealthMessage(total: number, readable: number, attention: number): string {
  if (!total) {
    return 'No source materials have been added yet.';
  }
  if (attention) {
    return `${attention} of ${total} source${total === 1 ? '' : 's'} may need OCR or a manual check before generation.`;
  }
  return `${readable} readable source${readable === 1 ? '' : 's'} are ready for notes and practice.`;
}

function sourceStatusLabel(document: Document): string {
  if (document.status === 'needs_ocr' || document.extraction_quality === 'poor') {
    return 'Needs text recognition before reliable studying';
  }
  if (document.extraction_quality === 'partial') {
    return `${Math.round(document.extraction_coverage * 100)}% readable - check source text`;
  }
  return 'Ready for study tools';
}

function summaryTypeLabel(value: string): string {
  if (value === 'concise') {
    return 'Quick review';
  }
  if (value === 'detailed') {
    return 'Deep review';
  }
  if (value === 'exam') {
    return 'Exam prep';
  }
  if (value === 'explanation') {
    return 'Additional explanation';
  }
  return value;
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
    lineHeight: 34,
  },
  subtitle: {
    color: colors.textMuted,
    lineHeight: 20,
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
  cardTitle: {
    color: colors.text,
    fontSize: 17,
    fontWeight: '900',
  },
  itemTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '800',
  },
  itemMeta: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 18,
  },
  bodyText: {
    color: colors.text,
    lineHeight: 20,
  },
  actions: {
    gap: 8,
  },
});
