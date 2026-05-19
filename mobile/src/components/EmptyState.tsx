import { StyleSheet, Text, View } from 'react-native';

import { colors } from '@/constants/colors';

export function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.message}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surfaceSubtle,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 8,
    gap: 7,
    padding: 18,
  },
  title: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '700',
  },
  message: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 20,
  },
});
