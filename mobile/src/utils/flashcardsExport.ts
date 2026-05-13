import type { Flashcard } from '@/api/types';
import { cleanDisplayText } from './text';

export function flashcardsToMarkdown(flashcards: Flashcard[]): string {
  const lines = ['# StudyPilot Flashcards', ''];

  for (const card of flashcards) {
    lines.push(`## ${cleanDisplayText(card.topic, 'General')} (${cleanDisplayText(card.difficulty, 'medium')})`);
    lines.push('');
    lines.push(`Front: ${cleanDisplayText(card.front, 'Question')}`);
    lines.push('');
    lines.push(`Back: ${cleanDisplayText(card.back, 'Answer')}`);
    if (card.source_quote) {
      lines.push('');
      lines.push(`Source: ${cleanDisplayText(card.source_quote)}`);
    }
    lines.push('');
  }

  return lines.join('\n').trim();
}
