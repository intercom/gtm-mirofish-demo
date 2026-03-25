import { onUnmounted } from 'vue'

const INTERACTIVE_TAGS = new Set(['input', 'textarea', 'select'])

function isTyping() {
  const tag = document.activeElement?.tagName?.toLowerCase()
  return INTERACTIVE_TAGS.has(tag) || document.activeElement?.isContentEditable
}

/**
 * Scoped keyboard shortcut manager.
 * Registers shortcuts on creation, auto-unregisters on component unmount.
 *
 * @param {Array<{ key: string, handler: Function, description?: string, ctrl?: boolean, shift?: boolean, meta?: boolean, allowInInput?: boolean }>} shortcuts
 * @returns {{ unregisterAll: Function }}
 */
export function useKeyboardShortcuts(shortcuts) {
  function handleKeydown(e) {
    if (!shortcuts.length) return

    for (const shortcut of shortcuts) {
      const keyMatch =
        e.key === shortcut.key ||
        e.code === shortcut.key ||
        e.key.toLowerCase() === shortcut.key.toLowerCase()

      if (!keyMatch) continue
      if (shortcut.ctrl && !e.ctrlKey && !e.metaKey) continue
      if (shortcut.shift && !e.shiftKey) continue
      if (shortcut.meta && !e.metaKey) continue
      if (!shortcut.allowInInput && isTyping()) continue

      e.preventDefault()
      shortcut.handler(e)
      return
    }
  }

  window.addEventListener('keydown', handleKeydown)

  function unregisterAll() {
    window.removeEventListener('keydown', handleKeydown)
  }

  onUnmounted(unregisterAll)

  return { unregisterAll }
}
