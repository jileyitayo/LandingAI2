import { useEffect } from 'react';

interface KeyboardShortcutHandlers {
  onToggleSelector?: () => void;
  onClearSelection?: () => void;
  onFocusChat?: () => void;
}

/**
 * Custom hook for handling keyboard shortcuts in the editor
 */
export function useKeyboardShortcuts({
  onToggleSelector,
  onClearSelection,
  onFocusChat,
}: KeyboardShortcutHandlers) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if user is typing in an input/textarea
      const target = event.target as HTMLElement;
      const isTyping = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';

      // E - Toggle selector (only when not typing)
      if (event.key === 'e' && !isTyping && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        onToggleSelector?.();
      }

      // Escape - Clear selection or disable selector
      if (event.key === 'Escape') {
        event.preventDefault();
        onClearSelection?.();
      }

      // Cmd/Ctrl + K - Focus chat input
      if (event.key === 'k' && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        onFocusChat?.();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onToggleSelector, onClearSelection, onFocusChat]);
}
