import { StyleSheet, Text, View } from 'react-native';

import type { Summary } from '@/api/types';
import { colors } from '@/constants/colors';
import { Card } from './Card';

export function SummaryView({ summary }: { summary: Summary }) {
  return (
    <Card>
      <Text style={styles.title}>{summary.title}</Text>
      <Text style={styles.body}>{summary.overview}</Text>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Key Points</Text>
        {summary.key_points.map((point, index) => (
          <Text key={`${point}-${index}`} style={styles.body}>
            {index + 1}. {point}
          </Text>
        ))}
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  title: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '800',
  },
  body: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
  },
  section: {
    gap: 6,
  },
  sectionTitle: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
});
