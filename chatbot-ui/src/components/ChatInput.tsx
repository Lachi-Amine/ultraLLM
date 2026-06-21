import { useState } from 'react';
import {
  type NativeSyntheticEvent,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  type TextInputKeyPressEventData,
  View,
} from 'react-native';

import type { ThemeColors } from '@/constants/config';
import { shouldSubmitOnEnter } from '@/utils/chatInputKeyboard';

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
  colors: ThemeColors;
}

export function ChatInput({ onSend, disabled, colors }: Props) {
  const [value, setValue] = useState('');

  const canSend = !disabled && value.trim().length > 0;

  const submit = () => {
    if (!canSend) return;
    onSend(value);
    setValue('');
  };

  const handleKeyPress = (
    event: NativeSyntheticEvent<TextInputKeyPressEventData>,
  ) => {
    if (Platform.OS !== 'web') return;

    const nativeEvent = event.nativeEvent as TextInputKeyPressEventData & {
      shiftKey?: boolean;
      isComposing?: boolean;
    };

    if (
      shouldSubmitOnEnter(
        nativeEvent.key,
        nativeEvent.shiftKey,
        nativeEvent.isComposing,
      )
    ) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: colors.surface, borderTopColor: colors.border },
      ]}
    >
      <TextInput
        style={[
          styles.input,
          {
            backgroundColor: colors.inputBackground,
            borderColor: colors.border,
            color: colors.text,
          },
        ]}
        placeholder="Type a message…"
        placeholderTextColor={colors.textMuted}
        value={value}
        onChangeText={setValue}
        onKeyPress={handleKeyPress}
        multiline
        editable={!disabled}
        returnKeyType="send"
      />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Send message"
        onPress={submit}
        disabled={!canSend}
        style={({ pressed }) => [
          styles.sendButton,
          {
            backgroundColor: canSend ? colors.accent : colors.disabled,
            opacity: pressed && canSend ? 0.85 : 1,
          },
        ]}
      >
        <Text style={styles.sendText}>Send</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 8,
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 140,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 22,
    borderWidth: StyleSheet.hairlineWidth,
    fontSize: 16,
  },
  sendButton: {
    minWidth: 64,
    height: 44,
    paddingHorizontal: 16,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});
