import { StyleSheet, Text, View } from 'react-native';

import type { Summary } from '@/api/types';
import { colors } from '@/constants/colors';
import { cleanDisplayText } from '@/utils/text';
import { Card } from './Card';

export function SummaryView({ summary }: { summary: Summary }) {
  const title = cleanDisplayText(summary.title, 'Review Notes');
  const overview = cleanDisplayText(summary.overview, 'No overview available.');
  const keyPoints = summary.key_points.map((point) => cleanDisplayText(point)).filter(Boolean);

  return (
    <Card>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.kicker}>Overview</Text>
      <Text style={styles.body}>{overview}</Text>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Key Ideas</Text>
        {keyPoints.length ? (
          keyPoints.map((point, index) => (
            <View key={`${point}-${index}`} style={styles.numberedRow}>
              <Text style={styles.number}>{index + 1}</Text>
              <Text style={styles.body}>{point}</Text>
            </View>
          ))
        ) : (
          <Text style={styles.body}>No key points available.</Text>
        )}
      </View>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Key Concepts</Text>
        {summary.key_terms.length ? (
          summary.key_terms.map((item, index) => (
            <View key={`${item.term}-${index}`} style={styles.termBlock}>
              <Text style={styles.term}>{cleanDisplayText(item.term, 'Term')}</Text>
              <Text style={styles.body}>{cleanDisplayText(item.definition, 'No definition available.')}</Text>
            </View>
          ))
        ) : (
          <Text style={styles.body}>No key terms available.</Text>
        )}
      </View>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Source Evidence</Text>
        {summary.source_quotes.length ? (
          summary.source_quotes.map((item, index) => (
            <View key={`${item.quote}-${index}`} style={styles.quoteBlock}>
              <Text style={styles.quote}>{cleanDisplayText(item.quote, 'No quote available.')}</Text>
              <Text style={styles.quoteReason}>{cleanDisplayText(item.reason, 'Representative source excerpt.')}</Text>
            </View>
          ))
        ) : (
          <Text style={styles.body}>No source quotes available.</Text>
        )}
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  title: {
    color: colors.text,
    fontSize: 20,
    fontWeight: '900',
    lineHeight: 26,
  },
  body: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
  },
  kicker: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  section: {
    gap: 8,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 12,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  numberedRow: {
    flexDirection: 'row',
    gap: 10,
  },
  number: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: 8,
    color: colors.text,
    fontSize: 12,
    fontWeight: '900',
    minWidth: 26,
    overflow: 'hidden',
    paddingHorizontal: 7,
    paddingVertical: 4,
    textAlign: 'center',
  },
  termBlock: {
    gap: 4,
  },
  term: {
    color: colors.text,
    fontSize: 14,
    fontWeight: '900',
  },
  quoteBlock: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: 8,
    gap: 5,
    padding: 10,
  },
  quote: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
  },
  quoteReason: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 17,
  },
});
