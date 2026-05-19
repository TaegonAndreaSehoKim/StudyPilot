import { StyleSheet, Text, View } from 'react-native';

import type { Flashcard } from '@/api/types';
import { colors } from '@/constants/colors';
import { Card } from './Card';

export function FlashcardList({ flashcards }: { flashcards: Flashcard[] }) {
  return (
    <View style={styles.list}>
      {flashcards.map((card) => (
        <Card key={card.id}>
          <View style={styles.metaRow}>
            <Text style={styles.topic}>{card.topic}</Text>
            <Text style={styles.difficulty}>{card.difficulty}</Text>
          </View>
          <Text style={styles.front}>{card.front}</Text>
          <Text style={styles.back}>{card.back}</Text>
        </Card>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  list: {
    gap: 10,
  },
  metaRow: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'space-between',
  },
  topic: {
    color: colors.textMuted,
    flex: 1,
    fontSize: 12,
    fontWeight: '800',
  },
  difficulty: {
    backgroundColor: colors.primarySurface,
    borderRadius: 8,
    color: colors.primary,
    fontSize: 12,
    fontWeight: '900',
    overflow: 'hidden',
    paddingHorizontal: 8,
    paddingVertical: 4,
    textTransform: 'capitalize',
  },
  front: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '800',
  },
  back: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
  },
});
