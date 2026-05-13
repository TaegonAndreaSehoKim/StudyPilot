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
    padding: 14,
  },
  info: {
    backgroundColor: '#EFF6FF',
    borderColor: '#BFDBFE',
  },
  success: {
    backgroundColor: '#ECFDF3',
    borderColor: '#B7E4C7',
  },
  warning: {
    backgroundColor: '#FFFAEB',
    borderColor: '#FEDF89',
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
