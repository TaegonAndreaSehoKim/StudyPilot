import { useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { api } from '@/api/client';
import type { ScheduleEventType, ScheduleItem } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingState } from '@/components/LoadingState';
import { colors } from '@/constants/colors';
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
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

    try {
      setSaving(true);
      setError(null);
      await api.createScheduleItem(id, {
        title: title.trim(),
        event_type: eventType,
        due_at: dueAt.toISOString(),
        notes: notes.trim() || undefined,
      });
      setTitle('');
      setNotes('');
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
      await api.updateScheduleItem(item.id, { is_completed: !item.is_completed });
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
      await api.deleteScheduleItem(itemId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete schedule item');
    }
  }

  if (loading) {
    return <LoadingState message="Loading schedule" />;
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      {error ? <ErrorState message={error} onRetry={load} /> : null}

      <View style={styles.header}>
        <Text style={styles.title}>Course Schedule</Text>
        <Text style={styles.subtitle}>Track assignments, exams, readings, and milestones.</Text>
      </View>

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
          <TextInput
            placeholder="YYYY-MM-DD"
            placeholderTextColor={colors.textMuted}
            style={[styles.input, styles.dateInput]}
            value={dueDate}
            onChangeText={setDueDate}
          />
          <TextInput
            placeholder="HH:mm"
            placeholderTextColor={colors.textMuted}
            style={[styles.input, styles.timeInput]}
            value={dueTime}
            onChangeText={setDueTime}
          />
        </View>
        <TextInput
          multiline
          placeholder="Notes"
          placeholderTextColor={colors.textMuted}
          style={[styles.input, styles.notesInput]}
          value={notes}
          onChangeText={setNotes}
        />
        <Button title={saving ? 'Saving...' : 'Add Schedule Item'} disabled={saving} onPress={createItem} />
      </Card>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Items</Text>
        {items.length ? (
          items.map((item) => (
            <Card key={item.id}>
              <View style={styles.itemHeader}>
                <Text style={[styles.itemTitle, item.is_completed && styles.completedText]}>{item.title}</Text>
                <Text style={[styles.badge, item.is_completed ? styles.doneBadge : styles.openBadge]}>
                  {item.is_completed ? 'done' : item.event_type}
                </Text>
              </View>
              <Text style={styles.itemMeta}>{formatTimeRemaining(item.due_at, item.is_completed)}</Text>
              <Text style={styles.itemMeta}>{formatDateTime(item.due_at)}</Text>
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
          ))
        ) : (
          <EmptyState title="No schedule items" message="Add your first assignment deadline or exam date." />
        )}
      </View>
    </ScrollView>
  );
}

function toDateInput(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
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

const styles = StyleSheet.create({
  container: {
    gap: 16,
    padding: 16,
  },
  header: {
    gap: 4,
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: '800',
    lineHeight: 30,
  },
  subtitle: {
    color: colors.textMuted,
    lineHeight: 20,
  },
  section: {
    gap: 10,
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
  timeInput: {
    width: 96,
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
    color: colors.text,
  },
  doneBadge: {
    backgroundColor: colors.successSurface,
    color: colors.text,
  },
  itemMeta: {
    color: colors.textMuted,
    fontSize: 13,
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
