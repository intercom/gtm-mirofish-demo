import { onUnmounted } from 'vue'

const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad|iPod/.test(navigator.userAgent)

const registry = new Map()
let listenerAttached = false

function isInputFocused() {
  const el = document.activeElement
  if (!el) return false
  const tag = el.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
  return el.isContentEditable
}

function normalizeShortcut(shortcut) {
  return shortcut
    .toLowerCase()
    .split('+')
    .map((k) => k.trim())
    .sort()
    .join('+')
}

function eventToShortcut(e) {
  const parts = []
  if (isMac ? e.metaKey : e.ctrlKey) parts.push('ctrl')
  if (e.shiftKey) parts.push('shift')
  if (e.altKey) parts.push('alt')

  const key = e.key.toLowerCase()
  if (!['control', 'meta', 'shift', 'alt'].includes(key)) {
    parts.push(key === ' ' ? 'space' : key)
  }

  return parts.sort().join('+')
}

function handleKeydown(e) {
  const combo = eventToShortcut(e)
  const entry = registry.get(combo)
  if (!entry) return

  if (entry.options?.allowInInput !== true && isInputFocused()) return

  e.preventDefault()
  entry.handler(e)
}

function ensureListener() {
  if (listenerAttached) return
  document.addEventListener('keydown', handleKeydown)
  listenerAttached = true
}

function removeListenerIfEmpty() {
  if (registry.size === 0 && listenerAttached) {
    document.removeEventListener('keydown', handleKeydown)
    listenerAttached = false
  }
}

function register(shortcut, handler, options = {}) {
  const key = normalizeShortcut(shortcut)

  if (registry.has(key)) {
    console.warn(`[useKeyboardShortcuts] Shortcut "${shortcut}" is already registered. Overwriting.`)
  }

  registry.set(key, { shortcut, handler, options })
  ensureListener()
}

function unregister(shortcut) {
  const key = normalizeShortcut(shortcut)
  registry.delete(key)
  removeListenerIfEmpty()
}

function getAll() {
  return Array.from(registry.values()).map(({ shortcut, options }) => ({
    shortcut,
    description: options.description || '',
    category: options.category || 'General',
    scope: options.scope || 'global',
  }))
}

function formatKey(shortcut) {
  return shortcut
    .split('+')
    .map((k) => {
      const lower = k.trim().toLowerCase()
      if (lower === 'ctrl') return isMac ? '⌘' : 'Ctrl'
      if (lower === 'shift') return isMac ? '⇧' : 'Shift'
      if (lower === 'alt') return isMac ? '⌥' : 'Alt'
      if (lower === 'escape') return 'Esc'
      if (lower === 'space') return 'Space'
      if (lower === 'arrowup') return '↑'
      if (lower === 'arrowdown') return '↓'
      if (lower === 'arrowleft') return '←'
      if (lower === 'arrowright') return '→'
      if (lower === 'backspace') return '⌫'
      if (lower === 'delete') return 'Del'
      if (lower === 'enter') return '↵'
      return k.trim().toUpperCase()
    })
    .join(isMac ? '' : '+')
}

export function useKeyboardShortcuts() {
  const registered = []

  function registerLocal(shortcut, handler, options = {}) {
    register(shortcut, handler, options)
    registered.push(shortcut)
  }

  function unregisterAll() {
    registered.forEach((s) => unregister(s))
    registered.length = 0
  }

  onUnmounted(unregisterAll)

  return {
    register: registerLocal,
    unregister,
    unregisterAll,
    getAll,
    formatKey,
    isMac,
  }
}

export { register, unregister, getAll, formatKey, normalizeShortcut, isMac, registry }
