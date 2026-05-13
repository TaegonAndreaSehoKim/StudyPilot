import * as DocumentPicker from 'expo-document-picker';
import { Link, router, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Alert, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { CourseDashboard, Document, Flashcard, Summary } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { colors } from '@/constants/colors';

export default function CourseDetailScreen() {
  const { courseId } = useLocalSearchParams<{ courseId: string }>();
  const id = Number(courseId);
  const [dashboard, setDashboard] = useState<CourseDashboard | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const [courseDashboard, docs, summaryList, cardList] = await Promise.all([
        api.courseDashboard(id),
        api.courseDocuments(id),
        api.courseSummaries(id),
        api.courseFlashcards(id),
      ]);
      setDashboard(courseDashboard);
      setDocuments(docs);
      setSummaries(summaryList);
      setFlashcards(cardList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load course');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

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
      await load();
      router.push(`/documents/${document.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to upload document');
    } finally {
      setUploading(false);
    }
  }

  function confirmDeleteCourse() {
    Alert.alert(
      'Delete course?',
      'This removes the course, uploaded documents, generated study materials, quizzes, and weak topics.',
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
    return <LoadingState message="Loading course" />;
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {dashboard ? (
        <>
          <View style={styles.header}>
            <Text style={styles.title}>{dashboard.course.title}</Text>
            {dashboard.course.description ? <Text style={styles.subtitle}>{dashboard.course.description}</Text> : null}
          </View>
          <View style={styles.metrics}>
            <Text style={styles.metric}>{dashboard.document_count} docs</Text>
            <Text style={styles.metric}>{dashboard.summary_count} summaries</Text>
            <Text style={styles.metric}>{dashboard.quiz_count} quizzes</Text>
          </View>
          <View style={styles.actions}>
            <Button title={uploading ? 'Uploading...' : 'Upload Document'} disabled={uploading || deleting} onPress={upload} />
            <Button title={deleting ? 'Deleting...' : 'Delete Course'} disabled={uploading || deleting} variant="danger" onPress={confirmDeleteCourse} />
          </View>

          <Section title="Documents">
            {documents.length ? (
              documents.map((document) => (
                <Link key={document.id} href={`/documents/${document.id}`} asChild>
                  <Card>
                    <Text style={styles.itemTitle}>{document.filename}</Text>
                    <Text style={styles.itemMeta}>{document.char_count} chars - {document.status}</Text>
                  </Card>
                </Link>
              ))
            ) : (
              <EmptyState title="No documents" message="Upload .txt, .md, or text-based .pdf notes." />
            )}
          </Section>

          <Section title="Saved Summaries">
            {summaries.length ? (
              summaries.map((summary) => (
                <Link key={summary.id} href={`/summaries/${summary.id}` as Href} asChild>
                  <Card>
                    <Text style={styles.itemTitle}>{summary.title}</Text>
                    <Text style={styles.itemMeta}>
                      {summary.summary_type} summary - document #{summary.document_id}
                    </Text>
                  </Card>
                </Link>
              ))
            ) : (
              <EmptyState title="No summaries" message="Generate a summary from a document and it will appear here." />
            )}
          </Section>

          <Section title="Saved Flashcards">
            {flashcards.length ? (
              <Link href={`/flashcards/course/${id}` as Href} asChild>
                <Card>
                  <Text style={styles.itemTitle}>Review Course Flashcards</Text>
                  <Text style={styles.itemMeta}>{flashcards.length} cards saved across this course</Text>
                </Card>
              </Link>
            ) : (
              <EmptyState title="No flashcards" message="Generate flashcards from a document and they will appear here." />
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
              <EmptyState title="No weak topics" message="Quiz misses for this course will appear here." />
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
  metric: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: 8,
    color: colors.text,
    fontWeight: '800',
    paddingHorizontal: 10,
    paddingVertical: 7,
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
