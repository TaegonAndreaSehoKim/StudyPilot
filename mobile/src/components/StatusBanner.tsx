import { StyleSheet, Text, View } from 'react-native';

import { colors } from '@/constants/colors';

type StatusVariant = 'info' | 'success' | 'warning';

interface StatusBannerProps {
  title: string;
  message: string;
  variant?: StatusVariant;
}

export function StatusBanner({ title, message, variant = 'info' }: StatusBannerProps) {
  return (
    <View style={[styles.container, styles[variant]]}>
      <Text style={[styles.title, { color: titleColor(variant) }]}>{title}</Text>
      <Text style={styles.message}>{message}</Text>
    </View>
  );
}

function titleColor(variant: StatusVariant) {
  if (variant === 'success') {
    return colors.success;
  }
  if (variant === 'warning') {
    return colors.warning;
  }
  return colors.primary;
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 8,
    borderWidth: 1,
    gap: 6,
    padding: 16,
  },
  info: {
    backgroundColor: colors.infoSurface,
    borderColor: colors.primarySurface,
  },
  success: {
    backgroundColor: colors.successSurface,
    borderColor: '#BDE7D2',
  },
  warning: {
    backgroundColor: colors.warningSurface,
    borderColor: '#F4C15D',
  },
  title: {
    fontSize: 15,
    fontWeight: '800',
  },
  message: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
  },
});
