import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { colors } from '@/constants/colors';

export function LoadingState({ message = 'Loading' }: { message?: string }) {
  return (
    <View style={styles.container}>
      <ActivityIndicator color={colors.primary} />
      <Text style={styles.text}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    gap: 10,
    justifyContent: 'center',
    minHeight: 180,
    padding: 24,
  },
  text: {
    color: colors.textMuted,
    fontWeight: '700',
  },
});
