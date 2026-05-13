export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString();
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString();
}

export function formatTimeRemaining(value: string, completed = false): string {
  if (completed) {
    return 'Completed';
  }

  const dueAt = new Date(value).getTime();
  const diffMs = dueAt - Date.now();
  const absMs = Math.abs(diffMs);
  const minuteMs = 60 * 1000;
  const hourMs = 60 * minuteMs;
  const dayMs = 24 * hourMs;

  let amount: number;
  let unit: string;
  if (absMs >= dayMs) {
    amount = Math.ceil(absMs / dayMs);
    unit = amount === 1 ? 'day' : 'days';
  } else if (absMs >= hourMs) {
    amount = Math.ceil(absMs / hourMs);
    unit = amount === 1 ? 'hour' : 'hours';
  } else {
    amount = Math.max(1, Math.ceil(absMs / minuteMs));
    unit = amount === 1 ? 'minute' : 'minutes';
  }

  return diffMs >= 0 ? `${amount} ${unit} left` : `${amount} ${unit} overdue`;
}
