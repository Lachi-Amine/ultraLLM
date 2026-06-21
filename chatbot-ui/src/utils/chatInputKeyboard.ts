export function shouldSubmitOnEnter(
  key: string,
  shiftKey = false,
  isComposing = false,
) {
  return key === 'Enter' && !shiftKey && !isComposing;
}
