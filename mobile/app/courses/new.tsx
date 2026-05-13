import { router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TextInput } from 'react-native';

import { api } from '@/api/client';
import { Button } from '@/components/Button';
import { ErrorState } from '@/components/ErrorState';
import { colors } from '@/constants/colors';

export default function NewCourseScreen() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!title.trim()) {
      setError('Course title is required');
      return;
    }
    try {
      setSaving(true);
      setError(null);
      const course = await api.createCourse({ title: title.trim(), description: description.trim() || undefined });
      router.replace(`/courses/${course.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create course');
    } finally {
      setSaving(false);
    }
  }

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.flex}>
      <ScrollView contentContainerStyle={styles.container}>
        {error ? <ErrorState message={error} /> : null}
        <Text style={styles.label}>Title</Text>
        <TextInput
          value={title}
          onChangeText={setTitle}
          placeholder="OMSCS AI"
          style={styles.input}
          autoCapitalize="words"
        />
        <Text style={styles.label}>Description</Text>
        <TextInput
          value={description}
          onChangeText={setDescription}
          placeholder="Lecture notes, readings, and review materials"
          style={[styles.input, styles.multiline]}
          multiline
        />
        <Button title={saving ? 'Creating...' : 'Create Course'} disabled={saving} onPress={submit} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
  container: {
    gap: 10,
    padding: 16,
  },
  label: {
    color: colors.text,
    fontSize: 14,
    fontWeight: '800',
  },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.text,
    fontSize: 16,
    minHeight: 46,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  multiline: {
    minHeight: 96,
    textAlignVertical: 'top',
  },
});
