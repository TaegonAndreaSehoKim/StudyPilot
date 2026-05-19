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
          const label = choice.replace(/^[A-Z][).:\-\s]+/, '').trim() || choice;
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
              <View
                style={[
                  styles.choiceLetter,
                  isSelected && styles.selectedLetter,
                  isCorrect && styles.correctLetter,
                  isMissedSelection && styles.incorrectLetter,
                ]}
              >
                <Text
                  style={[
                    styles.choiceLetterText,
                    isSelected && styles.selectedText,
                    isCorrect && styles.correctChoiceText,
                    isMissedSelection && styles.incorrectChoiceText,
                  ]}
                >
                  {letter}
                </Text>
              </View>
              <Text
                style={[
                  styles.choiceText,
                  isSelected && styles.selectedText,
                  isCorrect && styles.correctChoiceText,
                  isMissedSelection && styles.incorrectChoiceText,
                ]}
              >
                {label}
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
    fontWeight: '800',
    textTransform: 'capitalize',
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
    alignItems: 'flex-start',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    minHeight: 52,
    padding: 12,
  },
  selected: {
    backgroundColor: colors.primarySurface,
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
    flex: 1,
    color: colors.text,
    lineHeight: 20,
  },
  choiceLetter: {
    alignItems: 'center',
    backgroundColor: colors.surfaceMuted,
    borderRadius: 8,
    height: 28,
    justifyContent: 'center',
    width: 28,
  },
  choiceLetterText: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: '900',
  },
  selectedLetter: {
    backgroundColor: colors.surface,
  },
  correctLetter: {
    backgroundColor: colors.surface,
  },
  incorrectLetter: {
    backgroundColor: colors.surface,
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
