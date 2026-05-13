import { PropsWithChildren } from 'react';
import { Pressable, PressableProps, StyleProp, StyleSheet, View, ViewStyle } from 'react-native';

import { colors } from '@/constants/colors';

type CardProps = PropsWithChildren<Omit<PressableProps, 'style'> & { style?: StyleProp<ViewStyle> }>;

export function Card({ children, onPress, style, ...props }: CardProps) {
  if (onPress) {
    return (
      <Pressable
        {...props}
        onPress={onPress}
        style={({ pressed }) => [styles.card, pressed && styles.pressed, style]}
      >
        {children}
      </Pressable>
    );
  }

  return <View style={[styles.card, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    padding: 14,
    gap: 8,
  },
  pressed: {
    opacity: 0.82,
  },
});
