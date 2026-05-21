import { useEffect } from 'react';
import * as Notifications from 'expo-notifications';
import { router, Stack } from 'expo-router';
import type { Href } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { colors } from '@/constants/colors';
import { configureScheduleNotifications } from '@/services/scheduleNotifications';

export default function RootLayout() {
  useScheduleNotificationObserver();

  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.primary },
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
        <Stack.Screen name="sections/[sectionId]" options={{ title: 'Study Section' }} />
        <Stack.Screen name="documents/index" options={{ title: 'Sources' }} />
        <Stack.Screen name="documents/[documentId]" options={{ title: 'Source' }} />
        <Stack.Screen name="documents/[documentId]/text" options={{ title: 'Full Source' }} />
        <Stack.Screen name="summaries/[summaryId]" options={{ title: 'Review Notes' }} />
        <Stack.Screen name="flashcards/course/[courseId]" options={{ title: 'Flashcards' }} />
        <Stack.Screen name="quizzes/course/[courseId]" options={{ title: 'Practice Quizzes' }} />
        <Stack.Screen name="attempts/course/[courseId]" options={{ title: 'Practice History' }} />
        <Stack.Screen name="schedule/course/[courseId]" options={{ title: 'Deadlines' }} />
        <Stack.Screen name="study/course/[courseId]" options={{ title: 'Study Session' }} />
        <Stack.Screen name="quiz/[quizId]" options={{ title: 'Practice Quiz' }} />
      </Stack>
    </>
  );
}

function useScheduleNotificationObserver() {
  useEffect(() => {
    configureScheduleNotifications();

    function redirect(notification: Notifications.Notification) {
      const url = notification.request.content.data?.url;
      if (typeof url === 'string') {
        router.push(url as Href);
      }
    }

    const lastResponse = Notifications.getLastNotificationResponse();
    if (lastResponse?.notification) {
      redirect(lastResponse.notification);
    }

    const subscription = Notifications.addNotificationResponseReceivedListener((response) => {
      redirect(response.notification);
    });

    return () => {
      subscription.remove();
    };
  }, []);
}
