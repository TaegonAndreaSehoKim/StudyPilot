import { Link, router, useLocalSearchParams } from 'expo-router';
import type { Href } from 'expo-router';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import { useCallback, useEffect, useState } from 'react';
import { Alert, RefreshControl, Share, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { CourseSection, DocumentDetail, StudyNoteType, Summary } from '@/api/types';
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
  const [section, setSection] = useState<CourseSection | null>(null);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const loadedSummary = await api.summary(id);
      setSummary(loadedSummary);
      setSection(loadedSummary.section_id ? await api.section(loadedSummary.section_id) : null);
      setDocument(loadedSummary.document_id ? await api.document(loadedSummary.document_id) : null);
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

  async function regenerateSummary() {
    if (!summary || (!document && !summary.section_id)) {
      return;
    }
    try {
      setRegenerating(true);
      setError(null);
      const summaryType = summary.summary_type as StudyNoteType;
      const newSummary = summaryType === 'explanation'
        ? summary.section_id
          ? await api.createSectionExplanation(summary.section_id)
          : await api.createExplanation(document!.id)
        : summary.section_id
          ? await api.createSectionSummary(summary.section_id, summaryType)
          : await api.createSummary(document!.id, summaryType);
      router.replace(`/summaries/${newSummary.id}` as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to regenerate review notes');
    } finally {
      setRegenerating(false);
    }
  }

  function confirmDeleteSummary() {
    Alert.alert(
      'Delete review notes?',
      'This removes these saved notes from the source and course library. The original source material stays available.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: deleteSummary },
      ],
    );
  }

  async function deleteSummary() {
    if (!summary) {
      return;
    }
    try {
      setDeleting(true);
      setError(null);
      await api.deleteSummary(summary.id);
      if (summary.section_id) {
        router.replace(`/sections/${summary.section_id}` as Href);
      } else if (document) {
        router.replace(`/documents/${document.id}` as Href);
      } else {
        router.back();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete review notes');
    } finally {
      setDeleting(false);
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
                <Text style={styles.itemTitle}>Study Source</Text>
                <Text style={styles.itemMeta}>{document.filename}</Text>
                <Text style={styles.itemHint}>Open the source to read the original context or create more practice.</Text>
              </Card>
            </Link>
          ) : null}

          {section ? (
            <Link href={`/sections/${section.id}` as Href} asChild>
              <Card>
                <Text style={styles.itemTitle}>Study Section</Text>
                <Text style={styles.itemMeta}>{section.title}</Text>
                <Text style={styles.itemHint}>Open the section to review the full source set or create more practice.</Text>
              </Card>
            </Link>
          ) : null}

          <View style={styles.actions}>
            <Button
              title={sharing ? 'Creating PDF...' : 'Save / Share PDF'}
              disabled={sharing || regenerating || deleting}
              onPress={shareSummary}
            />
            <Button
              title={regenerating ? 'Regenerating...' : 'Regenerate Notes'}
              disabled={(!document && !summary.section_id) || sharing || regenerating || deleting}
              variant="secondary"
              onPress={regenerateSummary}
            />
          </View>

          <SummaryView summary={summary} />

          <Card>
            <Text style={styles.itemTitle}>Notes Management</Text>
            <Text style={styles.itemHint}>Delete these notes only when you no longer want them in the source or course library.</Text>
            <Button
              title={deleting ? 'Deleting...' : 'Delete Notes'}
              disabled={sharing || regenerating || deleting}
              variant="danger"
              onPress={confirmDeleteSummary}
            />
          </Card>
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
  if (value === 'explanation') {
    return 'Additional Explanation';
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
  actions: {
    gap: 8,
  },
});
