export function cleanDisplayText(value: string | null | undefined, fallback = ''): string {
  if (!value) {
    return fallback;
  }

  return value
    .replace(/\uFFFD/g, '')
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '')
    .replace(/[ \t]+/g, ' ')
    .trim() || fallback;
}
