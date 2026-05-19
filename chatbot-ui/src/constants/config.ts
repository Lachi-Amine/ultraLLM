import Constants from 'expo-constants';

const extra = (Constants.expoConfig?.extra ?? {}) as Record<string, unknown>;

export const API_BASE_URL: string =
  (extra.apiBaseUrl as string | undefined) ?? 'https://your-backend.example.com';

export const API_TIMEOUT_MS = 20_000;

export const INITIAL_ASSISTANT_MESSAGE =
  "Hi! I'm your assistant. Ask me anything to get started.";

export const Colors = {
  light: {
    background: '#ffffff',
    surface: '#f5f6f8',
    text: '#111827',
    textMuted: '#6b7280',
    border: '#e5e7eb',
    userBubble: '#2563eb',
    userBubbleText: '#ffffff',
    assistantBubble: '#f1f3f5',
    assistantBubbleText: '#111827',
    inputBackground: '#ffffff',
    accent: '#2563eb',
    disabled: '#9ca3af',
  },
  dark: {
    background: '#0b0d12',
    surface: '#11141b',
    text: '#f3f4f6',
    textMuted: '#9ca3af',
    border: '#1f2937',
    userBubble: '#3b82f6',
    userBubbleText: '#ffffff',
    assistantBubble: '#1f2330',
    assistantBubbleText: '#f3f4f6',
    inputBackground: '#11141b',
    accent: '#3b82f6',
    disabled: '#4b5563',
  },
} as const;

export type ColorScheme = keyof typeof Colors;
export type ThemeColors = (typeof Colors)[ColorScheme];
