import { StyleSheet, Text, View } from 'react-native';

import type { Summary } from '@/api/types';
import { colors } from '@/constants/colors';
import { cleanDisplayText } from '@/utils/text';
import { Card } from './Card';

export function SummaryView({ summary }: { summary: Summary }) {
  const title = cleanDisplayText(summary.title, 'Study Summary');
  const overview = cleanDisplayText(summary.overview, 'No overview available.');
  const keyPoints = summary.key_points.map((point) => cleanDisplayText(point)).filter(Boolean);

  return (
    <Card>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.body}>{overview}</Text>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Key Points</Text>
        {keyPoints.map((point, index) => (
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
    fontWeight: '700',
    lineHeight: 24,
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
    fontWeight: '700',
    textTransform: 'uppercase',
  },
});
