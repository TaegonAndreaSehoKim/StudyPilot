import type { Summary } from '@/api/types';
import { cleanDisplayText } from './text';

export function summaryToHtml(summary: Summary): string {
  const title = cleanDisplayText(summary.title, 'Review Notes');
  const type = summaryTypeLabel(summary.summary_type);
  const overview = cleanDisplayText(summary.overview, 'No overview available.');
  const keyPoints = summary.key_points.map((point) => cleanDisplayText(point)).filter(Boolean);
  const keyTerms = summary.key_terms.map((item) => ({
    term: cleanDisplayText(item.term, 'Term'),
    definition: cleanDisplayText(item.definition, 'No definition available.'),
  }));
  const sourceQuotes = summary.source_quotes.map((item) => ({
    quote: cleanDisplayText(item.quote, 'No quote available.'),
    reason: cleanDisplayText(item.reason, 'Representative source excerpt.'),
  }));
  const pointHeading = summary.summary_type === 'explanation' ? 'Additional Explanation' : 'What to Remember';
  const conceptHeading = summary.summary_type === 'explanation' ? 'Concepts Explained' : 'Key Concepts';

  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <style>
      body {
        color: #261714;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        line-height: 1.45;
        margin: 40px;
      }
      h1 {
        font-size: 28px;
        line-height: 1.2;
        margin: 0 0 8px;
      }
      h2 {
        border-bottom: 1px solid #D9C3B0;
        color: #A64029;
        font-size: 17px;
        margin: 28px 0 10px;
        padding-bottom: 6px;
      }
      h3 {
        color: #261714;
        font-size: 15px;
        margin: 14px 0 4px;
      }
      .meta {
        color: #8C7161;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 22px;
      }
      p {
        margin: 8px 0;
      }
      .point {
        margin: 12px 0;
      }
      .quote {
        background: #F6EEE8;
        border-left: 4px solid #D9663D;
        margin: 12px 0;
        padding: 12px 14px;
      }
      .reason {
        color: #8C7161;
        font-size: 13px;
        margin-top: 6px;
      }
    </style>
  </head>
  <body>
    <h1>${escapeHtml(title)}</h1>
    <div class="meta">StudyPilot - ${escapeHtml(type)} Notes</div>
    <h2>Overview</h2>
    <p>${escapeHtml(overview)}</p>
    <h2>${escapeHtml(pointHeading)}</h2>
    ${keyPoints.length ? keyPoints.map((point, index) => `<div class="point"><h3>${index + 1}. Key idea</h3><p>${escapeHtml(point)}</p></div>`).join('') : '<p>None</p>'}
    <h2>${escapeHtml(conceptHeading)}</h2>
    ${keyTerms.length ? keyTerms.map((item) => `<div class="point"><h3>${escapeHtml(item.term)}</h3><p>${escapeHtml(item.definition)}</p></div>`).join('') : '<p>None</p>'}
    <h2>Source Evidence</h2>
    ${sourceQuotes.length ? sourceQuotes.map((item) => `
      <div class="quote">
        <div>${escapeHtml(item.quote)}</div>
        <div class="reason">${escapeHtml(item.reason)}</div>
      </div>
    `).join('') : '<p>None</p>'}
  </body>
</html>`;
}

export function summaryToMarkdown(summary: Summary): string {
  const type = summaryTypeLabel(summary.summary_type);
  const pointHeading = summary.summary_type === 'explanation' ? 'Additional Explanation' : 'Key Points';
  const conceptHeading = summary.summary_type === 'explanation' ? 'Concepts Explained' : 'Key Terms';
  const lines = [
    `# ${cleanDisplayText(summary.title, 'Study Summary')}`,
    '',
    `Type: ${type}`,
    '',
    '## Overview',
    cleanDisplayText(summary.overview, 'No overview available.'),
    '',
    `## ${pointHeading}`,
    ...listLines(summary.key_points.map((point) => cleanDisplayText(point)).filter(Boolean)),
    '',
    `## ${conceptHeading}`,
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

function htmlList(values: string[], shouldEscape = true): string {
  if (!values.length) {
    return '<p>None</p>';
  }
  return `<ul>${values.map((value) => `<li>${shouldEscape ? escapeHtml(value) : value}</li>`).join('')}</ul>`;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function summaryTypeLabel(value: string): string {
  if (value === 'concise') {
    return 'Quick Review';
  }
  if (value === 'detailed') {
    return 'Deep Review';
  }
  if (value === 'exam') {
    return 'Exam Prep';
  }
  if (value === 'explanation') {
    return 'Additional Explanation';
  }
  return cleanDisplayText(value, 'Review');
}
