import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { colors } from '@/constants/colors';

export default function RootLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.text },
          headerTintColor: colors.surface,
          headerTitleStyle: { fontWeight: '800' },
          contentStyle: { backgroundColor: colors.background },
        }}
      >
        <Stack.Screen name="index" options={{ title: 'StudyPilot' }} />
        <Stack.Screen name="settings" options={{ title: 'Settings' }} />
        <Stack.Screen name="courses/index" options={{ title: 'Courses' }} />
        <Stack.Screen name="courses/new" options={{ title: 'New Course' }} />
        <Stack.Screen name="courses/[courseId]" options={{ title: 'Course' }} />
        <Stack.Screen name="documents/[documentId]" options={{ title: 'Source' }} />
        <Stack.Screen name="documents/[documentId]/text" options={{ title: 'Full Source' }} />
        <Stack.Screen name="summaries/[summaryId]" options={{ title: 'Review Notes' }} />
        <Stack.Screen name="flashcards/course/[courseId]" options={{ title: 'Flashcards' }} />
        <Stack.Screen name="quizzes/course/[courseId]" options={{ title: 'Practice Quizzes' }} />
        <Stack.Screen name="attempts/course/[courseId]" options={{ title: 'Practice History' }} />
        <Stack.Screen name="schedule/course/[courseId]" options={{ title: 'Deadlines' }} />
        <Stack.Screen name="quiz/[quizId]" options={{ title: 'Practice Quiz' }} />
      </Stack>
    </>
  );
}
