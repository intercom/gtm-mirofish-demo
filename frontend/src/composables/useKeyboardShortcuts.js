import { ref, getCurrentInstance, onUnmounted } from 'vue'

const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform)
const registry = new Map()
const gModeActive = ref(false)
const showHelp = ref(false)
let gModeTimer = null
let listenerAttached = false

const shortcuts = [
  {
    group: 'General',
    items: [
      { keys: ['?'], description: 'Show keyboard shortcuts' },
      { keys: ['Esc'], description: 'Close modal / dialog' },
    ],
  },
  {
    group: 'Workspace',
    items: [
      { keys: ['1'], description: 'Switch to Knowledge Graph tab' },
      { keys: ['2'], description: 'Switch to Simulation tab' },
    ],
  },
  {
    group: 'Chat',
    items: [
      { keys: ['Enter'], description: 'Send message' },
      { keys: ['Shift', 'Enter'], description: 'New line in message' },
    ],
  },
]

function isInputFocused() {
  const el = document.activeElement
  if (!el) return false
  const tag = el.tagName.toLowerCase()
  return tag === 'input' || tag === 'textarea' || tag === 'select' || el.isContentEditable
}

function eventToKey(e) {
  const parts = []
  const mod = isMac ? e.metaKey : e.ctrlKey
  if (mod) parts.push('mod')
  if (e.shiftKey && (mod || e.altKey)) parts.push('shift')
  if (e.altKey) parts.push('alt')
  parts.push(e.key.toLowerCase())
  return parts.join('+')
}

function handleKeydown(e) {
  if (e.repeat) return

  if (e.key === 'Escape') {
    gModeActive.value = false
    showHelp.value = false
    clearTimeout(gModeTimer)
    const entry = registry.get('escape')
    if (entry) {
      e.preventDefault()
      entry.handler()
    }
    return
  }

  const mod = isMac ? e.metaKey : e.ctrlKey
  if (mod) {
    const key = eventToKey(e)
    const entry = registry.get(key)
    if (entry) {
      e.preventDefault()
      entry.handler()
    }
    return
  }

  if (isInputFocused()) return

  if (gModeActive.value) {
    gModeActive.value = false
    clearTimeout(gModeTimer)
    const key = `g+${e.key.toLowerCase()}`
    const entry = registry.get(key)
    if (entry) {
      e.preventDefault()
      entry.handler()
    }
    return
  }

  if (e.key === 'g' && !e.shiftKey && !e.altKey) {
    const hasG = [...registry.keys()].some(k => k.startsWith('g+'))
    if (hasG) {
      gModeActive.value = true
      gModeTimer = setTimeout(() => { gModeActive.value = false }, 500)
      return
    }
  }

  const key = eventToKey(e)
  const entry = registry.get(key)
  if (entry) {
    e.preventDefault()
    entry.handler()
  }
}

function attachListener() {
  if (!listenerAttached) {
    window.addEventListener('keydown', handleKeydown)
    listenerAttached = true
  }
}

function getAll() {
  return Array.from(registry.entries()).map(([key, entry]) => ({
    shortcut: key,
    description: entry.description || '',
    category: entry.category || 'Global',
  }))
}

function formatKey(shortcut) {
  return shortcut
    .split('+')
    .map((k) => {
      const lower = k.trim().toLowerCase()
      if (lower === 'mod') return isMac ? '⌘' : 'Ctrl'
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
  attachListener()

  const localKeys = []

  function register(shortcut, handler, options = {}) {
    const key = shortcut.toLowerCase().replace(/ctrl|cmd|meta/g, 'mod')
    if (registry.has(key)) {
      console.warn(`[shortcuts] Overwriting: ${shortcut}`)
    }
    registry.set(key, {
      handler,
      description: options.description || '',
      category: options.category || 'Global',
    })
    localKeys.push(key)
  }

  function unregister(shortcut) {
    const key = shortcut.toLowerCase().replace(/ctrl|cmd|meta/g, 'mod')
    registry.delete(key)
    const idx = localKeys.indexOf(key)
    if (idx !== -1) localKeys.splice(idx, 1)
  }

  function unregisterAll() {
    localKeys.forEach(key => registry.delete(key))
    localKeys.length = 0
  }

  if (getCurrentInstance()) {
    onUnmounted(unregisterAll)
  }

  return { register, unregister, unregisterAll, getAll, formatKey, isMac, gModeActive, registry, showHelp, shortcuts }
}
