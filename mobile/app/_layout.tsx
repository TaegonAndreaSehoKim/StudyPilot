import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { colors } from '@/constants/colors';

export default function RootLayout() {
  return (
    <>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.surface },
          headerTintColor: colors.text,
          headerTitleStyle: { fontWeight: '800' },
          contentStyle: { backgroundColor: colors.background },
        }}
      >
        <Stack.Screen name="index" options={{ title: 'StudyPilot' }} />
        <Stack.Screen name="settings" options={{ title: 'Settings' }} />
        <Stack.Screen name="courses/index" options={{ title: 'Courses' }} />
        <Stack.Screen name="courses/new" options={{ title: 'New Course' }} />
        <Stack.Screen name="courses/[courseId]" options={{ title: 'Course' }} />
        <Stack.Screen name="documents/[documentId]" options={{ title: 'Document' }} />
        <Stack.Screen name="documents/[documentId]/text" options={{ title: 'Full Text' }} />
        <Stack.Screen name="summaries/[summaryId]" options={{ title: 'Summary' }} />
        <Stack.Screen name="quiz/[quizId]" options={{ title: 'Quiz' }} />
      </Stack>
    </>
  );
}
