import * as DocumentPicker from 'expo-document-picker';
import { Link, router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useState } from 'react';
import { Alert, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { CourseDashboard, CourseQuizAttempt, Document, Flashcard, Quiz, ScheduleItem, Summary } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { ResponsiveGrid, ScreenScrollView, useTabletLayout } from '@/components/Screen';
import { StatusBanner } from '@/components/StatusBanner';
import { colors } from '@/constants/colors';
import { formatDateTime, formatTimeRemaining } from '@/utils/format';

type CourseTab = 'overview' | 'materials' | 'practice' | 'schedule';

const COURSE_TABS: { key: CourseTab; label: string }[] = [
  { key: 'overview', label: 'Study' },
  { key: 'materials', label: 'Library' },
  { key: 'practice', label: 'Practice' },
  { key: 'schedule', label: 'Deadlines' },
];

export default function CourseDetailScreen() {
  const { courseId } = useLocalSearchParams<{ courseId: string }>();
  const id = Number(courseId);
  const [dashboard, setDashboard] = useState<CourseDashboard | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [attempts, setAttempts] = useState<CourseQuizAttempt[]>([]);
  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);
  const [activeTab, setActiveTab] = useState<CourseTab>('overview');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [generatingReviewQuiz, setGeneratingReviewQuiz] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isTablet = useTabletLayout();

  const load = useCallback(async () => {
    try {
      setError(null);
      const [courseDashboard, docs, summaryList, cardList, quizList, attemptList, scheduleList] = await Promise.all([
        api.courseDashboard(id),
        api.courseDocuments(id),
        api.courseSummaries(id),
        api.courseFlashcards(id),
        api.courseQuizzes(id),
        api.courseAttempts(id),
        api.courseSchedule(id, false),
      ]);
      setDashboard(courseDashboard);
      setDocuments(docs);
      setSummaries(summaryList);
      setFlashcards(cardList);
      setQuizzes(quizList);
      setAttempts(attemptList);
      setSchedule(scheduleList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load this course');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  async function upload() {
    try {
      setUploading(true);
      setError(null);
      const result = await DocumentPicker.getDocumentAsync({
        type: ['text/plain', 'text/markdown', 'application/pdf'],
        copyToCacheDirectory: true,
      });
      if (result.canceled) {
        return;
      }
      const asset = result.assets[0];
      const document = await api.uploadDocument(id, {
        uri: asset.uri,
        name: asset.name,
        mimeType: asset.mimeType,
      });
      setDocuments((current) => [document, ...current.filter((item) => item.id !== document.id)]);
      setActiveTab('materials');
      router.push(`/documents/${document.id}?uploaded=1` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to add this source material');
    } finally {
      setUploading(false);
    }
  }

  async function generateReviewQuiz() {
    try {
      setGeneratingReviewQuiz(true);
      setError(null);
      const quiz = await api.createReviewQuiz(id, 5, 'medium');
      setQuizzes((current) => [quiz, ...current]);
      setActiveTab('practice');
      router.push(`/quiz/${quiz.id}` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create weak-area practice');
    } finally {
      setGeneratingReviewQuiz(false);
    }
  }

  function confirmDeleteCourse() {
    Alert.alert(
      'Delete course?',
      'This removes the course, source materials, review notes, flashcards, quizzes, and weak areas.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: deleteCourse },
      ],
    );
  }

  async function deleteCourse() {
    try {
      setDeleting(true);
      setError(null);
      await api.deleteCourse(id);
      router.replace('/courses');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete course');
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return <LoadingState message="Loading this course" />;
  }

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {uploading ? (
        <StatusBanner
          title="Adding source material"
          message="Keep StudyPilot open while this source material is added to your course."
        />
      ) : null}
      {generatingReviewQuiz ? (
        <StatusBanner
          title="Generating review quiz"
          message="StudyPilot is using your missed topics and course materials to create focused practice."
        />
      ) : null}
      {dashboard ? (
        <>
          <View style={styles.header}>
            <Text style={styles.title}>{dashboard.course.title}</Text>
            {dashboard.course.description ? <Text style={styles.subtitle}>{dashboard.course.description}</Text> : null}
          </View>

          <View style={styles.metrics}>
            <Text style={styles.metric}>{dashboard.document_count} sources</Text>
            <Text style={styles.metric}>{dashboard.summary_count} review notes</Text>
            <Text style={styles.metric}>{dashboard.quiz_count} practice sets</Text>
          </View>

          <View style={[styles.actions, isTablet && styles.tabletActions]}>
            <Button title={uploading ? 'Adding...' : 'Add Source Material'} disabled={uploading || deleting} onPress={upload} />
            <Button title={deleting ? 'Deleting...' : 'Delete Course'} disabled={uploading || deleting} variant="danger" onPress={confirmDeleteCourse} />
          </View>

          <View style={styles.tabs}>
            {COURSE_TABS.map((tab) => (
              <Pressable
                key={tab.key}
                accessibilityRole="button"
                onPress={() => setActiveTab(tab.key)}
                style={[styles.tab, activeTab === tab.key && styles.activeTab]}
              >
                <Text style={[styles.tabText, activeTab === tab.key && styles.activeTabText]}>{tab.label}</Text>
              </Pressable>
            ))}
          </View>

          {activeTab === 'overview' ? (
            <ResponsiveGrid minItemWidth={340}>
              <Section title="Next Deadlines">
                <ScheduleCards courseId={id} schedule={schedule.slice(0, 3)} />
              </Section>

              <Section title="Weak Areas">
                {dashboard.weak_topics.length ? (
                  dashboard.weak_topics.map((topic) => (
                    <Card key={topic.id}>
                      <Text style={styles.itemTitle}>{topic.topic}</Text>
                      <Text style={styles.itemMeta}>Missed {topic.miss_count} times - practice this next</Text>
                    </Card>
                  ))
                ) : (
                  <EmptyState title="No weak areas yet" message="Missed quiz questions will show what to review next." />
                )}
              </Section>
            </ResponsiveGrid>
          ) : null}

          {activeTab === 'materials' ? (
            <ResponsiveGrid minItemWidth={340}>
              <Section title="Source Materials">
                {documents.length ? (
                  documents.map((document) => (
                    <Link key={document.id} href={`/documents/${document.id}`} asChild>
                      <Card>
                        <Text style={styles.itemTitle}>{document.filename}</Text>
                        <Text style={styles.itemMeta}>
                          {sourceStatusLabel(document)}
                        </Text>
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
                  <EmptyState title="No source materials" message="Add lecture notes, markdown files, text files, or PDFs to start studying." />
                )}
              </Section>

              <Section title="Review Notes">
                {summaries.length ? (
                  summaries.map((summary) => (
                    <Link key={summary.id} href={`/summaries/${summary.id}` as Href} asChild>
                      <Card>
                        <Text style={styles.itemTitle}>{summary.title}</Text>
                        <Text style={styles.itemMeta}>
                          {summaryTypeLabel(summary.summary_type)} notes
                        </Text>
                      </Card>
                    </Link>
                  ))
                ) : (
                  <EmptyState title="No review notes" message="Open a source material and create review notes from it." />
                )}
              </Section>

              <Section title="Flashcards">
                {flashcards.length ? (
                  <Link href={`/flashcards/course/${id}` as Href} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>Review Flashcards</Text>
                      <Text style={styles.itemMeta}>{flashcards.length} cards ready for this course</Text>
                    </Card>
                  </Link>
                ) : (
                  <EmptyState title="No flashcards" message="Create flashcards from a source material for quick recall." />
                )}
              </Section>
            </ResponsiveGrid>
          ) : null}

          {activeTab === 'practice' ? (
            <ResponsiveGrid minItemWidth={340}>
              <View style={styles.section}>
                <Button
                  title={generatingReviewQuiz ? 'Creating Focus Quiz...' : 'Practice Weak Areas'}
                  disabled={generatingReviewQuiz || deleting || !dashboard.weak_topics.length || !documents.length}
                  onPress={generateReviewQuiz}
                />
              </View>
              <Section title="Practice Quizzes">
                {quizzes.length ? (
                  <Link href={`/quizzes/course/${id}` as Href} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>Open Practice Quizzes</Text>
                      <Text style={styles.itemMeta}>{quizzes.length} quizzes ready for this course</Text>
                    </Card>
                  </Link>
                ) : (
                  <EmptyState title="No practice quizzes" message="Open a source material and create a quiz when you are ready to test yourself." />
                )}
              </Section>

              <Section title="Practice History">
                {attempts.length ? (
                  <Link href={`/attempts/course/${id}` as Href} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>Review Scores</Text>
                      <Text style={styles.itemMeta}>{attempts.length} attempts saved for this course</Text>
                    </Card>
                  </Link>
                ) : (
                  <EmptyState title="No practice history" message="Quiz scores and missed topics appear after you submit answers." />
                )}
              </Section>
            </ResponsiveGrid>
          ) : null}

          {activeTab === 'schedule' ? (
            <>
              <Button title="Add New Deadline" variant="secondary" onPress={() => router.push(`/schedule/course/${id}` as Href)} />
              <Section title="Active Deadlines">
                <ScheduleCards courseId={id} schedule={schedule} />
              </Section>
            </>
          ) : null}
        </>
      ) : null}
    </ScreenScrollView>
  );
}

function ScheduleCards({ courseId, schedule }: { courseId: number; schedule: ScheduleItem[] }) {
  if (!schedule.length) {
    return <EmptyState title="No deadlines yet" message="Add assignments, exams, readings, or project milestones." />;
  }

  return (
    <>
      {schedule.map((item) => (
        <Link key={item.id} href={`/schedule/course/${courseId}` as Href} asChild>
          <Card>
            <Text style={styles.itemTitle}>{item.title}</Text>
            <Text style={styles.itemMeta}>
              {item.event_type} - {formatTimeRemaining(item.due_at, item.is_completed)}
            </Text>
            <Text style={styles.itemMeta}>{formatDateTime(item.due_at)}</Text>
          </Card>
        </Link>
      ))}
    </>
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

function sourceStatusLabel(document: Document): string {
  if (document.status === 'needs_ocr' || document.extraction_quality === 'poor') {
    return 'Needs text recognition before studying';
  }
  if (document.extraction_quality === 'partial') {
    return 'Partially readable - check source text first';
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
  return value;
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
    padding: 16,
  },
  header: {
    gap: 5,
  },
  title: {
    color: colors.text,
    fontSize: 25,
    fontWeight: '900',
  },
  subtitle: {
    color: colors.textMuted,
    lineHeight: 20,
  },
  metrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  actions: {
    gap: 10,
  },
  tabletActions: {
    flexDirection: 'row',
  },
  metric: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: 8,
    color: colors.text,
    fontWeight: '800',
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  tabs: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: 'row',
    padding: 4,
  },
  tab: {
    alignItems: 'center',
    borderRadius: 6,
    flex: 1,
    minHeight: 40,
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  activeTab: {
    backgroundColor: colors.surface,
  },
  tabText: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: '800',
  },
  activeTabText: {
    color: colors.text,
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
