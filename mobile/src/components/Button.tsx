import { Pressable, StyleSheet, Text } from 'react-native';

import { colors } from '@/constants/colors';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
}

export function Button({ title, onPress, variant = 'primary', disabled = false }: ButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        styles[variant],
        disabled && styles.disabled,
        pressed && !disabled && styles.pressed,
      ]}
    >
      <Text style={[styles.text, variant === 'secondary' && styles.secondaryText]}>{title}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 44,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  primary: {
    backgroundColor: colors.primary,
  },
  secondary: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderWidth: 1,
  },
  danger: {
    backgroundColor: colors.danger,
  },
  pressed: {
    opacity: 0.82,
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    color: colors.surface,
    fontSize: 15,
    fontWeight: '700',
  },
  secondaryText: {
    color: colors.text,
  },
});
