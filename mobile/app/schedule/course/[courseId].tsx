import { useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Pressable, RefreshControl, StyleSheet, Text, TextInput, View } from 'react-native';

import { api } from '@/api/client';
import type { ScheduleEventType, ScheduleItem } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { ResponsiveGrid, ScreenScrollView, useTabletLayout } from '@/components/Screen';
import { StatusBanner } from '@/components/StatusBanner';
import { colors } from '@/constants/colors';
import {
  cancelReminderForItem,
  reminderLabel,
  scheduleReminderForItem,
  type ReminderScheduleStatus,
} from '@/services/scheduleNotifications';
import { formatDateTime, formatTimeRemaining } from '@/utils/format';

const EVENT_TYPES: ScheduleEventType[] = ['assignment', 'exam', 'reading', 'project', 'other'];

export default function CourseScheduleScreen() {
  const { courseId } = useLocalSearchParams<{ courseId: string }>();
  const id = Number(courseId);
  const today = useMemo(() => new Date(), []);
  const [items, setItems] = useState<ScheduleItem[]>([]);
  const [title, setTitle] = useState('');
  const [eventType, setEventType] = useState<ScheduleEventType>('assignment');
  const [dueDate, setDueDate] = useState(toDateInput(today));
  const [dueTime, setDueTime] = useState('23:59');
  const [notes, setNotes] = useState('');
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [calendarMonth, setCalendarMonth] = useState(startOfMonth(today));
  const [reminderEnabled, setReminderEnabled] = useState(true);
  const [reminderDays, setReminderDays] = useState('0');
  const [reminderHours, setReminderHours] = useState('1');
  const [reminderMinutes, setReminderMinutes] = useState('0');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const isTablet = useTabletLayout();

  const load = useCallback(async () => {
    try {
      setError(null);
      setItems(await api.courseSchedule(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load schedule');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function createItem() {
    const dueAt = parseLocalDateTime(dueDate, dueTime);
    if (!title.trim()) {
      setError('Enter a title for this schedule item.');
      return;
    }
    if (!dueAt) {
      setError('Use date format YYYY-MM-DD and time format HH:mm.');
      return;
    }
    const reminderMinutesBefore = reminderEnabled ? calculateReminderMinutes(reminderDays, reminderHours, reminderMinutes) : null;
    if (reminderMinutesBefore === undefined) {
      setError('Use whole numbers for popup alert days, hours, and minutes.');
      return;
    }
    if (reminderMinutesBefore !== null && reminderMinutesBefore > 10080) {
      setError('Popup alerts can be scheduled up to 7 days before the deadline.');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      setNotice(null);
      const createdItem = await api.createScheduleItem(id, {
        title: title.trim(),
        event_type: eventType,
        due_at: dueAt.toISOString(),
        notes: notes.trim() || undefined,
        reminder_minutes_before: reminderMinutesBefore,
      });
      const reminderStatus = await scheduleReminderForItem(createdItem);
      setTitle('');
      setNotes('');
      setNotice(reminderStatusMessage(reminderStatus, createdItem));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create schedule item');
    } finally {
      setSaving(false);
    }
  }

  async function toggleItem(item: ScheduleItem) {
    try {
      setError(null);
      setNotice(null);
      const updatedItem = await api.updateScheduleItem(item.id, { is_completed: !item.is_completed });
      let reminderStatus: ReminderScheduleStatus = 'disabled';
      if (updatedItem.is_completed) {
        await cancelReminderForItem(updatedItem.id);
      } else {
        reminderStatus = await scheduleReminderForItem(updatedItem);
      }
      setNotice(updatedItem.is_completed ? 'Schedule item marked done. Its popup alert was canceled.' : reminderStatusMessage(reminderStatus, updatedItem));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update schedule item');
    }
  }

  function confirmDelete(item: ScheduleItem) {
    Alert.alert('Delete schedule item?', item.title, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => deleteItem(item.id) },
    ]);
  }

  async function deleteItem(itemId: number) {
    try {
      setError(null);
      setNotice(null);
      await cancelReminderForItem(itemId);
      await api.deleteScheduleItem(itemId);
      setNotice('Schedule item deleted. Its popup alert was canceled.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete schedule item');
    }
  }

  if (loading) {
    return <LoadingState message="Loading schedule" />;
  }

  return (
    <ScreenScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {notice ? <StatusBanner title="Schedule alert" message={notice} variant="success" /> : null}

      <View style={styles.header}>
        <Text style={styles.title}>Course Schedule</Text>
        <Text style={styles.subtitle}>Track assignments, exams, readings, and milestones.</Text>
      </View>

      <View style={[styles.layout, isTablet && styles.tabletLayout]}>
        <View style={isTablet ? styles.formPane : undefined}>
          <Card>
            <Text style={styles.sectionTitle}>Add Item</Text>
            <TextInput
              placeholder="Title"
              placeholderTextColor={colors.textMuted}
              style={styles.input}
              value={title}
              onChangeText={setTitle}
            />
            <View style={styles.typeRow}>
              {EVENT_TYPES.map((type) => (
                <Button
                  key={type}
                  title={type}
                  variant={eventType === type ? 'primary' : 'secondary'}
                  onPress={() => setEventType(type)}
                />
              ))}
            </View>
            <View style={styles.dateRow}>
              <Pressable
                accessibilityRole="button"
                onPress={() => setCalendarOpen((current) => !current)}
                style={[styles.input, styles.dateInput, styles.datePickerButton]}
              >
                <Text style={dueDate ? styles.datePickerText : styles.datePickerPlaceholder}>
                  {dueDate || 'YYYY-MM-DD'}
                </Text>
              </Pressable>
              <TextInput
                placeholder="HH:mm"
                placeholderTextColor={colors.textMuted}
                keyboardType="number-pad"
                style={[styles.input, styles.timeInput]}
                value={dueTime}
                onChangeText={(value) => setDueTime(formatTimeInput(value))}
                onBlur={() => setDueTime(normalizeTimeInput(dueTime))}
              />
            </View>
            {calendarOpen ? (
              <MiniCalendar
                month={calendarMonth}
                selectedDate={dueDate}
                onPreviousMonth={() => setCalendarMonth(addMonths(calendarMonth, -1))}
                onNextMonth={() => setCalendarMonth(addMonths(calendarMonth, 1))}
                onSelect={(dateValue) => {
                  setDueDate(dateValue);
                  setCalendarMonth(startOfMonth(parseDateInput(dateValue) || calendarMonth));
                  setCalendarOpen(false);
                }}
              />
            ) : null}
            <TextInput
              multiline
              placeholder="Notes"
              placeholderTextColor={colors.textMuted}
              style={[styles.input, styles.notesInput]}
              value={notes}
              onChangeText={setNotes}
            />
            <View style={styles.reminderGroup}>
              <Text style={styles.inputLabel}>Popup alert</Text>
              <Pressable
                accessibilityRole="button"
                onPress={() => setReminderEnabled((current) => !current)}
                style={[styles.noAlertButton, !reminderEnabled && styles.activeNoAlertButton]}
              >
                <Text style={[styles.noAlertButtonText, !reminderEnabled && styles.activeNoAlertButtonText]}>
                  No alert
                </Text>
              </Pressable>
              <View style={[styles.customReminderRow, !reminderEnabled && styles.disabledReminderFields]}>
                <ReminderNumberInput
                  label="Days"
                  value={reminderDays}
                  disabled={!reminderEnabled}
                  onFocus={() => setReminderEnabled(true)}
                  onChange={setReminderDays}
                />
                <ReminderNumberInput
                  label="Hours"
                  value={reminderHours}
                  disabled={!reminderEnabled}
                  onFocus={() => setReminderEnabled(true)}
                  onChange={setReminderHours}
                />
                <ReminderNumberInput
                  label="Minutes"
                  value={reminderMinutes}
                  disabled={!reminderEnabled}
                  onFocus={() => setReminderEnabled(true)}
                  onChange={setReminderMinutes}
                />
              </View>
              {reminderEnabled ? (
                <Text style={styles.reminderHint}>
                  {customReminderSentence(reminderDays, reminderHours, reminderMinutes)}
                </Text>
              ) : null}
            </View>
            <Button title={saving ? 'Saving...' : 'Add Schedule Item'} disabled={saving} onPress={createItem} />
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Items</Text>
          {items.length ? (
            <ResponsiveGrid minItemWidth={320}>
              {items.map((item) => (
                <Card key={item.id}>
                  <View style={styles.itemHeader}>
                    <Text style={[styles.itemTitle, item.is_completed && styles.completedText]}>{item.title}</Text>
                    <Text style={[styles.badge, item.is_completed ? styles.doneBadge : styles.openBadge]}>
                      {item.is_completed ? 'done' : item.event_type}
                    </Text>
                  </View>
                  <Text style={styles.itemMeta}>{formatTimeRemaining(item.due_at, item.is_completed)}</Text>
                  <Text style={styles.itemMeta}>{formatDateTime(item.due_at)}</Text>
                  <Text style={styles.reminderMeta}>
                    Popup alert: {item.reminder_minutes_before == null ? 'Off' : reminderLabel(item.reminder_minutes_before)}
                  </Text>
                  {item.notes ? <Text style={styles.notes}>{item.notes}</Text> : null}
                  <View style={styles.itemActions}>
                    <Button
                      title={item.is_completed ? 'Mark Open' : 'Mark Done'}
                      variant="secondary"
                      onPress={() => toggleItem(item)}
                    />
                    <Button title="Delete" variant="danger" onPress={() => confirmDelete(item)} />
                  </View>
                </Card>
              ))}
            </ResponsiveGrid>
          ) : (
            <EmptyState title="No schedule items" message="Add your first assignment deadline or exam date." />
          )}
        </View>
      </View>
    </ScreenScrollView>
  );
}

function reminderStatusMessage(status: ReminderScheduleStatus, item: ScheduleItem): string {
  if (status === 'scheduled') {
    return `${reminderLabel(item.reminder_minutes_before)} popup alert scheduled for ${item.title}.`;
  }
  if (status === 'permission-denied') {
    return 'The schedule item was saved, but notifications are blocked on this device.';
  }
  if (status === 'skipped') {
    return 'The schedule item was saved, but the selected popup alert time is already past.';
  }
  if (status === 'unsupported') {
    return 'The schedule item was saved. Popup alerts are available on iOS and Android devices.';
  }
  if (status === 'failed') {
    return 'The schedule item was saved, but this device could not schedule the popup alert.';
  }
  return 'The schedule item was saved without a popup alert.';
}

function ReminderNumberInput({
  label,
  value,
  disabled,
  onFocus,
  onChange,
}: {
  label: string;
  value: string;
  disabled: boolean;
  onFocus: () => void;
  onChange: (value: string) => void;
}) {
  return (
    <View style={styles.reminderNumberField}>
      <Text style={styles.reminderNumberLabel}>{label}</Text>
      <TextInput
        keyboardType="number-pad"
        editable={!disabled}
        value={value}
        onFocus={onFocus}
        onChangeText={(text) => onChange(text.replace(/\D/g, '').slice(0, 4))}
        placeholder="0"
        placeholderTextColor={colors.textFaint}
        style={styles.reminderNumberInput}
      />
    </View>
  );
}

function MiniCalendar({
  month,
  selectedDate,
  onPreviousMonth,
  onNextMonth,
  onSelect,
}: {
  month: Date;
  selectedDate: string;
  onPreviousMonth: () => void;
  onNextMonth: () => void;
  onSelect: (dateValue: string) => void;
}) {
  const cells = buildCalendarCells(month);
  return (
    <View style={styles.calendar}>
      <View style={styles.calendarHeader}>
        <Pressable accessibilityRole="button" onPress={onPreviousMonth} style={styles.calendarNavButton}>
          <Text style={styles.calendarNavText}>{'<'}</Text>
        </Pressable>
        <Text style={styles.calendarTitle}>{month.toLocaleString(undefined, { month: 'long', year: 'numeric' })}</Text>
        <Pressable accessibilityRole="button" onPress={onNextMonth} style={styles.calendarNavButton}>
          <Text style={styles.calendarNavText}>{'>'}</Text>
        </Pressable>
      </View>
      <View style={styles.weekdayRow}>
        {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, index) => (
          <Text key={`${day}-${index}`} style={styles.weekdayText}>{day}</Text>
        ))}
      </View>
      <View style={styles.calendarGrid}>
        {cells.map((cell, index) => {
          const dateValue = cell ? toDateInput(cell) : '';
          const selected = !!dateValue && dateValue === selectedDate;
          const today = !!cell && dateValue === toDateInput(new Date());
          return (
            <Pressable
              key={`${dateValue || 'blank'}-${index}`}
              accessibilityRole={cell ? 'button' : undefined}
              disabled={!cell}
              onPress={() => cell && onSelect(dateValue)}
              style={[
                styles.calendarDay,
                !cell && styles.emptyCalendarDay,
                today && styles.todayCalendarDay,
                selected && styles.selectedCalendarDay,
              ]}
            >
              <Text
                style={[
                  styles.calendarDayText,
                  today && styles.todayCalendarDayText,
                  selected && styles.selectedCalendarDayText,
                ]}
              >
                {cell ? cell.getDate() : ''}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

function toDateInput(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function parseDateInput(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    return null;
  }
  const [, year, month, day] = match;
  const date = new Date(Number(year), Number(month) - 1, Number(day));
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date;
}

function startOfMonth(value: Date): Date {
  return new Date(value.getFullYear(), value.getMonth(), 1);
}

function addMonths(value: Date, amount: number): Date {
  return new Date(value.getFullYear(), value.getMonth() + amount, 1);
}

function buildCalendarCells(month: Date): Array<Date | null> {
  const firstDay = startOfMonth(month);
  const daysInMonth = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
  const cells: Array<Date | null> = Array.from({ length: firstDay.getDay() }, () => null);
  for (let day = 1; day <= daysInMonth; day += 1) {
    cells.push(new Date(month.getFullYear(), month.getMonth(), day));
  }
  while (cells.length % 7 !== 0) {
    cells.push(null);
  }
  return cells;
}

function formatDateInput(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 8);
  if (digits.length <= 4) {
    return digits;
  }
  if (digits.length <= 6) {
    return `${digits.slice(0, 4)}-${digits.slice(4)}`;
  }
  return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6)}`;
}

function formatTimeInput(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 4);
  if (digits.length <= 2) {
    return digits;
  }
  return `${digits.slice(0, 2)}:${digits.slice(2)}`;
}

function normalizeTimeInput(value: string): string {
  const digits = value.replace(/\D/g, '');
  if (digits.length === 3) {
    return formatTimeInput(digits.padStart(4, '0'));
  }
  return formatTimeInput(digits);
}

function parseLocalDateTime(dateValue: string, timeValue: string): Date | null {
  const dateMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateValue.trim());
  const timeMatch = /^(\d{2}):(\d{2})$/.exec(timeValue.trim());
  if (!dateMatch || !timeMatch) {
    return null;
  }

  const [, year, month, day] = dateMatch;
  const [, hour, minute] = timeMatch;
  const date = new Date(Number(year), Number(month) - 1, Number(day), Number(hour), Number(minute));
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date;
}

function calculateReminderMinutes(daysValue: string, hoursValue: string, minutesValue: string): number | null | undefined {
  const days = parseWholeNumber(daysValue || '0');
  const hours = parseWholeNumber(hoursValue || '0');
  const minutes = parseWholeNumber(minutesValue || '0');
  if (days === undefined || hours === undefined || minutes === undefined) {
    return undefined;
  }
  return days * 1440 + hours * 60 + minutes;
}

function parseWholeNumber(value: string): number | undefined {
  if (!/^\d+$/.test(value)) {
    return undefined;
  }
  return Number(value);
}

function customReminderSentence(daysValue: string, hoursValue: string, minutesValue: string): string {
  const total = calculateReminderMinutes(daysValue, hoursValue, minutesValue);
  if (total === undefined) {
    return 'Enter whole numbers for the popup alert time.';
  }
  if (total === 0) {
    return 'Alert at the due time.';
  }
  return `Alert ${reminderLabel(total)}.`;
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
  },
  layout: {
    gap: 16,
  },
  tabletLayout: {
    alignItems: 'flex-start',
    flexDirection: 'row',
  },
  formPane: {
    flexBasis: 340,
    flexGrow: 0,
  },
  header: {
    gap: 4,
  },
  title: {
    color: colors.text,
    fontSize: 26,
    fontWeight: '900',
    lineHeight: 32,
  },
  subtitle: {
    color: colors.textMuted,
    lineHeight: 20,
  },
  section: {
    flex: 1,
    gap: 10,
    minWidth: 0,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 17,
    fontWeight: '800',
  },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.text,
    fontSize: 15,
    minHeight: 44,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  notesInput: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  inputLabel: {
    color: colors.text,
    fontSize: 13,
    fontWeight: '800',
  },
  reminderGroup: {
    gap: 8,
  },
  noAlertButton: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    minHeight: 40,
    justifyContent: 'center',
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  activeNoAlertButton: {
    backgroundColor: colors.primarySurface,
    borderColor: colors.primary,
  },
  noAlertButtonText: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: '900',
  },
  activeNoAlertButtonText: {
    color: colors.primary,
  },
  customReminderRow: {
    flexDirection: 'row',
    gap: 8,
  },
  disabledReminderFields: {
    opacity: 0.48,
  },
  reminderNumberField: {
    flex: 1,
    gap: 5,
  },
  reminderNumberLabel: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '800',
  },
  reminderNumberInput: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.text,
    fontSize: 15,
    fontWeight: '800',
    minHeight: 42,
    paddingHorizontal: 10,
    paddingVertical: 8,
    textAlign: 'center',
  },
  reminderHint: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 17,
  },
  typeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  dateRow: {
    flexDirection: 'row',
    gap: 8,
  },
  dateInput: {
    flex: 1,
  },
  datePickerButton: {
    justifyContent: 'center',
  },
  datePickerText: {
    color: colors.text,
    fontSize: 15,
  },
  datePickerPlaceholder: {
    color: colors.textMuted,
    fontSize: 15,
  },
  timeInput: {
    width: 96,
  },
  calendar: {
    backgroundColor: colors.surfaceSubtle,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    gap: 10,
    padding: 10,
  },
  calendarHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  calendarTitle: {
    color: colors.text,
    fontSize: 15,
    fontWeight: '900',
  },
  calendarNavButton: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    height: 34,
    justifyContent: 'center',
    width: 38,
  },
  calendarNavText: {
    color: colors.primary,
    fontSize: 18,
    fontWeight: '900',
  },
  weekdayRow: {
    flexDirection: 'row',
  },
  weekdayText: {
    color: colors.textMuted,
    flex: 1,
    fontSize: 12,
    fontWeight: '900',
    textAlign: 'center',
  },
  calendarGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    rowGap: 6,
  },
  calendarDay: {
    alignItems: 'center',
    aspectRatio: 1,
    borderRadius: 8,
    justifyContent: 'center',
    width: '14.2857%',
  },
  emptyCalendarDay: {
    opacity: 0,
  },
  todayCalendarDay: {
    backgroundColor: colors.accentSurface,
  },
  selectedCalendarDay: {
    backgroundColor: colors.primary,
  },
  calendarDayText: {
    color: colors.text,
    fontSize: 14,
    fontWeight: '800',
  },
  todayCalendarDayText: {
    color: colors.accent,
  },
  selectedCalendarDayText: {
    color: colors.surface,
  },
  itemHeader: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    gap: 10,
    justifyContent: 'space-between',
  },
  itemTitle: {
    color: colors.text,
    flex: 1,
    fontSize: 16,
    fontWeight: '800',
    lineHeight: 22,
  },
  completedText: {
    color: colors.textMuted,
    textDecorationLine: 'line-through',
  },
  badge: {
    borderRadius: 8,
    fontSize: 12,
    fontWeight: '800',
    overflow: 'hidden',
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  openBadge: {
    backgroundColor: colors.warningSurface,
    color: colors.warning,
  },
  doneBadge: {
    backgroundColor: colors.successSurface,
    color: colors.success,
  },
  itemMeta: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 18,
  },
  reminderMeta: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '800',
    lineHeight: 18,
  },
  notes: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
  },
  itemActions: {
    gap: 8,
  },
});
