import type { Summary } from '@/api/types';
import { cleanDisplayText } from './text';

export function summaryToMarkdown(summary: Summary): string {
  const lines = [
    `# ${cleanDisplayText(summary.title, 'Study Summary')}`,
    '',
    `Type: ${cleanDisplayText(summary.summary_type, 'summary')}`,
    '',
    '## Overview',
    cleanDisplayText(summary.overview, 'No overview available.'),
    '',
    '## Key Points',
    ...listLines(summary.key_points.map((point) => cleanDisplayText(point)).filter(Boolean)),
    '',
    '## Key Terms',
    ...listLines(
      summary.key_terms.map((item) => {
        const term = cleanDisplayText(item.term, 'Term');
        const definition = cleanDisplayText(item.definition, 'No definition available.');
        return `${term}: ${definition}`;
      }),
    ),
    '',
    '## Source Quotes',
    ...listLines(
      summary.source_quotes.map((item) => {
        const quote = cleanDisplayText(item.quote, 'No quote available.');
        const reason = cleanDisplayText(item.reason, 'Representative source excerpt.');
        return `"${quote}" (${reason})`;
      }),
    ),
  ];

  return lines.join('\n').trim();
}

function listLines(values: string[]): string[] {
  return values.length ? values.map((value) => `- ${value}`) : ['- None'];
}
