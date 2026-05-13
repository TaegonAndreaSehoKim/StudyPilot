import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { QuizAnswerResult, QuizQuestion } from '@/api/types';
import { colors } from '@/constants/colors';
import { Card } from './Card';

export function QuizQuestionView({
  question,
  selected,
  result,
  onSelect,
}: {
  question: QuizQuestion;
  selected?: string;
  result?: QuizAnswerResult;
  onSelect: (answer: string) => void;
}) {
  const submitted = !!result;

  return (
    <Card>
      <Text style={styles.topic}>{question.topic} - {question.difficulty}</Text>
      <Text style={styles.question}>{question.question}</Text>
      <View style={styles.choices}>
        {question.choices.map((choice) => {
          const letter = choice.slice(0, 1);
          const isSelected = selected === letter;
          const isCorrect = submitted && result.correct_answer === letter;
          const isMissedSelection = submitted && result.selected_answer === letter && !result.is_correct;
          return (
            <Pressable
              key={choice}
              disabled={submitted}
              onPress={() => onSelect(letter)}
              style={[
                styles.choice,
                isSelected && styles.selected,
                isCorrect && styles.correctChoice,
                isMissedSelection && styles.incorrectChoice,
              ]}
            >
              <Text
                style={[
                  styles.choiceText,
                  isSelected && styles.selectedText,
                  isCorrect && styles.correctChoiceText,
                  isMissedSelection && styles.incorrectChoiceText,
                ]}
              >
                {choice}
              </Text>
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
    backgroundColor: colors.infoSurface,
    borderColor: colors.primary,
  },
  correctChoice: {
    backgroundColor: colors.successSurface,
    borderColor: colors.success,
  },
  incorrectChoice: {
    backgroundColor: colors.dangerSurface,
    borderColor: colors.danger,
  },
  choiceText: {
    color: colors.text,
    lineHeight: 20,
  },
  selectedText: {
    color: colors.primary,
    fontWeight: '700',
  },
  correctChoiceText: {
    color: colors.success,
    fontWeight: '800',
  },
  incorrectChoiceText: {
    color: colors.danger,
    fontWeight: '800',
  },
});
