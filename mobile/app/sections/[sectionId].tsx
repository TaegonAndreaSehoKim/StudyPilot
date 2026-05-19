import * as DocumentPicker from 'expo-document-picker';
import { Link, router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useState } from 'react';
import { Alert, Pressable, RefreshControl, StyleSheet, Text, TextInput, View } from 'react-native';

import { api } from '@/api/client';
import type { CourseSection, Document, Quiz, StudyNoteType, Summary } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { ResponsiveGrid, ScreenScrollView, useTabletLayout } from '@/components/Screen';
import { StatusBanner } from '@/components/StatusBanner';
import { colors } from '@/constants/colors';

type SummaryType = Exclude<StudyNoteType, 'explanation'>;
type QuizDifficulty = 'easy' | 'medium' | 'hard' | 'mixed';

const SUMMARY_OPTIONS: { type: SummaryType; title: string }[] = [
  { type: 'concise', title: 'Quick Review' },
  { type: 'detailed', title: 'Deep Review' },
  { type: 'exam', title: 'Exam Prep' },
];

const QUIZ_COUNTS = [5, 10, 15];
const QUIZ_DIFFICULTIES: QuizDifficulty[] = ['mixed', 'easy', 'medium', 'hard'];

export default function SectionDetailScreen() {
  const { sectionId } = useLocalSearchParams<{ sectionId: string }>();
  const id = Number(sectionId);
  const [section, setSection] = useState<CourseSection | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [working, setWorking] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [quizCount, setQuizCount] = useState(5);
  const [quizDifficulty, setQuizDifficulty] = useState<QuizDifficulty>('mixed');
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const isTablet = useTabletLayout();

  const load = useCallback(async () => {
    try {
      setError(null);
      const [sectionDetail, docs, summaryList, quizList] = await Promise.all([
        api.section(id),
        api.sectionDocuments(id),
        api.sectionSummaries(id),
        api.sectionQuizzes(id),
      ]);
      setSection(sectionDetail);
      setDocuments(docs);
      setSummaries(summaryList);
      setQuizzes(quizList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load this study section');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  function startEditing() {
    if (!section) {
      return;
    }
    setEditTitle(section.title);
    setEditDescription(section.description || '');
    setEditing(true);
    setNotice(null);
    setError(null);
  }

  async function saveSection() {
    if (!section) {
      return;
    }
    if (!editTitle.trim()) {
      setError('Section name is required.');
      return;
    }
    try {
      setSaving(true);
      setError(null);
      const updated = await api.updateSection(section.id, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
      });
      setSection(updated);
      setEditing(false);
      setNotice('Section details updated.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update section');
    } finally {
      setSaving(false);
    }
  }

  async function upload() {
    if (!section) {
      return;
    }
    try {
      setWorking('upload');
      setError(null);
      setNotice(null);
      const result = await DocumentPicker.getDocumentAsync({
        type: ['text/plain', 'text/markdown', 'application/pdf'],
        copyToCacheDirectory: true,
      });
      if (result.canceled) {
        return;
      }
      const asset = result.assets[0];
      const document = await api.uploadDocument(
        section.course_id,
        { uri: asset.uri, name: asset.name, mimeType: asset.mimeType },
        section.id,
      );
      setDocuments((current) => [document, ...current.filter((item) => item.id !== document.id)]);
      setSection((current) => current ? { ...current, document_count: current.document_count + 1 } : current);
      setNotice('Source material added to this section.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to add this source material');
    } finally {
      setWorking(null);
    }
  }

  async function generateSummary(summaryType: SummaryType) {
    try {
      setWorking(summaryType);
      setError(null);
      setNotice(null);
      const summary = await api.createSectionSummary(id, summaryType);
      setSummaries((current) => [summary, ...current]);
      setSection((current) => current ? { ...current, summary_count: current.summary_count + 1 } : current);
      router.push(`/summaries/${summary.id}` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create section review notes');
    } finally {
      setWorking(null);
    }
  }

  async function generateExplanation() {
    try {
      setWorking('explanation');
      setError(null);
      setNotice(null);
      const summary = await api.createSectionExplanation(id);
      setSummaries((current) => [summary, ...current]);
      setSection((current) => current ? { ...current, summary_count: current.summary_count + 1 } : current);
      router.push(`/summaries/${summary.id}` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create section explanation');
    } finally {
      setWorking(null);
    }
  }

  async function generateQuiz() {
    try {
      setWorking('quiz');
      setError(null);
      setNotice(null);
      const quiz = await api.createSectionQuiz(id, quizCount, quizDifficulty);
      setQuizzes((current) => [quiz, ...current]);
      setSection((current) => current ? { ...current, quiz_count: current.quiz_count + 1 } : current);
      router.push(`/quiz/${quiz.id}` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create section practice quiz');
    } finally {
      setWorking(null);
    }
  }

  function confirmDeleteSection() {
    Alert.alert(
      'Delete section?',
      'This removes section-level notes and quizzes. Source materials stay in the course library.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: deleteSection },
      ],
    );
  }

  async function deleteSection() {
    if (!section) {
      return;
    }
    try {
      setDeleting(true);
      setError(null);
      await api.deleteSection(section.id);
      router.replace(`/courses/${section.course_id}` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete section');
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return <LoadingState message="Loading study section" />;
  }

  const canGenerate = documents.some((document) => document.status === 'extracted');
  const actionDisabled = !!working || deleting || !canGenerate;

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {working ? <StatusBanner title={workingTitle(working)} message={workingMessage(working)} /> : null}
      {notice ? <StatusBanner title="Section updated" message={notice} variant="success" /> : null}
      {section ? (
        <>
          <View style={styles.header}>
            <View style={styles.headerTopRow}>
              <View style={styles.headerTextBlock}>
                <Text style={styles.title}>{section.title}</Text>
                {section.description ? <Text style={styles.subtitle}>{section.description}</Text> : null}
              </View>
              <Pressable accessibilityRole="button" onPress={startEditing} style={styles.editButton}>
                <Text style={styles.editButtonText}>Edit</Text>
              </Pressable>
            </View>
          </View>

          {editing ? (
            <Card style={styles.editCard}>
              <Text style={styles.sectionTitle}>Edit Section</Text>
              <Text style={styles.inputLabel}>Name</Text>
              <TextInput
                value={editTitle}
                onChangeText={setEditTitle}
                placeholder="Section name"
                placeholderTextColor={colors.textFaint}
                style={styles.input}
              />
              <Text style={styles.inputLabel}>Description</Text>
              <TextInput
                value={editDescription}
                onChangeText={setEditDescription}
                placeholder="Scope, topics, or exam coverage"
                placeholderTextColor={colors.textFaint}
                multiline
                style={[styles.input, styles.descriptionInput]}
              />
              <View style={[styles.actions, isTablet && styles.tabletActions]}>
                <Button title={saving ? 'Saving...' : 'Save Changes'} disabled={saving} onPress={saveSection} />
                <Button title="Cancel" variant="secondary" disabled={saving} onPress={() => setEditing(false)} />
              </View>
            </Card>
          ) : null}

          <View style={styles.metrics}>
            <Metric label="sources" value={documents.length} />
            <Metric label="review notes" value={summaries.length} />
            <Metric label="practice sets" value={quizzes.length} />
          </View>

          <Card style={styles.startCard}>
            <Text style={styles.sectionTitle}>Section Workflow</Text>
            <Text style={styles.optionDescription}>
              Add every source that belongs to this scope, then generate review notes or a quiz from the combined material.
            </Text>
            <View style={[styles.actions, isTablet && styles.tabletActions]}>
              <Button title={working === 'upload' ? 'Adding...' : 'Add Source'} disabled={!!working || deleting} onPress={upload} />
              <Button title="Back to Course" variant="secondary" onPress={() => router.push(`/courses/${section.course_id}` as Href)} />
            </View>
          </Card>

          {!canGenerate ? (
            <EmptyState title="No readable sources yet" message="Add extracted text, markdown, or readable PDFs before generating section-level study tools." />
          ) : null}

          <Section title="Create Section Review Notes">
            <ResponsiveGrid minItemWidth={280}>
              <Card style={styles.explanationCard}>
                <Text style={styles.optionTitle}>Additional Explanation</Text>
                <Text style={styles.optionDescription}>Create a slower, richer teaching guide from all readable sources in this section.</Text>
                <Button
                  title={working === 'explanation' ? 'Explaining...' : 'Create Explanation'}
                  disabled={actionDisabled}
                  onPress={generateExplanation}
                />
              </Card>
              {SUMMARY_OPTIONS.map((option) => (
                <Card key={option.type}>
                  <Text style={styles.optionTitle}>{option.title}</Text>
                  <Text style={styles.optionDescription}>Generate notes from all readable sources in this section.</Text>
                  <Button
                    title={working === option.type ? 'Creating...' : `Create ${option.title}`}
                    disabled={actionDisabled}
                    variant={option.type === 'concise' ? 'primary' : 'secondary'}
                    onPress={() => generateSummary(option.type)}
                  />
                </Card>
              ))}
            </ResponsiveGrid>
          </Section>

          <Section title="Create Section Practice">
            <Card>
              <Text style={styles.optionTitle}>Practice Quiz</Text>
              <Text style={styles.optionDescription}>Questions are generated from the combined section source set.</Text>
              <SegmentedControl label="Questions" options={QUIZ_COUNTS} value={quizCount} format={(value) => `${value}`} onChange={setQuizCount} />
              <SegmentedControl label="Difficulty" options={QUIZ_DIFFICULTIES} value={quizDifficulty} format={(value) => value} onChange={setQuizDifficulty} />
              <Button title={working === 'quiz' ? 'Creating...' : 'Create Quiz'} disabled={actionDisabled} onPress={generateQuiz} />
            </Card>
          </Section>

          <ResponsiveGrid minItemWidth={340}>
            <Section title="Section Sources">
              {documents.length ? (
                documents.map((document) => (
                  <Link key={document.id} href={`/documents/${document.id}` as Href} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>{document.filename}</Text>
                      <Text style={styles.itemMeta}>{sourceStatusLabel(document)}</Text>
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No section sources" message="Add lecture notes, files, or PDFs that match this section scope." />
              )}
            </Section>

            <Section title="Review Notes">
              {summaries.length ? (
                summaries.map((summary) => (
                  <Link key={summary.id} href={`/summaries/${summary.id}` as Href} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>{summary.title}</Text>
                      <Text style={styles.itemMeta}>{summaryTypeLabel(summary.summary_type)} notes</Text>
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No section notes" message="Create notes after adding readable section sources." />
              )}
            </Section>

            <Section title="Practice Quizzes">
              {quizzes.length ? (
                quizzes.map((quiz) => (
                  <Link key={quiz.id} href={`/quiz/${quiz.id}` as Href} asChild>
                    <Card>
                      <Text style={styles.itemTitle}>{quiz.title}</Text>
                      <Text style={styles.itemMeta}>{quiz.questions.length} questions</Text>
                    </Card>
                  </Link>
                ))
              ) : (
                <EmptyState title="No section quizzes" message="Create a quiz from this section when the source set is ready." />
              )}
            </Section>
          </ResponsiveGrid>

          <Section title="Section Management">
            <Card>
              <Text style={styles.itemTitle}>Delete Section</Text>
              <Text style={styles.itemMeta}>Source materials stay in the course library, but section-level notes and quizzes are removed.</Text>
              <Button title={deleting ? 'Deleting...' : 'Delete Section'} disabled={!!working || deleting} variant="danger" onPress={confirmDeleteSection} />
            </Card>
          </Section>
        </>
      ) : null}
    </ScreenScrollView>
  );
}

function workingTitle(working: string): string {
  if (working === 'upload') {
    return 'Adding source material';
  }
  if (working === 'quiz') {
    return 'Creating section quiz';
  }
  if (working === 'explanation') {
    return 'Writing section explanation';
  }
  return 'Writing section notes';
}

function workingMessage(working: string): string {
  if (working === 'upload') {
    return 'Saving this source inside the section scope.';
  }
  if (working === 'quiz') {
    return 'Combining section sources and writing practice questions.';
  }
  if (working === 'explanation') {
    return 'Expanding section sources into a slower teaching guide.';
  }
  return 'Combining section sources into review notes.';
}

function sourceStatusLabel(document: Document): string {
  if (document.status === 'needs_ocr' || document.extraction_quality === 'poor') {
    return 'Needs OCR before reliable generation';
  }
  if (document.extraction_quality === 'partial') {
    return 'Partially readable';
  }
  return 'Ready for section generation';
}

function summaryTypeLabel(value: string): string {
  if (value === 'concise') {
    return 'Quick Review';
  }
  if (value === 'detailed') {
    return 'Deep Review';
  }
  if (value === 'exam') {
    return 'Exam Prep';
  }
  if (value === 'explanation') {
    return 'Additional Explanation';
  }
  return value;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricText}>{value} {label}</Text>
    </View>
  );
}

function SegmentedControl<T extends string | number>({
  label,
  options,
  value,
  format,
  onChange,
}: {
  label: string;
  options: T[];
  value: T;
  format: (value: T) => string;
  onChange: (value: T) => void;
}) {
  return (
    <View style={styles.segmentGroup}>
      <Text style={styles.segmentLabel}>{label}</Text>
      <View style={styles.segmented}>
        {options.map((option) => {
          const active = option === value;
          return (
            <Pressable
              key={String(option)}
              accessibilityRole="button"
              onPress={() => onChange(option)}
              style={[styles.segment, active && styles.activeSegment]}
            >
              <Text style={[styles.segmentText, active && styles.activeSegmentText]}>{format(option)}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
    padding: 16,
  },
  header: {
    gap: 6,
  },
  headerTopRow: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    gap: 12,
    justifyContent: 'space-between',
  },
  headerTextBlock: {
    flex: 1,
    minWidth: 0,
  },
  title: {
    color: colors.text,
    fontSize: 27,
    fontWeight: '900',
    lineHeight: 33,
  },
  subtitle: {
    color: colors.textMuted,
    lineHeight: 20,
  },
  editButton: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    minHeight: 38,
    justifyContent: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  editButtonText: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '900',
  },
  editCard: {
    backgroundColor: colors.surfaceSubtle,
  },
  explanationCard: {
    backgroundColor: colors.primarySurface,
    borderColor: colors.primary,
  },
  startCard: {
    backgroundColor: colors.primarySurface,
    borderColor: colors.primary,
  },
  inputLabel: {
    color: colors.text,
    fontSize: 13,
    fontWeight: '800',
  },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.text,
    fontSize: 15,
    minHeight: 44,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  descriptionInput: {
    minHeight: 82,
    textAlignVertical: 'top',
  },
  actions: {
    gap: 10,
  },
  tabletActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  metrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  metric: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    minHeight: 36,
    justifyContent: 'center',
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  metricText: {
    color: colors.text,
    fontWeight: '800',
  },
  section: {
    gap: 10,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '800',
  },
  optionTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '900',
  },
  optionDescription: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 20,
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
  segmentGroup: {
    gap: 8,
  },
  segmentLabel: {
    color: colors.text,
    fontSize: 13,
    fontWeight: '800',
  },
  segmented: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: 'row',
    padding: 4,
  },
  segment: {
    alignItems: 'center',
    borderRadius: 6,
    flex: 1,
    minHeight: 38,
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  activeSegment: {
    backgroundColor: colors.primarySurface,
  },
  segmentText: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: '800',
    textTransform: 'capitalize',
  },
  activeSegmentText: {
    color: colors.primary,
  },
});
