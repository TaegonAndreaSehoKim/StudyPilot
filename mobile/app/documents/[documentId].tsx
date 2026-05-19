import { Link, router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Alert, Linking, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { DocumentDetail, Flashcard, OcrJob, Quiz, StudyNoteType, Summary } from '@/api/types';
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

type SummaryType = Exclude<StudyNoteType, 'explanation'>;
type QuizDifficulty = 'easy' | 'medium' | 'hard' | 'mixed';

const SUMMARY_OPTIONS: { type: SummaryType; title: string; description: string }[] = [
  {
    type: 'concise',
    title: 'Quick Review',
    description: 'Core concepts and the broad flow of the material.',
  },
  {
    type: 'detailed',
    title: 'Deep Review',
    description: 'Concepts, principles, and relationships with less focus on examples.',
  },
  {
    type: 'exam',
    title: 'Exam Prep',
    description: 'Likely test points, similar-concept comparisons, and memorization anchors.',
  },
];

const QUIZ_COUNTS = [5, 10, 15];
const QUIZ_DIFFICULTIES: QuizDifficulty[] = ['mixed', 'easy', 'medium', 'hard'];
const OCR_POLL_ATTEMPTS = 80;
const OCR_POLL_INTERVAL_MS = 1500;

export default function DocumentDetailScreen() {
  const { documentId, uploaded } = useLocalSearchParams<{ documentId: string; uploaded?: string }>();
  const id = Number(documentId);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [workingStep, setWorkingStep] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [quizCount, setQuizCount] = useState(5);
  const [quizDifficulty, setQuizDifficulty] = useState<QuizDifficulty>('mixed');
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<{ title: string; message: string } | null>(null);
  const [sourcePreviewExpanded, setSourcePreviewExpanded] = useState(false);
  const showedUploadNotice = useRef(false);
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
      if (uploaded === '1' && !showedUploadNotice.current) {
        showedUploadNotice.current = true;
        setNotice({
          title: doc.status === 'needs_ocr' ? 'This PDF needs text recognition' : 'Source material added',
          message:
            doc.status === 'needs_ocr'
              ? 'The file is saved, but StudyPilot needs to recognize the text before it can create review notes or practice.'
              : 'StudyPilot can now use this source to create review notes, flashcards, and practice quizzes.',
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load this source material');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  useEffect(() => {
    if (!working) {
      setWorkingStep(0);
      return undefined;
    }
    const interval = setInterval(() => {
      setWorkingStep((current) => current + 1);
    }, 2600);
    return () => clearInterval(interval);
  }, [working]);

  async function generateSummary(summaryType: SummaryType) {
    try {
      setWorking(summaryType);
      setError(null);
      setNotice(null);
      const summary = await api.createSummary(id, summaryType);
      setSummaries((current) => [summary, ...current]);
      setNotice({
        title: 'Review notes saved',
        message: `${summary.title} is saved. Opening the full notes now.`,
      });
      router.push(`/summaries/${summary.id}` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create review notes');
    } finally {
      setWorking(null);
    }
  }

  async function generateExplanation() {
    try {
      setWorking('explanation');
      setError(null);
      setNotice(null);
      const summary = await api.createExplanation(id);
      setSummaries((current) => [summary, ...current]);
      setNotice({
        title: 'Additional explanation saved',
        message: `${summary.title} is saved. Opening the full explanation now.`,
      });
      router.push(`/summaries/${summary.id}` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create additional explanation');
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
        message: `${generatedFlashcards.length} flashcards are ready. You can review them here or from the course library.`,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create flashcards');
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
      setError(err instanceof Error ? err.message : 'Unable to create a practice quiz');
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
        title: 'Text recognition completed',
        message: `StudyPilot can now use more of this PDF for review notes and practice. Job #${completedJob.id} is complete.`,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to recognize text in this file');
    } finally {
      setWorking(null);
    }
  }

  async function waitForOcrJob(startedJob: OcrJob): Promise<OcrJob> {
    if (startedJob.status === 'completed') {
      return startedJob;
    }
    if (startedJob.status === 'failed') {
      throw new Error(startedJob.error_message || 'Text recognition failed');
    }

    for (let attempt = 0; attempt < OCR_POLL_ATTEMPTS; attempt += 1) {
      await delay(OCR_POLL_INTERVAL_MS);
      const job = await api.ocrJob(startedJob.id);
      if (job.status === 'completed') {
        return job;
      }
      if (job.status === 'failed') {
        throw new Error(job.error_message || 'Text recognition failed');
      }
    }
    throw new Error('Text recognition is still running. Pull to refresh this source in a moment.');
  }

  async function openOriginalFile() {
    try {
      setError(null);
      await Linking.openURL(await api.documentDownloadUrl(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to open the original file');
    }
  }

  function confirmDeleteDocument() {
    Alert.alert(
      'Delete document?',
      'This removes the source material and the review notes, flashcards, quizzes, and attempts created from it.',
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
      setError(err instanceof Error ? err.message : 'Unable to delete this source material');
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return <LoadingState message="Loading source material" />;
  }

  const canGenerate = document?.status === 'extracted';
  const actionDisabled = !!working || deleting || !canGenerate;
  const canRunOcr = document?.file_type === '.pdf' && ['available', 'recommended', 'error', 'queued', 'running'].includes(document.ocr_status);
  const sourcePreview = document?.preview || '';
  const collapsedPreviewLimit = 900;
  const canExpandPreview = sourcePreview.length > collapsedPreviewLimit || !!document?.preview_is_truncated;
  const shownPreview =
    !sourcePreview || sourcePreviewExpanded || !canExpandPreview
      ? sourcePreview
      : `${sourcePreview.slice(0, collapsedPreviewLimit).trimEnd()}...`;

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {working ? (
        <StatusBanner
          title={workingTitle(working)}
          message={workingMessage(working, workingStep)}
        />
      ) : null}
      {notice ? <StatusBanner title={notice.title} message={notice.message} variant="success" /> : null}
      {document ? (
        <>
          <View style={styles.header}>
            <Text style={styles.title}>{document.filename}</Text>
            <Text style={styles.subtitle}>{sourceReadinessLabel(document)}</Text>
          </View>

          <Card style={styles.startCard}>
            <Text style={styles.sectionTitle}>Next Step</Text>
            <Text style={styles.optionDescription}>
              {nextSourceActionMessage(document)}
            </Text>
            <View style={[styles.actions, isTablet && styles.tabletActions]}>
              {canRunOcr && !canGenerate ? (
                <Button
                  title={working === 'ocr' ? 'Recognizing...' : 'Recognize Text'}
                  disabled={!!working || deleting}
                  onPress={runOcr}
                />
              ) : (
                <Button
                  title={working === 'concise' ? 'Creating...' : 'Create Quick Review'}
                  disabled={actionDisabled}
                  onPress={() => generateSummary('concise')}
                />
              )}
              <Button title="Read Full Source" variant="secondary" onPress={() => router.push(`/documents/${id}/text` as Href)} />
              <Button title="Open Original File" variant="secondary" onPress={openOriginalFile} />
            </View>
            <View style={styles.savedStrip}>
              <SavedCount label="Notes" value={summaries.length} />
              <SavedCount label="Cards" value={flashcards.length} />
              <SavedCount label="Quizzes" value={quizzes.length} />
            </View>
          </Card>

          <ExtractionQualityCard document={document} />

          {document.ocr_status !== 'not_required' ? (
            <Card style={styles.ocrCard}>
              <Text style={styles.optionTitle}>
                {document.status === 'needs_ocr' ? 'Text recognition needed' : document.ocr_status === 'completed' ? 'Text recognition complete' : 'Text recognition recommended'}
              </Text>
              <Text style={styles.qualityText}>
                StudyPilot can read {Math.round(document.extraction_coverage * 100)}% of this PDF right now.
              </Text>
              <Text style={styles.optionDescription}>
                {document.extraction_notes ||
                  'Some pages have little or no selectable text. Run text recognition so StudyPilot can use the full material.'}
              </Text>
              {document.ocr_status === 'completed' ? (
                <Text style={styles.ocrDone}>Ready to study</Text>
              ) : canRunOcr ? (
                <Button
                  title={working === 'ocr' ? 'Recognizing...' : document.ocr_status === 'queued' || document.ocr_status === 'running' ? 'Check Progress' : 'Recognize Text'}
                  disabled={!!working || deleting}
                  onPress={runOcr}
                />
              ) : null}
            </Card>
          ) : null}

          <Card>
            <Text style={styles.sectionTitle}>Source Preview</Text>
            <Text style={styles.previewMeta}>
              {sourcePreviewExpanded
                ? 'Expanded preview. Use Full Source for the complete extracted text.'
                : 'A short preview is shown here so the study tools stay easy to reach.'}
            </Text>
            <Text style={styles.preview}>{shownPreview || 'No readable text is available yet.'}</Text>
            {canExpandPreview ? (
              <Pressable
                accessibilityRole="button"
                onPress={() => setSourcePreviewExpanded((current) => !current)}
                style={styles.previewToggle}
              >
                <Text style={styles.previewToggleText}>
                  {sourcePreviewExpanded ? 'Show Less ^' : 'Show More v'}
                </Text>
              </Pressable>
            ) : null}
          </Card>

          {!canGenerate ? (
            <EmptyState
              title="Study tools are not ready yet"
              message="Run text recognition if this is a scanned PDF, then create review notes or practice."
            />
          ) : null}

          <Section title="Generate Study Tools">
            <Card>
              <View style={styles.toolHeader}>
                <Text style={styles.toolEyebrow}>From this source</Text>
                <Text style={styles.optionDescription}>
                  Choose one output type. Notes and explanations open after they are saved; practice tools stay in this source library.
                </Text>
              </View>
              <View style={[styles.toolGrid, isTablet && styles.tabletToolGrid]}>
                <ToolAction
                  title="Additional Explanation"
                  description="Use this when the lecture is hard to understand and needs slower teaching."
                  buttonTitle={working === 'explanation' ? 'Explaining...' : 'Create Explanation'}
                  disabled={actionDisabled}
                  highlight
                  onPress={generateExplanation}
                />
                {SUMMARY_OPTIONS.map((option) => (
                  <ToolAction
                    key={option.type}
                    title={option.title}
                    description={option.description}
                    buttonTitle={working === option.type ? 'Creating...' : `Create ${option.title}`}
                    disabled={actionDisabled}
                    variant={option.type === 'concise' ? 'primary' : 'secondary'}
                    onPress={() => generateSummary(option.type)}
                  />
                ))}
                <ToolAction
                  title="Flashcards"
                  description="Create quick recall cards from the document concepts."
                  buttonTitle={working === 'flashcards' ? 'Creating...' : 'Create Flashcards'}
                  disabled={actionDisabled}
                  variant="secondary"
                  onPress={generateFlashcards}
                />
                <ToolAction
                  title="Practice Quiz"
                  description="Generate a multiple-choice quiz with the selected count and difficulty."
                  buttonTitle={working === 'quiz' ? 'Creating...' : 'Create Quiz'}
                  disabled={actionDisabled}
                  onPress={generateQuiz}
                >
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
                </ToolAction>
              </View>
            </Card>
          </Section>

          <Section title="Saved Study Tools">
            <ResponsiveGrid minItemWidth={320}>
              <View style={styles.section}>
                <Text style={styles.subsectionTitle}>Latest Review Notes</Text>
                {summaries.length ? (
                  <>
                    <SummaryView summary={summaries[0]} />
                    <Button
                      title="Open Saved Notes"
                      variant="secondary"
                      onPress={() => router.push(`/summaries/${summaries[0].id}` as Href)}
                    />
                  </>
                ) : (
                  <EmptyState title="No review notes" message="Create review notes from this source." />
                )}
              </View>

              <View style={styles.section}>
                <Text style={styles.subsectionTitle}>Flashcards</Text>
                {flashcards.length ? <FlashcardList flashcards={flashcards} /> : <EmptyState title="No flashcards" message="Create flashcards for quick review." />}
              </View>

              <View style={styles.section}>
                <Text style={styles.subsectionTitle}>Practice Quizzes</Text>
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
                  <EmptyState title="No practice quizzes" message="Create a quiz to test your understanding." />
                )}
              </View>
            </ResponsiveGrid>
          </Section>

          <Section title="Source Management">
            <Card>
              <Text style={styles.itemTitle}>Source Settings</Text>
              <Text style={styles.itemMeta}>Delete this source only when you no longer need its review notes, flashcards, quizzes, and attempts.</Text>
              <Button title={deleting ? 'Deleting...' : 'Delete Source'} disabled={!!working || deleting} variant="danger" onPress={confirmDeleteDocument} />
            </Card>
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

function sourceReadinessLabel(document: DocumentDetail): string {
  if (document.status === 'needs_ocr' || document.extraction_quality === 'poor') {
    return 'Needs text recognition before StudyPilot can create reliable study tools.';
  }
  if (document.extraction_quality === 'partial') {
    return 'Partially readable. Review the source text before creating study tools.';
  }
  return 'Ready for review notes, flashcards, and practice.';
}

function nextSourceActionMessage(document: DocumentDetail): string {
  if (document.status === 'needs_ocr' || document.extraction_quality === 'poor') {
    return 'Run text recognition first so StudyPilot can use the source reliably.';
  }
  if (document.extraction_quality === 'partial') {
    return 'This source is partially readable. Check the full text, then create review notes from the readable content.';
  }
  return 'Create review notes first, then turn this source into flashcards or a practice quiz.';
}

function workingTitle(working: string): string {
  if (working === 'ocr') {
    return 'Recognizing text';
  }
  if (working === 'quiz') {
    return 'Creating practice quiz';
  }
  if (working === 'flashcards') {
    return 'Creating flashcards';
  }
  return 'Writing review notes';
}

function workingMessage(working: string, step: number): string {
  const messages: Record<string, string[]> = {
    ocr: [
      'Reading scanned PDF pages.',
      'Extracting text that was not selectable in the original file.',
      'Saving the recognized text back to this source.',
    ],
    flashcards: [
      'Finding recall-worthy concepts in the source.',
      'Turning the concepts into question and answer cards.',
      'Saving the flashcards to this course library.',
    ],
    quiz: [
      'Finding concepts that can be tested.',
      'Writing multiple-choice questions and distractors.',
      'Saving the practice quiz so you can review it later.',
    ],
    explanation: [
      'Reading the source for concepts that need more teaching context.',
      'Expanding the lecture into slower explanations, intuition, and connections.',
      'Saving the additional explanation to this source and course library.',
    ],
    concise: [
      'Reading the source and identifying the main conceptual flow.',
      'Rewriting the key ideas as compact study notes.',
      'Saving the review notes to this source and course library.',
    ],
    detailed: [
      'Reading the source and grouping related concepts.',
      'Re-explaining definitions, mechanisms, and relationships.',
      'Saving the deeper review notes to this course library.',
    ],
    exam: [
      'Reading the source for likely test points.',
      'Writing comparisons, exceptions, and memorization anchors.',
      'Saving the exam prep notes to this course library.',
    ],
  };
  const sequence = messages[working] || messages.concise;
  return sequence[step % sequence.length];
}

function ExtractionQualityCard({ document }: { document: DocumentDetail }) {
  const percentReadable = Math.round(document.extraction_coverage * 100);
  return (
    <Card style={qualityCardStyle(document)}>
      <Text style={styles.sectionTitle}>Source Reading Quality</Text>
      <Text style={styles.qualityHeadline}>{qualityHeadline(document)}</Text>
      <Text style={styles.optionDescription}>
        {document.page_count > 0
          ? `${document.extracted_page_count} of ${document.page_count} pages have readable text.`
          : `${document.char_count} readable characters extracted.`}
      </Text>
      <View style={styles.qualityTrack}>
        <View style={[styles.qualityFill, { width: `${Math.max(6, percentReadable)}%` }]} />
      </View>
      <Text style={styles.previewMeta}>{qualityDetail(document)}</Text>
    </Card>
  );
}

function qualityCardStyle(document: DocumentDetail) {
  if (document.status === 'needs_ocr' || document.extraction_quality === 'poor') {
    return styles.qualityWarningCard;
  }
  if (document.extraction_quality === 'partial') {
    return styles.qualityPartialCard;
  }
  return styles.qualityReadyCard;
}

function qualityHeadline(document: DocumentDetail): string {
  if (document.ocr_status === 'completed') {
    return 'OCR text is available';
  }
  if (document.status === 'needs_ocr' || document.extraction_quality === 'poor') {
    return 'This source needs OCR before reliable studying';
  }
  if (document.extraction_quality === 'partial') {
    return 'Some pages may be missing text';
  }
  return 'Ready for review notes and practice';
}

function qualityDetail(document: DocumentDetail): string {
  if (document.extraction_notes) {
    return document.extraction_notes;
  }
  if (document.extraction_quality === 'good' || document.extraction_quality === 'ocr') {
    return 'StudyPilot can use this extracted text for summaries, flashcards, and quizzes.';
  }
  return 'If the generated material feels incomplete, run text recognition or check the full source text.';
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function SavedCount({ label, value }: { label: string; value: number }) {
  return (
    <View style={styles.savedCount}>
      <Text style={styles.savedCountValue}>{value}</Text>
      <Text style={styles.savedCountLabel}>{label}</Text>
    </View>
  );
}

function ToolAction({
  title,
  description,
  buttonTitle,
  disabled,
  onPress,
  variant = 'primary',
  highlight = false,
  children,
}: {
  title: string;
  description: string;
  buttonTitle: string;
  disabled: boolean;
  onPress: () => void;
  variant?: 'primary' | 'secondary';
  highlight?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <View style={[styles.toolAction, highlight && styles.highlightToolAction]}>
      <View style={styles.toolTextBlock}>
        <Text style={styles.optionTitle}>{title}</Text>
        <Text style={styles.optionDescription}>{description}</Text>
      </View>
      {children ? <View style={styles.toolControls}>{children}</View> : null}
      <Button title={buttonTitle} disabled={disabled} variant={variant} onPress={onPress} />
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
  title: {
    color: colors.text,
    fontSize: 26,
    fontWeight: '900',
    lineHeight: 32,
  },
  subtitle: {
    color: colors.textMuted,
    lineHeight: 20,
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
  previewToggle: {
    alignSelf: 'flex-start',
    marginTop: 10,
    minHeight: 36,
    justifyContent: 'center',
  },
  previewToggleText: {
    color: colors.primary,
    fontSize: 14,
    fontWeight: '900',
  },
  actions: {
    gap: 10,
  },
  tabletActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  startCard: {
    backgroundColor: colors.primarySurface,
    borderColor: colors.primary,
  },
  savedStrip: {
    flexDirection: 'row',
    gap: 8,
  },
  savedCount: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flex: 1,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  savedCountValue: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '900',
  },
  savedCountLabel: {
    color: colors.textMuted,
    fontSize: 12,
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
  toolHeader: {
    gap: 4,
  },
  toolEyebrow: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  toolGrid: {
    gap: 10,
  },
  tabletToolGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  toolAction: {
    backgroundColor: colors.surfaceSubtle,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flexGrow: 1,
    gap: 10,
    minWidth: 250,
    padding: 12,
  },
  highlightToolAction: {
    backgroundColor: colors.primarySurface,
    borderColor: colors.primary,
  },
  toolTextBlock: {
    gap: 4,
  },
  toolControls: {
    gap: 10,
  },
  qualityText: {
    color: colors.text,
    fontSize: 13,
    fontWeight: '800',
    lineHeight: 18,
  },
  qualityHeadline: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '900',
  },
  qualityTrack: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    height: 10,
    overflow: 'hidden',
  },
  qualityFill: {
    backgroundColor: colors.accent,
    borderRadius: 8,
    height: '100%',
  },
  qualityReadyCard: {
    backgroundColor: colors.successSurface,
  },
  qualityPartialCard: {
    backgroundColor: colors.infoSurface,
  },
  qualityWarningCard: {
    backgroundColor: colors.warningSurface,
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
  section: {
    gap: 10,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 17,
    fontWeight: '800',
  },
  subsectionTitle: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: '900',
    textTransform: 'uppercase',
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
