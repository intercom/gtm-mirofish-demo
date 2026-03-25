import { computed } from 'vue'

const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform)

const modSymbols = {
  mod: isMac ? '⌘' : 'Ctrl',
  ctrl: isMac ? '⌃' : 'Ctrl',
  alt: isMac ? '⌥' : 'Alt',
  shift: '⇧',
  meta: isMac ? '⌘' : 'Win',
}

const keySymbols = {
  enter: '↵',
  escape: 'Esc',
  backspace: '⌫',
  delete: '⌦',
  arrowup: '↑',
  arrowdown: '↓',
  arrowleft: '←',
  arrowright: '→',
  space: '␣',
  tab: '⇥',
}

/**
 * Formats a shortcut string like "mod+k" into platform-aware display parts.
 * Returns an array of key labels, e.g. ["⌘", "K"] on Mac or ["Ctrl", "K"] on Windows.
 */
export function formatShortcut(shortcut) {
  if (!shortcut) return []
  return shortcut.split('+').map((key) => {
    const lower = key.trim().toLowerCase()
    if (modSymbols[lower]) return modSymbols[lower]
    if (keySymbols[lower]) return keySymbols[lower]
    return key.trim().toUpperCase()
  })
}

/**
 * Returns a plain-text shortcut string for use in title/aria attributes.
 * e.g. "mod+k" → "⌘K" on Mac, "Ctrl+K" on Windows
 */
export function formatShortcutText(shortcut) {
  return formatShortcut(shortcut).join('')
}

export function useKeyboardShortcuts() {
  const platform = computed(() => (isMac ? 'mac' : 'other'))

  return {
    isMac,
    platform,
    formatShortcut,
    formatShortcutText,
  }
}
