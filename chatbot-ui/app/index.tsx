import { useEffect, useRef } from 'react';
import {
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
  useColorScheme,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ChatInput } from '@/components/ChatInput';
import { MessageBubble } from '@/components/MessageBubble';
import { TypingIndicator } from '@/components/TypingIndicator';
import { Colors } from '@/constants/config';
import { useChat } from '@/hooks/useChat';
import type { Message } from '@/types/chat';

export default function ChatScreen() {
  const scheme = useColorScheme();
  const colors = Colors[scheme === 'dark' ? 'dark' : 'light'];

  const { messages, isLoading, error, send, reset, clearError } = useChat();
  const listRef = useRef<FlatList<Message>>(null);

  // Auto-scroll to the latest message whenever the list grows or typing starts.
  useEffect(() => {
    const id = setTimeout(() => {
      listRef.current?.scrollToEnd({ animated: true });
    }, 50);
    return () => clearTimeout(id);
  }, [messages.length, isLoading]);

  return (
    <SafeAreaView
      style={[styles.safe, { backgroundColor: colors.background }]}
      edges={['top', 'left', 'right']}
    >
      <View style={[styles.header, { borderBottomColor: colors.border }]}>
        <Text style={[styles.headerTitle, { color: colors.text }]}>Chat</Text>
        <Pressable
          onPress={reset}
          accessibilityRole="button"
          accessibilityLabel="Reset conversation"
          hitSlop={8}
        >
          <Text style={[styles.headerAction, { color: colors.accent }]}>Reset</Text>
        </Pressable>
      </View>

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 8 : 0}
      >
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(m) => m.id}
          contentContainerStyle={styles.listContent}
          renderItem={({ item }) => <MessageBubble message={item} colors={colors} />}
          ListFooterComponent={isLoading ? <TypingIndicator colors={colors} /> : null}
          onContentSizeChange={() =>
            listRef.current?.scrollToEnd({ animated: false })
          }
          refreshControl={
            <RefreshControl
              refreshing={false}
              onRefresh={reset}
              tintColor={colors.textMuted}
            />
          }
        />

        {error ? (
          <Pressable
            onPress={clearError}
            style={[styles.errorBanner, { backgroundColor: '#fee2e2' }]}
            accessibilityRole="button"
            accessibilityLabel="Dismiss error"
          >
            <Text style={styles.errorText}>
              {error} (tap to dismiss)
            </Text>
          </Pressable>
        ) : null}

        <SafeAreaView edges={['bottom']} style={{ backgroundColor: colors.surface }}>
          <ChatInput onSend={send} disabled={isLoading} colors={colors} />
        </SafeAreaView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  flex: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  headerAction: {
    fontSize: 15,
    fontWeight: '500',
  },
  listContent: {
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  errorBanner: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginHorizontal: 12,
    marginBottom: 6,
    borderRadius: 10,
  },
  errorText: {
    color: '#991b1b',
    fontSize: 14,
  },
});
