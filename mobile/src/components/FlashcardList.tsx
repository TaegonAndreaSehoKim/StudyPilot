import { StyleSheet, Text, View } from 'react-native';

import type { Flashcard } from '@/api/types';
import { colors } from '@/constants/colors';
import { Card } from './Card';

export function FlashcardList({ flashcards }: { flashcards: Flashcard[] }) {
  return (
    <View style={styles.list}>
      {flashcards.map((card) => (
        <Card key={card.id}>
          <Text style={styles.topic}>{card.topic} - {card.difficulty}</Text>
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
  topic: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '700',
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
