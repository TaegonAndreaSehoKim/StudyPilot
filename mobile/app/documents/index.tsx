import { Link, useFocusEffect } from 'expo-router';
import type { Href } from 'expo-router';
import { useCallback, useState } from 'react';
import { RefreshControl, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { Document } from '@/api/types';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { ResponsiveGrid, ScreenScrollView } from '@/components/Screen';
import { colors } from '@/constants/colors';
import { formatDate } from '@/utils/format';

export default function DocumentsScreen() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setDocuments(await api.documents());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load source materials');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  if (loading) {
    return <LoadingState message="Loading source materials" />;
  }

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Sources</Text>
        <Text style={styles.subtitle}>All uploaded course materials, newest first.</Text>
      </View>

      {error ? <ErrorState message={error} onRetry={load} /> : null}

      {documents.length ? (
        <ResponsiveGrid minItemWidth={320}>
          {documents.map((document) => (
            <Link key={document.id} href={`/documents/${document.id}` as Href} asChild>
              <Card>
                <Text style={styles.itemTitle}>{document.filename}</Text>
                <Text style={styles.itemMeta}>{sourceStatusLabel(document)}</Text>
                <Text style={styles.itemMeta}>{formatDate(document.created_at)}</Text>
              </Card>
            </Link>
          ))}
        </ResponsiveGrid>
      ) : (
        <EmptyState title="No source materials" message="Open a course and add lecture notes, PDFs, or markdown files." />
      )}
    </ScreenScrollView>
  );
}

function sourceStatusLabel(document: Document): string {
  if (document.status === 'needs_ocr' || document.extraction_quality === 'poor') {
    return 'Needs text recognition';
  }
  if (document.extraction_quality === 'partial') {
    return 'Partially readable';
  }
  return 'Ready for study tools';
}

const styles = StyleSheet.create({
  container: {
    gap: 14,
  },
  header: {
    gap: 6,
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
  itemTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '800',
    lineHeight: 22,
  },
  itemMeta: {
    color: colors.textMuted,
    fontSize: 13,
  },
});
