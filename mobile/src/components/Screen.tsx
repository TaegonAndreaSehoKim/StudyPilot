import { Children, PropsWithChildren } from 'react';
import { ScrollView, ScrollViewProps, StyleProp, StyleSheet, useWindowDimensions, View, ViewStyle } from 'react-native';

type ScreenScrollViewProps = PropsWithChildren<
  Omit<ScrollViewProps, 'contentContainerStyle'> & {
    contentContainerStyle?: StyleProp<ViewStyle>;
  }
>;

export function ScreenScrollView({ children, contentContainerStyle, ...props }: ScreenScrollViewProps) {
  const { width } = useWindowDimensions();
  const isTablet = width >= 768;

  return (
    <ScrollView
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
      {...props}
      contentContainerStyle={[styles.container, isTablet && styles.tabletContainer, contentContainerStyle]}
    >
      {children}
    </ScrollView>
  );
}

export function ResponsiveGrid({
  children,
  minItemWidth = 300,
  gap = 12,
}: PropsWithChildren<{ minItemWidth?: number; gap?: number }>) {
  const { width } = useWindowDimensions();
  const isTablet = width >= 768;

  return (
    <View style={[styles.grid, { gap }]}>
      {Children.toArray(children).map((child, index) => (
          <View
            key={index}
            style={isTablet ? { flexBasis: minItemWidth, flexGrow: 1, minWidth: minItemWidth } : styles.fullWidth}
          >
            {child}
          </View>
      ))}
    </View>
  );
}

export function useTabletLayout() {
  const { width } = useWindowDimensions();
  return width >= 768;
}

const styles = StyleSheet.create({
  container: {
    gap: 18,
    padding: 16,
    paddingBottom: 28,
  },
  tabletContainer: {
    alignSelf: 'center',
    maxWidth: 1120,
    paddingHorizontal: 32,
    paddingTop: 24,
    width: '100%',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  fullWidth: {
    width: '100%',
  },
});
