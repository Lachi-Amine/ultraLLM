import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import type { ThemeColors } from '@/constants/config';

interface Props {
  colors: ThemeColors;
}

export function TypingIndicator({ colors }: Props) {
  return (
    <View
      style={[
        styles.container,
        { backgroundColor: colors.assistantBubble },
      ]}
    >
      <ActivityIndicator size="small" color={colors.textMuted} />
      <Text style={[styles.text, { color: colors.textMuted }]}>
        Assistant is typing…
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 18,
    borderBottomLeftRadius: 4,
    marginVertical: 4,
    gap: 8,
  },
  text: {
    fontSize: 14,
  },
});
