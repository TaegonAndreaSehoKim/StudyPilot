import { useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { RefreshControl, ScrollView, Share, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { Flashcard } from '@/api/types';
import { Button } from '@/components/Button';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { FlashcardList } from '@/components/FlashcardList';
import { LoadingState } from '@/components/LoadingState';
import { colors } from '@/constants/colors';
import { flashcardsToMarkdown } from '@/utils/flashcardsExport';

export default function CourseFlashcardsScreen() {
  const { courseId } = useLocalSearchParams<{ courseId: string }>();
  const id = Number(courseId);
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setFlashcards(await api.courseFlashcards(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load flashcards');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function shareFlashcards() {
    try {
      setSharing(true);
      await Share.share({
        title: 'StudyPilot Flashcards',
        message: flashcardsToMarkdown(flashcards),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to share flashcards');
    } finally {
      setSharing(false);
    }
  }

  if (loading) {
    return <LoadingState message="Loading flashcards" />;
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      <View style={styles.header}>
        <Text style={styles.title}>Saved Flashcards</Text>
        <Text style={styles.subtitle}>{flashcards.length} cards across this course</Text>
      </View>

      {flashcards.length ? (
        <>
          <Button title={sharing ? 'Opening...' : 'Save / Share Flashcards'} disabled={sharing} onPress={shareFlashcards} />
          <FlashcardList flashcards={flashcards} />
        </>
      ) : (
        <EmptyState title="No flashcards" message="Generate flashcards from a document and they will appear here." />
      )}
    </ScrollView>
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
    fontWeight: '800',
    lineHeight: 30,
  },
  subtitle: {
    color: colors.textMuted,
  },
});
