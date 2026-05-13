import { useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { RefreshControl, Share, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { DocumentText } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { ScreenScrollView } from '@/components/Screen';
import { colors } from '@/constants/colors';

export default function DocumentTextScreen() {
  const { documentId } = useLocalSearchParams<{ documentId: string }>();
  const id = Number(documentId);
  const [document, setDocument] = useState<DocumentText | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setDocument(await api.documentText(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load document text');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function shareText() {
    if (!document) {
      return;
    }
    try {
      setSharing(true);
      await Share.share({
        title: document.filename,
        message: document.text,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to share document text');
    } finally {
      setSharing(false);
    }
  }

  if (loading) {
    return <LoadingState message="Loading full text" />;
  }

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {document ? (
        <>
          <View style={styles.header}>
            <Text style={styles.title}>{document.filename}</Text>
            <Text style={styles.subtitle}>{document.char_count} extracted chars - {document.status}</Text>
          </View>
          <Button title={sharing ? 'Opening...' : 'Save / Share Extracted Text'} disabled={sharing} onPress={shareText} />
          <Card>
            <Text selectable style={styles.fullText}>
              {document.text || 'No extracted text available.'}
            </Text>
          </Card>
        </>
      ) : null}
    </ScreenScrollView>
  );
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
  fullText: {
    color: colors.text,
    fontSize: 15,
    lineHeight: 23,
  },
});
