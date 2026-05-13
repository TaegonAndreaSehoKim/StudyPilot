import { Link, router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useState } from 'react';
import { Alert, Linking, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { DocumentDetail, Flashcard, OcrJob, Quiz, Summary } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { FlashcardList } from '@/components/FlashcardList';
import { LoadingState } from '@/components/LoadingState';
import { ResponsiveGrid, ScreenScrollView, useTabletLayout } from '@/components/Screen';
import { StatusBanner } from '@/components/StatusBanner';
import { SummaryView } from '@/components/SummaryView';
import { colors } from '@/constants/colors';

type SummaryType = 'concise' | 'detailed' | 'exam';
type QuizDifficulty = 'easy' | 'medium' | 'hard' | 'mixed';

const SUMMARY_OPTIONS: { type: SummaryType; title: string; description: string }[] = [
  {
    type: 'concise',
    title: 'Concise',
    description: 'Core concepts and the broad flow of the material.',
  },
  {
    type: 'detailed',
    title: 'Detailed',
    description: 'General conceptual explanation, principles, and relationships over examples.',
  },
  {
    type: 'exam',
    title: 'Exam',
    description: 'Likely test points, similar-concept comparisons, and memorization anchors.',
  },
];

const QUIZ_COUNTS = [5, 10, 15];
const QUIZ_DIFFICULTIES: QuizDifficulty[] = ['mixed', 'easy', 'medium', 'hard'];
const OCR_POLL_ATTEMPTS = 80;
const OCR_POLL_INTERVAL_MS = 1500;

export default function DocumentDetailScreen() {
  const { documentId } = useLocalSearchParams<{ documentId: string }>();
  const id = Number(documentId);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [quizCount, setQuizCount] = useState(5);
  const [quizDifficulty, setQuizDifficulty] = useState<QuizDifficulty>('mixed');
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<{ title: string; message: string } | null>(null);
  const isTablet = useTabletLayout();

  const load = useCallback(async () => {
    try {
      setError(null);
      const [doc, summaryList, cardList, quizList] = await Promise.all([
        api.document(id),
        api.summaries(id),
        api.flashcards(id),
        api.documentQuizzes(id),
      ]);
      setDocument(doc);
      setSummaries(summaryList);
      setFlashcards(cardList);
      setQuizzes(quizList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load document');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  async function generateSummary(summaryType: SummaryType) {
    try {
      setWorking(summaryType);
      setError(null);
      setNotice(null);
      const summary = await api.createSummary(id, summaryType);
      setSummaries((current) => [summary, ...current]);
      setNotice({
        title: 'Summary saved',
        message: `${summary.title} is saved. Opening the full saved summary now.`,
      });
      router.push(`/summaries/${summary.id}` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to generate summary');
    } finally {
      setWorking(null);
    }
  }

  async function generateFlashcards() {
    try {
      setWorking('flashcards');
      setError(null);
      setNotice(null);
      const generatedFlashcards = await api.createFlashcards(id, 10);
      setFlashcards(generatedFlashcards);
      setNotice({
        title: 'Flashcards saved',
        message: `${generatedFlashcards.length} flashcards are saved. Review them here or from the course Materials tab.`,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to generate flashcards');
    } finally {
      setWorking(null);
    }
  }

  async function generateQuiz() {
    try {
      setWorking('quiz');
      setError(null);
      setNotice(null);
      const quiz = await api.createQuiz(id, quizCount, quizDifficulty);
      setQuizzes((current) => [quiz, ...current]);
      router.push(`/quiz/${quiz.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to generate quiz');
    } finally {
      setWorking(null);
    }
  }

  async function runOcr() {
    try {
      setWorking('ocr');
      setError(null);
      setNotice(null);
      const startedJob = await api.runDocumentOcr(id);
      const completedJob = await waitForOcrJob(startedJob);
      const refreshedDocument = await api.document(id);
      setDocument(refreshedDocument);
      setNotice({
        title: 'OCR completed',
        message: `StudyPilot extracted ${refreshedDocument.char_count} characters with ${refreshedDocument.extraction_method}. Job #${completedJob.id} is complete.`,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to run OCR');
    } finally {
      setWorking(null);
    }
  }

  async function waitForOcrJob(startedJob: OcrJob): Promise<OcrJob> {
    if (startedJob.status === 'completed') {
      return startedJob;
    }
    if (startedJob.status === 'failed') {
      throw new Error(startedJob.error_message || 'OCR failed');
    }

    for (let attempt = 0; attempt < OCR_POLL_ATTEMPTS; attempt += 1) {
      await delay(OCR_POLL_INTERVAL_MS);
      const job = await api.ocrJob(startedJob.id);
      if (job.status === 'completed') {
        return job;
      }
      if (job.status === 'failed') {
        throw new Error(job.error_message || 'OCR failed');
      }
    }
    throw new Error('OCR is still running. Pull to refresh this document in a moment.');
  }

  async function openOriginalFile() {
    try {
      setError(null);
      await Linking.openURL(await api.documentDownloadUrl(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to open original file');
    }
  }

  function confirmDeleteDocument() {
    Alert.alert(
      'Delete document?',
      'This removes the uploaded document and generated summaries, flashcards, quizzes, and attempts.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: deleteDocument },
      ],
    );
  }

  async function deleteDocument() {
    try {
      setDeleting(true);
      setError(null);
      await api.deleteDocument(id);
      if (document?.course_id) {
        router.replace(`/courses/${document.course_id}`);
      } else {
        router.replace('/courses');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete document');
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return <LoadingState message="Loading document" />;
  }

  const canGenerate = document?.status === 'extracted';
  const actionDisabled = !!working || deleting || !canGenerate;
  const canRunOcr = document?.file_type === '.pdf' && ['available', 'recommended', 'error', 'queued', 'running'].includes(document.ocr_status);

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {working ? (
        <StatusBanner
          title={working === 'ocr' ? 'Running OCR' : 'Generating study material'}
          message={
            working === 'ocr'
              ? 'StudyPilot is extracting text from scanned PDF pages. Keep the app open until OCR finishes.'
              : 'StudyPilot is using the extracted document text. The saved result will appear on this screen when generation finishes.'
          }
        />
      ) : null}
      {notice ? <StatusBanner title={notice.title} message={notice.message} variant="success" /> : null}
      {document ? (
        <>
          <View style={styles.header}>
            <Text style={styles.title}>{document.filename}</Text>
            <Text style={styles.subtitle}>
              {document.char_count} chars - {document.status}
              {document.page_count ? ` - ${document.extracted_page_count}/${document.page_count} pages with embedded text` : ''}
            </Text>
          </View>

          {document.ocr_status !== 'not_required' ? (
            <Card style={styles.ocrCard}>
              <Text style={styles.optionTitle}>
                {document.status === 'needs_ocr' ? 'OCR required' : 'OCR may improve this PDF'}
              </Text>
              <Text style={styles.optionDescription}>
                {document.extraction_notes ||
                  'Some pages have little or no embedded text. Scanned PDFs need OCR before StudyPilot can use the full material.'}
              </Text>
              {document.ocr_status === 'completed' ? (
                <Text style={styles.ocrDone}>OCR completed</Text>
              ) : canRunOcr ? (
                <Button
                  title={working === 'ocr' ? 'Running OCR...' : document.ocr_status === 'queued' || document.ocr_status === 'running' ? 'Check OCR Status' : 'Run OCR'}
                  disabled={!!working || deleting}
                  onPress={runOcr}
                />
              ) : null}
            </Card>
          ) : null}

          <Card>
            <Text style={styles.sectionTitle}>Extracted Text Preview</Text>
            <Text style={styles.previewMeta}>
              {document.preview_is_truncated
                ? `Showing first ${document.preview_char_count} of ${document.char_count} extracted chars. Generation uses the full extracted text.`
                : `Showing all ${document.char_count} extracted chars.`}
            </Text>
            <Text style={styles.preview}>{document.preview || 'No extracted text preview available.'}</Text>
          </Card>

          {!canGenerate ? (
            <EmptyState
              title="Generation unavailable"
              message="Study materials can only be generated after text is extracted. Run OCR if this is a scanned PDF."
            />
          ) : null}

          <View style={[styles.actions, isTablet && styles.tabletActions]}>
            <Button title="Open Full Extracted Text" variant="secondary" onPress={() => router.push(`/documents/${id}/text` as Href)} />
            <Button title="Open Original File" variant="secondary" onPress={openOriginalFile} />
            <Button title={deleting ? 'Deleting...' : 'Delete Document'} disabled={!!working || deleting} variant="danger" onPress={confirmDeleteDocument} />
          </View>

          <Section title="Generate Summaries">
            <ResponsiveGrid minItemWidth={280}>
              {SUMMARY_OPTIONS.map((option) => (
                <Card key={option.type}>
                  <Text style={styles.optionTitle}>{option.title} Summary</Text>
                  <Text style={styles.optionDescription}>{option.description}</Text>
                  <Button
                    title={working === option.type ? 'Generating...' : `Generate ${option.title}`}
                    disabled={actionDisabled}
                    variant={option.type === 'concise' ? 'primary' : 'secondary'}
                    onPress={() => generateSummary(option.type)}
                  />
                </Card>
              ))}
            </ResponsiveGrid>
          </Section>

          <Section title="Generate Practice">
            <ResponsiveGrid minItemWidth={320}>
              <Card>
                <Text style={styles.optionTitle}>Flashcards</Text>
                <Text style={styles.optionDescription}>Create quick recall cards from the document concepts.</Text>
                <Button title={working === 'flashcards' ? 'Generating...' : 'Generate Flashcards'} disabled={actionDisabled} variant="secondary" onPress={generateFlashcards} />
              </Card>

              <Card>
                <Text style={styles.optionTitle}>Quiz</Text>
                <Text style={styles.optionDescription}>Choose question count and difficulty before generating a quiz.</Text>
                <SegmentedControl
                  label="Questions"
                  options={QUIZ_COUNTS}
                  value={quizCount}
                  format={(value) => `${value}`}
                  onChange={setQuizCount}
                />
                <SegmentedControl
                  label="Difficulty"
                  options={QUIZ_DIFFICULTIES}
                  value={quizDifficulty}
                  format={(value) => value}
                  onChange={setQuizDifficulty}
                />
                <Button title={working === 'quiz' ? 'Generating...' : 'Generate Quiz'} disabled={actionDisabled} onPress={generateQuiz} />
              </Card>
            </ResponsiveGrid>
          </Section>

          <Section title="Latest Summary">
            {summaries.length ? (
              <>
                <SummaryView summary={summaries[0]} />
                <Button
                  title="Open Saved Summary"
                  variant="secondary"
                  onPress={() => router.push(`/summaries/${summaries[0].id}` as Href)}
                />
              </>
            ) : (
              <EmptyState title="No summary" message="Generate a summary from this document." />
            )}
          </Section>

          <Section title="Flashcards">
            {flashcards.length ? <FlashcardList flashcards={flashcards} /> : <EmptyState title="No flashcards" message="Generate flashcards for quick review." />}
          </Section>

          <Section title="Quizzes">
            {quizzes.length ? (
              quizzes.map((quiz) => (
                <Link key={quiz.id} href={`/quiz/${quiz.id}`} asChild>
                  <Card>
                    <Text style={styles.itemTitle}>{quiz.title}</Text>
                    <Text style={styles.itemMeta}>{quiz.questions.length} questions</Text>
                  </Card>
                </Link>
              ))
            ) : (
              <EmptyState title="No quizzes" message="Generate a quiz to test your understanding." />
            )}
          </Section>
        </>
      ) : null}
    </ScreenScrollView>
  );
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
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
    gap: 4,
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: '900',
  },
  subtitle: {
    color: colors.textMuted,
  },
  preview: {
    color: colors.text,
    lineHeight: 20,
  },
  previewMeta: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 8,
  },
  actions: {
    gap: 10,
  },
  tabletActions: {
    flexDirection: 'row',
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
  ocrCard: {
    backgroundColor: colors.warningSurface,
  },
  ocrDone: {
    color: colors.success,
    fontWeight: '900',
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
    backgroundColor: colors.surfaceMuted,
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
    backgroundColor: colors.surface,
  },
  segmentText: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: '800',
    textTransform: 'capitalize',
  },
  activeSegmentText: {
    color: colors.text,
  },
  section: {
    gap: 10,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 17,
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
