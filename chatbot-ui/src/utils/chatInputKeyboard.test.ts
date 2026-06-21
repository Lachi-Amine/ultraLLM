import { describe, expect, it } from 'vitest';

import { shouldSubmitOnEnter } from './chatInputKeyboard';

describe('shouldSubmitOnEnter', () => {
  it('submits when Enter is pressed', () => {
    expect(shouldSubmitOnEnter('Enter')).toBe(true);
  });

  it('keeps Shift+Enter available for a newline', () => {
    expect(shouldSubmitOnEnter('Enter', true)).toBe(false);
  });

  it('does not submit while an input method is composing text', () => {
    expect(shouldSubmitOnEnter('Enter', false, true)).toBe(false);
  });

  it('ignores other keys', () => {
    expect(shouldSubmitOnEnter('a')).toBe(false);
  });
});
