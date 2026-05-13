import { Link, router, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { DocumentDetail, Flashcard, Quiz, Summary } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { FlashcardList } from '@/components/FlashcardList';
import { LoadingState } from '@/components/LoadingState';
import { SummaryView } from '@/components/SummaryView';
import { colors } from '@/constants/colors';

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
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    load();
  }, [load]);

  async function generateSummary(summaryType: 'concise' | 'exam') {
    try {
      setWorking(summaryType);
      setError(null);
      const summary = await api.createSummary(id, summaryType);
      setSummaries((current) => [summary, ...current]);
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
      setFlashcards(await api.createFlashcards(id, 10));
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
      const quiz = await api.createQuiz(id, 5, 'mixed');
      setQuizzes((current) => [quiz, ...current]);
      router.push(`/quiz/${quiz.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to generate quiz');
    } finally {
      setWorking(null);
    }
  }

  if (loading) {
    return <LoadingState message="Loading document" />;
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {document ? (
        <>
          <View style={styles.header}>
            <Text style={styles.title}>{document.filename}</Text>
            <Text style={styles.subtitle}>{document.char_count} chars - {document.status}</Text>
          </View>

          <Card>
            <Text style={styles.sectionTitle}>Preview</Text>
            <Text style={styles.preview}>{document.preview || 'No extracted text preview available.'}</Text>
          </Card>

          <View style={styles.actions}>
            <Button title={working === 'concise' ? 'Generating...' : 'Generate Concise Summary'} disabled={!!working} onPress={() => generateSummary('concise')} />
            <Button title={working === 'exam' ? 'Generating...' : 'Generate Exam Summary'} disabled={!!working} variant="secondary" onPress={() => generateSummary('exam')} />
            <Button title={working === 'flashcards' ? 'Generating...' : 'Generate Flashcards'} disabled={!!working} variant="secondary" onPress={generateFlashcards} />
            <Button title={working === 'quiz' ? 'Generating...' : 'Generate Quiz'} disabled={!!working} variant="secondary" onPress={generateQuiz} />
          </View>

          <Section title="Latest Summary">
            {summaries.length ? <SummaryView summary={summaries[0]} /> : <EmptyState title="No summary" message="Generate a summary from this document." />}
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
    </ScrollView>
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
  actions: {
    gap: 10,
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
