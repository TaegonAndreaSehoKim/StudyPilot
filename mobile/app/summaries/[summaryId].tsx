import { Link, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { DocumentDetail, Summary } from '@/api/types';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { SummaryView } from '@/components/SummaryView';
import { colors } from '@/constants/colors';

export default function SummaryDetailScreen() {
  const { summaryId } = useLocalSearchParams<{ summaryId: string }>();
  const id = Number(summaryId);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const loadedSummary = await api.summary(id);
      setSummary(loadedSummary);
      setDocument(await api.document(loadedSummary.document_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load summary');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <LoadingState message="Loading summary" />;
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {summary ? (
        <>
          <View style={styles.header}>
            <Text style={styles.title}>{summary.title}</Text>
            <Text style={styles.subtitle}>{summary.summary_type} summary</Text>
          </View>

          {document ? (
            <Link href={`/documents/${document.id}`} asChild>
              <Card>
                <Text style={styles.itemTitle}>Source Document</Text>
                <Text style={styles.itemMeta}>{document.filename}</Text>
              </Card>
            </Link>
          ) : null}

          <SummaryView summary={summary} />
        </>
      ) : null}
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
