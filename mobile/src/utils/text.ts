export function cleanDisplayText(value: string | null | undefined, fallback = ''): string {
  if (!value) {
    return fallback;
  }

  let text = value
    .replace(/\uFFFD/g, '')
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '')
    .replace(/de\.nition/g, 'definition')
    .replace(/De\.nition/g, 'Definition')
    .replace(/Speci\.c/g, 'Specific')
    .replace(/speci\.c/g, 'specific')
    .replace(/\.xed/g, 'fixed')
    .replace(/\.oats/g, 'floats')
    .replace(/\.oat/g, 'float')
    .replace(/\bTy p e o f M o v e m e n t\b/g, 'Type of Movement')
    .replace(/[ \t]+/g, ' ')
    .trim();

  text = text.replace(/\b(?:Source Material|Document)\s+\d+:\s*/gi, '');
  text = text.replace(/\bPage\s+\d+\s+of\s+\d+\b/gi, '');
  text = text.replace(/(^|[.!?]\s+)A\s+(?=[A-Z])/g, '$1');

  return text.trim() || fallback;
}
