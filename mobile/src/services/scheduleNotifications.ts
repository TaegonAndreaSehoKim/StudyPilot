import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

import type { ScheduleItem } from '@/api/types';

const STORAGE_KEY_PREFIX = 'studypilot.scheduleNotification.';
const SCHEDULE_CHANNEL_ID = 'study-schedule-reminders';

export const REMINDER_OPTIONS: { label: string; value: number | null }[] = [
  { label: 'No alert', value: null },
  { label: 'At due time', value: 0 },
  { label: '10 min before', value: 10 },
  { label: '1 hour before', value: 60 },
  { label: '1 day before', value: 1440 },
];

export type ReminderScheduleStatus = 'disabled' | 'scheduled' | 'skipped' | 'permission-denied' | 'unsupported' | 'failed';

let handlerConfigured = false;

export function configureScheduleNotifications() {
  if (handlerConfigured || Platform.OS === 'web') {
    return;
  }

  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldPlaySound: true,
      shouldSetBadge: false,
      shouldShowBanner: true,
      shouldShowList: true,
    }),
  });
  handlerConfigured = true;
}

export async function scheduleReminderForItem(item: ScheduleItem): Promise<ReminderScheduleStatus> {
  await cancelReminderForItem(item.id);

  if (Platform.OS === 'web') {
    return item.reminder_minutes_before == null ? 'disabled' : 'unsupported';
  }
  if (item.reminder_minutes_before == null || item.is_completed) {
    return 'disabled';
  }

  const dueAt = new Date(item.due_at);
  const reminderAt = new Date(dueAt.getTime() - item.reminder_minutes_before * 60 * 1000);
  if (Number.isNaN(reminderAt.getTime()) || reminderAt.getTime() <= Date.now() + 1000) {
    return 'skipped';
  }

  configureScheduleNotifications();
  try {
    const granted = await ensureNotificationPermission();
    if (!granted) {
      return 'permission-denied';
    }

    const notificationId = await Notifications.scheduleNotificationAsync({
      content: {
        title: reminderTitle(item),
        body: `${item.title} is due ${formatDueDate(dueAt)}.`,
        data: {
          url: `/schedule/course/${item.course_id}`,
          courseId: item.course_id,
          scheduleItemId: item.id,
        },
        sound: true,
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.DATE,
        date: reminderAt,
      },
    });
    await AsyncStorage.setItem(storageKey(item.id), notificationId);
    return 'scheduled';
  } catch {
    return 'failed';
  }
}

export async function cancelReminderForItem(itemId: number): Promise<void> {
  const key = storageKey(itemId);
  const notificationId = await AsyncStorage.getItem(key);
  try {
    if (notificationId && Platform.OS !== 'web') {
      await Notifications.cancelScheduledNotificationAsync(notificationId);
    }
  } finally {
    await AsyncStorage.removeItem(key);
  }
}

export function reminderLabel(minutes: number | null): string {
  const option = REMINDER_OPTIONS.find((item) => item.value === minutes);
  if (option) {
    return option.label;
  }
  if (minutes == null) {
    return 'No alert';
  }
  if (minutes === 0) {
    return 'At due time';
  }
  if (minutes < 60) {
    return `${minutes} min before`;
  }
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const remainingMinutes = minutes % 60;
  const parts = [
    days ? `${days} day${days === 1 ? '' : 's'}` : null,
    hours ? `${hours} hour${hours === 1 ? '' : 's'}` : null,
    remainingMinutes ? `${remainingMinutes} min` : null,
  ].filter(Boolean);
  if (parts.length) {
    return `${parts.join(' ')} before`;
  }
  return `${minutes} min before`;
}

function storageKey(itemId: number): string {
  return `${STORAGE_KEY_PREFIX}${itemId}`;
}

async function ensureNotificationPermission(): Promise<boolean> {
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync(SCHEDULE_CHANNEL_ID, {
      name: 'Study schedule reminders',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#2754C5',
    });
  }

  const existing = await Notifications.getPermissionsAsync();
  if (existing.granted || existing.ios?.status === Notifications.IosAuthorizationStatus.PROVISIONAL) {
    return true;
  }
  const requested = await Notifications.requestPermissionsAsync({
    ios: {
      allowAlert: true,
      allowBadge: false,
      allowSound: true,
    },
  });
  return requested.granted || requested.ios?.status === Notifications.IosAuthorizationStatus.PROVISIONAL;
}

function reminderTitle(item: ScheduleItem): string {
  const label = reminderLabel(item.reminder_minutes_before);
  if (label === 'At due time') {
    return `${eventTypeLabel(item.event_type)} due now`;
  }
  return `${eventTypeLabel(item.event_type)} due soon`;
}

function eventTypeLabel(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatDueDate(value: Date): string {
  return value.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}
