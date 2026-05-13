export interface ParsedQuizExplanation {
  summary: string;
  sourceQuote?: string;
  wrongChoiceReasons: string[];
}

export function parseQuizExplanation(value: string): ParsedQuizExplanation {
  const lines = value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  const summaryLines: string[] = [];
  const wrongChoiceReasons: string[] = [];
  let sourceQuote: string | undefined;
  let readingWrongReasons = false;

  for (const line of lines) {
    const lower = line.toLowerCase();
    if (lower.startsWith('source quote:')) {
      sourceQuote = line.slice(line.indexOf(':') + 1).trim();
      readingWrongReasons = false;
      continue;
    }
    if (lower.startsWith('why other choices are wrong')) {
      readingWrongReasons = true;
      continue;
    }
    if (readingWrongReasons || /^[A-D]:\s/.test(line)) {
      wrongChoiceReasons.push(line);
      continue;
    }
    summaryLines.push(line);
  }

  return {
    summary: summaryLines.join(' ') || value,
    sourceQuote,
    wrongChoiceReasons,
  };
}
