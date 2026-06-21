import { memo } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type { Message } from '@/types/chat';
import type { ThemeColors } from '@/constants/config';

interface Props {
  message: Message;
  colors: ThemeColors;
}

function MessageBubbleBase({ message, colors }: Props) {
  const isUser = message.role === 'user';

  const bubbleStyle = {
    backgroundColor: isUser ? colors.userBubble : colors.assistantBubble,
    alignSelf: isUser ? ('flex-end' as const) : ('flex-start' as const),
    borderBottomRightRadius: isUser ? 4 : 18,
    borderBottomLeftRadius: isUser ? 18 : 4,
  };

  const textColor = isUser ? colors.userBubbleText : colors.assistantBubbleText;

  return (
    <View style={[styles.bubble, bubbleStyle]}>
      <Text style={[styles.text, { color: textColor }]} selectable>
        {message.content}
      </Text>
      {!isUser && message.sources?.length ? (
        <Text style={[styles.sources, { color: colors.textMuted }]}>
          Sources: {message.sources.map((source) => source.engine).join(', ')}
        </Text>
      ) : null}
    </View>
  );
}

export const MessageBubble = memo(MessageBubbleBase);

const styles = StyleSheet.create({
  bubble: {
    maxWidth: '82%',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 18,
    marginVertical: 4,
  },
  text: {
    fontSize: 16,
    lineHeight: 22,
  },
  sources: {
    fontSize: 12,
    lineHeight: 16,
    marginTop: 8,
  },
});
