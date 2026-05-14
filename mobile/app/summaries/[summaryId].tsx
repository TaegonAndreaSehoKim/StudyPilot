import { Link, useLocalSearchParams } from 'expo-router';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import { useCallback, useEffect, useState } from 'react';
import { RefreshControl, Share, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { DocumentDetail, Summary } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { ScreenScrollView } from '@/components/Screen';
import { SummaryView } from '@/components/SummaryView';
import { colors } from '@/constants/colors';
import { summaryToHtml, summaryToMarkdown } from '@/utils/exportText';

export default function SummaryDetailScreen() {
  const { summaryId } = useLocalSearchParams<{ summaryId: string }>();
  const id = Number(summaryId);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const loadedSummary = await api.summary(id);
      setSummary(loadedSummary);
      setDocument(await api.document(loadedSummary.document_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load review notes');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function shareSummary() {
    if (!summary) {
      return;
    }
    try {
      setSharing(true);
      const pdf = await Print.printToFileAsync({
        html: summaryToHtml(summary),
      });
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(pdf.uri, {
          dialogTitle: 'Save / Share Review Notes PDF',
          mimeType: 'application/pdf',
          UTI: 'com.adobe.pdf',
        });
      } else {
        await Share.share({
          title: summary.title,
          message: summaryToMarkdown(summary),
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to share review notes');
    } finally {
      setSharing(false);
    }
  }

  if (loading) {
    return <LoadingState message="Loading review notes" />;
  }

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {summary ? (
        <>
          <View style={styles.header}>
            <Text style={styles.title}>{summary.title}</Text>
            <Text style={styles.subtitle}>{summaryTypeLabel(summary.summary_type)} review notes</Text>
          </View>

          {document ? (
            <Link href={`/documents/${document.id}`} asChild>
              <Card>
                <Text style={styles.itemTitle}>Source Material</Text>
                <Text style={styles.itemMeta}>{document.filename}</Text>
                <Text style={styles.itemHint}>Open the source to read the original context or create more practice.</Text>
              </Card>
            </Link>
          ) : null}

          <Button title={sharing ? 'Creating PDF...' : 'Save / Share PDF'} disabled={sharing} onPress={shareSummary} />

          <SummaryView summary={summary} />
        </>
      ) : null}
    </ScreenScrollView>
  );
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
  return value;
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
    maxWidth: 920,
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
  itemHint: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 18,
  },
});
