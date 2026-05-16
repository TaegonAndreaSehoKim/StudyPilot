import * as DocumentPicker from 'expo-document-picker';
import { Link, router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
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
  const [materialsLoading, setMaterialsLoading] = useState(false);
  const [practiceLoading, setPracticeLoading] = useState(false);
  const [materialsLoaded, setMaterialsLoaded] = useState(false);
  const [practiceLoaded, setPracticeLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isTablet = useTabletLayout();

  const load = useCallback(async () => {
    try {
      setError(null);
      const [courseDashboard, docs, scheduleList] = await Promise.all([
        api.courseDashboard(id),
        api.courseDocuments(id),
        api.courseSchedule(id, false),
      ]);
      setDashboard(courseDashboard);
      setDocuments(docs);
      setSchedule(scheduleList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load this course');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  const loadMaterials = useCallback(async () => {
    try {
      setMaterialsLoading(true);
      setError(null);
      const [summaryList, cardList] = await Promise.all([
        api.courseSummaries(id),
        api.courseFlashcards(id),
      ]);
      setSummaries(summaryList);
      setFlashcards(cardList);
      setMaterialsLoaded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load course library');
    } finally {
      setMaterialsLoading(false);
    }
  }, [id]);

  const loadPractice = useCallback(async () => {
    try {
      setPracticeLoading(true);
      setError(null);
      const [quizList, attemptList] = await Promise.all([
        api.courseQuizzes(id),
        api.courseAttempts(id),
      ]);
      setQuizzes(quizList);
      setAttempts(attemptList);
      setPracticeLoaded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load practice sets');
    } finally {
      setPracticeLoading(false);
    }
  }, [id]);

  useFocusEffect(useCallback(() => {
    void load();
    if (activeTab === 'materials') {
      void loadMaterials();
    }
    if (activeTab === 'practice') {
      void loadPractice();
    }
  }, [activeTab, load, loadMaterials, loadPractice]));

  useEffect(() => {
    if (activeTab === 'materials' && !materialsLoaded && !materialsLoading) {
      void loadMaterials();
    }
    if (activeTab === 'practice' && !practiceLoaded && !practiceLoading) {
      void loadPractice();
    }
  }, [activeTab, loadMaterials, loadPractice, materialsLoaded, materialsLoading, practiceLoaded, practiceLoading]);

  async function refreshCourse() {
    setRefreshing(true);
    await load();
    if (activeTab === 'materials') {
      await loadMaterials();
    }
    if (activeTab === 'practice') {
      await loadPractice();
    }
  }

  function openTab(tab: CourseTab) {
    setActiveTab(tab);
  }

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
      setMaterialsLoaded(false);
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
      setPracticeLoaded(true);
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
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refreshCourse} />}
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
            <MetricButton label="sources" value={dashboard.document_count} onPress={() => openTab('materials')} />
            <MetricButton label="review notes" value={dashboard.summary_count} onPress={() => openTab('materials')} />
            <MetricButton label="practice sets" value={dashboard.quiz_count} onPress={() => openTab('practice')} />
          </View>

          <View style={styles.tabs}>
            {COURSE_TABS.map((tab) => (
              <Pressable
                key={tab.key}
                accessibilityRole="button"
                onPress={() => openTab(tab.key)}
                style={[styles.tab, activeTab === tab.key && styles.activeTab]}
              >
                <Text style={[styles.tabText, activeTab === tab.key && styles.activeTabText]}>{tab.label}</Text>
              </Pressable>
            ))}
          </View>

          {activeTab === 'overview' ? (
            <>
              <Card style={styles.todayCard}>
                <Text style={styles.todayEyebrow}>Today</Text>
                <Text style={styles.todayTitle}>{todayHeadline(schedule[0], dashboard.weak_topics[0]?.topic)}</Text>
                <Text style={styles.itemMeta}>{courseReadinessSummary(documents, dashboard.summary_count, dashboard.quiz_count)}</Text>
                <View style={[styles.actions, isTablet && styles.tabletActions]}>
                  <Button title="Start Study Session" onPress={() => router.push(`/study/course/${id}` as Href)} />
                  <Button title={uploading ? 'Adding...' : 'Add Source'} disabled={uploading || deleting} variant="secondary" onPress={upload} />
                  {schedule.length ? (
                    <Button title="View Deadlines" variant="secondary" onPress={() => openTab('schedule')} />
                  ) : null}
                </View>
              </Card>

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

                <Section title="Source Readiness">
                  <Card>
                    <Text style={styles.itemTitle}>{sourceReadinessHeadline(documents)}</Text>
                    <Text style={styles.itemMeta}>{sourceReadinessDetail(documents)}</Text>
                    <Button title="Open Library" variant="secondary" onPress={() => openTab('materials')} />
                  </Card>
                </Section>
              </ResponsiveGrid>
            </>
          ) : null}

          {activeTab === 'materials' ? (
            materialsLoading && !materialsLoaded ? (
              <LoadingState message="Loading course library" />
            ) : (
              <ResponsiveGrid minItemWidth={340}>
                <View style={styles.section}>
                  <Button title={uploading ? 'Adding...' : 'Add Source Material'} disabled={uploading || deleting} onPress={upload} />
                </View>
                <Section title="Source Materials">
                  {documents.length ? (
                    documents.map((document) => (
                      <Link key={document.id} href={`/documents/${document.id}`} asChild>
                        <Card>
                          <Text style={styles.itemTitle}>{document.filename}</Text>
                          <Text style={styles.qualityPill}>{sourceQualityLabel(document)}</Text>
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
            )
          ) : null}

          {activeTab === 'practice' ? (
            practiceLoading && !practiceLoaded ? (
              <LoadingState message="Loading practice sets" />
            ) : (
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
            )
          ) : null}

          {activeTab === 'schedule' ? (
            <>
              <Button title="Add New Deadline" variant="secondary" onPress={() => router.push(`/schedule/course/${id}` as Href)} />
              <Section title="Active Deadlines">
                <ScheduleCards courseId={id} schedule={schedule} />
              </Section>
            </>
          ) : null}

          <Section title="Course Management">
            <Card>
              <Text style={styles.itemTitle}>Course Settings</Text>
              <Text style={styles.itemMeta}>Delete this course only when you no longer need its sources, notes, quizzes, attempts, and deadlines.</Text>
              <Button title={deleting ? 'Deleting...' : 'Delete Course'} disabled={uploading || deleting} variant="danger" onPress={confirmDeleteCourse} />
            </Card>
          </Section>
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

function MetricButton({ label, value, onPress }: { label: string; value: number; onPress: () => void }) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={styles.metric}>
      <Text style={styles.metricText}>{value} {label}</Text>
    </Pressable>
  );
}

function todayHeadline(deadline: ScheduleItem | undefined, weakTopic: string | undefined): string {
  if (deadline) {
    return `${formatTimeRemaining(deadline.due_at, deadline.is_completed)}: ${deadline.title}`;
  }
  if (weakTopic) {
    return `Review weak area: ${weakTopic}`;
  }
  return 'Keep the course moving';
}

function courseReadinessSummary(documents: Document[], summaryCount: number, quizCount: number): string {
  const readable = documents.filter((document) => document.status === 'extracted').length;
  if (!documents.length) {
    return 'Add a source first, then create notes and practice.';
  }
  if (!readable) {
    return 'Your sources need readable text before StudyPilot can create reliable study tools.';
  }
  if (!summaryCount) {
    return 'Readable sources are ready. Create review notes before starting a study session.';
  }
  if (!quizCount) {
    return 'Review notes are ready. Add a practice quiz to test understanding.';
  }
  return 'Sources, notes, and practice are ready for a focused study pass.';
}

function sourceReadinessHeadline(documents: Document[]): string {
  const attention = documents.filter((document) => document.status === 'needs_ocr' || document.extraction_quality === 'partial' || document.extraction_quality === 'poor').length;
  if (!documents.length) {
    return 'No sources yet';
  }
  if (attention) {
    return `${attention} source${attention === 1 ? '' : 's'} need attention`;
  }
  return 'Sources are ready';
}

function sourceReadinessDetail(documents: Document[]): string {
  const readable = documents.filter((document) => document.status === 'extracted').length;
  if (!documents.length) {
    return 'Add lecture notes, PDFs, or markdown files to begin.';
  }
  const attention = documents.filter((document) => document.status === 'needs_ocr' || document.extraction_quality === 'partial' || document.extraction_quality === 'poor').length;
  if (attention) {
    return `${readable} readable, ${attention} may need OCR or source review before generation.`;
  }
  return `${readable} readable source${readable === 1 ? '' : 's'} available for review notes and practice.`;
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

function sourceQualityLabel(document: Document): string {
  if (document.ocr_status === 'completed') {
    return 'OCR complete';
  }
  if (document.status === 'needs_ocr' || document.extraction_quality === 'poor') {
    return 'Needs OCR';
  }
  if (document.extraction_quality === 'partial') {
    return `${Math.round(document.extraction_coverage * 100)}% readable`;
  }
  return 'Ready';
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
    minHeight: 36,
    justifyContent: 'center',
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  metricText: {
    color: colors.text,
    fontWeight: '800',
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
  todayCard: {
    backgroundColor: colors.surface,
    borderColor: colors.primary,
  },
  todayEyebrow: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  todayTitle: {
    color: colors.text,
    fontSize: 21,
    fontWeight: '900',
    lineHeight: 27,
  },
  qualityPill: {
    alignSelf: 'flex-start',
    backgroundColor: colors.surfaceMuted,
    borderRadius: 8,
    color: colors.text,
    fontSize: 12,
    fontWeight: '900',
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
});
