import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { QuizQuestion } from '@/api/types';
import { colors } from '@/constants/colors';
import { Card } from './Card';

export function QuizQuestionView({
  question,
  selected,
  onSelect,
}: {
  question: QuizQuestion;
  selected?: string;
  onSelect: (answer: string) => void;
}) {
  return (
    <Card>
      <Text style={styles.topic}>{question.topic} · {question.difficulty}</Text>
      <Text style={styles.question}>{question.question}</Text>
      <View style={styles.choices}>
        {question.choices.map((choice) => {
          const letter = choice.slice(0, 1);
          const isSelected = selected === letter;
          return (
            <Pressable
              key={choice}
              onPress={() => onSelect(letter)}
              style={[styles.choice, isSelected && styles.selected]}
            >
              <Text style={[styles.choiceText, isSelected && styles.selectedText]}>{choice}</Text>
            </Pressable>
          );
        })}
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  topic: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '700',
  },
  question: {
    color: colors.text,
    fontSize: 17,
    fontWeight: '800',
    lineHeight: 23,
  },
  choices: {
    gap: 8,
  },
  choice: {
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    padding: 12,
  },
  selected: {
    backgroundColor: '#EAF1FF',
    borderColor: colors.primary,
  },
  choiceText: {
    color: colors.text,
    lineHeight: 20,
  },
  selectedText: {
    color: colors.primary,
    fontWeight: '700',
  },
});
