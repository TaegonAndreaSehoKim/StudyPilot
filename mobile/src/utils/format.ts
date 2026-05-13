export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString();
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}
